from pathlib import Path

import pandas as pd
import pytest

from fleetvrp.analysis import accuracy, annual_estimate, savings

DATA = Path(__file__).resolve().parents[1] / "data" / "thesis"


def test_accuracy_reproduces_thesis_delay():
    a = accuracy(pd.read_csv(DATA / "accuracy_segments.csv"))
    assert a.segments == 135
    assert a.mean_delay_min == pytest.approx(4.7, abs=0.05)
    assert a.share_slower > 0.85


def test_savings_reproduce_thesis_table():
    days = pd.read_csv(DATA / "manual_vs_algorithm_20_days.csv")
    s = savings(days)
    # recomputed savings match the reported ones (rounding of the inputs only)
    assert (s.saved_gbp_calc - s.saved_gbp).abs().max() < 0.2
    assert s.orders.sum() == 1079
    assert 100 * s.saved_gbp_calc.sum() / s.manual_gbp.sum() == pytest.approx(5.4, abs=0.05)


def test_annual_estimate_matches_thesis():
    est = annual_estimate(pd.read_csv(DATA / "manual_vs_algorithm_20_days.csv"))
    assert est["planner_gbp"] == 7800
    assert est["net_gbp"] == pytest.approx(18_500, rel=0.02)
