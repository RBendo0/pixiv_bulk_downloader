from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from PIL.Image import Image
from pixivpy3.utils import JsonDict

type JsonCollection = dict[str, JsonDict]


class CommandLineOptions(TypedDict):
    root: Path | None


class LoginCred(TypedDict):
    pixiv_id: str
    password: str


BookmarkMode = Literal[
    "all",
    "missing",
    "chrono",
]


BookmarkPrivacy = Literal[
    "public",
    "private",
]


class BookmarkOptions(TypedDict):
    mode: BookmarkMode
    restrict: BookmarkPrivacy


class AddListOptions(TypedDict):
    source_files: list[Path]
    restrict: BookmarkPrivacy


@dataclass(frozen=True)
class AnimationFrame:
    image: "Image"
    delay: int