"""
02_daily_vrp.py  –  ArcGIS Pro / ArcPy (Network Analyst)

Daily route planning for a collection fleet (thesis, Section 3.4).
Python version of the ModelBuilder model "DailyRoutingTool":

  model (ArcGIS tools)                              this script
  ------------------------------------------------  -----------------------------------------
  Select: RegularOrders where DaysCount = 1         same selection (01_update_order_schedule.py
  Select: OneTimeOrders where NextDate = <date>     fills DaysCount for both layers)
  Make Vehicle Routing Problem Analysis Layer       arcpy.nax.VehicleRoutingProblem
  Add Locations: Routes, Breaks, Depots, Orders     insertCursor for each input class
  Solve                                             solve()
  Select Data + Table To Excel                      one Excel file: stops per driver + route summary

Input field names follow the thesis tables (see docs/vrp_inputs.md):
  orders  : OrderID, Name, ServiceTime [min], WindowStart, WindowEnd (text "HH:MM"),
            Bags, Bins240, WeightKg, DaysCount
  depots  : Name, WindowStart, WindowEnd
  routes  : Name, Driver, StartDepot, EndDepot, StartServiceMin, EndServiceMin, EarliestStart,
            LatestStart, CapBags, CapBins240, CapWeightKg, CostPerMin, CostPerMile,
            OvertimeStartMin, MaxOrders, MaxTotalMin, MaxTravelMin, MaxDistanceMi,
            ArriveDepartDelayMin
  breaks  : Route, Precedence, ServiceMin, WindowStart, WindowEnd, Paid
ArriveDepartDelayMin = 4.7 min came from the accuracy assessment (Section 3.5).

Usage (ArcGIS Pro Python):
    propy 02_daily_vrp.py --network https://www.arcgis.com/ --travel-mode "Driving Time" ^
        --orders D:\\vrp\\Orders.gdb\\RegularOrders D:\\vrp\\Orders.gdb\\OneTimeOrders ^
        --depots D:\\vrp\\Orders.gdb\\Depots --routes D:\\vrp\\routes.csv --breaks D:\\vrp\\breaks.csv ^
        --date 2023-07-10 --out D:\\vrp\\ROUTES_2023-07-10.xlsx
--network can also be a local network dataset (e.g. built from OS Open Roads).
An ArcGIS Online network data source consumes credits (thesis: 4-5 credits per day).
"""

import argparse
import datetime as dt

import arcpy
import pandas as pd

arcpy.env.overwriteOutput = True
NAX = arcpy.nax


def at(date, hhmm):
    """'07:30' on the planned date -> datetime (Network Analyst needs full dates)."""
    if hhmm in (None, ""):
        return None
    if isinstance(hhmm, dt.datetime):
        return dt.datetime.combine(date, hhmm.time())
    h, m = (int(x) for x in str(hhmm).split(":")[:2])
    return dt.datetime.combine(date, dt.time(h, m))


def rows(table, fields, where=None):
    with arcpy.da.SearchCursor(table, fields, where) as cur:
        for r in cur:
            yield dict(zip(fields, r))


def load_orders(vrp, layers, date, where="DaysCount = 1"):
    fields = ["OrderID", "Name", "ServiceTime", "WindowStart", "WindowEnd", "Bags", "Bins240", "WeightKg", "SHAPE@"]
    out = ["Name", "Description", "ServiceTime", "TimeWindowStart", "TimeWindowEnd", "PickupQuantities", "SHAPE@"]
    n = 0
    with vrp.insertCursor(NAX.VehicleRoutingProblemInputDataType.Orders, out) as cur:
        for layer in layers:
            for r in rows(layer, fields, where):
                cur.insertRow([str(r["OrderID"]), r["Name"], r["ServiceTime"] or 10,
                               at(date, r["WindowStart"]), at(date, r["WindowEnd"]),
                               f'{r["Bags"] or 0} {r["Bins240"] or 0} {r["WeightKg"] or 0}', r["SHAPE@"]])
                n += 1
    return n


def load_depots(vrp, depots, date):
    with vrp.insertCursor(NAX.VehicleRoutingProblemInputDataType.Depots,
                          ["Name", "TimeWindowStart", "TimeWindowEnd", "SHAPE@"]) as cur:
        for r in rows(depots, ["Name", "WindowStart", "WindowEnd", "SHAPE@"]):
            cur.insertRow([r["Name"], at(date, r["WindowStart"]), at(date, r["WindowEnd"]), r["SHAPE@"]])


def load_routes(vrp, routes, date, available=None):
    f = ["Name", "Driver", "StartDepot", "EndDepot", "StartServiceMin", "EndServiceMin", "EarliestStart",
         "LatestStart", "CapBags", "CapBins240", "CapWeightKg", "CostPerMin", "CostPerMile",
         "OvertimeStartMin", "MaxOrders", "MaxTotalMin", "MaxTravelMin", "MaxDistanceMi", "ArriveDepartDelayMin"]
    out = ["Name", "Description", "StartDepotName", "EndDepotName", "StartDepotServiceTime",
           "EndDepotServiceTime", "EarliestStartTime", "LatestStartTime", "Capacities", "CostPerUnitTime",
           "CostPerUnitDistance", "OvertimeStartTime", "CostPerUnitOvertime", "MaxOrderCount",
           "MaxTotalTime", "MaxTotalTravelTime", "MaxTotalDistance", "ArriveDepartDelay"]
    drivers = {}
    with vrp.insertCursor(NAX.VehicleRoutingProblemInputDataType.Routes, out) as cur:
        for r in rows(routes, f):
            if available and r["Name"] not in available:
                continue
            drivers[r["Name"]] = r["Driver"]
            cur.insertRow([r["Name"], r["Driver"], r["StartDepot"], r["EndDepot"], r["StartServiceMin"],
                           r["EndServiceMin"], at(date, r["EarliestStart"]), at(date, r["LatestStart"]),
                           f'{r["CapBags"]} {r["CapBins240"]} {r["CapWeightKg"]}', r["CostPerMin"],
                           r["CostPerMile"], r["OvertimeStartMin"], r["CostPerMin"], r["MaxOrders"],
                           r["MaxTotalMin"], r["MaxTravelMin"], r["MaxDistanceMi"], r["ArriveDepartDelayMin"]])
    return drivers


def load_breaks(vrp, breaks, date, drivers):
    out = ["RouteName", "Precedence", "ServiceTime", "TimeWindowStart", "TimeWindowEnd", "IsPaid"]
    with vrp.insertCursor(NAX.VehicleRoutingProblemInputDataType.Breaks, out) as cur:
        for r in rows(breaks, ["Route", "Precedence", "ServiceMin", "WindowStart", "WindowEnd", "Paid"]):
            if r["Route"] in drivers:
                cur.insertRow([r["Route"], r["Precedence"], r["ServiceMin"], at(date, r["WindowStart"]),
                               at(date, r["WindowEnd"]), bool(r["Paid"])])


def table(result, out_type, wanted):
    fields = [f for f in wanted if f in result.fieldNames(out_type)]
    return pd.DataFrame(list(result.searchCursor(out_type, fields)), columns=fields)


def plan(network, orders, depots, routes, breaks, date, out_xlsx, travel_mode=None, available=None,
         where="DaysCount = 1"):
    arcpy.CheckOutExtension("Network")
    vrp = NAX.VehicleRoutingProblem(network)
    if travel_mode:
        vrp.travelMode = travel_mode
    vrp.timeUnits = NAX.TimeUnits.Minutes
    vrp.distanceUnits = NAX.DistanceUnits.Miles
    vrp.timeZoneForTimeFields = NAX.TimeZoneUsage.LocalTimeAtLocations
    vrp.routeShapeType = NAX.RouteShapeType.TrueShape
    vrp.timeWindowFactor = NAX.TimeWindowImportance.Medium
    vrp.excessTransitFactor = NAX.ExcessTransitTimeImportance.Medium
    vrp.spatiallyClusterRoutes = True

    load_depots(vrp, depots, date)
    drivers = load_routes(vrp, routes, date, available)
    load_breaks(vrp, breaks, date, drivers)
    n_orders = load_orders(vrp, orders, date, where)
    arcpy.AddMessage(f"{date}: {n_orders} orders, {len(drivers)} vehicles")

    result = vrp.solve()
    for _, msg in result.solverMessages(NAX.MessageSeverity.Warning):
        arcpy.AddWarning(msg)
    if not result.solveSucceeded:
        raise RuntimeError("\n".join(m[-1] for m in result.solverMessages(NAX.MessageSeverity.All)))

    out = NAX.VehicleRoutingProblemOutputDataType
    stops = table(result, out.Stops, ["RouteName", "Sequence", "StopType", "Name", "ArriveTime",
                                      "ServiceTime", "DepartTime", "PickupQuantities"])
    stops = stops[stops["RouteName"].notna()].sort_values(["RouteName", "Sequence"])
    stops.insert(1, "Driver", stops["RouteName"].map(drivers))
    summary = table(result, out.Routes, ["Name", "OrderCount", "StartTime", "EndTime", "TotalTime",
                                         "TotalTravelTime", "TotalDistance", "TotalCost"])
    summary.insert(1, "Driver", summary["Name"].map(drivers))

    with pd.ExcelWriter(out_xlsx) as xl:
        stops.to_excel(xl, sheet_name="Stops", index=False)
        summary.to_excel(xl, sheet_name="Routes", index=False)
    result.export(out.Routes, arcpy.env.scratchGDB + f"/Routes_{date:%Y%m%d}")
    unassigned = n_orders - int(summary["OrderCount"].sum()) if "OrderCount" in summary else None
    arcpy.AddMessage(f"Saved {out_xlsx}; unassigned orders: {unassigned}")
    return stops, summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Daily VRP for a collection fleet")
    ap.add_argument("--network", required=True, help="network dataset or https://www.arcgis.com/")
    ap.add_argument("--travel-mode")
    ap.add_argument("--orders", nargs="+", required=True, help="order layers (regular, one-time)")
    ap.add_argument("--depots", required=True)
    ap.add_argument("--routes", required=True)
    ap.add_argument("--breaks", required=True)
    ap.add_argument("--date", type=dt.date.fromisoformat, required=True, help="planned day")
    ap.add_argument("--vehicles", nargs="*", help="only these routes/vehicles are available")
    ap.add_argument("--where", default="DaysCount = 1")
    ap.add_argument("--out", required=True, help="output .xlsx")
    a = ap.parse_args()
    plan(a.network, a.orders, a.depots, a.routes, a.breaks, a.date, a.out, a.travel_mode, a.vehicles, a.where)
