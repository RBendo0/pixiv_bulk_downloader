from pathlib import Path
from typing import Final

DEFAULT_ROOT: Final[Path] = Path.home() / "pbd"

CONF_DIR: Final[Path] = Path("conf")
BOOKMARKS_DIR: Final[Path] = Path("bookmarks")
LISTS_DIR: Final[Path] = Path("lists")

NOT_FOUND_CSV_PREFIX: Final[str] = "not_found_"
DISCARDED_CSV_PREFIX: Final[str] = "discarded_"

CONFIG_FILE = Path("config.json")

FETCH_CHECKPOINT_FILE: Final[Path] = Path("fetch.json")
WORK_METADATA_FILE: Final[Path] = Path("metadata.json")
UGOIRA_METADATA_FILE: Final[Path] = Path("ugoira.json")
UGOIRA_ZIP_FILE: Final[Path] = Path("ugoira.zip")





