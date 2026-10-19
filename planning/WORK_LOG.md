# Work log

Append-only, dated record of what was done by hand (commands run, machines used, problems hit, results), kept as the raw material for the executive summary and Section 7 of the definition.
`LLM_USE.md` records what the LLM did and `DECISIONS.md` why; this file records what happened.

## 2026-10-19 (day 0)

### Decisions taken

- Accepted all recommended options of brain Section 23 (D-034): full 10,000 stores with the day-3 speed gate, window-aware assignment LP inside E, hard 12:00 window, pool search with a discrepancy GP and EI, Kontur H3 population-weighted store locations, bonus = value of information and robustness.
- Heavy one-off computation goes to the DGX Spark; light work stays on the laptop (D-035).

### Road distances with OSRM

**Why.**
The brief (§2.5) requires every distance to be an actual road value or calibrated against road values, with source, version, extract date and profile stated, and every distance cached in `code/`.
v0.1 and v0.2 used uncalibrated factors (map x 1.30, x 1.45 in the mountains), which do not meet that rule.

**Setup.**

| Item | Value |
|---|---|
| Map data | Geofabrik `south-korea-latest.osm.pbf`, 255 MB, md5 `ea750dde8e6e6ded7a677ec7e029257e`, OSM data as of 2026-10-18 20:25 UTC |
| Engine | OSRM `ghcr.io/project-osrm/osrm-backend:v6.0.0` (arm64 build), default car profile, MLD |
| Server machine | DGX Spark (`spark-d35c`), Docker 28.3.3 |
| Query machine | Laptop, through an SSH tunnel (`ssh -N -L 5000:localhost:5000 spark`) |
| Builder | `code/osrm/build_cache.py`, run in the pinned `code/.venv310` (Python 3.10, numpy 2.2.6) |
| Output | `code/data/road_cache.npz`, 4.9 MB |

**Steps run.**

1. Laptop: downloaded the extract and checked its md5; copied it to `~/osrm-korea/` on the Spark with `scp`.
2. Spark: Docker was already installed, but the user was not in the `docker` group ("permission denied" on the socket); fixed with `sudo usermod -aG docker $USER` and a new login.
3. Spark: a first `docker run` without the OSRM command opened a container shell that ignored keyboard input (`-t` without `-i`); the container was killed and each step rerun as one complete line.
4. Spark: `osrm-extract` (car profile), `osrm-partition`, `osrm-customize`, then `osrm-routed` as a background container on `127.0.0.1:5000`; the first test query came back empty only because the server was still loading.
5. Laptop: `python osrm/build_cache.py` through the tunnel, 193 s in total.

**What was cached.**

| Pairs | Count | Source |
|---|---|---|
| Store to site | 10,000 x 60 | OSRM |
| Store to its 50 nearest stores | 10,000 x 50 | OSRM |
| All other store pairs | - | Calibrated model `road = map x exp(a + b ln map)`, one line for flat pairs, one for pairs touching Gangwon or North Gyeongsang |

Each value is the mean of both driving directions plus the snap leg from each point to its nearest road.

**Results.**

| Measure | Value |
|---|---|
| Unroutable pairs | 0 (sites, neighbours and calibration) |
| Snap distance store to road | median 57 m, 99th percentile 1.25 km, maximum 4.5 km |
| Median road / map ratio | 1.26 for store-site pairs, 1.70 for nearest-store pairs |
| Calibration sample | 3,962 OSRM pairs over 1-250 km, half for fitting, half for testing |
| Model test error, median (90th percentile) | 25% (58%) at 1-10 km, 10% (24%) at 10-50 km, 5% (14%) at 50-250 km |
| Route legs on cached values (current network, one average day) | 93% in the dense Yongin territory (1,071 stores) and in the rural Wonju territory (325 stores) |
| Route km on model values | about 12% in both territories |

**What it means.**
The old factor of 1.30 was too low for short trips (1.70 measured between neighbouring stores) and about right for DC legs (1.26).
Almost every leg a route drives is a real OSRM value; the model covers about 12% of route km with a 10-25% error, so the remaining distance uncertainty in a day's route km is roughly 2%.
Short-range model error is driven partly by the synthetic store points that sit up to 4.5 km from any road; the Kontur switch puts stores where people live and should shrink it.

**Open.**

- Switch store generation to Kontur H3 population, then rerun `build_cache.py` (the server stays up on the Spark) and the leg-coverage check.
- Rerun the reduced and full pipelines on road distances; no v0.2 number survives (D-025).
- Balance-table check planned: all-pairs OSRM inside the top candidates' territories against the cache plus model.

### Store locations from population (Kontur) and a new current network

**Why.**
Stores clustered around a hand-made city list are not where people live; the plan (Section 23 Q3) chose population-weighted locations.

**Inputs.**

| Item | Value |
|---|---|
| Population | Kontur Population, South Korea, 2023-11-01, H3 resolution 8 (about 0.7 km² per hexagon), CC BY 4.0, from HDX; 74,200 hexagons, 51.8 M people |
| Outline | Natural Earth via geoBoundaries ADM1 (coarse: 3,966 points; the full-resolution file is the same) |
| Output | `code/data/kontur_hexes.npz`: 71,015 hexagons, 51.1 M people |

**Steps.**

1. `prep/build_hexes.py`: hexagon centres from the GeoPackage envelopes; Jeju excluded; coastal hexagons within 5 km of the coarse outline kept (they held 1.05 M people).
2. Found and fixed an old bug: Seoul, Daegu and Gwangju stores had been labelled as the surrounding province since v0.1.
3. User chose the p-median for the current network (the old 12 broke the 500-1,400 bounds: five above, five below, Gangneung only 125 stores).
4. User restarted the OSRM server (`ssh spark docker start osrm`) and opened the tunnel; `prep/road_connected.py` dropped 760 ferry-only hexagons (69,429 people, mostly South Jeolla islands and Ulleungdo).
5. `prep/current_network.py` (capacitated p-median, exchange search): two passes until a fixed point.
6. `osrm/build_cache.py` rebuilt the cache for the new stores with ferries excluded (188 s).

**Results.**

| Measure | Before (city clusters) | Now (Kontur) |
|---|---|---|
| Province shares vs population | not checked | within 0.5 points everywhere |
| Current DCs within 500-1,400 stores | 7 of 12 | 12 of 12 (499-1,327 planning stores) |
| Snap distance store to road, median / 99th percentile | 57 m / 1.25 km | 27 m / 0.42 km |
| Model test error 1-10 km, median (90th percentile) | 25% (58%) | 20% (44%) |
| Model test error 50-250 km | 5% (14%) | 4% (12%) |
| Route legs on OSRM values | 93% (2 territories) | 89-99% (all 12 territories) |
| Route km on model values | about 12% | 1.6-13%, about 5% overall |

New current network (north to south): Yangju, Gimpo, Hanam, Incheon Namdong, Wonju, Yongin, Cheonan, Daejeon, Iksan, Gyeongsan, Gwangju, Busan Gangseo.
Replaced: Chilgok, Gimhae, Gangneung, Wanju (they stay candidate sites).

**What it means.**
The baseline is now the network a planner with a map and the size rules would draw, so any saving must come from what that planner ignored: road distances, the noon window and the number of DCs.
Without an east-coast DC (Gangwon has only 253 stores, below the 500 minimum), Wonju runs 157 routes for 499 stores, many of them single-store trips to the coast: the coverage-versus-minimum-size trade-off the search has to price.

**Open.**

- Rerun the reduced and full pipelines on the new world (on the Spark).
- District labels for the `stores` table (the brief asks for province and district).
