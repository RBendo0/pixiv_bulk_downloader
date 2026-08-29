from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from pixivpy3.utils import JsonDict

from .const import (
    ARTWORK_METADATA_VERSION,
    AUTHOR_METADATA_VERSION,
)
from .iofile import JsonFile
from .pbd_types import (
    JsonCollection,
    MetadataPayload,
    MetadataState,
    MetadataType,
)


class PixivMetadata(ABC):

    _VERSION_CLASSES: ClassVar[dict[
        MetadataType,
        dict[int, type[PixivMetadata]],
    ]] = {}

    def __new__(  # noqa: PYI034
        cls,
        *,
        type: MetadataType,
        state: MetadataState = "",
        data: JsonDict | None = None,
    ) -> PixivMetadata:

        if cls is PixivMetadata:

            version = (
                ARTWORK_METADATA_VERSION["CURRENT"]
                if type == "artwork"
                else AUTHOR_METADATA_VERSION["CURRENT"]
            )

            version_class = cls._get_version_class(
                type,
                version,
            )

            return object.__new__(
                version_class
            )

        return object.__new__(cls)

    @classmethod
    def _get_version_class(
        cls,
        type: MetadataType,
        version: int,
    ) -> type[PixivMetadata]:

        type_versions = cls._VERSION_CLASSES.get(
            type
        )

        if type_versions is None:
            raise KeyError(
                f"Unsupported metadata type: {type}"
            )

        version_class = type_versions.get(
            version
        )

        if version_class is None:
            raise KeyError(
                f"Unsupported {type} metadata version: {version}"
            )

        return version_class

    def __init__(
        self,
        *,
        type: MetadataType,
        state: MetadataState = "",
        data: JsonDict | None = None,
    ) -> None:

        version = (
            ARTWORK_METADATA_VERSION["CURRENT"]
            if type == "artwork"
            else AUTHOR_METADATA_VERSION["CURRENT"]
        )

        self._collection: JsonCollection = {
            "header": {
                "type": type,
                "version": version,
                "timestamp": "",
                "state": state,
            }
        }

        if data is not None:

            payload: MetadataPayload = (
                "illust"
                if type == "artwork"
                else "author"
            )

            self.add(
                payload=payload,
                data=data,
            )

    def from_json(
        self,
        data: JsonDict,
    ) -> None:

        self._collection["metadata"] = data

    def add(
        self,
        *,
        payload: MetadataPayload,
        data: JsonDict,
    ) -> None:

        match payload:

            case "illust":
                formatted_data = self.type_illust(data)

            case "author":
                formatted_data = self.type_author(data)

            case "ugoira":
                formatted_data = self.type_ugoira(data)

        self._collection.update(
            formatted_data
        )

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

        version_class = cls._get_version_class(
            collection["header"]["type"],
            collection["header"]["version"],
        )

        obj = object.__new__(
            version_class
        )

        obj._collection = collection

        return obj

    @property
    def version(self) -> int:
        return self._collection["header"]["version"]

    @property
    def type(self) -> MetadataType:
        return self._collection["header"]["type"]

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
    # Formatter
    # -------------------------------------------------------------------------

    @abstractmethod
    def type_illust(
        self,
        data: JsonDict,
    ) -> JsonDict:
        ...

    @abstractmethod
    def type_author(
        self,
        data: JsonDict,
    ) -> JsonDict:
        ...

    @abstractmethod
    def type_ugoira(
        self,
        data: JsonDict,
    ) -> JsonDict:
        ...

    # -------------------------------------------------------------------------
    # Artwork
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def artw_id(self) -> int:
        ...

    @abstractmethod
    def artw_title(
        self,
        for_path: bool = False,
    ) -> str:
        ...

    @property
    @abstractmethod
    def artw_type(self) -> str:
        ...

    @property
    @abstractmethod
    def artw_is_illust(self) -> bool:
        ...

    @property
    @abstractmethod
    def artw_is_manga(self) -> bool:
        ...

    @property
    @abstractmethod
    def artw_is_ugoira(self) -> bool:
        ...

    @abstractmethod
    def artw_get_links(self) -> list[str]:
        ...

    @abstractmethod
    def ugoira_zip_url(self) -> str:
        ...

    @abstractmethod
    def ugoira_frames(self) -> list[JsonDict]:
        ...        

    # -------------------------------------------------------------------------
    # Author
    # -------------------------------------------------------------------------

    @property
    @abstractmethod
    def author_id(self) -> int:
        ...

    @abstractmethod
    def author_name(
        self,
        for_path: bool = False,
    ) -> str:
        ...


class PixivMetadataV1(PixivMetadata):

    def type_illust(
        self,
        data: JsonDict,
    ) -> JsonDict:

        return {    # pyright: ignore[reportReturnType]
            "metadata": {
                "illust": data,
            }
        }

    def type_author(
        self,
        data: JsonDict,
    ) -> JsonDict:

        return {    # pyright: ignore[reportReturnType]
            "metadata": data,
        }

    def type_ugoira(
        self,
        data: JsonDict,
    ) -> JsonDict:

        return {    # pyright: ignore[reportReturnType]
            "ugoira": data,
        }

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

    def ugoira_zip_url(self) -> str:
        return self._collection[
            "ugoira"
        ][
            "ugoira_metadata"
        ][
            "zip_urls"
        ][
            "medium"
        ]

    def ugoira_frames(self) -> list[JsonDict]:
        return self._collection[
            "ugoira"
        ][
            "ugoira_metadata"
        ][
            "frames"
        ]

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


PixivMetadata._VERSION_CLASSES = {
    "artwork": {
        1: PixivMetadataV1,
    },
    "author": {
        1: PixivMetadataV1,
    },
}