from __future__ import annotations

import json
import re
from pathlib import Path

from pixivpy3.utils import JsonDict

from .pbd_types import JsonCollection


class PixivMetadata:

    def __init__(
        self,
        data: JsonDict | None = None,
    ) -> None:

        self._collection: JsonCollection = {}

        if data is not None:
            self._collection["metadata"] = data

    def from_json(
        self,
        data: JsonDict,
    ) -> None:

        self._collection["metadata"] = data

    def add(
        self,
        name: str,
        data: JsonDict,
    ) -> None:

        self._collection[name] = data

    def get(
        self,
        name: str,
    ) -> JsonDict:

        return self._collection[name]

    def to_dict(
        self,
    ) -> JsonCollection:

        return self._collection    

    def save(
        self,
        path: Path,
    ) -> None:

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self._collection,
                file,
                indent=4,
                ensure_ascii=False,
                default=str,
            )

    def load(
        self,
        path: Path,
    ) -> None:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self._collection = json.load(file)

    @property
    def id(self) -> int:
        return self._collection["metadata"]["id"]

    @property
    def title(self) -> str:
        return self._collection["metadata"]["title"]
    
    @property
    def path_title(self) -> str:

        title = re.sub(
            r'[\\/:*?"<>|]',
            "_",
            self.title,
        )

        # Windows non consente nomi che terminano
        # con spazi o punti.
        return title.rstrip(" .")    

    @property
    def type(self) -> str:
        return self._collection["metadata"]["type"]

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

        for page in self._collection["metadata"]["meta_pages"]:
            links.append(page["image_urls"]["original"])

        if links:
            return links

        return [
            self._collection["metadata"]["meta_single_page"].get(
                "original_image_url",
                self._collection["metadata"]["image_urls"]["large"],
            )
        ]

