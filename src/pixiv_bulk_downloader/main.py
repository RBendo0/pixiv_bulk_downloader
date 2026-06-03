from __future__ import annotations

import os

from pathlib import Path
from typing import TYPE_CHECKING

import pwinput  # type: ignore[import-untyped]
from .my_gppt import PixivAuth

from .bookmarks import PixivBookmarksDownloader
from .followings import PixivFollowingsDownloader
from .pixiv_types import LoginFailedError
from .const import BOOKMARK_LIST_FILE
from .const import BOOKMARKS_DIR

if TYPE_CHECKING:
    from pixivpy3.aapi import AppPixivAPI

SAVE_DIR = Path(os.getenv("SAVE_DIR", Path.home() / "pbd"))
"""client.json
{
  'pixiv_id' : '<change this>',
  'password' : '<change this>'
}
"""

def interact(
    aapi: AppPixivAPI,
    f: PixivFollowingsDownloader,
    b: PixivBookmarksDownloader,
) -> None:

    def getch() -> str:
        c = pwinput.getch()
        print()
        return c.decode(errors="ignore")

    actions = {
        "1": b.get_all_bookmarked_works,
        "2": lambda: b.get_all_bookmarked_works("missing"),
        "3": lambda: b.get_all_bookmarked_works("chrono"),
        "4": lambda: b.resume_pending_jobs(BOOKMARKS_DIR),
        "5": lambda: b.add_list_to_bookmarks(BOOKMARK_LIST_FILE),
        "6": b.convert_bookmarks_to_private,
    }

    while True:

        print(
            "========================\n"
            " Pixiv Bulk Downloader\n"
            "========================\n"
            "\n"
            "[1] Scarica tutti i preferiti sull'archivio locale\n"
            "[2] Scarica preferiti non ancora salvati in locale\n"
            "[3] Scarica gli ultimi preferiti aggiunti di recente\n"
            "[4] Riprendi scaricamenti lasciati in sospeso\n"
            "[5] Aggiungi preferiti all'account da una lista di url\n"
            "[6] Converti preferiti in privati\n"
            "\n"
            "[0] Esci\n"
            "\n"
            "CTRL+C = Interrompe esecuzione\n"
        )

        c = getch()

        if c == "0":
            break

        action = actions.get(c)

        if action is None:
            print("[!]: Invalid selection.")
            continue

        action()

        print("[+]: Finish!")

def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    f = PixivFollowingsDownloader(aapi, login_info, SAVE_DIR)
    b = PixivBookmarksDownloader(aapi, login_info, SAVE_DIR)
#   if "-y" in sys.argv:
#       f.get_all_following_works()
#       print("\033[K[+]: Finish!")
#       b.get_all_bookmarked_works()
#       print("\033[K[+]: Finish!")
#   else:
#       interact(aapi, f, b)
    interact(aapi, f, b)


def main() -> None:
    try:
        _main()
    except (KeyError, LoginFailedError):
        print("\n[!]: Request limit seem to be exceeded. Try again later.")
    except KeyboardInterrupt:
        print("\n[!]: SIGINT")
    finally:
        print("\x1b[?25h", end="")


if __name__ == "__main__":
    main()
