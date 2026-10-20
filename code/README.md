# Dasol network lab - code

Version v0.4, 2026-10-20.
Python 3.10 or newer, no network access needed at run time.

## Three commands

```sh
pip install -r requirements.txt     # numpy 2.2.6, scipy 1.15.3
python run_full.py                  # all 10,000 stores, the reported run
python run_reduced.py               # 1 store in 5, the quick check of the thinning distortion
```

The shipped results were produced on a DGX Spark (Python 3.12.3, aarch64, 16 worker processes): `run_reduced.py` took 100 s and `run_full.py` 886 s.
On a laptop expect roughly 5 to 10 times longer; `WORKERS` in `dcn/config.py` sets the number of processes, and the numbers do not depend on it.
Run the reduced profile before the full one if you want the thinning check (the full run compares itself with `results/reduced/registry.json` when it exists).

Each run writes `results/<profile>/registry.json` (every reported number) and the input and outcome tables of brief §2.5 in `results/<profile>/tables/`.
The profile named by `DEMO_PROFILE` in `dcn/config.py` (`full`) also rebuilds `../demo.html`.

## Checks and the demo

- `python verify.py` checks the shown run independently (route audit, cost identities, LP bounds, determinism, worker pool, departure waves, outcome tables, heuristic against an exact solve, engine parity, the local app) and writes `results/full/verification.json`; the demo checks need `pip install playwright && playwright install chromium` and are skipped without it.
- `python build_demo.py` embeds the registry, the verification record and the road shapes into `../demo.html`.
- `../demo.html` opens offline from disk; its live solve runs a simplified in-browser copy of the routing rules (no 2-opt, calibrated distance model instead of the OSRM cache) and says so on the page.
- `python app.py` serves the same page on `http://localhost:8437` and answers the live solve with `dcn/routing.py` on the cached road distances, the same rules and inputs as the reported run.

## Distances

Road kilometres come from OSRM v6.0.0 (car profile, ferries excluded, MLD) on the Geofabrik `south-korea-latest.osm.pbf` extract of 2026-10-18T20:25:06Z, cached in `data/road_cache.npz`: every store to every site, each store to its 50 nearest stores, and a model calibrated on 3,959 road distances for the rest (`osrm/README.md`).
`osrm/build_shapes.py` stores the road shapes the demo draws (`results/full/shapes.json`, display only).
If the cache is missing the code warns and falls back to an uncalibrated placeholder; the shipped numbers never use it.

## Layout

| File | What it does |
|---|---|
| `dcn/config.py` | Teaching defaults (brief §2.6), the relay and dock assumptions, run profiles |
| `dcn/geo.py` | Cities, the 60 sites (stable ids S01 to S60), today's 12 DCs with lease ends, Korea outline |
| `dcn/distances.py` | Road km: OSRM cache and the calibrated model for uncached pairs |
| `dcn/world.py` | Stores, types, rates, churn, the historical assignment |
| `dcn/demand.py` | Calendar, demand history, Poisson-Gamma with exposure, stratified day sampler |
| `dcn/routing.py` | Lower level: savings + 2-opt under load, stops, km, shift and noon deadline; two-driver relay routes for stores no one-driver route reaches; departure waves under a dock limit |
| `dcn/evaluate.py` | Connection: transportation-LP assignment, newsvendor fleet, E over sampled days |
| `dcn/gp.py` | GP (Matern-5/2 ARD, marginal likelihood) and expected improvement |
| `dcn/search.py` | G0 centre of gravity, G1 p-median + route approximation, pool, budgeted search |
| `dcn/pipeline.py` | Whole run: search, validation, finals, held-out days, reversals, departure-wave and thinning checks, outcome tables, registry |
| `osrm/` | Rebuilds the road cache and the road shapes from a self-hosted OSRM server (not needed to run) |
| `prep/` | One-off inputs (not needed to run): `build_hexes.py` (Kontur population hexagons), `road_connected.py` (drops hexagons without a road to the mainland), `current_network.py` (today's 12 DCs: p-median on road km, every store within one driver-day), `districts.py` (district of every hexagon) |

## Assumptions that are business decisions

Two-driver relay routes for far stores (up to 500 km, on duty until 19:00, noon deadline unchanged), the dock count of the departure-wave check, the 30 min break and unlimited spot trucks are modelling choices the company has to confirm; the demo flags them.

## Sources

Seed 437; Korea outline from Natural Earth via geoBoundaries (public domain); store locations sampled from Kontur Population (South Korea, 2023-11-01, H3 resolution 8, CC BY 4.0); districts from geoBoundaries (KOR ADM2, CC BY 3.0); roads from OpenStreetMap contributors (ODbL) via OSRM.
