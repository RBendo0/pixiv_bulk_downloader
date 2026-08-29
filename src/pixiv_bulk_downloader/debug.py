from .config import config
from .const import (
    ADVANCED_KEY_DEBUG_ENABLED,
    ADVANCED_KEY_DEBUG_FAULT_INJECTION,
    ADVANCED_KEY_DEBUG_SIMULATION,
    DEFAULT_DEBUG_ENABLED,
    DEFAULT_DEBUG_FAULT_INJECTION,
    DEFAULT_DEBUG_SIMULATION,
)
from .errors import (
    FileError,
    InvalidDataFormatError,
    UserHasNotDefinedCustomConfiguration,
)
from .ui import ui


class Debug:

    _enabled: bool = DEFAULT_DEBUG_ENABLED
    _simulation: bool = DEFAULT_DEBUG_SIMULATION
    _fault_injection: bool = DEFAULT_DEBUG_FAULT_INJECTION

    @classmethod
    def _load_setting(
        cls,
        key: str,
    ) -> bool | None:

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


# Alias della classe statica che gestisce il debug
debug = Debug