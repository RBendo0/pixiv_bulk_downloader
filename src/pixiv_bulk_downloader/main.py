from __future__ import annotations

import argparse
from pathlib import Path

from .animation import m3
from .bookmarks import pbd
from .config import config
from .errors import LoginFailedError
from .pbd_path import sd
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

    actions = {
        "1": lambda: pbd.download_bookmarks(sd.bookmarks()),
        "2": lambda: pbd.resume_pending_jobs(sd.bookmarks()),
        "3": lambda: pbd.add_list_to_bookmarks(sd.lists()),
        "4": pbd.convert_bookmarks_to_private,
        "5": sd.config_root_dir,
        "6": m3.set_preferred_media_formats,
        "7": config.Advanced.show_and_reset_settings,
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
                "6": "Configura formati salvataggio animazioni", 
                "7": "Abilita accesso a impostazioni avanzate",
            },
            footer="[ESC=Termina / SPAZIO=Refresh]",
            frame=True,
            top_margin=4,
        )

        choice = ui.input_key(
            prompt=(
                "[?] Effettuare la scelta desiderata"
            ),
            valid="1234567" + ui.KEY_ESCAPE + ui.KEY_SPACE,
        )        

        ui.line()

        if choice == ui.KEY_SPACE:
            ui.refresh()
            continue

        if choice == ui.KEY_ESCAPE:
            break

        actions[choice]()


def _main() -> None:

    try:

        options = parse_args()

        ui.line(
            "[+]: Initialisation Begin. "
        )

        caapi.open_session()
        sd.init(options["root"])
        m3.init()

        ui.line(
            "[-]: Initialisation End. " 
        )

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