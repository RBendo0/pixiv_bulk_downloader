from __future__ import annotations

import math
import subprocess
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import IO, Literal

from .const import FFMPEG_LOG_DIR
from .debug import debug
from .errors import (
    EncoderStreamError,
    FFmpegExecutableError,
    FFmpegExecutionError,
    InvalidDataFormatError,
    PBDError,
)
from .pbd_types import FFmpegResult, FrameSpec

MediaFormat = Literal["gif", "webm", "mp4"]


class DebuggedFFmpegProcess:

    def __init__(
        self,
        command: Sequence[str],
        log_id: int,
        output_path: Path,
    ) -> None:

        timestamp = datetime.now().astimezone().strftime(
            "%Y%m%d_%H%M%S"
        )

        self._error_log_path = (
            FFMPEG_LOG_DIR
            / (
                f"{timestamp}_"
                f"{log_id}_"
                f"{output_path.name}.log"
            )
        )

        self._process: subprocess.Popen[bytes] | None = None
        self._error_log: IO[bytes] | None = None

        if debug.simulation():
            return

        FFMPEG_LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._error_log = self._error_log_path.open(
            "w+b"
        )

        try:

            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=self._error_log,
            )

            if self._process.stdin is None:
                raise EncoderStreamError(
                    "FFmpeg input stream is unavailable"
                )

        except Exception:

            self._close_log()

            if self._error_log_path.exists():
                self._error_log_path.unlink()

            raise

    def _close_log(
        self,
    ) -> None:

        if (
            self._error_log is not None
            and not self._error_log.closed
        ):
            self._error_log.close()

    def write(
        self,
        data: bytes | None,
    ) -> None:

        if debug.simulation():
            return

        if data is None:
            raise EncoderStreamError(
                "FFmpeg input data is unavailable"
            )

        if self._process is None or self._process.stdin is None:
            raise EncoderStreamError(
                "FFmpeg process is unavailable"
            )

        self._process.stdin.write(data)

    def close_input(
        self,
    ) -> None:

        if debug.simulation():
            return

        if self._process is None or self._process.stdin is None:
            raise EncoderStreamError(
                "FFmpeg process is unavailable"
            )

        if not self._process.stdin.closed:
            self._process.stdin.close()

    def abort(
        self,
    ) -> None:

        if debug.simulation():
            return

        if self._process is None:
            raise EncoderStreamError(
                "FFmpeg process is unavailable"
            )

        try:

            if self._process.poll() is None:
                self._process.kill()

            self._process.wait()

        finally:
            self._close_log()

    def wait(
        self,
    ) -> FFmpegResult:

        if debug.simulation():
            return FFmpegResult(
                code=0,
                log_file=self._error_log_path,
            )

        if self._process is None:
            raise EncoderStreamError(
                "FFmpeg process is unavailable"
            )

        try:

            return_code = self._process.wait()

        finally:
            self._close_log()

        if (
            return_code == 0
            and self._error_log_path.exists()
        ):
            self._error_log_path.unlink()

        return FFmpegResult(
            code=return_code,
            log_file=self._error_log_path,
        )


class Encoder:
    """
    Encoder FFmpeg riutilizzabile per conversioni sequenziali.

    Ogni ciclo di conversione segue il protocollo:

        start(...)
        add(image_data)  # una chiamata per ogni voce di frames
        stop()

    La classe non conosce ZIP, metadata Pixiv, UI o thread pool.
    Riceve in start() la specifica ordinata dei frame e in add()
    i byte completi dell'immagine JPEG/PNG corrispondente.
    """

    def __init__(
        self,
        ffmpeg: Path,
    ) -> None:
        self._ffmpeg = ffmpeg

        self._process: DebuggedFFmpegProcess | None = None

        self._frames: Sequence[FrameSpec] = ()
        self._frame_index = 0
        self._tick_ms = 0

    @staticmethod
    def _delay_from_frame(
        frame: FrameSpec,
        index: int,
    ) -> int:
        try:

            delay_ms = int(frame["delay"])

        except (KeyError, TypeError, ValueError) as error:

            raise InvalidDataFormatError(
                f"Invalid delay at index {index}"
            ) from error

        if delay_ms <= 0:
            raise InvalidDataFormatError(
                f"Delay must be positive: index={index} delay={delay_ms}"
            )

        return delay_ms

    @classmethod
    def _common_delay_tick_ms(
        cls,
        frames: Sequence[FrameSpec],
    ) -> int:
        if not frames:
            raise InvalidDataFormatError(
                "No frames provided"
            )

        tick_ms = cls._delay_from_frame(frames[0], 0)

        for index, frame in enumerate(frames[1:], start=1):
            tick_ms = math.gcd(
                tick_ms,
                cls._delay_from_frame(frame, index),
            )

        if tick_ms <= 0:
            raise InvalidDataFormatError(
                "Delays time must be positive"
            )

        return tick_ms

    @staticmethod
    def _output_arguments(
        format_name: MediaFormat,
        output_path: Path,
        codec: str | None,
    ) -> list[str]:
        if format_name == "gif":
            return [
                "-filter_complex",
                (
                    "[0:v]split[a][b];"
                    "[a]palettegen[p];"
                    "[b][p]paletteuse"
                ),
                "-loop",
                "0",
                str(output_path),
            ]

        if not codec:
            raise InvalidDataFormatError(
                f"No codec provided for {format_name} format"
            )

        even_dimensions = (
            "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        )

        if format_name == "webm":
            return [
                "-vf",
                even_dimensions,
                "-c:v",
                codec,
                "-crf",
                "30",
                "-b:v",
                "0",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

        if format_name == "mp4":
            return [
                "-vf",
                even_dimensions,
                "-c:v",
                codec,
                "-crf",
                "23",
                "-preset",
                "medium",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]

    def start(
        self,
        log_id: int,
        *,
        format_name: MediaFormat,
        output_path: Path,
        frames: Sequence[FrameSpec],
        codec: str | None = None,
    ) -> None:
        """
        Avvia una nuova conversione.

        frames deve essere la sequenza ordinata già presente nei
        metadata Ugoira. Ogni elemento deve esporre almeno la chiave
        "delay". Il campo "file" resta competenza del chiamante.
        """
        try:

            self._reset()

            self._frames = frames
            self._frame_index = 0
            self._tick_ms = self._common_delay_tick_ms(frames)

            output_path = Path(output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            input_framerate = f"1000/{self._tick_ms}"

            command = [
                str(self._ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "image2pipe",
                "-framerate",
                input_framerate,
                "-i",
                "pipe:0",
                *self._output_arguments(
                    format_name,
                    output_path,
                    codec,
                ),
            ]

            try:

                self._process = DebuggedFFmpegProcess(
                    command,
                    log_id,
                    output_path,
                )

            except Exception as e:

                raise FFmpegExecutableError.hierarchy(e) from e

        except Exception as e:

            raise PBDError.hierarchy(e) from e

    def add(
        self,
        image_data: bytes | None,
    ) -> None:

        """
        Invia a FFmpeg l'immagine corrispondente al frame corrente.

        image_data contiene il file JPEG/PNG completo, già estratto
        dallo ZIP in memoria ma non decodificato.
        """

        try:

            if self._process is None:
                raise EncoderStreamError(
                    "Encoder not ready. Ensure .start() is called before first .add()"
                )

            if self._frame_index >= len(self._frames):
                raise EncoderStreamError(
                    "Frame stream overflow: too many frames provided"
                )

            delay_ms = self._delay_from_frame(
                self._frames[self._frame_index],
                self._frame_index,
            )
            repetitions = delay_ms // self._tick_ms

            try:

                for _ in range(repetitions):
                    self._process.write(image_data)

            except Exception as e:

                raise EncoderStreamError.hierarchy(e) from e

            self._frame_index += 1

        except Exception as e:

            raise PBDError.hierarchy(e) from e

    def stop(
        self,
        *,
        ignore_errors: bool = False,
    ) -> None:

        """
        Chiude la sessione di encoding corrente e libera le risorse
        associate al processo FFmpeg.
        """

        try:

            if self._process is None:
                raise EncoderStreamError(
                    "Encoder not ready. Ensure .start() is called before .stop()"
                )

            process = self._process

            try:

                process.close_input()

                if self._frame_index != len(self._frames):

                    missing = (
                        len(self._frames)
                        - self._frame_index
                    )

                    process.abort()

                    raise EncoderStreamError(
                        "Frame stream underflow: not enough frames provided "
                        f"(missing {missing} frames)"
                    )

                result = process.wait()

                if result.code != 0:

                    raise FFmpegExecutionError(
                        f"FFmpeg exited with code {result.code}. "
                        f"For more details, see error log: "
                        f"{result.log_file.name}"
                    )

            finally:

                self._reset()

        except Exception as e:

            if not ignore_errors:
                raise PBDError.hierarchy(e) from e

    def _reset(self) -> None:

        self._process = None
        self._frames = ()
        self._frame_index = 0
        self._tick_ms = 0