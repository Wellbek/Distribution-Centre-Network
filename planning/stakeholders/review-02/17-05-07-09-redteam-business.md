# Review 02 - red team, strategy, data team, real estate (v0.1 reduced run)

Scope: `code/results/reduced/registry.json` (seed 437, 1,955 planning stores, bounds 100-280, k = 7..19, B = 40), `code/dcn/*.py`, `planning/DECISIONS.md`, brain sections 5, 11, 12, 14.
All money is KRW per month on the reduced instance (fixed costs x 0.2).
Numbers below were read from the registry or recomputed from its store and site coordinates; nothing was re-run.

## 17 Red team - is the 532 M saving real? (ranked by damage)

### R1 (critical) - the saving is mostly the relay penalty on stores the baseline cannot reach

Evidence: baseline penalty 803.0 M versus recommended 418.2 M, so 384.8 M of the 532.3 M saving (72%) is the D-019 relay charge.
That charge is exactly 48 versus 25 over-limit routes per day x 550k x 30.4 days, constant on every day.
Each over-limit route is a single store more than 125 road km from its DC (savings can never merge it), so it also carries a dedicated vehicle and about 300 km of fuel: roughly 25 M per store per month in all.
48 such stores make up about 1.2 B of the 2,534 M baseline; the 23 removed ones (about 575 M) explain the whole saving.
Fleet (82.5 M), fuel (47.0 M) and rent (19.8 M) are the only other components, and the fleet and fuel deltas are largely the same stores.
The relay was introduced in a development run because a hard filter emptied k = 7-11 (D-019), not from Finance's figures, and it is charged on top of the vehicle that already drives the route.
Smallest fix: report the saving with the relay set to 0, to the stock-out penalty (500k) and to the D-019 value, and add a "saving excluding over-limit stores" row; if it survives at 0 the claim stands.

### R2 (critical) - the baseline is infeasible by construction, so it is a strawman under R5

Evidence: 48 planning stores are beyond 125 road km from every current DC, yet 0 are beyond 125 km from the nearest of the 72 sites.
35 of the 48 belong to Wonju Munmak (the Gangwon east coast: Gangneung, Sokcho, Donghae, Samcheok); the rest are Chilgok 5, Gimhae 4, Gwangju 3, Yangju 1.
A chain grown over decades would not serve 2.4% of its demand with routes that break its own 250 km limit every day; it would have an east-coast DC or a cross-dock.
`reassigned12` (2,543.5 M) is no better than history, so the problem is placement, not territories: the historical-assignment argument is not where the saving comes from.
Smallest fix: make the baseline feasible (add a Gangneung-Donghae DC or a priced cross-dock in `geo.CURRENT_DCS`), or state that the reported saving is "closing a coverage hole" and size it separately.

### R3 (high) - a saving larger than the whole fixed-cost budget, at the same k

Evidence: saving 532 M against 370.5 M of baseline DC fixed cost, with k unchanged at 12 and fixed cost down only 19.8 M (21% of total cost removed by moving sites).
This is the persona's first red flag, and the brief's "convince me it is not circular" applies directly: the world (rural 10% background, 1.45 Gangwon detour), the baseline and the penalty are all ours.
Smallest fix: one-line saving waterfall (baseline -> reassigned12 -> best 12 -> best k) in the registry and on the demo, with the relay and over-limit share shown as its own bar.

### R4 (high) - one world seed and a deterministic interval

Evidence: `C.SEED = 437` for stores, DCs and history; the final CI [528.7, 535.8] and held-out CI [529.5, 536.8] are narrow because the dominant term (over-limit count) does not vary with demand.
Held-out days differ only in demand draws (seed + 13), on the same world, so "held-out 533 M" adds no evidence about the claim that matters.
Search days are 7 of 7 weekdays (registry `search_days`), so the owned fleet and the selection never saw a weekend.
Smallest fix: regenerate the world for 2 more seeds and report k* and the saving per seed; stratify the 7 search days by weekday and weekend.

### R5 (medium) - the GP-versus-random win is one replicate, and caching is not the problem

Evidence: GP best 1,938.8 M found at step 37 with EI 17.8 M; random best 2,052.1 M; both bests are G0 candidates, and the gap is one lucky pick of candidate 71.
The shared cache does not bias the numbers (E is deterministic given sites and days) and the 13 G1 seeds are shared by design, so 17 of 40 evaluations overlap.
Smallest fix: 20 random replicates (pure cache lookups after an exhaustive pool evaluation on the DGX) and report the GP's rank in that band; state in the log that the cache is shared.

## 05 Head of Strategy - was eight treated fairly?

### S1 (high) - k = 8 got 2 evaluations, k = 11 got 7

Evidence: `log_bo` per k: 7:3, 8:2, 9:2, 10:4, 11:7, 12:5; k = 8 is the G1 seed (2,603.6 M) plus one swap (5,372.2 M); its G0 (5,339.5 M) was only seen by random.
This is my red flag almost word for word.
Smallest fix: a minimum of 3 evaluations per k in the plausible range (8-14), or a per-k local search under E before the global EI phase.

### S2 (high) - eight loses mainly through the same relay artefact

Evidence: best k = 8 penalty 869.9 M (52 over-limit routes per day) versus 418.2 M for the recommended network.
Removing the relay alone still leaves 8 behind by about 213 M, but about 27 extra over-limit stores x (vehicle + fuel) is roughly 235 M, so with the far stores handled equally (cross-dock or one coastal site) 8 and 12 are within roughly 20 M of each other.
Smallest fix: re-evaluate the best 8 and best 12 with the far stores served the same way and show vehicles, km and fixed cost side by side.

### S3 (medium) - the finals compare k = 7, not k = 8

Evidence: `pipeline.py` puts `best_k{kmin}` in the finals and kmin = 7 at reduced scale; k = 8 enters only by accident as `proxy_only`.
Smallest fix: always add `best_k8` to the finals (the meeting's claim), regardless of kmin.

### S4 (medium) - the fixed-cost saving is not shown in full first

Evidence: no table shows 12 x 30 M versus 8 x 30 M (120 M at reduced scale) before operating cost is subtracted; the sweep gives totals only per k.
Smallest fix: a sweep column "fixed saving versus 12" and a vehicle-and-km breakdown of what eats it.

### S5 (medium) - no break-even for eight

Evidence: no stop-time, speed or fixed-cost sweep exists yet (brain section 12 lists it as planned).
Smallest fix: one-way sweep of DC fixed cost and stop time on the best 8 and best 12 only (4 x a few evaluations).

## 07 Data Team lead - centre of gravity under full E

### T1 (critical, in my favour) - the recommended network is my centre of gravity

Evidence: candidate 71, origin "G0 centre of gravity", k = 12, sites [0, 5, 9, 10, 15, 21, 22, 31, 36, 40, 50, 59], E = 1,938.8 M, is the recommendation.
G0 is also the best evaluated network at k = 9 (2,035.2 versus G1 3,062.6), 13 and 14; the random run's best (2,052.1 M) is G0 too.
A sweep of G0 over k under E (13 evaluations) would have produced the same answer as the 40-evaluation GP search.
Smallest fix: add a "G0 + E sweep" row to the approaches table with its evaluation count and runtime, and stop claiming the pipeline beats the centre of gravity until it does.

### T2 (high) - the pool is built around G1, the weaker criterion

Evidence: all 156 swaps are neighbours of the G1-best (`build_pool`, `s = list(best)`); no local move around G0; the GP models E - G1 although G1 has R^2 = -1.30 and Spearman 0.48 against E.
Smallest fix: generate swaps around G0 as well, and let the GP model E minus the better proxy.

### T3 (medium) - G0 is one random k-means start

Evidence: `g0_sites` uses one initialisation (seed + k) and stops at a local optimum; it is the centre of gravity (squared distance), not the Weber point, on map coordinates, which matches what I said but is the weakest version of it.
Smallest fix: best of 10 starts by weighted within-cluster sum; name it "centre of gravity (squared distance)" and optionally add a Weiszfeld step.

### T4 (medium) - G0 was not evaluated at every k

Evidence: G0 for k = 7, 17 and 18 has no E; k = 8 and 15 only through random.
Smallest fix: evaluate every G0 as a seed (13 more evaluations, or count them in B as the brief allows for G seeds).

### T5 (low) - compute comparison missing

Evidence: runtime 276.6 s total, no split between G0 (milliseconds), pool build and E calls.
Smallest fix: log wall time per stage in `meta`.

## 09 Real estate and leases manager

### L1 (high) - the recommendation exits 8 of 12 leases at once

Evidence: it keeps only Yongin, Daejeon, Chilgok and Gimhae; it drops Wonju (lease to 2031-06), Gwangju (2030-09), Cheonan (2030-03), Yangju (2029-09), Wanju (2029-03) and opens 8 new sites.
Several swaps are 10-15 km moves (Gwangju Pyeongdong -> Naju, Wanju -> Iksan, Cheonan -> Asan) whose operating gain is small but which require breaking a lease years early.
Smallest fix: re-evaluate the recommended network with every current site forced back in wherever a candidate within 20 km was chosen, and price the early exits as one-off cost with a payback line.

### L2 (high) - rent is a province step, which drives micro-swaps

Evidence: `site_cost_factor` gives 1.20 capital, 1.05 metro city, 0.88 elsewhere; Gwangju Pyeongdong costs 31.5 M and Naju Bitgaram 26.4 M 15 km away, Ulsan Onsan 31.5 M versus Gyeongju Oedong 26.4 M.
The fixed-cost part of the saving (19.8 M) is mostly this boundary artefact; Yongin and Gimpo at the same rate as central Seoul is also generous to the capital region.
Smallest fix: rent by distance to Seoul and to metro centres (smooth), stated as an assumption, plus a sensitivity with uniform rent.

### L3 (medium) - sites are plausible logistics locations, with gaps

Evidence: the 12 current sites (Yongin Giheung, Gimpo Gochon, Yangju Gwangjeok, Hanam Gamil, Wanju Bongdong, Chilgok Waegwan, Gimhae Hallim, Ulsan Onsan, Daejeon Daedeok) are recognisable logistics or industrial areas near expressways; none is a rice field or city centre.
But no current site serves the east coast while S24 Gangneung Gujeong exists as a candidate, and Busan Gangseo, Icheon and Pyeongtaek (the real big logistics clusters) are candidates rather than current sites.
Smallest fix: state the siting rule and sources in `geo.py` (interchange plus industrial zone), and justify why the chain has no east-coast DC.

### L4 (medium) - lease expiry exists but is never used

Evidence: `lease_expires_on` is in `dcs.csv` but no code or discussion uses it; brain section 12 only promises a payback sensitivity.
Smallest fix: a closure sequence in expiry order (2027 Yongin and Hanam and Chilgok first) showing the network cost after each step; the bonus extension can reuse E.

### L5 (low) - capacity per site is uniform

Evidence: every site has `max_stores` = 280; three recommended DCs (Yongin, Namyangju, Incheon Namdong) sit exactly at the bound.
Smallest fix: state uniform capacity as an assumption and test the recommendation with the three boundary sites at 1.2x capacity.

## Verdict of the panel

The 532 M is not manufactured by the historical assignment or the cache, but most of it is the D-019 relay charge on 48 Gangwon-coast and fringe stores that the baseline cannot reach.
The recommendation is the Data Team's centre-of-gravity network at k = 12, which the GP search found late and random missed by chance.
Before any number goes to the board: a feasible baseline, the saving with and without the relay, two more world seeds, three evaluations per k, and G0 in the approaches table.
