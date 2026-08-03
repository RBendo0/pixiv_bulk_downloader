import zipfile
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path

from .config import config
from .const import (
    ADVANCED_KEY_MP4_CODEC,
    ADVANCED_KEY_WEBM_CODEC,
    CONFIG_KEY_PREF_MEDIA,
    DEFAULT_CODEC_SETTINGS,
    DEFAULT_PREFERRED_MEDIA_FORMATS,
    FFMPEG_ENCODERS,
)
from .encoder import Encoder, FrameSpec, MediaFormat
from .errors import (
    InvalidDataFormat,
    JsonError,
    PBDError,
    UserHasNotDefinedCustomConfiguration,
)
from .pbd_types import (
    AnimationFrame,
    CodecSettings,
    PreferredMediaFormats,
    ToggleOption,
)
from .ui import ui


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

                raise PBDError.hierarchy(e) from e

        except UserHasNotDefinedCustomConfiguration:

            return

        except JsonError as e:

            ui.line(
                "[!]: Failed to load preferences about media formats.",
                ui.COLOR_ERROR,
            )

            ui.line(
                f"     {e.report()}",
                ui.COLOR_ERROR,
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
                raise InvalidDataFormat()

            else:
                return codec_setting

        except UserHasNotDefinedCustomConfiguration:

            pass

        except JsonError as e:

            ui.line(
                f"[!]: Failed to load [@@{key}@@.], "
                " codec will be set to default.",
                ui.COLOR_WARNING,
                tag_color=ui.COLOR_ERROR,
            )

            ui.line(
                f"     {e.report()}",
                ui.COLOR_ERROR,
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
        progress: str,
        zip_path: Path,
        frames: Sequence[FrameSpec],
    ) -> None:

        formats: list[
            tuple[
                MediaFormat,
                bool,
                str | None,
            ]
        ] = [
            (
                "gif",
                cls._preferred_media_formats.gif,
                None,
            ),
            (
                "webm",
                cls._preferred_media_formats.webm,
                cls._codec.webm,
            ),
            (
                "mp4",
                cls._preferred_media_formats.mp4,
                cls._codec.mp4,
            ),
        ]

        encoder = Encoder()

        frame_total = len(frames)
        frame_width = len(str(frame_total))

        completed_statuses: list[str] = []

        def write_progress(
            current_status: str = "",
        ) -> None:

            status_parts = [
                *completed_statuses,
            ]

            if current_status:
                status_parts.append(current_status)

            status_suffix = "".join(
                (
                    f"{ui.COLOR_DEFAULT}"
                    f" | "
                    f"{status}"
                )
                for status in status_parts
            )

            ui.Renderer.in_thread_write(
                progress + status_suffix
            )

        for (
            format_name,
            enabled,
            codec_symbol,
        ) in formats:

            if not enabled:
                continue

            format_label = format_name.upper()

            output_path = (
                zip_path.parent
                / f"a0.{format_name}"
            )

            try:

                codec = (
                    None
                    if codec_symbol is None
                    else FFMPEG_ENCODERS[codec_symbol]
                )

                encoder.start(
                    format_name=format_name,
                    output_path=output_path,
                    frames=frames,
                    codec=codec,
                )

                write_progress(
                    f"{ui.COLOR_INFO}"
                    f"Building {format_label} "
                    f"[{0:0{frame_width}d}/"
                    f"{frame_total:0{frame_width}d}] "
                    f"0%"
                )

                with zipfile.ZipFile(
                    zip_path,
                    "r",
                ) as archive:

                    archive_names = set(
                        archive.namelist()
                    )

                    for frame_index, frame in enumerate(
                        frames,
                        start=1,
                    ):

                        try:
                            frame_name = str(
                                frame["file"]
                            )

                        except (
                            KeyError,
                            TypeError,
                        ) as error:

                            raise ValueError(
                                "Nome del frame non valido "
                                f"all'indice {frame_index - 1}"
                            ) from error

                        if frame_name not in archive_names:

                            raise FileNotFoundError(
                                f"Frame {frame_name!r} "
                                f"non presente in {zip_path.name}"
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
                            f"{ui.COLOR_INFO}"
                            f"Building {format_label} "
                            f"[{frame_index:0{frame_width}d}/"
                            f"{frame_total:0{frame_width}d}] "
                            f"{percentage}%"
                        )

                encoder.stop()

            except Exception as error:

                # Se l'errore è avvenuto fuori da Encoder.add(),
                # per esempio durante la lettura dello ZIP, assicura
                # comunque la chiusura del processo FFmpeg.
                try:
                    encoder.stop()

                except Exception:
                    pass

                error = PBDError.cast(
                    error
                )

                write_progress(
                    f"{ui.COLOR_ERROR}"
                    f"{format_label} discarded: "
                    f"{error.report()}"
                )

                completed_statuses.append(
                    f"{ui.COLOR_ERROR}"
                    f"{format_label} discarded"
                )

                continue

            completed_statuses.append(
                f"{ui.COLOR_SUCCESS}"
                f"{format_label} completed"
            )

            write_progress()


# Alias della classe di conversione delle animazioni in GIF e WEBM
m3 = MultiMediaManager