from __future__ import annotations

import math
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, Any, Literal

MediaFormat = Literal["gif", "webm", "mp4"]
FrameSpec = Mapping[str, Any]


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
        ffmpeg: str | Path = "ffmpeg",
    ) -> None:
        self._ffmpeg = Path(ffmpeg)

        self._process: subprocess.Popen[bytes] | None = None
        self._error_log: IO[bytes] | None = None

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
            raise ValueError(
                f"Delay non valido per il frame all'indice {index}"
            ) from error

        if delay_ms <= 0:
            raise ValueError(
                f"Delay non positivo per il frame all'indice {index}: "
                f"{delay_ms}"
            )

        return delay_ms

    @classmethod
    def _common_delay_tick_ms(
        cls,
        frames: Sequence[FrameSpec],
    ) -> int:
        if not frames:
            raise ValueError(
                "La conversione richiede almeno un frame"
            )

        tick_ms = cls._delay_from_frame(frames[0], 0)

        for index, frame in enumerate(frames[1:], start=1):
            tick_ms = math.gcd(
                tick_ms,
                cls._delay_from_frame(frame, index),
            )

        if tick_ms <= 0:
            raise ValueError(
                "Impossibile calcolare una base temporale valida"
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
                "[0:v]split[a][b];"
                "[a]palettegen[p];"
                "[b][p]paletteuse",
                "-loop",
                "0",
                str(output_path),
            ]

        if not codec:
            raise ValueError(
                f"Il formato {format_name} richiede "
                "il nome dell'encoder FFmpeg"
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

        raise ValueError(
            f"Formato non supportato: {format_name}"
        )

    def start(
        self,
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

        self._error_log = tempfile.TemporaryFile(
            mode="w+b",
        )

        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=self._error_log,
            )

            if self._process.stdin is None:
                raise RuntimeError(
                    "Impossibile aprire stdin di FFmpeg"
                )

        except BaseException:
            self._cleanup_process(kill=True)
            raise

    def add(
        self,
        image_data: bytes,
    ) -> None:
        """
        Invia a FFmpeg l'immagine corrispondente al frame corrente.

        image_data contiene il file JPEG/PNG completo, già estratto
        dallo ZIP in memoria ma non decodificato.
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError(
                "FFmpeg non è stato avviato"
            )

        if self._frame_index >= len(self._frames):
            raise RuntimeError(
                "Sono state fornite più immagini "
                "di quelle dichiarate in frames"
            )

        delay_ms = self._delay_from_frame(
            self._frames[self._frame_index],
            self._frame_index,
        )
        repetitions = delay_ms // self._tick_ms

        if repetitions <= 0:
            raise ValueError(
                "Numero di ripetizioni non valido per il frame "
                f"all'indice {self._frame_index}"
            )

        try:
            for _ in range(repetitions):
                self._process.stdin.write(image_data)

        except BaseException:
            self._cleanup_process(kill=True)
            raise

        self._frame_index += 1

    def stop(self) -> None:
        """
        Chiude il flusso di ingresso e attende la finalizzazione
        del file da parte di FFmpeg.
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError(
                "FFmpeg non è stato avviato"
            )

        if self._frame_index != len(self._frames):
            missing = len(self._frames) - self._frame_index
            self._cleanup_process(kill=True)
            raise RuntimeError(
                "Conversione incompleta: "
                f"mancano {missing} immagini"
            )

        process = self._process
        stdin = process.stdin
        error_log = self._error_log

        assert stdin is not None

        try:
            stdin.close()
            return_code = process.wait()

            if return_code != 0:
                error_text = self._read_error_log(error_log)
                raise RuntimeError(
                    f"FFmpeg è terminato con codice {return_code}."
                    + (
                        f"\n{error_text}"
                        if error_text
                        else ""
                    )
                )

        finally:
            self._cleanup_process(kill=False)

    @staticmethod
    def _read_error_log(
        error_log: IO[bytes] | None,
    ) -> str:
        if error_log is None:
            return ""

        error_log.seek(0)

        return error_log.read().decode(
            "utf-8",
            errors="replace",
        ).strip()

    def _cleanup_process(
        self,
        *,
        kill: bool,
    ) -> None:
        process = self._process

        if process is not None:
            if (
                process.stdin is not None
                and not process.stdin.closed
            ):
                process.stdin.close()

            if kill and process.poll() is None:
                process.kill()

            if process.poll() is None:
                process.wait()

        if self._error_log is not None:
            self._error_log.close()

        self._process = None
        self._error_log = None
        self._frames = ()
        self._frame_index = 0
        self._tick_ms = 0
