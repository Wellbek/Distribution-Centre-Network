# Review 03 · 17 Red team · Markdown audit

Frozen artefact: commit `c5cc0a3` (plus the untracked `code/osrm/build_shapes.py`), registries `code/results/full/registry.json` (generated 2026-10-20T10:19:15, Spark run 2) and `code/results/reduced/registry.json` (2026-10-20T10:07:26).
Method: read-only; grep, reading and small one-liners on the registries and the shipped tables; nothing rerun.
Brief line numbers refer to `assignment.md` v2.2 (`A:n`), the template (`T:n`) and the classification reference (`Ref:n`).

> "You built the world, you built the baseline, and you found a saving. Convince me that is not circular."
> After this audit my answer is: about 41% of the saving is a cost term the brief does not have, and the rest is concentrated in far stores that a baseline we built ourselves cannot reach.

## Ranked findings

### Blockers

1. **Over-limit deliveries are counted late although they arrive by noon, and our own tables contradict the reported service level.**
   `evaluate.py:143` sets `good = 0` for every stop on a route flagged `violates limit`, so those stores count as missed for the 98% rule.
   The shipped `deliveries.csv.gz` (full) has no `delivered_at` later than 12:00 in 3,502,822 rows, yet `history_ops.service` = 0.976.
   An examiner who recomputes service from `deliveries` gets 100%, not 97.6%.
   No markdown states the rule; `MIDTERM_BRAIN.md:276` even says service is 100% unless the fleet cannot cover.
   Fix: state the rule in the definition (or add an `on_time` flag column to `deliveries`), and report service both ways.
2. **The saving rests on the relay term, which is not one of the brief's cost terms.**
   The brief's objective is DC fixed, vehicle fixed, fuel, spot and service failures (`A:10`, `A:50`).
   Component split, baseline to recommended (final days, M KRW/month): fixed +55.5, fleet -709.5, fuel -395.4, spot +4.7, relay -731.5; relay is 41% of the 1,776 M saving.
   At relay 0 the saving is 1,045 M (`reversal[0]`); at 550,000 KRW it is 3,270 M.
   The documents record this only in `WORK_LOG.md:186` and `:194`; `DECISIONS.md:37` (D-027) still claims "k* = 12 at all three prices", which run 2 contradicts (13 / 13 / 12).
   Fix: a cost-component waterfall in the definition with relay as its own bar, and the relay reversal as a top row of the reversal table.
3. **The baseline was given the capacity bounds the brief exempts it from, and so lost its east-coast DC.**
   `A:71`: "The baseline ... is exempt from the capacity bounds you impose on new designs".
   D-044 (`DECISIONS.md:54`) places the current 12 by a capacitated p-median with 500-1,400 stores each and supersedes D-024 and D-028, which Review 02 adopted precisely because "a baseline that leaves 2.5% of stores beyond reach is a strawman under R5" (`DECISIONS.md:34`).
   `WORK_LOG.md:110` justifies the missing east-coast DC by the 500 minimum, the bound the baseline does not have.
   Result: 227 over-limit routes a day in the baseline (`finals.baseline.over_limit_day`), 1,248.5 M relay, worst-day service 97.7%.
   Rough upper bound (mine, not from the code): one far single-store route costs about 5.5 M vehicle + 3.15 M fuel (296 km median single-store route in `vehicle_days`) + 5.5 M relay = 14 M a month; 133 fewer such routes (227 to 94) is about 1.9 bn, the size of the whole saving.
   Fix: add a baseline variant with today's 12 plus an east-coast DC (or with the bound lifted), and decompose the saving into far stores (beyond 125 km) and the rest.
4. **R5 reversals are not run.**
   `A:189` asks under which assumptions (stop time, speed, DC fixed cost, distance model) the recommendation reverses; only the relay reversal exists (`registry.reversal`).
   `code/README.md:42` admits it; `MIDTERM_BRAIN.md:415` still plans seven one-way sweeps.
   Fix: run at least stop time, speed, DC fixed cost and docks with break-even values, sorted by margin.
5. **The reported recommendation fails our own required check.**
   The departure-wave check (D-011, a required balance-table check) moves k* from 13 to 14 (`waves.k_star_waves`), and the recommended k = 13 overflows the 30 docks by 30 departures a day.
   `WORK_LOG.md:192` calls the dock count "the first number to confirm", but nothing says whether we recommend 13 or 14.
   The brief penalises "a simplification that could reverse the conclusion" only when unchecked (`A:177`); here it was checked and did reverse, so the definition must state the decision rule we apply to that result.

### Majors

6. `code/README.md` gives no expected run time for any command; `A:246` and `T:109` require it (85 s and 709 s on the 16-worker Spark exist only in `WORK_LOG.md:171`).
7. Command order inverted against the brief: `A:224` lists install, full run, reduced run; `code/README.md:10` says run reduced first because the full run reads the reduced registry for the thinning check (`pipeline.py`, `other.exists()`); a grader following the brief gets `thinning: null` in the full registry.
8. Python version claim unsupported: `code/README.md:9` says "tested on Python 3.10.19" and D-029 (`DECISIONS.md:39`) says the run is under 3.10, but both registries record Python 3.12.3 on aarch64; no 3.10 or x86 reproduction is recorded.
9. `code/README.md:42` says "the G remedy ... not in yet" while D-052 (`DECISIONS.md:62`) is titled "The G remedy" and Accepted; one of them is wrong, and `T:105` needs a remedy section either way.
10. D-052's evidence (rank correlation 0.85 after the remedy) is not what run 2 measures: `r3.spearman` = 0.60 over evaluated candidates and 0.25 within k; the 0.85 was on run 1's overwritten registry and cannot be traced.
11. Saving interval overclaims precision: [1,771, 1,782] M is day noise under one posterior draw of rates per scenario set (`demand.sample_days`), one world seed and fixed assumptions; the red-team checklist item "world regenerated with two other seeds" (`MIDTERM_BRAIN.md:700`) is not done.
12. The recommended network still leaves 94 stores below 98% on time, with the worst store at 0% (`stores_view.below98_rec`, `worst_rec`); no markdown mentions it, and the store-owner persona will.
13. 28% of baseline history vehicle-days exceed 250 km (83,801 of 300,778 in `vehicle_days`) and returns run to 16:17; the brief's vehicle limit (`A:68`) is treated as soft and priced by a second driver, which does not lift a vehicle km limit; not stated anywhere.
14. Stock-out and late penalties are identically zero in every network (`penalty: 0.0` everywhere; `STOCKOUT_PEN` is written to `cost_parameters.csv` but never used): the brief's "service failures" term is present in the table and absent from E; the definition must say why.
15. DC fixed costs deviate from the 150 M default (`A:112`) without a stated check: sites are 132 / 157.5 / 180 M (`geo.site_cost_factor`), the candidate mean is 145.75 M (not the "national mean" of `config.py:9`), the current 12 average 158.4 M; open item 11 (`MIDTERM_BRAIN.md:696`, uniform 150 M check) is not done.
16. The ZIP allowlist builder claimed by D-001 and `MIDTERM_BRAIN.md:8` does not exist (`tools/` holds only `render_math.py`); `planning/` with the instructor-repo intelligence (`MIDTERM_BRAIN.md` Section 2) must never ship.
17. Proxy-only approach: `MIDTERM_BRAIN.md:677` says G0 (the Data Team's centre of gravity) is the proxy-only approach, the code's `finals.proxy_only` is `argmin G1` over the pool; `T:89` needs one definition.

### Minors

18. `code/results/reduced/verification.json` is stale (19 Oct, 1,955 stores, v0.2 world) while the reduced registry is from 20 Oct with 1,938 stores.
19. Fleet quantile 0.671 instead of the 2/3 default (`A:121`); the reason is in `config.py:36`, but `MIDTERM_BRAIN.md:33` presents it as equal to the default; state it as a deliberate change.
20. Held-out dates exclude only the final dates (`demand.sample_days(..., exclude=d_final)`), not the search dates; draws are independent, so the leak is small, but `A:13` says "days the search never saw".
21. Heuristic accuracy is measured on 7-store instances only (`verification.json`), while routes carry up to 25 stops; `MIDTERM_BRAIN.md:289-291` promised 14-store exact, PyVRP and a lower bound.
22. Template conflict: `T:11` and `Ref:86` prescribe the marker `N/A <em dash> reason` with the em dash character; the owner forbids the character; decide once (`N/A - reason`) and say nothing more.
23. The brief allows a 04:00-07:00 departure (`A:61`); E departs everyone at 04:00 with unlimited docks; this is legal but must be a balance-table row (it is in the plan, `MIDTERM_BRAIN.md:432`).

## 1. Brief versus our work

| Brief | Requirement | What we do | Problem | Fix |
|---|---|---|---|---|
| `A:10`, `A:50` | Five cost terms | Adds a sixth, relay (`evaluate.monthly`) | 41% of the saving; not a brief term | Name it a modelling choice with its reversal (blocker 2) |
| `A:50`, `A:62` | 98% of a day's deliveries before 12:00 | `ok98 = min over sampled days >= 0.98`; over-limit stops count as missed | Rule is tighter than the brief and invisible in tables | Blocker 1 |
| `A:61` | Leave between 04:00 and 07:00 | All leave 04:00 in E; waves only in check 1 | Check reverses k* | Blocker 5 |
| `A:34`, `A:61` | One delivery per store per day | Every store routed daily, zero orders included (D-031) | Complies | None |
| `A:68` | 25 stops, 250 km, 10 h shift | Merges respect them; single-store routes may break km and shift | Soft limit priced as relay | Major 13 |
| `A:71` | Baseline exempt from capacity bounds | Baseline placed under the bounds (D-044) | Removes the east-coast DC | Blocker 3 |
| `A:89` | Plausible current DCs, no strawman | Map-distance p-median | Plausible, but fails 98% on its own | State why a real chain would run below its own service rule |
| `A:112` | 150 M per DC | 132-180 M by region | No uniform check | Major 15 |
| `A:121` | 2/3 quantile | 0.671 | Unstated change | Minor 19 |
| `A:122` | 7 / 28 / 14 days | 7 / 28 / 14, stratified | Held-out not disjoint from search dates | Minor 20 |
| `A:123`, `A:166` | B = 40 incl. one G seed per k | 13 seeds + 27 EI; random 13 + 27 | Complies; log rows lack the "one fresh run" statement | Put the statement in the log header |
| `A:146` | Cost per solve and accuracy | 0.15 s per territory-day (D-047); exact on 7 stores | Accuracy sample small | Minor 21 |
| `A:177`, `A:189` | Two checks; reversal assumptions | Two checks; relay reversal only | R5 list missing | Blocker 4 |
| `A:185` | Lecture 5 remedy or why none | G1 aligned with LP and far stores | README says not in yet | Major 9 |
| `A:224`, `A:246` | Three commands, run times, seed, source | Seed and source yes; no times; order reversed | Majors 6, 7 |
| `A:104` | Source, version, extract date, profile stated | In `osrm/README.md` and registry `meta`; not in `code/README.md:43` | README lacks version and date | Add one line |
| `A:242` | `[ASSUMPTION]`, `TBD`, `N/A - reason`; three approaches | Not written yet (`problem-definition.md` missing) | Open | Draft |
| `T:50` | Upper-level constraints include the lease schedule | One-shot design (`A:49` allows it) | Must be stated as `N/A - reason` | One line in 2c |
| `T:109` | Run times and what reduced omits | Not in README | Major 6 | Add |

## 2. Our markdown versus code and results

### `code/README.md`

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 3 | Version v0.3, 2026-10-20 | Fine; run 2 is v0.3 | None |
| 9 | Tested on Python 3.10.19 | Registries say 3.12.3 aarch64 | Record a 3.10 run or say 3.12 |
| 10-11 | Run reduced first | Brief order is full then reduced | Make thinning independent of order, or say why |
| 6-12 | Three commands | No expected run times, no memory note | Add 85 s / 709 s (16 workers) and a laptop estimate |
| 20 | Static demo runs savings without 2-opt | Omits that it uses model distances, 4% off the cache (D-056) | Add |
| 25-38 | Layout | `build_demo.py`, `run_*.py`, `verify.py`, `osrm/build_shapes.py` missing | Add rows |
| 37 | G1 "p-median + route approximation" | G1 is greedy add plus swaps, not a solved p-median | Say "p-median objective, local search" |
| 42 | G remedy not in yet | D-052 says it is | Major 9 |
| 43 | Distance source line | No OSRM version or extract date | Add v6.0.0 and 2026-10-18T20:25:06Z |

### `code/osrm/README.md`

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 12 | About 4,000 calibration pairs | 3,959 in registry `meta`; fine | None |
| 20 | Car profile, ferries excluded | Consistent with D-042 | None |
| 38 | Builder takes 10-20 minutes | Measured 193 s and 188 s (`WORK_LOG.md:36`, `:91`) | Say about 3 minutes |
| - | No mention of `build_shapes.py` | New untracked file | Document or drop |

### `planning/MIDTERM_BRAIN.md` (v1.2, day 0; most of it is now stale)

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 3, 5 | Version 1.2; "nothing implemented yet" | v0.3 code and two Spark runs exist | Add a status block pointing to the registry |
| 7, 34, 187 | k in [8, 20]; "eight" is the minimum; k = 7 infeasible | 9,718 planning stores give k in [7, 19]; failure case is k = 6 (`cases.failure`) | Update |
| 28, 181-184 | Noon reach 50-88 km | Code uses `REACH_KM = 55` | Align |
| 35, 184 | Thinning breaks the window mechanism (reach 8 km) | Measured km per store ratio 1.26x, predicted 2.24x; k* 12 vs 13 | Record that the prior argument overstated it |
| 190 | Baseline DC 1.80 B, vehicles 2.65 B, fuel 0.5 B | Run 2: 1.90 B, 4.63 B, 1.49 B, plus relay 1.25 B | Replace with registry values |
| 270, 276 | Hard noon window; service 100% unless uncovered | Over-limit routes kept and counted missed | Blocker 1 |
| 286 | Or-opt, relocate, swap, 2-opt*, route elimination | Only intra-route 2-opt (`routing.two_opt`) | Update |
| 287 | numba | Not used (`requirements.txt`: numpy, scipy) | Remove |
| 289-291 | Exact on 14 stores, PyVRP, lower bound | 7 stores exact only | Minor 21 |
| 299 | Driver breaks omitted | `BREAK_H = 0.5` is modelled | Move to modelled |
| 311 | One evaluation about 30 s, 8 workers | About 15 s (D-047), 16 workers | Update |
| 329 | Upper level constraint max distance <= 125 km | Priced, not a constraint (D-019, D-052) | Update |
| 333, 340 | G1 exact MILP on H3 cells, HiGHS gap | Greedy plus swaps | Update |
| 341 | G2 continuous approximation | Folded into G1; no G2 | Rename |
| 346 | Pool 400-600, all coverage-feasible | 390, not coverage-filtered | Update |
| 351 | EI x PF | Not implemented | Remove or implement |
| 356 | Log has sites, G0, G2, components, wall time, seed | Log has step, cand, rule, E, G1, k, ei, ok98 | Align with `A:167` |
| 378 | Prior strength about 14 | 1.8-2.2 (`r2.prior_strength`) | Update |
| 411, 449, 687 | Hand-placed baseline; nearest-DC history rule | p-median baseline (D-044); capacitated history (D-045) | Update |
| 415-416 | Seven reversal sweeps; payback | Only relay | Blocker 4 |
| 427 | 1.4 M cached pairs, 15 MB | 1.1 M pairs, 5 MB | Update |
| 431-435 | Checks: 12:30 deadline, two assignment rules, spot cap, extra sites | None run | Mark `Not run` |
| 454-455 | 500 calibration pairs; arm64 unconfirmed | 3,959 pairs; arm64 confirmed (`LLM_USE.md:39`) | Update |
| 507, 549, 707-712 | Open `[DECIDE]` items | Answered by D-022 and D-034 | Close them |
| 509-530 | `analysis.py`, `numbers.py`, `tools/osrm/`, `tools/make_zip.py` | None exist; osrm is in `code/osrm/` | Update; Major 16 |
| 547 | Failure case k = 7 | k = 6 | Update |
| 666 | "this version (v1.1)" | Header says 1.2 | Fix |
| 677 | G0 is the proxy-only approach | Code uses argmin G1 | Major 17 |

### `planning/DECISIONS.md` (status and chain audit)

| Line | ID | Problem | Fix |
|---|---|---|---|
| 14 | D-004 Proposed | Implemented by D-022 | Accepted, see D-022 |
| 15 | D-005 "proposed (no-logo rule)" | Never resolved | Close |
| 17-20 | D-007 to D-010 Proposed | Accepted by D-034 (line 44) and in code | Accepted, see D-034 |
| 19 | D-009 hard window | Partly superseded by D-019/D-027 (over-limit routes allowed) | Add a row stating the exception |
| 27-28 | D-017, D-018 "Accepted (temporary)" | Superseded by D-047 and D-036 | Superseded |
| 29 | D-019 "Accepted (review)" | Superseded by D-023, then D-027 | Superseded |
| 30 | D-020 Accepted | Superseded by D-044 | Superseded |
| 33 | D-023 promises cross-dock pricing | D-027 chose a driver-day instead | Superseded by D-027 |
| 34, 38 | D-024 Proposed, D-028 Accepted | Both superseded by D-044, which contradicts their reason | Superseded; blocker 3 |
| 37 | D-027 "k* = 12 at all three prices" | Run 2: 13 / 13 / 12 | New row with run-2 evidence |
| 40 | D-030 prior about 2.3 store-days | Run 2: 1.8-2.2 | Fine within rounding; cite registry |
| 47 | D-037 Proposed | Superseded by D-056 | Superseded |
| 50 | D-040 "review after Kontur" | Reviewed in `WORK_LOG.md:99-103`, row not updated | New row |
| 59 | D-049 16 docks Accepted | Superseded by D-054 | Superseded |
| 62 | D-052 "0.85" | Not reproducible from run 2 | Major 10 |
| 7 | Status legend includes superseded | No row uses it although eight are superseded | Apply it |

### `planning/LLM_USE.md`

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 5 | Three discussions to be selected | None tagged yet; planned ones (`MIDTERM_BRAIN.md:659`) rely on a two-assignment-rules check that was never run | Tag three rows now, one with a calculation |
| 17 | Instructor material used only to prioritise | The brain reconstructs a grading guide from it (Section 2.5-2.7) | Keep out of ZIP; never echo in Section 7 |
| 38 | v0.2 "east-coast DC in the current network" | Reversed by D-044; no correction row | Add a correction row (append-only rule) |
| 39 | "the real run is pending on the Spark" | Done later; fine under append-only | None |
| 44 | `verify.py` 23/23 | Matches `verification.json` (full) | None |
| - | Review 03 agents | No row yet | Add when consolidated |

### `planning/WORK_LOG.md`

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 110 | No east-coast DC because Gangwon is below the 500 minimum | The baseline is exempt (`A:71`) | Blocker 3 |
| 148-157 | Run 1 full results | Identical to run 2 to the million (9,383; 7,607; 1,776 [1,771, 1,782]); run 1 registry overwritten, so unverifiable | Say they coincide or archive run 1 |
| 162 | Two sentences on one line | Formatting | Split |
| 165 | Baseline misses 98% because of about 111 over-limit routes | Those stores arrive by 12:00; counted missed by our rule | Blocker 1 |
| 171 | Python 3.12.3 | Contradicts `code/README.md:9` | Major 8 |
| 176-187 | Run 2 table | Matches the registries (checked: saving, waterfall, sweep, waves, relay reversal, thinning, R3, history) | None |
| 191 | Saving "mostly relocation and redrawn territories" | Relay is 731.5 M across both steps | Split by component |
| 194 | "saving positive at every price" | True, but drops 41% at relay 0 | Say so |

### `planning/stakeholders/README.md`

| Line | Statement | Problem | Fix |
|---|---|---|---|
| 40-41 | Reviews are `REVIEW-NN-<artefact>.md`; round 1 named | Round 2 exists, with a `review-02/` folder; round 3 uses `review-03/` | Document folder convention, list rounds |
| 45-52 | Gates on days 0, 4, 7, 9, 11, 13 | Reviews ran on day 0 and day 1 instead | Record actual gates |
| 57 | Independent agents through `ecc:council` and similar | Review 02 used general-purpose agents (`LLM_USE.md:37`) | Update |

## 3. Formatting rules

| Rule | Result |
|---|---|
| No em dash | None in any of our `.md`, `.py`, `.html`, `.csv` files, nor in `demo.html` or `MIDTERM_BRAIN.html`; only the brief files (`assignment.md`, template, reference, example) contain them; the template marker conflict is minor 22 |
| One sentence per line | Violations: `planning/WORK_LOG.md:162`; `planning/stakeholders/17-red-team/README.md:5`, `:7`, `:40`; `planning/stakeholders/REVIEW-02-v0.1.md:36-40` |
| No AI co-author in commits | All 17 commits by Wellbek; no `Co-Authored-By`, Claude, Anthropic or "Generated with" in any message; "LLM use" appears only as a file name in `c5cc0a3` and `44843b3` |

## 4. Exploits a sharp examiner would attack

| Exploit | Size in run 2 | Where our documents say it | Verdict |
|---|---|---|---|
| Relay pricing of over-limit routes | 731.5 M of 1,776 M saving; saving 1,045 M at relay 0 | `WORK_LOG.md:186`, `:194`; D-027 (stale) | Partly disclosed; must lead the reversal table |
| Over-limit routes counted late | Baseline service 97.7% instead of about 100% by arrival time | Nowhere | Undisclosed: blocker 1 |
| Baseline without an east-coast DC, bounds imposed on it | 227 over-limit routes a day, 1,248.5 M relay | `WORK_LOG.md:110`, `:165` as "real geography" | Disclosed as a fact, but the reason contradicts `A:71`: blocker 3 |
| Docks and one 04:00 departure | k* 13 to 14; recommended overflows 30 a day at 30 docks; docks derived from today's vehicles per store | `WORK_LOG.md:182`, `:192`; D-054 | Disclosed; decision rule missing: blocker 5 |
| Regional rents | Current 12 pay 1,900.5 M against 1,800 M at the default; best-12 saves 76.5 M on rent | `config.py:9` comment only | Undisclosed: major 15 |
| Single world, one rate draw | Interval width 11 M on 1,776 M | Nowhere | Overprecise: major 11 |
| G-versus-E after the remedy | Within-k Spearman 0.25, RMSE 1,283 M, loss 116 M | `WORK_LOG.md:184` | Disclosed; remedy claim untraceable: major 10 |
| Saving larger than the DC fixed costs removed | Recommended adds a DC (+55.5 M fixed) yet saves 1,776 M, 93% of today's whole DC fixed cost | Nowhere as an explanation | Red flag from my persona file; explain via fleet, fuel and relay |
| "Cut to eight" | Best k = 8 fails 98% (97.96%), 8,763 M | Registry only | Worth a sentence: k = 8 fails on service, not only on cost |

## 5. My checklist

- [ ] Saving decomposition with intervals: waterfall exists, no intervals per step, no split by cost component or by far stores.
- [ ] World regenerated with two other seeds: not done.
- [ ] Break-even table sorted by margin: only relay, and docks implicitly.
- [ ] Claim-to-number trace: WORK_LOG run-2 table traces cleanly; DECISIONS and the brain do not.
