from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import PixivBaseDownloader
from .const import BOOKMARKS_DIR
from .metadata import PixivMetadata
from .pixiv_types import BookmarkMode, BookmarkOptions, BookmarkPrivacy
from .utils import abort_requested

if TYPE_CHECKING:
    from pixivpy3.utils import JsonDict


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

        print("[+]: Fetching information of bookmarked works...")
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
        is_abort_requested = False
        urls: list[PixivMetadata] = []
        next_qs: dict[str, Any] | None = {}
        target_id = self.login_info["response"]["user"]["id"]
        total = self.aapi.user_detail(self.aapi.user_id)["profile"][
            "total_illust_bookmarks_public"
        ]
        d_width = len(str(total))
        urls_len = 0

        # Lista ID già scaricati
        local_ids: set[str] = set()

        # Se necessario scarica la lista di tutti i lavori già presenti in locale
        if mode in ("missing", "chrono"):
            for folder in BOOKMARKS_DIR.rglob("*_*"):
                local_ids.add(folder.name.split("_")[0])
        
        # Prima inizializzazione della pagina corrente e successiva 
        res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id, restrict=restrict)
        next_json: JsonDict | None = res_json

        # Imposta ultima pagina non ancora raggiunta (solo modalità chrono)
        is_chrono_last_missing_page = False

        while next_qs is not None:

            # E' stata richiesta l'interruzione, esce dal ciclo
            if is_abort_requested:
                break

            # Passa alla pagina successiva  
            assert next_json is not None
            next_qs = self.aapi.parse_qs(next_json["next_url"])
            if next_qs is None:
                # Raggiunta l'ultima pagina dell'intero set di bookmarks
                next_json = None
            else:
                next_json = self.aapi.user_bookmarks_illust(**next_qs)

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
                image_data: PixivMetadata = PixivMetadata(illust)               
                urls.append(image_data)
                self.save_index(image_data, BOOKMARKS_DIR)
                print(
                    f"\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d) [Indexed]"
                    % (urls_len + idx + 1, total, illust.title, illust.id),
                    end="\r",
                    flush=True,
                )

            # Aggiorna la pagina successiva
            if next_json is not None:
                res_json = next_json

            urls_len = len(urls)
            self.rand_sleep(0.5)
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

            self.rand_sleep(0.5)

        print()
        print(f"[+]: Added bookmarks : {added}")
        print(f"[-]: Skipped URLs    : {skipped}")
        print(f"[!]: Errors          : {errors}")

    def convert_bookmarks_to_private(self) -> None:
        pass
