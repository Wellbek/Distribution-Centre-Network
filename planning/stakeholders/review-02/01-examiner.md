# Review 02 - Examiner (v0.1, 2026-10-19)

Grader's reading of v0.1 against assignment.md section 7 and the twelve things in "At a glance".
All numbers are from `code/results/reduced/registry.json` (reduced run, 1,955 planning stores, seed 437) unless a file and line are named.
Penalty-free figures below come from subtracting a component after the fact, not from a re-run, and are marked as such.

## Findings

### F1 - Blocker: the saving and the choice of k are set by the relay charge, not by routing

- Evidence: `evaluate.py:90` charges 550k KRW per over-limit route per day, on top of the vehicle and fuel that route already costs.
- Baseline penalty 803.0 M of 2,533.9 M per month (48 over-limit routes every day, the same on all 28 final days); recommended 418.2 M (25 per day).
- So 384.8 M of the 532.3 M saving (72%) is this assumed charge.
- With the penalty subtracted (post hoc), the saving falls to about 148 M, and the sweep minimum flattens: k = 9, 11, 12 come to 1,533, 1,531 and 1,521 M, within 0.8% of each other.
- The penalty is deterministic, so the 90% interval [528.7, 535.8] M (held-out [529.5, 536.8] M) is ±0.7% and says nothing about the assumption that drives it.
- This confirms the author's known issue and makes it worse: as the numbers stand, they do not support "12 DCs at these sites".
- Criterion: Evidence R3/R5 (15) and Balance 3.4 (15); about 8-10 points at stake.
- Smallest fix: price an over-limit store as what it costs in your world (a second vehicle-day at 180k, or a satellite or cross-dock row), run the relay price at 0 / 180k / 550k as a reversal row, and report the saving with the penalty split out.

### F2 - Major: G and E use different assignments, so the surrogate learns a gap that its own features cannot see

- Evidence: `search.py:10-28`, where `greedy_assign` caps only the maximum, against `evaluate.py:36-53`, where the LP enforces 100 ≤ load ≤ 280.
- The features (`search.py:131`) are computed on the greedy assignment, not the one E routes.
- The recommended network has 8 of 12 DCs on a bound (loads 280, 100, 132, 205, 280, 280, 126, 149, 100, 103, 100, 100), yet `cases.boundary_dc` lists only the 3 DCs at the maximum.
- The k = 17-19 blow-up (5.4-9.2 B, service 96.5% at k = 18-19, below the 98% requirement but still shown as a cost) comes from E forcing 100 stores into sparse sites that G1 never had to fill.
- G1 has R² = -1.30, Spearman 0.48 and RMSE 3.7 B, and it picks k = 8, losing 665 M.
- The cause is not named: it is the assignment (the brief's own warning in section 3.2) plus the relay charge, not the clock.
- Criterion: Connection and search (15), R3; about 4-5 points.
- Smallest fix: compute G1 and the features on the same capacitated LP, report the LP duals (`cap_price`, already computed and then dropped), and mark candidates under 98% service as infeasible in the sweep.

### F3 - Major: the evidence for the search is one draw, and the recommendation is the Data Team's centre of gravity

- Evidence: the recommendation is pool[71], origin "G0 centre of gravity", found at step 37.
- The G1 seed for k = 12 costs 2,671 M; one G0 candidate beats every G1 seed.
- BO best 1,939 M against random 2,052 M: one run each, no band, and 13 of the 40 evaluations are shared seeds.
- Only 63 of 182 pool candidates were ever evaluated; whether 1,939 M is the pool optimum is unknown.
- The pick is the lowest noisy value over 7 days, and its runner-up (k = 13, 1,958 M, 1% worse) was never re-scored on 28 days.
- Criterion: Connection and search R4 (15) and the four statements R1; about 4 points.
- Smallest fix: evaluate the whole pool once as a labelled validation (feasible: 182 candidates), give best-of-random as an exact curve with a band, re-score the top 5 on 28 days, and say plainly what it means that G0 won.

### F4 - Major: the lower level has no measured accuracy and no measured cost per solve

- Evidence: `routing.py` has savings plus intra-route 2-opt only, with no relocate, no exchange and no route elimination.
- Vehicles are about 45% of E (fleet 891 of 2,002 M), so an error in the vehicle count goes straight into the decision.
- There is no exact check, no PyVRP check and no bound in code or registry (the plan has these at MIDTERM_BRAIN 7.3, lines 289-292), and no time per solve is reported.
- Also: on-time is 100% by construction (hard window at merge, `routing.py:101`), and over-limit routes are counted as on time (`routing.py:120`).
- Stores with 0 cages ordered are still given a 15-minute stop (`routing.py:86`); I estimate roughly 10% of stops (speculation, not counted).
- Criterion: Lower level 3.1 (15); about 5 points.
- Smallest fix: run the set-partitioning MILP on 10-14-store instances, give the gap against the vehicle lower bound split by k, give seconds per DC-day, and report service as "hard by construction" next to the over-limit count.

### F5 - Major: the demand model is fitted but sampled carelessly, and the gap analysis inherits that

- Evidence: all 7 search days are weekdays (`search_days`), about a 1-in-10 chance under unstratified `rng.choice` (`demand.py:134`), so the fleet quantile never saw a weekend or holiday.
- Sampled, expected-count and average-day costs are 1,938.8, 1,933.4 and 1,928.1 M (gaps 0.3% and 0.5%), measured on those weekday-only days.
- The peak day (186 vehicles against 158 owned) is the only calendar evidence.
- λ is redrawn for every day (`demand.py:141`), so parameter uncertainty is independent across days instead of shared.
- Prior strength is fixed at 14 (`config.py:37`), not estimated as the plan says (MIDTERM_BRAIN line 378).
- The store-day overdispersion in the generator (`demand.py:73`) is left unmodelled, with no posterior predictive check, and short-history behaviour is one example store.
- Criterion: Demand R2 (10); about 3-4 points.
- Smallest fix: stratify the 7 days by calendar class, draw λ once per scenario, estimate b by empirical Bayes, add a check that replicates the weekly profile, and plot posterior means against history length.

### F6 - Major: the fidelity-computation table and its two checks do not exist yet; thinning is the unchecked row

- Evidence: README line 37 lists them as missing.
- The plan's own arithmetic (MIDTERM_BRAIN line 184) says option (i) thinning "breaks the window mechanism outside cities", and v0.1 uses exactly option (i) with no denser sub-instance check.
- All vehicles leave at 04:00 (`config.py:22`); D-011 makes the departure-wave check mandatory, and it has not been run.
- Thinning also moved the feasible range to k = 7..19 (n = 1,955), against "8 is the minimum" (MIDTERM_BRAIN line 187).
- The finals hold `best_k7`, not the k = 8 that Strategy & Planning proposed.
- Criterion: Balance 3.4 (15); about 10 points at stake today.
- Smallest fix: write the table, run (a) a denser sub-instance or aggregated stops for one region and (b) departure waves on the top 3, and say whether k* or the ranking moves.

### F7 - Minor: the sweep confounds k with search effort, and the outcome tables are missing

- Evidence: `sweep.evals` per k is 3, 2, 2, 4, 7, 5, 4, 4, 2, 3, 1, 1, 2, and the sweep is scored on 7 search days, not 28.
- The `deliveries`, `vehicle_days` and `spot_hires` tables are not generated (`pipeline.py:41`).
- `cases.budget_one` is just whichever seed comes first (k = 7, 5.7 B), not a boundary case anyone chose.
- Criterion: R1 data (15) and R5; about 3 points.
- Smallest fix: re-score the G-best and E-best per k on 28 days with the components, generate the three tables from the baseline run, and choose the B = 1 case on purpose.

## What is genuinely good

- The four statements are placed at four levels, and the consequence is drawn (MIDTERM_BRAIN section 5): the centre-of-gravity claim is correctly limited to its own criterion, and the barrier is a validity claim.
- Common random numbers, the baseline routed by the same code with its historical nearest-DC assignment and exempt from the bounds, a held-out set scored with the fleet fixed in advance (`pipeline.py:126-128`), and "re-assigned 12" isolating the assignment effect (+9.5 M, honestly worse): this is the right design for identical conditions.
- The budget protocol matches section 3.3 exactly: 13 seeds plus 27 picks equals 40, random runs on the same pool with the same seeds, every evaluation is logged with its rule, the GP models the gap on features rather than coordinates, and the failure case (k = 6) is explained, not shown as valid.

## What I would grade this today and why

As v0.1 stands, I would give roughly 50 of 100.
R1 gets 10/15: strong statements and decisions, but no outcome tables.
The lower level gets 8/15: standard form and hard window are stated, accuracy and cost per solve are missing.
Connection and search get 10/15: the protocol is correct, but there is one random draw and the G-E assignment mismatch.
Balance gets 3/15: the table is planned, nothing is checked, and thinning is unchecked.
R2 gets 6/10: a correct conjugate model with exposure, but weekday-only sampling and a fixed prior.
Evidence gets 6/15: both G-E qualities and held-out intervals are present, but the saving is mostly an assumption and there are no reversal conditions or remedy.
Code and demo get 7/10: they reproduce and show the results, but the live solve has no 2-opt in the browser.
Proposal and LLM review get 0-1/5: not yet delivered.
The single highest-value move is F1: once the saving is priced honestly and given a reversal row, the evidence and balance criteria (30 points) become gradeable.
