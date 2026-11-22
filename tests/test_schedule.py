import datetime as dt

import pytest

from fleetvrp.schedule import frequency_weeks, next_visit, next_working_day, transparency, working_days_until

FRI, MON = dt.date(2023, 7, 7), dt.date(2023, 7, 10)


@pytest.mark.parametrize("text,weeks", [("weekly", 1), ("2 weekly", 2), ("6-weekly", 6), (4, 4), ("", None), (None, None)])
def test_frequency_weeks(text, weeks):
    assert frequency_weeks(text) == weeks


def test_next_visit_adds_interval():
    assert next_visit(dt.date(2023, 7, 3), 2) == dt.date(2023, 7, 17)


def test_next_visit_rolls_forward_past_missed_visits():
    # last visit long ago: the next visit must not be in the past and stays on the same weekday
    nxt = next_visit(dt.date(2023, 5, 1), 2, today=FRI)
    assert nxt >= FRI and nxt.weekday() == 0 and (nxt - dt.date(2023, 5, 1)).days % 14 == 0


def test_working_days_skip_weekend_and_holidays():
    assert working_days_until(FRI, MON) == 1
    assert working_days_until(FRI, dt.date(2023, 7, 14)) == 5
    assert working_days_until(FRI, dt.date(2023, 7, 11), holidays=[MON]) == 1
    assert working_days_until(FRI, FRI) == 0


def test_next_working_day():
    assert next_working_day(FRI) == MON
    assert next_working_day(FRI, holidays=[MON]) == dt.date(2023, 7, 11)


def test_transparency_rule_matches_arcade():
    assert [transparency(d) for d in (None, 1, 5, 6)] == [0, 0, 0, 80]
