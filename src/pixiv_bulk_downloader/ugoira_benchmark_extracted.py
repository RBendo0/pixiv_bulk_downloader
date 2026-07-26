from __future__ import annotations

import csv
import subprocess
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

INPUT_DIR = Path(r"C:\Users\pc\pbd\test")
FFMPEG = Path("ffmpeg")

FILE_COLUMNS = ("file", "filename", "image", "frame", "path")
DELAY_COLUMNS = ("delay", "delay_ms", "duration", "duration_ms")


@dataclass(frozen=True)
class Frame:
    file: str
    delay_ms: int


@dataclass(frozen=True)
class TestResult:
    artwork_id: str
    method: str
    format: str
    frame_count: int
    theoretical_duration_s: float
    extraction_s: float
    encoding_s: float
    total_s: float
    output_size_bytes: int
    output_file: str
    status: str
    error: str = ""


def find_column(
    fieldnames: Sequence[str],
    candidates: tuple[str, ...],
) -> str:
    normalized = {
        fieldname.strip().lower(): fieldname
        for fieldname in fieldnames
    }

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    raise ValueError(
        "Colonna CSV non trovata. "
        f"Attese una tra {candidates}; presenti: {list(fieldnames)}"
    )


def load_frames(metadata_path: Path) -> list[Frame]:
    frames = []

    with metadata_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)

        for row in reader:
            if len(row) != 2:
                raise ValueError(f"Riga non valida: {row}")

            frames.append(
                Frame(
                    file=row[0],
                    delay_ms=int(row[1]),
                )
            )

    return frames

def ffconcat_quote(path: Path) -> str:
    text = path.resolve().as_posix()
    return "'" + text.replace("'", r"'\''") + "'"


def create_ffconcat_manifest(
    frames: list[Frame],
    frame_dir: Path,
    manifest_path: Path,
) -> None:
    lines = ["ffconcat version 1.0"]

    for frame in frames:
        lines.append(f"file {ffconcat_quote(frame_dir / frame.file)}")
        lines.append(f"duration {frame.delay_ms / 1000:.9f}")

    lines.append(f"file {ffconcat_quote(frame_dir / frames[-1].file)}")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def output_arguments(format_name: str, output_path: Path) -> list[str]:
    if format_name == "gif":
        return [
            "-filter_complex",
            "[0:v]split[a][b];[a]palettegen[p];[b][p]paletteuse",
            "-loop",
            "0",
            str(output_path),
        ]

    even_dimensions = "scale=trunc(iw/2)*2:trunc(ih/2)*2"

    if format_name == "webm":
        return [
            "-vf",
            even_dimensions,
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "30",
            "-b:v",
            "0",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]

    if format_name == "mp4":
        return [
            "-vf",
            even_dimensions,
            "-c:v",
            "libx264",
            "-crf",
            "20",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

    raise ValueError(f"Formato non supportato: {format_name}")


def run_ffmpeg(command: list[str]) -> float:
    started = time.perf_counter()

    with tempfile.TemporaryFile(mode="w+b") as error_log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=error_log,
        )

        try:
            return_code = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise

        elapsed = time.perf_counter() - started

        if return_code != 0:
            error_log.seek(0)
            error_text = error_log.read().decode(
                "utf-8",
                errors="replace",
            )
            raise RuntimeError(
                f"FFmpeg è terminato con codice {return_code}.\n"
                f"{error_text}"
            )

    return elapsed


def encode_from_folder(
    ffmpeg: Path,
    manifest_path: Path,
    format_name: str,
    output_path: Path,
) -> float:
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(manifest_path),
        "-fps_mode",
        "vfr",
        *output_arguments(format_name, output_path),
    ]
    return run_ffmpeg(command)


def make_result(
    *,
    artwork_id: str,
    format_name: str,
    frames: list[Frame],
    encoding_s: float,
    total_s: float,
    output_path: Path,
    status: str,
    error: str = "",
) -> TestResult:
    return TestResult(
        artwork_id=artwork_id,
        method="folder",
        format=format_name,
        frame_count=len(frames),
        theoretical_duration_s=sum(
            frame.delay_ms for frame in frames
        ) / 1000,
        extraction_s=0.0,
        encoding_s=encoding_s,
        total_s=total_s,
        output_size_bytes=(
            output_path.stat().st_size if output_path.exists() else 0
        ),
        output_file=str(output_path),
        status=status,
        error=error,
    )


def process_artwork(
    ffmpeg: Path,
    artwork_dir: Path,
) -> list[TestResult]:
    artwork_id = artwork_dir.name
    metadata_path = artwork_dir / "metadata.csv"
    frames = load_frames(metadata_path)
    results: list[TestResult] = []

    print(
        f"\n{artwork_id}: {len(frames)} frame, "
        f"{sum(frame.delay_ms for frame in frames) / 1000:.3f} s teorici"
    )

    with tempfile.TemporaryDirectory(
        prefix=f"ugoira_{artwork_id}_"
    ) as temp_name:
        manifest_path = Path(temp_name) / "frames.ffconcat"
        create_ffconcat_manifest(
            frames,
            artwork_dir,
            manifest_path,
        )

        for format_name in ("gif", "webm", "mp4"):
            output_path = artwork_dir / f"outcli.{format_name}"
            test_started = time.perf_counter()

            try:
                encoding_s = encode_from_folder(
                    ffmpeg,
                    manifest_path,
                    format_name,
                    output_path,
                )
                status = "ok"
                error = ""
            except Exception as exc:
                encoding_s = 0.0
                status = "error"
                error = str(exc)

            total_s = time.perf_counter() - test_started
            results.append(
                make_result(
                    artwork_id=artwork_id,
                    format_name=format_name,
                    frames=frames,
                    encoding_s=encoding_s,
                    total_s=total_s,
                    output_path=output_path,
                    status=status,
                    error=error,
                )
            )

            print(
                f"  {format_name}: {status}, "
                f"codifica {encoding_s:.3f}s"
            )

    return results


def write_csv(
    results: list[TestResult],
    csv_path: Path,
) -> None:
    fields = list(TestResult.__dataclass_fields__)

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    field: getattr(result, field)
                    for field in fields
                }
            )


def main() -> int:
    input_dir = INPUT_DIR.resolve()

    if not input_dir.is_dir():
        raise FileNotFoundError(
            f"Cartella di test non trovata: {input_dir}"
        )

    artwork_dirs = sorted(
        (
            path
            for path in input_dir.iterdir()
            if path.is_dir() and path.name.isdigit()
        ),
        key=lambda path: int(path.name),
    )

    if not artwork_dirs:
        raise FileNotFoundError(
            f"Nessuna cartella numerata trovata in {input_dir}"
        )

    all_results: list[TestResult] = []

    for artwork_dir in artwork_dirs:
        metadata_path = artwork_dir / "metadata.csv"

        if not metadata_path.is_file():
            print(
                f"\n[SKIP] Manca metadata.csv in {artwork_dir}"
            )
            continue

        try:
            all_results.extend(
                process_artwork(
                    FFMPEG,
                    artwork_dir,
                )
            )
        except Exception as exc:
            print(f"\n[ERRORE] {artwork_dir.name}: {exc}")

    csv_path = input_dir / "results.csv"
    write_csv(all_results, csv_path)

    print(f"\nRisultati scritti in: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
