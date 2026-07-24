import ctypes
import msvcrt
import re
import time
import weakref
import winsound
from ctypes import wintypes
from dataclasses import dataclass, replace
from shutil import get_terminal_size
from threading import (
    Event,
    Lock,
    Thread,
    current_thread,
    get_ident,
)

import pwinput
from wcwidth import wcswidth

from .pbd_types import ToggleOption


class UI:

    # ------------------
    # Colori disponibili
    # ------------------
    
    COLOR_DEFAULT = "\033[37m"    # bianco
    COLOR_SUCCESS = "\033[32m"    # verde
    COLOR_WARNING = "\033[33m"    # giallo
    COLOR_ERROR = "\033[31m"      # rosso

    COLOR_INFO = "\033[90m"       # grigio scuro
    COLOR_INPUT = "\033[36m"      # ciano

    COLOR_RESET = "\033[0m"       # nero

    # --------------
    # Tasti speciali
    # --------------

    KEY_ENTER = "\r"
    KEY_ESCAPE = "\x1b"
    KEY_SPACE = " "

    _console_lock = Lock()

    @classmethod
    def _key_name(
        cls,
        key: str,
    ) -> str:

        match key:

            case cls.KEY_ENTER:
                return "ENTER"

            case cls.KEY_ESCAPE:
                return "ESC"

            case cls.KEY_SPACE:
                return "SPACE"

            case _:
                return key


    @classmethod
    def refresh(cls) -> None:

        with cls._console_lock:

            print(
                "\033[2J\033[H",
                end="",
                flush=True,
            )

    @classmethod
    def _apply_inline_markup(
        cls,
        text: str,
        *,
        old_style: str,
        new_style: str,
    ) -> str:    

        return (
            text
            .replace("@@.", old_style)
            .replace("@@", new_style)
        )

    @classmethod
    def line(
        cls,
        text: str = "",
        color: str = COLOR_DEFAULT,
        *,
        tag_color: str = COLOR_INFO,
        home: bool = True,
        clear: bool = True,
        history: bool = True,
    ) -> None:

        with cls._console_lock:

            text = cls._apply_inline_markup(
                text,
                old_style=color,
                new_style=tag_color,
            )

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
    def toggle_menu(
        cls,
        options: list[ToggleOption],
        *,
        header: str = "",
        footer: str = "",
    ) -> list[ToggleOption]:

        current_options = [
            replace(option)
            for option in options
        ]

        initial_states = [
            option.enabled
            for option in current_options
        ]

        parts: list[str] = ["\n"]
        check_positions: list[int] = []
        buffer_length = 1

        if header:
            header_block = f"{header}\n\n"
            parts.append(header_block)
            buffer_length += len(header_block)

        for option in current_options:

            option_prefix = (
                f"{option.key}. "
                f"[{cls.COLOR_SUCCESS}"
            )

            parts.append(option_prefix)
            buffer_length += len(option_prefix)

            # Indice del carattere compreso fra il colore verde
            # e il ripristino del colore predefinito.
            check_positions.append(buffer_length)

            option_suffix = (
                f" {cls.COLOR_DEFAULT}] "
                f"{option.label}\n"
            )

            parts.append(option_suffix)
            buffer_length += len(option_suffix)

        parts.append("\n")
        buffer_length += 1

        if footer:
            footer_block = f"{footer}\n\n"
            parts.append(footer_block)
            buffer_length += len(footer_block)

        commands = (
            "[SPAZIO] Ripristina"
            " - "
            "[INVIO] Conferma"
        )

        parts.append(commands)

        menu_buffer = list("".join(parts))

        for index, option in enumerate(current_options):
            menu_buffer[check_positions[index]] = (
                "✓" if option.enabled else " "
            )

        # Il numero di righe da risalire coincide con il numero
        # di avanzamenti di riga presenti nel blocco.
        rows_up = menu_buffer.count("\n")

        valid_keys = (
            "".join(
                option.key
                for option in current_options
            )
            + " \r"
        )

        print(
            "".join(menu_buffer),
            end="",
            flush=True,
        )

        while True:

            key = cls.poll_key(valid=valid_keys)

            if not key:
                time.sleep(0.05)
                continue

            if key == "\r":
                
                print(
                    "\r\033[K"
                    + "\033[A\r\033[K" * rows_up,
                    end="",
                    flush=True,
                )
                
                return current_options

            if key == " ":

                for index, option in enumerate(current_options):

                    option.enabled = initial_states[index]

                    menu_buffer[check_positions[index]] = (
                        "✓" if option.enabled else " "
                    )

            else:

                for index, option in enumerate(current_options):

                    if option.key != key:
                        continue

                    option.enabled = not option.enabled

                    menu_buffer[check_positions[index]] = (
                        "✓" if option.enabled else " "
                    )

                    break

            # Il cursore si trova sulla riga dei comandi.
            # Torna alla posizione precedente alla prima riga vuota
            # e ristampa l'intero buffer aggiornato.
            print(
                f"\r\033[{rows_up}A"
                f"{''.join(menu_buffer)}",
                end="",
                flush=True,
            )

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
                    "Invalid selection.",
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
                    prompt + f" (Default [{cls._key_name(default)}] tra {remaining}s): ",
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
    def input_string(
        cls,
        prompt: str = "",
        default: str = "",
    ) -> str:

        if not prompt:
            prompt = "Input"

        if default:

            class CHAR_UNION(ctypes.Union):

                _fields_ = [
                    ("UnicodeChar", wintypes.WCHAR),
                    ("AsciiChar", wintypes.CHAR),
                ]

            class KEY_EVENT_RECORD(ctypes.Structure):

                _anonymous_ = ("char",)

                _fields_ = [
                    ("bKeyDown", wintypes.BOOL),
                    ("wRepeatCount", wintypes.WORD),
                    ("wVirtualKeyCode", wintypes.WORD),
                    ("wVirtualScanCode", wintypes.WORD),
                    ("char", CHAR_UNION),
                    ("dwControlKeyState", wintypes.DWORD),
                ]

            class EVENT_UNION(ctypes.Union):

                _fields_ = [
                    ("KeyEvent", KEY_EVENT_RECORD),
                ]

            class INPUT_RECORD(ctypes.Structure):

                _anonymous_ = ("event",)

                _fields_ = [
                    ("EventType", wintypes.WORD),
                    ("event", EVENT_UNION),
                ]

            kernel32 = ctypes.WinDLL(
                "kernel32",
                use_last_error=True,
            )

            kernel32.GetStdHandle.argtypes = [
                wintypes.DWORD,
            ]

            kernel32.GetStdHandle.restype = (
                wintypes.HANDLE
            )

            kernel32.WriteConsoleInputW.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(INPUT_RECORD),
                wintypes.DWORD,
                ctypes.POINTER(wintypes.DWORD),
            ]

            kernel32.WriteConsoleInputW.restype = (
                wintypes.BOOL
            )

            STD_INPUT_HANDLE = -10
            KEY_EVENT = 0x0001

            console_input = kernel32.GetStdHandle(
                STD_INPUT_HANDLE,
            )

            records = (
                INPUT_RECORD * len(default)
            )()

            for idx, char in enumerate(default):

                records[idx].EventType = KEY_EVENT

                records[idx].KeyEvent = KEY_EVENT_RECORD(
                    bKeyDown=True,
                    wRepeatCount=1,
                    wVirtualKeyCode=0,
                    wVirtualScanCode=0,
                    UnicodeChar=char,
                    dwControlKeyState=0,
                )

            written = wintypes.DWORD()

            success = kernel32.WriteConsoleInputW(
                console_input,
                records,
                len(records),
                ctypes.byref(written),
            )

            if not success:

                error_code = ctypes.get_last_error()

                raise OSError(
                    error_code,
                    "Failed to initialize console input.",
                )

        with cls._console_lock:

            value = input(
                f"\r\033[K"
                f"{cls.COLOR_DEFAULT}"
                f"{prompt}: "
                f"{cls.COLOR_INPUT}"
            )

        print(cls.COLOR_RESET, end="")

        return value

    @classmethod
    def confirm(
        cls,
        prompt: str = "Continue",
        *,
        valid: str = KEY_ENTER + KEY_ESCAPE,
        default: str = KEY_ENTER,
    ) -> bool:

        choice = cls.input_key(
            prompt=f"[?]: {prompt} (@@ENTER@@.=Confirm / @@ESC@@.=Cancel):",
            valid=valid,
            default=default,
        )

        cls.clear_lines(1)

        return choice == default

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
        def _terminal_width(cls) -> int:

            return max(
                1,
                get_terminal_size().columns - 5,
            )

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
                cls._update_event.clear()

        @classmethod
        def _build_line(
            cls,
            text: str,
            *,
            main: bool = False,
            show_thread_name: bool = True,
        ) -> str:

            slot = 0 if main else cls._assign_slot()

            header = (
                "[+].{MAIN}"
                if main
                else f"[+].{{T{slot:02d}}}"
            )

            if show_thread_name and not main:
                header = (
                    header[:-1]
                    + f":{current_thread().name}}}"
                )

            return (
                f"{UI.COLOR_DEFAULT}"
                f"{header}: "
                f"{text}"
                f"{UI.COLOR_RESET}"
            )
        
        @classmethod
        def _display_width(
            cls,
            text: str,
        ) -> int:

            plain_text = cls.ANSI_ESCAPE.sub("", text)

            return wcswidth(plain_text)        

        # ATTENZIONE: Per risolvere correttamente il nome del thread nella
        # intestazione dello slot tutti i metodi dichiarati in_thread_<...>
        # devono necessariamente essere invocati all'interno di un thread in
        # esecuzione
        @classmethod
        def in_thread_overflow_width(
            cls,
            text: str,
            *,
            main: bool = False,
            show_thread_name: bool = True,
        ) -> int:

            line = cls._build_line(
                text,
                main=main,
                show_thread_name=show_thread_name,
            )

            return max(
                0,
                cls._display_width(line)
                - cls._terminal_width(),
            )

        @classmethod
        def truncate_width(
            cls,
            text: str,
            remove_width: int,
        ) -> str:

            if remove_width <= 0:
                return text

            target_width = cls._display_width(text) - remove_width

            if target_width <= 0:
                return ""

            ellipsis = "…"
            content_width = target_width - wcswidth(ellipsis)

            result = []
            visible_text = ""
            truncated = False
            index = 0

            while index < len(text):

                ansi_match = cls.ANSI_ESCAPE.match(
                    text,
                    index,
                )

                if ansi_match:

                    result.append(
                        ansi_match.group()
                    )

                    index = ansi_match.end()
                    continue

                char = text[index]
                index += 1

                if truncated:
                    continue

                candidate = visible_text + char
                candidate_width = wcswidth(candidate)

                if candidate_width < 0:
                    continue

                if candidate_width > content_width:

                    result.append(ellipsis)
                    truncated = True
                    continue

                result.append(char)
                visible_text = candidate

            return "".join(result)

        # text deve contenere la riga completa già pronta per il rendering.
        # Il Renderer aggiunge esclusivamente l'intestazione dello slot:
        #
        #     [+].{T<nn>:<nome_thread>}:
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
        # ATTENZIONE: Per risolvere correttamente il nome del thread nella
        # intestazione dello slot tutti i metodi dichiarati in_thread_<...>
        # devono necessariamente essere invocati all'interno di un thread in
        # esecuzione
        @classmethod
        def in_thread_write(
            cls,
            text: str,
            *,
            main: bool = False,
            show_thread_name: bool = True
        ) -> None:
            
            slot = 0 if main else cls._assign_slot()

            line = cls._build_line(text, main=main, show_thread_name=show_thread_name)

            overflow = max(
                0,
                cls._display_width(line)
                - cls._terminal_width(),
            )

            if overflow:

                line = cls.truncate_width(
                    line,
                    overflow,
                )

            with cls._lock:

                cls._slots[slot] = (
                    line
                    + "\033[K"
                )

            cls._start()
            cls._update_event.set()

        # ATTENZIONE: Per risolvere correttamente il nome del thread nella
        # intestazione dello slot tutti i metodi dichiarati in_thread_<...>
        # devono necessariamente essere invocati all'interno di un thread in
        # esecuzione
        @classmethod
        def in_thread_clear(
            cls,
            *,
            main: bool = False,
        ) -> None:

            cls.in_thread_write("", main=main)

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