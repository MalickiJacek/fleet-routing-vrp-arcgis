# ArcGIS Pro scripts

| Script | Thesis section | What it does |
|---|---|---|
| `00_import_sample_data.py` | – | loads the synthetic CSV files into `FleetRouting.gdb` (points in British National Grid) |
| `01_update_order_schedule.py` | 3.3 Virtual map | fills `FrequencyWeeks`, `NextDate` and `DaysCount` for recurring orders and `DaysCount` for one-off orders |
| `02_daily_vrp.py` | 3.4 Daily routing | Python version of the *DailyRoutingTool* model: selects the next day's orders, solves the VRP and writes the Excel file for drivers |
| `symbology_transparency.arcade` | 3.3 | transparency rule for the order layers |

## Requirements

- ArcGIS Pro 3.x with **Network Analyst** (`arcpy.nax`)
- a network data source:
  - `https://www.arcgis.com/`: ArcGIS Online routing service; uses credits (about 4–5 a day in the thesis);
  - or a local network dataset, e.g. built from OS Open Roads.
- `01_update_order_schedule.py` imports `../src/fleetvrp/schedule.py`, so keep the repository structure.

## Try it on the synthetic data

From the *Python Command Prompt* of ArcGIS Pro, in the repository folder:

```bat
propy arcpy\00_import_sample_data.py --workspace C:\temp\vrp

propy arcpy\01_update_order_schedule.py --regular C:\temp\vrp\FleetRouting.gdb\RegularOrders ^
      --one-time C:\temp\vrp\FleetRouting.gdb\OneTimeOrders --today 2023-07-07

propy arcpy\02_daily_vrp.py --network https://www.arcgis.com/ --travel-mode "Driving Time" ^
      --orders C:\temp\vrp\FleetRouting.gdb\RegularOrders C:\temp\vrp\FleetRouting.gdb\OneTimeOrders ^
      --depots C:\temp\vrp\FleetRouting.gdb\Depots ^
      --routes data\sample\routes.csv --breaks data\sample\breaks.csv ^
      --date 2023-07-10 --out C:\temp\vrp\ROUTES_2023-07-10.xlsx
```

On Friday 7 July 2023 the sample has about 50 orders for Monday (34 recurring + 16 one-off) and 5 vehicles.

## Status

- The ModelBuilder models (diagrams in [`../model/`](../model/)) were used in the thesis with real data.
- The ArcPy scripts were written in 2026 from those models and **have not been run against every ArcGIS Pro version yet**. Field names of `arcpy.nax` outputs (`Stops`, `Routes`) can differ between versions; the script reads only the fields that exist.
- The scheduling logic is tested with `pytest`, which needs no ArcGIS licence.
