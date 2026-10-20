# Review 03 - TA reproducer (02) with the lead developer's eye (13)

Reviewer state: code v0.3 (`code/README.md:3`), full registry `generated` 2026-10-20T10:19:15, reduced registry 2026-10-20T10:07:26.
Read-only review; no run, verify or app command was executed.
Table checks were streamed with a small `csv`/`gzip` script over `code/results/full/tables` and `code/results/reduced/tables`.

## 1. README against the brief and the code

### What holds

- Three commands are given in order install, reduced, full (`code/README.md:8-12`), and the order is justified by the thinning check (`dcn/pipeline.py:258-261`).
- `requirements.txt` pins `numpy==2.2.6` and `scipy==1.15.3`, and `registry.meta` records `python`, `numpy`, `scipy` and `machine` (`dcn/pipeline.py:325-326`); review-02 T1 is fixed.
- Only `DEMO_PROFILE` rebuilds the demo (`run_full.py:9`, `run_reduced.py:9`, `dcn/config.py:51`); review-02 T3 is fixed.
- The road cache exists (`code/data/road_cache.npz`, 5.0 MB) and its `meta` names source, md5, extract timestamp, engine, profile, snap statistics and test error; review-02 T4 is fixed.
- No run-time path touches the network: only `osrm/*.py` and `prep/road_connected.py` call `urllib` against `localhost:5000`, and `verify.py:170` only calls the local app.
- Seed 437 is stated (`code/README.md:43`, `dcn/config.py:4`) and recorded (`meta.seed`).

### What is false, stale or missing

- No expected run time for any command, which brief 6.2 asks for by name; the registry already has the numbers: full `runtime_s` 708.7 and reduced 85.3, both on `machine` aarch64 (DGX Spark, up to 16 workers).
  A TA laptop with 4 to 8 cores should expect several times longer, and the README must say so (review-02 T2 still open).
- "tested on Python 3.10.19" (`code/README.md:9`) is true only for the venv (`code/.venv310/pyvenv.cfg`: 3.10.19, x86_64); every shipped number was produced on Python 3.12.3 aarch64 (`registry.meta.python`).
  The README should state which numbers were produced where, and whether a 3.10 x86 reduced run was compared against the shipped reduced registry.
- The distance source in the main README is "roads from OpenStreetMap contributors (ODbL) via OSRM" (`code/README.md:43`) without engine version, extract date or profile; those exist in `osrm/build_cache.py:16-18` and `registry.meta.distance_model` but brief 2.5 and 6.2 ask for them in the hand-in text.
  One line is enough: OSRM v6.0.0, Geofabrik south-korea-latest extract of 2026-10-18T20:25:06Z, default car profile without ferries, MLD.
- Seed and data sources sit under the heading "Known gaps of this version" (`code/README.md:40-43`); they are not gaps and a literal TA will skip that section.
- "Known gaps" says "the G remedy and the remaining reversal sweeps are not in yet" (`code/README.md:42`); fine as an honest status line, but it must be removed or updated before hand-in.
- The README does not say how the reduced run differs beyond "1 store in 5": `pool_per_k` is 14 against 30 (`dcn/config.py:54-55`), fixed costs and bounds scale to 100-280 stores, and k still spans 7-19 in both (`meta.k_range`).
- The in-browser solve is described as "a simplified in-browser copy of the savings rules (no 2-opt)" (`code/README.md:20`), but it also uses the calibrated map model instead of the cached OSRM legs (`verify.py:142` builds the JS reference from `routing.dist_matrix`, the template's `roadKm` at `static/demo.template.html:559`); the page's label "same savings rules, no 2-opt" (`static/demo.template.html:601`) omits this too, and brief 6.3 asks a static page to state the difference.
- `python app.py` serves "on http://localhost:8437" (`code/README.md:21`), but `app.py:56-61` silently moves to 8438-8447 and raises `NameError` on `server` if all are taken (review-02 T5 still open).
- `python verify.py` is advertised (`code/README.md:16`) without saying it needs `playwright` and Chromium, which are not in `requirements.txt`; on a TA machine the check "JS engine = Python engine" is recorded as FAIL with "not run" (`verify.py:158-159`).
- Reproducing the shipped `demo.html` needs five commands, not three: the run builds the demo with whatever `verification.json` exists (`build_demo.py:12`), so the shipped page (verification 10:25:44 embedded, run 10:19:15) is only reached by `run_full.py`, then `verify.py`, then `build_demo.py`.
  The README never mentions `build_demo.py`.
- The demo prints the verification time but never compares `VER.registry` with `M.generated` (`static/demo.template.html:820`), so a stale verification would display as current.
- The layout table omits `app.py`, `verify.py`, `build_demo.py`, `static/`, `results/` and `data/`; the TA questions "where is the cache and how big" (02, Q5) are not answered in the README.
- Jeju is dropped (`dcn/geo.py:125-126`); nationwide coverage without Jeju should be stated where the instance is described.

### osrm/README.md

- Engine image, extract file and profile are stated (`code/osrm/README.md:20-30`); the extract date is not, although `build_cache.py:18` has it.
- No download step for the PBF (Geofabrik URL and the md5 that `build_cache.py:17` records).
- "fitted on about 4,000 OSRM pairs ... error measured on a held-out half" (`code/osrm/README.md:12`): the test error is measured on a half-fit model (`build_cache.py:93`), but the shipped coefficients are refit on all pairs (`build_cache.py:98`); say so, or ship the half-fit coefficients.
- "the engine refuses a cache built for another world" (`code/osrm/README.md:42`) is half true: `distances.site_km` compares store coordinates only (`dcn/distances.py:67`); `site_ids` is saved (`build_cache.py:113`) and never checked, so a changed site list with 60 entries would load silently.
- The rebuild chain is undocumented: `prep/build_hexes.py`, `prep/districts.py`, `prep/road_connected.py` (needs OSRM), `prep/current_network.py`, then `osrm/build_cache.py`.
  `data/kontur_hexes.npz` is dated 2026-10-20 09:25, after `road_cache.npz` (2026-10-19 20:56); the full run at 10:19 passed the coordinate check, so stores did not move, but the order of these steps should be written down.
- The SSH host alias `spark` and "here the DGX Spark" are personal setup; keep them, but add that any Docker host with about 4 GB works.
- `osrm/build_shapes.py` is untracked and appears in neither README.

## 2. Tables against brief Section 2.5 (full profile; reduced gives the same verdicts)

| Table | Rows | Schema | Checks |
|---|---:|---|---|
| `stores.csv` | 10,000 | 8 columns, names as in the brief | ids unique; `region` is "province, district" for every row, no empty district; dates ISO, 568 opened and 282 closed, none both; lat 34.31-38.44, lon 126.09-129.55 |
| `demand_history.csv.gz` | 3,502,822 | 3 columns as in the brief | 365 dates 2025-10-01 to 2026-09-30; no row outside a store's open window; 849 short histories; cages 0-31 |
| `dcs.csv` | 12 | 7 columns as in the brief | fixed cost 132.0, 157.5 or 180.0 M KRW by region; every `dc_id` is also a `site_id` with the same coordinates |
| `candidate_sites.csv` | 60 | 5 columns as in the brief | includes the 12 current sites; `max_stores` 1,400 (280 reduced) |
| `cost_parameters.csv` | 6 | `parameter, value, unit` | all six brief items present |
| `deliveries.csv.gz` | 3,502,822 | 5 columns as in the brief | one row per open store-day, no duplicates, no store-day missing against `demand_history`; `delivered_at` always HH:mm |
| `vehicle_days.csv.gz` | 300,778 | 7 columns as in the brief | `stops` equals the vehicle-day's deliveries for every row; every `vehicle_id` starts with its `dc_id`; vehicle-day sets identical in both tables |
| `spot_hires.csv` | 4,380 | 4 columns as in the brief | `cost = trucks_hired x 550,000` on every row; `trucks_hired` equals the `-Sxx` vehicles in `vehicle_days`; total 2,488.2 M over the year equals `history_ops.spot_month` x 12 |

Consistency with the registry: `history_ops.deliveries` 3,502,822 and `km_day` 139,918.8 match the tables (139,919.5 from the rounded `km_driven`).

### Findings in the tables

- The deliveries table says every delivery is on time while the registry says 97.6%.
  The latest `delivered_at` is 12:00 and no row is after 12:00, yet `history_ops.service` is 0.9761, because routes tagged "violates limit" count as not on time (`dcn/pipeline.py:129-130`, `dcn/evaluate.py:141-144`).
  A TA who computes the service level from `deliveries.csv.gz` gets 100% and cannot reproduce 97.6%.
- `vehicle_days` breaks the stated vehicle limits on 83,801 of 300,778 rows (27.9%): `km_driven` above 250 (maximum 421.0), and 37,646 rows return after 13:00 (latest 16:17).
  All 83,801 are one-stop routes to far stores, about 230 a day, which the model prices as a relay driver (`dcn/config.py:47-49`).
  Nothing in the table, the README or a column says so; a TA who checks the 250 km limit will read this as a bug.
  Smallest fix: one README sentence stating the relay convention and that these rows are the `over_limit_day` routes.
- `departed_at` is 04:00 on all 300,778 rows (`dcn/pipeline.py:128` writes `p.depart`), so about 69 vehicles per DC leave in the same minute, while the departure-wave check sizes docks at 30 per hour (`waves.docks`).
  The outcome tables therefore describe an operation that the wave check calls infeasible; at least say the tables use the no-dock model.
- 633,918 deliveries (18%) carry 0 cages and still cost a 15-minute stop; this follows "Every store receives one delivery each day" (brief 2.1, cited at `dcn/evaluate.py:131`), but it should be an `[ASSUMPTION]` in the definition because it is a material share of stops.
- Stock-out penalty is listed in `cost_parameters.csv` but never used in any cost (`STOCKOUT_PEN` appears only in `config.py:14` and `pipeline.py:78`), and the late penalty is 0 in the baseline (`finals.baseline.penalty` 0.0), because every store is served before the hard deadline or relayed.
  Say in the definition that both penalties are inactive by construction.
- Money columns are written as floats in `cost_parameters.csv` ("5500000.0"), while all other cost columns are integers; minor.
- Gzip headers carry the write time (`dcn/pipeline.py:80`, `:114`), so a rerun cannot be byte-compared with the shipped tables (review-02 T6 still open).

## 3. Code review (`dcn/*.py`, entry scripts)

### Bugs and silent failures

- `dcn/distances.py:15-17` and `:41-42`: a missing `road_cache.npz` silently falls back to map x 1.30 or 1.45; the run then reports placeholder numbers with only a phrase in `meta.distance_model`.
  This is the 02 persona's named red flag; now that the cache ships, raise instead.
- `dcn/world.py:101-103`: `transport_lp` returns `None` when infeasible, and `res.x` then raises `AttributeError` with no message.
- `dcn/routing.py:162`: `_binding` never tests `load > p.cap`, so a single store above 48 cages is tagged "load", not "violates limit" (review-02 D2, still open); harmless today (max 31 cages), but a silent feasibility hole.
- `dcn/search.py:17-29`: `greedy_assign` stops after three passes and may return an assignment above `hi` with no flag; it only feeds G1, but G1 is then scored on an infeasible assignment.
- `dcn/search.py:192`: EI's incumbent ignores `ok98`, so the search can spend evaluations improving on a candidate that fails the 98% constraint; the selection filters later (`dcn/pipeline.py:201-203`).
- `app.py:41-49`: a malformed POST raises inside the handler and the client gets no response; `app.py:56-62`: `NameError` if all eleven ports are taken.

### Labels that misstate what was computed

- `dcn/pipeline.py:215`: the key is `best_k8` but falls back to `kmin` when 8 is not in range; name it by its k.
- `dcn/pipeline.py:331-332`: `params.detour` and `params.detour_mountain` record the placeholder factors 1.30 and 1.45 although the run used the OSRM cache and `road_coef`; drop them when the cache exists.
- `dcn/pipeline.py:238-239`: the sweep takes the best of the whole 390-candidate pool, which is evaluated only for validation (`dcn/pipeline.py:183-186`); for k = 14 to 19 the sweep's candidate was never in the 40-step search log (`sweep[].cand` not in `log_bo`).
  The sweep, `k_star_plain` and the wave check therefore rest on about 390 full evaluations, not B = 40; label the sweep as validation in the demo and the definition.
- `dcn/evaluate.py:61`: the docstring hard-codes "0.671"; the template repeats it as text (`static/demo.template.html:640`) instead of reading `meta.fleet_quantile`.

### Dead code and duplication

- `dcn/pipeline.py:54`: `write_tables(world, model, hist, out)` never uses `model`.
- `dcn/search.py:162-163` and `FEATURE_NAMES` (`:166`) hard-code 55 and 125 instead of `C.REACH_KM` and `C.FAR_KM` (review-02 D3, still open).
- Count feasibility is written twice (`dcn/search.py:107-109`, `dcn/evaluate.py:41`).
- `dcn/config.py:48` recomputes `365 / 12` instead of `DAYS_MONTH`.
- `dcn/world.py:86`, `:99`, `:112` compute the scaled bounds three times.
- Decision-relevant constants outside `config.py`: the G1 factors 0.92, 1.08, 0.7124 and latitude 36 (`dcn/search.py:52-58`, `:69`), `k_nn=40` and the 400-store switch (`dcn/routing.py:54-57`), the `kmax` cap 20 (`dcn/pipeline.py:164`), the example-store cut 300 and 365 (`dcn/pipeline.py:384`).
- `dcn/pipeline.py:63-64` reaches `timedelta` through `demand.timedelta`; import it directly.
- `dcn/evaluate.py:74-89` keeps the pool in a module global; it lives only in the parent, so it is safe, but a context object passed to `territories` would remove the global the lead developer flags.

### Comment style

- Mostly terse and imperative, one-sentence docstrings; good.
- Stale: `dcn/config.py:39` "placeholder until the OSRM cache exists" (it exists); `dcn/distances.py:38` "the v0.1 placeholder factors" (version reference that will rot).
- Wordy: `dcn/config.py:29-30` (two-line rationale for `WAVES`, belongs in the definition); `dcn/world.py:30-31`; `dcn/routing.py:132-133` (two-sentence docstring).
- Misaligned inline comment at `dcn/config.py:51`; `dcn/pipeline.py:292` has `[ _spearman`; `dcn/pipeline.py:3-5` imports out of order (`gzip` after `sys`).
- Underscore-suffixed names to dodge shadowing (`s_`, `out_`, `sites_`, `open_`) appear in `world.py:80`, `search.py:87`, `search.py:143`, `pipeline.py:303`, `pipeline.py:340`; rename once.

## 4. Registry, demo and verification agreement

- `demo.html` embeds the full registry byte-for-byte (parsed JSON equal to `results/full/registry.json`), `generated` 2026-10-20T10:19:15.
- `demo.html` embeds the full `verification.json`, `generated` 10:25:44, `registry` 10:19:15, 23/23 passed; consistent.
- `results/reduced/verification.json` is stale: `generated` 2026-10-19T18:23:30 for registry 2026-10-19T18:22:44, while the shipped reduced registry is 2026-10-20T10:07:26 (20/20 passed on the old run).
  Rerun `verify.py` with the reduced profile or delete the file before hand-in.
- Numbers: full final saving 1,776.2 M KRW per month (90% interval 1,770.8 to 1,782.0), held-out 1,777.7 M; recommended k = 13; thinning check k* 13 (full) against 12 (reduced); wave check k* 13 to 14.
  The interval width (0.6% of the saving) comes from resampling days only, with one posterior draw of store rates (`dcn/demand.py:165`, `dcn/pipeline.py:22-38`); the statistician should judge whether it understates the uncertainty.
- The wave check moves k* from 13 to 14, and the thinning check from 13 to 12: both checks change the decision, which the definition must say plainly.

## 5. Packaging

- `code/.venv310/` (189 MB) and `code/.ruff_cache/` sit inside `code/`; `.gitignore` hides `.venv*/` from git, but a ZIP of the folder would include it and break the 200 MB limit.
  Build the ZIP from `git archive` or an explicit file list, and check its size.
- `code/results/` is 46 MB (full deliveries 24 MB); fine against 200 MB.

## Ranked findings

### Blockers

1. README has no expected run time for any command (brief 6.2); add full 709 s and reduced 85 s on the Spark with 16 workers, plus an estimate for a 4-core laptop (`code/README.md:8-12`, `meta.runtime_s`).
2. The outcome tables contradict the registry with no explanation: `deliveries` shows 100% on time against `history_ops.service` 0.976, and 27.9% of `vehicle_days` exceed 250 km or the shift; document the relay convention for the 230 far-store routes per day in the README and the definition (`dcn/pipeline.py:124-130`).

### Majors

3. README distance source lacks engine version, extract date and profile (`code/README.md:43`); copy them from `meta.distance_model`.
4. The shipped numbers come from Python 3.12.3 aarch64, the README claims 3.10.19; state both and whether a 3.10 x86 reduced run matched (`code/README.md:9`).
5. The sweep for k = 14 to 19, `k_star_plain` and both checks use whole-pool validation evaluations beyond B = 40; label them (`dcn/pipeline.py:183-186`, `:238`).
6. The in-browser solve differs by distances too (calibrated model, not OSRM cache), not only by 2-opt; say so on the page and in the README (`static/demo.template.html:601`).
7. Silent fallback to placeholder distances when the cache is missing; raise instead (`dcn/distances.py:41-42`).
8. `results/reduced/verification.json` is stale against the shipped reduced registry.
9. `code/.venv310/` inside `code/` would put a 189 MB folder into a naive ZIP.
10. `verify.py` needs `playwright` (not in requirements) and reports FAIL without it; the README should say so, and reproducing the shipped demo needs `verify.py` then `build_demo.py`.

### Minors

11. `departed_at` is 04:00 on every vehicle-day, contradicting the 30-dock wave check; state it.
12. Stock-out and late penalties are inactive by construction; state it.
13. 18% of deliveries carry 0 cages; mark as `[ASSUMPTION]`.
14. `app.py` port fallback undocumented, `NameError` when all ports are taken, no error response on a bad POST.
15. osrm README: no PBF download step, no extract date, coefficients refit on all pairs after the half-split test, `site_ids` never checked, prep order undocumented, `build_shapes.py` unlisted.
16. Unused `model` parameter in `write_tables`; duplicated 55/125, feasibility test, `365 / 12`, scaled bounds; decision constants outside `config.py`.
17. Mislabels: `best_k8` fallback, placeholder `detour` fields in `params`, "0.671" hard-coded in a docstring and the template.
18. `_binding` ignores load above capacity; `world.py:101` crashes without a message on an infeasible LP; `greedy_assign` may leave overloads.
19. Stale or wordy comments (`config.py:39`, `distances.py:38`, `config.py:29-30`), import order, `[ _spearman`, underscore-suffixed names.
20. Seed and sources live under "Known gaps"; layout table omits entry scripts, `static/`, `results/` and the cache size; Jeju exclusion unstated; demo does not check that the embedded verification belongs to the embedded registry; gzip mtime breaks byte comparison.
