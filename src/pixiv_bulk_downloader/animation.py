from dataclasses import asdict, replace

from .config import config
from .const import (
    ADVANCED_KEY_MP4_CODEC,
    ADVANCED_KEY_WEBM_CODEC,
    CONFIG_KEY_PREF_MEDIA,
    DEFAULT_CODEC_SETTINGS,
    DEFAULT_PREFERRED_MEDIA_FORMATS,
)
from .pbd_types import (
    AnimationFrame,
    CodecSettings,
    PreferredMediaFormats,
    ToggleOption,
)
from .ui import ui

WEBM_ENCODERS = {
    "vp8": "libvpx",
    "vp9": "libvpx-vp9",
    "av1": "libaom-av1",
}


class MultiMediaManager:

    _preferred_media_formats: PreferredMediaFormats = replace(DEFAULT_PREFERRED_MEDIA_FORMATS)

    _codec: CodecSettings = replace(DEFAULT_CODEC_SETTINGS) 

    @classmethod
    def _load_preferred_media_formats(cls) -> None:

        cls._preferred_media_formats = replace(DEFAULT_PREFERRED_MEDIA_FORMATS)

        preferred_media_formats = config.load(
            CONFIG_KEY_PREF_MEDIA
        )

        if (
            isinstance(preferred_media_formats, dict)
            and any(preferred_media_formats)
        ):

            cls._preferred_media_formats = PreferredMediaFormats(
                **preferred_media_formats
            )

    @classmethod
    def _load_media_codecs(cls) -> None:

        cls._codec = replace(DEFAULT_CODEC_SETTINGS) 

        webm_codec = config.Advanced.load(
            ADVANCED_KEY_WEBM_CODEC
        )

        mp4_codec = config.Advanced.load(
            ADVANCED_KEY_MP4_CODEC
        )

        if (
            isinstance(webm_codec, str)
            and webm_codec
        ):

            cls._codec.webm = webm_codec

        if (
            isinstance(mp4_codec, str)
            and mp4_codec
        ):

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
        ui.line("[i]: Selezionare i singoli formati di salvataggio delle animazioni")
        ui.line("[i]: premendo il tasto del numero associato alla rispettiva voce menu.")
        ui.line("[i]: Nessuna selezione imposta formati di default")
        ui.line("[i]: [SPAZIO] ripristina impostazioni precedenti")
        ui.line("[i]: [INVIO] per confermare")
        ui.line()
        
        options = cls._pmfs_to_togo(
            cls._preferred_media_formats
        )

        options = ui.toggle_menu(
            options,
        )

        cls._preferred_media_formats = cls._togo_to_pmfs(
            options
        )

        config.save(
            CONFIG_KEY_PREF_MEDIA,
            asdict(cls._preferred_media_formats),
        )

        ui.clear_lines(6)

        cls.init()

    @classmethod
    def load_images(cls):
        pass

    @classmethod
    def build_frames(cls):
        pass

    @classmethod
    def to_gif(cls):
        pass

    @classmethod
    def to_webm(cls):
        pass


# Alias della classe di conversione delle animazioni in GIF e WEBM
m3 = MultiMediaManager