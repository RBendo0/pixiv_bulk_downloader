from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import tempfile
import time
import zipfile
from dataclasses import dataclass
from functools import reduce
from pathlib import Path
from typing import BinaryIO, Iterable


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Banco prova ugoira: genera GIF, WebM e MP4 sia da una cartella "
            "temporanea sia inviando a FFmpeg un'immagine alla volta."
        )
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Cartella contenente coppie <id>.json e <id>.zip.",
    )
    parser.add_argument(
        "--ffmpeg",
        type=Path,
        default=Path("ffmpeg"),
        help="Percorso di ffmpeg.exe oppure nome del comando nel PATH.",
    )
    return parser.parse_args()


def load_frames(metadata_path: Path) -> list[Frame]:
    with metadata_path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)

    raw_frames = data["ugoira"]["ugoira_metadata"]["frames"]
    frames = [
        Frame(file=item["file"], delay_ms=int(item["delay"]))
        for item in raw_frames
    ]

    if not frames:
        raise ValueError("Il metadata non contiene frame.")

    for frame in frames:
        if frame.delay_ms <= 0:
            raise ValueError(
                f"Delay non valido per {frame.file}: {frame.delay_ms}"
            )
        if Path(frame.file).name != frame.file:
            raise ValueError(
                f"Nome frame non sicuro o contenente directory: {frame.file}"
            )

    return frames


def ffconcat_quote(path: Path) -> str:
    text = path.resolve().as_posix()
    return "'" + text.replace("'", r"'\''") + "'"


def extract_frames(
    zip_path: Path,
    frames: Iterable[Frame],
    destination: Path,
) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

        for frame in frames:
            if frame.file not in names:
                raise FileNotFoundError(
                    f"{frame.file} non è presente in {zip_path.name}"
                )

            target = destination / frame.file
            with archive.open(frame.file) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


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


def run_ffmpeg(command: list[str], *, stdin_writer=None) -> float:
    started = time.perf_counter()

    with tempfile.TemporaryFile(mode="w+b") as error_log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if stdin_writer is not None else None,
            stdout=subprocess.DEVNULL,
            stderr=error_log,
        )

        try:
            if stdin_writer is not None:
                assert process.stdin is not None
                stdin_writer(process.stdin)
                process.stdin.close()

            return_code = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise

        elapsed = time.perf_counter() - started

        if return_code != 0:
            error_log.seek(0)
            error_text = error_log.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"FFmpeg è terminato con codice {return_code}.\n{error_text}"
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


def common_delay_tick_ms(frames: list[Frame]) -> int:
    return reduce(math.gcd, (frame.delay_ms for frame in frames))


def encode_from_stream(
    ffmpeg: Path,
    zip_path: Path,
    frames: list[Frame],
    format_name: str,
    output_path: Path,
) -> float:
    """
    Invia a FFmpeg un solo frame letto dallo ZIP alla volta.

    Per conservare delay variabili usa il MCD dei delay come unità temporale:
    un frame da 60 ms, con tick da 20 ms, viene inviato tre volte a 50 fps.
    """
    tick_ms = common_delay_tick_ms(frames)
    frame_rate = f"1000/{tick_ms}"

    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "image2pipe",
        "-framerate",
        frame_rate,
        "-i",
        "pipe:0",
        *output_arguments(format_name, output_path),
    ]

    def write_frames(stdin: BinaryIO) -> None:
        with zipfile.ZipFile(zip_path) as archive:
            names = set(archive.namelist())

            for frame in frames:
                if frame.file not in names:
                    raise FileNotFoundError(
                        f"{frame.file} non è presente in {zip_path.name}"
                    )

                image = archive.read(frame.file)
                repetitions = frame.delay_ms // tick_ms

                for _ in range(repetitions):
                    stdin.write(image)

    return run_ffmpeg(command, stdin_writer=write_frames)


def make_result(
    *,
    artwork_id: str,
    method: str,
    format_name: str,
    frames: list[Frame],
    extraction_s: float,
    encoding_s: float,
    total_s: float,
    output_path: Path,
    status: str,
    error: str = "",
) -> TestResult:
    return TestResult(
        artwork_id=artwork_id,
        method=method,
        format=format_name,
        frame_count=len(frames),
        theoretical_duration_s=sum(f.delay_ms for f in frames) / 1000,
        extraction_s=extraction_s,
        encoding_s=encoding_s,
        total_s=total_s,
        output_size_bytes=(
            output_path.stat().st_size if output_path.exists() else 0
        ),
        output_file=str(output_path),
        status=status,
        error=error,
    )


def process_pair(
    ffmpeg: Path,
    metadata_path: Path,
    zip_path: Path,
    output_dir: Path,
) -> list[TestResult]:
    artwork_id = metadata_path.stem
    frames = load_frames(metadata_path)
    results: list[TestResult] = []

    print(
        f"\n{artwork_id}: {len(frames)} frame, "
        f"{sum(f.delay_ms for f in frames) / 1000:.3f} s teorici"
    )

    with tempfile.TemporaryDirectory(prefix=f"ugoira_{artwork_id}_") as temp_name:
        temp_dir = Path(temp_name)
        extraction_started = time.perf_counter()
        extract_frames(zip_path, frames, temp_dir)
        extraction_s = time.perf_counter() - extraction_started

        manifest_path = temp_dir / "frames.ffconcat"
        create_ffconcat_manifest(frames, temp_dir, manifest_path)

        for format_name in ("gif", "webm", "mp4"):
            output_path = output_dir / f"{artwork_id}_folder.{format_name}"
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

            total_s = time.perf_counter() - test_started + extraction_s
            results.append(
                make_result(
                    artwork_id=artwork_id,
                    method="folder",
                    format_name=format_name,
                    frames=frames,
                    extraction_s=extraction_s,
                    encoding_s=encoding_s,
                    total_s=total_s,
                    output_path=output_path,
                    status=status,
                    error=error,
                )
            )
            print(
                f"  folder/{format_name}: {status}, "
                f"estrazione {extraction_s:.3f}s, codifica {encoding_s:.3f}s"
            )

    for format_name in ("gif", "webm", "mp4"):
        output_path = output_dir / f"{artwork_id}_stream.{format_name}"
        test_started = time.perf_counter()

        try:
            encoding_s = encode_from_stream(
                ffmpeg,
                zip_path,
                frames,
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
                method="stream",
                format_name=format_name,
                frames=frames,
                extraction_s=0.0,
                encoding_s=encoding_s,
                total_s=total_s,
                output_path=output_path,
                status=status,
                error=error,
            )
        )
        print(f"  stream/{format_name}: {status}, totale {total_s:.3f}s")

    return results


def write_csv(results: list[TestResult], csv_path: Path) -> None:
    fields = list(TestResult.__dataclass_fields__)

    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {field: getattr(result, field) for field in fields}
            )


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_files = sorted(
        input_dir.glob("*.json"),
        key=lambda path: int(path.stem),
    )
    if not metadata_files:
        raise FileNotFoundError(f"Nessun file JSON trovato in {input_dir}")

    all_results: list[TestResult] = []

    for metadata_path in metadata_files:
        zip_path = input_dir / f"{metadata_path.stem}.zip"

        if not zip_path.exists():
            print(f"\n[SKIP] Manca {zip_path.name} per {metadata_path.name}")
            continue

        try:
            all_results.extend(
                process_pair(
                    args.ffmpeg,
                    metadata_path,
                    zip_path,
                    output_dir,
                )
            )
        except Exception as exc:
            print(f"\n[ERRORE] {metadata_path.name}: {exc}")

    csv_path = output_dir / "results.csv"
    write_csv(all_results, csv_path)

    print(f"\nRisultati scritti in: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
