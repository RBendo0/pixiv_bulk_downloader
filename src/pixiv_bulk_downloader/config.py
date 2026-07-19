from pathlib import Path
from typing import Any

from .const import (
    CONF_DIR,
    CONFIG_FILE,
    DEFAULT_ROOT,
    DEFAULT_WEBM_CODEC,
)
from .iofile import JsonFile


class Config:

    _config_file: Path = (
        DEFAULT_ROOT
        / CONF_DIR
        / CONFIG_FILE
    )

    _backup_file: Path = _config_file.with_suffix(
        _config_file.suffix + ".bak"
    )

    class Key:
        USER_ROOT = "user_root"
        WEBM_CODEC = "webm_codec"

    _defaults: dict[str, Any] = {
        Key.USER_ROOT: "",
        Key.WEBM_CODEC: DEFAULT_WEBM_CODEC,
    }

    @classmethod
    def load(
        cls,
        key: str,
    ) -> Any | None:

        if not cls._config_file.exists():
            return None

        config = JsonFile(
            cls._config_file
        ).load()

        if not isinstance(config, dict):
            raise TypeError(
                f"Config.load() '{cls._config_file.name}': "
                "expected key/value format."
            )

        return config.get(key)

    @classmethod
    def backup(
        cls,
        key: str,
    ) -> None:

        value = cls._defaults.get(key)

        if cls._config_file.exists():

            config = JsonFile(
                cls._config_file
            ).load()

            if not isinstance(config, dict):
                raise TypeError(
                    f"Config.backup() '{cls._config_file.name}': "
                    "expected key/value format."
                )

            value = config.get(
                key,
                value,
            )

        if cls._backup_file.exists():

            backup = JsonFile(
                cls._backup_file
            ).load()

            if not isinstance(backup, dict):
                raise TypeError(
                    f"Config.backup() '{cls._backup_file.name}': "
                    "expected key/value format."
                )

        else:
            backup = {}

        backup[key] = value

        JsonFile(
            cls._backup_file
        ).save(backup)

    @classmethod
    def save(
        cls,
        key: str,
        value: Any,
    ) -> None:

        cls.backup(key)

        if cls._config_file.exists():

            config = JsonFile(
                cls._config_file
            ).load()

            if not isinstance(config, dict):
                raise TypeError(
                    f"Config.save() '{cls._config_file.name}': "
                    "expected key/value format."
                )

        else:
            config = {}

        config[key] = value

        JsonFile(
            cls._config_file
        ).save(config)

    @classmethod
    def restore(
        cls,
        key: str,
    ) -> None:

        value = cls._defaults.get(key)

        if cls._backup_file.exists():

            backup = JsonFile(
                cls._backup_file
            ).load()

            if not isinstance(backup, dict):
                raise TypeError(
                    f"Config.restore() '{cls._backup_file.name}': "
                    "expected key/value format."
                )

            value = backup.get(
                key,
                value,
            )

        if cls._config_file.exists():

            config = JsonFile(
                cls._config_file
            ).load()

            if not isinstance(config, dict):
                raise TypeError(
                    f"Config.restore() '{cls._config_file.name}': "
                    "expected key/value format."
                )

        else:
            config = {}

        config[key] = value

        JsonFile(
            cls._config_file
        ).save(config)


# Alias della classe statica di configurazione
config = Config