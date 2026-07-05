import time
from enum import Enum, auto
from http.client import RemoteDisconnected

from .timing import (
    MENU_TIMEOUT,
    RATE_LIMIT_WAIT,
)
from .ui import ui

# P = ParamSpec("P")
# R = TypeVar("R")


class ContinueShortcut(Exception):
    """
    Eccezione di controllo del flusso utilizzata per
    interrompere l'elaborazione dell'opera corrente e
    passare direttamente a quella successiva.
    """
    pass


class RecoveryControl(Exception):

    class Action(Enum):
        ABORT = auto()
        RETRY = auto()
        CONTINUE = auto()


class Abort(RecoveryControl):
    pass


class Retry(RecoveryControl):
    pass


class Continue(RecoveryControl):
    pass


# Classe base interna per tutte le eccezioni gestite da PBD.
class PBDError(Exception):

    @classmethod
    def hierarchy(cls, e: Exception) -> "PBDError":

        if isinstance(e, PBDError):
            return e

        return PBDError(str(e))

    @classmethod
    def cast(cls, e: Exception) -> "PBDError":

        return PBDError(str(e))

    def _error_menu(
        self,
        options: dict[str, str],
        valid: str,
        default: str = "",
        timeout: int = MENU_TIMEOUT,
    ) -> str:

        menu_lines = ui.menu(
            title="",
            options=options,
            top_margin=1,
        )

        choice = ui.input_key(
            valid=valid,
            default=default,
            timeout=timeout,
        )

        ui.clear_lines(menu_lines + 1)

        return choice
    
    def handle(self) -> RecoveryControl.Action:

        action = self._error_menu(
            {
                "A": "Abort",
                "R": "Retry",
                "C": "Continue",
            },
            valid="ARC",
            default="C",
        )

        return {
            "A": RecoveryControl.Action.ABORT,
            "R": RecoveryControl.Action.RETRY,
            "C": RecoveryControl.Action.CONTINUE,
        }[action]


class ApiError(PBDError):

    pass


class PageNotFoundError(ApiError):

    @classmethod
    def is_page_not_found(cls, page) -> bool:

        if page is None:
            return False

        if "error" in page:
            error = page["error"]
            if error.get("user_message") == "Page not found":
                return True

        return False


class RateLimitError(ApiError):

    def _wait_rate_limit(
        self, 
        seconds: int = RATE_LIMIT_WAIT,
    ) -> bool:

        ui.line()

        for remaining in range(
            seconds,
            0,
            -1,
        ):

            ui.line(
                f"[!]: Access limited. "
                f"Retry in {remaining}s "
                f"[A] Abort",
                history=False, 
            )

            start = time.time()

            while (
                time.time() - start
                < 1.0
            ):

                key = ui.poll_key("A")

                if key == "A":
        
                    ui.clear_lines(0)
        
                    return False

                time.sleep(0.05)

        ui.clear_lines(0)

        return True

    def handle(self) -> RecoveryControl.Action:

        if self._wait_rate_limit():
            return RecoveryControl.Action.RETRY

        return RecoveryControl.Action.ABORT
    

class ApiRateLimitError(RateLimitError):

    @classmethod
    def is_rate_limited(cls, page) -> bool:

        if page is None:
            return False

        if "error" in page:
            error = page["error"]
            if error.get("message") == "Rate Limit":
                return True

        return False


class DownloadRateLimitError(RateLimitError):

    @classmethod
    def is_remote_disconnected(cls, exc: BaseException) -> bool:

        current: BaseException | None = exc

        while current is not None:

            if isinstance(current, RemoteDisconnected):
                return True

            current = current.__cause__ or current.__context__

        return False