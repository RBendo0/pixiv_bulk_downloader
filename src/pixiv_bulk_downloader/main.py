from __future__ import annotations

from .bookmarks import PixivBookmarksDownloader
from .const import BOOKMARK_LIST_FILE, BOOKMARKS_DIR, PBD_ROOT
from .my_gppt import PixivAuth
from .pixiv_types import LoginFailedError
from .test import runtest8
from .ui import ui


def interact(
    b: PixivBookmarksDownloader,
) -> None:

    actions = {
        "1": b.download_bookmarks,
        "2": lambda: b.resume_pending_jobs(BOOKMARKS_DIR),
        "3": lambda: b.add_list_to_bookmarks(BOOKMARK_LIST_FILE),
        "4": b.convert_bookmarks_to_private,
    }

    while True:

        choice = ui.main_menu(
            title="Pixiv Bulk Downloader",
            options={
                "1": "Scarica i preferiti sull'archivio locale",
                "2": "Riprendi scaricamenti lasciati in sospeso",
                "3": "Aggiungi preferiti da una lista di url",
                "4": "Cambia profilo di privacy ai preferiti",
                "0": "Esci",
            },
            footer="[T]: Debugger - [CTRL+C]: Termina",
            top_margin=4,
            prompt=(
                "[?] Inserire il carattere "
                "corrispondente alla scelta desiderata:"
            ),
            validate="01234T",
        )        

        if choice == "0":
            break
        elif choice == "T":
            # inserire in questa riga eventuali routine di test
            continue
        
        action = actions[choice]
        action()

        ui.line("[+]: Finish!")


def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    b = PixivBookmarksDownloader(aapi, login_info, PBD_ROOT)
    interact(b)


def main() -> None:
    try:

        _main()

    except (KeyError, LoginFailedError):

        ui.line(
            "[!]: Request limit seem to be exceeded. "
            "Try again later.",
            ui.COLOR_ERROR,
        )        

    except KeyboardInterrupt:

        ui.line(
            "[!]: SIGINT",
            ui.COLOR_ERROR,
        )

    finally:
        print("\x1b[?25h", end="")


if __name__ == "__main__":
    # main()
    # graph()
    # bucks()
    # pathtest()
    runtest8()