from __future__ import annotations

import shutil
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from pixiv_bulk_downloader.const import PBD_ROOT
from pixiv_bulk_downloader.metadata import PixivMetadata
from pixiv_bulk_downloader.my_gppt import PixivAuth
from pixiv_bulk_downloader.ui import InputPending, ui

WORKERS = 32
FETCH_BATCH_PAGES = 10
RECOVERY_DELAYS = [30, 60, 90]
TEST_DIR = PBD_ROOT / "_rate_limit_download_test"


def probe_download(
    aapi,
    target: dict,
    idx: int,
) -> tuple[int, int, str, dict]:    
    
    link = target["link"]

    try:

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
        
        return idx, -1, f"{type(e).__name__}: {e!r}", target


def probe_recovery(
    aapi,
    link: str,
) -> tuple[int, str]:

    try:

        with aapi.requests_call(
            "GET",
            link,
            headers={"Referer": "https://app-api.pixiv.net/"},
            stream=True,
        ) as response:

            status = response.status_code
            response.close()

            return status, ""

    except Exception as e:

        return -1, f"{type(e).__name__}: {e!r}"
    

def print_exception(title: str, e: Exception) -> None:
    ui.line(
        f"[!]: {title}: {type(e).__name__}: {e}",
        ui.COLOR_ERROR,
    )
    ui.line(f"[i]: repr: {repr(e)}")
    ui.line(f"[i]: args: {getattr(e, 'args', None)}")
    ui.line(f"[i]: module: {type(e).__module__}")


def test_ugoira(aapi, ugoira_data: PixivMetadata) -> None:
    ui.line()
    ui.line(
        f"[+]: Testing ugoira while limited: "
        f"{ugoira_data.title} "
        f"(id: {ugoira_data.id})"
    )

    try:
        metadata = aapi.ugoira_metadata(ugoira_data.id)

        ui.line("[+]: ugoira_metadata() succeeded.")

        zip_url = metadata["ugoira_metadata"]["zip_urls"]["medium"]

        with aapi.requests_call(
            "GET",
            zip_url,
            headers={"Referer": "https://app-api.pixiv.net/"},
            stream=True,
        ) as response:

            status = response.status_code

            ui.line(f"[i]: ugoira zip HTTP status: {status}")

            if status >= 400:
                ui.line(f"[i]: headers: {dict(response.headers)}")
                ui.line(f"[i]: body: {response.text[:500]}")
                return

            test_path = TEST_DIR / "ugoira_test.zip"

            with open(test_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)

            ui.line(f"[+]: ugoira zip downloaded: {test_path}")

    except Exception as e:
        print_exception("Ugoira exception", e)


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
                        ugoira_data = PixivMetadata(illust)
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

                with ThreadPoolExecutor(max_workers=WORKERS) as executor:

                    futures = [
                        executor.submit(
                            probe_download,
                            aapi,
                            target,
                            idx,
                        )
                        for idx, target in enumerate(download_targets, 1)
                    ]

                    completed = 0
                    start_batch = time.monotonic()
                    last_completion = start_batch

                    future_targets = dict(zip(futures, download_targets))

                    submitted_at = {
                        future: time.monotonic()
                        for future in futures
                    }

                    while futures:

                        done, pending = wait(
                            futures,
                            timeout=5,
                            return_when=FIRST_COMPLETED,
                        )

                        if not done:
                            now = time.monotonic()

                            oldest_future = max(
                                pending,
                                key=lambda future: now - submitted_at[future],
                            )

                            oldest_age = now - submitted_at[oldest_future]
                            oldest_target = future_targets[oldest_future]

                            ui.line(
                                f"[i]: Waiting workers | "
                                f"completed: {completed}/{len(download_targets)} | "
                                f"remaining: {len(pending)} | "
                                f"batch elapsed: {now - start_batch:.1f}s | "
                                f"idle: {now - last_completion:.1f}s | "
                                f"oldest pending: {oldest_age:.1f}s"
                            )

                            ui.line(
                                f"[i]: Oldest target: "
                                f"{oldest_target['title']} "
                                f"(id: {oldest_target['id']}) "
                                f"p{oldest_target['page']}"
                            )

                            ui.line(
                                f"[i]: Oldest future idx: "
                                f"{download_targets.index(oldest_target) + 1}/"
                                f"{len(download_targets)}"
                            )                            

                            ui.line(
                                f"[i]: Oldest URL: "
                                f"{oldest_target['link']}"
                            )

                            continue

                        if user_abort.is_requested:
                            if not user_abort.is_notified:
                                user_abort.set_notified()
                                ui.line()
                                ui.line("[!]: Operation interrupted by user.")

                            executor.shutdown(
                                wait=False,
                                cancel_futures=True,
                            )
                            return

                        for future in done:

                            futures.remove(future)

                            idx, status, body, target = future.result()

                            completed += 1
                            last_completion = time.monotonic()

                            ui.line(
                                f"[+]: Download probe "
                                f"[{completed:04d}/{len(download_targets):04d}] "
                                f"| HTTP {status}",
                                history=False,
                            )

                            if status == 429:
                                
                                ui.line()
                                ui.line("[!]: HTTP 429 Too Many Requests")
                                ui.line(
                                    f"[i]: Progress: "
                                    f"{completed}/{len(download_targets)} "
                                    f"| Batch page: {page_number}"
                                )
                                ui.line(
                                    f"[i]: {target['title']} "
                                    f"(id: {target['id']}) "
                                    f"p{target['page']}"
                                )
                                test_ugoira(aapi, ugoira_data)
                                return

                            if status >= 400:
                                ui.line()
                                ui.line(f"[!]: HTTP error {status}")
                                ui.line(
                                    f"[i]: Progress: "
                                    f"{completed}/{len(download_targets)} "
                                    f"| Batch page: {page_number}"
                                )
                                ui.line(
                                    f"[i]: {target['title']} "
                                    f"(id: {target['id']}) "
                                    f"p{target['page']}"
                                )
                                ui.line(f"[i]: {body}")
                                test_ugoira(aapi, ugoira_data)
                                return

                            if status == -1:
                                ui.line()
                                ui.line("[!]: Request exception")
                                ui.line(
                                    f"[i]: Progress: "
                                    f"{completed}/{len(download_targets)} "
                                    f"| Batch page: {page_number}"
                                )
                                ui.line(
                                    f"[i]: {target['title']} "
                                    f"(id: {target['id']}) "
                                    f"p{target['page']}"
                                )
                                ui.line(f"[i]: {body}")

                                start = time.monotonic()

                                for delay in RECOVERY_DELAYS:

                                    ui.line()
                                    ui.line(
                                        f"[i]: Waiting {delay} seconds "
                                        f"before recovery probe..."
                                    )

                                    time.sleep(delay)

                                    status2, body2 = probe_recovery(
                                        aapi,
                                        target["link"],
                                    )

                                    elapsed = time.monotonic() - start

                                    ui.line(
                                        f"[i]: Recovery probe after "
                                        f"{elapsed:.1f} s "
                                        f"-> HTTP {status2}"
                                    )

                                    if status2 == 200:
                                        ui.line(
                                            f"[+]: Download recovered "
                                            f"after {elapsed:.1f} s."
                                        )
                                        break

                                    if status2 == -1:
                                        ui.line(f"[i]: {body2}")

                                # test_ugoira(aapi, ugoira_data)
                                break
            
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