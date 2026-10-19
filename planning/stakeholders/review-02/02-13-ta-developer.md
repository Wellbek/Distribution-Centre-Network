# Review 02 - TA reproducer (02) and lead developer (13) on code v0.1

Scope: brief sections 6, 6.2, 6.3, 9; `code/` (README, requirements, run scripts, build_demo, app, `dcn/*.py`, template), `demo.html`, `code/results/reduced/`.
Checks run: registry and table inspection, Python 3.10 grammar check of every `.py` (`ast.parse(feature_version=(3, 10))`, passes), one `routing.solve` on 200 stores (0.03 s), two edge-case solves, `python app.py` started briefly with two POSTs and then killed by PID, scan of `demo.html` for external URLs, cp1252 decode scan of text files.
Not run: `run_reduced.py`, `run_full.py`, `verify.py`.

## TA reproducer (02)

### T1 - blocker - The registry was produced by library versions that cannot be installed on Python 3.10

Evidence: the run used Python 3.13 with numpy 2.4.6 (`Requires-Python >=3.11`) and scipy 1.18.0 (`Requires-Python >=3.12`).
`requirements.txt:1-2` is `numpy>=1.24`, `scipy>=1.10`, so a 3.10 venv resolves numpy 2.2 and scipy 1.15, and a 3.12 venv resolves something else again.
NumPy does not promise identical `Generator` streams across versions, and scipy 1.15 rewrote L-BFGS-B (GP fit, `gp.py:33`) and has a different HiGHS (`evaluate.py:48`), so the EI picks and the whole search log can change.
Smallest fix: pin `numpy==2.2.6` and `scipy==1.15.3` (both have wheels for 3.10 to 3.13), re-run the reduced profile with them, and write `sys.version`, `numpy.__version__` and `scipy.__version__` into `registry.meta`.

### T2 - blocker - `run_full.py` has no run time and has never finished, so the three-commands requirement is not yet met

Evidence: README line 10 says only "run on a large machine"; brief 6.2 requires the expected run time of each command.
The reduced run took 276.6 s (`meta.runtime_s`) for 1,955 stores with territories of 100 to 280 stores.
The full profile has 5x the stores, territories of 500 to 1,400 stores (savings on 40-nearest pairs plus pure-Python 2-opt), `pool_per_k=30` against 14, and the same roughly 80 unique evaluations plus 5 x 28 and 2 x 14 final days, so it is likely hours, not minutes, on a TA laptop.
Smallest fix: time the full run once on the DGX, state machine and minutes in the README, and say which numbers only the full run produces.

### T3 - major - The command order in the README leaves `demo.html` showing whichever run finished last

Evidence: `run_full.py:9` and `run_reduced.py:9` both overwrite `../demo.html` (`build_demo.py:10`); the README order is install, full, reduced, so the TA ends with the reduced demo even if the definition quotes full-run numbers.
The template also hard-codes reduced-run text: "bounds scaled to the reduced instance" and "this reduced run keeps 1 store in 5" (`demo.template.html`, `renderCases` and `renderAbout`).
Smallest fix: let only the profile that the documents quote rebuild `demo.html` (or write `demo.full.html`), and take those phrases from `R.meta.profile`.

### T4 - major - Distances are a placeholder, and no distance cache exists in `code/`

Evidence: `geo.py:168-172` is map distance x 1.30 or 1.45; README line 37 says so; brief 2.5 and checklist item 6 require road values or a calibration against them, cached in `code/`.
Every number in `registry.json` will move once the cache lands, so any number copied into `problem-definition.md` now will drift.
Smallest fix: treat all v0.1 numbers as provisional, copy no number into a document until the cache exists, and give the cache's path and size in the README (TA question 5).

### T5 - minor - The demo app fails loudly in some cases and silently in others

Evidence: a POST without `stores` prints `KeyError: 'stores'` in the server log and the client gets no response (`curl` rc=52, `app.py:33-38`); the page then falls back to the JS engine silently.
If ports 8437 to 8447 are all taken, `server` is unbound and `app.py:51` raises `NameError`.
The URL print is not flushed when stdout is redirected, and it says `localhost` while binding `127.0.0.1`.
Smallest fix: wrap `do_POST` in a `try` that returns `400` with the message, raise a clear `SystemExit` after the port loop, and print `http://127.0.0.1:{port}` with `flush=True`.

### T6 - minor - Outputs are not byte-reproducible, and the ZIP would carry `__pycache__`

Evidence: `meta.generated` and `meta.runtime_s` (`pipeline.py:178`) and the gzip header mtime (`pipeline.py:66`) change on every run, so a TA cannot `diff` a re-run against the shipped registry or demo; `code/dcn/__pycache__/` exists and there is no `.gitignore`.
Smallest fix: write the timestamp and runtime to a separate `run_info.json`, use `gzip.GzipFile(..., mtime=0)`, and exclude `__pycache__` from the ZIP.

## Lead developer (13)

### D1 - major - The JS demo is a second source of truth for constants and rules

Evidence: `demo.template.html` repeats `1.45 : 1.30` (`roadKm`), `350` and `120000` (live daily cost), `14` (failure time), `max_km: 250`, the `2.2 / 0.25 / 15` binding thresholds, `DEF = {12, 15, 35, 48, 25, 4}`, `dep = 4.0, stop = 0.25` (`truckPos`), `a > 12` (day animation), and the text "0.671 quantile" and `"1.30"`.
It also invents a rule that Python does not have, `shift_end: Math.max(13, dep + 9)`, uses all pairs where Python uses 40-nearest pairs beyond 400 stores (`routing.py:51`), and leaves relay trucks out of its daily cost.
Smallest fix: put a `params` block in the registry (`dataclasses.asdict(routing.Params())` plus `FUEL_KM`, `LATE_PEN`, `SPOT_DAY`, `FAIL_AT`, `DETOUR*`, `FLEET_Q`) and have the JS read it; delete the `shift_end` rule or add it to `Params`.

### D2 - major - Feasibility failures are priced, not flagged, and the headline service level hides them

Evidence: a store that no route can reach in time stays as a singleton tagged "violates limit" and is charged one `SPOT_DAY` (`evaluate.py:90`).
The recommended network has 25 such routes a day (about 15% of routes) and the baseline 48 (about 28%), while `held_service_*` is 1.0, because `service` (`routing.py:120`) counts only arrivals before the deadline and ignores breaches of the 250 km and shift limits.
A load above capacity is tagged "load", not "violates limit": my solve with one store at 60 cages returned `(60.0, 'load')` (`routing.py:127-130`).
The baseline is evaluated with `assign=hist_assign`, which skips the capacity-bound check: its loads include 342 against `hi=280` and 81 against `lo=100`, and nothing in the registry says so.
Smallest fix: add `load > p.cap` to the `violates limit` test, report `over_limit_day` beside `service` in every summary and in the demo, and record `bounds_ok` for the baseline.

### D3 - major - Thresholds that drive the decision live outside `config.py`, and some are duplicated

Evidence: the reach thresholds `55`, `3`, `125`, `1e4` (`evaluate.py:32`) are repeated as `55` and `125` in `search.py:138` and `FEATURE_NAMES`.
Also outside config: the G1 constants `0.92`, `1.08`, `0.7124` and latitude `36` (`search.py:39-45`), `k_nn=40` and the `n <= 400` switch (`routing.py:48-51`), the `kmax` cap of `20` (`pipeline.py:92`), and `HIST_START` and `PLAN_START`.
The count-feasibility test is written twice (`search.feasible` and `evaluate.assign_lp:39`).
Smallest fix: move these into `config.py` under named constants, and have `assign_lp` call `search.feasible` (or the reverse).

### D4 - minor - Unused parameters and returns

Evidence: `STOCKOUT_PEN` never enters a cost and is only written to `cost_parameters.csv` (`config.py:13`, `pipeline.py:64`); `cap_price` (`evaluate.py:53`) is never read; `evaluate(p=...)` and `solve(improve=...)` are never passed; `times` in `buildDay` is dead; the variable `k8` holds the best result at `kmin` (`pipeline.py:116`).
Smallest fix: delete them, or use `STOCKOUT_PEN` once missed deliveries exist.

### D5 - minor - `run_search` and `assign_lp` can crash or misreport on solver failure

Evidence: any `res.status != 0` returns `None` (`evaluate.py:49`), and `evaluate` then reports the capacity-bound reason, which is wrong for a numerical or iteration-limit failure; `run_search` reads `e["total"]` without checking `feasible` (`search.py:150,169`), so this becomes a `KeyError`.
`z.argmax(1)` assumes an integral vertex without checking it.
Smallest fix: return `res.message` as the reason, `assert e["feasible"]` in `run_search`, and `assert np.allclose(z, z.round())`.

### D6 - minor - Comment style and pipeline readability

Evidence: most comments are noun phrases, not imperatives: "Road km, index 0 = DC" (`routing.py:23`), "Great-circle km, broadcasting" (`geo.py:161`), "Which limit stops this route..." (`routing.py:126`), "Savings for all pairs..." (`routing.py:49`).
Several functions use a first-line comment where the other functions have a docstring (`walk`, `reach_cost`, `features`).
The `[ASSUMPTION]` tag sits at the end of a 200-character line (`evaluate.py:90`).
`pipeline.run` is 150 lines, with the sweep's `min(...)` comprehension written twice inside the registry literal (`pipeline.py:199-201`).
Smallest fix: rewrite the comments as imperatives ("Build road km, DC at index 0"), make each function's first line a one-sentence docstring, and lift `sweep` into one helper.

## Already solid

- `demo.html` has no external resource; the only URL is the SVG namespace string, and it embeds the registry (377 KB).
- Paths are relative to `__file__` everywhere; the scripts work from any working directory; there is no argparse and no network at run time.
- Every `.py` file parses under the Python 3.10 grammar; all text files decode under cp1252 and the registry is ASCII JSON, so Windows defaults do not break `read_text`.
- Seeds are fixed and derived from `SEED = 437`; tie-breaking in savings is deterministic (`lexsort`); the same day sets are used for every candidate (common random numbers in practice).
- One small solve takes 0.03 s on 200 stores, well inside the 0.5 s target; `/api/solve` returns the Python result; the infeasible-k case is explained, not shown as valid.
- The reduced run took 4.6 minutes, inside the README's "about 6 minutes"; it writes every input table and one registry, and the demo labels precomputed numbers with their command.
