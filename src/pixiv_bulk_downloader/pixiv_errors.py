import msvcrt
import time

from .timing import (
    MENU_TIMEOUT,
    RATE_LIMIT_WAIT,
)


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
    actions: dict[str, str],
    default_action: str | None = None,
    timeout: int = MENU_TIMEOUT,
) -> str:

    valid_actions = {
        key.upper(): value
        for key, value in actions.items()
    }

    if default_action is not None:

        default_action = default_action.upper()

        if default_action not in valid_actions:
            raise ValueError(
                f"Invalid default action: {default_action}"
            )

    menu_lines = len(valid_actions) + 1    # ... + 1 ?

    for key, label in valid_actions.items():
        print(f"[{key}] {label}")

    # Nessuna scelta automatica
    if default_action is None:

        while True:

            choice = (
                input("Choice: ")
                .strip()
                .upper()
            )

            if choice in valid_actions:

                for _ in range(menu_lines):
                    print("\033[A\033[K", end="")

                return choice

            print("[!]: Invalid selection.")

    # Scelta automatica abilitata
    selected_action = None

    print()

    for remaining in range(
        timeout,
        0,
        -1,
    ):

        print(
            f"\rAuto {valid_actions[default_action]} "
            f"in {remaining}s",
            end="",
            flush=True,
        )

        start = time.time()

        while (
            time.time() - start
            < 1.0
        ):

            if msvcrt.kbhit():

                key = (
                    msvcrt.getch()
                    .decode(
                        "utf-8",
                        errors="ignore",
                    )
                    .upper()
                )

                if key in valid_actions:

                    selected_action = key
                    break

            time.sleep(0.05)

        if selected_action is not None:
            break

    if selected_action is None:
        selected_action = default_action

    # Cancella countdown
    print("\r\033[K", end="")

    # Cancella menu
    for _ in range(menu_lines):
        print("\033[A\033[K", end="")

    return selected_action


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

    print()

    for remaining in range(
        seconds,
        0,
        -1,
    ):

        print(
            f"\r[!]: Access limited. "
            f"Retry in {remaining}s "
            f"[A] Abort",
            end="",
            flush=True,
        )

        start = time.time()

        while (
            time.time() - start
            < 1.0
        ):

            if msvcrt.kbhit():

                key = (
                    msvcrt.getch()
                    .decode(
                        "utf-8",
                        errors="ignore",
                    )
                    .upper()
                )

                if key == "A":

                    print("\r\033[K", end="")
                    return False

            time.sleep(0.05)

    print("\r\033[K", end="")

    return True