import msvcrt
import time
import weakref
import winsound
from dataclasses import dataclass

import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"    # bianco
    COLOR_SUCCESS = "\033[32m"    # verde
    COLOR_WARNING = "\033[33m"    # giallo
    COLOR_ERROR = "\033[31m"      # rosso

    COLOR_RESET = "\033[0m"       # nero

    def line(
        self,
        text: str = "",
        color: str = COLOR_DEFAULT,
        *,
        home: bool = True,
        clear: bool = True,
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
        frame: bool = False,
        top_margin: int = 0,
        bottom_margin: int = 0,
    ) -> int:

        menu_lines = 0

        for _ in range(top_margin):
            self.line()
            menu_lines += 1

        if title:

            width = len(f" {title} ")
            frameline = "=" * width

            if frame: 
                self.line(frameline)
                menu_lines += 1
            
            self.line(f" {title}")

            if frame: 
                self.line(frameline)
                menu_lines += 1

            self.line()

            menu_lines += 2

        for key, label in options.items():
            self.line(f"[{key}] {label}")
            menu_lines += 1
        
        self.line()
        menu_lines += 1

        if footer:
            self.line(footer)
            self.line()
            menu_lines += 2

        for _ in range(bottom_margin):
            self.line()
            menu_lines += 1

        return menu_lines

    def clear_lines(
        self,
        lines: int = 0,
    ) -> None:

        print("\r\033[K", end="", flush=True)

        for _ in range(lines):

            print("\033[A\033[K", end="", flush=True)

    def input_key(
        self,
        prompt: str = "",
        valid: str = "",
        default: str = "",
        timeout: int = 5,
    ) -> str:

        if not prompt:
            prompt = "Choice"

        if not default:

            while True:

                self.line(
                    prompt + ": ",
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
                    self.line()
                    return c

                self.line(
                    "[!]: Invalid selection.",
                    self.COLOR_ERROR,
                    home=False,
                    clear=False,
                    history=False,
                )

                # Beeppata contrariata
                # winsound.Beep(1000, 200)
                # winsound.Beep(1000, 150)
                winsound.MessageBeep()
                
                time.sleep(0.5)

        else:

            for remaining in range(timeout, 0, -1):

                self.line(
                    prompt + f" (Default [{default}] tra {remaining}s): ",
                    history=False,
                )

                start = time.time()

                while time.time() - start < 1.0:

                    if msvcrt.kbhit():

                        c = msvcrt.getch().decode(
                            errors="ignore"
                        )

                        if c == "\x03":
                            print()
                            raise KeyboardInterrupt

                        if not valid or c in valid:
                            self.line()
                            return c

                        self.line(
                            "[!]: Invalid selection.",
                            self.COLOR_ERROR,
                            home=False,
                            clear=False,
                            history=False,
                        )

                        # Beeppata contrariata
                        # winsound.Beep(1000, 200)
                        # winsound.Beep(1000, 150)
                        winsound.MessageBeep()
                        
                        time.sleep(0.5)

                        break

                    time.sleep(0.05)

            self.line("")

            return default

    def confirm(self) -> bool:

        choice = ui.input_key(
            prompt="[?] Continue (Y/N)",
            valid="YN",
            default="Y",
        )

        ui.clear_lines(1)

        return choice == "Y"

    def poll_key(
        self,
        valid: str = "",
    ) -> str:
        
        # poll_key() e InputPending condividono il medesimo buffer
        # di input della console. I caratteri consumati e non validi
        # vengono deliberatamente scartati e non sono soggetti a
        # buffering o reiniezione.
        #
        # Questa scelta privilegia semplicità e prevedibilità del
        # modello rispetto alla conservazione dell'input.

        if not msvcrt.kbhit():
            return ""

        c = msvcrt.getch().decode(
            errors="ignore"
        )

        if c == "\x03":
            print()
            raise KeyboardInterrupt

        if not valid or c in valid:
            return c

        return ""


@dataclass(eq=False)
class InputPending:

    # poll_key() e InputPending condividono il medesimo buffer
    # di input della console. I caratteri consumati e non validi
    # vengono deliberatamente scartati e non sono soggetti a
    # buffering o reiniezione.
    #
    # Questa scelta privilegia semplicità e prevedibilità del
    # modello rispetto alla conservazione dell'input.

    _instances = weakref.WeakSet()

    valid: str
    prompt: str = ""
    requested: bool = False
    notified: bool = False

    def __post_init__(self):

        InputPending._instances.add(self)

    @classmethod
    def _listen(cls) -> None:

        while msvcrt.kbhit():

            key = msvcrt.getch().decode(
                errors="ignore"
            )

            if key == "\x03":
                print()
                raise KeyboardInterrupt

            for pending in cls._instances:

                if key in pending.valid:

                    pending.requested = True

    @property
    def is_requested(self) -> bool:

        self._listen()

        return self.requested

    @property
    def is_notified(self) -> bool:

        return self.notified

    def set_notified(self) -> None:

        self.notified = True

    def reset(self) -> None:

        self.requested = False
        self.notified = False


# Istanza comune della classe di interfaccia grafica
ui = UI()