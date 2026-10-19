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
