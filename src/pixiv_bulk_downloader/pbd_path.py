from pathlib import Path
from typing import Final

from .config import config
from .const import (
    BOOKMARKS_DIR,
    CONFIG_KEY_USER_ROOT,
    DEFAULT_ROOT,
    LISTS_DIR,
)
from .errors import (
    FileError,
    FileOperationError,
    InvalidDataFormatError,
    PBDError,
    UserHasNotDefinedCustomConfiguration,
)
from .metadata import PixivMetadata
from .ui import ui

_BasePath = type(Path())


class PixivPath(_BasePath):

    _FIRST_LEVEL_BUCKET_COUNT: Final[int] = 256

    @staticmethod
    def _get_bucket(
        id_: int,
        bucket_count: int,
    ) -> int:

        return id_ % bucket_count

    def author_dir(
        self,
        metadata: PixivMetadata,
    ) -> "PixivPath":

        first_bucket = self._get_bucket(
            metadata.author_id,
            self._FIRST_LEVEL_BUCKET_COUNT,
        )

        author_dirname = (
            f"{metadata.author_id}_"
            f"{metadata.author_name(for_path=True)}"
        )

        return PixivPath(
            self
            / str(first_bucket)
            / author_dirname
        )

    def artwork_dir(
        self,
        metadata: PixivMetadata,
    ) -> "PixivPath":

        artwork_dirname = (
            f"{metadata.artw_id}_"
            f"{metadata.artw_title(for_path=True)}"
        )

        return PixivPath(
            self.author_dir(metadata)
            / artwork_dirname
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
           f"[+]: Storage root located to: [ @@{cls._root}@@. ]",
           tag_color=ui.COLOR_INFO,
        )

    @classmethod
    def _mkdir(cls, path: Path) -> None:

        # Identico al mkdir metodo della classe Path, impostato per creare la cartella se non esiste 
        # Necessario perchè introduce una convenzione di chiamata che traduce gli errori dalla classe 
        # OSError a PBDError

        try:

            path.mkdir(
                parents=True,
                exist_ok=True,
            )

        except OSError as e:
            
            raise PBDError.hierarchy(e) from e

    @classmethod
    def init(
        cls,
        cli_user_root: Path | None = None,
    ) -> None:

        # Controlla se c'è un percorso da riga di comando già registrato
        # ATTENZIONE: affinché l'override del percorso specificato da riga
        # di comando funzioni correttamente, cls._cli_user_root deve essere
        # inizializzata a livello di classe con il valore None.        
        if cls._cli_user_root is not None:
            cli_user_root = cls._cli_user_root

        # ATTENZIONE: l'eventuale percorso indicato da riga di comando, anche all'interno dei collegamenti,
        # ha la precedenza sia sul percorso di default che su quello specificato nel file di configurazione
        actual_user_root = cli_user_root = cls._normalize_root(cli_user_root) if cli_user_root else None

        cls._cli_user_root = cli_user_root
 
        if cli_user_root is None:

            try:

                value = config.load(CONFIG_KEY_USER_ROOT)

                if value is None or value == "":

                    actual_user_root = None

                elif isinstance(value, str):

                    actual_user_root = cls._normalize_root(Path(value))

                else:

                    raise InvalidDataFormatError()

            except UserHasNotDefinedCustomConfiguration:

                actual_user_root = None

            except (FileError, InvalidDataFormatError) as e:

                ui.line(
                    "[!]: Failed to load storage path.",
                    ui.COLOR_ERROR,
                )

                ui.line(
                    f"     {e.report()}",
                    ui.COLOR_ERROR,
                )

                ui.line(
                    "     Storage path will be set to default.",
                    ui.COLOR_WARNING,
                )

                actual_user_root = None

        cls._user_root = actual_user_root

        cls._root = (
            actual_user_root
            if actual_user_root is not None
            else cls._default_root
        )

        cls._bookmarks = cls._root / BOOKMARKS_DIR
        cls._lists = cls._root / LISTS_DIR

        # Genera la Directory principale e la sottocartella \lists
        # in caso di errore traduce l'eccezione nella classe PBDError
        cls._mkdir(cls._lists)

        cls._show_current_storage_root()

    @classmethod
    def config_root_dir(cls) -> None:

        ui.line()

        if cls._cli_user_root is not None:

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

            cls._show_current_storage_root()

            return

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

                cls._mkdir(root)

            except FileOperationError as e:

                ui.line(
                    f"[!]: Failed to set storage path: "
                    f"{e.report()}",
                    ui.COLOR_ERROR,
                )

                cls._show_current_storage_root()

                return

        if not config.save_with_interact(
            key=CONFIG_KEY_USER_ROOT,
            value=str(root),
            subject="storage path"
        ):

            cls._show_current_storage_root()

            return

        try:

            cls.init()

        except FileOperationError as e:

            ui.line(
                "[!]: Path init failed: ",
                ui.COLOR_ERROR,
            )

            ui.line(
                f"    {e.report()}",
                ui.COLOR_ERROR,
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
    def bookmarks(cls) -> Path:
        return cls._bookmarks

    @classmethod
    def lists(cls) -> Path:
        return cls._lists
    

# Alias della classe statica che gestisce i percorsi di archiviazione
sd = StorageDirs    