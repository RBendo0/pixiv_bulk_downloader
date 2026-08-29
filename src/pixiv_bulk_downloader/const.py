import sys
from pathlib import Path
from typing import Final

from .pbd_types import (
    CodecSettings,
    MetadataVersionDescriptor,
    PreferredMediaFormats,
)

# ROOT DI DEFAULT: necessaria per archiviare le impostazioni dell'applicazione
# viene determinata dalla posizione dell'eseguibile compilato con PyInstaller
# se l'esecuzione è partita da lì, altrimenti usa il percorso assoluto
DEFAULT_ROOT: Final[Path] = (
    Path(sys.executable).resolve().parent.parent
    if getattr(sys, "frozen", False)
    else Path.home() / "pbd"
)

BROWSER_DIR: Final[Path] = Path("browser")

CHROME_PROFILE_DIR: Final[Path] = (
    DEFAULT_ROOT
    / BROWSER_DIR
    / "chrome"
    / "profile"
)

PROFILE_DIR: Final[Path] = CHROME_PROFILE_DIR

TOOLS_DIR: Final[Path] = Path("tools")

FFMPEG_EXECUTABLE: Final[Path] = (
    DEFAULT_ROOT
    / TOOLS_DIR
    / "ffmpeg"
    / "bin"
    / "ffmpeg.exe"
)

FFMPEG_LOG_DIR: Final[Path] = (
    DEFAULT_ROOT
    / "logs"
    / "ffmpeg"
)

# TRADUZIONE DEI SIMBOLI DEI CODEC
# NEL NOME DELL'ENCODER FFMPEG
FFMPEG_ENCODERS: Final[dict[str, str]] = {
    "vp8":  "libvpx",
    "vp9":  "libvpx-vp9",
    "av1":  "libaom-av1",
    "h264": "libx264",
    "h265": "libx265",
}

MEDIA_TOOL_EXECUTABLE: Final[Path] = FFMPEG_EXECUTABLE
MEDIA_TOOL_LOG_DIR: Final[Path] = FFMPEG_LOG_DIR
MEDIA_TOOL_ENCODERS: Final[dict[str, str]] = FFMPEG_ENCODERS

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
CONFIG_KEY_AUTHOR_METADATA: Final[str] = "author_metadata"
CONFIG_KEY_PREF_MEDIA: Final[str] = "preferred_media_formats"

ADVANCED_KEY_DEBUG: Final[str] = "debug"
ADVANCED_KEY_DEBUG_ENABLED: Final[str] = (
    f"{ADVANCED_KEY_DEBUG}.enabled"
)
ADVANCED_KEY_DEBUG_SIMULATION: Final[str] = (
    f"{ADVANCED_KEY_DEBUG}.simulation"
)
ADVANCED_KEY_DEBUG_FAULT_INJECTION: Final[str] = (
    f"{ADVANCED_KEY_DEBUG}.fault_injection"
)

ADVANCED_KEY_CODEC: Final[str] = "codec"
ADVANCED_KEY_WEBM_CODEC: Final[str] = f"{ADVANCED_KEY_CODEC}.webm"
ADVANCED_KEY_MP4_CODEC: Final[str] = f"{ADVANCED_KEY_CODEC}.mp4"

# IMPOSTAZIONI DI DEFAULT
DEFAULT_AUTHOR_METADATA: Final[bool] = False

DEFAULT_PREFERRED_MEDIA_FORMATS: Final[PreferredMediaFormats] = PreferredMediaFormats(
    gif=True,
    webm=True,
    mp4=False,
)

# IMPOSTAZIONI DI DEFAULT AVANZATE
DEFAULT_DEBUG_ENABLED: Final[bool] = False
DEFAULT_DEBUG_SIMULATION: Final[bool] = False
DEFAULT_DEBUG_FAULT_INJECTION: Final[bool] = False

DEFAULT_CODEC_SETTINGS: Final[CodecSettings] = CodecSettings(
    webm="vp9",
    mp4="h264",
)

# SEMANTICA DEI FILES LISTA PREFERITI
NOT_FOUND_CSV_PREFIX: Final[str] = "not_found_"
DISCARDED_CSV_PREFIX: Final[str] = "discarded_"

# FILES DELLE OPERE
UGOIRA_ZIP_FILE: Final[Path] = Path("ugoira.zip")

ARTWORK_METADATA_FILE = Path("artwork.metadata.json")
AUTHOR_METADATA_FILE = Path("author.metadata.json")

ARTWORK_METADATA_VERSION: Final[MetadataVersionDescriptor] = {
    "LAST": 1,
    "CURRENT": 1,
}

AUTHOR_METADATA_VERSION: Final[MetadataVersionDescriptor] = {
    "LAST": 1,
    "CURRENT": 1,
}