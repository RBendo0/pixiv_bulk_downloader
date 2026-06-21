import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"

    COLOR_RESET = "\033[0m"

    def __init__(self):

        self._reset_block()

    def _reset_block(self):
        self._count = 0
    
    def _add_lines(self, delta=1):
    
        self._count += delta
 
    def clear(self, keep=0):

        print("\033[2K\r", end="")

        lines = max(0, self._count - keep)

        for _ in range(lines):

            print("\033[F\033[2K", end="")

        self._reset_block()
    
    def message(
        self,
        message: str,
        color: str = COLOR_DEFAULT,
        nl: bool = True,
        block: bool = False
    ) -> None:

        # Azzera il contatore di blocco
        if not block:
            self._reset_block()

        print(
            f"{color}{message}{self.COLOR_RESET}",
            end="\n" if nl else "",
            flush=True,
        )

        # Incrementa il contatore di blocco
        if nl:
            self._add_lines()

    def input_key(
        self,
        prompt: str = "",
        valid: str = "",
        block: bool = False
    ) -> str:

        # Azzera il contatore di blocco
        if not block:
            self._reset_block()

        while True:

            if prompt:
                self.message(
                    prompt + " ",
                    nl=False,
                    block=True,
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
                self._add_lines()
                return c

            self.message(
                "[!]: Invalid selection.\r",
                self.COLOR_ERROR,
                nl=False,
                block=True,
            )

    def menu(
        self,
        title: str,
        options: dict[str, str],
        footer: str = "",
        top_margin: int = 0,
        bottom_margin: int = 0,
        block: bool = False,
    ) -> None:

        # Azzera il contatore di blocco
        if not block:
            self._reset_block()

        width = len(f" {title}")

        for _ in range(top_margin):
            self.message("", block=True)

        self.message("=" * width, block=True)
        self.message(f" {title}", block=True)
        self.message("=" * width, block=True)
        self.message("", block=True)

        for key, label in options.items():
            self.message(
                f"[{key}] {label}",
                block=True
            )

        if footer:
            self.message("", block=True)
            self.message(footer, block=True)

        for _ in range(bottom_margin):
            self.message("", block=True)


# Istanza comune della classe di interfaccia grafica
ui = UI()