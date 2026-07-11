from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict


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