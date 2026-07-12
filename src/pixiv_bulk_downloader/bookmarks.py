from __future__ import annotations

import re
from typing import Any

from pixivpy3.utils import JsonDict

from .base import PixivBaseDownloader
from .const import (
    BOOKMARKS_DIR,
    DISCARDED_CSV_PREFIX,
    LISTS_DIR,
    NOT_FOUND_CSV_PREFIX,
)
from .errors import (
    ApiError,
    ApiRateLimitError,
    PageNotFoundError,
    PBDError,
    rcc,
)
from .iofile import CsvFile
from .metadata import PixivMetadata
from .pbd_types import (
    AddListOptions,
    BookmarkMode,
    BookmarkOptions,
    BookmarkPrivacy,
)
from .pixiv_call_api import caapi
from .timing import (
    API_DELAY_TURBO,
    random_api_delay,
)
from .ui import ui


class PixivBookmarksDownloader(PixivBaseDownloader):
    
    @classmethod
    def main_download_interact(cls) -> BookmarkOptions | None:

        mode_map: dict[str, BookmarkMode] = {
            "1": "all",
            "2": "missing",
            "3": "chrono",
        }

        privacy_map: dict[str, BookmarkPrivacy] = {
            "1": "public",
            "2": "private",
        }

        ui.menu(
            title="Modalità download",
            options={
                "1": "Scarica tutti i preferiti nell'archivio locale",
                "2": "Scarica solo i preferiti non ancora salvati in locale",
                "3": "Scarica solo i preferiti aggiunti di recente",
            },
        )

        c1 = ui.input_key(
            prompt="[?] Scegliere ([0] per Menu principale)",
            valid="0123",
        )

        if c1 == "0":
            return None

        ui.menu(
            title="Visibilità bookmark",
            options={
                "1": "Pubblici",
                "2": "Privati",
            },
        )

        c2 = ui.input_key(
            prompt="[?] Scegliere ([0] per Menu principale)",
            valid="012",
        )

        if c2 == "0":
            return None

        return {
            "mode": mode_map[c1],
            "restrict": privacy_map[c2],
        }

    @classmethod
    def add_list_interact(
        cls,
    ) -> AddListOptions | None:

        privacy_map: dict[str, BookmarkPrivacy] = {
            "1": "public",
            "2": "private",
        }

        # A è riservata all'opzione "Tutte le liste"
        choices = "BCDEFGHIJKLMNOPQRSTUVWXYZ"

        source_files = sorted(
            (
                file
                for file in LISTS_DIR.glob("*.csv")
                if not file.name.startswith(
                    (
                        NOT_FOUND_CSV_PREFIX,
                        DISCARDED_CSV_PREFIX,
                    )
                )
            ),
            key=lambda file: file.stat().st_mtime,
            reverse=True,
        )

        if not source_files:

            ui.line(
                "[!]: No CSV lists found.",
                ui.COLOR_WARNING,
            )

            return None

        displayed_files = source_files[:len(choices)]

        list_options = {
            "A": "Tutte le liste",
            **{
                letter: file.name
                for letter, file in zip(
                    choices,
                    displayed_files,
                )
            },
        }

        ui.menu(
            title="",
            options=list_options,
            top_margin=1,
        )

        choice = ui.input_key(
            prompt="[?] Scegliere ([0] per Menu principale)",
            valid=(
                "0A"
                + choices[:len(displayed_files)]
            ),
        )

        if choice == "0":
            return None

        if choice == "A":

            selected_files = source_files

        else:

            selected_files = [
                displayed_files[
                    choices.index(choice)
                ]
            ]

        ui.menu(
            title="",
            options={
                "1": "Pubblici",
                "2": "Privati",
            },
            top_margin=1,
        )

        privacy_choice = ui.input_key(
            prompt="[?] Scegliere ([0] per Menu principale)",
            valid="012",
        )

        if privacy_choice == "0":
            return None

        return {
            "source_files": selected_files,
            "restrict": privacy_map[privacy_choice],
        }

    @classmethod
    def download_bookmarks(cls) -> None:

        # Rileva opzioni utente
        options: BookmarkOptions | None = cls.main_download_interact()

        if not options: 
            return

        # Scansiona e crea la lista di opere
        bookmarked_data = cls.retrieve_bookmarks(**options)

        if not bookmarked_data:
            return

        # Scarica le opere
        cls.download(bookmarked_data, BOOKMARKS_DIR)

    @classmethod
    def retrieve_bookmarks(
        cls,
        mode: BookmarkMode = "all",
        restrict: BookmarkPrivacy = "public",
    ) -> list[PixivMetadata] | None:

        urls: list[PixivMetadata] = []
        next_qs: dict[str, Any] | None = {}
        target_id = caapi.user_id()

        ui.line()
        ui.line("[+]: Fetching information of bookmarked works...")
        
        # Chiede conferma a procedere
        if not ui.confirm():
            return

        d_width: int | None = None

        try:
            
            # Numero di opere totali
            total = caapi.user_detail(
                target_id,
            )["profile"][
                "total_illust_bookmarks_public"
            ]

            # Numero di opere totali marcate come preferite
            d_width = len(str(total))

        except Exception as e:

            ui.line(
                f"[!]: Failed to obtain total artwork count: "
                f"{type(e).__name__}: {e}",
                ui.COLOR_WARNING,
            )

        urls_len = 0
        
        # Lista ID già scaricati
        local_ids: set[str] = set()

        # Se necessario scarica la lista di tutti i lavori già presenti in locale
        if mode in ("missing", "chrono"):
            for folder in BOOKMARKS_DIR.rglob("*_*"):
                local_ids.add(folder.name.split("_")[0])

        # Imposta interruzione da utente
        user_abort = ui.InputPending(
            valid="Q",
            prompt="Press Q to interrupt the process."
        )

        # Stampe informative
        ui.line("[i]: " + user_abort.prompt)

        while next_qs is not None:

            # E' stata richiesta l'interruzione, esce dal ciclo
            if user_abort.is_requested:

                ui.line("[!]: Fetching interrupted by user.")

                break

            try:

                # Legge l'intera pagina di bookmarks, a seconda se è la prima o una successiva
                if "user_id" not in next_qs:

                    res_json: JsonDict = caapi.user_bookmarks_illust(
                        target_id,
                        restrict=restrict,
                    )

                else:

                    res_json = caapi.user_bookmarks_illust(
                        **next_qs
                    )

                # Passa alla pagina successiva  
                next_qs = caapi.parse_qs(
                    res_json.get("next_url"),
                )

                """
                test_case = random.randint(1, 10)

                if test_case == 1:
                    # raise StorageError("Storage test")
                    pass

                elif test_case == 2:
                    raise PixivApiError("Pixiv API test")

                elif test_case == 3:
                    raise RateLimitError("Rate limit test")
                """

            except ApiRateLimitError as e:

                ui.line(
                    f"[!]: {e.info()}: {e} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}",
                    ui.COLOR_WARNING,
                )

                if rcc.wait_rate_limit() == rcc.Action.ABORT: 

                    ui.line(
                        "[!]: Operation interrupted by user.",
                    )

                    break

                ui.line(
                    "[i]: Access limited by the service. Retrying in a moment."
                )                    

                continue

            except ApiError as e:

                ui.line(
                    f"[!]: {e.info()}: {e} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}",
                    ui.COLOR_ERROR,
                )

                action = rcc.prompt_error_menu(
                    {
                        "A": "Abort",
                        "R": "Retry",
                    },
                    valid="AR",
                    default="R",
                )

                if action == rcc.Action.ABORT:

                    ui.line(
                        "[!]: Operation interrupted by user.",
                    )

                    break

                ui.line(
                    "[i]: Operation resumed."
                )                    

                continue

            for idx, illust in enumerate(res_json["illusts"]):

                # Rileva se è stata richiesta l'interruzione del processo
                if user_abort.is_requested and not user_abort.is_notified:
                    
                    ui.line(
                        "[!]: Operation interrupted. "
                        "Waiting for the current page to complete.",
                    )

                    user_abort.set_notified()

                # Opera già presente nel database locale
                if str(illust.id) in local_ids:

                    # Modalità Missing, se l'ID corrente è presente in locale salta il ciclo
                    if mode == "missing":

                        ui.line(
                            f"[-]: Already downloaded: "
                            f"{illust.title} "
                            f"(id: {illust.id})",
                            history=False,
                        )                    
                                            
                        continue

                    # Modalità Chrono, se l'ID corrente è presente in locale termina la scansione
                    if mode == "chrono":

                        ui.line(
                            "[-]: Last chrono artwork reached. Fetching completed."
                        )

                        return urls

                while True:

                    try:

                        image_data: PixivMetadata = PixivMetadata(illust)
                        cls.save_index(image_data, BOOKMARKS_DIR)
                        urls.append(image_data)

                        counter = (
                            f"[{urls_len + idx + 1:0{d_width}d}/{total:0{d_width}d}]"
                            if d_width is not None
                            else f"[{urls_len + idx + 1}]"
                        )

                        ui.line(
                            f"[+]: "
                            f"{counter}: "
                            f"{illust.title} "
                            f"(id: {illust.id}) [Indexed]",
                            history=False,
                        )

                        break

                    except Exception as e:

                        # Normalizza le eccezioni di livello superiore a PBDError, per una gestione uniforme
                        e = PBDError.hierarchy(e)

                        ui.line(
                            " | ",
                            home=False,
                            clear=False,
                            history=False,
                        )

                        ui.line(
                            f"[!]: {e.info()}: "
                            f"{type(e).__name__}: {e}",
                            ui.COLOR_ERROR,
                            home=False,
                            clear=False,
                        )                        

                        action = rcc.prompt_error_menu(
                            {
                                "A": "Abort",
                                "R": "Retry",
                                "C": "Continue",
                            },
                            valid="ARC",
                            default="C",
                        )

                        if action == rcc.Action.ABORT:

                            ui.line(
                                "[!]: Operation interrupted by user."
                            )

                            # Ritorna al processo chiamante
                            return urls
                    
                        if action == rcc.Action.CONTINUE:
                            break

                        if action == rcc.Action.RETRY:
                            
                            ui.clear_lines(1)

                            continue

            urls_len = len(urls)
            random_api_delay()

        else:

            # WHILE ... ELSE, eseguito solamente se il ciclo while 
            # termina senza interruzioni forzate quali break o return
            ui.line("[+]: Fetching completed.")

        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    @classmethod
    def add_list_to_bookmarks(cls) -> None:

        options = cls.add_list_interact()

        if not options:
            return

        ui.line()
        ui.line("[+]: Adding bookmarks from CSV lists...")

        statistics = {
            "added": 0,
            "not_found": 0,
            "discarded": 0,
        }

        final_message = "[+]: Adding bookmarks completed."

        try:

            # Imposta interruzione da utente
            user_abort = ui.InputPending(
                valid="Q",
                prompt="Press Q to interrupt the process."
            )

            for source_file in options["source_files"]:

                source_csv = CsvFile(
                    source_file,
                    purge=True,
                )

                lines = source_csv.read_lines()

                not_found_file = (
                    LISTS_DIR
                    / f"{NOT_FOUND_CSV_PREFIX}{source_file.name}"
                )

                discarded_file = (
                    LISTS_DIR
                    / f"{DISCARDED_CSV_PREFIX}{source_file.name}"
                )

                not_found_csv = CsvFile(not_found_file)
                discarded_csv = CsvFile(discarded_file)

                ui.line(f"[i]: List ......... : {source_file.name}")
                ui.line(f"[i]: URLs ......... : {len(lines)}")
                ui.line(f"[i]: Privacy ...... : {options['restrict']}")

                # Chiede conferma a procedere, in caso negativo salta alla lista successiva
                if not ui.confirm():

                    ui.clear_lines(3)

                    ui.line(
                        f"[!]: {source_file.name} | ",
                        history=False,
                    )

                    ui.line(
                        "Discarded!",
                        ui.COLOR_WARNING,
                        home=False,
                        clear=False,
                    )

                    continue

                # Stampe informative
                ui.line("[i]: " + user_abort.prompt)

                for line in reversed(lines):

                    if user_abort.is_requested:

                        final_message = "[!]: Adding bookmarks interrupted by user."

                        raise rcc.Abort

                    url = line.strip()

                    match = re.search(
                        r"artworks/(\d+)",
                        url,
                    )

                    if not match:

                        error_description = "Not an artwork URL"

                        discarded_csv.append_row(
                            url,
                            error_description,
                        )

                        statistics["discarded"] += 1

                        ui.line(
                            f"[!]: {url} | ",
                            history=False,
                        )

                        ui.line(
                            f"{error_description}",
                            ui.COLOR_WARNING,
                            home=False,
                            clear=False,
                            history=False,
                        )

                    else:           

                        illust_id = int(match.group(1))

                        while True:

                            ui.line(
                                f"[+]: Adding bookmark: {illust_id}",
                                history=False,
                            )

                            try:

                                caapi.illust_bookmark_add(
                                    illust_id,
                                    restrict=options["restrict"],
                                )

                                statistics["added"] += 1

                                break

                            except ApiRateLimitError as e:

                                ui.line(
                                    " | ",
                                    home=False,
                                    clear=False,
                                    history=False,
                                )

                                ui.line(
                                    f"[!]: {e.info()}: {e}",
                                    ui.COLOR_WARNING,
                                    home=False,
                                    clear=False,
                                )

                                if rcc.wait_rate_limit() == rcc.Action.ABORT:

                                    final_message = "[!]: Operation interrupted by user."

                                    raise rcc.Abort

                                ui.line(
                                    "[i]: Access limited by the service. Retrying in a moment."
                                )

                                continue

                            except PageNotFoundError as e:

                                not_found_csv.append_row(url)

                                statistics["not_found"] += 1

                                ui.line(
                                    " | ",
                                    home=False,
                                    clear=False,
                                    history=False,
                                )

                                ui.line(
                                    f"[!]: {e.info()}: "
                                    f"{type(e).__name__}: {e}",
                                    ui.COLOR_WARNING,
                                    home=False,
                                    clear=False,
                                )

                                break

                            except ApiError as e:

                                error_description = (
                                    f"{e.info()}: "
                                    f"{type(e).__name__}: {e}"
                                )

                                discarded_csv.append_row(
                                    url,
                                    error_description,
                                )

                                statistics["discarded"] += 1

                                ui.line(
                                    " | ",
                                    home=False,
                                    clear=False,
                                    history=False,
                                )

                                ui.line(
                                    f"[!]: {error_description}",
                                    ui.COLOR_ERROR,
                                    home=False,
                                    clear=False,
                                )

                                break

                    # Aggiorna immediatamente la lista persistente.
                    source_csv.truncate_last()

                    # Ritardo casuale tra le chiamate API, per evitare il rate limit
                    random_api_delay(*API_DELAY_TURBO)

        except rcc.Abort:

            pass

        # STATISTICHE FINALI 

        ui.line()

        ui.line(
            f"[+]: Added bookmarks .. : {statistics['added']}",
            ui.COLOR_SUCCESS,
        )

        ui.line(
            f"[-]: Not found ........ : {statistics['not_found']}",
            (
                ui.COLOR_WARNING
                if statistics["not_found"]
                else ui.COLOR_SUCCESS
            ),
        )

        ui.line(
            f"[!]: Discarded ........ : {statistics['discarded']}",
            (
                ui.COLOR_ERROR
                if statistics["discarded"]
                else ui.COLOR_SUCCESS
            ),
        )

        ui.line(final_message)

    @classmethod
    def convert_bookmarks_to_private(cls) -> None:
        pass


# Alias del downloader principale
pbd = PixivBookmarksDownloader