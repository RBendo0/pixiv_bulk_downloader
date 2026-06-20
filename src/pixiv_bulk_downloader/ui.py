import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"

    COLOR_RESET = "\033[0m"

    def message(
        self,
        message: str,
        color: str = COLOR_DEFAULT,
        cf: bool = False,
        cr: bool = False,
        nl: bool = True,
    ) -> None:

        prefix = ""
        postfix = ""

        if cf:
            prefix += "\033[2K"

        if cr:
            postfix += "\r"

        print(
            f"{color}{prefix}{message}{postfix}{self.COLOR_RESET}",
            end="\n" if nl else "",
            flush=True,
        )

    def input_key(
        self,
        prompt: str = "",
        valid: str = "",
    ) -> str:

        while True:

            if prompt:
                self.message(
                    prompt + " ",
                    nl=False,
                )

            c = pwinput.getch()

            c = c.decode(
                errors="ignore"
            )

            if c == "\x03":
                print()
                raise KeyboardInterrupt

            if not valid or c in valid:
                print()
                return c

            self.message(
                "[!]: Invalid selection.",
                self.COLOR_ERROR,
                cr=True,
                nl=False,
            )

    def menu(
        self,
        title: str,
        options: dict[str, str],
        footer: str = "",
        top_margin: int = 0,
        bottom_margin: int = 0,
    ) -> None:

        width = len(f" {title}")

        for _ in range(top_margin):
            self.message("")

        self.message("=" * width)
        self.message(f" {title}")
        self.message("=" * width)
        self.message("")

        for key, label in options.items():
            self.message(
                f"[{key}] {label}"
            )

        if footer:
            self.message("")
            self.message(footer)

        for _ in range(bottom_margin):
            self.message("")


# Istanza comune della classe di interfaccia grafica
ui = UI()