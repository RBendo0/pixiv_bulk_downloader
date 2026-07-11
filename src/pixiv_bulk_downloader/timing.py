import random
import time

# UI

MENU_TIMEOUT = 10        # = 10
RATE_LIMIT_WAIT = 60     # = 60

# Pixiv API

API_DELAY_HIGH = (0.5, 1.5)
API_DELAY_MEDIUM = (0.2, 0.8)
API_DELAY_LOW = (0.05, 0.2)
API_DELAY_TURBO = (0.0, 0.02)


# Time delay randomizer

def random_api_delay(
    t_min: float = API_DELAY_HIGH[0], 
    t_max: float = API_DELAY_HIGH[1],
) -> None:
    
    time.sleep(
        random.uniform(
            t_min, 
            t_max,
        )
    )
    