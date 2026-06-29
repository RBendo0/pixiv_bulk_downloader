from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import PixivBaseDownloader
from .const import BOOKMARKS_DIR
from .metadata import PixivMetadata
from .errors import (
    PixivApiError,
    RateLimitError,
    is_rate_limited,
    prompt_error_menu,
    wait_rate_limit,
)
from .pbd_types import BookmarkMode, BookmarkOptions, BookmarkPrivacy
from .timing import (
    PIXIV_API_DELAY_MIN,
    random_api_delay,
)
from .ui import InputPending, ui

if TYPE_CHECKING:
    from pixivpy3.utils import JsonDict

# import random


class PixivBookmarksDownloader(PixivBaseDownloader):
    
    def interact(self) -> BookmarkOptions | None:

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

    def download_bookmarks(self) -> None:

        # Rileva opzioni utente
        options: BookmarkOptions | None = self.interact()

        if not options: 
            return

        # Scansiona e crea la lista di opere
        bookmarked_data = self.retrieve_bookmarks(**options)

        if not bookmarked_data:
            return

        # Scarica le opere
        self.download(bookmarked_data, BOOKMARKS_DIR)

    def retrieve_bookmarks(
        self,
        mode: BookmarkMode = "all",
        restrict: BookmarkPrivacy = "public",
    ) -> list[PixivMetadata] | None:

        urls: list[PixivMetadata] = []
        next_qs: dict[str, Any] | None = {}
        target_id = self.login_info["response"]["user"]["id"]

        ui.line()
        ui.line("[+]: Fetching information of bookmarked works...")
        
        # Chiede conferma a procedere
        if not ui.confirm():
            return

        try:

            # Numero di opere totali
            total = self.aapi.user_detail(self.aapi.user_id)["profile"][
                "total_illust_bookmarks_public"
            ]

            # Prima inizializzazione della pagina corrente e successiva 
            res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id, restrict=restrict)
            next_json: JsonDict | None = res_json

        except Exception as e:

            ui.line(
                f"[!]: API call failed: "
                f"{type(e).__name__}: {e}",
                ui.COLOR_ERROR,
            )

            return []

        d_width = len(str(total))
        urls_len = 0
        page_number = 0
        paging_fault: Exception | None = None
        
        # Lista ID già scaricati
        local_ids: set[str] = set()

        # Se necessario scarica la lista di tutti i lavori già presenti in locale
        if mode in ("missing", "chrono"):
            for folder in BOOKMARKS_DIR.rglob("*_*"):
                local_ids.add(folder.name.split("_")[0])

        # Imposta ultima pagina non ancora raggiunta (solo modalità chrono)
        is_chrono_last_missing_page = False

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
                break

            page_number += 1
            paging_fault = None 

            # Aggiorna la pagina successiva
            if page_number > 1 and next_json is not None:
                res_json = next_json

            # ASSERT DISABILITATA
            #
            # In teoria next_json non dovrebbe mai essere None
            # all'interno del ciclo while, perché:
            #
            # - viene inizializzata con res_json
            # - viene impostata a None solo quando next_qs diventa None
            # - in quel caso il ciclo termina
            #
            # Se questa assunzione si rivelasse falsa in futuro,
            # rivalutare la logica di paginazione.
            #
            # assert next_json is not None

            # Passa alla pagina successiva  
            next_qs = None if next_json is None else self.aapi.parse_qs(next_json.get("next_url")) 

            if next_qs is None:

                # Raggiunta l'ultima pagina dell'intero set di bookmarks
                next_json = None

            else:
                try:

                    next_json = self.aapi.user_bookmarks_illust(**next_qs)

                except Exception as e:

                    paging_fault = e

            # Verifica la validità del responso da Pixiv
            try:
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
                if paging_fault:
                    raise PixivApiError(
                        f"{type(paging_fault).__name__}: "
                        f"{paging_fault}"
                    )                

                if is_rate_limited(res_json):
                    raise RateLimitError(
                        "Pixiv API rate limit reached"
                    )

            except RateLimitError as e:

                ui.line(
                    f"[!]: {e} | "
                    f"Page: {page_number} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}",
                    ui.COLOR_WARNING,
                )

                if not wait_rate_limit():
 
                    ui.line(
                        "[!]: Operation interrupted by user.",
                    )

                    break

                ui.line(
                    "[i]: Access limited by the service. Retrying in a moment."
                )                    
                
                page_number -= 1

                continue

            except PixivApiError as e:

                ui.line(
                    f"[!]: API call failed: {e} | "
                    f"Page: {page_number} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}",
                    ui.COLOR_ERROR,
                )

                action = prompt_error_menu(
                    {
                        "A": "Abort",
                        "R": "Retry",
                    },
                    valid="AR",
                    default="R",
                )

                if action == "A":

                    ui.line(
                        "[!]: Operation interrupted by user.",
                    )

                    break

                ui.line(
                    "[i]: Operation resumed."
                )                    

                page_number -= 1

                continue

            # Modalità Chrono, primo ID pagina corrente presente in locale, termina
            if mode == "chrono":
                if str(res_json["illusts"][0].id) in local_ids:

                    ui.line(
                        "[-]: Last chrono page reached."
                    )

                    break

                # Rileva se e è l'ultima pagina da scaricare (solo modalità chrono)
                if next_json is not None:
                    is_chrono_last_missing_page = (str(next_json["illusts"][0].id) in local_ids)

            for idx, illust in enumerate(res_json["illusts"]):

                # Rileva se è stata richiesta l'interruzione del processo
                if user_abort.is_requested and not user_abort.is_notified:
                    
                    ui.line(
                        "[!]: Operation interrupted. "
                        "Waiting for the current page to complete.",
                    )

                    user_abort.set_notified()

                # Modalità Missing o Chrono ultima pagina, se l'ID corrente è presente in locale, salta il ciclo
                if (mode == "missing" or is_chrono_last_missing_page) and str(illust.id) in local_ids:

                    ui.line(
                        f"[-]: Already downloaded: "
                        f"{illust.title} "
                        f"(id: {illust.id})",
                        history=False,
                    )                    
                                        
                    continue
                
                while True:

                    try:

                        image_data: PixivMetadata = PixivMetadata(illust)
                        self.save_index(image_data, BOOKMARKS_DIR)
                        urls.append(image_data)

                        ui.line(
                            f"[+]: "
                            f"[{urls_len + idx + 1:0{d_width}d}/"
                            f"{total:0{d_width}d}]: "
                            f"{illust.title} "
                            f"(id: {illust.id}) [Indexed]",
                            history=False,
                        )

                        break

                    except Exception as e:

                        ui.line(
                            " | ",
                            home=False,
                            clear=False,
                            history=False,
                        )

                        ui.line(
                            f"[!]: Failed: "
                            f"{type(e).__name__}: {e}",
                            ui.COLOR_ERROR,
                            home=False,
                            clear=False,
                        )                        

                        action = prompt_error_menu(
                            {
                                "A": "Abort",
                                "R": "Retry",
                                "C": "Continue",
                            },
                            valid="ARC",
                            default="C",
                        )

                        if action == "A":

                            ui.line(
                                "[!]: Operation interrupted by user."
                            )

                            # Ritorna al processo chiamante
                            return urls
                    
                        if action == "C":
                            break

                        if action == "R":
                            
                            ui.clear_lines(1)

                            continue

            urls_len = len(urls)
            random_api_delay(PIXIV_API_DELAY_MIN)

        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    def add_list_to_bookmarks(self, file_path: Path) -> None:

        ui.line()
        ui.line("[+]: Adding bookmarks from URL list...")

        lines = file_path.read_text(encoding="utf-8").splitlines()

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

                self.aapi.illust_bookmark_add(
                    illust_id,
                    restrict="private",
                )
                
                added += 1

            except Exception as e:

                errors += 1
                
                ui.line(
                    f" [!]: Error: {type(e).__name__}: {e}",
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

    def convert_bookmarks_to_private(self) -> None:
        pass
