from __future__ import annotations

# import os
# from typing import TYPE_CHECKING
from .bookmarks import PixivBookmarksDownloader
from .const import BOOKMARK_LIST_FILE, BOOKMARKS_DIR, PBD_ROOT
from .my_gppt import PixivAuth
from .pixiv_types import LoginFailedError
from .test import runtest7
from .ui import ui

# if TYPE_CHECKING:
#     from pixivpy3.aapi import AppPixivAPI


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

        # os.system("cls")

        ui.menu(
            title="Pixiv Bulk Downloader",
            options={
                "1": "Scarica i preferiti sull'archivio locale",
                "2": "Riprendi scaricamenti lasciati in sospeso",
                "3": "Aggiungi preferiti da una lista di url",
                "4": "Cambia profilo di privacy ai preferiti",
                "0": "Esci",
                "T": "Test",
            },
            footer="CTRL+C = Interrompe esecuzione",
            top_margin=4,
        )        

        c = ui.input_key(
            prompt=(
                "[?] Inserire il carattere "
                "corrispondente alla scelta desiderata:"
            ),
            valid="01234T",
        )

        if c == "0":
            break
        elif c == "T":
            # inserire in questa riga eventuali routine di test
            continue
        
        action = actions[c]
        action()

        ui.message("[+]: Finish!")


def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    b = PixivBookmarksDownloader(aapi, login_info, PBD_ROOT)
    interact(b)
    
    """
    # Esecuzione diretta senza interazione, per test rapidi
    if "-y" in sys.argv:
        f.get_all_following_works()
        print("\033[K[+]: Finish!")
        b.get_all_bookmarked_works()
        print("\033[K[+]: Finish!")
    else:
        interact(aapi, f, b)
    """ 


def main() -> None:
    try:

        _main()

    except (KeyError, LoginFailedError):

        ui.message(
            "[!]: Request limit seem to be exceeded. "
            "Try again later.",
            ui.COLOR_ERROR,
        )        

    except KeyboardInterrupt:

        ui.message(
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
    runtest7()