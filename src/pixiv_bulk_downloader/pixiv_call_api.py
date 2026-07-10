from __future__ import annotations

from collections.abc import Callable
from typing import (
    ParamSpec,
    TypeVar,
    cast,
)

from pixivpy3 import AppPixivAPI

from .errors import (
    ApiError,
    ApiRateLimitError,
    DownloadRateLimitError,
    PageNotFoundError,
)
from .my_gppt import LoginInfo, PixivAuth

P = ParamSpec("P")
R = TypeVar("R")


class CallAAPI:

    aapi: AppPixivAPI | None = None
    login_info: LoginInfo | None = None

    @classmethod
    def _aapi(cls) -> AppPixivAPI:
        return cast(AppPixivAPI, cls.aapi)

    @classmethod
    def open_session(cls) -> None:
        cls.aapi, cls.login_info = cls.auth(PixivAuth())

    @classmethod
    def call_api(
        cls,
        func: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:

        try:

            result = func(*args, **kwargs)

        except Exception as e:

            raise ApiError(str(e)) from e
        
        if (
            isinstance(result, dict)
            and ApiRateLimitError.is_rate_limited(result)
        ):
            raise ApiRateLimitError(
                "Pixiv API rate limit reached"
            )
        
        if (
            isinstance(result, dict)
            and PageNotFoundError.is_page_not_found(result)
        ):
            raise PageNotFoundError(
                "Pixiv resource not found"
            )

        return result

    @classmethod
    def call_download_api(
        cls,
        func: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:

        try:

            return func(*args, **kwargs)

        except Exception as e:

            if DownloadRateLimitError.is_remote_disconnected(e):
                raise DownloadRateLimitError(
                    "Remote server closed connection during download"
                ) from e

            raise ApiError(str(e)) from e

    @classmethod
    def call_auth_api(cls, func, *args, **kwargs):
        return func(*args, **kwargs)

    @classmethod
    def auth(cls, auth_provider, *args, **kwargs):
        return cls.call_auth_api(auth_provider.auth, *args, **kwargs)

    @classmethod
    def refresh(cls, token_provider, *args, **kwargs):
        return cls.call_auth_api(token_provider.refresh, *args, **kwargs)

    @classmethod
    def parse_qs(cls, *args, **kwargs):
        return cls._aapi().parse_qs(*args, **kwargs)

    @classmethod
    def user_id(cls):
        return cls._aapi().user_id
    
    @classmethod
    def user_detail(cls, *args, **kwargs):
        return cls.call_api(cls._aapi().user_detail, *args, **kwargs)

    @classmethod
    def user_bookmarks_illust(cls, *args, **kwargs):
        return cls.call_api(cls._aapi().user_bookmarks_illust, *args, **kwargs)

    @classmethod
    def ugoira_metadata(cls, *args, **kwargs):
        return cls.call_api(cls._aapi().ugoira_metadata, *args, **kwargs)

    @classmethod
    def illust_bookmark_add(cls, *args, **kwargs):
        return cls.call_api(cls._aapi().illust_bookmark_add, *args, **kwargs)

    @classmethod
    def download(cls, *args, **kwargs):
        return cls.call_download_api(cls._aapi().download, *args, **kwargs)


# Alias dell'interfaccia API PixivPy3
caapi = CallAAPI