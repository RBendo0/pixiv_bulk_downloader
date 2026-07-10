from pathlib import Path
from typing import Final

PBD_ROOT: Final[Path] = Path.home() / "pbd"

BOOKMARKS_DIR: Final[Path] = PBD_ROOT / "bookmarks"

LISTS_DIR: Final[Path] = PBD_ROOT / "lists"

STATE_DIR: Final[Path] = PBD_ROOT / "state"

BOOKMARKS_PENDING: Final[Path] = LISTS_DIR / "pending_urls.txt"

BOOKMARKS_NOT_FOUND: Final[Path] = LISTS_DIR / "not_found_urls.txt"

DOWNLOADED_IDS_FILE: Final[Path] = STATE_DIR / "downloaded_ids.txt"

FETCH_CHECKPOINT_FILE: Final[Path] = Path("fetch.json")

WORK_METADATA_FILE: Final[Path] = Path("metadata.json")

UGOIRA_METADATA_FILE: Final[Path] = Path("ugoira.json")

UGOIRA_ZIP_FILE: Final[Path] = Path("ugoira.zip")
