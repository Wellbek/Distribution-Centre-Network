# Review 03 · 14 OR scientist (routing and location)

Reviewed on 2026-10-20 against Spark run 2 (`code/results/full/registry.json`, generated 2026-10-20T10:19:15, seed 437, B = 40, 7 / 28 / 14 days).
Read: `assignment.md` §3-4, lecture `ie437/md/ch05_surrogate_design_optimization.md` (A + gap + B), `code/dcn/*.py`, `code/verify.py`, `code/static/math.json`, the lectures block of `code/static/demo.template.html`, `code/README.md`, `planning/WORK_LOG.md`, `planning/DECISIONS.md` D-040..D-057, `planning/MIDTERM_BRAIN.md` §7-9.
All numbers below are read from the registry or recomputed from it with one-liners; no evaluation was rerun.

"What is your lower bound?" is still unanswered, and one modelling rule nobody checked turns out to carry most of the result.

## What holds up

- The gap decomposition is the lecture's identity, translated correctly to minimisation: `B = E(x̂) - G(x̂)`, `gap = G(x̂) - G(x*) ≤ 0`, `A = G(x*) - E(x*)`, and 845.4 - 317.8 - 411.7 = 115.9 M = the reported loss.
- The transportation LP is totally unimodular even with the lower bounds (a bipartite incidence matrix with interval right-hand sides), HiGHS returns a vertex, and `lp_frac = 0.0` is reported for every final network.
- The newsvendor fractile is right: 1 - (5.5 M / 30.42) / 550,000 = 0.671, sized per DC because spot hire is per DC, and `wquantile` is a proper left inverse of the weighted empirical CDF.
- The search protocol follows the brief: 13 G seeds + 27 EI picks = 40, random selection on the same pool with the same 13 seeds, and the whole-pool validation runs after both searches (`pipeline.py` lines 179-186).
- EI found the pool's best feasible candidate (7,447.5 M, cand 195) at step 18; the random median after 40 is 7,928.5 M and the random p10 is 7,502.1 M.
- Savings merges are checked against load, stops, km, deadline and shift (`routing.solve` lines 104-110), so the red flag "savings with no time-window check" does not apply.

## Blockers

### B1. The far-store rule carries most of the saving and was never checked

`routing.solve` cannot merge a store whose solo route breaks the 250 km or shift limit, so every store beyond about 125 km gets its own 48-cage truck plus a relay driver-day.
On the stored weekday routes, today's network runs 227 such routes (1.0 store and 1.9 cages each) out of 799 vehicles; the recommended network runs 94 out of 672, 87 of them from Jecheon to the east coast (150 vehicles for 500 stores).
The owned fleet differs by 842 - 713 = 129 vehicles (710 M a month) and relay by 1,248.5 - 517.0 = 731 M, which together are about 1.44 G of the 1,776 M saving.
Every one of these deliveries arrives before noon (latest arrival 10:01 today, 10:34 recommended), yet `evaluate.py` line 143 counts them as not on time, so the baseline's 97.7% worst-day service, and therefore its failing of the 98% target, comes entirely from this rule.
The departure-wave flip (k* 13 to 14) has the same cause: with 30 docks x 4 waves = 120 departures, Wonju's 157 routes give the baseline's 37 overflows and Jecheon's 150 give k = 13's 30 overflows.
The relay reversal (0 / 180,822 / 550,000 KRW) only reprices the second driver; the one-truck-per-store assumption stays in every row.
A real operator would put the 87 coast stores (about 180 cages) on a handful of multi-stop two-driver routes.
This is the case the brief singles out in §3.4: "A simplification that could reverse the conclusion and was not checked is the main thing this section penalises."
Required: a relay route type (two drivers, longer km and shift limits, multi-stop, priced per route), the sweep and the saving rerun with it, and the service metric split into "before noon" and "within route limits".

### B2. The k sweep cannot tell k = 10, 11, 12 and 13 apart

The sweep is the best of about 30 pool candidates per k, made by random 1-2 swaps to any of the 60 sites (`search.py` line 143, `new = rng.integers(J)`), which are not the "local moves between candidate sites" the brief asks for.
Going from the G1 seed to the best of those 30 gains 308, 794, 403, 389 and 728 M at k = 9-13 but only 4-94 M at k = 14-19, so search quality differs by k; the per-k optima are not converged.
The best of k = 10-13 lie within 145 M of each other (7,592.7 / 7,563.4 / 7,549.6 / 7,447.5), which is smaller than the gain one more batch of swaps gave at those k.
The k = 14 point opens one more DC than k = 13 yet owns 63 more vehicles (fleet 4,141.5 vs 3,795.0 M), and the 564 M jump from 13 to 14 looks like a weak k = 14 layout rather than an effect of k.
The routing heuristic has noise of the same size: the more constrained wave schedule comes out cheaper than the plain one, by 99.9 M at k = 10 (7,492.8 vs 7,592.7) and 70.6 M at k = 11, with fewer vehicles.
The day sample matters as much: the recommended network costs 7,447.5 M on 7 days and 7,606.8 M on 28 (+159 M; owned 690 vs 713).
On 28 days, the k = 11, 12 and 13 top-5 entries lie within 87 M of each other (7,689.7 / 7,693.5 / 7,606.8), and k = 10 was never re-scored.
Required: an E-based swap neighbourhood around the best evaluated layout of each k from 10 to 14 (as validation, labelled), all per-k bests re-scored on the 28 days, and k reported as a range unless the gap beats both the heuristic noise and the day noise.

## Majors

### M1. No measured routing accuracy where it matters

The only accuracy check is exact set partitioning on 7 stores (`verify.py` lines 105-136), drawn from the 60 stores nearest the DC with q ~ U(4, 12).
In that regime the answer is ceil(sum q / 48) vehicles, and the 25-stop, clock and shift limits never bind.
At full size the recommended weekday's binding census is shift 235, load 212, over-limit 94, geometry 53, km 36, stops 34 and clock 8.
There is no lower bound, no full-size reference, and no gap by k.
A free bound, max(ceil(sum q / 48), ceil(n / 25)) per DC, gives 432 vehicles against 672 used (56% apart), so a time-based bound is needed before it certifies anything.
`MIDTERM_BRAIN.md` §7.3 promised PyVRP at full size, lower bounds, the gap against territory size, and inter-route moves (relocate, swap, 2-opt*, route elimination); none of them is in `routing.py`, which has only intra-route 2-opt.
§7.1 says the lower level minimises "vehicles first and km second (lexicographic)", but Clarke-Wright with 2-opt minimises km and never tries to remove a route; the exact check uses a 10^4 weight per vehicle, so it scores against an objective the heuristic does not pursue.
The exact check also skips an infeasible MILP silently (`if res.status != 0: continue`), so "25 instances" can be fewer.
Persona questions 1-2 (the gap at n = 12 and at n = 1,000, and whether it changes with k) remain open.

### M2. The departure-wave check does not isolate the dock effect

Apart from B1, the check re-scores only the plain sweep's best candidate at each k, so k* = 14 rests on the weak k = 14 layout of B2.
Dock overflow is not priced; it only flips `ok98` (`pipeline.py` line 250), which mixes a dock limit with service.
Docks are sized from today's vehicles per store (D-054), and that count includes the 227 single-store trucks, so the dock count is itself inflated by B1.
"Does the simplification change the decision?" gets a yes here, but for the wrong reason.
A dock-count sweep, already listed under "Open", should come after B1 is fixed.

### M3. Only one of the two §3.4 checks tests a simplification of the reported model

The reported run is the full instance (D-047), so thinning is not a simplification inside it.
The thinning check also confounds thinning with a different pool: the reduced run builds its own G1 seeds and swaps.
It moves k* from 13 to 12, and the per-store km ratio (1.26 against the square-root rule's 2.24) shows that line-haul, not local tour length, dominates; that is worth a sentence, not a check.
Checks that are cheap from what exists: 7 versus 28 days (already +159 M and +23 vehicles on the recommended network), speed 30 km/h, and the far-store rule of B1.

### M4. Search reporting: honest protocol, but the reference rules are weak

61% of the pool fails 98% because swaps go to random sites, so random selection draws a feasible candidate only 26% of the time against EI's 81%; that widens the EI-versus-random gap.
A trivial rule, the lowest G1 first after the same 13 seeds, also reaches 7,447.5 M within 40 (at step 37, against EI's step 18).
Report it, because it shows what the GP adds: speed, not a better final answer at B = 40.
The sweep, the reversal's k*, the wave rows, the thinning rows and `pool_best` all use the 390-candidate validation, about 10 times B.
The WORK_LOG table row "k sweep, search days (M)" and the line "flat choice between 10 and 13" do not say so; label every such number "validation, whole pool".
There is a single EI seed; one or two more seeds would show whether step 18 is typical.

### M5. "G1-best" is not the G1 optimum, and G1 is not a p-median

In 12 of 13 k, a pool swap has a lower G1 than the "G1-best" seed (k = 11: 6,834 vs 6,718 M; k = 12: 6,941 vs 6,745 M).
The cause: `g1_best` optimises G1 under `greedy_assign`, while the pool's G1 values use the LP assignment (`build_pool` lines 147-150).
`g1_best` is greedy add plus two passes of swaps among the 12 nearest sites, with no bound; brain §9.1-9.2 promised an exact MILP and the LP relaxation as a bound on G.
G1 is a cost model (fixed + load-based fleet + line-haul + BHH local km), not a p-median objective; call it "G1, route-length approximation" and drop "G1-best" for "G1 local search seed".
Persona: "Is that a p-median or a capacitated facility location problem?" Currently it is neither.

### M6. R3: the numbers are right, the reading needs care

0.60 and 0.25 are computed on the 40 EI-chosen candidates, a range EI has already narrowed.
The within-k mean averages 8 groups of 3-10 points (k = 13 has 10, five groups have 3), and a 3-point Spearman can only be -1, -0.5, 0.5 or 1.
The whole pool (validation) gives 0.98 overall and 0.94 within k, inflated by infeasible layouts, and about 0.56 within k on the 98%-feasible candidates only.
Report n per k and both sets.
A and B are dominated by a level bias, since E/G averages 1.148 on the evaluated set.
Rescaling G by that ratio gives A = +632, B = -151 and gap = -365 M with the same loss of 116 M, because a scalar rescale cannot change the arg min.
So the brief's "rescale G by E/G" remedy cannot improve decision quality on its own; only a k-dependent or feature-dependent correction (the GP on E - G) can.
"x*" is the best evaluated candidate, not the true optimum; write "loss against the best evaluated" everywhere.
The cause named in the demo ("G ignores the clock ... so it under-rates large territories") reads a level bias as a ranking effect; the evidence for a clock effect would be E - G growing with territory size, which nobody has shown.

### M7. The service metric is misnamed

WORK_LOG line 187 says "97.6% before noon", but the 2.3% of deliveries counted as failures arrive before 10:35; they fail the km or shift limit, not the window.
Brief §3.1 asks for "the realised service level of every network you compare"; report the before-noon share and the within-limits share separately.

### M8. The demo's formulas do not match the code

- `lower_st` states km(r) ≤ 250 and return + 1/2 h ≤ 13:00 as hard constraints, while `lower_obj` charges c_relay |R^over|, a cost for routes that break them; state the relay route as an explicit recourse with its own limits.
- `lower_obj` drops the late penalty that E charges (`LATE_PEN` per arrival after 14:00, `evaluate.py` line 150), and the owned fleet n_j enters only through the spot term; say that n_j is given to the day problem.
- `upper` has only sum y_j = k; it lacks the 500-1,400 store bounds (through the LP), the 98% service requirement that `ok98` enforces in the ranking, and the fact that the assignment is re-solved inside E.
- `E` uses w_n without stating sum w_n = 1 (the code normalises, `evaluate.monthly` line 65).
- `ko` writes delta ~ GP(0, k), but `gp.py` standardises y, so the prior mean is the sample mean of the gap; `ei` writes f+, but the code uses the minimum posterior mean at evaluated points (`search.py` line 191); both are fine choices that should be stated as made.
- `bound` is labelled a bound but is the exact identity; the bound is A + B, valid because the gap ≤ 0 for the arg min of G over the evaluated set.
- `lp` shows d~_ij without its definition: road km + 3 (d - 55) beyond 55 km + 10^4 beyond 125 km (`reach_cost`); the LP therefore optimises a proxy, not E.

## Minors

1. LP duals exist (`price_hi`, `price_lo`) but are in cage-km of the proxy cost, not KRW, and are not reported anywhere; 7 of the 13 recommended DCs sit at the 500-store minimum with positive duals (for example 309.8 and 313.4), and Hanam sits at 1,400; the minimum bound shapes the design and deserves one sentence (persona checklist: "duals for binding DC capacities").
2. The 7-day quantile: owned fleet 690 (7 days) vs 713 (28 days) recommended and 820 vs 842 today, so the 0.671 quantile from 7 weighted points under-sizes by about 3%; this is the persona's "quantile stability with 7 and 28 days", answered by data already in the registry.
3. The saving's 90% band [1,771, 1,782] resamples days only; it excludes the routing error (±100 M, B2), the quantile (M3) and the far-store rule (B1), and an 11 M band on a figure that moves by 1 G with one modelling rule is false precision.
4. The recommendation is picked from the top 5 on the same 28 final days that `final_mean` is then reported on; the held-out days guard this, so say that the held-out figure is the unbiased one.
5. `code/README.md` "Known gaps": "the G remedy ... not in yet" is stale; D-052 is in `search.py` lines 30-61.
6. The demo's Q6 text "G ignores the clock and the 250 km limit" is stale since D-052 (G1 prices stores beyond 125 km, per the docstring at `search.py` line 44).
7. `demo.template.html` line 357 still says "placeholder road distances" in the no-saving branch; the run uses OSRM.
8. WORK_LOG line 165 calls the single-store routes "real geography ... and stays"; the geography is real, but routing each store alone is a model choice (B1).
9. Sweep rows k = 14 and k = 15 have identical fleet (4,141.5 M), relay (440.0 M) and `service_min` (0.9917678534677917) on different site sets (cand 217 and 247); probably the same far stores bind both, but check.
10. Mixed OSRM and model legs in `distances.territory` need not satisfy the triangle inequality; harmless for savings and 2-opt, but it weakens any bound built on the matrix.
11. G0 snaps k-means centres to sites by an assignment on squared degree distance (`g0_sites`); fine for a Data Team baseline, but it is map distance, so do not call it road-aware.

## Answers to my standing questions

1. The gap at n = 12 and at n = 1,000: not measured (only n = 7, in an easy regime; M1).
2. Does the gap change with k: not measured; the wave run hints at 70-100 M of noise at k = 10-11 (B2).
3. Lexicographic objective: claimed in the brain, not implemented (M1).
4. TU with lower bounds: yes, and integrality is confirmed by `lp_frac = 0` (holds up).
5. Days for a stable 0.67 quantile: 7 is short by about 3% of the fleet (minor 2).

## Priority for the next Spark run

1. A multi-stop relay route for stores beyond reach, then the saving, the sweep, the wave check and the service figures again (B1, M7).
2. An E-based swap neighbourhood per k for k = 10-14, re-scored on 28 days (B2).
3. A time-based vehicle bound and a reference solve on two or three real territories at small and large k (M1).
4. Label the validation-only numbers; add the G-ranking rule and a second EI seed (M4).
5. Fix the formula block and the stale text (M8, minors 5-8).
