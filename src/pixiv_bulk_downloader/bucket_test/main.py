from pathlib import Path
from collections import Counter
import math

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


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

    buckets = Counter()

    for illust_id in ids:

        bucket = int(
            illust_id / 15600
        )

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

    print("=== GENERALE ===")
    print(f"Works           : {len(ids)}")
    print(f"Used buckets    : {len(buckets)}")
    print(f"Avg works/bucket: {len(ids)/len(buckets):.2f}")
    print(f"Max bucket size : {max(sizes)}")

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
            f"P{p:<2} : {percentile(p)}"
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

    min_id = ids[0]
    max_id = ids[-1]

    n = len(ids)

    x_real = []
    y_real = []
    
    for i, illust_id in enumerate(ids):

        xnorm = i / (n - 1)

        ynorm = (
            illust_id - min_id
        ) / (
            max_id - min_id
        )

        x_real.append(xnorm)
        y_real.append(ynorm)
    
    fig, ax = plt.subplots(figsize=(14, 8))

    plt.subplots_adjust(
        left=0.10,
        bottom=0.20
    )

    ax.plot(
        x_real,
        y_real,
        label="Reale",
        linewidth=2
    )

    KE0 = 1.0
    K00 = 10.0
    K10 = 0.2
    K20 = 0
    K30 = 0

    def build_curve(ke, k0, k1, k2, k3):

        y = []

        for x in x_real:

            #f = k3 * math.log(1 + k1 * (x ** ke)) / math.log(1 + k2)+k0
            #f = k1 * math.atan(k0 * x ** ke + k2) + k3
            #f = math.atan(k0 * x ** ke) / math.atan(k0) # migliore
            #f = math.atan(k0 * x ** (k0/10)) / math.atan(k0)
            #z = 1.438244795 * x
            #f = 404538286 * math.cos(z)**2 / (math.tan(z)**(1/3))
            z = max(1e-9, 1.438244795 * x)
            f = math.cos(z)**2 / (math.tan(z)**(1/3))

            y.append(f)

        return y

    y_model = build_curve(
        KE0,
        K00,
        K10,
        K20,
        K30
    )

    (line_model,) = ax.plot(
        x_real,
        y_model,
        label="Modello",
        linewidth=2
    )

    ax.grid(True)
    ax.legend()

    ax_ke = plt.axes(
        [0.15, 0.20, 0.70, 0.03]
    )
    
    ax_k0 = plt.axes(
        [0.15, 0.15, 0.70, 0.03]
    )
    
    ax_k1 = plt.axes(
        [0.15, 0.10, 0.70, 0.03]
    )

    ax_k2 = plt.axes(
        [0.15, 0.05, 0.70, 0.03]
    )

    ax_k3 = plt.axes(
        [0.15, 0.00, 0.70, 0.03]
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
        label="K1",
        valmin=0,
        valmax=10.0,
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

        line_model.set_ydata(
            y_model
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

if __name__ == "__main__":
    graph()