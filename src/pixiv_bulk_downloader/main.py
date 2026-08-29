from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .animation import m3
from .bookmarks import pbd
from .config import config
from .debug import debug
from .errors import (
    LoginFailedError,
    PBDError,
)
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


def settings_interact() -> None:

    actions = {
        "1": sd.config_root_dir,
        "2": pbd.set_author_metadata,
        "3": m3.set_preferred_media_formats,
        "4": config.Advanced.show_and_reset_settings,
    }

    while True:

        ui.menu(
            title="Settings",
            options={
                "1": "Configura il percorso dell'archivio",
                "2": "Configura salvataggio metadata autore",
                "3": "Configura formati salvataggio animazioni",
                "4": "Abilita accesso a impostazioni avanzate",
            },
            footer="[ESC=Torna al menu principale]",
            frame=True,
            top_margin=4,
        )

        choice = ui.input_key(
            prompt="[?] Effettuare la scelta desiderata",
            valid="1234" + ui.KEY_ESCAPE,
        )

        ui.line()

        if choice == ui.KEY_ESCAPE:
            break

        actions[choice]()


def main_interact() -> None:

    actions = {
        "1": lambda: pbd.download_bookmarks(sd.bookmarks()),
        "2": lambda: pbd.resume_pending_jobs(sd.bookmarks()),
        "3": lambda: pbd.add_list_to_bookmarks(sd.lists()),
        "4": pbd.convert_bookmarks_to_private,
        "5": settings_interact,
    }

    while True:

        ui.menu(
            title="Pixiv Bulk Downloader",
            options={
                "1": "Scarica i preferiti sull'archivio locale",
                "2": "Riprendi scaricamenti lasciati in sospeso",
                "3": "Aggiungi preferiti da una lista di url",
                "4": "Cambia profilo di privacy ai preferiti",
                "5": "Impostazioni", 
            },
            footer="[ESC=Termina / SPAZIO=Refresh]",
            frame=True,
            top_margin=4,
        )

        choice = ui.input_key(
            prompt=(
                "[?] Effettuare la scelta desiderata"
            ),
            valid="12345" + ui.KEY_ESCAPE + ui.KEY_SPACE,
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

        timestamp = datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        ui.line()
        ui.line()
        ui.line("==============================================")
        ui.line(f" PBD :: initialize() :: {timestamp}")
        ui.line("==============================================")
        ui.line()

        options = parse_args()

        ui.line(
            "[+]: Initialisation Begin. "
        )

        ui.line(
            "[+]: Login...",
            history=False,
        )

        caapi.open_session()

        ui.line(
            "[+]: Login...OK!",
        )

        debug.init()
        sd.init(options["root"])
        pbd.init()
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

    except LoginFailedError as e:

        e.notify(
            "Authentication failed",
            with_report=True,
        )

    except PBDError as e:

        e.notify(
            "Fatal error",
            with_report=True,
        )

    except KeyboardInterrupt:

        ui.line(
            "[!]: Process terminated by user. ",
            ui.COLOR_WARNING,
        )


if __name__ == "__main__":
    main()    