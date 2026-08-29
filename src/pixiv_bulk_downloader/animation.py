import zipfile
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path
from typing import Self

from .config import config
from .const import (
    ADVANCED_KEY_MP4_CODEC,
    ADVANCED_KEY_WEBM_CODEC,
    CONFIG_KEY_PREF_MEDIA,
    DEFAULT_CODEC_SETTINGS,
    DEFAULT_PREFERRED_MEDIA_FORMATS,
    FFMPEG_ENCODERS,
    FFMPEG_EXECUTABLE,
)
from .debug import debug
from .encoder import Encoder, MediaFormat
from .errors import (
    AnimationError,
    ConfigError,
    FileError,
    InvalidDataFormatError,
    PBDError,
    UserHasNotDefinedCustomConfiguration,
)
from .pbd_types import CodecSettings, FrameSpec, PreferredMediaFormats, ToggleOption
from .ui import ui


class DebuggedZipFile:

    def __init__(
        self,
        path: Path | str,
        frames: Sequence[FrameSpec],
    ) -> None:

        self._path = Path(path)
        self._frames = frames
        self._archive: zipfile.ZipFile | None = None

    def __enter__(
        self,
    ) -> Self:

        if not debug.simulation():
            self._archive = zipfile.ZipFile(
                self._path,
                "r",
            )

        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:

        if self._archive is not None:
            self._archive.close()

        self._archive = None

    def namelist(
        self,
    ) -> list[str] | None:

        if debug.simulation():

            names: list[str] = []

            for frame in self._frames:

                try:
                    names.append(
                        str(frame["file"])
                    )

                except (KeyError, TypeError):
                    continue

            return names

        if self._archive is None:
            return None

        return self._archive.namelist()

    def read(
        self,
        name: str,
    ) -> bytes | None:

        if debug.simulation():

            names = self.namelist()

            if names is None:
                return None

            if name not in names:
                raise KeyError(
                    f"There is no item named {name!r} in the archive"
                )

            return b""

        if self._archive is None:
            return None

        return self._archive.read(name)


class MultiMediaManager:

    _preferred_media_formats: PreferredMediaFormats = replace(DEFAULT_PREFERRED_MEDIA_FORMATS)

    _codec: CodecSettings = replace(DEFAULT_CODEC_SETTINGS) 

    @classmethod
    def _load_preferred_media_formats(cls) -> None:

        cls._preferred_media_formats = replace(DEFAULT_PREFERRED_MEDIA_FORMATS)

        try:

            preferred_media_formats = config.load(
                CONFIG_KEY_PREF_MEDIA
            )

            if preferred_media_formats is None:

                return

            try:

                cls._preferred_media_formats = PreferredMediaFormats(
                    **preferred_media_formats
                )

            except (TypeError, ValueError) as e:

                raise ConfigError.hierarchy(e) from e

        except UserHasNotDefinedCustomConfiguration:

            return

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                "Failed to load preferences about media formats.",
                with_report=True,
            )

            ui.line(
                "[+]: Preferred formats will be set to default.",
                ui.COLOR_WARNING,
            )

    @classmethod
    def _load_codec_setting(
        cls,
        key: str,
    ) -> str | None:

        try:

            codec_setting = config.Advanced.load(key)

            if codec_setting is None or codec_setting == "":
                raise UserHasNotDefinedCustomConfiguration()

            elif not isinstance(codec_setting, str):
                raise InvalidDataFormatError()

            else:
                return codec_setting

        except UserHasNotDefinedCustomConfiguration:

            pass

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                f"Failed to load [@@{key}@@.], "
                "codec will be set to default.",
                with_report=True,
            )

        return None
    
    @classmethod
    def _load_media_codecs(cls) -> None:

        cls._codec = replace(DEFAULT_CODEC_SETTINGS) 

        webm_codec = cls._load_codec_setting(
            ADVANCED_KEY_WEBM_CODEC
        )

        mp4_codec = cls._load_codec_setting(
            ADVANCED_KEY_MP4_CODEC
        )

        if webm_codec is not None:
            cls._codec.webm = webm_codec 

        if mp4_codec is not None:
            cls._codec.mp4 = mp4_codec 

    @classmethod
    def _pmfs_to_togo(
        cls,
        pmfs: PreferredMediaFormats,
    ) -> list[ToggleOption]:

        return [
            ToggleOption("1", "GIF", pmfs.gif),
            ToggleOption("2", "WEBM", pmfs.webm),
            ToggleOption("3", "MP4", pmfs.mp4),
        ]

    @classmethod
    def _togo_to_pmfs(
        cls,
        togo: list[ToggleOption],
    ) -> PreferredMediaFormats:

        return PreferredMediaFormats(
            gif=togo[0].enabled,
            webm=togo[1].enabled,
            mp4=togo[2].enabled,
        )

    @classmethod
    def _show_current_media_settings(cls) -> None:
        
        ui.line(
            "[+]: Animation downloads formats: [@@"
            f"{' GIF' if cls._preferred_media_formats.gif else ""}"
            f"{' WEBM' if cls._preferred_media_formats.webm else ""}"
            f"{' MP4' if cls._preferred_media_formats.mp4 else ""}"
            "@@. ]",
            tag_color=ui.COLOR_INFO,
        )

        ui.line(
            "[+]: Animation current codecs: ["
            f" WEBM=@@{cls._codec.webm}@@."
            f" MP4=@@{cls._codec.mp4}@@. ]",
            tag_color=ui.COLOR_INFO,
        )

    @classmethod
    def init(cls) -> None:

        cls._load_preferred_media_formats()
        cls._load_media_codecs()

        cls._show_current_media_settings()

    @classmethod
    def set_preferred_media_formats(cls) -> None:

        ui.line()
        ui.line("[+]: Selezionare i singoli formati di salvataggio delle animazioni")
        ui.line("     premendo il tasto del numero associato alla rispettiva voce menu.")
        ui.line("     Nessuna selezione imposta formati di default")
        ui.line("[-]: [SPAZIO] ripristina impostazioni precedenti")
        ui.line("[+]: [INVIO] per confermare")
        ui.line()
        
        options = cls._pmfs_to_togo(
            cls._preferred_media_formats
        )

        options = ui.toggle_menu(
            options,
        )

        ui.clear_lines(6)

        new_preferred_media_formats = cls._togo_to_pmfs(
            options
        )

        cls._preferred_media_formats = new_preferred_media_formats

        if not config.save_with_interact(
            key=CONFIG_KEY_PREF_MEDIA,
            value=asdict(new_preferred_media_formats),
            subject="preferred media formats"
        ):

            ui.line(
                "[+]: The new preferences will remain active "
                "for the current session only.",
                ui.COLOR_WARNING,
            )

        cls._show_current_media_settings()

    @classmethod
    def build_animation(
        cls,
        log_id: int,
        progress: str,
        zip_path: Path,
        frames: Sequence[FrameSpec],
    ) -> bool:

        formats: list[
            tuple[
                MediaFormat,
                str | None,
            ]
        ] = []

        if cls._preferred_media_formats.gif:
            formats.append(
                (
                    "gif",
                    None,
                )
            )

        if cls._preferred_media_formats.webm:
            formats.append(
                (
                    "webm",
                    FFMPEG_ENCODERS[cls._codec.webm],
                )
            )

        if cls._preferred_media_formats.mp4:
            formats.append(
                (
                    "mp4",
                    FFMPEG_ENCODERS[cls._codec.mp4],
                )
            )

        encoder = Encoder(FFMPEG_EXECUTABLE)

        frame_total = len(frames)

        def write_progress(
            progress: str,
            status: str,
            *,
            history: bool = False,
        ) -> str:

            status_suffix = (
                f"{ui.COLOR_DEFAULT}"
                f" | "
                f"{status}"
            )

            display_progress = (
                progress + status_suffix
            )

            ui.Renderer.in_thread_write(
                display_progress
            )

            if history:
                return display_progress

            return progress

        try:

            with DebuggedZipFile(
                zip_path,
                frames,
            ) as archive:

                archive_names_list = archive.namelist()

                if archive_names_list is None:
                    raise AnimationError(
                        f"Animation archive {zip_path.name!r} is not initialized"
                    )

                archive_names = set(
                    archive_names_list
                )                

                for frame_index, frame in enumerate(
                    frames,
                    start=1,
                ):

                    try:

                        frame_name = str(
                            frame["file"]
                        )

                    except (KeyError, TypeError) as error:

                        raise AnimationError(
                            f"Invalid frame name at index {frame_index - 1}"
                        ) from error

                    if frame_name not in archive_names:

                        raise AnimationError(
                            f"Missing {frame_name!r} in {zip_path.name}"
                        )

                completed = True

                for (
                    format_name,
                    codec,
                ) in formats:

                    format_label = format_name.upper()

                    output_path = (
                        zip_path.parent
                        / f"a0.{format_name}"
                    )

                    try:

                        encoder.start(
                            log_id,
                            format_name=format_name,
                            output_path=output_path,
                            frames=frames,
                            codec=codec,
                        )

                        write_progress(
                            progress,
                            f"{ui.COLOR_INFO}"
                            f"Building {format_label} "
                            f"[0/{frame_total}] "
                            f"0%"
                        )

                        for frame_index, frame in enumerate(
                            frames,
                            start=1,
                        ):

                            frame_name = str(
                                frame["file"]
                            )

                            image_data = archive.read(
                                frame_name
                            )

                            encoder.add(
                                image_data
                            )

                            percentage = (
                                frame_index
                                * 100
                                // frame_total
                            )

                            write_progress(
                                progress,
                                f"{ui.COLOR_INFO}"
                                f"Building {format_label} "
                                f"[{frame_index}/{frame_total}] "
                                f"{percentage}%",
                            )

                        encoder.stop()

                    except Exception as error:  # noqa: BLE001

                        # Se l'errore è avvenuto fuori da Encoder.add(),
                        # per esempio durante la lettura dello ZIP, assicura
                        # comunque la chiusura del processo FFmpeg.
                        encoder.stop(ignore_errors=True)

                        error = PBDError.hierarchy(error)

                        # storico console
                        error.notify(
                            f"Failed to encode @@{format_label}@@. | "
                            f"Artwork: <ID:@@{log_id}@@.>",
                            with_report=True,
                        )

                        # renderer
                        progress = write_progress(
                            progress,
                            f"{ui.COLOR_ERROR}"
                            f"{format_label} discarded",
                            history=True,
                        )

                        completed = False

                        continue

                    progress = write_progress(
                        progress,
                        f"{ui.COLOR_SUCCESS}"
                        f"{format_label} completed",
                        history=True,
                    )

        except AnimationError:

            raise

        except Exception as error:

            raise AnimationError(
                f"Failed to process animation archive {zip_path.name!r}"
            ) from error

        return completed


# Alias della classe di conversione delle animazioni in GIF e WEBM
m3 = MultiMediaManager