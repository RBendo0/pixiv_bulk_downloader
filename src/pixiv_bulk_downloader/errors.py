import time
from enum import Enum, auto
from http.client import RemoteDisconnected
from math import ceil

from .debug import debug
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

    class RateLimitTimer:

        def __init__(
            self,
            seconds: float = RATE_LIMIT_WAIT,
        ) -> None:

            self._deadline = (
                time.monotonic()
                + max(0.0, seconds)
            )

        @property
        def remaining(self) -> int:

            return max(
                0,
                ceil(
                    self._deadline
                    - time.monotonic()
                ),
            )

        @property
        def expired(self) -> bool:

            return (
                time.monotonic()
                >= self._deadline
            )        

    @classmethod
    def wait_rate_limit(
        cls, 
        context: str = "",
        seconds: int = RATE_LIMIT_WAIT,
    ) -> Action:

        for remaining in range(
            seconds,
            0,
            -1,
        ):

            ui.line(
                f"{context}"
                f"{' | ' if context else ''}"
                f"@@Access limited. "
                f"Retry in {remaining}s "
                f"[A] Abort@@.",
                tag_color=ui.COLOR_WARNING,
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

    def report(
        self,
        *,
        with_message: bool = True,
    ) -> str:

        return (
            f"{self.info()}"
            + (f": {self}" if with_message and str(self) else "")
        )

    def notify(
        self,
        message: str,
        *,
        with_report: bool = False,
    ) -> None:

        with ui.suspend_thread_rendering():

            ui.line(
                f"[!]: {message}",
                ui.COLOR_ERROR,
                tag_color=ui.COLOR_WARNING,
            )

            if with_report:
                ui.line(
                    f"    {self.report()}",
                    ui.COLOR_ERROR,
                    tag_color=ui.COLOR_WARNING,
                )

            debug.DTB.log(
                self,
                f"{message} | {self.report()}"
            )

    @classmethod
    def hierarchy(cls, e: Exception) -> "PBDError":

        if isinstance(e, PBDError):
            return e

        if isinstance(e, FileNotFoundError):
            error = MissingFileError(str(e))

        elif isinstance(e, OSError):
            error = FileOperationError(str(e))

        elif isinstance(
            e,
            (
                KeyError,
                TypeError,
                ValueError,
            ),
        ):
            error = InvalidDataFormatError(str(e))

        else:
            error = PBDError(str(e))

        debug.DTB.inherit(error, e)

        return error

    @classmethod
    def cast(cls, e: Exception) -> "PBDError":

        error = PBDError(str(e))

        debug.DTB.inherit(error, e)

        return error


class ApiError(PBDError):

    @classmethod
    def info(cls) -> str:

        return "API call failed"


class LoginFailedError(ApiError):

    @classmethod
    def info(cls) -> str:

        return "Login failed"


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
    

class FileError(PBDError):

    @classmethod
    def info(cls) -> str:

        return "File I/O Error"


class MissingFileError(FileError):

    @classmethod
    def info(cls) -> str:

        return "File Not Found"


class FileOperationError(FileError):

    @classmethod
    def info(cls) -> str:

        return "Unable To Perform File Operation"


class InvalidDataFormatError(PBDError):

    @classmethod
    def info(cls) -> str:

        return "Invalid Data Format"


class ConfigError(PBDError):

    @classmethod
    def info(cls) -> str:
        return "Configuration Error"

    @classmethod
    def hierarchy(
        cls,
        e: Exception,
    ) -> PBDError:

        e = PBDError.hierarchy(e)

        if isinstance(
            e,
            MissingFileError,
        ):
            error = UserHasNotDefinedCustomConfiguration(
                str(e)
            )

            debug.DTB.inherit(error, e)

            return error

        return e

    
class UserHasNotDefinedCustomConfiguration(ConfigError):

    @classmethod
    def info(cls) -> str:

        return "User Has Not Defined Custom Configuration"


class AnimationError(PBDError):

    @classmethod
    def info(cls) -> str:

        return "Animation Error"


class EncoderError(AnimationError):

    @classmethod
    def info(cls) -> str:

        return "Encoder Error"


class MediaToolError(EncoderError):

    @classmethod
    def info(cls) -> str:

        return "FFmpeg Error"


class MediaToolExecutableError(MediaToolError):

    @classmethod
    def info(cls) -> str:

        return "FFmpeg Executable Error"

    @classmethod
    def hierarchy(
        cls,
        e: Exception,
    ) -> PBDError:

        if isinstance(e, OSError):
            error = cls(str(e))

            debug.DTB.inherit(error, e)

            return error

        return PBDError.hierarchy(e)


class MediaToolExecutionError(MediaToolError):

    @classmethod
    def info(cls) -> str:

        return "FFmpeg Execution Error"


class EncoderStreamError(EncoderError):

    @classmethod
    def info(cls) -> str:

        return "Encoder Stream Error"    

    @classmethod
    def hierarchy(
        cls,
        e: Exception,
    ) -> PBDError:

        e = PBDError.hierarchy(e)

        if isinstance(
            e,
            (
                FileError,
                InvalidDataFormatError,
            ),
        ):

            error = cls(str(e))

            debug.DTB.inherit(error, e)

            return error

        return e