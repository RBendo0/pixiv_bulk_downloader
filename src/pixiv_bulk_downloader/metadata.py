from __future__ import annotations

import re

from pixivpy3.utils import JsonDict

#if TYPE_CHECKING:
#    from pixivpy3.utils import JsonDict


class PixivMetadata:

    def __init__(
        self,
        data: JsonDict | None = None,
    ) -> None:

        self._data: JsonDict = JsonDict()

        if data is not None:
            self._data = data

    def from_json(
        self,
        data: JsonDict,
    ) -> None:
        self._data = data

    def to_dict(self) -> JsonDict | None:
        return self._data

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def title(self) -> str:
        return self._data["title"]
    
    @property
    def path_title(self) -> str:

        return re.sub(
            r'[\\/:*?"<>|]',
            "_",
            self.title,
        )
    
    @property
    def type(self) -> str:
        return self._data["type"]

    @property
    def is_illust(self) -> bool:
        return self.type == "illust"

    @property
    def is_manga(self) -> bool:
        return self.type == "manga"

    @property
    def is_ugoira(self) -> bool:
        return self.type == "ugoira"

    def get_links(self) -> list[str]:
        """
        Restituisce sempre una lista di URL.
        """

        links: list[str] = []

        for page in self._data["meta_pages"]:
            links.append(page["image_urls"]["original"])

        if links:
            return links

        return [
            self._data["meta_single_page"].get(
                "original_image_url",
                self._data["image_urls"]["large"],
            )
        ]

