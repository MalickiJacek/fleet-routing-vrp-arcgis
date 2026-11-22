"""Accuracy assessment and savings estimate from the thesis (Sections 3.5 and 3.6)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

COST_PER_MINUTE_GBP = 0.20     # driver: 12 GBP / hour
COST_PER_MILE_GBP = 1.25       # vehicle running cost used in the thesis


@dataclass
class Accuracy:
    segments: int
    mean_delay_min: float        # real - algorithm, used as ArriveDepartDelay
    median_delay_min: float
    share_slower: float          # share of segments where reality was slower


def accuracy(segments: pd.DataFrame) -> Accuracy:
    """``segments``: columns real_min, algorithm_min (one row per drive between two stops)."""
    diff = segments["real_min"] - segments["algorithm_min"]
    return Accuracy(len(diff), float(diff.mean()), float(diff.median()), float((diff > 0).mean()))


def route_cost(travel_min, distance_mi, per_min=COST_PER_MINUTE_GBP, per_mile=COST_PER_MILE_GBP):
    return travel_min * per_min + distance_mi * per_mile


def savings(days: pd.DataFrame, per_min=COST_PER_MINUTE_GBP, per_mile=COST_PER_MILE_GBP) -> pd.DataFrame:
    """Cost of manual vs algorithm routes per day (columns as in data/thesis/manual_vs_algorithm_20_days.csv)."""
    out = days.copy()
    out["manual_gbp"] = route_cost(out.manual_travel_min, out.manual_distance_mi, per_min, per_mile)
    out["algorithm_gbp"] = route_cost(out.algorithm_travel_min, out.algorithm_distance_mi, per_min, per_mile)
    out["saved_gbp_calc"] = out.manual_gbp - out.algorithm_gbp
    out["saved_pct_calc"] = 100 * out.saved_gbp_calc / out.manual_gbp
    return out


def annual_estimate(days: pd.DataFrame, working_days_per_year=260, planner_hours_saved_per_day=2.5,
                    planner_rate_gbp=12.0, licence_gbp=2050.0, extra_credits_gbp=180.0) -> dict:
    """Annual savings as estimated in the thesis (driving + planner time - ArcGIS licence)."""
    s = savings(days)
    driving = s.saved_gbp_calc.sum() / len(s) * working_days_per_year
    planner = planner_hours_saved_per_day * planner_rate_gbp * working_days_per_year
    return {"driving_gbp": driving, "planner_gbp": planner,
            "costs_gbp": licence_gbp + extra_credits_gbp,
            "net_gbp": driving + planner - licence_gbp - extra_credits_gbp}
