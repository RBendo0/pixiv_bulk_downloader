import time
from enum import Enum, auto
from http.client import RemoteDisconnected

from .timing import (
    MENU_TIMEOUT,
    RATE_LIMIT_WAIT,
)
from .ui import ui


class RecoveryControl(Exception):

    class Action(Enum):
        ABORT = auto()
        RETRY = auto()
        CONTINUE = auto()

    @classmethod
    def wait_rate_limit(
        cls, 
        seconds: int = RATE_LIMIT_WAIT,
    ) -> Action:

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
                    return cls.Action.ABORT

                time.sleep(0.05)

        ui.clear_lines(0)

        return cls.Action.RETRY

    @classmethod
    def prompt_error_menu(
        cls,
        options: dict[str, str],
        valid: str,
        default: str = "",
        timeout: int = MENU_TIMEOUT,
    ) -> Action:

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

        return {
            "A": cls.Action.ABORT,
            "R": cls.Action.RETRY,
            "C": cls.Action.CONTINUE,
        }[choice]

    class Abort(Exception):
        pass

    class Retry(Exception):
        pass

    class Continue(Exception):
        pass


# Alias statico delle classe di controllo del flusso per l'uso in tutto il programma.
rcc = RecoveryControl


# Classe base interna per tutte le eccezioni gestite da PBD.
class PBDError(Exception):

    @classmethod
    def info(cls) -> str:

        return "Operation failed"

    @classmethod
    def hierarchy(cls, e: Exception) -> "PBDError":

        if isinstance(e, PBDError):
            return e

        return PBDError(str(e))

    @classmethod
    def cast(cls, e: Exception) -> "PBDError":

        return PBDError(str(e))


class ApiError(PBDError):

    @classmethod
    def info(cls) -> str:

        return "API call failed"


class PageNotFoundError(ApiError):

    @classmethod
    def info(cls) -> str:

        return "Page not found"    

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
    pass
    

class ApiRateLimitError(RateLimitError):

    @classmethod
    def info(cls) -> str:

        return "API Request Limit Reached"    

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
    def info(cls) -> str:

        return "Download Request Limit Reached"    

    @classmethod
    def is_remote_disconnected(cls, exc: BaseException) -> bool:

        current: BaseException | None = exc

        while current is not None:

            if isinstance(current, RemoteDisconnected):
                return True

            current = current.__cause__ or current.__context__

        return False