import sys
from pathlib import Path
from typing import Final

from .pbd_types import CodecSettings, PreferredMediaFormats

# ROOT DI DEFAULT: necessaria per archiviare le impostazioni dell'applicazione
# viene determinata dalla posizione dell'eseguibile compilato con PyInstaller
# se l'esecuzione è partita da lì, altrimenti usa il percorso assoluto
DEFAULT_ROOT: Final[Path] = (
    Path(sys.executable).resolve().parent.parent
    if getattr(sys, "frozen", False)
    else Path.home() / "pbd"
)

# CARTELLA DELLE IMPOSTAZIONI: salvata sono nella root di default
CONF_DIR: Final[Path] = Path("conf")

# CARTELLE DELL'APPLICAZIONE: salvate nella root utente 
BOOKMARKS_DIR: Final[Path] = Path("bookmarks")
LISTS_DIR: Final[Path] = Path("lists")

# FILES DI CONFIGURAZIONE
CONFIG_MAIN_FILE: Final[Path] = Path("config.json")
CONFIG_ADVANCED_FILE: Final[Path] = Path("advanced.json")

# LISTA DELLE CHIAVI
CONFIG_KEY_USER_ROOT: Final[str] = "user_root"
CONFIG_KEY_PREF_MEDIA: Final[str] = "preferred_media_formats"

ADVANCED_KEY_CODEC: Final[str] = "codec"
ADVANCED_KEY_WEBM_CODEC: Final[str] = f"{ADVANCED_KEY_CODEC}.webm"
ADVANCED_KEY_MP4_CODEC: Final[str] = f"{ADVANCED_KEY_CODEC}.mp4"

# IMPOSTAZIONI DI DEFAULT
DEFAULT_PREFERRED_MEDIA_FORMATS: Final[PreferredMediaFormats] = PreferredMediaFormats(
    gif=True,
    webm=True,
    mp4=False,
)

# IMPOSTAZIONI DI DEFAULT AVANZATE
DEFAULT_CODEC_SETTINGS: Final[CodecSettings] = CodecSettings(
    webm="vp9",
    mp4="h264",
)

# SEMANTICA DEI FILES LISTA PREFERITI
NOT_FOUND_CSV_PREFIX: Final[str] = "not_found_"
DISCARDED_CSV_PREFIX: Final[str] = "discarded_"

# FILES DELLE OPERE
FETCH_CHECKPOINT_FILE: Final[Path] = Path("fetch.json")
METADATA_FILE: Final[Path] = Path("metadata.json")
UGOIRA_ZIP_FILE: Final[Path] = Path("ugoira.zip")

