from __future__ import annotations

import re

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import PixivBaseDownloader
from .const import BOOKMARKS_DIR

if TYPE_CHECKING:
    from pixivpy3.utils import JsonDict

    from .pixiv_types import IllustInfo


class PixivBookmarksDownloader(PixivBaseDownloader):
    def get_all_bookmarked_works(self, mode: str = "all") -> None:
        print("[+]: Fetching information of bookmarked works...")
        bookmarked_data = self.retrieve_bookmarks(mode)

        # Salva l'indice delle opere da scaricare
        self.save_index(bookmarked_data, Path(self.save_dir) / "bookmarks")

        print("\n[+]: Downloading bookmarked works...")
        self.download(bookmarked_data, Path(self.save_dir) / "bookmarks")

    def retrieve_bookmarks(self, mode: str = "all") -> list[IllustInfo]:
        urls: list[IllustInfo] = []
        next_qs: dict[str, Any] | None = {}
        target_id = self.login_info["response"]["user"]["id"]
        total = self.aapi.user_detail(self.aapi.user_id)["profile"][
            "total_illust_bookmarks_public"
        ]
        d_width = len(str(total))
        urls_len = 0

        # Lista ID già scaricati
        local_ids = set()

        # Se necessario scarica la lista di tutti i lavori già presenti in locale
        if mode in ("missing", "chrono"):
#           for folder in BOOKMARKS_DIR.iterdir():
            for folder in BOOKMARKS_DIR.rglob("*_*"):
                local_ids.add(folder.name.split("_")[0])
        
        # Prima inizializzazione della pagina corrente e successiva 
        res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id)
        next_json: JsonDict | None = res_json

        # Imposta ultima pagina non ancora raggiunta (solo modalità chrono)
        is_chrono_last_missing_page = False

        while next_qs is not None:
#           if "user_id" not in next_qs:
#               res_json: JsonDict = self.aapi.user_bookmarks_illust(target_id)
#           else:
#               res_json = self.aapi.user_bookmarks_illust(**next_qs)

            # Passa alla pagina successiva   
            next_qs = self.aapi.parse_qs(next_json["next_url"])
            if next_qs is None:
                # Raggiunta l'ultima pagina dell'intero set di bookmarks
                next_json = None
            else:
                next_json = self.aapi.user_bookmarks_illust(**next_qs)

            # Modalità Chrono, se il primo ID della pagina corrente è presente in locale, termina la scansione
            if mode == "chrono":
                if str(res_json["illusts"][0].id) in local_ids:
                    print(
                        f"\033[K[-]: Last chrono page reached: %s (id: %d)"
                        % (illust.title, illust.id),
                        end="\r",
                        flush=True,
                    )
                    break
                # Rileva se quella corrente è l'ultima pagina da scaricare (solo modalità chrono)                
                if next_json is not None:
                    is_chrono_last_missing_page = (str(next_json["illusts"][0].id) in local_ids)

            for idx, illust in enumerate(res_json["illusts"]):

                # Modalità Missing o Chrono ultima pagina, se l'ID corrente è presente in locale, salta il ciclo
                if (mode == "missing" or is_chrono_last_missing_page) and str(illust.id) in local_ids:
                    print(
                        f"\033[K[-]: Already downloaded: %s (id: %d)"
                        % (illust.title, illust.id),
                        end="\r",
                        flush=True,
                    )
                    continue

                print(
                    f"\033[K[+]: [%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                    % (urls_len + idx + 1, total, illust.title, illust.id),
                    end="\r",
                    flush=True,
                )
                urls.append(
                    {
                        "id": illust.id,
                        "title": illust.title,
                        "link": self.ext_links(illust),
                    },
                )

            # Aggiorna la pagina successiva
            if next_json is not None:
                res_json = next_json

#           next_qs = self.aapi.parse_qs(res_json["next_url"])
            urls_len = len(urls)
            self.rand_sleep(0.5)
        return urls

    # Aggiunge nuovi bookmarks all'account, a partire da una lista di url in un file .txt
    def add_list_to_bookmarks(self, file_path) -> None:

#       with open(file_path, "r", encoding="utf-8") as f:

#           for line in f:

        lines = file_path.read_text(encoding="utf-8").splitlines()

        total = len(lines)

        added = 0
        errors = 0
        skipped = 0

        for idx, line in enumerate(lines):

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


