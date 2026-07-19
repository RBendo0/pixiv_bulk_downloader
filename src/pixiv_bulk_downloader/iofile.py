from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any


class BaseFile:

    def __init__(
        self,
        path: Path | str,
    ) -> None:

        self._path = Path(path)

    def backup(self) -> None:

        if not self._path.exists():
            return

        backup_path = self._path.with_suffix(
            self._path.suffix + ".bak"
        )

        shutil.copy2(
            self._path,
            backup_path,
        )

    def restore(self) -> None:

        backup_path = self._path.with_suffix(
            self._path.suffix + ".bak"
        )

        if not backup_path.exists():
            return

        shutil.copy2(
            backup_path,
            self._path,
        )        


class JsonFile(BaseFile):

    def load(self) -> Any:

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def save(
        self,
        data: Any,
    ) -> None:

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
                default=str,
            )


class CsvFile(BaseFile):

    def __init__(
        self,
        path: Path | str,
        purge: bool = False,
    ) -> None:

        super().__init__(path)

        if purge:
            self._purge_blank_lines()

    def read_lines(self) -> list[str]:

        if not self._path.exists():
            return []

        return self._path.read_text(
            encoding="utf-8",
        ).splitlines()

    def append_row(
        self,
        *columns: Any,
    ) -> None:

        with self._path.open(
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

        with self._path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as file:

            csv.writer(file).writerows(
                [line]
                for line in lines
            )

    def _truncate_last(self) -> bool:

        if not self._path.exists():
            return False

        with self._path.open("rb+") as file:

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
