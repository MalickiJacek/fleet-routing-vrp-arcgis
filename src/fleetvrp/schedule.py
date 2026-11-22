"""
Scheduling of recurring collection orders ("virtual map" in the thesis).

Every regular order is visited on a fixed weekday every N weeks. From the date of
the last visit we compute the next visit date and the number of working days left
until that visit. The map symbology uses these fields: colour = weekday,
transparency = visit later than one working week ahead.

Pure Python (no arcpy) so it can be tested; arcpy/01_update_order_schedule.py
writes the results into the feature class.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def frequency_weeks(text: str | int | None) -> int | None:
    """
    Visit frequency in weeks from the CRM text field.

    >>> frequency_weeks("weekly"), frequency_weeks("2 weekly"), frequency_weeks("6-weekly")
    (1, 2, 6)
    """
    if text is None:
        return None
    if isinstance(text, int):
        return text
    t = str(text).strip().lower()
    if t in ("weekly", "every week", "1 weekly"):
        return 1
    m = re.match(r"(\d+)", t)
    return int(m.group(1)) if m else None


def next_visit(last_visit: dt.date, weeks: int, today: dt.date | None = None) -> dt.date:
    """
    Next visit date: last visit + N weeks, rolled forward by N weeks until it is
    not in the past (the thesis version added the interval once, so orders with a
    missed visit showed a date in the past).
    """
    if weeks <= 0:
        raise ValueError("frequency must be at least one week")
    nxt = last_visit + dt.timedelta(weeks=weeks)
    if today is not None:
        while nxt < today:
            nxt += dt.timedelta(weeks=weeks)
    return nxt


def is_working_day(day: dt.date, holidays: Iterable[dt.date] = ()) -> bool:
    return day.weekday() < 5 and day not in set(holidays)


def working_days_until(today: dt.date, visit: dt.date, holidays: Iterable[dt.date] = ()) -> int:
    """
    Number of working days from ``today`` (exclusive) to ``visit`` (inclusive).
    1 = the next working day, i.e. the orders to plan this evening.

    >>> working_days_until(dt.date(2023, 7, 7), dt.date(2023, 7, 10))   # Friday -> Monday
    1
    """
    holidays = set(holidays)
    if visit <= today:
        return 0
    n, day = 0, today
    while day < visit:
        day += dt.timedelta(days=1)
        if is_working_day(day, holidays):
            n += 1
    return n


def next_working_day(today: dt.date, holidays: Iterable[dt.date] = ()) -> dt.date:
    day = today + dt.timedelta(days=1)
    while not is_working_day(day, holidays):
        day += dt.timedelta(days=1)
    return day


def transparency(days_count: int | None, horizon: int = 5) -> int:
    """Same rule as the Arcade expression on the map: fade visits beyond one working week."""
    return 80 if days_count is not None and days_count > horizon else 0
