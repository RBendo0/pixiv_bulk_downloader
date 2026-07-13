import msvcrt
import re
import time
import weakref
import winsound
from dataclasses import dataclass
from shutil import get_terminal_size
from threading import (
    Event,
    Lock,
    Thread,
    current_thread,
    get_ident,
)

import pwinput


class UI:

    COLOR_DEFAULT = "\033[37m"    # bianco
    COLOR_SUCCESS = "\033[32m"    # verde
    COLOR_WARNING = "\033[33m"    # giallo
    COLOR_ERROR = "\033[31m"      # rosso

    COLOR_RESET = "\033[0m"       # nero

    _console_lock = Lock()

    @classmethod
    def line(
        cls,
        text: str = "",
        color: str = COLOR_DEFAULT,
        *,
        home: bool = True,
        clear: bool = True,
        history: bool = True,
    ) -> None:

        with cls._console_lock:

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
                f"{color}{text}{cls.COLOR_RESET}"
                f"{postfix}",
                end="",
                flush=True,
            )

    @classmethod
    def menu(
        cls,
        title: str,
        options: dict[str, str],
        footer: str = "",
        frame: bool = False,
        top_margin: int = 0,
        bottom_margin: int = 0,
    ) -> int:

        menu_lines = 0

        for _ in range(top_margin):
            cls.line()
            menu_lines += 1

        if title:

            width = len(f" {title} ")
            frameline = "=" * width

            if frame: 
                cls.line(frameline)
                menu_lines += 1
            
            cls.line(f" {title}")

            if frame: 
                cls.line(frameline)
                menu_lines += 1

            cls.line()

            menu_lines += 2

        for key, label in options.items():
            cls.line(f"[{key}] {label}")
            menu_lines += 1
        
        cls.line()
        menu_lines += 1

        if footer:
            cls.line(footer)
            cls.line()
            menu_lines += 2

        for _ in range(bottom_margin):
            cls.line()
            menu_lines += 1

        return menu_lines

    @classmethod
    def clear_lines(
        cls,
        lines: int = 0,
    ) -> None:

        with cls._console_lock:

            print("\r\033[K", end="", flush=True)

            for _ in range(lines):

                print("\033[A\033[K", end="", flush=True)

    @classmethod
    def input_key(
        cls,
        prompt: str = "",
        valid: str = "",
        default: str = "",
        timeout: int = 5,
    ) -> str:

        if not prompt:
            prompt = "Choice"

        if not default:

            while True:

                cls.line(
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
                    cls.line()
                    return c

                cls.line(
                    "[!]: Invalid selection.",
                    cls.COLOR_ERROR,
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

                cls.line(
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
                            cls.line()
                            return c

                        cls.line(
                            "[!]: Invalid selection.",
                            cls.COLOR_ERROR,
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

            cls.line("")

            return default

    @classmethod
    def confirm(cls) -> bool:

        choice = cls.input_key(
            prompt="[?]: Continue (Y/N)",
            valid="YN",
            default="Y",
        )

        cls.clear_lines(1)

        return choice == "Y"

    @classmethod
    def poll_key(
        cls,
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

            type(self)._instances.add(self)

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
            
    class Renderer:

        ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

        _lock = Lock()
        _update_event = Event()
        _stop_event = Event()

        _thread: Thread | None = None

        _thread_slots: dict[int, int] = {}
        _slots: list[str] = [""]

        @classmethod
        def _assign_slot(cls) -> int:

            thread_id = get_ident()

            with cls._lock:

                slot = cls._thread_slots.get(thread_id)

                if slot is None:

                    slot = len(cls._slots)

                    cls._thread_slots[thread_id] = slot

                    cls._slots.append("")

                return slot

        @classmethod
        def _start(cls) -> None:

            if cls._thread is not None:
                return

            with cls._lock:

                if cls._thread is not None:
                    return

                cls._thread = Thread(
                    target=cls.render_loop,
                    name="PBD-UI-Renderer",
                    daemon=True,
                )

                thread = cls._thread

            thread.start()

        @classmethod
        def stop(cls) -> None:

            thread = cls._thread

            if thread is None:
                return

            cls._stop_event.set()
            cls._update_event.set()

            thread.join()

            with UI._console_lock:

                lines = len(cls._slots)

                for idx in range(lines):

                    print("\r\033[K", end="", flush=True)

                    if idx < lines - 1:
                        print("\033[B", end="", flush=True)

                if lines > 1:
                    print(
                        f"\033[{lines - 1}A\r",
                        end="",
                        flush=True,
                    )            

            with cls._lock:

                cls._thread = None
                cls._thread_slots.clear()
                cls._slots = [""]
                cls._stop_event.clear()

        # text deve contenere la riga completa già pronta per il rendering.
        #
        # Il Renderer aggiunge esclusivamente l'intestazione dello slot:
        #
        #     [+].{T00}:
        #
        # e il padding finale fino a LINE_WIDTH.
        #
        # Tutta la restante formattazione è responsabilità del chiamante.
        #
        # Esempio:
        #
        # text = (
        #     f"{artwork.title} | "
        #     f"{image.name} | "
        #     f"{ui.COLOR_SUCCESS}"
        #     f"Completed"
        #     f"{ui.COLOR_RESET}"
        # )
        @classmethod
        def write(
            cls,
            text: str,
            *,
            main: bool = False,
            show_thread_name: bool = True
        ) -> None:
            
            slot = 0 if main else cls._assign_slot()

            line_width = get_terminal_size().columns - 1

            thread = current_thread()
            thread_name = thread.name            

            header = (
                "[+].{MAIN}"
                if main
                else f"[+].{{T{slot:02d}}}"
            )

            if show_thread_name and not main:
                header = header[:-1] + f":{thread_name}}}"

            header += ": "

            line = (
                f"{UI.COLOR_DEFAULT}"
                f"{header}"
                f"{text}"
                f"{UI.COLOR_RESET}"
            )

            visible_length = len(
                cls.ANSI_ESCAPE.sub("", line)
            )

            padding = " " * max(
                0,
                line_width - visible_length,
            )

            with cls._lock:

                cls._slots[slot] = (
                    line
                    + padding
                )

            cls._start()
            cls._update_event.set()

        @classmethod
        def clear(
            cls,
            *,
            main: bool = False,
        ) -> None:

            cls.write("", main=main)

        # Entry point del thread renderer.
        @classmethod
        def render_loop(cls) -> None:

            while True:

                cls._update_event.wait()
                cls._update_event.clear()

                if cls._stop_event.is_set():
                    break

                with cls._lock:

                    slots = cls._slots.copy()

                cls._render(slots)

        @classmethod
        def _render(
            cls,
            slots: list[str],
        ) -> None:

            with UI._console_lock:

                panel = "\n".join(slots) + "\n"

                cursor_up = f"\033[{len(slots)}A\r"

                print(
                    panel + cursor_up,
                    end="",
                    flush=True,
                )


# Alias della classe di interfaccia grafica
ui = UI