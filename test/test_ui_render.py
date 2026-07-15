from __future__ import annotations

import random
import string
import time
from concurrent.futures import ThreadPoolExecutor
from shutil import get_terminal_size

from .ui import ui

WORKERS = 4
UPDATES_PER_WORKER = 40

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 35

MIN_DELAY = 0.05
MAX_DELAY = 0.25


def random_text(
    reserved_width: int = 50,
) -> str:

    viewport_width = get_terminal_size().columns - 5

    max_length = max(
        1,
        viewport_width - reserved_width,
    )

    min_length = max(
        1,
        max_length - 10,
    )

    length = random.randint(
        viewport_width,
        viewport_width * 2,
    )
    
    return "".join(
        random.choices(
            string.ascii_letters
            + string.digits
            + " ",
            k=length,
        )
    )


def renderer_worker(
    worker_id: int,
) -> None:

    colors = (
        ui.COLOR_DEFAULT,
        ui.COLOR_SUCCESS,
        ui.COLOR_WARNING,
        ui.COLOR_ERROR,
    )

    for update in range(
        1,
        UPDATES_PER_WORKER + 1,
    ):

        color = random.choice(colors)

        ui.Renderer.write(
            f"Worker {worker_id} | "
            f"Update {update:02d}/{UPDATES_PER_WORKER} | "
            f"{color}"
            f"{random_text()}"
        )

        time.sleep(
            random.uniform(
                MIN_DELAY,
                MAX_DELAY,
            )
        )

    ui.Renderer.write(
        f"Worker {worker_id} | "
        f"{ui.COLOR_SUCCESS}"
        f"Completed"
    )


def main() -> None:

    try:

        with ThreadPoolExecutor(
            max_workers=WORKERS,
            thread_name_prefix="RENDER-TEST",
        ) as executor:

            futures = [
                executor.submit(
                    renderer_worker,
                    worker_id,
                )
                for worker_id in range(
                    1,
                    WORKERS + 1,
                )
            ]

            while not all(
                future.done()
                for future in futures
            ):

                completed = sum(
                    future.done()
                    for future in futures
                )

                ui.Renderer.write(
                    f"Renderer test | "
                    f"Completed workers: "
                    f"{completed}/{WORKERS}",
                    main=True,
                )

                if random.random() < 0.25:

                    ui.line(
                        f"[i]: Console message {random.randint(1, 999)}",
                    )

                time.sleep(0.1)

            for future in futures:
                future.result()

            ui.Renderer.write(
                f"{ui.COLOR_SUCCESS}"
                f"Renderer test completed",
                main=True,
            )

            time.sleep(2)

    finally:

        ui.Renderer.stop()

    ui.line(
        "[+]: Renderer test terminated.",
        ui.COLOR_SUCCESS,
    )


if __name__ == "__main__":
    main()