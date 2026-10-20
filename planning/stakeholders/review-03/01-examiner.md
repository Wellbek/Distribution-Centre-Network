# Review 03 - 01 Examiner (course instructor and grader)

State reviewed: code v0.3, Spark run 2 (`code/results/full/registry.json`, generated 2026-10-20T10:19:15), `demo.html` built 10:28, `verify.json` 23/23.
`problem-definition.md` and `proposal.html` do not exist yet.
Line numbers for `assignment.md` and `problem-definition-template.md` are the file's own lines.
All numbers come from the registry unless another file is named; M = million KRW per month.

## 1. Verdict in five lines

The engine is honest and much stronger than in review 02: same `E` for the baseline and every candidate, a budgeted GP + EI search of exactly 40 that finds the pool's best (7,447.5 M) while random selection at the same budget reaches a median of 7,928 M, and two checks that were actually run.
As things stand I would grade about 46 of 100, because the two documents that carry 60 points of formulation, the balance table and the proposal are missing.
The largest threat to the result is not missing text: the far-store treatment creates 227 single-store trucks a day in the baseline and 94 in the recommendation, and my rough arithmetic puts that difference at about the size of the whole saving.
The demo labels those on-time deliveries as "late", so the claim "today's network misses 98%" is an artefact of a label, not of the clock.
Only one of the four reversal conditions the brief names (stop time, speed, DC fixed cost, distance model) has been run, and the README says so.

## 2. Compliance matrix

Status: met / partly / missing / contradicted.

### 2.1 Deliverables (assignment.md 11, 221-226, 291)

| Requirement (quote, line) | Status | Evidence | What to do |
|---|---|---|---|
| "`problem-definition.md` ... Sections 3.1-3.4 of this brief answered in full, the I/O schema, the evaluation log summary and your LLM review" (223) | missing | file absent | Write it on the template; see Section 4 below for the minimum content |
| "`code/` ... at most three commands (install, full run, reduced run) and no network access" (224) | met | `code/README.md:8-12`; `verify.json` "worker pool = one process", "deterministic evaluation" | Keep |
| "`demo.html` or a local app" with map, sweep, log, baseline comparison, live solve (225) | partly | `demo.html` 2.2 MB, 0 external tags (verify); live-solve fleet bug, see 2.6 | Fix the items in 2.6 |
| "`proposal.html` ... answering management's two questions" (226) | missing | file absent | Write it; see Section 4 |
| ZIP at most 200 MB (219) | met | `code/` without `.venv310` is about 53 MB (`results/` 46 MB, `data/` 6.3 MB) | Exclude `.venv310`, `.ruff_cache`, `__pycache__`, `planning/` from the ZIP |

### 2.2 Data, Section 2.5 tables and schema (assignment.md 81-104)

| Requirement (quote, line) | Status | Evidence | What to do |
|---|---|---|---|
| `stores` with `region` (province, district), `store_type`, `opened_on`, `closed_on`, `current_dc_id` (87) | met | `tables/stores.csv`: 10,000 rows, 568 openings, 282 closures | Keep |
| `demand_history` "last 12 months; stores opened during the year have short histories" (88) | met | `demand_history.csv.gz`; `r2.example` store ST00211 with 61 days | Keep |
| `dcs` with `lease_expires_on`, cost, bounds; "Place them plausibly" (89) | met | `dcs.csv` 12 rows, leases 2027-03 to 2031-06; sites by capacitated p-median (D-044) | State the p-median placement in Section 3 of the definition as the anti-strawman argument |
| `candidate_sites` 40-80 "including the 12 current sites ... higher fixed costs in the capital region" (90) | met | 60 sites, 132-180 M, mean 145.75 M | Say why the mean is 145.75 M and not the 150 M default (brief 108 asks for a reason) |
| `cost_parameters` "Finance's figures" (91) | partly | `cost_parameters.csv` has six rows; the relay driver-day (180,822 KRW), which carries 517 M of the recommended cost, is not in it | Add the relay price, the docks and the shift rule as rows |
| `deliveries`, `vehicle_days`, `spot_hires` "from your lower level on the current network" (92-94) | met | `history_ops.deliveries` 3,502,822; verify "outcome tables" | Say so in the definition, as 83 requires |
| "do not generate a table you never use" (83) | partly | stock-out penalty 500,000 is generated but no code path can produce a stock-out (`STOCKOUT_PEN` only in `pipeline.py:78`) | Mark it `N/A - spot trucks always cover` in the definition |
| "Give your own I/O schema" (96) | missing | no file | Template table, 54-57 |
| "State the source, version, extract date and vehicle profile. Cache every distance" (104) | met | `meta.distance_model`: OSRM v6.0.0 car profile, Geofabrik extract 2026-10-18T20:25:06Z, md5, 3,959 calibration pairs; `data/road_cache.npz` 5.0 MB | Put the calibration error on the held-out half into the definition |
| "car profile" versus trucks (70: "scale them to truck speeds and say so") | partly | durations are not used, speed is a flat 35 km/h, so this is fine, but it is not said | One sentence |

### 2.3 Section 2.7 tractability (assignment.md 127-134)

| Requirement | Status | Evidence | What to do |
|---|---|---|---|
| "say which [reduction] you used" (127) | partly | full 9,718 planning stores reported (D-047); reduced 1 in 5 as the check | State it; it is a strength |
| Thinning "you must say how you handled both" fixed cost and stop density (129-131) | met (in code) | `thinning.k_star_full` 13 vs `k_star_reduced` 12; `km_ratio_baseline` 1.26 vs `km_ratio_pred` 2.24 | Explain why km per store rises 1.26x and not 2.24x (stem legs from the DC dominate route km); this is a nice finding |
| "an exact solution belongs on small instances where you measure the heuristic's accuracy" (132) | partly | verify: 7 stores, 25 instances, km gap mean 0.6%, max 4.4% | Add one check on a real territory size (savings vs savings + 2-opt, or a lower bound) so question 4 ("does its error depend on the number of DCs") has an answer |

### 2.4 Formulation, Sections 3.1-3.4 (assignment.md 140-177)

| Requirement (quote, line) | Status | Evidence | What to do |
|---|---|---|---|
| Lower level "in the standard form ... variables, objective, constraints" (144) | partly | demo formula `tools/render_math.py:12-13` | Add decision variables, "each store on exactly one route", and the far-store exception; see the contradiction in 3.2 |
| "Decide how the delivery window enters: as a hard constraint ... or as penalties" (145) | contradicted | D-009 says hard; `routing.py:162-163` and `evaluate.py:141-146` let single-store routes break 250 km and charge a relay | Write "hard for every merge; a store that no route can reach within 250 km gets its own route with a relay driver, priced and flagged" |
| "report the realised service level of every network you compare" (145) | partly | `service_min` per sweep row; but see 3.1, the number is mislabelled | Report two numbers: share delivered before 12:00, and share served within the vehicle limits |
| "State the cost of one solve and the accuracy" (146) | partly | 0.17 s per territory day, about 15 s per evaluation (`WORK_LOG.md` v0.3, D-047), not in the registry | Write the timing into the registry so the definition can cite it |
| "what passes down ... and up ... how many lower-level solves" (153) | partly | `evaluate.py` docstrings; 13 x 7 = 91 territory solves per search evaluation | Write it in 2b |
| "where demand uncertainty enters" (154) | met (code) | `r2.sampled` 7,447.5 vs `r2.average_day` 7,373.3 M | Write it |
| "whether the store-to-DC assignment is part of the candidate ... or re-solved inside the evaluation, and why" (155) | met (code), missing (text) | transportation LP inside E (D-008), `lp_frac` 0.0 | The argument lives only in `DECISIONS.md`, which is not handed in |
| `evaluated_by` "separately from the dependencies" (156) | missing | no file | Write it |
| Upper level "in standard form. Say what is convex or linear" (162) | partly | `render_math.py:23` shows only sum y = k; capacity bounds, assignment and fleet policy are absent | Write the full model: y, x (assignment), bounds 500-1,400, fleet quantile; LP part convex, site choice combinatorial |
| Budget B, strategy, G, selection (163-164) | met | `meta.budget` 40 = 13 G1 seeds + 27 EI; pool of 390 with 7 summary features; GP on E - G | Keep |
| "Compare your selection rule with random selection at the same budget on the same pool" (165) | met | `curve_bo` end 7,448 vs `random_band.p50` 7,928 (p10 7,502, p90 7,939) | Keep, and cite the 2,000-replication band |
| "the reported search is one fresh run ... Say so in the log" (166) | partly | `pipeline.py:181-183` runs it once; nothing in `log_bo` says "fresh run" | Add a field or a sentence to the log |
| "Log every full evaluation" (167) | partly | `log_bo` and `log_random` are logged; the 390 validation evaluations behind the sweep are not logged as such | See 3.4 |
| Balance table with at least nine rows (171-175) | missing | no file | Write it; the "how you checked" column must not say "not checked" for the far-store and distance rows |
| "for at least two of them the check" (177) | met (in code) | departure waves: k* 13 -> 14 at 30 docks; thinning: k* 13 vs 12 | Both checks move k; the definition must say so and draw the consequence (Section 3.5) |

### 2.5 Required analysis R1-R5 (assignment.md 181-189)

| Requirement | Status | Evidence | What to do |
|---|---|---|---|
| R1 four statements placed at levels "and draw the consequence" (181) | partly | demo "The four voices" (`demo.template.html:444-446`) | Put the table in the definition, template 23-28 |
| R1 "every decision with a stable ID ... classification within a stated boundary" (181) | missing | no file | Write it |
| R2 conjugate model, calendar exposure, prior strength, short histories (183) | met (code) | `r2.prior_strength` 1.84-2.17 store-days by type, `r2.kappa` 8.13, `r2.example` | Explain why empirical Bayes gives so weak a prior and what that does to a 61-day store |
| R2 "Report the difference between sampled-day and average-day cost; if it is small, say why" (183) | met (number), missing (text) | 7,447.5 vs 7,373.3 M = 74 M (1.0%); expected counts 7,435.0; peak 849 vehicles vs 713 owned on 2027-09-13 | Split the 74 M into fleet sizing and spot; name the holiday eve as the chain-wide driver |
| R3 prediction quality and decision quality as two numbers (185) | met | Spearman 0.60 on the 40 evaluated (0.25 within k), R2 0.67; G-pick k = 11 loses 116 M | Also report the pool: my recomputation gives Spearman 0.977 over all 390 (0.81-0.99 within k); explain the range restriction |
| R3 "Name the cause ... apply one of Lecture 5's remedies" (185) | contradicted | D-052 says the system-knowledge remedy is applied; `code/README.md:42` says "the G remedy ... not in yet" | Pick one story; store G-without-remedy and G-with-remedy correlations in the registry so the before/after is reproducible |
| R4 executed search (187) | met | as 3.3 | Keep |
| R5 baseline "same E, the same sampled days and the same routing method" (189) | met | `finals.baseline` uses `evaluate()` on `d_final`; verify identities | Keep |
| R5 "Sweep the number of DCs and show total cost and its two components" (189) | partly | `sweep` 13 rows k = 7-19 with six components | Values come from the whole-pool validation, not the B = 40 run (3.4); show fixed vs operating as the two components |
| R5 uncertainty "over sampled days, and on held-out days" (189) | met | 1,776 M [1,771, 1,782] on 28 days; 1,778 M [1,771, 1,784] on 14 held-out days | Say the interval is day-sampling only; model uncertainty (relay price alone: 1,045 to 3,270 M) is wider |
| R5 reversal "stop time, speed, DC fixed cost, the distance model" (189) | missing (3 of 4) | `reversal` holds the relay price only; `code/README.md:42` | Run the four named reversals, at least on the top five and the k sweep |

### 2.6 Demo requirements (assignment.md 250-255)

| Requirement | Status | Evidence | What to do |
|---|---|---|---|
| "baseline and the recommended network on a plotted map ... points and lines" (252) | met | map view; straight lines are allowed by the brief | Keep straight lines but fix the legend (3.3) |
| "the number-of-DCs sweep with its two cost components, the evaluation log, and the G-versus-E comparison for every evaluated candidate" (252) | met | `#sweep`, `#step` log slider, `#fig-scatter` | Label the sweep as whole-pool validation |
| Live solve, reader changes "demand day, the delivery window, the stop time and the vehicle limits" (253) | partly | `demo.template.html:187-193`: day, deadline, stop, speed, capacity, stops, fleet; no 250 km slider | Add the km limit; it is the limit at the centre of the far-store question |
| Live solve gives a sensible normal case | contradicted | live DC Hanam has 1,400 stores and needs 72 vehicles (verify "JS engine"), but `lv-fleet` has max 40 and default 40 (`demo.template.html:193, 555`), and `:601` drops every route beyond 40 | Set the slider max and default from the territory's vehicle need; today the default solve shows about 30 uncovered routes |
| "a static page may use a simplified version if it states the difference" (253) | met | "in-browser engine (same savings rules, no 2-opt)"; verify JS = Python without 2-opt | Also state that the static page uses model distances, not the OSRM cache (D-056) |
| Normal, boundary, failure cases (254) | met | `cases`: k = 6 infeasible, Hanam at 1,400, seven DCs at 500, budget-one 12,993 M | Keep |
| "Label every precomputed number ... which command" (255) | met | run pill "precomputed · python run_full.py", KPI badges | Keep |

### 2.7 Code README (assignment.md 246)

| Requirement | Status | Evidence | What to do |
|---|---|---|---|
| "states the three commands, the expected run time of each, the seed, and the distance source" (246) | partly | commands and seed (`README.md:8-12, 43`); no run times; distance source without OSRM version and extract date | Add 85 s and 709 s on the Spark with 16 workers, and an estimate for a one-core laptop; add the `meta.distance_model` string |
| "say how it differs from the full run" (246) | partly | `README.md:42` one sentence | Add: 1,938 stores, k* 12 vs 13, saving 294 vs 1,776 M |
| Python 3.10+ fresh environment (224) | partly | README says tested on 3.10.19; reported run is 3.12.3 aarch64 (`meta.python`) | Rerun `run_reduced.py` once under 3.10 and record it |

### 2.8 Section 8 and template Section 7 (assignment.md 287; template 125-133)

| Requirement | Status | Evidence | What to do |
|---|---|---|---|
| "Record the tools used and their roles in the definition" (287) | missing | only `planning/LLM_USE.md`, not handed in | Header line of the definition |
| "three important discussions, including at least one in which you checked a suggestion with a calculation or a small experiment" (287) | missing (text), material exists | candidates: D-023/D-027 relay artefact (72% of the v0.1 saving), D-052 G1 Spearman 0.20 -> 0.85, D-031 zero-order stores | Pick three with the check and the final location |

## 3. Contradictions and claims of unimplemented work

### 3.1 Over-limit deliveries are counted as late although they arrive before noon (major, close to blocker)

`evaluate.py:143` sets on-time to 0 for any route whose binding is "violates limit".
On the recommended weekday all 94 such routes are single-store routes of 251-460 km, and their arrivals run from 07:35 to 10:34 (`show.recommended_weekday`).
On the baseline weekday the 227 such routes also have 0 arrivals after 12:00.
So "baseline worst-day service 97.7%, misses 98%" (`finals.baseline.service_min` 0.9766) is a statement about the 250 km limit, not about the clock that the brief defines (line 50: "at least 98% of a day's deliveries before 12:00").
The demo repeats the label at `demo.template.html:218, 814, 818` ("relay deliveries count as late").
Fix: report time-based service and limit compliance as two numbers, and stop calling these deliveries late.

### 3.2 The lower-level formulation contradicts the code

`render_math.py:13` states km(r) <= 250 as a constraint, while `render_math.py:12` prices |R^over| in the objective.
If the constraint held, R^over would be empty.
Write the exception into the model, or turn the 250 km limit into a priced soft constraint and say so in the window row of the balance table.

### 3.3 The demo promises a feature that does not exist

`demo.template.html:182` reads "lines are straight between stops (road geometry follows with OSRM)".
Nothing in `code/` draws road geometry, and the brief (215) forbids describing an unimplemented feature as done.
My judgement on the user's concern: straight lines are explicitly allowed (252), and every distance and time behind them is OSRM road km (`meta.distance_model`), so this is not a fidelity problem.
It becomes one only if the reader infers km from the drawing, so the legend should say "straight segments for display; km and times are road values from OSRM (median road/map ratio X)".
Drop "follows with OSRM" unless the geometry is shipped.

### 3.4 The sweep is not the reported search

`pipeline.py:186-188` evaluates the whole pool of 390 after the search, and `best_k` (`pipeline.py:210-212`) picks the sweep, `best12`, `best_k8`, `proxy_only` and the relay `k_star` from that pool.
For example the sweep's k = 14 point (8,012 M) appears nowhere in `log_bo`, whose two k = 14 rows are 8,088 and 17,074 M.
This is legitimate as validation, but the brief (166) says "Development runs are free; the reported search is one fresh run", and the sweep is presented next to `evals` counts from the B run.
Label it "sweep over the whole validated pool (390 evaluations), not the B = 40 search" everywhere, or build it from `log_bo` only.

### 3.5 Other stale or conflicting text

- `code/README.md:42` "the G remedy ... not in yet" against D-052 "The G remedy ... Accepted".
- `demo.template.html:357` "placeholder road distances" survives in the branch shown when the saving interval includes zero.
- `config.py:39` comment "Distances: placeholder until the OSRM cache exists" is stale.
- Both checks reverse k: waves move k* from 13 to 14 (`waves.k_star_waves`), thinning gives 12 (`thinning.k_star_reduced`), and the relay price of 550,000 gives 12 (`reversal[2].k_star`).
A recommendation of exactly "13 DCs" must therefore be written as "relocate and redraw; 12-14 DCs is a flat choice", which `WORK_LOG.md` "What it means" already says.

## 4. The two judged user concerns

### 4.1 Straight lines on the map

Allowed by the brief and not a scoring issue; the legend text is the only defect (3.3).
I would not spend time on road geometry before the definition exists.

### 4.2 About 700 trucks for 9,718 stores, of which about 94-99 serve one far store

The fleet size itself is plausible: the load bound is 22,277 cages a day / 48 = 464 vehicles (`r2.chain_hist` mean), the multi-stop routes on the recommended weekday carry 16.7 stores and 35.0 cages each (73% fill), and the census says shift (235 routes) and load (212) bind most.
That answers question 1 well; put the load bound in the definition as a sanity check.
The far stores are the problem.
They sit on the Gangwon east coast (centroid 37.64 N, 128.95 E); Gangneung Gujeong and Donghae Bukpyeong are candidates, but only about 100 stores lie within 70 km map distance of them, so the 500-store minimum makes a coastal DC infeasible and the LP must send them inland (87 of the 94 go to Jecheon).
Because any route that contains such a store already breaks 250 km, the savings merge (`routing.py:107-110`) can never combine two of them, so each gets its own truck.
A real operator would run a few multi-drop relay or cross-dock routes instead.
Rough cost of one singleton route-day: owned vehicle-day 180,822 + relay 180,822 + fuel about 306 km x 350 = 107,000, about 470,000 KRW, or about 14 M a month.
Baseline 227 vs recommended 94 singletons is a difference of 133 routes, about 1,900 M a month, which is the size of the 1,776 M saving (my estimate, not a registry number; the singletons carry 49.9% of baseline km and 30.3% of recommended km on the showcase weekday).
The relay reversal at 0 KRW still leaves 1,045 M, but it removes only the driver, not the vehicle or the fuel of the singleton artefact.
Smallest fix that earns the points: one check that lets far stores of one DC share multi-drop relay routes (merge ignoring the km cap for flagged stores, or a cross-dock stem leg), rerun baseline and top five, and report whether the saving and k survive; put it as a row of the balance table.
Without it, the examiner's red flag "a baseline that is placed or routed worse than the candidates" applies, because the baseline is routed by a rule that punishes its specific geography.

## 5. Estimated marks as things stand (rubric, assignment.md 265-274)

| Criterion | Points | Now | Reason | Reachable with definition, proposal and the fixes |
|---|---:|---:|---|---:|
| Problem structure, data and I/O (R1) | 15 | 5 | tables faithful and generated from a seed; no decisions, IDs, classification or I/O schema | 13 |
| Lower level (3.1) | 15 | 7 | engine, limits, 7-store exact check; formula contradicts code; cost per solve not cited | 12 |
| Connection, upper level, search (3.2, 3.3, R4) | 15 | 9 | search, random band and log are strong; upper standard form incomplete; assignment argument not handed in | 13 |
| Fidelity-computation balance (3.4) | 15 | 5 | two checks run, no table, no argument, far-store and distance rows unchecked | 12 |
| Demand (R2) | 10 | 6 | model and numbers present; explanation only in the demo | 9 |
| Evidence (R3, R5) | 15 | 8 | both qualities, baseline, sweep, held-out interval; 3 of 4 reversals missing; far-store artefact | 12 |
| Code and demo (6.2, 6.3) | 10 | 6 | three commands, verify 23/23; README run times missing; live fleet default broken; stale legend | 9 |
| Proposal and LLM review (6.4, Section 8) | 5 | 0 | both missing | 4 |
| Total | 100 | 46 | | 84 |

## 6. What `problem-definition.md` and `proposal.html` must contain (do not omit)

- Header per template 5-9, with the summary naming 13 DCs, 1,776 M [1,771, 1,782] and the far-store or dock assumption as the simplification that matters most.
- Four-statement table (template 23-28): Strategy = a decision proposal (k = 8, `finals.best_k8` 8,763 M); Delivery Operations = an evaluation claim; Data Team = a method (G0); Field Manager = a model-validity claim about distance; only the first two meet on the E scale.
- Decision IDs (k, sites, assignment, fleet, daily routes), dependencies as `parent → child: what changes`, `evaluated_by: daily-routing`, classification table with evidence.
- Standard forms for 2a, 2b, 2c, the I/O schema and the component table; hard vs priced limits stated once.
- The full balance table with at least nine rows and the waves, thinning, relay and far-store checks in the last column; "Not run" where true.
- Section 5 cases, prediction vs decision quality (both the 40 and the 390), the log, held-out days.
- Three LLM discussions with the check (D-023/D-027, D-052, D-031 are the best candidates).
- Proposal: both questions answered, the waterfall (redraw -630, move sites -1,059, 13th DC -87 M), reversal conditions, what to measure first (docks, far-store operation), and "demonstrated in a fictional instance" vs "needs real data" separated.

## 7. Ranked findings

### Blockers

1. `problem-definition.md` is missing: it carries R1, 3.1-3.4, the I/O schema and the LLM review, about 60 of 100 points (assignment.md 223, 267-271).
2. The far-store singleton rule may produce the whole saving: 227 vs 94 single-store routes a day, roughly 1,900 M of cost difference against a 1,776 M saving (my estimate); run a multi-drop or cross-dock check before any number goes into the proposal (Section 4.2).
3. `proposal.html` is missing (assignment.md 226, 259).

### Majors

4. Over-limit deliveries arrive 07:35-10:34 but are counted late; "today misses 98%" is a label artefact; report time-based service and limit compliance separately (`evaluate.py:143`).
5. Three of the four named reversal conditions (stop time, speed, DC fixed cost, distance model) are not run (assignment.md 189; `code/README.md:42`).
6. The live solve's "vehicles available" slider caps at 40 for a 72-vehicle territory, so the default normal case drops about 30 routes (`demo.template.html:193, 601`).
7. The lower-level formula states km <= 250 as hard while the objective prices violations (`render_math.py:12-13`); the window row must say which.
8. The sweep, `best12`, `proxy_only` and relay `k_star` come from 390 validation evaluations, not the B = 40 run; label them (`pipeline.py:186-212`).
9. README and DECISIONS disagree on whether the G remedy is in (`README.md:42` vs D-052); the before/after correlation is not in the registry.
10. Both checks and the relay reversal move k (14, 12, 12); the recommendation must be phrased as a range with the sites as the robust part.

### Minors

11. README lacks run times, the OSRM version and extract date, and a 3.10 rerun of the reported profile (assignment.md 246).
12. Legend "road geometry follows with OSRM" describes an unimplemented feature (`demo.template.html:182`); stale "placeholder road distances" at `:357` and `config.py:39`.
13. Relay price, docks and shift rule are not in `cost_parameters.csv`; stock-out penalty is generated but unusable.
14. No 250 km slider in the live solve, although km is the limit at the centre of the far-store question.
15. Heuristic accuracy is measured on 7-store instances only; add one territory-size comparison to answer whether the error depends on k.
16. The search log does not state that it is one fresh run of exactly B (assignment.md 166).
17. The 90% saving interval is only 0.6% wide; say it reflects day sampling only and set it beside the 1,045-3,270 M relay range.
