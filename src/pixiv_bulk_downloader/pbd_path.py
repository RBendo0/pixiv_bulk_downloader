import math
from pathlib import Path

from .config import config
from .const import (
    BOOKMARKS_DIR,
    DEFAULT_ROOT,
    LISTS_DIR,
)
from .errors import PBDError
from .ui import ui

_BasePath = type(Path())


class PixivPath(_BasePath):

    _GROUP_SIZE = 500

    _ID_FORK_000 = 125_000_000

    _N_MAX = 39_724
    _ID_MAX = 145_654_652

    _DENSITY_HYPE_A = 0.16223786
    _DENSITY_HYPE_B = 1.09912234
    _DENSITY_HYPE_SCALE = 3.0

    _DENSITY_STABLE = 550
    _BUCKET_GUARD_BAND = 1000
    
    # Il valore di questa variavile è calcolato mediante la formula 
    #   _HYPE_MAX_BUCKET = MAX(ID_GROUP_HYPE(0), ID_GROUP_HYPE(_ID_FORK_000))
    # dove ID_GROUP_HYPE() è la formula per calcolare il bucket nell'era hype
    _HYPE_MAX_BUCKET = 1_563_047

    _BUCKET_STABLE_OFFSET = (_HYPE_MAX_BUCKET + _BUCKET_GUARD_BAND)

    def _density_hype(
        self,
        id_: int,
    ) -> float:

        a = (
            self._DENSITY_HYPE_A
            * self._ID_MAX
        )

        b = (
            self._DENSITY_HYPE_B
            * self._ID_MAX
        )

        return (
            self._DENSITY_HYPE_SCALE
            * a
            / (
                self._N_MAX
                * math.exp(
                    (id_ - b)
                    / a
                )
            )
        )
    
    def _get_bucket(
        self,
        id_: int,
    ) -> str:

        if id_ < self._ID_FORK_000:

            bucket = int(
                id_
                / (
                    self._GROUP_SIZE
                    * self._density_hype(id_)
                )
            )

            return f"H_{bucket}"

        bucket = int(
            self._BUCKET_STABLE_OFFSET
            + (
                id_
                / (
                    self._GROUP_SIZE
                    * self._DENSITY_STABLE
                )
            )
        )

        return f"S_{bucket}"
    
    def work_dir(
        self,
        id_: int,
        title: str | None = None,
    ) -> "PixivPath":

        bucket = self._get_bucket(id_)

        folder_name = str(id_)

        if title is not None:
            folder_name += f"_{title}"

        return PixivPath(
            self / bucket / folder_name
        )


class StorageDirs:

    _cli_user_root: Path | None = None

    _default_root: Path = DEFAULT_ROOT
    _user_root: Path | None = None

    _root: Path
    _bookmarks: Path
    _lists: Path

    @classmethod
    def _normalize_root(
        cls,
        root: Path,
    ) -> Path:

        if root.name.casefold() != "pbd":
            root /= "PBD"

        return root

    @classmethod
    def _show_current_storage_root(cls) -> None:

        ui.line(
           "[i]: Storage root: ",
           history=False,
        )

        ui.line(
           f"{cls._root}",
           color=ui.COLOR_INPUT,
           home=False,
           clear=False,
        )

    @classmethod
    def init(
        cls,
        cli_user_root: Path | None = None,
    ) -> None:

        # ATTENZIONE: l'eventuale percorso indicato da riga di comando, anche all'interno dei collegamenti,
        # ha la precedenza sia sul percorso di default che su quello specificato nel file di configurazione
        cli_user_root = cls._normalize_root(cli_user_root) if cli_user_root else None

        cls._cli_user_root = cli_user_root
 
        if cli_user_root is None:

            try:

                value = config.load(
                    config.Key.USER_ROOT
                )

            except Exception as e:

                e = PBDError.cast(e)

                ui.line(
                    f"[!]: Failed to load storage path: "
                    f"{e.info()}: "
                    f"{type(e).__name__}: {e}",
                    ui.COLOR_ERROR,
                )

                # Il percorso non può essere determinato da una
                # configurazione illeggibile. Ripristina quindi
                # l'ultimo valore valido e tenta nuovamente la lettura.
                config.restore(
                    config.Key.USER_ROOT
                )

                value = config.load(
                    config.Key.USER_ROOT
                )

                ui.line(
                    "[+]: Storage path restored "
                    "from previous settings.",
                    ui.COLOR_WARNING,
                )

            if isinstance(value, str) and value:
                cli_user_root = cls._normalize_root(Path(value))

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

        cls._show_current_storage_root()

    @classmethod
    def config_root_dir(cls) -> None:

        if cls._cli_user_root is not None:

            ui.line()

            ui.line(
                "[!]: The storage path cannot be changed while "
                "a command-line path override is active.",
                ui.COLOR_WARNING,
            )

            ui.line(
                "[i]: Command-line paths, including those specified "
                "in link files, take precedence over both the default "
                "path and the configuration file settings."
            )

        else:

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
                prompt="[?]: Root",
                default=str(cls._root),
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

            # Verifica che il nuovo percorso di archiviazione sia
            # utilizzabile prima di salvarlo nella configurazione.
            #
            # mkdir() svolge due funzioni:
            # - valida il percorso;
            # - crea la directory se non esiste.
            if root:

                root = cls._normalize_root(root)

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

                    cls._show_current_storage_root()

                    return

            try:

                config.save(
                    config.Key.USER_ROOT,
                    str(root),
                )

            except Exception as e:

                e = PBDError.cast(e)

                ui.line(
                    f"[!]: Failed to save storage path: "
                    f"{e.info()}: "
                    f"{type(e).__name__}: {e}",
                    ui.COLOR_ERROR,
                )

        cls.init(cls._cli_user_root)

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
    def bookmarks(cls) -> Path:
        return cls._bookmarks

    @classmethod
    def lists(cls) -> Path:
        return cls._lists
    

# Alias della classe statica che gestisce i percorsi di archiviazione
sd = StorageDirs    