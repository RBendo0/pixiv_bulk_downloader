import random
import time

# UI

MENU_TIMEOUT = 5
RATE_LIMIT_WAIT = 5

# Pixiv API

PIXIV_API_DELAY_MIN = 0.5
PIXIV_API_DELAY_MAX = 1.5


# Time delay randomizer

def random_api_delay(
    base: float = PIXIV_API_DELAY_MIN, 
    delta: float = (PIXIV_API_DELAY_MAX - PIXIV_API_DELAY_MIN)
) -> None:
    time.sleep(base + delta * random.random())
