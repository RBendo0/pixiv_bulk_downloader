from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pwinput  # type: ignore[import-untyped]

from .bookmarks import PixivBookmarksDownloader
from .const import BOOKMARK_LIST_FILE, BOOKMARKS_DIR
from .my_gppt import PixivAuth
from .pixiv_types import LoginFailedError

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

        #os.system("cls")

        print(
            "\n"
            "\n"            
            "\n"
            "\n"
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
            "[T] Test\n"
            "\n"
            "CTRL+C = Interrompe esecuzione\n"
        )

        c = getch()

        if c == "0":
            break
        elif c == "T":
            runtest3(aapi)
            continue
        
        action = actions.get(c)

        if action is None:
            print("[!]: Invalid selection.")
            continue

        action()

        print("[+]: Finish!")

def runtest3(aapi):
    user_id = aapi.user_id

    public = aapi.user_bookmarks_illust(
        user_id=user_id,
        restrict="public",
    )

    private = aapi.user_bookmarks_illust(
        user_id=user_id,
        restrict="private",
    )

    print(f"Public total : {public.total}")
    print(f"Private total: {private.total}")

    print(f"Public page items : {len(public.illusts)}")
    print(f"Private page items: {len(private.illusts)}") 

    print("Public IDs:")
    for illust in public.illusts[:5]:
        print(illust.id)

    print("Private IDs:")
    for illust in private.illusts[:5]:
        print(illust.id)  

    detail = aapi.user_detail(aapi.user_id)

    for key, value in detail["profile"].items():
        print(f"{key}: {value}")     
    
def runtest2(aapi) -> None:
    
    for name in dir(aapi):
        print(name)

# Rutine di test: eseguire qui tutte le porcate
def runtest1(aapi) -> None:

    test_dir = Path("test")
    test_dir.mkdir(exist_ok=True)

    found = {
        "illust": False,
        "manga": False,
        "ugoira": False,
    }

    res_json = aapi.user_bookmarks_illust(aapi.user_id)
    next_json = res_json

    while next_json is not None:

        res_json = next_json

        next_qs = aapi.parse_qs(res_json["next_url"])

        if next_qs is None:
            next_json = None
        else:
            next_json = aapi.user_bookmarks_illust(**next_qs)

        for illust in res_json["illusts"]:

            work_type = illust.type

            if work_type not in found:
                continue

            if found[work_type]:
                continue

            # Dump bookmark
            dump_file = test_dir / f"{work_type}_dump.json"

            with open(dump_file, "w", encoding="utf-8") as f:
                json.dump(
                    illust,
                    f,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            print(f"[+]: Salvato {dump_file}")

            # Dump illust_detail
            detail_file = test_dir / f"{work_type}_detail.json"

            detail = aapi.illust_detail(illust.id)

            with open(detail_file, "w", encoding="utf-8") as f:
                json.dump(
                    detail,
                    f,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            print(f"[+]: Salvato {detail_file}")

            # Dump ugoira_metadata
            if work_type == "ugoira":

                metadata_file = test_dir / "ugoira_metadata.json"

                metadata = aapi.ugoira_metadata(illust.id)

                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(
                        metadata,
                        f,
                        indent=4,
                        ensure_ascii=False,
                        default=str,
                    )

                print(f"[+]: Salvato {metadata_file}")

            found[work_type] = True

        if all(found.values()):
            break

    print("[+]: Test completato") 


def _main() -> None:
    aapi, login_info = PixivAuth().auth()
    b = PixivBookmarksDownloader(aapi, login_info, SAVE_DIR)
    interact(aapi, b)
    
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
        print("\n[!]: Request limit seem to be exceeded. Try again later.")
    except KeyboardInterrupt:
        print("\n[!]: SIGINT")
    finally:
        print("\x1b[?25h", end="")


if __name__ == "__main__":
    main()

