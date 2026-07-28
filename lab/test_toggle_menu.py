from .pbd_types import ToggleOption
from .ui import UI


def print_result(title: str, options: list[ToggleOption]) -> None:
    print()
    print(title)

    for option in options:
        state = "enabled" if option.enabled else "disabled"
        print(f"- {option.key}: {option.label} -> {state}")


def main() -> None:
    options = [
        ToggleOption(
            key="1",
            label="GIF",
            enabled=True,
        ),
        ToggleOption(
            key="2",
            label="MP4",
            enabled=False,
        ),
        ToggleOption(
            key="3",
            label="WEBM",
            enabled=True,
        ),
    ]

    selected = UI.toggle_menu(
        options,
        header="Formati animazioni",
        footer="Seleziona uno o più formati.",
    )

    print_result(
        "Stato confermato:",
        selected,
    )

    print()
    input("Premi INVIO per provare il menu senza header e footer...")

    selected = UI.toggle_menu(selected)

    print_result(
        "Stato confermato nel secondo test:",
        selected,
    )


if __name__ == "__main__":
    main()
