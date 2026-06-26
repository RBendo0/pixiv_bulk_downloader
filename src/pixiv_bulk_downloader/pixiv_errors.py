import time

from .timing import (
    MENU_TIMEOUT,
    RATE_LIMIT_WAIT,
)
from .ui import ui


class PixivDownloaderError(Exception):
    """
    Classe base per tutte le eccezioni del downloader.
    """
    pass


class PixivApiError(PixivDownloaderError):
    """
    Errore durante comunicazione o elaborazione
    di una risposta proveniente dalle API Pixiv.
    """
    pass


class RateLimitError(PixivApiError):
    pass


class StorageError(PixivDownloaderError):
    """
    Errore durante accesso al filesystem,
    gestione checkpoint o serializzazione dati.
    """
    pass


def prompt_error_menu(
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


def is_rate_limited(page) -> bool:

    if page is None:
        return False

    if "error" in page:
        error = page["error"]
        if error.get("message") == "Rate Limit":
            return True

    return False


def wait_rate_limit(
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