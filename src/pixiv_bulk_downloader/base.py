from __future__ import annotations

from pathlib import Path

from .const import (
    FETCH_CHECKPOINT_FILE,
    PBD_ROOT,
    UGOIRA_ZIP_FILE,
    WORK_METADATA_FILE,
)
from .errors import (
    DownloadRateLimitError,
    PBDError,
    rcc,
)
from .metadata import PixivMetadata
from .pbd_path import PixivPath
from .pixiv_call_api import caapi
from .ui import ui
from .tps import TPS


class PixivBaseDownloader:

    # Mantenuto per eventuali modifiche future. 
    save_dir = PBD_ROOT

    artwork_pool = TPS(
        thread_name_prefix="ARTWORK",
    )

    image_pool = TPS(
        thread_name_prefix="IMAGE",
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

            ui.Renderer.write(
                progress,
                main=True,
            )

            # Salva l'intero dump dei metadata, animazioni comprese
            metadata_file = work_dir / WORK_METADATA_FILE
            image_data.save(metadata_file)

        except Exception as e:

            e = PBDError.cast(e)                    

            ui.line(
                f"{progress} | ",
                history=False,
            )

            ui.line(
                f"[!]: Failed to save metadata: "
                f"{e.info()}: "
                f"{type(e).__name__}: {e} "
                f"(checkpoint preserved)",
                ui.COLOR_WARNING,
                home=False,
                clear=False,
            )

            keep_checkpoint = True

        # Versione che genera il nome estraendolo dall'url
        for link in links:


# CICLO DI MEDIA


        if not keep_checkpoint:

            checkpoint_file = (
                work_dir
                / FETCH_CHECKPOINT_FILE
            )

            if checkpoint_file.exists():

                checkpoint_file.unlink()

        # E' stata richiesta l'interruzione, esce dal ciclo
        if user_abort.is_requested:

            ui.line("[!]: Download interrupted by user.")

            break
































    @classmethod
    def _download_media(
        cls,
    ):

                    basename = link.split("/")[-1].split("?")[0]
                    fname = UGOIRA_ZIP_FILE.name if _is_ugoira_ else basename.split("_")[-1] 

                    while True:

                        ui.line(
                            f"{progress} | {fname}",
                            history=False,
                        )

                        try:
                            
                            caapi.download(
                                link,
                                path=str(work_dir),
                                fname=fname,
                            )                            

                            break

                        except DownloadRateLimitError as e:

                            ui.line(
                                " | ",
                                home=False,
                                clear=False,
                                history=False,
                            )

                            ui.line(
                                f"[!]: {e.info()}: "
                                f"{type(e).__name__}: {e} "
                                f"(id: {_id_})",
                                ui.COLOR_WARNING,
                                home=False,
                                clear=False,
                            )

                            if rcc.wait_rate_limit() == rcc.Action.ABORT:

                                ui.line(
                                    "[!]: Operation interrupted by user.",
                                )

                                return 
                            
                            ui.line(
                                "[i]: Access limited by the service. Retrying in a moment."
                            )

                            continue

                        except Exception as e:

                            e = PBDError.cast(e)

                            ui.line(
                                " | ",
                                home=False,
                                clear=False,
                                history=False,
                            )

                            ui.line(
                                f"[!]: Download failed: "
                                f"{e.info()}: "
                                f"{type(e).__name__}: {e} "
                                f"(checkpoint preserved)",
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
                                ui.line("[!]: Operation interrupted by user.")
                                return

                            if action == rcc.Action.CONTINUE:
                                keep_checkpoint = True
                                break

                            if action == rcc.Action.RETRY:
                                ui.clear_lines(1)
                                continue

                    # Rileva se è stata richiesta l'interruzione del processo
                    if user_abort.is_requested and not user_abort.is_notified:

                        if not _is_ugoira_:
                            ui.line(
                                "[!]: Download interruption requested. "
                                "Waiting for completion of the current artwork."
                            )

                        user_abort.set_notified()
























    @classmethod
    def download(cls, data: list[PixivMetadata], save_path: Path) -> None:
                
        ui.line()
        ui.line("[+]: Downloading pending works...")

        # Chiede conferma a procedere
        if not ui.confirm():
            return

        # Imposta interruzione da utente
        user_abort = ui.InputPending(
            valid="Q",
            prompt="Press Q to interrupt the process."
        )

        # Stampe informative
        ui.line("[i]: " + user_abort.prompt)
                
        data_len = len(data)
        d_width = len(str(data_len))
        
        for idx, image_data in enumerate(data):

            progress = (
                f"[+]: "
                f"[{idx + 1:0{d_width}d}/"
                f"{data_len:0{d_width}d}]: "
                f"{image_data.title} "
                f"(id: {image_data.id})"
            )


# CICLO DI OPERA







        else:

            ui.line("[+]: Download completed.")            

        ui.Renderer.stop()

        ui.line("[+]: Download completed.")            

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
                    f"{e.info()}: "
                    f"{type(e).__name__}: {e}",
                    ui.COLOR_ERROR,
                )

        data.sort(key=lambda x: x.id)

        return data
    
    @classmethod
    def resume_pending_jobs(
        cls,
    ) -> None:

        ui.line("[+]: Rebuilding pending jobs index...")

        pending = cls.rebuild_index(cls.save_dir)

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
            cls.save_dir,
        )