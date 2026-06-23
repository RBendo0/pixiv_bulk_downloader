import msvcrt


def abort_requested() -> bool:

    if not msvcrt.kbhit():
        return False

    key = msvcrt.getch().decode(errors="ignore")

    return key == "Q"
