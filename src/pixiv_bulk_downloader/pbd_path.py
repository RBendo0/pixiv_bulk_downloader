import math
from pathlib import Path

_BasePath = type(Path())


class PixivPath(_BasePath):

    _GROUP_SIZE = 500

    _ID_FORK_000 = 125_000_000

    _N_MAX = 39_724
    _ID_MAX = 145_654_652

    _DENSITY_HYPE_A = 0.16223786
    _DENSITY_HYPE_B = 1.09912234
    _DENSITY_HYPE_SCALE = 3.0

    _DENSITY_STABLE = 550
    _BUCKET_GUARD_BAND = 1000
    
    # Il valore di questa variavile è calcolato mediante la formula 
    #   _HYPE_MAX_BUCKET = MAX(ID_GROUP_HYPE(0), ID_GROUP_HYPE(_ID_FORK_000))
    # dove ID_GROUP_HYPE() è la formula per calcolare il bucket nell'era hype
    _HYPE_MAX_BUCKET = 1_563_047

    _BUCKET_STABLE_OFFSET = (_HYPE_MAX_BUCKET + _BUCKET_GUARD_BAND)

    def _density_hype(
        self,
        id_: int,
    ) -> float:

        a = (
            self._DENSITY_HYPE_A
            * self._ID_MAX
        )

        b = (
            self._DENSITY_HYPE_B
            * self._ID_MAX
        )

        return (
            self._DENSITY_HYPE_SCALE
            * a
            / (
                self._N_MAX
                * math.exp(
                    (id_ - b)
                    / a
                )
            )
        )
    
    def _get_bucket(
        self,
        id_: int,
    ) -> str:

        if id_ < self._ID_FORK_000:

            bucket = int(
                id_
                / (
                    self._GROUP_SIZE
                    * self._density_hype(id_)
                )
            )

            return f"H_{bucket}"

        bucket = int(
            self._BUCKET_STABLE_OFFSET
            + (
                id_
                / (
                    self._GROUP_SIZE
                    * self._DENSITY_STABLE
                )
            )
        )

        return f"S_{bucket}"
    
    def work_dir(
        self,
        id_: int,
        title: str | None = None,
    ) -> "PixivPath":

        bucket = self._get_bucket(id_)

        folder_name = str(id_)

        if title is not None:
            folder_name += f"_{title}"

        return PixivPath(
            self / bucket / folder_name
        )
