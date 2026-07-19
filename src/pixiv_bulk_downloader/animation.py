from .pbd_types import AnimationFrame


WEBM_ENCODERS = {
    "vp8": "libvpx",
    "vp9": "libvpx-vp9",
    "av1": "libaom-av1",
}


class AnimationConverter:

    @classmethod
    def config_webm_codec(cls) -> None:
        pass

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
animat = AnimationConverter