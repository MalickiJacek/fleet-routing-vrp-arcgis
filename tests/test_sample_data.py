import datetime as dt
from pathlib import Path

import pandas as pd

from fleetvrp.schedule import frequency_weeks, next_visit, working_days_until

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_sample_orders_for_next_working_day():
    today = dt.date(2023, 7, 7)
    r = pd.read_csv(SAMPLE / "regular_orders.csv")
    nxt = [next_visit(dt.date.fromisoformat(d), frequency_weeks(f), today) for d, f in zip(r.LastDate, r.Frequency)]
    # every visit falls on the agreed service day
    assert all(n.strftime("%A") == day for n, day in zip(nxt, r.ServiceDay))
    monday = sum(working_days_until(today, n) == 1 for n in nxt)
    assert 20 <= monday <= 60
    routes = pd.read_csv(SAMPLE / "routes.csv")
    assert set(pd.read_csv(SAMPLE / "breaks.csv").Route) == set(routes.Name)
