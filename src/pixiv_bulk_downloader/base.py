from __future__ import annotations

import json
import shutil
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
from .pixiv_errors import (
    ContinueShortcut,
    DownloadRateLimitError,
    call_download_api,
    prompt_error_menu,
    wait_rate_limit,
)
from .pixiv_path import PixivPath
from .ui import InputPending, ui


class PixivBaseDownloader:

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

    def download(self, data: list[PixivMetadata], save_path: Path) -> None:
                
        # Imposta interruzione da utente
        user_abort = InputPending(
            valid="Q",
            prompt="Press Q to interrupt the process."
        )

        # Stampe informative
        ui.line("[i]: " + user_abort.prompt)
                
        # Ridondante
        # save_path.mkdir(parents=True, exist_ok=True)
        data_len = len(data)
        d_width = len(str(data_len))
        for idx, image_data in enumerate(data):

            try: 

                # Mantenere il checkpoint?
                keep_checkpoint = False

                _id_ = image_data.id
                _is_ugoira_ = image_data.is_ugoira

                progress = (
                    f"[+]: "
                    f"[{idx + 1:0{d_width}d}/"
                    f"{data_len:0{d_width}d}]: "
                    f"{image_data.title} "
                    f"(id: {_id_})"
                )            

                # Crea la cartella di download
                work_dir = self.work_dir(save_path, _id_, image_data.path_title)

                if _is_ugoira_:

                    zip_url = ""

                    while True:

                        try: 

                            ugoira_data = self.aapi.ugoira_metadata(_id_)
                            zip_url = ugoira_data["ugoira_metadata"]["zip_urls"]["medium"]

                            break

                        except Exception as e:
                            
                            ui.line(
                                f"{progress} |",
                                home=False,
                                clear=False,
                                history=False,
                            )

                            ui.line(
                                f" [!]: Ugoira metadata unavailable: "
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
                                ui.line("[!]: Operation interrupted by user.")
                                return

                            if action == "C":
                                # keep_checkpoint = True
                                raise ContinueShortcut
                                
                            if action == "R":
                                ui.clear_lines(1)
                                continue
                    
                    links = [zip_url]

                else: 
                
                    links = image_data.get_links()            

                try:

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

                    if _is_ugoira_:

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

                except Exception as e:
                    
                    ui.line(
                        f"{progress} |",
                        home=False,
                        clear=False,
                        history=False,
                    )

                    ui.line(
                        f" [!]: Failed to save metadata: "
                        f"{type(e).__name__}: {e} "
                        f"(checkpoint preserved)",
                        ui.COLOR_WARNING,
                        home=False,
                        clear=False,
                    )

                    keep_checkpoint = True

                # Versione che genera il nome estraendolo dall'url
                for link in links:

                    basename = link.split("/")[-1].split("?")[0]
                    fname = UGOIRA_ZIP_FILE.name if _is_ugoira_ else basename.split("_")[-1] 

                    while True:

                        ui.line(
                            f"{progress} | {fname}",
                            history=False,
                        )

                        try:
                            
                            call_download_api(
                                self.aapi.download,
                                link,
                                path=str(work_dir),
                                fname=fname,
                            )

                            break

                        except DownloadRateLimitError as e:

                            ui.line(
                                " |",
                                home=False,
                                clear=False,
                                history=False,
                            )

                            ui.line(
                                f" [!]: {type(e).__name__}: {e} "
                                f"(id: {_id_})",
                                ui.COLOR_WARNING,
                                home=False,
                                clear=False,
                            )

                            if not wait_rate_limit():

                                ui.line(
                                    "[!]: Operation interrupted by user.",
                                )

                                return 
                            
                            ui.line(
                                "[i]: Access limited by the service. Retrying in a moment."
                            )

                            continue

                        except Exception as e:

                            ui.line(
                                " |",
                                home=False,
                                clear=False,
                                history=False,
                            )

                            ui.line(
                                f" [!]: Download failed: "
                                f"{type(e).__name__}: {e} "
                                f"(checkpoint preserved)",
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
                                ui.line("[!]: Operation interrupted by user.")
                                return

                            if action == "C":
                                keep_checkpoint = True
                                break

                            if action == "R":
                                ui.clear_lines(1)
                                continue

                    # Rileva se è stata richiesta l'interruzione del processo
                    if user_abort.is_requested and not user_abort.is_notified:

                        message = "[!]: Operation interrupted by user. " + (
                            "Waiting for completion of the current artwork download." if _is_ugoira_ else ""
                        )

                        ui.line(message)

                        user_abort.set_notified()

                if not keep_checkpoint:

                    # Elimina eventuale fetch checkpoint
                    fetch_dir = (
                        PixivPath(save_path)
                        .work_dir(_id_)
                    )

                    if fetch_dir.exists():
                        shutil.rmtree(fetch_dir)

                # E' stata richiesta l'interruzione, esce dal ciclo
                if user_abort.is_requested:
                    break

            except ContinueShortcut:
                continue
            
    def save_index(
        self,
        image_data: PixivMetadata,
        save_path: Path,
    ) -> None:

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
                    print(
                        f"[!]: Failed to load index: {index_file} "
                        f"-> {type(e).__name__}: {e}"
                    )

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
