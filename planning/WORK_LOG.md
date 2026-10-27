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

### v0.3 engine and the Spark run

**Why.**
No v0.2 number survives the road cache and the Kontur world (D-025); the brief also asks for outcome tables, districts and two checks.

**Changes.**

- Territory process pool (D-048); departure waves (D-049); outcome tables (D-050); districts (D-051).
- Timing on one laptop core: a 1,039-store territory takes 0.14 s for its road matrix and 0.17 s to route one day.
- Smoke run at 5% (483 stores, 52 candidates): 202 s on one capped core; pooled and serial costs identical.

**Run on the Spark** (from the laptop, in `Distribution-Centre-Network/`):

```sh
tar czf - --exclude=.venv310 --exclude=results --exclude=__pycache__ code | ssh spark 'rm -rf ~/dcn && mkdir -p ~/dcn && tar xzf - -C ~/dcn'
ssh spark
python3 -m venv ~/dcn-venv && ~/dcn-venv/bin/pip install -r ~/dcn/code/requirements.txt
tmux new -s dcn
cd ~/dcn/code && ~/dcn-venv/bin/python run_reduced.py && ~/dcn-venv/bin/python run_full.py 2>&1 | tee run.log
```

Then back on the laptop: `scp -r spark:~/dcn/code/results code/` (the full tables are about 40 MB).

**Open.**

- Results of both runs; switch `DEMO_PROFILE` to `full`, rebuild the demo, rerun `verify.py`.

### Spark run 1 (v0.3) and what it exposed

**Run.** Spark, Python 3.12.3 aarch64; reduced 83 s, full 718 s (16 workers).

**Results (not reportable, superseded).**

| Measure | Reduced | Full |
|---|---|---|
| Baseline E (M KRW/month) | 2,069 | 9,383 |
| Recommended | k = 12, 1,803 | k = 13, 7,607 |
| Saving, 28 final days (90% band) | 266 [261, 271] | 1,776 [1,771, 1,782] |
| Saving, held-out days | 274 | 1,778 |
| Baseline worst-day service | 97.9% | 97.7% |
| History year (outcome tables) | 97.9%, 190 vehicles/day | 97.6%, 824 vehicles/day, 3.50 M deliveries |
| G1 against E, Spearman | 0.55 | 0.20 |

**What was wrong.**

- The k sweep jumped at k = 10 and 12 (10.7 and 10.9 bn against 7.8 bn at k = 11): the best k = 12 pool candidate put Naju and Muan 20 km apart, and the 500-store minimum then forced Naju to serve stores up to 515 km away (196 vehicles, 113 failures a day).
  G1 never saw it because its assignment ignored the minimum (D-052).
- No k = 12 candidate in the pool was as good as today's sites with redrawn territories (D-053).
- With 16 docks every k, the baseline included, overflowed; the dock count must follow the 1,400-store cap (D-054).
- The baseline itself misses 98% on its worst day: Wonju serves the east coast with about 111 over-limit single-store routes a day (stores 125-210 km away); this is real geography of a network without an east-coast DC and stays.

**Rerun.** Same commands as above (copy the code again first); then copy `results/` back.

### Spark run 2 (v0.3, reportable)

**Run.** Spark, Python 3.12.3 aarch64, numpy 2.2.6, scipy 1.15.3; seed 437; reduced 85 s, full 709 s; budget 40 (13 G seeds + 27 EI); 7 search, 28 final, 14 held-out days.

| Measure | Full (9,718 planning stores) | Reduced (1,938) |
|---|---|---|
| Today's network E (M KRW/month) | 9,383 | 2,069 |
| Recommended | 13 DCs (keep 7, close 5, open 6), 7,607 | 12 DCs, 1,775 |
| Saving, 28 final days (90% band) | 1,776 [1,771, 1,782] | 294 [291, 297] |
| Saving, held-out days | 1,778 [1,771, 1,784] | 296 |
| Worst-day service, today / recommended | 97.7% / 99.0% | 97.9% / 99.1% |
| Waterfall: redraw territories / move sites / 13th DC | -630 / -1,059 / -87 | |
| k sweep, search days (M) | 9: 7,964 · 10: 7,593 · 11: 7,563 · 12: 7,550 · 13: 7,448 · 14: 8,012 | flat 10-13 |
| Departure waves (30 docks) | k* 13 -> 14 (k = 9-13 overflow the docks by 13-34 departures a day; today's network by 37) | 12 -> 12 (8 docks) |
| Thinning | full k* 13, reduced k* 12; km per store 1.26x (square-root rule predicts 2.24x) | |
| G1 against E (Spearman, within k) | 0.60, 0.25; G-pick loss 116 M | 0.75, 0.51 |
| Search vs random selection (best after 40) | 7,448 vs 7,929 (random median 7,929) | both 1,793 |
| Relay reversal (0 / 180,822 / 550,000 KRW) | k* 13 / 13 / 12; saving 1,045 / 1,776 / 3,270 | k* 11 / 12 / 12 |
| History year (outcome tables) | 3,502,822 deliveries, 97.6% before noon, 824 vehicles/day, 139,919 km/day | |

**What it means.**

- The saving is mostly relocation (1,059 M) and redrawn territories (630 M); the number of DCs is a flat choice between 10 and 13 (within 150 M), so k is the least certain part of the answer.
- The departure-wave check moves k* from 13 to 14 at an assumed 30 docks: the dock count is the first number to confirm with operations.
- The reduced instance is off by one DC; the full instance is reported.
- Relay routes still carry 517 M of the recommended network's cost and 1,249 M of today's; the reversal keeps k* at 12-13 and the saving positive at every price.
- `verify.py`: 23/23.

**Open.**

- Review 03 with the panel on run 2 and the demo.
- Dock-count sweep (break-even docks for k = 13), stop-time and demand-growth reversals in the next Spark run.

### Review 03 and v0.4 (run 2 superseded)

**Why.**
Review 03 (`stakeholders/REVIEW-03-v0.3.md`) found that one-truck-per-far-store routes carried most of the run-2 saving and were counted late although they arrived by 10:34, and that today's network had been built with the store minimum the brief exempts it from.

**Correction to the run-2 notes above.**
The statement that today's network "misses 98%" because of real geography was wrong: it was the late label on relay deliveries (1 - 227/9,718 = 97.66%).

**Changes.**

- Relay route class, service by the clock (D-058); reach-constrained baseline with stable site ids (D-059); R5 reversals (D-060); second dock count and pool-wide Spearman (D-061); road shapes in the demo (D-062); business decision log (`BUSINESS_DECISIONS.md`).
- New today's network (fixed point of `prep/current_network.py`): Gangneung Gujeong, Namyangju Jingeon, Gimpo Gochon, Gwangju-si Opo, Hwaseong Hyangnam, Yeongju Munsu, Nonsan Yeonmu, Daegu Dalseong, Gyeongju Oedong, Busan Gangseo, Naju Bitgaram, Gwangyang Port; demand-weighted road km 31.9, farthest store 121 km.
- 5% smoke run (215 s, one capped core): no relay route in today's network, today's network cheaper than every candidate at that scale (not evidence; thinning distorts).

**Run 3 on the Spark** (from the laptop, in `Distribution-Centre-Network/`):

```sh
tar czf - --exclude=.venv310 --exclude=results --exclude=__pycache__ code | ssh spark 'rm -rf ~/dcn && mkdir -p ~/dcn && tar xzf - -C ~/dcn'
ssh spark
tmux new -s dcn
cd ~/dcn/code && ~/dcn-venv/bin/python run_reduced.py && ~/dcn-venv/bin/python run_full.py 2>&1 | tee run.log
```

Then `scp -r spark:~/dcn/code/results code/`, and with the OSRM tunnel open `python osrm/build_shapes.py full` for the new routes.

### Spark run 3 (v0.4, reportable)

**Run.** Spark, Python 3.12.3 aarch64, numpy 2.2.6, scipy 1.15.3, 16 workers; seed 437; reduced 100 s, full 886 s; budget 40 (13 G seeds + 27 EI); 7 search, 28 final, 14 held-out days; road shapes 27,437 legs, 0 missing.

| Measure | Full (9,718 planning stores) | Reduced (1,938) |
|---|---|---|
| Today's network E (M KRW/month) | 5,874 (579 vehicles/day, no relay route, 100% before noon) | 1,355 |
| Best alternative (top-5 re-scored on 28 days) | 10 DCs, 5,975 (617 vehicles/day, 18 relay routes/day) | 12 DCs, 1,466 |
| Saving, 28 final days (90% band over demand days) | -100 [-110, -91] | -112 [-114, -107] |
| Saving, held-out days | -103 [-108, -97] | -110 |
| Today's sites, territories redrawn within 500-1,400 | 9,568 (118 routes a day beyond even the relay limits) | 2,161 |
| k sweep, search days (validation, best of the pool per k) | 9: 5,952 · 10: 5,828 · 11: 5,856 · 12: 5,982 · 13: 6,066 | flat 10-12 |
| Departure waves (21 docks; 27 docks) | k* 10 -> 12; 10 with 27 docks; today's network does not overflow | 11 -> 11 |
| Thinning | full k* 10, reduced k* 11; km per store 1.45x for today's network (square-root rule 2.24x) | |
| Reversals (saving at k*) | stop 10 min -41 (10), 20 min -156 (10); speed 30 km/h -261 (11), 45 km/h -32 (10); calibrated model only -55 (10); DC fixed 100 M -197 (11), **200 M +29 (10)** | all negative |
| Relay price reversal (0 / 180,822 / 550,000 KRW) | saving -1 / -100 / -302; k* 10 / 10 / 11 | k* 11 |
| G1 against E, Spearman (40 evaluated / whole pool / within k) | 0.66 / 0.58 / 0.76; G-pick loss 446 M (k = 8 against 10) | 0.55 / 0.46 / 0.46 |
| Search vs random selection | both reach the pool best (5,828); the G seeds already contain it | same |
| History year (outcome tables) | 3,502,822 deliveries, 100% before noon, 573 vehicles/day, 64,811 km/day | |
| Average day vs sampled days | 5,758 vs 5,828 (1.2% lower) | |

**What it means.**

- With today's network placed as a planner would (every store within one driver-day, small regional DCs allowed because the baseline is exempt from the bounds), no redesign that respects 500-1,400 stores per DC beats it; the best alternative costs about 100 M a month more on every day set.
- The bounds are what make redesign unattractive: forcing today's own sites into 500-1,400 costs 3.7 bn a month (Gangneung, Yeongju and Gwangyang would have to take stores far beyond one driver-day).
- Only a DC rent of 200 M turns the answer (+29 M at 10 DCs); every other tested assumption keeps today's network.
- The departure-wave check moves the best alternative from 10 to 12 DCs at 21 docks, but no alternative beats today's network either way.
- The search added nothing over its seeds this time (the G1-best of k = 10 was already the pool best); both rules reach it.

**Open.**

- `verify.py` on run 3; demo QA; definition and proposal.

## 2026-10-21 (day 2)

### Algorithm review (laptop only)

**Why.** Run 3 says today's network beats every bounded redesign; the user asked whether the algorithms are the reason.

**Runs.** Laptop, one core each (`taskset`, `nice -n 19`), scratch `uv` environment with pyvrp 0.11.3; full world of run 3 rebuilt in 2 s.

| Experiment | Run time | Result |
|---|---|---|
| Savings against PyVRP, today's network, search day 0, 0.1 s per store | 17 min | 587 vs 558 vehicles (-4.9%), km equal |
| Same, k = 10 alternative (Naju and Gimhae rerun at 0.3 s per store, 9 min) | 17 + 9 min | 620 vs 596 vehicles (-3.9%); at 0.1 s per store PyVRP found no feasible solution for Naju and Gimhae |
| Selection-rule replay on the 390 evaluated pool candidates, 30 repetitions | about 15 min | Every model-based rule finds the pool best; random 13% |
| Full-swap check of G1's site search, k = 8..13 | seconds | Already a local optimum |

**Problems hit.** PyVRP with one vehicle per store returned all single-store routes on rural territories; bounding the fleet at the savings count + 25% fixed it. My first relay setup (one model, prohibitive edges for relay vehicles) gave infeasible routes; replaced by E's own split (one-driver routes, then relay routes for far stores).

**What it means.** See `ALGORITHM_REVIEW.md`: the router's error (about 4% of daily cost) shifts both networks alike, the selection rule is fine, the weak part is G1 without the clock and the pool built from it. No Spark run needed for the decision; two optional scripts are in `experiments/`.

### Baseline checks X1-X5 (laptop only)

| Check | Run time | Result |
|---|---|---|
| X1-X3: reproduce run 3, then change one rule at a time (7 search days) | 2 min, one core | Run 3 reproduced (5,736 / 5,828); today's sites and the best redesign within 0.2% under identical rules |
| X4: local search on E from today's sites, no minimum, cap 1,400 | 41 min, one core | 328 evaluations; 12 DCs; final days 5,824 vs today 5,874 (-50 M) |
| X5: local search on E from run 3's best redesign, within 500-1,400 | 24 min, one core (parallel to X4) | 193 evaluations; 10 DCs; final days 5,943 (+69 M vs today) |

**What it means.** The redesigns lose because of the 500-store minimum and today's exemption from the bounds, not because of weak algorithms; on the same feasible set the optimiser wins (review Section 9).

### Demo tab and Omelet papers (laptop only)

- `code/static/demo.template.html`: new "Data & baseline" tab; `python build_demo.py` rebuilt `demo.html` (4.82 MB); Playwright check at 1920, 1440 px and iPhone 13: no console errors, no horizontal overflow.
- X6 learned territory cost (`experiments/territory_surrogate.py`), one core, 46 min, peak 1.4 GB: 421 training territories; held-out Spearman 0.92 (G1 0.60); learned-cost MILP 14 DCs, final days 6,909 M within bounds and 6,128 M without the minimum (today 5,874 M); both MILPs stopped at the 600 s limit.
- A first run was stopped after its regression gave negative per-store costs; the rerun uses non-negative least squares and caches the training territories in `territory_surrogate_train.npz`.

## 2026-10-27 (day 3)

### New baseline, G2, run 4 (Spark)

**Why.** Run 3 said every redesign loses to today's network; its baseline was the optimum of the search's own objective (D-069).

**Runs.** Laptop reduced run of the new code (2 workers, 1,008 s): saving 124.5 M, k = 11. Spark run 4 (`run_reduced.py` 109 s, `run_full.py` 908 s): baseline 6,564.8 M on the final days, recommended k = 10 at 5,974.5 M, saving 590.3 M (581.4-599.8), held-out 576.7 M (564.4-589.5); G2 Spearman 0.86 (G1 0.56); only the "today already optimal" reversal flips the sign (-61 M). The results landed in `~/code/` because `scp` ran from the home directory; moved into `code/results/`, run 3 archived in `archive/run3_results/`.

**Problem hit.** The Spark's reduced run differed from the laptop's (pool differs from the k = 7 G1-best on; saving 117.2 vs 124.5 M): unstable `np.argsort` on ties orders differently per processor (D-075). Fixed with stable sorts everywhere; the 2016 planner's 12 sites are unchanged.

**PyVRP check (laptop, one core each, 17 min).** Run 4's networks, day 0, 0.1 s per store: where both solvers are feasible savings is 1.4-4.4% above PyVRP, but 18% on Gangneung (116 stores: 17 vs 14 vehicles); PyVRP finds no feasible solution on 4 baseline and 2 recommended territories at this time limit. To redo on run 5's networks with a longer limit for those territories.

### Extensions, demo, proposal (laptop)

- `dcn/extensions.py` (D-076): reduced test on run 4's reduced registry, 147 evaluations, 438 s on one core; the myopic sequence renews Hanam and Gangneung and ends at 13 DCs, the committed one reaches the recommendation.
- Demo: Extensions tab (animated lease timeline, policies' monthly cost, robustness curves, VOI grid), growth animation 1990-2026, G2/G1 toggle in R3, new baseline text, waterfall with a cut axis, every precomputed card tagged with its command; Playwright offline: no console errors, no horizontal overflow on any tab at 1440 px.
- `proposal.html` (D-077): 11-12 slides from the registry; Playwright: no errors.
- Definition §5 and §6 written from run 4; placeholders left for run-5 timings, verify, PyVRP and extensions.

### Spark run 5 (v1.0, reportable)

**Code.** Stable sorts (D-075), extensions (D-076), timing and store years in the registry (D-078), proposal built with the demo (D-077).

**Commands** (user, from the laptop and in tmux on the Spark): copy `code/` with `tar | ssh`, then `cd ~/dcn/code && (~/dcn-venv/bin/python run_reduced.py && ~/dcn-venv/bin/python run_full.py) 2>&1 | tee run5.log`; results copied back with `scp` into `code/results/`.

| Measure | Reduced (1,938 stores) | Full (9,718 stores) |
|---|---|---|
| Run time, Spark, 16 workers | 106.5 s pipeline + 32.4 s extensions | 909 s pipeline + 160.5 s extensions |
| Baseline E, search days | 1,581.0 M | 6,418.9 M |
| Recommended k | 12 | 10 |
| Saving, final days (90% interval) | 117.2 M | 592.4 M (584.0-601.0) |
| Saving, held-out days | 126.4 M | 582.6 M (570.9-593.7) |
| G2 / G1 Spearman | 0.92 / 0.37 | 0.86 / 0.56 |
| Search | pool best found | pool best found at evaluation 18; random selection ends at the best seed |

**Cross-machine check.** The laptop's reduced run of the same code (x86_64, 1 worker) and the Spark's (aarch64, 16 workers) agree in 52,205 of 52,206 registry numbers to 1e-9; the exception is the expected-improvement value of the last search step (1e-7, 0.07% apart), which changes no choice.

**Extensions rerun on the laptop** (2 workers, reduced 390 s, full 1,411 s) after fixing how the myopic path's end state is priced (D-076); every other extension number identical to the Spark's.

| Extension | Result |
|---|---|
| 36 months, bn KRW | keep everything 231.1; redraw territories only 217.6; committed sequence 214.5; one-shot switch 240.5 (30.7 bn of rent on released sites) |
| Myopic sequence | renews Yongin, Andong, Gangneung; 1.0 bn cheaper over 36 months, end state 15.8 M a month dearer than the committed one |
| Robustness | k* = 10 under chain volume -15%, +20% and capital region +30% (saving 580-602 M); k* = 9 with the calibrated distance model only (saving 393 M, regret of k = 10: 4 M) |
| Value of information | travel times: EVPI 27.2 M a month (a* = 11 under the prior, k = 10 regret 40.4 M); chain volume: 0; true store rates: 0 |

**Laptop checks after run 5.**

- `osrm/build_shapes.py full` through the tunnel: 28,333 legs, 0 without a route.
- `verify.py` (Playwright 1.61 installed in `.venv310`): 28/28.
- Offline browser check of `demo.html` (Chromium 149, every non-file request blocked) at 1440 and 390 px: no console errors, no requests, no overflow; live solve 67 vehicles, 4,878 km, 100% before noon; `proposal.html`: 12 slides, no errors, no overflow.
- Store impact on the shown weekday: 2,346 stores (24%) served more than 2 h later under the recommendation, 3,219 more than 1 h earlier.

**PyVRP on run 5's networks** (laptop, one core each, day 0): first pass at 0.1 s per store (17 min each), then the territories PyVRP could not route at 0.5 s per store (baseline DCs 0, 1, 5, 8, 54, 57; recommended DCs 6, 40, 47). Recommended network, all ten territories feasible: savings 0.3% below to 7.0% above PyVRP per territory. Baseline: Yongin (1,356 stores) unrouted by PyVRP even at 0.5 s per store.

**Problems hit.**

- `scp` run from the home directory put the results in `~/code/` (moved into place).
- PyVRP does not build on the Spark (no aarch64 wheel for 0.11.3, source build fails); the check stays on the laptop.
- A grader running the reduced run with the default worker count could exhaust the laptop's 6.8 GB; added `DCN_WORKERS` (README).

### Fresh-environment reproduction (laptop)

`tools/make_zip.py` (53.6 MB, 61 files), extracted into the scratchpad; `uv venv --python 3.10` and `uv pip install -r code/requirements.txt` (numpy 2.2.6, scipy 1.15.3); `unshare -rn env DCN_WORKERS=2 python run_reduced.py` (no network): 17 min 15 s.
Against the shipped reduced registry: 54,642 numbers compared, 27 differ by more than 1e-9, all of them expected-improvement values in the search log (at most 0.07%); every search choice, the recommendation and every cost identical.

### PyVRP comparison complete, and what it changed

Baseline reruns at 0.5 s per store finished (Daejeon 51 vs 43, Andong 33 vs 24, Daegu 67 vs 59, Gwangju 39 vs 35, Gimpo 76 vs 72; Yongin still unrouted by PyVRP).
`checks/routing_summary.py`: today's network 654 vs 608 vehicles (operating cost 6.6% above PyVRP), recommended 620 vs 599 (2.9%); day-0 operating saving 6.3 M a day by savings, 1.2 M by PyVRP; monthly saving about 156 M lower, about 437 M.
Two cheap router repairs prototyped in the scratchpad: route elimination by cheapest insertion (Daejeon 51 -> 50) and a sweep construction with insertion (worse than savings everywhere); neither adopted.
The summary is embedded by `build_demo.py` (demo Checks tab card, reversal row, hero note; proposal slides 1 and 9) and stated in the definition (Sections 2a, 4, 5, 6, 7, header).

### Midterm grading round 1 and fixes

Three fresh graders with the frozen prompt v2 on the hand-in ZIP: base 92 / 94 / 92, bonus 6.5 / 6 / 6 (`../../grading/GRADING_LOG.md`).
All three ran the reduced run and hit their 15-minute limit on two cores; every number they reached matched the shipped log to the digit.
Fixes:
- Per-type calendar multipliers explained with numbers (office weekend 0.70, residential 1.12, a pooled profile 1.04; DC-level error up to 2.7%) in Section 3 and the demo.
- The 9-, 10- and 11-DC networks take the same action at every lease expiry; the 10-vs-11 choice (Jinju Sabong) waits for the GPS study.
- Model uncertainty next to the demand interval (about 400-600 M across the checks), the baseline rule's history stated, catch-up orders traced, and wording fixed (distance check, sweep source, reduced k*, slide 10, `C-fleet-cost`).
- Reduced profile without the report-only steps (`checks=False`): 10 min 22 s on two workers of the laptop while other jobs ran; against run 5's reduced registry, 53,902 numbers compared, only the same 27 EI values differ; the full run's thinning rows stay valid. Run 5's reduced outcome tables archived in `archive/run5_reduced_outcome_tables/`.
- PyVRP on the best 9- and 11-DC networks started (laptop, 0.3 s per store) to test whether the router bias moves k.

### Spark run 6 (reported) and the assumption register

**Code.** Stock-out penalty applied (D-079); strict-brief reversal rows (D-080); reduced profile without report-only steps.
**Run.** Spark, user: reduced 74 s, full 966 s + extensions 160 s; registry 2026-10-27T11:24:50.
**Against run 5.** Every final-day figure, the recommendation, the saving and its intervals, the extensions and the router check are unchanged. Changed because penalised candidates cost more: G2 Spearman 0.83 (0.91 pool, 0.72 within k), G1 0.58; G2's R² 0.36; sweep k = 7 7,807 M and k = 18 7,331 M; budget-of-one case 8,686 M; the pool's best found at evaluation 16 instead of 18.
**New reversal rows.** Strict brief (no relay, far stores are stock-outs): best network checked k = 11, saving -511 M; strict brief and no minimum: k = 12, saving +625 M. The redesign therefore needs one of two business rules: a second driver on far routes, or a small coastal DC below 500 stores.
**Checks.** Road shapes rebuilt (28,333 legs); `verify.py` 28/28; demo offline at 1440 and 390 px and all 13 slides: no errors, no overflow.
**Scratchpad.** The session scratchpad was wiped while the session was paused (grader folders, fresh environment, scripts); grader results survive in `../../grading/GRADING_LOG.md`.

### After grading round 2: drift sweep, candidate generation, redraw check

- Full extensions recomputed on the laptop (2 workers, 38.5 min, 178 evaluations): drift sweep (saving 675 / 488 / 591 / 323 / 302 / 357 M for redesign years 2010 / 2013 / 2016 / 2019 / 2022 / 2026; the 2016 row equals the baseline); candidate generation (best new network 6,009 M against the pool's 5,828 M).
- PyVRP on today's sites with redrawn territories (laptop, 0.3 s per store): the redraw step is worth 12.4 M a day with savings routes and 8.9 M with PyVRP's, about 270 M a month instead of 375 M.
- Corrected: the saving is not "entirely" today's drift (definition Sections 3, 5, 6; demo drift card).
- `verify.py` 29/29 (new: drift 2016 row = baseline); QA scripts kept in `tools/qa/` because the session scratchpad was wiped twice; demo and all 13 slides clean (no errors, no overflow, no cut formulas).

### After grading round 3: faster reduced run, demo fixes

- Grading round 3 (G7-G9): base 99.5 / 99 / 99, bonus 6.5 / 7.5 / 7; logged in `../../grading/GRADING_LOG.md`.
- Router: feasibility check without the arrival list, plain-list lookups on small territories, savings pairs of stores already inside a route skipped; route fingerprints (108 territory-days x 3 parameter sets, fractions 0.2 and 1.0) identical to the old code.
- Greedy assignment: overloaded DCs' stores moved with plain-list lookups instead of one numpy call per store; identical on 2,400 random networks, identical reduced pool (103 s to 85 s on one core).
- Reduced run on two pinned laptop cores: 6 min 48 s (was 10 min 22 s); registry equal to the shipped one except 16 EI values and the timing fields; shipped Spark registry kept.
- Demo: data tab states the baseline rule was adopted after an earlier baseline beat every redesign; the failure-case button resets the live-solve sliders first (checked in Chromium, no errors).

### Brief coverage audit and the demo additions (27 Oct, evening)

- Side-by-side audit of assignment.md against demo.html and proposal.html (lavish review page, `.lavish/`, not in the ZIP): 45 brief items, 24 clear in the demo, 16 partial, 4 missing, 1 definition-only; the user annotated 11 items.
- Answer tab: why this network is the best found (all 402 evaluated networks on one axis, challengers head to head, five tests, what "best" means) and the recommended network DC by DC (per-DC fleet columns appear after the next full run, which now stores `owned_by_dc`, `need_mean_by_dc`, `need_max_by_dc`).
- How it works: I/O schema; sampled against average-day cost with the non-linearity stated; hard window; cost and return of one solve; in and out of the model; what passes down and up; the assignment's place; linear against combinatorial parts; budget; an evaluation log table; Q7 the balance table with a decision chip per row.
- Data tab: seven generation steps with how and why, the eight tables with what one row cannot tell, the assumption register.
- Checks: reduced run and how it differs; Delivery day: one command tag for the KPIs, fading truck tails (about 10% more draw time, no extra data); a "Find an answer" index of 28 business and analyst questions.
- Proposal (15 slides): scope as must, should, could, won't (left-out items flagged for the business); why the answer is right; linear against combinatorial; owned vehicles in the four voices as in the demo.
- README: scope section. Checks: demo offline at 1440 and 390 px clean, all 15 slides clean, `verify.py` 29/29.

### User feedback round, 28 Oct: lag, visuals, proposal, definition

- Delivery day: truck tails and emoji labels removed; the map now draws from cached layers (static land and routes, incremental stores, truck sprites, a padded layer so following a truck only shifts it): 60 frames per second in every view, against 9-27 before (Chromium, measured by painted frames).
- Visuals: night-to-day light with headlight glows, DC progress rings, delivery pulses, a day-against-the-clock chart; the answer map plays the change from today's territories and follows waterfall clicks; count-up hero numbers, growing bars, cards rising into view (all off under reduced motion).
- The challenger card is gone; its comparison is the sixth test. No horizontal scrolling at ten widths from 390 to 1920 px (nav wraps below 1180 px, engine status moved to the live card).
- Proposal regenerated in project-management order, 16 slides: section tracker, methodology with pipeline and measured accuracy, assumption register with status, inputs from the business with owners and dates, risk register, lease roadmap, stage gates with what to measure first.
- Definition v1.1: Section 7 completed (tools and roles, LLM uses and checks, where it was wrong, my decisions and corrections, run history, guardrails, sources); Section 5 test register; Section 6 risk register; no reference to review or grading roles.
- Checks: demo offline clean, 28 finder jumps, every slide free of collisions and template leftovers, `verify.py` 29/29.

### User feedback, 28 Oct (second round)

- Day map: night-to-day light, headlights and delivery pulses removed; DC progress rings kept; still 60 frames per second.
- Answer map: territories as tinted convex hulls (farthest 3% of stores left out), faint spokes from each DC to its stores, a soft shadow under the land, today's territories as dashed outlines in the change view, DC labels placed after all markers so they never overlap.
- How it works and Extensions: every method stated upfront ("Use X to achieve Y because Z") in the lectures' notation: Gamma(alpha, beta) update as a weighted average, negative-binomial posterior predictive, GP posterior mu(x|D) and sigma(x|D), EI as E[max(0, f_min - f(x))], EVPI via d*, a generator conditioned on a target (Lecture 6), formulas re-rendered with KaTeX.
- Proposal (17 slides): source line for the four meeting statements (from the brief, not invented), method names with lectures, one colour per scope block, the quick estimate explained first (about 10 ms against about 20 core-seconds), "Further inputs required from the business", an operating-realities slide; the same items added to the definition's register.
- Checks: demo offline clean, no overflow at 390-1920 px, every slide free of collisions and leftovers, `verify.py` 29/29.
