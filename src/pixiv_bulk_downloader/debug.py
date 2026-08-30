import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from .config import config
from .const import (
    ADVANCED_KEY_DEBUG_ENABLED,
    ADVANCED_KEY_DEBUG_FAULT_INJECTION,
    ADVANCED_KEY_DEBUG_SIMULATION,
    DEBUG_LOG_DIR,
    DEFAULT_DEBUG_ENABLED,
    DEFAULT_DEBUG_FAULT_INJECTION,
    DEFAULT_DEBUG_SIMULATION,
)
from .ui import ui


class Timestamp:

    def __init__(self) -> None:
        self._time: datetime = datetime.now(UTC)

    def console(self) -> str:
        return self._time.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

    def log(self) -> str:
        return self._time.isoformat()

    def file(self) -> str:
        return self._time.strftime(
            "%Y%m%d_%H%M%S"
        )


class Debug:

    _enabled: bool = DEFAULT_DEBUG_ENABLED
    _simulation: bool = DEFAULT_DEBUG_SIMULATION
    _fault_injection: bool = DEFAULT_DEBUG_FAULT_INJECTION

    @classmethod
    def _load_setting(
        cls,
        key: str,
    ) -> bool | None:

        from .errors import (
            FileError,
            InvalidDataFormatError,
            UserHasNotDefinedCustomConfiguration,
        )

        try:

            value = config.Advanced.load(key)

            if value is None or value == "":
                raise UserHasNotDefinedCustomConfiguration()

            if not isinstance(value, bool):
                raise InvalidDataFormatError()

            return value

        except UserHasNotDefinedCustomConfiguration:
            pass

        except (FileError, InvalidDataFormatError) as e:

            e.notify(
                f"Failed to load debug setting [@@{key}@@.].",
                with_report=True,
            )

        return None

    @classmethod
    def _show_current_debug_settings(cls) -> None:

        if not cls._enabled:
            return

        ui.line(
            "[+]: Debug mode active.",
            tag_color=ui.COLOR_INFO,
        )

        ui.line(
            "[+]: Simulation mode "
            f"[ @@{'Enabled' if cls._simulation else 'Disabled'}@@. ]",
            tag_color=ui.COLOR_INFO,
        )

        ui.line(
            "[+]: Fault injection mode "
            f"[ @@{'Enabled' if cls._fault_injection else 'Disabled'}@@. ]",
            tag_color=ui.COLOR_INFO,
        )

    @classmethod
    def init(cls) -> None:

        cls._enabled = DEFAULT_DEBUG_ENABLED
        cls._simulation = DEFAULT_DEBUG_SIMULATION
        cls._fault_injection = DEFAULT_DEBUG_FAULT_INJECTION

        enabled = cls._load_setting(
            ADVANCED_KEY_DEBUG_ENABLED
        )

        simulation = cls._load_setting(
            ADVANCED_KEY_DEBUG_SIMULATION
        )

        fault_injection = cls._load_setting(
            ADVANCED_KEY_DEBUG_FAULT_INJECTION
        )

        if enabled is not None:
            cls._enabled = enabled

        if simulation is not None:
            cls._simulation = simulation

        if fault_injection is not None:
            cls._fault_injection = fault_injection

        cls.Log.init()

        cls._show_current_debug_settings()

    @classmethod
    def enabled(cls) -> bool:
        return cls._enabled

    @classmethod
    def simulation(cls) -> bool:
        return cls._enabled and cls._simulation

    @classmethod
    def fault_injection(cls) -> bool:
        return cls._enabled and cls._fault_injection

    @classmethod
    def write(
        cls,
        timestamp: Timestamp,
        message: str,
    ) -> None:

        if not cls._enabled:
            return

        ui.line(
            f"[#]: {timestamp.console()}: {message}",
            ui.COLOR_DEBUG,
            tag_color=ui.COLOR_DEFAULT,
        )    

    class DTB:

        # ===================
        # Debug Trace Binding
        # ===================

        @dataclass(frozen=True)
        class _DebugInfo:
            timestamp: Timestamp

        @classmethod
        def register(
            cls,
            error: Exception,
            timestamp: Timestamp,
        ) -> None:

            if not Debug._enabled:
                return

            error._debug_info = cls._DebugInfo(  # pyright: ignore[reportAttributeAccessIssue]
                timestamp=timestamp,
            )

        @classmethod
        def inherit(
            cls,
            error: Exception,
            source: Exception,
        ) -> None:

            if not Debug._enabled:
                return

            debug_info = getattr(
                source,
                "_debug_info",
                None,
            )

            if debug_info is None:
                return

            error._debug_info = debug_info  # pyright: ignore[reportAttributeAccessIssue]

        @classmethod
        def log(
            cls,
            error: Exception,
            message: str,
        ) -> None:

            if not Debug._enabled:
                return

            debug_info = getattr(
                error,
                "_debug_info",
                None,
            )

            if debug_info is None:
                return

            Debug.Log.write(
                "ERRSYS",
                debug_info.timestamp,
                message,
            )

    class Log:

        _file: Path | None = None
        _lock = Lock()

        @classmethod
        def init(cls) -> None:
            cls._file = None


        @classmethod
        def write(
            cls,
            source: str,
            timestamp: Timestamp,
            message: str,
            context_cat: str | None = None,
            context_val: str | None = None,
        ) -> None:

            if not Debug._enabled:
                return

            record = {
                "timestamp": timestamp.log(),
                "source": source,
                "message": message,
            }

            if context_cat is not None:
                record["context_cat"] = context_cat

            if context_val is not None:
                record["context_val"] = context_val

            with cls._lock:

                if cls._file is None:
                    cls._file = (
                        DEBUG_LOG_DIR
                        / f"{Timestamp().file()}.jsonl"
                    )

                DEBUG_LOG_DIR.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with cls._file.open(
                    "a",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        record,
                        file,
                        ensure_ascii=False,
                    )

                    file.write("\n")


# Alias della classe statica che gestisce il debug
debug = Debug


"""
error = SomeError(...)

debug_info = Debug.message(
    message,
    artwork_id,
)

Debug.DTB.register(
    error,
    debug_info,
)

Debug.Log.write(
    "DEBUG",
    debug_info,
)

raise error
"""