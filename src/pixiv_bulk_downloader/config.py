from pathlib import Path
from typing import Any

from .const import (
    CONF_DIR,
    CONFIG_ADVANCED_FILE,
    CONFIG_MAIN_FILE,
    DEFAULT_ROOT,
)
from .errors import (
    ConfigError,
    FileError,
    InvalidDataFormatError,
    UserHasNotDefinedCustomConfiguration,
)
from .iofile import JsonFile
from .ui import ui


class Config:

    _config_file: Path = (
        DEFAULT_ROOT
        / CONF_DIR
        / CONFIG_MAIN_FILE
    )

    _backup_file: Path = _config_file.with_suffix(
        _config_file.suffix + ".bak"
    )

    @classmethod
    def _load_file(
        cls,
        path: Path,
    ) -> Any:

        try:

            return JsonFile(
                path
            ).load()

        except Exception as error:

            raise ConfigError.hierarchy(
                error
            ) from None

    @classmethod
    def _save_file(
        cls,
        path: Path,
        data: Any,
    ) -> None:

        try:

            JsonFile(
                path
            ).save(data)

        except Exception as error:

            raise ConfigError.hierarchy(
                error
            ) from None

    @classmethod
    def _resolve_path(
        cls,
        data: dict[str, Any],
        path: str,
        default: Any = None,
    ) -> Any:

        value: Any = data

        for key in path.split("."):

            if not isinstance(value, dict):
                return default

            value = value.get(key)

            if value is None:
                return default

        return value
    
    @classmethod
    def _set_path(
        cls,
        data: dict[str, Any],
        path: str,
        value: Any,
    ) -> None:

        keys = path.split(".")
        target = data

        for key in keys[:-1]:

            child = target.get(key)

            if not isinstance(child, dict):
                child = {}
                target[key] = child

            target = child

        target[keys[-1]] = value    

    @classmethod
    def load(
        cls,
        key: str,
    ) -> Any | None:

        config = cls._load_file(cls._config_file)

        if not isinstance(config, dict):
            raise InvalidDataFormatError(
                "conf:load: "
                "expected key/value format."
            )

        return cls._resolve_path(config, key)

    @classmethod
    def backup(
        cls,
        key: str,
    ) -> bool:

        try:

            config = cls._load_file(cls._config_file)

            if not isinstance(config, dict):
                raise InvalidDataFormatError(
                    f"conf:bkup '{cls._config_file.name}': "
                    "expected key/value format."
                )

            value = cls._resolve_path(config, key, "")

        except UserHasNotDefinedCustomConfiguration:

            # Non Serve salvare un backup se il file di configurazione non esiste
            return False

        try:

            backup = cls._load_file(cls._backup_file)

            if not isinstance(backup, dict):
                raise InvalidDataFormatError(
                    f"conf:bkup '{cls._backup_file.name}': "
                    "expected key/value format."
                )

        except UserHasNotDefinedCustomConfiguration:    

            backup = {}

        cls._set_path(backup, key, value)

        cls._save_file(cls._backup_file, backup)

        return True

    @classmethod
    def save(
        cls,
        key: str,
        value: Any,
    ) -> None:

        try:

            config = cls._load_file(cls._config_file)

            if not isinstance(config, dict):
                raise InvalidDataFormatError(
                    "conf:save: "
                    "expected key/value format."
                )

        except UserHasNotDefinedCustomConfiguration:

            config = {}

        cls._set_path(config, key, value)

        cls._save_file(cls._config_file, config)

    @classmethod
    def restore(
        cls,
        key: str,
    ) -> None:

        try:

            backup = cls._load_file(cls._backup_file)

            if not isinstance(backup, dict):
                raise InvalidDataFormatError(
                    f"conf:rest '{cls._backup_file.name}': "
                    "expected key/value format."
                )

            value = cls._resolve_path(backup, key, "")

        except UserHasNotDefinedCustomConfiguration:

            # Se il file di backup non esiste, non ripristina nessuna chiave
            return

        try:

            config = cls._load_file(cls._config_file)

            if not isinstance(config, dict):
                raise InvalidDataFormatError(
                    f"conf:rest '{cls._config_file.name}': "
                    "expected key/value format."
                )

        except UserHasNotDefinedCustomConfiguration:

            config = {}

        cls._set_path(config, key, value)

        cls._save_file(cls._config_file, config)

        cls._set_path(backup, key, "",)

        cls._save_file(cls._backup_file, backup)

    @classmethod
    def save_with_interact(
        cls,
        *,
        key: str,
        value: Any,
        subject: str,
    ) -> bool:

        backup_available = False

        try:

            backup_available = config.backup(key)

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                "Unable to create a backup of the current configuration.",
                with_report=True,
            )

        try:

            config.save(key, value)

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                f"Unable to save the new {subject}.",
                with_report=True,
            )

            ui.line(
                "[!]: The configuration file may have been damaged.",
                ui.COLOR_ERROR,
            )

            if backup_available:

                ui.line(
                    "[+]: The previous settings can be restored. Proceed?",
                )

                if (
                    ui.confirm(
                        "Press ESC to skip this step",
                        default=ui.KEY_ESCAPE,
                    )
                ):

                    try:

                        config.restore(key)

                    except (FileError, InvalidDataFormatError) as e:

                        e.notify(
                            "Unable to restore previous settings.",
                            with_report=True,
                        )

                    else:    

                        ui.line(
                            "[+]: Previous settings restored. "
                        )

                else:

                    ui.line(
                        "[-]: Previous settings discarded"
                    )

            return False

        return True

    class Advanced:

        _advanced_file: Path = (
            DEFAULT_ROOT
            / CONF_DIR
            / CONFIG_ADVANCED_FILE
        )

        @classmethod
        def _generate_advanced_file(cls) -> None:

            advanced = {

                "_info": {

                    "caption": [
                        "ATTENZIONE: MODULO RISERVATO AGLI ESPERTI",
                        "Per ogni proprietà viene definito in 'avaible_choices' la lista di opzioni",
                        "disponibili da specifica pari pari nel sottostante campo 'value', riportare",
                        "l'opzione desiderata mantenendola nel formato stringa.",

                    ],

                },

                "codec": {

                    "webm": {

                        "caption": [
                            "Codec utilizzato per generare i file WebM.",
                            "Modificare il valore scegliendo una delle opzioni ammesse.",
                        ],

                        "available_choices": [
                            "vp8",
                            "vp9",
                            "av1",
                        ],

                        "value": "",
                    },

                    "mp4": {

                        "caption": [
                            "Codec utilizzato per generare i file MP4.",
                            "Modificare il valore scegliendo una delle opzioni ammesse.",
                        ],

                        "available_choices": [
                            "h264",
                            "h265",
                        ],

                        "value": "",
                    },

                }
            }

            Config._save_file(cls._advanced_file, advanced)

        @classmethod
        def show_and_reset_settings(cls) -> None:

            ui.line()

            ui.line(
                "This option generates the configuration file:"
            )

            ui.line(
                f"{cls._advanced_file}"
            )

            ui.line(
                "This file allows advanced application settings to be edited using a standard text editor."
            )

            ui.line(
                "If the file already exists, it will be recreated and any previous changes will be lost."            
            )

            if (not ui.confirm("Generate/Reset advanced settings")):
                return

            cls._generate_advanced_file()

        @classmethod
        def load(
            cls,
            key: str,
        ) -> Any | None:

            advanced = Config._load_file(cls._advanced_file)

            if not isinstance(advanced, dict):
                raise InvalidDataFormatError(
                    "conf:adv:load: "
                    "expected key/value format."
                )

            return Config._resolve_path(
                advanced,
                f"{key}.value",
            )


# Alias della classe statica di configurazione
config = Config