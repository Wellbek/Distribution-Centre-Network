# Dasol network lab - code

Version v1.0, 2026-10-27.
Python 3.10 or newer, no network access needed at run time.

## Three commands

```sh
pip install -r requirements.txt     # numpy 2.2.6, scipy 1.15.3
python run_full.py                  # all 10,000 stores, the reported run
python run_reduced.py               # 1 store in 5: the same search and evaluation, the thinning check
```

The shipped results were produced on a DGX Spark (Python 3.12.3, aarch64, 16 worker processes): `run_full.py` took 1,127 s and `run_reduced.py` 74 s, the extensions included in the full run.
`run_reduced.py` takes about 7 minutes with 2 worker processes on an 8-core laptop (6 min 48 s on two pinned cores) and less with one process per core; the full run takes roughly 5 to 10 times longer on a laptop than on the Spark.
The number of processes is one per core up to 16; set `DCN_WORKERS=2` (for example `DCN_WORKERS=2 python run_reduced.py`) on a machine with little memory.
The numbers do not depend on it.
Every sort that can meet ties is stable, so the numbers do not depend on the processor either: run 5's reduced run, repeated from the hand-in ZIP in a fresh Python 3.10 environment on x86_64 with the network cut off (`unshare -rn`, 2 workers, 17 min), reproduced the registry produced on the Spark (aarch64, Python 3.12): of 54,642 numbers, only 27 expected-improvement values differ by more than 1e-9 (at most 0.07%), and every choice the search makes is the same.
Run the reduced profile before the full one if you want the thinning check (the full run compares itself with `results/reduced/registry.json` when it exists).

Each run writes `results/<profile>/registry.json` and the input tables of brief §2.5 in `results/<profile>/tables/`.
The full run also writes the outcome tables (`deliveries`, `vehicle_days`, `spot_hires`), the departure-wave check and the reversals, and after the pipeline computes the extensions (`dcn/extensions.py`: closure sequence along the lease expiries, robustness to demand shifts and the distance source, value of information, today's network rebuilt for other years of its last redesign, and a CbAS-style candidate generator) and stores them in the same registry.
The profile named by `DEMO_PROFILE` in `dcn/config.py` (`full`) also rebuilds `../demo.html` and `../proposal.html`.

## Checks and the demo

- `python verify.py` checks the shown run independently (route audit, cost identities, LP bounds, determinism, worker pool, departure waves, outcome tables, heuristic against an exact solve, engine parity, the local app) and writes `results/full/verification.json`; the demo checks need `pip install playwright && playwright install chromium` and are skipped without it.
- `python build_demo.py` embeds the registry, the verification record and the road shapes into `../demo.html`, and the registry into `../proposal.html`.
- `python checks/routing_gap.py [baseline|recommended] [days] [sec_per_store] [dcs]` measures the routing heuristic against PyVRP 0.11.3 (optional: `pip install pyvrp==0.11.3`); its cached results are in `results/checks/`, and `python checks/routing_summary.py` (no PyVRP needed) summarises them per network; `build_demo.py` embeds that summary in both pages.
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
| `dcn/search.py` | G0 centre of gravity, G1 load-based route approximation, G2 with the clock, pool, budgeted search |
| `dcn/pipeline.py` | Whole run: search, validation, finals, held-out days, reversals, departure-wave and thinning checks, outcome tables, registry |
| `dcn/extensions.py` | Closure sequence along the lease expiries, robustness, value of information, design-year drift sweep, candidate generation (CbAS) |
| `checks/routing_gap.py` | Optional accuracy check of the routing heuristic against PyVRP |
| `checks/routing_summary.py` | Per-network summary of the cached PyVRP comparison and its effect on the saving |
| `osrm/` | Rebuilds the road cache and the road shapes from a self-hosted OSRM server (not needed to run) |
| `prep/` | One-off inputs (not needed to run): `build_hexes.py` (Kontur population hexagons), `road_connected.py` (drops hexagons without a road to the mainland), `current_network.py` (today's 12 DCs: the 2016 design, a p-median on straight-line km over the stores open in 2016, every store within one driver-day), `districts.py` (district of every hexagon) |

## Assumptions that are business decisions

Two-driver relay routes for far stores (up to 500 km, on duty until 19:00, noon deadline unchanged), the dock count of the departure-wave check, the 30 min break and unlimited spot trucks are modelling choices the company has to confirm; the demo flags them.
The full register is in the demo's Data tab, proposal slide 6 and the problem definition, Section 3.

## Scope

In the model: every store served every day with every stop before noon, the vehicle limits (48 cages, 25 stops, 250 km, the shift), 500-1,400 stores per new DC, road distances, sampled and held-out demand days, and today's network priced exactly like every redesign.
Left out, because the brief does not detail them; flagged for the business to confirm (proposal slide 7): several trips per vehicle and day, loading-dock congestion, returns and empty cages, the fresh-food second wave (out of scope in the brief unless brought in), Jeju and island stores, and one-off moving costs.
Next, with real data: speeds by time of day (the first simplification to remove), real dock counts, a stronger router inside the evaluation, and store sales next to orders.

## Sources

Seed 437; Korea outline from Natural Earth via geoBoundaries (public domain); store locations sampled from Kontur Population (South Korea, 2023-11-01, H3 resolution 8, CC BY 4.0); districts from geoBoundaries (KOR ADM2, CC BY 3.0); roads from OpenStreetMap contributors (ODbL) via OSRM.
