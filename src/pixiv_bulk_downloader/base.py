from __future__ import annotations

import json
import random
import shutil
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pixivpy3 import AppPixivAPI
    
    from .my_gppt import LoginInfo

from .const import (
    FETCH_CHECKPOINT_FILE,
    UGOIRA_METADATA_FILE,
    UGOIRA_ZIP_FILE,
    WORK_METADATA_FILE,
)
from .metadata import PixivMetadata
from .pixiv_path import PixivPath
from .utils import abort_requested


class PixivBaseDownloader:

    # Limite massimo cartelle per sottogruppo
    GROUP_SIZE = 500

    def __init__(
        self, aapi: AppPixivAPI, login_info: LoginInfo, save_dir: Path
    ) -> None:
        self.aapi = aapi
        self.login_info = login_info
        self.save_dir = save_dir

    # Crea una nuova cartella 
    def work_dir(
        self,
        save_path: Path,
        id_: int,
        title: str | None = None,
    ) -> PixivPath:

        w_dir = (
            PixivPath(save_path)
            .work_dir(id_, title)
        )

        w_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return w_dir

    def fetch_dir(
        self,
        save_path: Path,
        id_: int        
    ) -> PixivPath:

        f_dir = (
            PixivPath(save_path)
            .work_dir(id_)
        )

        f_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return f_dir

    @staticmethod
    def rand_sleep(base: float = 0.1, rand: float = 2.5) -> None:
        time.sleep(base + rand * random.random())  # noqa: S311
  
    def download(self, data: list[PixivMetadata], save_path: Path) -> None:
        # Ridondante
        # save_path.mkdir(parents=True, exist_ok=True)
        is_abort_requested = False
        data_len = len(data)
        d_width = len(str(data_len))
        for idx, image_data in enumerate(data):

            download_ok = True

            _id_ = image_data.id
            print(
                f"\033[K[%0{d_width}d/%0{d_width}d]: %s (id: %d)"
                % (idx + 1, data_len, image_data.title, _id_),
            )

            try:

                # Crea la cartella di download
                work_dir = self.work_dir(save_path, _id_, image_data.path_title)

                # Salva l'intero dump dei metadata
                metadata_file = work_dir / WORK_METADATA_FILE
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(
                        image_data.to_dict(),
                        f,
                        indent=4,
                        ensure_ascii=False,
                        default=str,
                    )

                # Discrimina il tipo di opera
                if image_data.is_ugoira:

                    ugoira_data = self.aapi.ugoira_metadata(_id_)

                    # Salva il dump metadata delle animazioni
                    metadata_file = work_dir / UGOIRA_METADATA_FILE
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(
                            ugoira_data,
                            f,
                            indent=4,
                            ensure_ascii=False,
                            default=str,
                        )

                    zip_url = ugoira_data["ugoira_metadata"]["zip_urls"]["medium"]

                    self.aapi.download(
                        zip_url,
                        path=str(work_dir),
                        fname=UGOIRA_ZIP_FILE.name,
                    )

                    # Rileva se è stata richiesta l'interruzione del processo
                    if not is_abort_requested and abort_requested():
                        is_abort_requested = True

                else:

                    links = image_data.get_links()            

                    # Versione che genera il nome estraendolo dall'url
                    for link in links:

                        basename = link.split("/")[-1].split("?")[0]
                        fname = basename.split("_")[-1]

                        print("\033[K" + fname, end="\r")

                        self.aapi.download(link, path=str(work_dir), fname=fname)

                        # Rileva se è stata richiesta l'interruzione del processo
                        if not is_abort_requested and abort_requested():
                            print("\n[!]: Richiesta interruzione, attendere completamento download opera.")
                            is_abort_requested = True

            except Exception as e:

                print(
                    f"\n[!]: Download failed: {_id_} -> {type(e).__name__}: {e}"
                )

                print(
                    "[i]: Checkpoint preserved for future resume."
                )

                download_ok = False

            if download_ok:

                # Elimina eventuale fetch checkpoint
                fetch_dir = (
                    PixivPath(save_path)
                    .work_dir(_id_)
                )

                if fetch_dir.exists():
                    shutil.rmtree(fetch_dir)

            """
            # ATTENZIONE Rende il bookmark privato
            try:
                self.aapi.illust_bookmark_add(_id_, restrict="private")
            except Exception as e:
                print(f"[!]: Bookmark privacy update failed: {_id_} -> {e}")
            """
            
            print("\033[K\033[A\033[K", end="", flush=True)

            # E' stata richiesta l'interruzione, esce dal ciclo
            if is_abort_requested:
                print("\r\033[K[!]: Download interrotto dall'utente.")
                break
            
    def save_index(
        self,
        image_data: PixivMetadata,
        save_path: Path,
    ) -> None:

        # Ridondante
        # save_path.mkdir(parents=True, exist_ok=True)
         
        # Directory temporanea utilizzata per il checkpoint.
        # Viene eliminata dopo il completamento del download.        
        fetch_dir = self.fetch_dir(save_path, image_data.id)

        # Crea percorso file indice
        index_file = fetch_dir / FETCH_CHECKPOINT_FILE

        # salva il record di dati
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(image_data.to_dict(), f)

    def rebuild_index(
        self,
        save_path: Path,
    ) -> list[PixivMetadata]:

        data: list[PixivMetadata] = []

        found = 0

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
                        image_data: PixivMetadata = PixivMetadata(data=json.load(f))

                    data.append(image_data)

                    found += 1

                    print(
                        f"\033[K[+]: Pending jobs found: {found}",
                        end="\r",
                        flush=True,
                    )                    

                except Exception as e:
                    print(f"[!]: Failed to load index: {index_file} -> {e}")

        data.sort(key=lambda x: x.id)

        return data

    def resume_pending_jobs(
        self,
        save_path: Path,
    ) -> None:
        print("[+]: Rebuilding pending jobs index...")
        pending = self.rebuild_index(save_path)

        if not pending:
            print("[!]: No pending jobs found.")
            return

        print(f"[+]: Found {len(pending)} pending jobs.")
        print("[i]: Premere Q per interrompere il processo.")
        self.download(pending, save_path) 
