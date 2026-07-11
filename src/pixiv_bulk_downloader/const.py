from pathlib import Path
from typing import Final

PBD_ROOT: Final[Path] = Path.home() / "pbd"

BOOKMARKS_DIR: Final[Path] = PBD_ROOT / "bookmarks"

LISTS_DIR: Final[Path] = PBD_ROOT / "lists"

NOT_FOUND_CSV_PREFIX: Final[str] = "not_found_"

DISCARDED_CSV_PREFIX: Final[str] = "discarded_"

STATE_DIR: Final[Path] = PBD_ROOT / "state"

DOWNLOADED_IDS_FILE: Final[Path] = STATE_DIR / "downloaded_ids.txt"

FETCH_CHECKPOINT_FILE: Final[Path] = Path("fetch.json")

WORK_METADATA_FILE: Final[Path] = Path("metadata.json")

UGOIRA_METADATA_FILE: Final[Path] = Path("ugoira.json")

UGOIRA_ZIP_FILE: Final[Path] = Path("ugoira.zip")
