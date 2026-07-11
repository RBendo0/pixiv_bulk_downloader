from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvFile:

    def __init__(
        self,
        path: Path | str,
        purge: bool = False,
    ) -> None:

        self.path = Path(path)

        if purge:
            self._purge_blank_lines()

    def read_lines(self) -> list[str]:

        if not self.path.exists():
            return []

        return self.path.read_text(
            encoding="utf-8",
        ).splitlines()

    def append_row(
        self,
        *columns: Any,
    ) -> None:

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="",
        ) as file:

            csv.writer(file).writerow(columns)

    def truncate_last(
        self,
        count: int = 1,
    ) -> None:

        if count < 0:
            raise ValueError(
                "count cannot be negative"
            )

        for _ in range(count):

            if not self._truncate_last():
                break

    def _purge_blank_lines(self) -> None:

        lines = [
            line
            for line in self.read_lines()
            if line.strip()
        ]

        with self.path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:

            csv.writer(file).writerows(
                [line]
                for line in lines
            )

    def _truncate_last(self) -> bool:

        if not self.path.exists():
            return False

        with self.path.open("rb+") as file:

            file.seek(0, 2)
            size = file.tell()

            if size == 0:
                return False

            position = size - 1

            # Salta i terminatori dell'ultima riga.
            while position >= 0:

                file.seek(position)

                if file.read(1) not in (
                    b"\r",
                    b"\n",
                ):
                    break

                position -= 1

            # Cerca il terminatore della riga precedente.
            while position >= 0:

                file.seek(position)

                if file.read(1) == b"\n":
                    file.truncate(position + 1)
                    return True

                position -= 1

            # Il file conteneva una sola riga.
            file.truncate(0)

            return True
