from __future__ import annotations

import csv
import json
from pathlib import Path

TEST_ROOT = Path(r"C:\Users\pc\pbd\test")
JSON_NAME = "metadata.json"
CSV_NAME = "metadata.csv"


def convert_folder(folder: Path) -> None:
    json_path = folder / JSON_NAME
    csv_path = folder / CSV_NAME

    if not json_path.is_file():
        print(f"[SALTO] {folder.name}: {JSON_NAME} non trovato")
        return

    with json_path.open("r", encoding="utf-8-sig") as source:
        data = json.load(source)

    try:
        frames = data["ugoira"]["ugoira_metadata"]["frames"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            "struttura JSON non valida: atteso "
            "'ugoira -> ugoira_metadata -> frames'"
        ) from error

    if not isinstance(frames, list):
        raise ValueError("'frames' non è una lista")

    with csv_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination, lineterminator="\n")

        for position, frame in enumerate(frames, start=1):
            if not isinstance(frame, dict):
                raise ValueError(f"frame {position}: valore non valido")

            filename = frame.get("file")
            delay = frame.get("delay")

            if not isinstance(filename, str) or not filename:
                raise ValueError(f"frame {position}: campo 'file' non valido")

            if not isinstance(delay, int) or delay < 0:
                raise ValueError(f"frame {position}: campo 'delay' non valido")

            image_path = folder / filename
            if not image_path.is_file():
                raise FileNotFoundError(
                    f"frame {position}: immagine non trovata: {filename}"
                )

            writer.writerow((filename, delay))

    print(f"[OK] {folder.name}: {len(frames)} frame -> {CSV_NAME}")


def folder_sort_key(folder: Path) -> tuple[int, int | str]:
    try:
        return (0, int(folder.name))
    except ValueError:
        return (1, folder.name.lower())


def main() -> None:
    if not TEST_ROOT.is_dir():
        raise SystemExit(f"Cartella di test inesistente: {TEST_ROOT}")

    folders = sorted(
        (path for path in TEST_ROOT.iterdir() if path.is_dir()),
        key=folder_sort_key,
    )

    if not folders:
        raise SystemExit(f"Nessuna sottocartella trovata in: {TEST_ROOT}")

    converted = 0
    failed = 0

    for folder in folders:
        try:
            convert_folder(folder)
            if (folder / CSV_NAME).is_file():
                converted += 1
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"[ERRORE] {folder.name}: {error}")
            failed += 1

    print()
    print(f"Cartelle convertite: {converted}")
    print(f"Errori: {failed}")


if __name__ == "__main__":
    main()
