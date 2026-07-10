from __future__ import annotations

import re
from typing import Any

from pixivpy3.utils import JsonDict

from .base import PixivBaseDownloader
from .const import (
    BOOKMARKS_DIR,
    BOOKMARKS_NOT_FOUND,
    BOOKMARKS_PENDING,
)
from .errors import (
    ApiError,
    ApiRateLimitError,
    PBDError,
    rcc,
)
from .metadata import PixivMetadata
from .pbd_types import BookmarkMode, BookmarkOptions, BookmarkPrivacy
from .pixiv_call_api import caapi
from .timing import (
    PIXIV_API_DELAY_MIN,
    random_api_delay,
)
from .ui import InputPending, ui


class PixivBookmarksDownloader(PixivBaseDownloader):
    
    @classmethod
    def interact(cls) -> BookmarkOptions | None:

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
    def download_bookmarks(cls) -> None:

        # Rileva opzioni utente
        options: BookmarkOptions | None = cls.interact()

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
        user_abort = InputPending(
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
            random_api_delay(PIXIV_API_DELAY_MIN)

        else:

            # WHILE ... ELSE, eseguito solamente se il ciclo while 
            # termina senza interruzioni forzate quali break o return
            ui.line("[+]: Fetching completed.")

        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    @classmethod
    def add_list_to_bookmarks(cls) -> None:

        ui.line()
        ui.line("[+]: Adding bookmarks from URL list...")

        lines = BOOKMARKS_PENDING.read_text(encoding="utf-8").splitlines()

        added = 0
        errors = 0
        skipped = 0

        for line in lines:

            url = line.strip()

            if not url:
                continue

            match = re.search(r"artworks/(\d+)", url)

            if not match:
                
                skipped += 1
                
                ui.line(
                    f"[!]: Invalid URL: {url}",
                    ui.COLOR_ERROR,
                )
                
                continue

            illust_id = int(match.group(1))

            ui.line(
                f"[+]: Adding bookmark: {illust_id}",
                history=False,
            )

            try:

                caapi.illust_bookmark_add(
                    illust_id,
                    restrict="private",
                )
                
                added += 1

            except Exception as e:
            
                e = PBDError.cast(e)

                errors += 1
                
                ui.line(
                    f" [!]: {e.info()}: "
                    f"{type(e).__name__}: {e}",
                    ui.COLOR_ERROR,
                    home=False,
                    clear=False,
                )

            random_api_delay(PIXIV_API_DELAY_MIN)

        ui.line()

        ui.line(
            f"[+]: Added bookmarks .. : {added}",
            ui.COLOR_SUCCESS,
        )

        ui.line(
            f"[-]: Skipped URLs ..... : {skipped}",
            ui.COLOR_WARNING if skipped else ui.COLOR_SUCCESS,
        )

        ui.line(
            f"[!]: Errors ........... : {errors}",
            ui.COLOR_ERROR if errors else ui.COLOR_SUCCESS,
        )

        ui.line("[+]: Adding bookmarks completed.")

    @classmethod
    def convert_bookmarks_to_private(cls) -> None:
        pass


# Alias del downloader principale
pbd = PixivBookmarksDownloader