from __future__ import annotations

from typing import Literal, TypedDict


class LoginFailedError(Exception):
    pass


class LoginCred(TypedDict):
    pixiv_id: str
    password: str

"""
class NextBookmarksRequest(TypedDict):
    user_id: str
    restrict: str
    filter: str
    max_bookmark_id: str


class NextFollowingsRequest(TypedDict):
    user_id: str
    restrict: str
    offset: str
"""


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
