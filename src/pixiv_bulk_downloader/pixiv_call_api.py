from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

from .errors import (
    ApiError,
    ApiRateLimitError,
    DownloadRateLimitError,
    PageNotFoundError,
    PBDError,
)

P = ParamSpec("P")
R = TypeVar("R")


class CallAAPI:

    def call_api(
        self,
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

    def call_download_api(
        self,
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

    def call_auth_api(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def auth(self, auth_provider, *args, **kwargs):
        return self.call_auth_api(auth_provider.auth, *args, **kwargs)

    def refresh(self, token_provider, *args, **kwargs):
        return self.call_auth_api(token_provider.refresh, *args, **kwargs)

    def parse_qs(self, aapi, *args, **kwargs):
        return aapi.parse_qs(*args, **kwargs)
    
    def user_id(self, aapi):
        return aapi.user_id

    def user_detail(self, aapi, *args, **kwargs):
        return self.call_api(aapi.user_detail, *args, **kwargs)

    def user_bookmarks_illust(self, aapi, *args, **kwargs):
        return self.call_api(aapi.user_bookmarks_illust, *args, **kwargs)

    def ugoira_metadata(self, aapi, *args, **kwargs):
        return self.call_api(aapi.ugoira_metadata, *args, **kwargs)

    def illust_bookmark_add(self, aapi, *args, **kwargs):
        return self.call_api(aapi.illust_bookmark_add, *args, **kwargs)

    def download(self, aapi, *args, **kwargs):
        return self.call_download_api(aapi.download, *args, **kwargs)


# Crea un'istanza globale dell'interfaccia
caapi = CallAAPI()