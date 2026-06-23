import msvcrt
import time
import winsound

import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"
    COLOR_WARNING = "\033[33m"
    COLOR_ERROR = "\033[31m"

    COLOR_RESET = "\033[0m"

    def __init__(self):
        self._pending: dict[str, dict] = {}

    def line(
        self,
        text: str = "",
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
        lines: int,
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
                    self.line()
                    return c

                self.line(
                    "[!]: Invalid selection.",
                    self.COLOR_ERROR,
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
                    home=True,
                    clear=True,
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

    def poll_key(
        self,
        valid: str = "",
    ) -> str:

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

            if key == "\x03":
                print()
                raise KeyboardInterrupt

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