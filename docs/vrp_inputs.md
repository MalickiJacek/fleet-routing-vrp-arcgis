# Inputs of the Vehicle Routing Problem layer

How the company's rules were translated into the ArcGIS Pro VRP layer (thesis, Sections 3.2 and 3.4). The values are the ones used in the case study. The sample data in `data/sample/` follow the same structure.

## Routes – one row per available vehicle and driver

| VRP field | Value | Meaning |
|---|---|---|
| `StartDepotName` / `EndDepotName` | Depot (or a night stop) | the yard; for trips to England the route can end at a night stop and start there the next day |
| `StartDepotServiceTime` / `EndDepotServiceTime` | 30 / 30 min | preparing and unloading the vehicle |
| `EarliestStartTime` / `LatestStartTime` | 05:00 / 07:00 | flexible start |
| `Capacities` | bags · 240 L bins · weight [kg] | e.g. 100 bags, 15 bins, 3,500 kg for a van; 200 bags, 40 bins, 7,500 kg for a lorry |
| `CostPerUnitTime` | £0.20 / min | driver at £12 / h, the same rate for overtime |
| `CostPerUnitDistance` | £0.80 – £1.50 / mile | depends on the vehicle |
| `OvertimeStartTime` | 540 min | 9 h working day (unpaid breaks included) |
| `MaxTotalTime` | 720 min | at most 12 h |
| `MaxTotalTravelTime` | 480 min | |
| `MaxOrderCount` | 30 | |
| `MaxTotalDistance` | 300 miles | |
| `ArriveDepartDelay` | **4.7 min** | measured in the accuracy assessment (real vs network travel time) |

## Breaks – two per driver

| `Precedence` | `ServiceTime` | Time window | `IsPaid` |
|---|---|---|---|
| 1 | 15 min | 09:30 – 10:30 | no |
| 2 | 45 min | 13:00 – 14:00 | no |

## Depots

| `Name` | Time window |
|---|---|
| Depot | 05:00 – 18:00 |
| NightStop (optional) | 07:00 – 17:00 |

## Orders

| VRP field | Source |
|---|---|
| `Name` | job / order id |
| `ServiceTime` | expected time at the customer [min] |
| `TimeWindowStart` / `TimeWindowEnd` | opening hours of the customer (a second window is possible) |
| `PickupQuantities` | bags · 240 L bins · weight, same order as the vehicle capacities |

Orders for the next working day are those with `DaysCount = 1` in the regular orders layer, plus the one-off orders with that date.

## Results exported to Excel

- **Stops:** for each driver, in sequence: arrival time, service time, departure time, customer and quantity, with the breaks in between.
- **Routes:** number of orders, start and end time, travel time, distance and cost for each vehicle.

In the company the file is sent to drivers the evening before.
