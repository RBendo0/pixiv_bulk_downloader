from __future__ import annotations

import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Lock, get_ident

from pixiv_bulk_downloader.const import PBD_ROOT
from pixiv_bulk_downloader.metadata import PixivMetadata
from pixiv_bulk_downloader.my_gppt import PixivAuth
from pixiv_bulk_downloader.ui import InputPending, ui

WORKERS = 48
FETCH_BATCH_PAGES = 10
RECOVERY_DELAYS = [30, 60, 90]
TEST_DIR = PBD_ROOT / "_rate_limit_download_test"

THREAD_LOCK = Lock()
THREAD_SLOTS = {}
NEXT_SLOT = 0

# COMPLETED_LOCK = Lock()
COMPLETED = 0
TOTAL = 0

PRINT_LOCK = Lock()

# PANEL_LOCK = Lock()
PANEL = bytearray(b"_" * WORKERS)
PANEL_COLUMNS = 16


def increment_completed() -> int:
    global COMPLETED
    COMPLETED += 1
    return COMPLETED


def get_completed() -> int:
    return COMPLETED
    

def push(slot: int, code: str) -> None:
    PANEL[slot] = ord(code[0])


def get_panel_line() -> str:
    return PANEL.decode("ascii")


"""
def print_panel_loop() -> None:
    while True:
        completed = get_completed()
        lines = get_panel_lines()
        progress = f"[{completed:04d}/{TOTAL:04d}]"

        print("\r", end="")
        for row, line in enumerate(lines):
            if row > 0:
                print()
            print(f"{progress} {line}", end="")

        # sys.stdout.flush()

        if completed >= TOTAL:
            print()
            return

        # sleep(2)
"""


def probe_download(
    aapi,
    target: dict,
    idx: int,
) -> tuple[int, int, str, dict]:
        
    link = target["link"]

    global NEXT_SLOT

    thread_id = get_ident()

    with THREAD_LOCK:
        if thread_id not in THREAD_SLOTS:
            THREAD_SLOTS[thread_id] = NEXT_SLOT
            NEXT_SLOT += 1

        slot = THREAD_SLOTS[thread_id]

    try:

        push(slot, "R")

        with aapi.requests_call(
            "GET",
            link,
            headers={"Referer": "https://app-api.pixiv.net/"},
            stream=True,
        ) as response:
            status = response.status_code
            body = ""

            if status >= 400:
                body = response.text[:500]

            if status < 400:
                for _ in response.iter_content(chunk_size=1024 * 256):
                    pass

            response.close()
        
            return idx, status, body, target
        
    except Exception as e:

        name = type(e).__name__
        msg = repr(e)

        if name == "RemoteDisconnected" or "RemoteDisconnected" in msg:
            code = "_"
        else:
            code = "X"

        push(slot, code)

        progress = f"[{get_completed():04d}/{TOTAL:04d}]"

        line = get_panel_line()

        with PRINT_LOCK:
            print(
                f"\r{progress} {line:<32}",
                end="",
            )

        return (
            idx,
            -1,
            f"{type(e).__module__}."
            f"{type(e).__name__}: "
            f"{e!r}",
            target,
        )
    
    finally:
        increment_completed()


def print_exception(title: str, e: Exception) -> None:
    ui.line(
        f"[!]: {title}: {type(e).__name__}: {e}",
        ui.COLOR_ERROR,
    )
    ui.line(f"[i]: repr: {repr(e)}")
    ui.line(f"[i]: args: {getattr(e, 'args', None)}")
    ui.line(f"[i]: module: {type(e).__module__}")


def main() -> None:
    aapi, login_info = PixivAuth().auth()
    aapi.requests_kwargs["timeout"] = (10, 60)

    target_id = login_info["response"]["user"]["id"]

    user_abort = InputPending("Q")
    user_abort.reset()
    
    ui.line("[+]: Fetching public bookmarks...")

    try:

        ugoira = None

        res_json = aapi.user_bookmarks_illust(
            target_id,
            restrict="public",
        )

        next_json = res_json
        next_qs = {}
        page_number = 0
        download_targets = []

        while next_qs is not None:

            page_number += 1

            ui.line(
                f"[+]: Fetch page {page_number} ",
                history=False,
            )            

            illusts = res_json["illusts"]

            for illust in illusts:

                if illust.type == "ugoira":
                    if ugoira is None:
                        ugoira = illust
                        # ugoira_data = PixivMetadata(illust)
                    continue

                image_data = PixivMetadata(illust)

                for page, link in enumerate(image_data.get_links()):
                    download_targets.append(
                        {
                            "id": image_data.id,
                            "title": image_data.title,
                            "page": page,
                            "link": link,
                        }
                    )

            if (
                page_number % FETCH_BATCH_PAGES == 0
                and download_targets
            ):

                ui.line(
                    f"[+]: Download page {page_number} "
                    f"| URLs: {len(download_targets)}"
                )

                global COMPLETED, TOTAL, NEXT_SLOT
                
                COMPLETED = 0
                TOTAL = len(download_targets)

                PANEL[:] = b"_" * WORKERS

                THREAD_SLOTS.clear()
                NEXT_SLOT = 0                

                with ThreadPoolExecutor(max_workers=WORKERS) as executor:

                    # printer = Thread(target=print_panel_loop)
                    # printer.start()

                    futures = [
                        executor.submit(
                            probe_download,
                            aapi,
                            target,
                            idx,
                        )
                        for idx, target in enumerate(download_targets, 1)
                    ]

                    while futures:
                        done, pending = wait(
                            futures,
                            return_when=FIRST_COMPLETED,
                        )

                        for future in done:
                            
                            futures.remove(future)
                            
                            idx, status, body, target = future.result()

                            completed = get_completed()
                            print(
                                f"\r[{completed:04d}/{TOTAL:04d}]",
                                end="",
                            )

                            """
                            completed += 1

                            # stampa pannello
                            lines = get_panel_lines()
                            progress = f"[{completed:04d}/{len(download_targets):04d}]"

                            print("\r", end="")
                            for row, line in enumerate(lines):
                                if row > 0:
                                    print()
                                print(f"{progress} {line}", end="")

                            sys.stdout.flush()
                            """

                            if status == -1:
                                print()
                                print(f"[!]: {body}")
                                print(f"[i]: idx: {idx}/{TOTAL}")
                                print(f"[i]: id: {target['id']} p{target['page']}")
                                print(f"[i]: panel: {get_panel_line()}")

                    # printer.join()

                download_targets = []

            next_qs = (
                None
                if next_json is None
                else aapi.parse_qs(
                    next_json.get("next_url")
                )
            )

            if next_qs is None:
                next_json = None
            else:
                res_json = next_json = (
                    aapi.user_bookmarks_illust(
                        **next_qs
                    )
                )

    except Exception as e:
        print_exception("Failed while fetching test artworks", e)
        return

    TEST_DIR.mkdir(parents=True, exist_ok=True)

    ui.line()
    ui.line("[+]: Test completed without HTTP error or exception.")


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        ui.line()
        ui.line("[!]: Test interrupted by user.")

    except Exception as e:
        ui.line()
        print_exception("Unhandled exception", e)
        sys.exit(1)