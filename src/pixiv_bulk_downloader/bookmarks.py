from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import PixivBaseDownloader
from .const import BOOKMARKS_DIR
from .metadata import PixivMetadata
from .pixiv_errors import (
    PixivApiError,
    RateLimitError,
    is_rate_limited,
    prompt_error_menu,
    wait_rate_limit,
)
from .pixiv_types import BookmarkMode, BookmarkOptions, BookmarkPrivacy
from .timing import (
    PIXIV_API_DELAY_MIN,
    random_api_delay,
)
from .ui import ui
from .utils import abort_requested

if TYPE_CHECKING:
    from pixivpy3.utils import JsonDict

import random


class PixivBookmarksDownloader(PixivBaseDownloader):
    def interact(self) -> BookmarkOptions:

        while True:

            print(
                "\n"
                "Modalità download\n"
                "\n"
                "[1] Scarica tutti i preferiti nell'archivio locale\n"
                "[2] Scarica solo i preferiti non ancora salvati in locale\n"
                "[3] Scarica solo i preferiti aggiunti di recente\n"
            )

            choice = input("Scelta: ").strip()

            mode_map: dict[str, BookmarkMode] = {
                "1": "all",
                "2": "missing",
                "3": "chrono",
            }

            mode = mode_map.get(choice)

            if mode is not None:
                break

            print("[!]: Selezione non valida.")

        while True:

            print(
                "\n"
                "Visibilità bookmark\n"
                "\n"
                "[1] Pubblici\n"
                "[2] Privati\n"
            )

            choice = input("Scelta: ").strip()

            privacy_map: dict[str, BookmarkPrivacy] = {
                "1": "public",
                "2": "private",
            }

            restrict = privacy_map.get(choice)

            if restrict is not None:
                break

            print("[!]: Selezione non valida.")

        return {
            "mode": mode,
            "restrict": restrict,
        }

    def download_bookmarks(self) -> None:

        options = self.interact()

        print("\n[+]: Fetching information of bookmarked works...")
        print("[i]: Premere Q per interrompere il processo.")

        bookmarked_data = self.retrieve_bookmarks(**options)

        print("\n[+]: Downloading bookmarked works...")
        print("[i]: Premere Q per interrompere il processo.")

        self.download(bookmarked_data, BOOKMARKS_DIR)

    def retrieve_bookmarks(
        self,
        mode: BookmarkMode = "all",
        restrict: BookmarkPrivacy = "public",
    ) -> list[PixivMetadata]:
        is_fatal_abort = False
        is_abort_requested = False
        urls: list[PixivMetadata] = []
        next_qs: dict[str, Any] | None = {}
        target_id = self.login_info["response"]["user"]["id"]

        try:

            # Numero di opere totali
            total = self.aapi.user_detail(self.aapi.user_id)["profile"][
                "total_illust_bookmarks_public"
            ]

            # Prima inizializzazione della pagina corrente e successiva 
            res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id, restrict=restrict)
            next_json: JsonDict | None = res_json

        except Exception as e:

            print(
                f"[!]: API call failed: "
                f"{type(e).__name__}: {e}"
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

        while next_qs is not None:

            # E' stata richiesta l'interruzione, esce dal ciclo
            if is_fatal_abort or is_abort_requested:
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

                test_case = random.randint(1, 10)

                if test_case == 1:
                    # raise StorageError("Storage test")
                    pass

                elif test_case == 2:
                    raise PixivApiError("Pixiv API test")

                elif test_case == 3:
                    raise RateLimitError("Rate limit test")
                
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

                print(
                    "\n"
                    f"[!]: {e} | "
                    f"Page: {page_number} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}"
                )

                if not wait_rate_limit():

                    is_fatal_abort = True
                    continue

                page_number -= 1

                continue

            except PixivApiError as e:

                print(
                    "\n"
                    f"[!]: API call failed: {e} | "
                    f"Page: {page_number} | "
                    f"Last artwork: "
                    f"{urls[-1].id if urls else 'N/A'}"
                )

                action = prompt_error_menu(
                    {
                        "A": "Abort",
                        "R": "Retry",
                    },
                    default_action="R",
                    timeout=10,
                )

                if action == "A":

                    is_fatal_abort = True

                else:

                    page_number -= 1

                continue

            # Modalità Chrono, primo ID pagina corrente presente in locale, termina
            if mode == "chrono":
                if str(res_json["illusts"][0].id) in local_ids:
                    print(
                        "\033[K[-]: Last chrono page reached.",
                        end="\n",
                        flush=True,
                    )
                    break
                # Rileva se e è l'ultima pagina da scaricare (solo modalità chrono)
                if next_json is not None:
                    is_chrono_last_missing_page = (str(next_json["illusts"][0].id) in local_ids)

            for idx, illust in enumerate(res_json["illusts"]):

                # Rileva se è stata richiesta l'interruzione del processo
                if not is_abort_requested and abort_requested():
                    print("\n[!]: Richiesta interruzione, attendere completamento pagina corrente.")
                    is_abort_requested = True

                # Modalità Missing o Chrono ultima pagina, se l'ID corrente è presente in locale, salta il ciclo
                if (mode == "missing" or is_chrono_last_missing_page) and str(illust.id) in local_ids:
                    print(
                        "\033[K[-]: Already downloaded: %s (id: %d)"
                        % (illust.title, illust.id),
                        end="\r",
                        flush=True,
                    )
                    continue

                while True:

                    try:

                        image_data: PixivMetadata = PixivMetadata(illust)
                        self.save_index(image_data, BOOKMARKS_DIR)
                        urls.append(image_data)

                        print(
                            f"\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d) [Indexed]"
                            % (
                                urls_len + idx + 1,
                                total,
                                illust.title,
                                illust.id,
                            ),
                            end="\r",
                            flush=True,
                        )

                        break

                    except Exception as e:

                        print(
                            "\n"
                            f"[!]: Artwork processing failed: "
                            f"{illust.id} -> "
                            f"{type(e).__name__}: {e}"
                        )

                        action = prompt_error_menu(
                            {
                                "A": "Abort",
                                "R": "Retry",
                                "C": "Continue",
                            },
                            default_action="C",
                        )

                        if action == "A":
                            is_fatal_abort = True
                            break

                        if action == "C":
                            break

                        if action == "R":
                            continue

                # Interruzione a seguito di errore fatale
                if is_fatal_abort:
                    break

            urls_len = len(urls)
            random_api_delay(PIXIV_API_DELAY_MIN)
        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    def add_list_to_bookmarks(self, file_path: Path) -> None:

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
                print(f"[!]: Invalid URL: {url}")
                continue

            illust_id = int(match.group(1))

            print(f"[+]: Adding bookmark: {illust_id}")

            try:

                self.aapi.illust_bookmark_add(
                    illust_id,
                    restrict="private",
                )
                added += 1

            except Exception as e:

                errors += 1
                print(f"[!]: Error adding {illust_id}: {e}")

            random_api_delay(PIXIV_API_DELAY_MIN)

        print()
        print(f"[+]: Added bookmarks : {added}")
        print(f"[-]: Skipped URLs    : {skipped}")
        print(f"[!]: Errors          : {errors}")

    def convert_bookmarks_to_private(self) -> None:
        pass
