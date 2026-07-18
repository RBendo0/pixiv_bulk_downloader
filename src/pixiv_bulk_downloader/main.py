from __future__ import annotations

import argparse
from pathlib import Path

from .bookmarks import pbd
from .config import config
from .errors import LoginFailedError
from .pbd_types import CommandLineOptions
from .pixiv_call_api import caapi
from .ui import ui


def parse_args() -> CommandLineOptions:

    parser = argparse.ArgumentParser(
        description="Pixiv Bulk Downloader",
    )

    parser.add_argument(
        "--root",
        type=Path,
        help="Percorso della directory principale dell'archivio PBD.",
    )

    args = parser.parse_args()

    return {
        "root": args.root,
    }


def main_interact() -> None:

    bookmarks_path = config.Dirs.bookmarks()
    lists_path = config.Dirs.lists()

    actions = {
        "1": lambda: pbd.download_bookmarks(bookmarks_path),
        "2": lambda: pbd.resume_pending_jobs(bookmarks_path),
        "3": lambda: pbd.add_list_to_bookmarks(lists_path),
        "4": pbd.convert_bookmarks_to_private,
        "5": config.root_dir,
    }

    while True:

        ui.menu(
            title="Pixiv Bulk Downloader",
            options={
                "1": "Scarica i preferiti sull'archivio locale",
                "2": "Riprendi scaricamenti lasciati in sospeso",
                "3": "Aggiungi preferiti da una lista di url",
                "4": "Cambia profilo di privacy ai preferiti",
                "5": "Configura il percorso dell'archivio", 
                "0": "Esci",
            },
            footer="[T]: Debugger - [CTRL+C]: Termina",
            frame=True,
            top_margin=4,
        )

        choice = ui.input_key(
            prompt=(
                "[?] Effettuare la scelta desiderata"
            ),
            valid="012345T",
        )        

        ui.line()

        if choice == "0":
            break
        elif choice == "T":
            # inserire in questa riga eventuali routine di test
            continue
        
        actions[choice]()


def _main() -> None:

    try:

        options = parse_args()

        config.init(options["root"])
        caapi.open_session()
        main_interact()

    finally:

        pbd.pool_shutdown()    
        ui.Renderer.stop()        


def main() -> None:

    try:

        _main()

    except (KeyError, LoginFailedError) as e:

        ui.line(
            f"[!]: {type(e).__name__}: {e}",
            ui.COLOR_ERROR,
        )

    except KeyboardInterrupt:

        ui.line(
            "[!]: Process terminated by user. ",
            ui.COLOR_ERROR,
        )

    finally:
        
        print("\x1b[?25h", end="")


if __name__ == "__main__":
    main()    