from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pixivpy3.utils import JsonDict

from .iofile import JsonFile
from .pbd_types import (
    JsonCollection,
    MetadataState,
    MetadataType,
)


class PixivMetadata:

    def __init__(
        self,
        *,
        type: MetadataType,
        state: MetadataState = "",
        data: JsonDict | None = None,
    ) -> None:

        self._collection: JsonCollection = {
            "header": {
                "type": type,
                "state": state,
                "timestamp": "",
            }
        }

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

        self._collection["header"]["timestamp"] = (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        )

        JsonFile(path).save(
            self._collection
        )

    @classmethod
    def from_file(
        cls,
        path: Path,
    ) -> PixivMetadata:

        collection = JsonFile(path).load()

        obj = cls(
            type=collection["header"]["type"],
            state=collection["header"]["state"],
        )

        obj._collection = collection

        return obj

    def load(
        self,
        path: Path,
    ) -> None:

        self._collection = JsonFile(path).load()

    @property
    def state(self) -> MetadataState:
        return self._collection["header"]["state"]

    @state.setter
    def state(
        self,
        value: MetadataState,
    ) -> None:

        self._collection["header"]["state"] = value

    @staticmethod
    def _normalize_for_path(
        value: str,
    ) -> str:

        value = re.sub(
            r'[\\/:*?"<>|]',
            "_",
            value,
        )

        # Windows non consente nomi che terminano
        # con spazi o punti.
        return value.rstrip(" .")

    # -------------------------------------------------------------------------
    # Common
    # -------------------------------------------------------------------------

    @property
    def has_error(self) -> bool:
        return "error" in self._collection["metadata"]

    # -------------------------------------------------------------------------
    # Artwork
    # -------------------------------------------------------------------------

    @property
    def artw_id(self) -> int:
        return self._collection["metadata"]["illust"]["id"]

    def artw_title(
        self,
        for_path: bool = False,
    ) -> str:

        title = self._collection["metadata"]["illust"]["title"]

        return (
            self._normalize_for_path(title)
            if for_path
            else title
        )

    @property
    def artw_type(self) -> str:
        return self._collection["metadata"]["illust"]["type"]

    @property
    def artw_is_illust(self) -> bool:
        return self.artw_type == "illust"

    @property
    def artw_is_manga(self) -> bool:
        return self.artw_type == "manga"

    @property
    def artw_is_ugoira(self) -> bool:
        return self.artw_type == "ugoira"

    def artw_get_links(self) -> list[str]:
        """
        Restituisce sempre una lista di URL.
        """

        links: list[str] = []

        for page in self._collection["metadata"]["illust"]["meta_pages"]:
            links.append(
                page["image_urls"]["original"]
            )

        if links:
            return links

        return [
            self._collection["metadata"]["illust"]["meta_single_page"].get(
                "original_image_url",
                self._collection["metadata"]["illust"]["image_urls"]["large"],
            )
        ]

    # -------------------------------------------------------------------------
    # Author
    # -------------------------------------------------------------------------

    @property
    def _author_data(self) -> JsonDict:

        metadata = self._collection["metadata"]

        return (
            metadata["illust"]["user"]
            if self._collection["header"]["type"] == "artwork"
            else metadata["user"]
        )

    @property
    def author_id(self) -> int:
        return self._author_data["id"]

    def author_name(
        self,
        for_path: bool = False,
    ) -> str:

        name = self._author_data["name"]

        return (
            self._normalize_for_path(name)
            if for_path
            else name
        )