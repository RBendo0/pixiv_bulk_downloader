from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypedDict

type JsonCollection = dict[str, Any]


MetadataType = Literal[
    "artwork",
    "author",
]


MetadataState = Literal[
    "",
    "pending",
    "complete",
]


MetadataPayload = Literal[
    "illust",
    "author",
    "ugoira",
]


class FrameSpec(TypedDict):
    file: str
    delay: int


@dataclass(frozen=True)
class MediaToolResult:
    code: int
    log_file: Path


class MetadataVersionDescriptor(TypedDict):
    LAST: int
    CURRENT: int


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


@dataclass
class ToggleOption:
    key: str
    label: str
    enabled: bool


@dataclass
class PreferredMediaFormats:
    gif: bool
    webm: bool
    mp4: bool

    def __iter__(self):
        return iter((
            self.gif,
            self.webm,
            self.mp4,
        ))


@dataclass
class CodecSettings:
    webm: str
    mp4: str