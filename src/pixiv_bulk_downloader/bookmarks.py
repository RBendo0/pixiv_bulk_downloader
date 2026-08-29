from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pixivpy3.utils import JsonDict

from .base import PixivBaseDownloader
from .config import config
from .const import (
    CONFIG_KEY_AUTHOR_METADATA,
    DEFAULT_AUTHOR_METADATA,
    DISCARDED_CSV_PREFIX,
    NOT_FOUND_CSV_PREFIX,
)
from .errors import (
    ApiError,
    ApiRateLimitError,
    FileError,
    InvalidDataFormatError,
    PageNotFoundError,
    PBDError,
    UserHasNotDefinedCustomConfiguration,
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
    random_delay,
)
from .ui import ui


class PixivBookmarksDownloader(PixivBaseDownloader):

    _author_metadata: bool = DEFAULT_AUTHOR_METADATA

    @classmethod
    def _load_author_metadata_setting(cls) -> None:

        cls._author_metadata = DEFAULT_AUTHOR_METADATA

        try:

            author_metadata = config.load(
                CONFIG_KEY_AUTHOR_METADATA
            )

            if author_metadata is None or author_metadata == "":
                return

            if not isinstance(author_metadata, bool):
                raise InvalidDataFormatError()

            cls._author_metadata = author_metadata

        except UserHasNotDefinedCustomConfiguration:
            return

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                "Failed to load author metadata setting.",
                with_report=True,
            )

            ui.line(
                "[+]: Author metadata setting will be set to default.",
                ui.COLOR_WARNING,
            )

    @classmethod
    def _show_author_metadata_settings(cls) -> None:

        ui.line(
            "[+]: Author metadata: [@@"
            f"{' Enabled' if cls._author_metadata else ' Disabled'}"
            "@@. ]",
            tag_color=ui.COLOR_INFO,
        )

    @classmethod
    def init(cls) -> None:

        cls._load_author_metadata_setting()
        cls._show_author_metadata_settings()

    @classmethod
    def set_author_metadata(cls) -> None:

        ui.line()

        author_metadata = ui.confirm(
            prompt="Enable author metadata",
            valid="YN",
            default=(
                "Y"
                if cls._author_metadata
                else "N"
            ),
        )

        cls._author_metadata = author_metadata

        if not config.save_with_interact(
            key=CONFIG_KEY_AUTHOR_METADATA,
            value=author_metadata,
            subject="author metadata setting",
        ):

            ui.line(
                "[+]: The new setting will remain active "
                "for the current session only.",
                ui.COLOR_WARNING,
            )

        cls._show_author_metadata_settings()

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
            prompt="[?] Scegliere (ESC per Menu principale)",
            valid="123" + ui.KEY_ESCAPE,
        )

        if c1 == ui.KEY_ESCAPE:
            return None

        ui.menu(
            title="Visibilità bookmark",
            options={
                "1": "Pubblici",
                "2": "Privati",
            },
        )

        c2 = ui.input_key(
            prompt="[?] Scegliere (ESC per Menu principale)",
            valid="12" + ui.KEY_ESCAPE,
        )

        if c2 == ui.KEY_ESCAPE:
            return None

        return {
            "mode": mode_map[c1],
            "restrict": privacy_map[c2],
        }

    @classmethod
    def add_list_interact(
        cls,
        lists_path: Path,
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
                for file in lists_path.glob("*.csv")
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
    def download_bookmarks(
        cls,
        bookmarks_path: Path,
    ) -> None:

        # Rileva opzioni utente
        options: BookmarkOptions | None = cls.main_download_interact()

        if not options: 
            return

        # Scansiona e crea la lista di opere
        bookmarked_data = cls.retrieve_bookmarks(
            bookmarks_path, 
            **options,
        )

        if not bookmarked_data:
            return

        # Scarica le opere
        cls.download(
            bookmarked_data,
            bookmarks_path
        )

    @classmethod
    def retrieve_bookmarks(
        cls,
        bookmarks_path: Path,
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

        online_total: int | None = None

        if restrict == "public":

            try:
                
                # Numero di opere totali
                online_total = caapi.user_detail(
                    target_id,
                )["profile"][
                    "total_illust_bookmarks_public"
                ]

                # Numero di opere totali marcate come preferite
                d_width = len(str(online_total))

            except Exception as e:  # noqa: BLE001

                e = PBDError.hierarchy(e)

                e.notify(
                    "@@Failed to obtain total public artwork count:@@.",
                    with_report=True,
                )

        # Lista ID delle opere e degli autori già presenti nell'archivio locale
        local = SimpleNamespace(
            work_ids=set(),
            user_ids=set(),
        )
        local_total: int = 0

        def check_for_artworks(
            local: SimpleNamespace,
            metadata_file: Path,
        ) -> None:

            try:

                image_data = PixivMetadata.from_file(
                    metadata_file
                )

                if image_data.type != "artwork":
                    return

                if image_data.state != "complete":
                    return

                local.work_ids.add(image_data.artw_id)

                local.user_ids.add(image_data.author_id)

                ui.line(
                    f"[+]: Found @@{len(local.work_ids)}@@. artworks.",
                    tag_color=ui.COLOR_INFO,
                    history=False,
                )

            except Exception:  # noqa: BLE001
                return

        if mode in ("missing", "chrono"):

            ui.line("[+]: Scanning local archive...")   

            cls.scan_archive(
                bookmarks_path, 
                shared_context=local, 
                run_for_each_metadata=check_for_artworks
            )

            ui.line(
                home=False, 
                clear=False,
            )

            local_total = len(local.work_ids)
            
        # ATTENZIONE:
        # default_abort è persistente.
        # Chiamare sempre reset() prima del primo utilizzo.
        cls.default_abort.reset()

        # Stampe informative.
        ui.line("[i]: " + cls.default_abort.prompt)

        counter = (
            f"[{0:0{d_width}d}/{online_total:0{d_width}d}]"
            if online_total is not None
            else "[0]"
        )

        while next_qs is not None:

            # E' stata richiesta l'interruzione, esce dal ciclo
            if cls.default_abort.is_requested:

                ui.line("[!]: Fetching interrupted by user.")

                break

            try:

                ui.line(
                    f"[+]: {counter}: Retrieving new page",
                    history=False,
                )                

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

            except ApiRateLimitError:

                if rcc.wait_rate_limit(
                    f"[!]: {counter}: Retrieving new page"
                ) == rcc.Action.ABORT: 

                    ui.line(
                        "[!]: Operation interrupted by user.",
                    )

                    break

                continue

            except ApiError as e:

                e.notify(
                    "Failed to retrieve new page.",
                    with_report=True,
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

            for illust in res_json["illusts"]:

                # Rileva se è stata richiesta l'interruzione del processo
                if cls.default_abort.is_requested and not cls.default_abort.is_notified:
                    
                    ui.line(
                        "[!]: Operation interrupted. "
                        "Waiting for the current page to complete.",
                    )

                    cls.default_abort.set_notified()

                # Opera già presente nel database locale
                if illust.id in local.work_ids:

                    # Modalità Missing, se l'ID corrente è presente in locale salta il ciclo
                    if mode == "missing":

                        ui.line(
                            f"[-]: Already downloaded: "
                            f"<ID:{illust.id}> "
                            f"{illust.title}",
                            history=False,
                        )                    
                                            
                        continue

                    # Modalità Chrono, se l'ID corrente è presente in locale termina la scansione
                    if mode == "chrono":

                        ui.line(
                            "[-]: Last chrono artwork reached. Fetching completed."
                        )

                        return urls

                current = len(urls) + 1

                if mode in ("missing", "chrono"):
                    current += local_total

                counter = (
                    f"[{current:0{d_width}d}/{online_total:0{d_width}d}]"
                    if online_total is not None
                    else f"[{current}]"
                )

                progress = (
                    f"{counter}: "
                    f"<ID:{illust.id}> "
                    f"{illust.title}"
                )                    

                while True:

                    try:

                        ui.line(
                            f"[+]: {progress}",
                            history=False,
                        )

                        artwork_data = PixivMetadata(   # pyright: ignore[reportAbstractUsage]
                            type="artwork",
                            state="pending",
                            data=illust,
                        )

                        if artwork_data.has_error:
                            break

                        if artwork_data.artw_is_ugoira:

                            ugoira_data = caapi.ugoira_metadata(
                                artwork_data.artw_id
                            )

                            artwork_data.add(
                                payload="ugoira",
                                data=ugoira_data,
                            )

                        author_data: PixivMetadata | None = None

                        if (
                            cls._author_metadata
                            and artwork_data.author_id not in local.user_ids
                        ):

                            author_data = PixivMetadata(  # pyright: ignore[reportAbstractUsage]
                                type="author",
                                data=caapi.user_detail(
                                    artwork_data.author_id
                                ),
                            )

                            local.user_ids.add(
                                artwork_data.author_id
                            )

                        cls.save_metadata(
                            bookmarks_path,
                            artwork_data,
                            author_data,
                        )

                        urls.append(artwork_data)

                        ui.line(
                            f"[+]: {progress} @@[Indexed]@@.",
                            tag_color=ui.COLOR_SUCCESS,
                            history=False,
                        )

                        break

                    except ApiRateLimitError:

                        if rcc.wait_rate_limit(
                            f"[!]: {progress}"
                        ) == rcc.Action.ABORT:

                            ui.line(
                                "[!]: Operation interrupted by user.",
                            )

                            return urls

                        continue

                    except Exception as e:  # noqa: BLE001

                        # Normalizza le eccezioni di livello superiore a PBDError, per una gestione uniforme
                        e = PBDError.hierarchy(e)

                        e.notify(
                            f"Failed to index artwork: @@{progress}@@.",
                            with_report=True,
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

            random_delay()

        else:

            # WHILE ... ELSE, eseguito solamente se il ciclo while 
            # termina senza interruzioni forzate quali break o return
            ui.line("[+]: Fetching completed.")

        # Best practice:
        # reset() finale consigliato ma non obbligatorio.
        cls.default_abort.reset()

        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    @classmethod
    def add_list_to_bookmarks(
        cls,
        lists_path: Path,
    ) -> None:

        options = cls.add_list_interact(lists_path)

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

            # ATTENZIONE:
            # default_abort è persistente.
            # Chiamare sempre reset() prima del primo utilizzo.
            cls.default_abort.reset()

            for source_file in options["source_files"]:

                source_csv = CsvFile(
                    source_file,
                    purge=True,
                )

                lines = source_csv.read_lines()

                not_found_file = (
                    lists_path
                    / f"{NOT_FOUND_CSV_PREFIX}{source_file.name}"
                )

                discarded_file = (
                    lists_path
                    / f"{DISCARDED_CSV_PREFIX}{source_file.name}"
                )

                not_found_csv = CsvFile(not_found_file)
                discarded_csv = CsvFile(discarded_file)

                ui.line(f"[+]: List ......... : {source_file.name}")
                ui.line(f"[+]: URLs ......... : {len(lines)}")
                ui.line(f"[+]: Privacy ...... : {options['restrict']}")

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
                ui.line("[i]: " + cls.default_abort.prompt)

                for line in reversed(lines):

                    if cls.default_abort.is_requested:

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

                        progress = f"Adding bookmark: {illust_id}"

                        while True:

                            ui.line(
                                f"[+]: {progress}",
                                history=False,
                            )

                            try:

                                caapi.illust_bookmark_add(
                                    illust_id,
                                    restrict=options["restrict"],
                                )

                                statistics["added"] += 1

                                break

                            except ApiRateLimitError:

                                if rcc.wait_rate_limit(
                                    f"[!]: {progress}"
                                ) == rcc.Action.ABORT:

                                    final_message = "[!]: Operation interrupted by user."

                                    raise rcc.Abort

                                continue

                            except PageNotFoundError as e:

                                not_found_csv.append_row(url)

                                statistics["not_found"] += 1

                                e.notify(
                                    f"Page not found for URL: @@{url}@@.",
                                    with_report=True,
                                )

                                break

                            except ApiError as e:

                                error_description = f"{e.report()}"

                                discarded_csv.append_row(
                                    url,
                                    error_description,
                                )

                                statistics["discarded"] += 1

                                e.notify(
                                    f"Failed to add bookmark: <ID:@@{illust_id}@@.>",
                                    with_report=True,
                                )

                                break

                    # Aggiorna immediatamente la lista persistente.
                    source_csv.truncate_last()

                    # Ritardo casuale tra le chiamate API, per evitare il rate limit
                    random_delay(*API_DELAY_TURBO)

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