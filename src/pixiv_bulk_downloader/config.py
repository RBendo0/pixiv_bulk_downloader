from pathlib import Path
from typing import Any

from .const import (
    BOOKMARKS_DIR,
    CONF_DIR,
    CONFIG_FILE,
    DEFAULT_ROOT,
    LISTS_DIR,
)
from .errors import PBDError
from .iofile import JsonFile
from .ui import ui


class Config:

    _USER_ROOT_KEY = "user_root"

    @classmethod
    def init(
        cls,
        cli_user_root: Path | None = None,
    ) -> None:

        cls.Dirs.init(cli_user_root)

    @classmethod
    def load(
        cls,
        key: str,
    ) -> Any | None:

        try:

            config = JsonFile(
                cls.Dirs.config()
            ).load()

            if not isinstance(config, dict):
                return None

            return config.get(key)

        except Exception:
            return None

    @classmethod
    def save(
        cls,
        key: str,
        value: Any,
    ) -> None:

        try:

            config = JsonFile(
                cls.Dirs.config()
            ).load()

            if not isinstance(config, dict):
                config = {}

        except Exception:
            config = {}

        config[key] = value

        JsonFile(
            cls.Dirs.config()
        ).save(config)

    @classmethod
    def root_dir(cls) -> None:

        ui.line()

        ui.line(
            "[i]: Enter new storage path "
            "(leave empty for default path)."
        )

        ui.line(
            "[i]: Changes will take effect "
            "after pressing Enter."
        )

        root = ui.input_string(
            prompt="[?]: >",
            default=str(cls.Dirs.root()),
        )

        ui.clear_lines(1)

        # Il file di configurazione distingue due casi:
        # - ""     -> usa il percorso predefinito;
        # - Path() -> usa un percorso personalizzato.
        #
        # Path("") rappresenta la directory corrente ("."),
        # non il percorso predefinito. Per questo il caso
        # della stringa vuota viene gestito separatamente.
        root = Path(root) if root else ""

        # Verifica il percorso tentando di crearlo.
        #
        # mkdir() svolge due funzioni:
        # - valida il percorso;
        # - crea la directory se non esiste.
        if root:

            if root.name.casefold() != "pbd":
                root /= "pbd"

            try:

                root.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            except Exception as e:

                e = PBDError.cast(e)

                ui.line(
                    f"[!]: Failed to set storage path: "
                    f"{e.info()}: "
                    f"{type(e).__name__}: {e}",
                    ui.COLOR_ERROR,
                )

                return

        config_file = JsonFile(
            cls.Dirs.config()
        )

        # Il percorso è valido e disponibile.

        config_file.backup()

        try:

            Config.save(
                "user_root",
                str(root),
            )

        except Exception as e:

            e = PBDError.cast(e)

            config_file.restore()
  
            ui.line(
                f"[!]: Path restored to previous settings: "
                f"{e.info()}: "
                f"{type(e).__name__}: {e}",
                ui.COLOR_ERROR,
            )

        Config.init()

        ui.line(
            f"[+]: New path set to: {Config.Dirs.root()}",
            color=ui.COLOR_SUCCESS,
        )

    class Dirs:

        _default_root: Path = DEFAULT_ROOT
        _user_root: Path | None = None

        _root: Path
        _conf: Path
        _config: Path
        _bookmarks: Path
        _lists: Path

        @classmethod
        def init(
            cls,
            cli_user_root: Path | None = None,
        ) -> None:

            cls._conf = cls._default_root / CONF_DIR
            cls._config = cls._conf / CONFIG_FILE

            if cli_user_root is None:

                value = Config.load(Config._USER_ROOT_KEY)

                if isinstance(value, str) and value:
                    cli_user_root = Path(value)

            cls._user_root = cli_user_root

            cls._root = (
                cli_user_root
                if cli_user_root is not None
                else cls._default_root
            )

            cls._bookmarks = cls._root / BOOKMARKS_DIR
            cls._lists = cls._root / LISTS_DIR

            cls._lists.mkdir(
                parents=True,
                exist_ok=True,
            )            

        @classmethod
        def default_root(cls) -> Path:
            return cls._default_root

        @classmethod
        def user_root(cls) -> Path | None:
            return cls._user_root

        @classmethod
        def root(cls) -> Path:
            return cls._root

        @classmethod
        def conf(cls) -> Path:
            return cls._conf

        @classmethod
        def config(cls) -> Path:
            return cls._config

        @classmethod
        def bookmarks(cls) -> Path:
            return cls._bookmarks

        @classmethod
        def lists(cls) -> Path:
            return cls._lists


# Alias della classe (statica) di configurazione 
config = Config