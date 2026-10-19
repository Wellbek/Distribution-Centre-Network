# Dasol network lab - code

Version v0.2, 2026-10-19.
Python 3.10+, no network access needed at run time.

## Three commands

```sh
pip install -r requirements.txt     # numpy 2.2.6, scipy 1.15.3 (tested on Python 3.10.19)
python run_full.py                  # all 10,000 stores; run on a large machine
python run_reduced.py               # 1 store in 5, about 17 minutes on one laptop core (includes whole-pool validation)
```

Each run writes `results/<profile>/registry.json` (every reported number), the input tables in `results/<profile>/tables/`, and rebuilds `../demo.html`.

## Demo

- `../demo.html` opens offline from disk; the live lower-level solve then runs a simplified in-browser copy of the savings rules (no 2-opt).
- `python app.py` serves the same page on `http://localhost:8437` and answers the live solve with the Python engine (`dcn/routing.py`).

## Layout

| File | What it does |
|---|---|
| `dcn/config.py` | Teaching defaults (brief §2.6) and run profiles |
| `dcn/geo.py` | Cities, current DCs, candidate sites, land mask, map distance |
| `dcn/distances.py` | Road km: OSRM cache (`data/road_cache.npz`) and the calibrated model for uncached pairs |
| `osrm/` | Rebuilds the road cache from a self-hosted OSRM server (not needed to run) |
| `prep/` | One-off inputs (not needed to run): `build_hexes.py` (Kontur population hexagons), `road_connected.py` (drops hexagons without a road to the mainland), `current_network.py` (the 12 current DCs by capacitated p-median) |
| `dcn/world.py` | Stores, types, rates, churn, historical assignment |
| `dcn/demand.py` | Calendar, demand history, Poisson-Gamma with exposure, day sampler |
| `dcn/routing.py` | Lower level: savings + 2-opt with load, stops, km, shift and noon deadline |
| `dcn/evaluate.py` | Connection: transportation-LP assignment, newsvendor fleet, E over sampled days |
| `dcn/gp.py` | GP (Matern-5/2 ARD, marginal likelihood) and expected improvement |
| `dcn/search.py` | G0 centre of gravity, G1 p-median + route approximation, pool, budgeted search |
| `dcn/pipeline.py` | Whole run and the results registry |

## Known gaps of this version

Until `data/road_cache.npz` exists (see `osrm/README.md`) distances fall back to map distance x 1.30 (x 1.45 in Gangwon and North Gyeongsang); the reduced run thins stores without aggregating stops; outcome tables, the G remedy, reversal sweeps and the balance-table checks are not in yet.
Seed 437; Korea outline from Natural Earth via geoBoundaries (public domain); store locations sampled from Kontur Population (South Korea, 2023-11-01, H3 resolution 8, CC BY 4.0); roads from OpenStreetMap contributors (ODbL) via OSRM.
