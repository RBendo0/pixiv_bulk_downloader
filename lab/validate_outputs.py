#!/usr/bin/env python3
"""
Valida gli output prodotti dalla CLI e dalla libreria in tutte le cartelle opera.

Struttura attesa:

    test/
    ├── 1/
    │   ├── outcli.gif
    │   ├── outcli.webm
    │   ├── outcli.mp4
    │   ├── output.gif
    │   ├── output.webm
    │   └── output.mp4
    ├── 2/
    └── ...

Confronti eseguiti:
- risoluzione
- formato pixel
- profondità colore dichiarata
- numero di frame
- durata totale
- dimensione del file
- frame rate medio e nominale
- bitrate video
- durata di ogni singolo frame GIF

Requisito:
- ffprobe deve essere disponibile nel PATH, oppure indicato con --ffprobe.

Uso:

    python validate_outputs.py

oppure:

    python validate_outputs.py "C:\\Users\\pc\\pbd\\test"
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(r"C:\Users\pc\pbd\test")
FORMATS = ("gif", "webm", "mp4")
CLI_PREFIX = "outcli"
LIBRARY_PREFIX = "output"


class ValidationError(RuntimeError):
    """Errore previsto durante la validazione."""


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    width: int | None
    height: int | None
    pixel_format: str | None
    color_range: str | None
    color_space: str | None
    color_transfer: str | None
    color_primaries: str | None
    bits_per_raw_sample: int | None
    frame_count: int | None
    duration_seconds: Decimal | None
    size_bytes: int
    avg_frame_rate: str | None
    nominal_frame_rate: str | None
    bitrate: int | None


SUMMARY_FIELDS = [
    "opera",
    "formato",
    "cli_file",
    "library_file",
    "width_cli",
    "width_library",
    "width_diff",
    "height_cli",
    "height_library",
    "height_diff",
    "pixel_format_cli",
    "pixel_format_library",
    "pixel_format_equal",
    "color_range_cli",
    "color_range_library",
    "color_range_equal",
    "color_space_cli",
    "color_space_library",
    "color_space_equal",
    "color_transfer_cli",
    "color_transfer_library",
    "color_transfer_equal",
    "color_primaries_cli",
    "color_primaries_library",
    "color_primaries_equal",
    "bits_per_raw_sample_cli",
    "bits_per_raw_sample_library",
    "depth_equal",
    "frame_count_cli",
    "frame_count_library",
    "frame_count_diff",
    "duration_seconds_cli",
    "duration_seconds_library",
    "duration_seconds_diff",
    "size_bytes_cli",
    "size_bytes_library",
    "size_bytes_diff",
    "avg_frame_rate_cli",
    "avg_frame_rate_library",
    "avg_frame_rate_equal",
    "nominal_frame_rate_cli",
    "nominal_frame_rate_library",
    "nominal_frame_rate_equal",
    "bitrate_cli",
    "bitrate_library",
    "bitrate_diff",
    "status",
    "error",
]


FRAME_FIELDS = [
    "opera",
    "frame",
    "duration_cli_ms",
    "duration_library_ms",
    "duration_diff_ms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta automaticamente outcli.* e output.* "
            "in tutte le cartelle numerate."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=DEFAULT_ROOT,
        help=(
            "Cartella principale del dataset. "
            f"Predefinita: {DEFAULT_ROOT}"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        help=(
            "CSV riepilogativo. "
            "Predefinito: <root>/validation_report.csv"
        ),
    )
    parser.add_argument(
        "--frame-report",
        type=Path,
        help=(
            "CSV delle durate dei frame GIF. "
            "Predefinito: <root>/gif_frame_durations.csv"
        ),
    )
    parser.add_argument(
        "--ffprobe",
        default="ffprobe",
        help="Percorso o nome dell'eseguibile ffprobe.",
    )
    return parser.parse_args()


def resolve_ffprobe(value: str) -> str:
    explicit = Path(value).expanduser()

    if explicit.is_absolute() or explicit.parent != Path("."):
        if not explicit.is_file():
            raise ValidationError(f"ffprobe non trovato: {explicit}")
        return str(explicit.resolve())

    resolved = shutil.which(value)
    if resolved is None:
        raise ValidationError(
            "ffprobe non trovato nel PATH. "
            "Indicalo esplicitamente con --ffprobe."
        )

    return resolved


def run_ffprobe(
    ffprobe: str,
    arguments: list[str],
    path: Path,
) -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        *arguments,
        "-of",
        "json",
        str(path),
    ]

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "errore ffprobe non specificato"
        raise ValidationError(
            f"ffprobe non è riuscito ad analizzare '{path}': {message}"
        ) from error
    except OSError as error:
        raise ValidationError(
            f"Impossibile avviare ffprobe: {error}"
        ) from error

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValidationError(
            f"ffprobe ha restituito JSON non valido per '{path}'."
        ) from error


def optional_int(value: Any) -> int | None:
    if value in (None, "", "N/A"):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def optional_decimal(value: Any) -> Decimal | None:
    if value in (None, "", "N/A"):
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def normalize_rate(value: Any) -> str | None:
    if value in (None, "", "N/A", "0/0"):
        return None

    text = str(value)

    try:
        rate = Fraction(text)
    except (ValueError, ZeroDivisionError):
        return text

    if rate.denominator == 1:
        return str(rate.numerator)

    return f"{float(rate):.6f}".rstrip("0").rstrip(".")


def probe_media(ffprobe: str, path: Path) -> MediaInfo:
    data = run_ffprobe(
        ffprobe,
        [
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            (
                "stream=width,height,pix_fmt,color_range,color_space,"
                "color_transfer,color_primaries,bits_per_raw_sample,"
                "nb_frames,nb_read_frames,duration,avg_frame_rate,"
                "r_frame_rate,bit_rate:"
                "format=duration,size,bit_rate"
            ),
            "-show_streams",
            "-show_format",
        ],
        path,
    )

    streams = data.get("streams") or []
    if not streams:
        raise ValidationError(
            f"Nessun flusso video trovato in '{path}'."
        )

    stream = streams[0]
    container = data.get("format") or {}

    frame_count = optional_int(stream.get("nb_read_frames"))
    if frame_count is None:
        frame_count = optional_int(stream.get("nb_frames"))

    duration = optional_decimal(stream.get("duration"))
    if duration is None:
        duration = optional_decimal(container.get("duration"))

    bitrate = optional_int(stream.get("bit_rate"))
    if bitrate is None:
        bitrate = optional_int(container.get("bit_rate"))

    return MediaInfo(
        path=path,
        width=optional_int(stream.get("width")),
        height=optional_int(stream.get("height")),
        pixel_format=stream.get("pix_fmt") or None,
        color_range=stream.get("color_range") or None,
        color_space=stream.get("color_space") or None,
        color_transfer=stream.get("color_transfer") or None,
        color_primaries=stream.get("color_primaries") or None,
        bits_per_raw_sample=optional_int(
            stream.get("bits_per_raw_sample")
        ),
        frame_count=frame_count,
        duration_seconds=duration,
        size_bytes=path.stat().st_size,
        avg_frame_rate=normalize_rate(
            stream.get("avg_frame_rate")
        ),
        nominal_frame_rate=normalize_rate(
            stream.get("r_frame_rate")
        ),
        bitrate=bitrate,
    )


def probe_gif_frame_durations(
    ffprobe: str,
    path: Path,
) -> list[Decimal | None]:
    data = run_ffprobe(
        ffprobe,
        [
            "-select_streams",
            "v:0",
            "-show_frames",
            "-show_entries",
            (
                "frame=best_effort_timestamp_time,"
                "pkt_duration_time,duration_time"
            ),
        ],
        path,
    )

    frames = data.get("frames") or []
    durations: list[Decimal | None] = []

    for index, frame in enumerate(frames):
        duration = optional_decimal(frame.get("pkt_duration_time"))

        if duration is None:
            duration = optional_decimal(frame.get("duration_time"))

        if duration is None and index + 1 < len(frames):
            current_pts = optional_decimal(
                frame.get("best_effort_timestamp_time")
            )
            next_pts = optional_decimal(
                frames[index + 1].get(
                    "best_effort_timestamp_time"
                )
            )

            if current_pts is not None and next_pts is not None:
                duration = next_pts - current_pts

        durations.append(duration)

    return durations


def seconds_text(value: Decimal | None) -> str:
    if value is None:
        return ""

    return format(
        value.quantize(Decimal("0.000001")),
        "f",
    )


def milliseconds_text(value: Decimal | None) -> str:
    if value is None:
        return ""

    return format(
        (value * Decimal(1000)).quantize(Decimal("0.001")),
        "f",
    )


def number_diff(
    cli_value: int | None,
    library_value: int | None,
) -> int | str:
    if cli_value is None or library_value is None:
        return ""

    return library_value - cli_value


def decimal_diff(
    cli_value: Decimal | None,
    library_value: Decimal | None,
) -> str:
    if cli_value is None or library_value is None:
        return ""

    return seconds_text(library_value - cli_value)


def value_or_empty(value: Any) -> Any:
    return "" if value is None else value


def build_summary_row(
    artwork: str,
    media_format: str,
    cli: MediaInfo,
    library: MediaInfo,
) -> dict[str, Any]:
    return {
        "opera": artwork,
        "formato": media_format,
        "cli_file": str(cli.path),
        "library_file": str(library.path),
        "width_cli": value_or_empty(cli.width),
        "width_library": value_or_empty(library.width),
        "width_diff": number_diff(cli.width, library.width),
        "height_cli": value_or_empty(cli.height),
        "height_library": value_or_empty(library.height),
        "height_diff": number_diff(cli.height, library.height),
        "pixel_format_cli": value_or_empty(cli.pixel_format),
        "pixel_format_library": value_or_empty(
            library.pixel_format
        ),
        "pixel_format_equal": (
            cli.pixel_format == library.pixel_format
        ),
        "color_range_cli": value_or_empty(cli.color_range),
        "color_range_library": value_or_empty(
            library.color_range
        ),
        "color_range_equal": (
            cli.color_range == library.color_range
        ),
        "color_space_cli": value_or_empty(cli.color_space),
        "color_space_library": value_or_empty(
            library.color_space
        ),
        "color_space_equal": (
            cli.color_space == library.color_space
        ),
        "color_transfer_cli": value_or_empty(
            cli.color_transfer
        ),
        "color_transfer_library": value_or_empty(
            library.color_transfer
        ),
        "color_transfer_equal": (
            cli.color_transfer == library.color_transfer
        ),
        "color_primaries_cli": value_or_empty(
            cli.color_primaries
        ),
        "color_primaries_library": value_or_empty(
            library.color_primaries
        ),
        "color_primaries_equal": (
            cli.color_primaries == library.color_primaries
        ),
        "bits_per_raw_sample_cli": value_or_empty(
            cli.bits_per_raw_sample
        ),
        "bits_per_raw_sample_library": value_or_empty(
            library.bits_per_raw_sample
        ),
        "depth_equal": (
            cli.bits_per_raw_sample
            == library.bits_per_raw_sample
        ),
        "frame_count_cli": value_or_empty(cli.frame_count),
        "frame_count_library": value_or_empty(
            library.frame_count
        ),
        "frame_count_diff": number_diff(
            cli.frame_count,
            library.frame_count,
        ),
        "duration_seconds_cli": seconds_text(
            cli.duration_seconds
        ),
        "duration_seconds_library": seconds_text(
            library.duration_seconds
        ),
        "duration_seconds_diff": decimal_diff(
            cli.duration_seconds,
            library.duration_seconds,
        ),
        "size_bytes_cli": cli.size_bytes,
        "size_bytes_library": library.size_bytes,
        "size_bytes_diff": (
            library.size_bytes - cli.size_bytes
        ),
        "avg_frame_rate_cli": value_or_empty(
            cli.avg_frame_rate
        ),
        "avg_frame_rate_library": value_or_empty(
            library.avg_frame_rate
        ),
        "avg_frame_rate_equal": (
            cli.avg_frame_rate == library.avg_frame_rate
        ),
        "nominal_frame_rate_cli": value_or_empty(
            cli.nominal_frame_rate
        ),
        "nominal_frame_rate_library": value_or_empty(
            library.nominal_frame_rate
        ),
        "nominal_frame_rate_equal": (
            cli.nominal_frame_rate
            == library.nominal_frame_rate
        ),
        "bitrate_cli": value_or_empty(cli.bitrate),
        "bitrate_library": value_or_empty(library.bitrate),
        "bitrate_diff": number_diff(
            cli.bitrate,
            library.bitrate,
        ),
        "status": "ok",
        "error": "",
    }


def build_error_row(
    artwork: str,
    media_format: str,
    cli_path: Path,
    library_path: Path,
    error: str,
) -> dict[str, Any]:
    row = {field: "" for field in SUMMARY_FIELDS}
    row.update(
        {
            "opera": artwork,
            "formato": media_format,
            "cli_file": str(cli_path),
            "library_file": str(library_path),
            "status": "error",
            "error": error,
        }
    )
    return row


def build_frame_rows(
    artwork: str,
    cli_durations: list[Decimal | None],
    library_durations: list[Decimal | None],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    frame_count = max(
        len(cli_durations),
        len(library_durations),
    )

    for index in range(frame_count):
        cli_duration = (
            cli_durations[index]
            if index < len(cli_durations)
            else None
        )
        library_duration = (
            library_durations[index]
            if index < len(library_durations)
            else None
        )

        difference = ""
        if (
            cli_duration is not None
            and library_duration is not None
        ):
            difference = milliseconds_text(
                library_duration - cli_duration
            )

        rows.append(
            {
                "opera": artwork,
                "frame": index,
                "duration_cli_ms": milliseconds_text(
                    cli_duration
                ),
                "duration_library_ms": milliseconds_text(
                    library_duration
                ),
                "duration_diff_ms": difference,
            }
        )

    return rows


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def find_artwork_dirs(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir() and path.name.isdigit()
        ),
        key=lambda path: int(path.name),
    )


def main() -> int:
    args = parse_args()

    try:
        root = args.root.expanduser().resolve()

        if not root.is_dir():
            raise ValidationError(
                f"Cartella dataset non trovata: {root}"
            )

        ffprobe = resolve_ffprobe(args.ffprobe)
        artwork_dirs = find_artwork_dirs(root)

        if not artwork_dirs:
            raise ValidationError(
                f"Nessuna cartella numerata trovata in {root}"
            )

        report_path = (
            args.report.expanduser().resolve()
            if args.report
            else root / "validation_report.csv"
        )
        frame_report_path = (
            args.frame_report.expanduser().resolve()
            if args.frame_report
            else root / "gif_frame_durations.csv"
        )

        summary_rows: list[dict[str, Any]] = []
        frame_rows: list[dict[str, Any]] = []

        successful_pairs = 0
        failed_pairs = 0

        for artwork_dir in artwork_dirs:
            artwork = artwork_dir.name
            print(f"\n[Opera {artwork}]")

            for media_format in FORMATS:
                cli_path = artwork_dir / (
                    f"{CLI_PREFIX}.{media_format}"
                )
                library_path = artwork_dir / (
                    f"{LIBRARY_PREFIX}.{media_format}"
                )

                try:
                    if not cli_path.is_file():
                        raise ValidationError(
                            f"File CLI mancante: {cli_path.name}"
                        )

                    if not library_path.is_file():
                        raise ValidationError(
                            "File libreria mancante: "
                            f"{library_path.name}"
                        )

                    cli_info = probe_media(ffprobe, cli_path)
                    library_info = probe_media(
                        ffprobe,
                        library_path,
                    )

                    summary_rows.append(
                        build_summary_row(
                            artwork,
                            media_format,
                            cli_info,
                            library_info,
                        )
                    )

                    if media_format == "gif":
                        cli_durations = (
                            probe_gif_frame_durations(
                                ffprobe,
                                cli_path,
                            )
                        )
                        library_durations = (
                            probe_gif_frame_durations(
                                ffprobe,
                                library_path,
                            )
                        )
                        frame_rows.extend(
                            build_frame_rows(
                                artwork,
                                cli_durations,
                                library_durations,
                            )
                        )

                    successful_pairs += 1
                    print(f"  {media_format}: OK")

                except ValidationError as error:
                    failed_pairs += 1
                    summary_rows.append(
                        build_error_row(
                            artwork,
                            media_format,
                            cli_path,
                            library_path,
                            str(error),
                        )
                    )
                    print(f"  {media_format}: ERRORE - {error}")

        write_csv(
            report_path,
            SUMMARY_FIELDS,
            summary_rows,
        )
        write_csv(
            frame_report_path,
            FRAME_FIELDS,
            frame_rows,
        )

        print("\n========================================")
        print(f"Coppie confrontate: {successful_pairs}")
        print(f"Coppie fallite:     {failed_pairs}")
        print(f"Report:             {report_path}")
        print(f"Durate GIF:         {frame_report_path}")
        print("========================================")

        return 0 if failed_pairs == 0 else 1

    except ValidationError as error:
        print(f"Errore: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
