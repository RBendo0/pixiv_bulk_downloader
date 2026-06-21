import msvcrt
import winsound

import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"

    COLOR_RESET = "\033[0m"

    def __init__(self):
        self._pending: dict[str, dict] = {}

    def _not_valid_input(
            self,
    ) -> None:

        self.line(
            "[!]: Invalid selection.",
            self.COLOR_ERROR,
            history=False,
        )

        # Beeppata contrariata
        # winsound.Beep(1000, 200)
        # winsound.Beep(1000, 150)
        winsound.MessageBeep()

    def line(
        self,
        text: str,
        color: str = COLOR_DEFAULT,
        *,
        home: bool = False,
        clear: bool = False,
        history: bool = True,
    ) -> None:

        prefix = ""
        
        if home:
            prefix += "\r"

        if clear:
            prefix += "\033[K"

        postfix = ""

        if history:
            postfix += "\n"

        print(
            f"{prefix}"
            f"{color}{text}{self.COLOR_RESET}"
            f"{postfix}",
            end="",
            flush=True,
        )

    def menu(
        self,
        title: str,
        options: dict[str, str],
        footer: str = "",
        prompt: str = "Scelta:",
        validate: str = "",
        clear: bool = False, 
    ) -> str:

        menu_lines = 0

        if title:
            self.line(f" {title}")
            self.line("")
            menu_lines = 2

        for key, label in options.items():
            self.line(f"[{key}] {label}")
            menu_lines += 1

        if footer:
            self.line("")
            self.line(footer)
            self.line("")
            menu_lines += 3

        if not validate:
            validate = "".join(options.keys())

        choice = self.input_key(prompt, validate)

        menu_lines += 1

        if clear:

            print("\r\033[K", end="")
            for _ in range(menu_lines):
                print("\033[A\r\033[K", end="")

        return choice

    def main_menu(
        self,
        title: str,
        options: dict[str, str],
        footer: str = "",
        top_margin: int = 0,
        bottom_margin: int = 0,
        prompt: str = "Scelta:",
        validate: str = "",
    ) -> str:

        for _ in range(top_margin):
            self.line("")

        width = len(f" {title}")

        frame = "=" * width

        self.line(frame)
        self.line(f" {title}")
        self.line(frame)
        self.line("")

        choice = self.menu(
            "", 
            options,
            footer,
            prompt,
            validate,
        )

        for _ in range(bottom_margin):
            self.line("")

        return choice

    def input_key(
        self,
        prompt: str = "",
        valid: str = "",
    ) -> str:

        while True:

            if prompt:
                self.line(
                    prompt + " ",
                    home=True,
                    clear=True,
                    history=False,
                )

            c = pwinput.getch()

            c = c.decode(
                errors="ignore"
            )

            if c == "\x03":
                print()
                raise KeyboardInterrupt

            if not valid or c in valid:
                self.line("")
                return c

            self._not_valid_input()

    def set_pending(
        self,
        name: str,
        prompt: str,
        input: str,
    ) -> None:

        self._pending[name] = {
            "prompt": prompt,
            "input": input,
            "state": False,
        }

    def _listen_pending(self) -> None:

        while msvcrt.kbhit():

            key = msvcrt.getch().decode(
                errors="ignore"
            )

            for pending in self._pending.values():

                if key in pending["input"]:

                    pending["state"] = True

    def requested(
        self,
        name: str,
    ) -> bool:

        self._listen_pending()

        pending = self._pending.get(name)

        if pending is None:
            return False

        return pending["state"]
    
    def pending_prompt(
        self,
        name: str,
    ) -> str:

        pending = self._pending.get(name)

        if pending is None:
            return ""

        return pending["prompt"]    


# Istanza comune della classe di interfaccia grafica
ui = UI()