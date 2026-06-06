from pathlib import Path

_BasePath = type(Path())


class PixivPath(_BasePath):

    _ID_FORK_000 = 125_000_000

    def work_dir(
        self,
        id_: int,
        title: str | None = None,
    ) -> "PixivPath":
        raise NotImplementedError

    def _get_bucket(
        self,
        id_: int,
    ) -> str:
        raise NotImplementedError