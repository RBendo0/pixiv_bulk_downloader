from __future__ import annotations

import random
import time
import re
import json
import shutil
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from .my_gppt import LoginInfo
    from pixivpy3 import AppPixivAPI
    from pixivpy3.utils import JsonDict

    from .pixiv_types import IllustInfo

# Legge il nome del file di indicizzazione
from .const import FETCH_CHECKPOINT_FILE

class PixivBaseDownloader:

    # Limite massimo cartelle per sottogruppo
    GROUP_SIZE = 500

    def __init__(
        self, aapi: AppPixivAPI, login_info: LoginInfo, save_dir: Path
    ) -> None:
        self.aapi = aapi
        self.login_info = login_info
        self.save_dir = save_dir

    # Calcola il GROUP_ID
    def get_bucket(self, id_: int) -> str:
        return f"{id_ // self.GROUP_SIZE:06d}"

    # Crea una nuova cartella 
    def create_dir(
        self,
        save_path: Path,
        id_: int,
        title: str | None = None,
    ) -> Path:

        bucket = self.get_bucket(id_)

        folder_name = str(id_)

        if title is not None:
            folder_name += f"_{title}"

        work_dir = save_path / bucket / folder_name

        work_dir.mkdir(parents=True, exist_ok=True)

        return work_dir

    @staticmethod
    def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
        time.sleep(base + rand * random.random())  # noqa: S311

    @staticmethod
    def ext_links(illust: JsonDict) -> list[str] | str:
        links: list[str] = [page.image_urls.original for page in illust.meta_pages]
        link: str = illust.meta_single_page.get(
            "original_image_url",
            illust.image_urls.large,
        )

        return links if links != [] else link

    def retrieve_works(self, target_id: int) -> list[IllustInfo]:
        
        urls: list[IllustInfo] = []
        next_qs: dict[str, Any] | None = {}
        while next_qs is not None:
            print(next_qs)
            if next_qs == {}:
                res_json = self.aapi.user_illusts(target_id, type="illust")
            else:
                res_json = self.aapi.user_illusts(**next_qs)
            if "error" in res_json and "invalid_grant" in res_json["error"]["message"]:
                self.aapi.auth()
                continue
            for illust in res_json["illusts"]:
                urls.append(  # noqa: PERF401
                    {
                        "id": illust.id,
                        "title": illust.title,
                        "link": self.ext_links(illust),
                    },
                )
            next_qs = self.aapi.parse_qs(res_json["next_url"])
#            self.rand_sleep(1.5)
            self.rand_sleep(1.5)
        return urls

    def download(self, data: list[IllustInfo], save_path: Path) -> None:
        save_path.mkdir(parents=True, exist_ok=True)
        data_len = len(data)
        d_width = len(str(data_len))
        for idx, image_data in enumerate(data):
            title, id_ = image_data["title"], image_data["id"]
            title = re.sub(r'[\\/:*?"<>|]', "_", title)
            links = image_data["link"]
            print(
                f"\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                % (idx + 1, data_len, title, id_),
            )
            self.__download(links, title, id_, save_path)

            # ATTENZIONE Rende il bookmark privato
            try:
                self.aapi.illust_bookmark_add(id_, restrict="private")
            except Exception as e:
                print(f"[!]: Bookmark privacy update failed: {id_} -> {e}")

            print("\033[K\033[A\033[K", end="", flush=True)

    def __download(
        self,
        links: str | list[str],
        title: str,
        id_: int,
        save_path: Path,
    ) -> None:

        # Crea la cartella di download
        work_dir = self.create_dir(save_path, id_, title)

        if isinstance(links, str):
            links = [links]
#       elif isinstance(links, list):
#       Mettere qui in futuro eventuale ordinamento della lista "links" di url da scaricare

        # Versione che genera il nome confidando che la lista di url
        # sia ordinata secondo l'ordine naturale delle immagini 
#       for idx, link in enumerate(links):
#
#           ext = link.split(".")[-1].split("?")[0]
#           fname = f"p{idx}.{ext}"
#
#           print(time.time(), fname)
#
#           self.aapi.download(link, path=str(work_dir), fname=fname)

        # Versione che genera il nome estraendolo dall'url
        for link in links:

            basename = link.split("/")[-1].split("?")[0]
            fname = basename.split("_")[-1]

            print(time.time(), fname)

            self.aapi.download(link, path=str(work_dir), fname=fname)

        # Elimina eventuale fetch checkpoint
        fetch_dir = save_path / self.get_bucket(id_) / str(id_)
        if fetch_dir.exists():
            shutil.rmtree(fetch_dir)

    def save_index(
        self,
        data: list[IllustInfo],
        save_path: Path,
    ) -> None:

        # Se non esiste, crea cartella capostipite
        save_path.mkdir(parents=True, exist_ok=True)

        data_len = len(data)
        d_width = len(str(data_len))

        for idx, image_data in enumerate(data):

            title, id_ = image_data["title"], image_data["id"]

            print(
                f"\033[K[+]: Indexed [%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                % (idx + 1, data_len, title, id_),
            )

            # Crea la cartella di indicizzazione
            work_dir = self.create_dir(save_path, id_, title)

            # Crea percorso file indice
            index_file = work_dir / FETCH_CHECKPOINT_FILE

            #salva il record di dati
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(image_data, f)

    def rebuild_index(
        self,
        save_path: Path,
    ) -> list[IllustInfo]:

        data: list[IllustInfo] = []

        if not save_path.exists():
            return data

        for bucket_dir in save_path.iterdir():

            if not bucket_dir.is_dir():
                continue

            for work_dir in bucket_dir.iterdir():

                if not work_dir.is_dir():
                    continue

                index_file = work_dir / FETCH_CHECKPOINT_FILE

                if not index_file.exists():
                    continue

                try:
                    with open(index_file, "r", encoding="utf-8") as f:
                        image_data: IllustInfo = json.load(f)

                    data.append(image_data)

                except Exception as e:
                    print(f"[!]: Failed to load index: {index_file} -> {e}")

        data.sort(key=lambda x: x["id"])

        return data

    def resume_pending_jobs(
        self,
        save_path: Path,
    ) -> None:
        pass
