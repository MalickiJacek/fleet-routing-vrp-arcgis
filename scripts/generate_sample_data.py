"""
Synthetic input data with the same structure as in the thesis (no company data).

Writes CSV files to data/sample/:
    regular_orders.csv   recurring collections (weekday, every N weeks, last visit)
    one_time_orders.csv  on-call collections with a fixed date
    depots.csv           company yard + one night stop
    routes.csv           available vehicles and drivers
    breaks.csv           two breaks per driver (15 min ~9:30, 45 min ~13:00)
Coordinates are WGS 84 random points around towns of the Scottish Central Belt.
"""

import csv
import datetime as dt
import random
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "sample"
rnd = random.Random(42)

TOWNS = {  # name: (lon, lat, weight)
    "Glasgow": (-4.25, 55.86, 30), "Edinburgh": (-3.19, 55.95, 25), "Paisley": (-4.42, 55.85, 6),
    "East Kilbride": (-4.18, 55.76, 6), "Hamilton": (-4.04, 55.78, 5), "Livingston": (-3.52, 55.90, 6),
    "Falkirk": (-3.78, 56.00, 5), "Stirling": (-3.94, 56.12, 5), "Dunfermline": (-3.46, 56.07, 5),
    "Airdrie": (-3.98, 55.87, 4), "Kilmarnock": (-4.50, 55.61, 3),
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
FREQ = ["weekly"] * 4 + ["2 weekly"] * 4 + ["4 weekly"] * 3 + ["6 weekly", "8 weekly"]
TODAY = dt.date(2023, 7, 7)   # a Friday: plan Monday's routes


def point(town):
    lon, lat, _ = TOWNS[town]
    return round(lon + rnd.gauss(0, 0.035), 5), round(lat + rnd.gauss(0, 0.02), 5)


def window():
    return rnd.choice([("08:00", "17:00"), ("09:00", "17:00"), ("07:00", "16:00"), ("09:00", "12:00")])


def write(name, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    towns, weights = zip(*[(t, v[2]) for t, v in TOWNS.items()])

    regular = []
    for i in range(1, 301):
        town = rnd.choices(towns, weights)[0]
        lon, lat = point(town)
        day = rnd.choice(WEEKDAYS)
        freq = rnd.choice(FREQ)
        weeks = int(freq.split()[0]) if freq != "weekly" else 1
        # last visit: that weekday, 1..weeks weeks before TODAY
        back = (TODAY.weekday() - WEEKDAYS.index(day)) % 7 + 7 * rnd.randint(0, weeks - 1)
        last = TODAY - dt.timedelta(days=back or 7)
        bags = max(1, int(rnd.expovariate(1 / 6)))
        s, e = window()
        regular.append({"OrderID": f"R{i:04d}", "Name": f"Customer {i:04d}", "Town": town,
                        "Lon": lon, "Lat": lat, "ServiceTime": min(60, 5 + 2 * bags),
                        "WindowStart": s, "WindowEnd": e, "ServiceDay": day, "Frequency": freq,
                        "LastDate": last.isoformat(), "Bags": bags, "Bins240": rnd.choice([0] * 8 + [1, 2]),
                        "WeightKg": bags * 9})
    write("regular_orders.csv", regular)

    one_time = []
    for i in range(1, 41):
        town = rnd.choices(towns, weights)[0]
        lon, lat = point(town)
        date = TODAY + dt.timedelta(days=rnd.choice([3, 3, 4, 5, 6, 7]))   # next week
        bags = max(1, int(rnd.expovariate(1 / 10)))
        s, e = window()
        one_time.append({"OrderID": f"T{i:04d}", "Name": f"One-off {i:04d}", "Town": town,
                         "Lon": lon, "Lat": lat, "ServiceTime": min(60, 5 + 2 * bags),
                         "WindowStart": s, "WindowEnd": e, "VisitDate": date.isoformat(),
                         "Bags": bags, "Bins240": 0, "WeightKg": bags * 9})
    write("one_time_orders.csv", one_time)

    write("depots.csv", [
        {"Name": "Depot", "Lon": -3.64, "Lat": 55.9, "WindowStart": "05:00", "WindowEnd": "18:00"},
        {"Name": "NightStop", "Lon": -1.89, "Lat": 52.48, "WindowStart": "07:00", "WindowEnd": "17:00"},
    ])

    vans = [("Van 1", 80, 4, 3000, 0.8), ("Van 2", 100, 18, 3500, 1.0), ("Van 3", 100, 15, 3500, 1.0),
            ("Van 4", 100, 15, 3500, 1.25), ("Lorry 5", 200, 40, 7500, 1.5)]
    routes, breaks = [], []
    for k, (name, bags, bins, kg, per_mile) in enumerate(vans, 1):
        routes.append({"Name": name, "Driver": f"Driver {chr(64 + k)}", "StartDepot": "Depot",
                       "EndDepot": "Depot", "StartServiceMin": 30, "EndServiceMin": 30,
                       "EarliestStart": "05:00", "LatestStart": "07:00",
                       "CapBags": bags, "CapBins240": bins, "CapWeightKg": kg,
                       "CostPerMin": 0.2, "CostPerMile": per_mile, "OvertimeStartMin": 540,
                       "MaxOrders": 30, "MaxTotalMin": 720, "MaxTravelMin": 480,
                       "MaxDistanceMi": 300, "ArriveDepartDelayMin": 4.7})
        breaks += [{"Route": name, "Precedence": 1, "ServiceMin": 15, "WindowStart": "09:30", "WindowEnd": "10:30", "Paid": 0},
                   {"Route": name, "Precedence": 2, "ServiceMin": 45, "WindowStart": "13:00", "WindowEnd": "14:00", "Paid": 0}]
    write("routes.csv", routes)
    write("breaks.csv", breaks)


if __name__ == "__main__":
    main()
