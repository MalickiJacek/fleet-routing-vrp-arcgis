"""Figures for the README (thesis results + synthetic virtual map)."""

import datetime as dt
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fleetvrp.analysis import accuracy, savings  # noqa: E402
from fleetvrp.schedule import frequency_weeks, next_visit, working_days_until  # noqa: E402

IMG = ROOT / "docs" / "img"
IMG.mkdir(parents=True, exist_ok=True)
GREY, BLUE, ORANGE = "#bfc3c7", "#2f74b5", "#e08a2e"


def fig_accuracy():
    seg = pd.read_csv(ROOT / "data/thesis/accuracy_segments.csv")
    a = accuracy(seg)
    diff = seg.real_min - seg.algorithm_min
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    lim = 60
    ax1.scatter(seg.algorithm_min, seg.real_min, s=14, color=BLUE, alpha=.7)
    ax1.plot([0, lim], [0, lim], color="k", lw=.8, label="real = algorithm")
    ax1.plot([0, lim], [a.mean_delay_min, lim + a.mean_delay_min], color=ORANGE, lw=1.2, ls="--",
             label=f"algorithm + {a.mean_delay_min:.1f} min")
    ax1.set(xlim=(0, lim), ylim=(0, lim), xlabel="Algorithm travel time [min]",
            ylabel="Real travel time (driver forms) [min]", title="Drive between two stops")
    ax1.legend(frameon=False, fontsize=9)
    ax2.hist(diff.clip(-20, 40), bins=30, color=BLUE)
    ax2.axvline(a.mean_delay_min, color=ORANGE, ls="--", label=f"mean {a.mean_delay_min:.1f} min")
    ax2.set(xlabel="Real − algorithm [min] (clipped to −20…40)", ylabel="Segments",
            title=f"{a.segments} segments, 20 routes")
    ax2.legend(frameon=False, fontsize=9)
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "accuracy_assessment.png", dpi=150)
    print("accuracy", a)


def fig_savings():
    s = savings(pd.read_csv(ROOT / "data/thesis/manual_vs_algorithm_20_days.csv"))
    fig, ax = plt.subplots(figsize=(10, 3.8))
    x = range(len(s))
    ax.bar([i - .2 for i in x], s.manual_gbp, .4, color=GREY, label="Manual planning")
    ax.bar([i + .2 for i in x], s.algorithm_gbp, .4, color=BLUE, label="VRP in ArcGIS Pro")
    for i, p in zip(x, s.saved_pct_calc):
        ax.text(i + .2, s.algorithm_gbp.iloc[i] + 25, f"−{p:.0f}%", ha="center", fontsize=7)
    ax.set_xticks(list(x), [pd.Timestamp(d).strftime("%d.%m.%y") for d in s.date], rotation=60, fontsize=8)
    ax.set_ylabel("Cost of driving [£]\n(0.20 £/min + 1.25 £/mile)")
    total = 100 * s.saved_gbp_calc.sum() / s.manual_gbp.sum()
    ax.set_title(f"20 working days, {s.orders.sum():,} collections: −£{s.saved_gbp_calc.sum():,.0f} ({total:.1f}%)")
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "savings_20_days.png", dpi=150)


def fig_virtual_map():
    today = dt.date(2023, 7, 7)
    r = pd.read_csv(ROOT / "data/sample/regular_orders.csv")
    r["next"] = [next_visit(dt.date.fromisoformat(d), frequency_weeks(f), today) for d, f in zip(r.LastDate, r.Frequency)]
    r["days"] = [working_days_until(today, n) for n in r.next]
    colors = {"Monday": "#1b9e77", "Tuesday": "#d95f02", "Wednesday": "#7570b3",
              "Thursday": "#e7298a", "Friday": "#66a61e"}
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for day, c in colors.items():
        sub = r[r.ServiceDay == day]
        near, far = sub[sub.days.between(1, 5)], sub[(sub.days > 5) | (sub.days == 0)]
        ax.scatter(far.Lon, far.Lat, s=18, color=c, alpha=.2, edgecolor="none")
        ax.scatter(near.Lon, near.Lat, s=34, color=c, edgecolor="k", lw=.4, label=day)
        for _, o in near.iterrows():
            ax.annotate(str(o.days), (o.Lon, o.Lat), xytext=(3, 3), textcoords="offset points", fontsize=6)
    ax.scatter([-3.64], [55.9], marker="s", s=70, color="k", label="Depot")
    ax.set_title("Virtual map of recurring collections (synthetic data, planning on Fri 7 Jul 2023)\n"
                 "colour = weekday, label = working days until the visit, faded = later than next week",
                 fontsize=10)
    ax.set(xlabel="Longitude", ylabel="Latitude")
    ax.legend(frameon=False, fontsize=8, loc="lower right", ncol=2)
    ax.set_aspect(1 / 0.56)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(IMG / "virtual_map_synthetic.png", dpi=150)


if __name__ == "__main__":
    fig_accuracy()
    fig_savings()
    fig_virtual_map()
