# Review 02 · Implementation v0.1 (reduced run, 2026-10-19)

Artefact: `code/` v0.1, `code/results/reduced/registry.json` (generated 2026-10-19T13:46:33), `demo.html`.
Mode: six independent persona agents (no shared context, read-only) plus an independent verification script (`code/verify.py`).
Full findings per persona: `review-02/*.md`.

---

## 1. Verification (code/verify.py)

| Check | Result |
|---|---|
| World rebuilt from the seed, showcase day matches | PASS |
| Every store served exactly once, baseline and recommended | PASS (1,955/1,955) |
| Route limits recomputed from coordinates | PASS: 0 unflagged violations; 48 (baseline) and 25 (recommended) flagged over-limit routes, all single-store |
| Cost identity for all five final networks | PASS |
| Paired saving equals the difference of totals | PASS (532.3 M) |
| Assignment LP within bounds | PASS (100-280) |
| Deterministic evaluation | PASS |
| Heuristic against exact set partitioning, 25 instances of 7 stores | PASS: +0.08 vehicles on average (max 1), km -0.4% on average (max +1.9%) |
| In-browser engine equals Python without 2-opt | PASS: 13 vehicles both; 1,381.70 vs 1,381.64 km (0.004%, the demo stores coordinates rounded to 4 decimals) |
| `app.py` live solve | PASS after a fix: the startup line was not flushed, so a piped launcher hung (now `flush=True`) |

The OR agent measured +4.5% vehicles on 11-store exact instances (2 of 20 instances one vehicle over).

## 2. The verdict in one paragraph

The machinery is correct and fair (routing limits, identities, determinism, common days, budget protocol), but the conclusion is not yet earned.
All six agents independently found the same blocker: the relay charge for over-limit routes (D-019) produces 385 of the 532 M saving (72%), does not vary by day (so the 90% interval of ±3.6 M is an artefact), and decides k*.
Without it the cost is flat within 1% from k = 9 to 12.
The over-limit routes exist because the current network has no east-coast DC (a strawman under R5), and far stores are charged three times (own vehicle, fuel, relay).
The Examiner's estimate today: about 50/100 (R1 10, lower level 8, connection and search 10, balance 3, R2 6, evidence 6, code and demo 7, proposal 0-1).

## 3. Round table

- **Examiner, red team, CFO, operations, statistician agree** on the relay blocker; they differ only on the fix (price as line-haul plus route, as a satellite or second vehicle-day, or forbid the assignment).
  Resolution: model a far store as served by a second wave from a cross-dock (line-haul cost) and show a reversal row at relay 0 / 180k / 550k; fix the baseline with an east-coast DC.
- **Data team vs Examiner** on the search: the recommended network is the centre-of-gravity candidate (pool 71), found by the GP at step 37; a centre-of-gravity sweep over k would have found it in 13 evaluations.
  Resolution: say so honestly; build the pool from E-relevant generators, not only G1 neighbours; random as a band with replicates; re-score the top 5 on 28 days.
- **Operations vs plan** on what binds: the 13:00 shift end, not the noon deadline, is the tightest limit on 54 of 126 routes and is never labelled; no driver break fits.
  Resolution: label all five limits; put the legally required break inside the shift; revisit whether the shift or the window creates the trade-off once distances are real.
- **Statistician vs plan** on the prior: strength 14 is far too strong (moment estimate about 2); rates redrawn each day wash out parameter uncertainty; Poisson understates DC-level spread.
  Resolution: empirical Bayes prior, draw rates once per scenario, negative binomial, predictive check, stratified days, held-out dates disjoint from final dates.
- **TA vs developer** on reproducibility: unpinned numpy/scipy (registry made on 3.13), `run_full.py` never run, both run scripts overwrite `demo.html`, constants duplicated in the page.
  Resolution: pin, record versions in meta, params block in the registry, only the named profile builds the demo.
- **CEO, product, UX, store owner** on the demo: the answer is not a decision (keep 4, close 8, open 8), the live solve cannot fail (no vehicle limit), charts squashed, labels collide, contrast below 4.5:1, no store-level view (896 stores end up farther, 123 by more than 30 km).

## 4. Gap list (owner, severity, status)

| # | Gap | Owner | Sev. | Status |
|---|---|---|---|---|
| 1 | Relay charge drives saving and k*; far stores charged three times | Examiner, red team, CFO, ops | B | Open: cross-dock pricing + reversal row |
| 2 | Current network leaves the east coast uncovered (strawman) | Field, red team | B | Open: add an east-coast DC to the baseline |
| 3 | Saving interval covers only daily noise; fleet not resized in bootstrap | Statistician, CFO | M | Open |
| 4 | G uses greedy assignment, E the LP: G-vs-E gap partly an artefact; sweep blow-up at k 17-19 | Examiner | M | Open: one assignment for both; mark < 98% service infeasible |
| 5 | Search evidence: one random replicate; recommendation is the G0 candidate; runner-up never re-scored | Examiner, data team | M | Open |
| 6 | Lower level accuracy not reported by k; vehicle gap +4.5% at 11 stores; no route-elimination move; shift end unlabelled; no driver break | OR, ops | M | Open |
| 7 | Demand: prior 14 too strong; daily redraw of rates; Poisson vs overdispersion; weekday-only search days; overlapping held-out dates | Statistician | M | Open |
| 8 | Balance table and the two required checks (thinning, departure waves) absent | Examiner | M | Open |
| 9 | Reproducibility: pins, versions in meta, run_full timing, demo overwrite, params block | TA, developer | B | Open |
| 10 | Demo as a decision; live solve with vehicle limit; honest labels; chart fixes; contrast; store-level view | CEO, product, UX, store | M | Open |
| 11 | Rent as a province step function; lease exits; site names vs coordinates | Real estate | M | Open |
| 12 | k = 8 under-searched; finals show k = 7, not 8 | Strategy | M | Open |

Accepted as already good: the four statements analysis; comparison design (common days, same routing, held-out days with fixed fleet, honest reassigned-12 row); budget protocol (13 seeds + 27 = 40, same pool, logged); routing feasibility; offline demo.

## 5. Next

v0.2 should fix 1, 2, 9 first (they invalidate every number), then 4, 3, 7, 6, 5, then the demo (10) and the business items (11, 12); then review 03.
