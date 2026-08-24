from __future__ import annotations

import asyncio
import re
from base64 import urlsafe_b64encode
from hashlib import sha256
from secrets import token_urlsafe
from typing import TYPE_CHECKING, Final
from urllib.parse import urlencode

import requests
from pixivpy3 import AppPixivAPI
from playwright.async_api import Request, async_playwright

from .const import PROFILE_DIR

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page
    from playwright.async_api._generated import Playwright as AsyncPlaywright


class PixivLogin:

    LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
    REDIRECT_URI = "https://accounts.pixiv.net/post-redirect"

    CALLBACK_URI: Final[str] = (
        "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
    )

    AUTH_TOKEN_URL: Final[str] = (
        "https://oauth.secure.pixiv.net/auth/token"
    )

    CLIENT_ID: Final[str] = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
    CLIENT_SECRET: Final[str] = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

    USER_AGENT: Final[str] = (
        "PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)"
    )

    TIMEOUT: Final[float] = 10.0

    def __init__(self) -> None:
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.code: str | None = None

    @staticmethod
    def _oauth_pkce() -> tuple[str, str]:

        def s256(data: bytes) -> str:
            encoded = urlsafe_b64encode(
                sha256(data).digest()
            ).rstrip(b"=")

            return encoded.decode("ascii")

        code_verifier = token_urlsafe(32)
        code_challenge = s256(
            code_verifier.encode("ascii")
        )

        return code_verifier, code_challenge

    async def _capture_oauth_code(
        self,
        request: Request,
    ) -> None:

        if not request.url.startswith("pixiv://"):
            return

        match = re.search(r"code=([^&]*)", request.url)

        if match:
            self.code = match.group(1)

    async def _open_browser(
        self,
        playwright: AsyncPlaywright,
    ) -> None:

        self.context = await playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            chromium_sandbox=True,
            args=[
                "--start-maximized",
            ],
        )

        if not self.context.pages:
            raise RuntimeError(
                "Chrome persistent context has no available page."
            )

        self.page = self.context.pages[0]

        self.code = None
        self.page.on("request", self._capture_oauth_code)

    async def _open_login_page(
        self,
        code_challenge: str,
    ) -> None:

        if self.page is None:
            raise RuntimeError("Chrome page is not available.")

        login_params = {
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "client": "pixiv-android",
        }

        await self.page.goto(
            f"{self.LOGIN_URL}?{urlencode(login_params)}"
        )        


    async def _wait_for_redirect(self) -> None:

        if self.page is None:
            raise RuntimeError("Chrome page is not available.")

        await self.page.wait_for_url(
            re.compile(
                f"^{re.escape(self.REDIRECT_URI)}"
            ),
            wait_until="networkidle",
            timeout=60000,
        )


    async def _wait_for_redirect(self) -> None:

        if self.page is None:
            raise RuntimeError("Chrome page is not available.")

        await self.page.wait_for_url(
            re.compile(
                f"^{re.escape(self.REDIRECT_URI)}"
            ),
            wait_until="networkidle",
            timeout=60000,
        )

    async def _browser_login(self) -> str:

        code_verifier, code_challenge = self._oauth_pkce()

        async with async_playwright() as playwright:

            await self._open_browser(playwright)

            try:
                await self._open_login_page(code_challenge)
                await self._wait_for_redirect()

                if self.page is None:
                    raise RuntimeError(
                        "Chrome page is not available."
                    )

                await self.page.wait_for_timeout(1000)

                if self.code is None:
                    raise RuntimeError(
                        "Pixiv OAuth code was not captured."
                    )

            finally:
                if self.context is not None:
                    await self.context.close()

        return code_verifier     

    def _get_refresh_token(
        self,
        code_verifier: str,
    ) -> str:

        if self.code is None:
            raise RuntimeError(
                "Pixiv OAuth code is not available."
            )

        response = requests.post(
            self.AUTH_TOKEN_URL,
            data={
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "code": self.code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "include_policy": "true",
                "redirect_uri": self.CALLBACK_URI,
            },
            headers={
                "user-agent": self.USER_AGENT,
                "app-os-version": "14.6",
                "app-os": "ios",
            },
            timeout=self.TIMEOUT,
        )

        return response.json()["refresh_token"]       

    def login(self) -> AppPixivAPI:

        code_verifier = asyncio.run(
            self._browser_login()
        )

        refresh_token = self._get_refresh_token(
            code_verifier
        )

        aapi = AppPixivAPI()
        aapi.auth(
            refresh_token=refresh_token
        )

        return aapi    