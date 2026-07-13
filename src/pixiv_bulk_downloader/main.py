from __future__ import annotations

from .bookmarks import pbd
from .errors import LoginFailedError
from .pixiv_call_api import caapi
from .ui import ui


def main_interact() -> None:

    actions = {
        "1": pbd.download_bookmarks,
        "2": pbd.resume_pending_jobs,
        "3": pbd.add_list_to_bookmarks,
        "4": pbd.convert_bookmarks_to_private,
    }

    while True:

        ui.menu(
            title="Pixiv Bulk Downloader",
            options={
                "1": "Scarica i preferiti sull'archivio locale",
                "2": "Riprendi scaricamenti lasciati in sospeso",
                "3": "Aggiungi preferiti da una lista di url",
                "4": "Cambia profilo di privacy ai preferiti",
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
            valid="01234T",
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

        caapi.open_session()
        main_interact()

    finally:

        pbd.pool_shutdown()    


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