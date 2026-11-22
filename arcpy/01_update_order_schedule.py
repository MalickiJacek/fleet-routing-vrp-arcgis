"""
01_update_order_schedule.py  –  ArcGIS Pro / ArcPy

Daily update of the "virtual map" of recurring collections (thesis, Section 3.3).

For every regular order it fills:
    FrequencyWeeks  number of weeks between visits ("weekly", "2 weekly", ...)
    NextDate        next visit date (last visit + N weeks, rolled forward to today)
    DaysCount       working days until the next visit (1 = next working day)
and for one-time orders only DaysCount (from their fixed VisitDate).

In the thesis this was three Calculate Field expressions that had to be re-run
every morning with today's date typed in. Here it is one script that can run as a
scheduled task; the logic lives in src/fleetvrp/schedule.py and is unit-tested.

The map symbology uses: colour = ServiceDay, transparency = DaysCount > 5
(Arcade expression in symbology_transparency.arcade).

Usage (ArcGIS Pro Python):
    propy 01_update_order_schedule.py --regular D:\\vrp\\Orders.gdb\\RegularOrders ^
          --one-time D:\\vrp\\Orders.gdb\\OneTimeOrders [--today 2023-07-07] [--holidays 2023-08-07]
"""

import argparse
import datetime as dt
import os
import sys

import arcpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from fleetvrp.schedule import frequency_weeks, next_visit, working_days_until  # noqa: E402


def ensure_fields(fc, fields):
    existing = {f.name.lower() for f in arcpy.ListFields(fc)}
    for name, ftype in fields:
        if name.lower() not in existing:
            arcpy.management.AddField(fc, name, ftype)


def as_date(value):
    if value is None:
        return None
    return value.date() if isinstance(value, dt.datetime) else value


def update_regular(fc, today, holidays, frequency_field="Frequency", last_field="LastDate"):
    ensure_fields(fc, [("FrequencyWeeks", "SHORT"), ("NextDate", "DATE"), ("DaysCount", "LONG")])
    n = 0
    with arcpy.da.UpdateCursor(fc, [frequency_field, last_field, "FrequencyWeeks", "NextDate", "DaysCount"]) as cur:
        for freq, last, _, _, _ in cur:
            weeks, last = frequency_weeks(freq), as_date(last)
            if not weeks or last is None:
                cur.updateRow([freq, last, weeks, None, None])
                continue
            nxt = next_visit(last, weeks, today)
            cur.updateRow([freq, last, weeks, dt.datetime.combine(nxt, dt.time(12)),
                           working_days_until(today, nxt, holidays)])
            n += 1
    arcpy.AddMessage(f"{fc}: {n} regular orders scheduled")


def update_one_time(fc, today, holidays, date_field="VisitDate"):
    ensure_fields(fc, [("DaysCount", "LONG")])
    with arcpy.da.UpdateCursor(fc, [date_field, "DaysCount"]) as cur:
        for date, _ in cur:
            d = as_date(date)
            cur.updateRow([date, None if d is None else working_days_until(today, d, holidays)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Update NextDate / DaysCount of collection orders")
    ap.add_argument("--regular", required=True, help="feature class of recurring orders")
    ap.add_argument("--one-time", help="feature class of one-time orders")
    ap.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument("--holidays", nargs="*", type=dt.date.fromisoformat, default=[],
                    help="non-working days, e.g. bank holidays")
    a = ap.parse_args()
    update_regular(a.regular, a.today, a.holidays)
    if a.one_time:
        update_one_time(a.one_time, a.today, a.holidays)
