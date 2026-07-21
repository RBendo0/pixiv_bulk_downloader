from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from .const import (
    FETCH_CHECKPOINT_FILE,
    METADATA_FILE,
    UGOIRA_ZIP_FILE,
)
from .errors import (
    DownloadRateLimitError,
    PBDError,
    rcc,
)
from .metadata import PixivMetadata
from .pbd_path import PixivPath
from .pixiv_call_api import caapi
from .tps import TPS
from .ui import ui

T = TypeVar("T")


class PixivBaseDownloader:

    artwork_pool = TPS(
        thread_name_prefix="ARTWORK",
    )

    image_pool = TPS(
        thread_name_prefix="IMAGE",
    )

    default_abort = ui.InputPending(
        valid="Q",
        prompt="Press Q to interrupt the process.",
    )

    @classmethod
    def pool_shutdown(cls) -> None:

        cls.artwork_pool.shutdown(wait=True)
        cls.image_pool.shutdown(wait=True)    

    # Crea una nuova cartella 
    @classmethod
    def work_dir(
        cls,
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

    @classmethod
    def fetch_dir(
        cls,
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

    @classmethod
    def _download_artwork(
        cls,
        progress: str,
        image_data: PixivMetadata,
        save_path: Path,
    ) -> None:

        # Mantenere il checkpoint?
        keep_checkpoint = False

        # Crea la cartella di download
        work_dir = cls.work_dir(
            save_path,
            image_data.id,
            image_data.path_title,
        )

        if image_data.is_ugoira:

            ugoira_data = image_data.get("ugoira")

            zip_url = (
                ugoira_data["ugoira_metadata"]["zip_urls"]["medium"]
            )

            links = [zip_url]

        else: 
        
            links = image_data.get_links()            

        try:

            overflow = ui.Renderer.in_thread_overflow_width(
                progress, 
                main=True,
            )

            progress = ui.Renderer.truncate_width(
                progress,
                overflow,
            )

            ui.Renderer.in_thread_write(
                progress,
                main=True,
            )

            # Salva l'intero dump dei metadata, animazioni comprese
            metadata_file = work_dir / METADATA_FILE
            image_data.save(metadata_file)

        except Exception as e:

            e = PBDError.cast(e)                    

            ui.line(
                f"{progress} | ",
                history=False,
            )

            ui.line(
                f"[!]: Failed to save metadata: "
                f"{e.report()} "
                f"(checkpoint preserved)",
                ui.COLOR_WARNING,
                home=False,
                clear=False,
            )

            keep_checkpoint = True

        media_futures = []

        media_total = len(links)
        media_width = len(str(media_total))

        for media_idx, link in enumerate(
            links,
            start=1,
        ):
            
            # Rileva se è stata richiesta l'interruzione del processo
            if cls.default_abort.is_requested and not cls.default_abort.is_notified:

                ui.line(
                    "[!]: Download interrupted by user. "
                    "Waiting for completion of pending jobs. ",
                )

                cls.default_abort.set_notified()

            media_prefix = (
                f"{ui.COLOR_DEFAULT}"
                f" | "
                f"[{media_idx:0{media_width}d}/"
                f"{media_total:0{media_width}d}]:"
            )

            basename = link.split("/")[-1].split("?")[0]

            fname = (
                UGOIRA_ZIP_FILE.name
                if image_data.is_ugoira
                else basename.split("_")[-1]
            )
            
            future = cls.image_pool.submit(
                cls._download_media,
                progress,
                media_prefix,
                link,
                work_dir,
                fname,
            )

            media_futures.append(future)

        media_completed = all(
            future.result()
            for future in media_futures
        )

        if not media_completed:

            keep_checkpoint = True

        # Qualcosa è andato storto: mantiene il checkpoint per un successivo tentativo di download
        if not keep_checkpoint:

            checkpoint_file = (
                work_dir
                / FETCH_CHECKPOINT_FILE
            )

            if checkpoint_file.exists():

                checkpoint_file.unlink()

    @classmethod
    def _download_media(
        cls,
        progress: str,
        media_prefix: str,
        link: str,
        work_dir: Path,
        fname: str,
    ) -> bool:

        while True:

            try:

                overflow = ui.Renderer.in_thread_overflow_width(
                    progress + media_prefix + " " + fname
                )

                progress = ui.Renderer.truncate_width(
                    progress,
                    overflow,
                ) + media_prefix

                ui.Renderer.in_thread_write(
                    f"{progress} "
                    f"{ui.COLOR_SUCCESS}"
                    F"{fname}",
                )

                caapi.download(
                    link,
                    path=str(work_dir),
                    fname=fname,
                )                            

                return True

            except DownloadRateLimitError:

                timer = rcc.RateLimitTimer()

                while not timer.expired:

                    status = (
                        f" | "
                        f"{ui.COLOR_WARNING}"
                        f"Access limited by the service. "
                        f"Retrying in {timer.remaining}s."
                    )

                    overflow = ui.Renderer.in_thread_overflow_width(
                        progress + " " + fname + status
                    )

                    display_progress = ui.Renderer.truncate_width(
                        progress,
                        overflow,
                    )                    

                    ui.Renderer.in_thread_write(
                        f"{display_progress} {fname}{status}"
                    )

                    time.sleep(1)

                continue

            except Exception as e:

                e = PBDError.cast(e)

                status = (
                    f" | "
                    f"{ui.COLOR_ERROR}"
                    f"Download failed: "
                    f"{e.report()} "
                    f"(checkpoint preserved)"
                )

                overflow = ui.Renderer.in_thread_overflow_width(
                    progress + " " + fname + status
                )

                display_progress = ui.Renderer.truncate_width(
                    progress,
                    overflow,
                )                    

                ui.Renderer.in_thread_write(
                    f"{display_progress} {fname}{status}"
                )

                return False

    @classmethod
    def download(
        cls,
        data: list[PixivMetadata],
        save_path: Path,
    ) -> None:

        ui.line()
        ui.line("[+]: Downloading pending works...")

        # Chiede conferma a procedere.
        if not ui.confirm():
            return

        # ATTENZIONE:
        # default_abort è persistente.
        # Chiamare sempre reset() prima del primo utilizzo.
        cls.default_abort.reset()

        # Stampe informative
        ui.line("[i]: " + cls.default_abort.prompt)

        data_len = len(data)
        d_width = len(str(data_len))

        submit_failed = False

        for idx, image_data in enumerate(data):

            if cls.default_abort.is_requested:
                break

            progress = (
                f"[{idx + 1:0{d_width}d}/"
                f"{data_len:0{d_width}d}]: "
                f"{ui.COLOR_INPUT}"
                f"<ID:{image_data.id}> "
                f"{image_data.title}"
                f"{ui.COLOR_DEFAULT}"
            )

            try:

                cls.artwork_pool.submit(
                    cls._download_artwork,
                    progress,
                    image_data,
                    save_path,
                )

            except Exception as e:

                e = PBDError.cast(e)

                ui.line(
                    f"[!]: {progress} | ",
                    history=False,
                )

                ui.line(
                    f"Failed to submit artwork: "
                    f"{e.report()}",
                    ui.COLOR_ERROR,
                    home=False,
                    clear=False,
                )

                ui.line(
                    "[!]: Download interrupted. "
                    "Waiting for pending jobs to complete.",
                    ui.COLOR_WARNING,
                )

                submit_failed = True

                break

        # Attende tutte le opere già affidate al pool.
        cls.artwork_pool.wait()
        cls.image_pool.wait()

        # Ferma il thread del renderer e ripulisce il pannello.
        ui.Renderer.stop()

        if submit_failed:

            ui.line(
                "[!]: Download terminated due to an internal error.",
                ui.COLOR_ERROR,
            )

        elif cls.default_abort.is_requested:

            ui.line(
                "[!]: Download interrupted by user.",
            )

        else:

            ui.line("[+]: Download completed.")

        # Reset finale consigliato ma non obbligatorio.
        cls.default_abort.reset()            

    @classmethod
    def save_index(
        cls,
        image_data: PixivMetadata,
        save_path: Path,
    ) -> None:

        """
        DEPRECATO: LA CARTELLA DI CHECKPOINT COINCIDE CON QUELL DELL'OPERA
        # Directory temporanea utilizzata per il checkpoint.
        # Viene eliminata dopo il completamento del download.        
        fetch_dir = cls.fetch_dir(save_path, image_data.id)

        # Crea percorso file indice
        index_file = fetch_dir / FETCH_CHECKPOINT_FILE
        """

        # Crea la cartella definitiva dell'opera.
        work_dir = cls.work_dir(
            save_path,
            image_data.id,
            image_data.path_title,
        )

        # Crea percorso file indice.
        index_file = work_dir / FETCH_CHECKPOINT_FILE

        # salva il record di dati
        image_data.save(index_file)    

    @classmethod
    def scan_archive(
        cls,
        save_path: Path,
        *,
        shared_context: T,
        run_for_each_folder: Callable[
            [T, Path | None, Path | None], 
            None,
        ],
    ) -> None:

        for folder in save_path.rglob("*"):

            if not folder.is_dir():
                continue

            metadata_file = folder / METADATA_FILE
            checkpoint_file = folder / FETCH_CHECKPOINT_FILE

            run_for_each_folder(
                shared_context,
                metadata_file if metadata_file.exists() else None,
                checkpoint_file if checkpoint_file.exists() else None,
            )

    @classmethod
    def rebuild_index(
        cls,
        save_path: Path,
    ) -> list[PixivMetadata]:

        data: list[PixivMetadata] = []

        found = 0

        if not save_path.exists():
            return data

        for index_file in save_path.rglob(
            FETCH_CHECKPOINT_FILE.name
        ):

            try:

                image_data = PixivMetadata()
                image_data.load(index_file)
                
                data.append(image_data)

                found += 1

                ui.line(
                    f"[+]: Pending jobs found: {found}",
                    history=False,
                )

            except Exception as e:

                e = PBDError.cast(e)

                ui.line(
                    f"[!]: Failed to load index: {index_file}: "
                    f"{e.report()}",
                    ui.COLOR_ERROR,
                )

        data.sort(key=lambda x: x.id)

        return data

    @classmethod
    def resume_pending_jobs(
        cls,
        save_path: Path,
    ) -> None:

        ui.line("[+]: Rebuilding pending jobs index...")

        pending = cls.rebuild_index(save_path)

        if not pending:
            ui.line(
                "[!]: No pending jobs found.",
                ui.COLOR_WARNING,
            )
            return

        ui.line(
            f"[+]: Found {len(pending)} pending jobs."
        )

        cls.download(
            pending,
            save_path,
        )