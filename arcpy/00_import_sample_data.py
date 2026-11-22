"""
00_import_sample_data.py  –  ArcGIS Pro / ArcPy

Loads the synthetic CSV files from data/sample into a file geodatabase so that
01_update_order_schedule.py and 02_daily_vrp.py can be tried without company data.

    propy 00_import_sample_data.py --workspace D:\\vrp
creates D:\\vrp\\FleetRouting.gdb with RegularOrders, OneTimeOrders and Depots
(points in British National Grid, EPSG:27700). routes.csv and breaks.csv are read
directly as tables.
"""

import argparse
import datetime as dt
import os

import arcpy

arcpy.env.overwriteOutput = True
SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample")
BNG = arcpy.SpatialReference(27700)


def csv_to_points(csv_path, out_fc, date_fields=()):
    tmp = "memory/xy"
    arcpy.management.XYTableToPoint(csv_path, tmp, "Lon", "Lat", coordinate_system=arcpy.SpatialReference(4326))
    arcpy.management.Project(tmp, out_fc, BNG)
    for name in date_fields:                       # text "YYYY-MM-DD" -> DATE field
        arcpy.management.AddField(out_fc, name + "_d", "DATE")
        with arcpy.da.UpdateCursor(out_fc, [name, name + "_d"]) as cur:
            for text, _ in cur:
                cur.updateRow([text, dt.datetime.fromisoformat(str(text)) if text else None])
        arcpy.management.DeleteField(out_fc, name)
        arcpy.management.AlterField(out_fc, name + "_d", name, name)
    arcpy.AddMessage(f"{out_fc}: {arcpy.management.GetCount(out_fc)[0]} points")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    a = ap.parse_args()
    gdb = os.path.join(a.workspace, "FleetRouting.gdb")
    if not arcpy.Exists(gdb):
        arcpy.management.CreateFileGDB(a.workspace, "FleetRouting.gdb")
    csv_to_points(os.path.join(SAMPLE, "regular_orders.csv"), os.path.join(gdb, "RegularOrders"), ["LastDate"])
    csv_to_points(os.path.join(SAMPLE, "one_time_orders.csv"), os.path.join(gdb, "OneTimeOrders"), ["VisitDate"])
    csv_to_points(os.path.join(SAMPLE, "depots.csv"), os.path.join(gdb, "Depots"))
