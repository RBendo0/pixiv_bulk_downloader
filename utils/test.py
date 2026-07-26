import json
import math
import random
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pwinput
from matplotlib.widgets import Slider
from rich.console import Console

from .pbd_path import PixivPath
from .ui import ui
from .utils import abort_requested


# Scarica tutti gli ID
def runtest4(aapi):

    ids_file = Path("bookmarks_public_ids.txt")
    state_file = Path("bookmarks_public_state.json")

    target_id = aapi.user_id

    # Ripresa da stato precedente
    if state_file.exists():

        state = json.loads(
            state_file.read_text(
                encoding="utf-8"
            )
        )

        next_qs = state["next_qs"]

        print(
            f"[i]: Resume from saved state "
            f"({state['ids_collected']} IDs)"
        )

        res_json = aapi.user_bookmarks_illust(
            **next_qs
        )

        ids_count = state["ids_collected"]

    else:

        res_json = aapi.user_bookmarks_illust(
            target_id,
            restrict="public",
        )

        ids_count = 0

    while True:

        for illust in res_json["illusts"]:

            with open(
                ids_file,
                "a",
                encoding="utf-8",
            ) as f:

                f.write(
                    f"{illust.id}\n"
                )

            ids_count += 1

            time.sleep(
                0.05 + 0.15 * random.random()
            )

        print(
            f"\033[K[+]: IDs collected: "
            f"{ids_count}",
            end="\r",
            flush=True,
        )

        if abort_requested():
            break

        next_qs = aapi.parse_qs(
            res_json["next_url"]
        )

        if next_qs is None:

            if state_file.exists():
                state_file.unlink()

            break

        state_file.write_text(
            json.dumps(
                {
                    "next_qs": next_qs,
                    "ids_collected": ids_count,
                },
                indent=4,
            ),
            encoding="utf-8",
        )

        res_json = aapi.user_bookmarks_illust(
            **next_qs
        )

        time.sleep(
            0.05 + 0.15 * random.random()
        )

    print(
        f"\n[+]: Saved {ids_count} IDs."
    )


def runtest3(aapi):
    user_id = aapi.user_id

    public = aapi.user_bookmarks_illust(
        user_id=user_id,
        restrict="public",
    )

    private = aapi.user_bookmarks_illust(
        user_id=user_id,
        restrict="private",
    )

    print(f"Public total : {public.total}")
    print(f"Private total: {private.total}")

    print(f"Public page items : {len(public.illusts)}")
    print(f"Private page items: {len(private.illusts)}") 

    print("Public IDs:")
    for illust in public.illusts[:5]:
        print(illust.id)

    print("Private IDs:")
    for illust in private.illusts[:5]:
        print(illust.id)  

    detail = aapi.user_detail(aapi.user_id)

    for key, value in detail["profile"].items():
        print(f"{key}: {value}")     


def runtest2(aapi) -> None:
    
    for name in dir(aapi):
        print(name)


# Rutine di test: eseguire qui tutte le porcate
def runtest1(aapi) -> None:

    test_dir = Path("test")
    test_dir.mkdir(exist_ok=True)

    found = {
        "illust": False,
        "manga": False,
        "ugoira": False,
    }

    res_json = aapi.user_bookmarks_illust(aapi.user_id)
    next_json = res_json

    while next_json is not None:

        res_json = next_json

        next_qs = aapi.parse_qs(res_json["next_url"])

        if next_qs is None:
            next_json = None
        else:
            next_json = aapi.user_bookmarks_illust(**next_qs)

        for illust in res_json["illusts"]:

            work_type = illust.type

            if work_type not in found:
                continue

            if found[work_type]:
                continue

            # Dump bookmark
            dump_file = test_dir / f"{work_type}_dump.json"

            with open(dump_file, "w", encoding="utf-8") as f:
                json.dump(
                    illust,
                    f,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            print(f"[+]: Salvato {dump_file}")

            # Dump illust_detail
            detail_file = test_dir / f"{work_type}_detail.json"

            detail = aapi.illust_detail(illust.id)

            with open(detail_file, "w", encoding="utf-8") as f:
                json.dump(
                    detail,
                    f,
                    indent=4,
                    ensure_ascii=False,
                    default=str,
                )

            print(f"[+]: Salvato {detail_file}")

            # Dump ugoira_metadata
            if work_type == "ugoira":

                metadata_file = test_dir / "ugoira_metadata.json"

                metadata = aapi.ugoira_metadata(illust.id)

                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(
                        metadata,
                        f,
                        indent=4,
                        ensure_ascii=False,
                        default=str,
                    )

                print(f"[+]: Salvato {metadata_file}")

            found[work_type] = True

        if all(found.values()):
            break

    print("[+]: Test completato") 


def idminmax() -> None:

    ids = [
        int(line)
        for line in Path(
            "bookmarks_public_ids.txt"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    print()
    print(f"Works : {len(ids)}")
    print(f"IDmin : {min(ids)}")
    print(f"IDmax : {max(ids)}")


def pathtest() -> None:
    bookmarks = PixivPath("D:/TEST")

    print(type(bookmarks))
    print(bookmarks)


def bucks() -> None:

    ids = sorted(
        int(line)
        for line in Path(
            "bookmarks_public_ids.txt"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    )

    GROUP_SIZE = 500

    SPLIT_FRAC = 0.25

    DENSITY_STABLE = 550

    nworks = len(ids)

    split_index = int(SPLIT_FRAC * nworks)

    print()
    print("=== INTORNO A ID_SPLIT ===")

    for i in range(
        split_index - 50,
        split_index + 51
    ):

        if i == split_index:
            print()
            print("========== ID_SPLIT ==========")
            print()

        print(f"{i:5d} : {ids[i]}")

        if i == split_index:
            print()
            print("========== ID_SPLIT ==========")
            print()

    print()

    ID_MIN = ids[0]

    ID_SPLIT = ids[split_index]

    ID_MAX = ids[-1]

    hype_works = split_index

    stable_works = (
        nworks - hype_works
    )

    DENSITY_HYPE_A = 0.16223786 * ID_MAX 
    DENSITY_HYPE_B = 1.09912234 * ID_MAX
    DENSITY_HYPE_SCALE = 3.0

    for id_test in (
            ids[0],
            ids[1000],
            ids[3000],
            ids[6000],
            ID_SPLIT,
        ):
        
        dhype = DENSITY_HYPE_SCALE * DENSITY_HYPE_A / (
            nworks * math.exp((id_test - DENSITY_HYPE_B) / DENSITY_HYPE_A)
        )            

        print(
            f"{id_test} -> {dhype:.1f}"
        )

    print()

    print("=== PARAMETRI ===")

    print(f"Works          : {nworks}")

    print(f"ID_MIN         : {ID_MIN}")

    print(f"ID_SPLIT       : {ID_SPLIT}")

    print(f"ID_MAX         : {ID_MAX}")

    print()

    print(f"Hype works     : {hype_works}")

    print(f"Stable works   : {stable_works}")

    print()

    print(
        f"DENSITY_HYPE   : "
        f"{DENSITY_HYPE_A:.1f}"
    )

    print(
        f"DENSITY_STABLE : "
        f"{DENSITY_STABLE:.1f}"
    )

    print()
    """
    hype_bucket_count = int(
        hype_works /
        GROUP_SIZE
    )
    """
    buckets = Counter()

    for illust_id in ids:

        if illust_id < ID_SPLIT:

            dhype = DENSITY_HYPE_SCALE * (
                DENSITY_HYPE_A
                /
                (
                    nworks
                    * math.exp(
                        (illust_id - DENSITY_HYPE_B)
                        / DENSITY_HYPE_A
                    )
                )
            )

            # bucket = int((illust_id - ID_MIN) / (GROUP_SIZE * dhype)
            bucket = int(illust_id / (GROUP_SIZE * dhype)
                
            )

        else:

            # bucket = (hype_bucket_count + int((illust_id - ID_SPLIT) / (GROUP_SIZE * DENSITY_STABLE)))
            bucket = int(illust_id / (GROUP_SIZE * DENSITY_STABLE))

        buckets[bucket] += 1

    sizes = sorted(
        buckets.values()
    )

    n = len(sizes)

    def percentile(p):

        i = int(
            (n - 1) * p / 100
        )

        return sizes[i]

    print()

    print("=== BUCKETS ===")

    print(
        f"Used buckets    : "
        f"{len(buckets)}"
    )

    print(
        f"Avg works/bucket: "
        f"{len(ids) / len(buckets):.2f}"
    )

    print(
        f"Max bucket size : "
        f"{max(sizes)}"
    )

    print()

    print("=== PERCENTILI ===")

    for p in (
        10,
        25,
        50,
        75,
        90,
        95,
        99,
    ):
        print(
            f"P{p:<2} : "
            f"{percentile(p)}"
        )

    print()
    print("=== PRIMI 20 BUCKET ===")

    for i in range(20):

        if i in buckets:

            print(
                f"{i:2d} : "
                f"{buckets[i]}"
            )

    largest_bucket = None
    largest_size = 0

    for bucket, size in buckets.items():

        if size > largest_size:

            largest_bucket = bucket
            largest_size = size

    print()

    print(
        f"Largest bucket : "
        f"{largest_bucket}"
    )

    print(
        f"Largest size   : "
        f"{largest_size}"
    )

    def percentiles(values, p):

        idx = int(
            p / 100 * (len(values) - 1)
        )

        return values[idx]

    first_stable_bucket = math.ceil(
        hype_works / GROUP_SIZE
    )

    print()
    print("=== HYPE ONLY ===")

    hype_sizes = []

    for bucket, size in buckets.items():

        if bucket < first_stable_bucket:

            hype_sizes.append(size)

    hype_sizes.sort()

    print(
        f"Hype buckets        : "
        f"{len(hype_sizes)}"
    )

    print(
        f"Hype P25            : "
        f"{percentiles(hype_sizes, 25)}"
    )

    print(
        f"Hype P50            : "
        f"{percentiles(hype_sizes, 50)}"
    )

    print(
        f"Hype P75            : "
        f"{percentiles(hype_sizes, 75)}"
    )

    print(
        f"Hype P90            : "
        f"{percentiles(hype_sizes, 90)}"
    )

    print(
        f"Hype max size       : "
        f"{max(hype_sizes)}"
    )

    print()
    print("=== STABLE ONLY ===")

    stable_sizes = []

    stable_max_bucket = None
    stable_max_size = 0

    for bucket, size in buckets.items():

        if bucket >= first_stable_bucket:

            stable_sizes.append(size)

            if size > stable_max_size:

                stable_max_size = size
                stable_max_bucket = bucket

    stable_sizes.sort()

    stable_bucket_count = len(
        stable_sizes
    )

    print(
        f"First stable bucket : "
        f"{first_stable_bucket}"
    )

    print(
        f"Stable buckets      : "
        f"{stable_bucket_count}"
    )

    print(
        f"Stable P25          : "
        f"{percentiles(stable_sizes, 25)}"
    )

    print(
        f"Stable P50          : "
        f"{percentiles(stable_sizes, 50)}"
    )

    print(
        f"Stable P75          : "
        f"{percentiles(stable_sizes, 75)}"
    )

    print(
        f"Stable P80          : "
        f"{percentiles(stable_sizes, 80)}"
    )

    print(
        f"Stable P85          : "
        f"{percentiles(stable_sizes, 85)}"
    )

    print(
        f"Stable P90          : "
        f"{percentiles(stable_sizes, 90)}"
    )

    print(
        f"Stable P95          : "
        f"{percentiles(stable_sizes, 95)}"
    )

    print(
        f"Stable max bucket   : "
        f"{stable_max_bucket}"
    )

    print(
        f"Stable max size     : "
        f"{stable_max_size}"
    )


def graph() -> None:

    ids = sorted(
        int(line)
        for line in Path(
            "bookmarks_public_ids.txt"
        ).read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    )

    max_id = ids[-1]

    n = len(ids)

    x_real = []
    y_real = []

    print(f"N     = {n}")
    print(f"IDmax = {max_id}")

    for i, illust_id in enumerate(ids):

        xnorm = (i + 1) / n

        ynorm = illust_id / max_id

        x_real.append(xnorm)
        y_real.append(ynorm)
    
    x_delta = []
    y_delta = []

    WINDOW = 100

    for i in range(WINDOW, n):

        delta = (
            ids[i] -
            ids[i - WINDOW]
        ) / WINDOW

        x = (i + 1) / n

        x_delta.append(x)
        y_delta.append(delta)

    print(
        f"Delta min : {min(y_delta):.1f}"
    )

    print(
        f"Delta max : {max(y_delta):.1f}"
    )

    print(
        f"Delta avg : "
        f"{sum(y_delta) / len(y_delta):.1f}"
    )

    tail20 = y_delta[
        int(0.2 * len(y_delta)):
    ]

    print(
        f"Delta tail avg (20%) : "
        f"{sum(tail20) / len(tail20):.1f}"
    )

    tail50 = y_delta[
        int(0.5 * len(y_delta)):
    ]

    print(
        f"Delta tail avg (50%) : "
        f"{sum(tail50) / len(tail50):.1f}"
    )

    tail80 = y_delta[
        int(0.8 * len(y_delta)):
    ]

    print(
        f"Delta tail avg (80%) : "
        f"{sum(tail80) / len(tail80):.1f}"
    )

    def linear_fit(start_frac):

        start = int(start_frac * n)

        x_fit = x_real[start:]
        y_fit = y_real[start:]

        m, q = np.polyfit(
            x_fit,
            y_fit,
            1
        )

        density = (m * max_id) / n

        return m, q, density

    def linear_fit_hype(split_frac=0.20):

        end = int(split_frac * n)

        x_fit = x_real[:end]
        y_fit = y_real[:end]

        m, q = np.polyfit(
            x_fit,
            y_fit,
            1
        )

        density = (m * max_id) / n

        return m, q, density
    
    def quadratic_fit_hype(
        split_frac=0.20
    ):

        end = int(split_frac * n)

        x_fit = x_real[:end]
        y_fit = y_real[:end]

        a, b, c = np.polyfit(
            x_fit,
            y_fit,
            2
        )

        a, b = np.polyfit(
            np.log(x_fit),
            y_fit,
            1
        )

        return a, b, c

    fig, ax = plt.subplots(figsize=(14, 8))

    plt.subplots_adjust(
        left=0.10,
        bottom=0.20
    )

    ax.scatter(
        x_real,
        y_real,
        s=2,
        label="Reale"
    )

    KE0 = 1.0
    K00 = 10.0
    K10 = 0.2
    K20 = 0
    K30 = 0
    """
    def build_curve(ke, k0, k1, k2, k3):

        y = []

        for x in x_real:

            #f = k3 * math.log(1 + k1 * (x ** ke)) / math.log(1 + k2)+k0
            #f = k1 * math.atan(k0 * x ** ke + k2) + k3
            #f = math.atan(k0 * x ** ke) / math.atan(k0) # migliore
            #f = math.atan(k0 * x ** (k0/10)) / math.atan(k0)
            #z = 1.438244795 * x
            #f = 404538286 * math.cos(z)**2 / (math.tan(z)**(1/3))
            #z = max(1e-9, 1.438244795 * x)
            #f = math.cos(z)**2 / (math.tan(z)**(1/3))
            f = m * x + q
            y.append(f)

        return y
    """
    def build_curve(
        ke,
        k0,
        start_frac,
        k2,
        k3
    ):

        m, q, density = linear_fit(start_frac)

        return [
            m * x + q
            for x in x_real
        ]

    y_model = build_curve(
        KE0,
        K00,
        K10,
        K20,
        K30
    )

    split_frac = 0.25
    
    m_hype, q_hype, density_hype = (
       linear_fit_hype(split_frac)
    )

    print(
        f"HYPE density = "
        f"{density_hype:.1f}"
    )

    a_hype, b_hype, c_hype = (
        quadratic_fit_hype(split_frac)
    )

    print()
    print(f"a_hype = {a_hype:.8f}")
    print(f"b_hype = {b_hype:.8f}")
    print(f"c_hype = {c_hype:.8f}")
    print()

    x_hype = [
        x
        for x in x_real
        if x <= split_frac
    ]

    y_hype = [
#        a_hype * x**2
#        + b_hype * x
#        + c_hype
        a_hype * np.log(x) + b_hype
        for x in x_hype
    ]

    line_model, = ax.plot(
        x_real,
        y_model,
        label="Regressione lineare",
        linewidth=2
    )

    line_hype, = ax.plot(
        x_hype,
        y_hype,
        "--",
        linewidth=2,
        label="Regressione HYPE"
    )

    ax2 = ax.twinx()

    line_delta, = ax2.plot(
        x_delta,
        y_delta,
        label="Delta ID",
        alpha=0.6
    )

    ax.grid(True)
    ax.legend()

    m, q, density = linear_fit(K10)

    density_text = ax.text(
        0.02,
        0.92,
        (
            f"Stable={density:.1f}\n"
            f"Hype={density_hype:.1f}"
        ),
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
    )

    ax_ke = plt.axes(
        (0.15, 0.20, 0.70, 0.03)
    )
    
    ax_k0 = plt.axes(
        (0.15, 0.15, 0.70, 0.03)
    )
    
    ax_k1 = plt.axes(
        (0.15, 0.10, 0.70, 0.03)
    )

    ax_k2 = plt.axes(
        (0.15, 0.05, 0.70, 0.03)
    )

    ax_k3 = plt.axes(
        (0.15, 0.00, 0.70, 0.03)
    )

    slider_ke = Slider(
        ax=ax_ke,
        label="KE",
        valmin=0.1,
        valmax=2.0,
        valinit=KE0
    )

    slider_k0 = Slider(
        ax=ax_k0,
        label="K0",
        valmin=0,
        valmax=100,
        valinit=K00
    )

    slider_k1 = Slider(
        ax=ax_k1,
        label="START",
        valmin=0,
        valmax=0.95,
        valinit=K10
    )

    slider_k2 = Slider(
        ax=ax_k2,
        label="K2",
        valmin=-10,
        valmax=10,
        valinit=K20
    )

    slider_k3 = Slider(
        ax=ax_k3,
        label="K3",
        valmin=-10,
        valmax=10,
        valinit=K30
    )

    def update(val):

        ke = slider_ke.val
        k0 = slider_k0.val
        k1 = slider_k1.val
        k2 = slider_k2.val
        k3 = slider_k3.val

        y_model = build_curve(
            ke,
            k0,
            k1,
            k2,
            k3
        )

        m, q, density = linear_fit(k1)

        density_text.set_text(
            f"Stable={density:.1f}\n"
            f"Hype={density_hype:.1f}"
        )

        line_model.set_ydata(
            y_model
        )

        line_delta.set_ydata(
            y_delta
        )

        fig.canvas.draw_idle()

    slider_ke.on_changed(
        update
    )

    slider_k0.on_changed(
        update
    )

    slider_k1.on_changed(
        update
    )

    slider_k2.on_changed(
        update
    )

    slider_k3.on_changed(
        update
    )

    plt.show()


def runtest5(aapi):

    target_id = aapi.user_id

    counter = 0

    while True:

        try:

            res_json = aapi.user_bookmarks_illust(
                target_id,
                restrict="public",
            )

            if "illusts" not in res_json:

                with open(
                    "pixiv_stress_test_response.json",
                    "w",
                    encoding="utf-8",
                ) as f:

                    json.dump(
                        res_json,
                        f,
                        indent=4,
                        ensure_ascii=False,
                        default=str,
                    )

                raise KeyError("illusts")

            # forza la lettura del contenuto
            _ = res_json["illusts"][0].id

            counter += 1

            print(f"\rCalls: {counter}", end="", flush=True)

        except Exception as e:

            trace = traceback.format_exc()

            with open(
                "pixiv_stress_test.log",
                "a",
                encoding="utf-8",
            ) as f:

                f.write(
                    f"{datetime.now()}\n"
                    f"Calls: {counter}\n"
                    f"Exception: {type(e).__name__}\n"
                    f"Message: {e}\n"
                    f"\n"
                    f"{trace}\n"
                    f"{'-' * 60}\n"
                )

            print(
                f"\n[!]: {type(e).__name__}: {e}"
            )

            break


def runtest6():

    c = Console()

    for i in range(10):

        c.print(
            f"Counter: {i}",
            end="\r",
        )

        time.sleep(1)

    print("\nFine")


def runtest7():

    c = pwinput.getch()

    print(f"\nDEBUG: {repr(c)}")


def runtest8():

    print("\n=== TEST 1 - Input normale ===\n")

    result = ui.input_key(
        prompt="Scelta:",
        valid="ABC",
    )

    print(f"Risultato: {result}")

    print("\n=== TEST 2 - Timeout ===\n")

    result = ui.input_key(
        prompt="Scelta:",
        valid="ABC",
        default="B",
        timeout=10,
    )

    print(f"Risultato: {result}")