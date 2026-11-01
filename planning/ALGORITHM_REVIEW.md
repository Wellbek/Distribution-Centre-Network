# Algorithm review - are the algorithms behind run 3 the right ones?

Date: 2026-10-21 (day 2 of 14).
Trigger: run 3 says today's network beats every bounded redesign by about 100 M KRW a month, and the user suspected that the algorithms, not the network, produce that answer.
Scope: every algorithm in `code/dcn/` checked against the brief (`assignment.md` v2.2), `BUSINESS_DECISIONS.md`, the lecture decks (`ie437/md/ch01`, `ch02`, `ch04`, `ch05`, `ch06`), published practice and three experiments.
This file is a rolling reference: later checks append a dated section at the end.

## 0. Short answer

- **The lower level (savings + 2-opt) is measurably not optimal, but its error does not favour today's network.**
  PyVRP (hybrid genetic search) needs 4.9% fewer vehicles than savings on today's network and 3.9% fewer on the k = 10 alternative (search day 0), so a better router lowers both by about the same amount and widens today's lead slightly (about 12 M KRW a month on that day's cost), it does not close it.
- **The selection rule (Kennedy-O'Hagan GP + EI) is fine.**
  On run 3's fully evaluated pool every model-based rule finds the pool's best candidate within 10 to 20 evaluations from random starts; random selection finds it in 13% of runs after 40.
- **G1's site search is fine.**
  The greedy-plus-12-nearest-swap search is already a local optimum of G1 under the full swap neighbourhood for every k from 8 to 13.
- **The weak parts are G1 itself and the pool built from it.**
  G1 ignores the clock (Spearman 0.66 against E, G-pick loss 446 M), the planned clock-aware G2 was never built, and the ten best pool candidates all descend from G1's own optimum (seven sites shared by all ten), so the search can only confirm G1's choice.
- **What decides the result is a business rule, not an algorithm (Section 9).**
  Today's network keeps five DCs below the 500-store minimum and three above the 1,400 cap (the brief exempts the baseline); no redesign may do that (B-07).
  Under the same rules an optimiser wins: a local search on E without the minimum beats today's network by 50 M a month (5,824 against 5,874 on the final days); inside 500-1,400 the best found is still 69 M worse (5,943).
- **No Spark run is needed to keep the decision.**
  Two optional Spark scripts exist (Section 6) if the user wants the routing gap on all seven search days or a local search beyond the pool.

## 1. What the brief and the business decisions ask of the algorithms

| Requirement | Source | What it implies for the algorithm choice |
|---|---|---|
| Lowest total monthly cost with at least 98% of deliveries before 12:00 | Brief §2.2 | The lower level should minimise vehicles first: an owned vehicle-day costs 180,822 KRW, the fuel of 517 km |
| "A continuous approximation of route length is fine inside G; a routing heuristic belongs inside E; an exact solution belongs on small instances where you measure the heuristic's accuracy" | Brief §2.7 | Our three-tier split is the one the brief asks for; a metaheuristic inside E is allowed but not expected |
| State the cost of one solve and the accuracy "against an exact solution on small instances, against a bound, or against an alternative heuristic, and what its error does to the upper level" | Brief §3.1 | The router's error must be measured at full territory size and its effect on the ranking stated; the 7-store exact check alone does not do this |
| One evaluation is expensive; a budget B of full evaluations; generation by G, selection by a surrogate with an acquisition rule, compared with random at the same budget | Brief §3.3, R4 | GP + EI on a pool is the course default; the pool's quality bounds what any rule can find |
| Raw coordinates fail; use knobs or a pool with summary features and model the gap E - G | Brief §3.3 | Our pool + discrepancy GP is option (ii); option (i), knobs, is the named alternative |
| Remedies for the G-E gap: conservative correction, uncertainty penalty from proxy disagreement, or system knowledge (detour ratio, the window's effect on stops per route) | Brief R3 | G1 has the detour (road km) but not the window; the window term is the missing remedy |
| Reduced run in a few minutes, three commands, offline, Python 3.10 | Brief §6.2 | Any new solver must install from a wheel on a grader's laptop and keep the reduced run in minutes |
| Realistic workarounds (relay drivers, longer shifts) flagged as business decisions | `BUSINESS_DECISIONS.md` B-01 to B-07 | The relay pass must stay part of any router we compare (it does, in both) |

## 2. Lecture algorithms and where they sit

| Lecture | Algorithms taught | Used in the engine | Not used, and could be |
|---|---|---|---|
| 1 Optimization modelling | Standard form, convexity, LP, KKT and duality, successive convexification with a trust region, bilevel "evaluate a layout through its best operation", "compare optimisers using the same surrogate" | Transportation LP for the assignment (HiGHS, duals price the bounds); bilevel structure of E | Trust region over site sets for the upper level (Section 4, row U5) |
| 2 Bayesian statistics | Conjugate updating (Beta-Binomial, Poisson-Gamma with exposure, Normal-Normal), predictive distributions, Bayesian linear regression | Poisson-Gamma demand with calendar exposure, empirical-Bayes prior, negative-binomial predictive | Bayesian linear regression as a cheaper gap model (tested in the replay: equal to the GP) |
| 4 Bayesian optimization | GP regression, kernel fitting by marginal likelihood, PI, EI, UCB, acquisition optimisers, constrained EI x PF, Wall 2 (dimension: stay local, latent space) | Matérn-5/2 ARD GP on 7 pool features, EI on the enumerable pool | UCB/LCB, Thompson sampling (tested: equal); EI x PF (no infeasible candidate near the top, not needed); local trust regions (Wall 2) |
| 5 Surrogate-based design | Prediction versus decision quality, signed decision bound, COMs and RoMA (conservatism), deep ensembles and NEMO (uncertainty), Kennedy-O'Hagan discrepancy, system knowledge | K&O discrepancy E = G + δ; R3 decision bound | Conservative rescaling of G by E/G; proxy-disagreement penalty; the window as system knowledge in G (G2) |
| 6 Generative design | Latent search, CbAS (conditioning a generator on success), guidance | None | A CbAS-style site-inclusion distribution for diverse candidates (bonus "candidate generation") |

## 3. The algorithms as implemented

| Component | File | Algorithm | Cost |
|---|---|---|---|
| Lower level | `routing.py` | Parallel Clarke-Wright savings on 40 nearest neighbours (all pairs up to 400 stores), merge only if load, stops, km, noon and shift hold; 2-opt inside each route; relay pass re-routes stores no one-driver route reaches | About 0.15-0.3 s per territory-day |
| Assignment | `evaluate.assign_lp` | Transportation LP, demand-weighted road km plus a steep penalty beyond the 55 km noon reach, prohibitive beyond 125 km, 500-1,400 stores per DC | One LP per evaluation |
| Fleet | `evaluate.monthly` | Newsvendor fractile 0.671 of daily vehicle need over the sampled days, spot above | Free |
| E | `evaluate.evaluate` | Sample average over 7 / 28 / 14 posterior-predictive days with common random numbers and calendar weights | About 70 territory-days per evaluation |
| G0 | `search.g0_sites` | Demand-weighted k-means on map coordinates, snapped to distinct sites | Milliseconds |
| G1 | `search.g1` | Fixed cost + load-based fleet (routes = demand / (0.92 x 48), x 1.08) + line-haul + continuous-approximation local km on road distances; greedy capacity-aware assignment; far stores priced as relay routes; **no clock** | 1.6 ms |
| G1 site search | `search.g1_best` | Greedy add from the k-1 solution, then two passes of swaps with each site's 12 nearest candidates | Seconds per k |
| Pool | `search.build_pool` | Per k: G1-best, G0, today's sites at k = 12, random 1-2 site swaps of these until 30 candidates; 390 in all | 26 s |
| Selection | `search.run_search` | 13 G1 seeds (k = 7..19), then 27 picks by EI on a K&O discrepancy GP over 7 features | GP fits on at most 40 points |
| Demand | `demand.py` | Poisson-Gamma with chain calendar exposure, empirical-Bayes prior strength, gamma overdispersion, AR(1) chain shock | Seconds |

## 4. The argument table

Verdicts: **Keep** (the current choice is right), **Add** (keep it and add this as a check or remedy), **Replace**, **Reject** (considered, not adopted).
"Evidence" points to Section 5 or to the run-3 registry.

### Lower level and connection

| # | Choice | For | Against | What practice and the literature do | Evidence here | Verdict |
|---|---|---|---|---|---|---|
| L1 | Clarke-Wright savings + intra-route 2-opt (current) | 0.2 s per territory-day, so E costs about 15 s, the whole run fits the Spark and the reduced run fits a laptop; deterministic, so common random numbers stay exact; the classic for many-stop depots (Clarke and Wright 1964); every merge respects all limits | Minimises km, not vehicles, although a vehicle-day is worth 517 km of fuel; no move between routes, so it never empties a route; about 7-11% above best known or optimal solutions on CVRP benchmarks | Savings is the standard *construction* step (OR-Tools offers it as a first-solution strategy), followed in practice by a metaheuristic | Savings uses 29 more vehicles than PyVRP on today's network (587 vs 558, 4.9%) and 24 more on the k = 10 alternative (620 vs 596, 3.9%) (E1) | **Keep inside the search, Add the PyVRP accuracy row**: the error is 3.5-4.2% of daily cost on both networks and slightly favours the redesign, so it cannot reverse the recommendation |
| L2 | PyVRP hybrid genetic search inside E | State of the art for VRPTW and CVRP (won the 2021 DIMACS VRPTW challenge, first on the static EURO meets NeurIPS 2022 VRP); native time windows, two load dimensions (cages and stops), max distance and duration, heterogeneous fleet for relay vehicles; MIT, pip | 60-150 s per large territory-day against 0.2 s: one E becomes about 1.5 h on one core, the 40-evaluation search days on a laptop and hours on the Spark; stochastic, so common random numbers need a fixed seed and still add noise; no aarch64 Linux wheel (builds from source on the Spark); stalls on rural territories (with one vehicle per store it returned all single-store routes; with a bounded fleet it found no feasible solution for 2 of 10 k = 10 territories at 0.1 s per store and needed 0.3 s per store, 3-6 min each); breaks "reduced run in a few minutes" | Academic benchmark leader; operational routing products use metaheuristics, while strategic network studies use approximations or fast heuristics inside the design loop | E1 | **Reject inside the search; Keep as the accuracy reference** (brief §3.1 "against an alternative heuristic") |
| L3 | OR-Tools routing with guided local search | Widely deployed, aarch64 wheels, the instructor's company benchmarks against it | A few percent behind HGS in published comparisons; the same run-time problem at 1,400 stores; another dependency | Common industrial default | Not run (PyVRP covers the reference role) | **Reject** |
| L4 | Savings + inter-route local search (relocate, swap, 2-opt*, route elimination) in our own code | Keeps the speed (about 1 s per territory-day), stays deterministic, would close most of the 3-5% vehicle gap; a vehicles-first objective becomes possible | New code to test before the deadline; changes every number, so a new Spark run and new demo numbers; still a heuristic | The usual "construction + local search" pipeline | E1: the gap is almost all vehicles at equal km, which route elimination targets | **Add only if time remains after the deliverables**; the decision does not depend on it |
| L5 | Exact set partitioning on 7-store toys (`verify.py`) | Proves the heuristic is exact where exact is possible | Seven heavy stores need 1-3 vehicles, where savings is trivially optimal; says nothing about vehicle counts at 1,400 stores | Exact methods (branch-price-and-cut) reach a few hundred customers | Run 3 verify: gap 0 on every toy, while E1 finds 0.4-11.4% at full size | **Keep, Add** the load lower bound and the PyVRP comparison as the full-size accuracy evidence |
| L6 | Continuous approximation of route length inside G | Milliseconds; the brief's own recommendation; standard in strategic design (Daganzo; Franceschetti, Jabali and Laporte 2017; La Poste network redesign) | Constants need calibration; ignores the clock unless added | Strategic network studies estimate routing cost this way | G1 against E: Spearman 0.66 (evaluated), 0.58 (pool) | **Keep, Add the clock (U1)** |
| C1 | Transportation LP for the assignment inside E | Exact, convex, integral; duals price the 500 and 1,400 bounds (Lecture 1); small search space | A distance proxy, not route cost; the bounds bind on 5 of 10 DCs of the k = 10 network (two at 500, three at 1,400), so the LP shapes the cost | Commercial network design tools solve location-allocation MILPs with lane costs | Redrawing today's own sites inside 500-1,400 costs 3.7 bn a month: a bounds effect, not an LP effect | **Keep** |
| C2 | Newsvendor fleet quantile over 7 days | The fractile 0.671 is cost-optimal with unlimited spot (B-05) | A 0.671 quantile of 7 days is the 5th order statistic, noisy | Standard fleet-sizing logic | The final comparison uses 28 days and held-out days | **Keep** (open item 23 stays) |
| C3 | Sample average approximation with common random numbers | Paired differences are precise; the brief's sampled-day evaluation | Seven days in the search | Kleywegt, Shapiro and Homem-de-Mello 2002 | Saving interval [-110, -91] M over 28 days, [-108, -97] held out | **Keep** |

### Upper level

| # | Choice | For | Against | What practice and the literature do | Evidence here | Verdict |
|---|---|---|---|---|---|---|
| U1 | G1 without the clock (current) | 1.6 ms; road distances and relay pricing already inside | Ignores the noon deadline and the shift, which bind on about 40% of routes (census: shift 232, load 263 of 579 routes a day in today's network); ranks k = 8 first although E puts it 446 M behind k = 10 | Brief R3 names "the window's effect on stops per route" as the system-knowledge remedy; Salhi and Rand 1989: locating without routes misleads | Spearman 0.66 / 0.58; R2 = -0.24; G-pick loss 446 M | **Replace by G2**: vehicles per DC from the stops a route can make before noon given its out-leg (out-leg time + stops x 15 min ≤ 8 h), the remedy the brief names and the plan promised |
| U2 | G1 site search (greedy add + swaps with 12 nearest) | Fast; warm starts across k | A restricted neighbourhood might miss better G1 solutions | Teitz-Bart style exchange is the classic p-median heuristic | The full swap neighbourhood (all 60 sites) finds no G1 improvement for any k = 8..13 (E3) | **Keep** |
| U3 | Exact MILP for G (capacitated facility location, HiGHS) | A certified optimum with a gap (Lecture 1 duality) | G1 is nonlinear (ceilings, square roots), so a MILP certifies a different, linearised criterion; single-source CFLP at 9,718 x 60 needs aggregation | Standard in commercial network design | U2 shows G1's local search is already locally optimal | **Reject** for now |
| U4 | Pool = G1-best, G0 and random 1-2 swaps of them | Feasible by construction; the brief's option (ii) | The ten best candidates share seven sites and all descend from G1-best; the pool's best is a G1 seed, so the 27 EI picks could only confirm it ("search added nothing over its seeds") | Brief §3.3: "a pool of candidates with G and local moves" | Pool statistics and replay (E2) | **Add** diversity: seed the pool from G2 as well as G1, and regenerate swaps around the best E so far (U5) |
| U5 | Trust-region local search on E over site sets (swap, add, drop around the incumbent) | Lecture 1 trust region and Lecture 4 Wall 2 "stay local" (TuRBO, Eriksson et al. 2019); tests whether the pool hides a better network | Each step costs 100-180 evaluations, far beyond B = 40: a development check, not the reported search | Local search is how location heuristics refine candidates | Not run; `experiments/spark_e_local_search.py` is ready | **Optional Spark check** (Section 6) |
| U6 | Generator knobs (brief option i: k, volume exponent, detour penalty, minimum spacing) with BO on 4-5 numbers | Low-dimensional and continuous, the GP's home ground | Another generator to build; the knobs still produce G-optimal networks, so they share G's blind spot unless G2 exists | The brief's other working parameterisation | Not built | **Reject**; name it as the considered alternative |
| U7 | CbAS-style site-inclusion distribution (Lecture 6) | Diverse good candidates; counts for the bonus | Needs many evaluations to learn | Research method | Not built | **Reject** unless the bonus is pursued |
| U8 | K&O discrepancy GP + EI (current) | The course default; the brief's "model the gap E - G over the pool" | Nine hyperparameters on as few as 13 points | Noisy-EI practice (Letham et al. 2019); BOCS and COMBO for purely combinatorial inputs | From 5 random starts, GP-EI, GP-LCB and BLR-EI reach the pool best by evaluation 10 in 30 of 30 runs, Thompson sampling by 20; random selection in 4 of 30 after 40 (E2) | **Keep** |
| U9 | 13 G1 seeds over k = 7..19 | One seed per k swept is required by the brief | k = 14-19 lose 500-1,900 M against the best on E; six seeds go where nothing can win | Prune with a certified bound (fixed cost + load lower bound on vehicles above the incumbent) | Pool best per k (E2) | **Add** the bound argument to justify a narrower swept range, freeing budget |
| U10 | Demand: Poisson-Gamma with exposure | Lecture 2; negative-binomial predictive as in DeepAR and M5 practice | Nothing material | Standard | Average-day gap 1.2% explained | **Keep** |

## 5. Experiments

All run on the laptop, one core (`taskset -c 2` or `-c 4`, `nice -n 19`, one BLAS thread), in a separate environment (`uv venv --python 3.10`, numpy 2.2.6, scipy 1.15.3, pyvrp 0.11.3, ortools 9.15) so the pinned `code/.venv310` stays untouched.
They rebuild run 3's full world exactly (`make_world(1.0, 437)`, history seed 438, search days seed 448, 9,718 planning stores) and read `code/results/full/registry.json` of Spark run 3.
Scripts and raw results are in `planning/experiments/`.

### E1 - Router accuracy at full size (`routing_gap.py`)

Setting: search day 0 (2026-12-04, weekday, chain factor 1.06); today's network with its historical assignment (12 DCs) and the k = 10 alternative of run 3 with the LP assignment (10 DCs); each territory routed by `routing.solve` (savings + 2-opt + relay pass) and by PyVRP on the same matrix and demand; PyVRP structured like E: one-driver vehicles for the stores one driver can reach, relay vehicles (500 km, on duty to 19:00, one extra driver-day) for the rest; cost weights 180,822 KRW per vehicle-day and 350 KRW/km; fleet bounded by the savings count + 25% (at least 5); 0.1 s per store (10-148 s per territory), seed 1; every PyVRP route re-checked with the engine's own `walk()` and limits (0 violations where feasible).
Run time: about 17 min per network on one core.

| Network | Territories compared | Stores | Vehicles, savings | Vehicles, PyVRP | Difference | Per 1,000 stores | Route km, savings / PyVRP | Daily cost gap |
|---|---|---|---|---|---|---|---|---|
| Today (12 DCs) | 12 of 12 | 9,718 | 587 | 558 | -29 (-4.9%) | -2.98 | 65,610 / 65,627 | 4.2% (129.1 to 123.9 M a day) |
| k = 10 alternative | 10 of 10 | 9,718 | 620 | 596 | -24 (-3.9%) | -2.47 | 79,762 / 78,456 | 3.5% (143.3 to 138.5 M a day) |

Naju Bitgaram and Gimhae Hallim needed 0.3 s per store (see below); all other territories ran at 0.1 s per store.

- PyVRP reaches the load lower bound on Gimpo Gochon (1,484 stores, 77 vehicles against 80) and saves up to six vehicles a day on one territory (Hwaseong Hyangnam, 79 to 73).
- Per territory the savings gap ranges from 0.4% to 11.4% of daily cost, largest on the small east-coast DC (Gangneung Gujeong, 100 stores: 11 to 10 vehicles).
- PyVRP trades km for vehicles: it often drives a little more (Gimpo +207 km) to save a vehicle, which savings, a km minimiser, never does.
- Two k = 10 territories (Naju Bitgaram, 601 stores, and Gimhae Hallim, 1,180 stores, both with relay stores) gave PyVRP no feasible solution at 0.1 s per store (PenaltyBoundWarning); at 0.3 s per store both solved (Naju 55 to 51 vehicles, Gimhae 76 to 72); a first attempt with one vehicle per store stalled at all single-store routes on every rural territory.
- On that day today's lead over the k = 10 alternative grows from 14.2 M to 14.6 M KRW of daily cost (about +12 M a month): PyVRP saves 5 more vehicles on today's network, but 1,300 more km on the k = 10 network.
  This is one day (n = 1) and the difference is small; what is robust is that the router moves both networks by about the same 4%.

What it means: the router's error is real (3.5-4.2% of daily cost, mostly vehicles) and slightly larger on today's network, which has more small and rural territories.
A better router therefore lowers every E by about 4% and leaves the ranking in place; it cannot overturn "keep today's network", and the reported -100 M saving is, if anything, slightly conservative.

### E2 - Selection rules on the evaluated pool (`upper_level_replay.py`)

Setting: run 3's 390 pool candidates, every one already evaluated by E on the 7 search days (the pipeline's validation step), so the replay needs no new routing; budget 40; rules: random, G1 order, EI / LCB (κ = 2) / Thompson sampling / posterior mean on the K&O GP of `dcn/gp.py`, and EI on Bayesian linear regression over the same 7 features; two starts: the 13 G1 seeds (as reported) and 5 random candidates; 30 repetitions for random starts (seeds 0-29), one run for deterministic rules.

| Start | Rule | Median best after 10 / 20 / 40 (M KRW) | Pool best found |
|---|---|---|---|
| 13 G1 seeds | every rule | 5,828 / 5,828 / 5,828 | 100% (the pool best is a seed) |
| 5 random | random | 6,349 / 6,165 / 6,011 | 13% |
| 5 random | G1 order | 6,274 / 5,828 / 5,828 | 100% |
| 5 random | GP-EI (current) | 5,828 / 5,828 / 5,828 | 100% |
| 5 random | GP-LCB | 5,828 / 5,828 / 5,828 | 100% |
| 5 random | GP-Thompson | 5,842 / 5,828 / 5,828 | 100% |
| 5 random | GP mean only | 5,828 / 5,828 / 5,828 | 100% |
| 5 random | BLR-EI | 5,828 / 5,828 / 5,828 | 100% |

Pool facts: the ten best candidates are 4 G1 seeds and 6 swaps of G1 seeds and share sites 1, 6, 15, 34, 40, 47 and 56 (Gimpo, Wonju, Namyangju, Nonsan, Naju, Gimhae, Chilgok); the best per k is 7,374 (k = 7), 6,274 (8), 5,952 (9), 5,828 (10), 5,856 (11), 5,982 (12), 6,066 (13) and 6,331 to 7,730 for k = 14-19; today's network scores 5,736 on the same days.
What it means: the rule earns its keep against random selection, but on this pool any sensible rule ties; the limit is what the pool contains.

### E3 - Is G1's site search a local optimum? (`upper_level_replay.py`)

Setting: from the pool's G1-best of each k = 8..13, first-improvement swaps over every closed site (60 candidates), repeated until none improves G1 by more than 1,000 KRW.
Result: no change for any k (G1 5,129 / 5,199 / 5,295 / 5,411 / 5,533 / 5,665 M for k = 8..13).
What it means: the restricted 12-nearest neighbourhood loses nothing; improving the upper level means improving G (U1) or searching on E (U5), not searching G harder.

## 6. Recommendations, in order

1. **Write the router accuracy into the deliverables (no compute).**
   Balance-table row "Routing method": savings + 2-opt, 0.2 s per territory-day; measured 4.9% (today) and 3.9% (k = 10) more vehicles than PyVRP on one full search day, 4.2% and 3.5% of daily cost; the error shifts both networks alike, so the ranking and the recommendation stand.
   This answers brief §3.1 "against an alternative heuristic, and what its error does to the upper level", which the 7-store exact check cannot.
2. **Build G2, the clock-aware G (code change, then one Spark run like run 3).**
   Vehicles per DC from the stops a route can make before noon given its out-leg, the remedy brief R3 names; seed the pool from G1 and G2.
   This is the one algorithm change that could change *which* candidates the search sees.
3. **Keep the GP + EI selection rule** and say why with E2 (rules tie on this pool; the rule beats random).
4. **Justify a narrower k range with a bound** (fixed cost plus the load lower bound on vehicles) so fewer of the 40 evaluations go to k = 14-19.
5. **Optional Spark checks** (not needed for the decision):
   - `spark_hgs_rescore.py`: today's network, the top 5 and the best of each k = 8..13 re-scored with savings and with PyVRP on all 7 search days (about 30-60 min on 16 cores); turns E1's one day into seven and checks that the ranking holds; its savings column must reproduce run 3's search-day E (today 5,736 M, k = 10 5,828 M).
   - `spark_e_local_search.py`: best-improvement swap / add / drop on E from the pool's best k = 9..12 candidates, then the 28 final days (up to about 75 min on 16 cores); tests whether the pool hides a network that beats today's.
   Commands: copy `code/` and `planning/experiments/` to the Spark with the usual `tar | ssh`, install `pyvrp==0.11.3` into `~/dcn-venv` (builds from source on aarch64; needs `g++`), run inside `tmux`, copy the JSON back with `scp`.
6. **Ask the business question that actually decides the answer (B-07):** may a kept regional DC run below 500 stores?
   With the minimum, no redesign wins; without it, the search space includes today's network and its neighbours.

## 7. Where the data comes from

No company data exists: the brief (§2.5) asks for a fictional chain generated from a fixed seed, with public sources allowed for where stores are and how far roads run.
Everything below is rebuilt by `make_world(1.0, 437)` and `demand.make_history(seed 438)` in the full run; the numbers are from that world.

### 7.1 Inputs from public data

| Item | Source | What we take from it |
|---|---|---|
| Where people live | Kontur Population, South Korea, 2023-11-01, H3 resolution 8 (about 0.7 km² per hexagon), CC BY 4.0, from HDX | 71,015 hexagons with 51.1 M people after removing Jeju, sea points and 760 ferry-only island hexagons (`prep/build_hexes.py`, `prep/road_connected.py`) |
| Province and district of each store | geoBoundaries ADM1 and ADM2 | The `region` field; the mountain class (Gangwon, North Gyeongsang) for the distance model |
| Road distances | OSRM v6.0.0, car profile, Geofabrik `south-korea-latest.osm.pbf` (OSM data of 2026-10-18), ferries excluded, run on the DGX Spark | Every store-to-site pair (9,718 x 60) and each store's 50 nearest stores; other store pairs by a model calibrated on 3,959 OSRM distances (median error 4-20% by distance band); 89-99% of the legs a route drives are OSRM values |
| City list | Approximate 2024 city populations (`geo.CITIES`) | Only to label store types (office near big-city centres) |

### 7.2 What is generated, and how

| Table or quantity | How it is made | Result in the full world |
|---|---|---|
| Stores | 10,000 points drawn in proportion to population over the Kontur hexagons, jittered up to 0.4 km inside the hexagon; hexagons under 500 people mark rural stores | 10,000 generated; 568 opened and 282 closed during the history year; **9,718 open at the planning horizon** (the planning set) |
| Store distribution | Follows population: Gyeonggi 3,059, Seoul 1,732, South Gyeongsang 694, Busan 579, North Gyeongsang 493, South Jeolla 473, Incheon 467, South Chungcheong 390, Daegu 387, North Jeolla 317, North Chungcheong 311, Daejeon 253, **Gangwon 242**, Ulsan 220, Gwangju 86, Sejong 15 | Province shares within half a point of population shares |
| Store type | Rules on location: office and mixed near big-city centres, roadside and residential in the countryside, mostly residential elsewhere | 5,433 residential, 2,173 mixed, 1,313 roadside, 799 office |
| Store demand level | Lognormal (σ = 0.45) times a type level, rescaled to a mean of 2.2 cages a day and clipped to 0.5-6 (brief §2.6) | Mean 2.19, 10th-90th percentile 1.10-3.56 cages a day |
| Daily demand history | 365 days from 2025-10-01: store level x weekday profile by type x summer peak x Korean holidays and eves x chain-wide AR(1) shock (φ 0.6, σ 0.06, 1.5% storm days) x store-day gamma noise (shape 8), Poisson counts; closed days marked | Chain total 22,277 cages a day on average (17,064 to 34,186) |
| Demand model (what the planner fits, Lecture 2) | Poisson-Gamma per store with the fitted calendar as exposure, prior strength by empirical Bayes, overdispersion and chain shock estimated | Prior strength about 2 store-days, κ = 8.1, φ = 0.46; sampled planning days come from this posterior predictive |
| Candidate sites | 60 hand-placed sites near motorway interchanges and logistics zones (`geo.SITES`, S01-S60), the 12 current sites among them | 14 capital-region sites at 180 M KRW a month, 6 metro sites at 157.5 M, 40 regional sites at 132 M (150 M x 1.20 / 1.05 / 0.88); cap 1,400 stores each |
| Costs and vehicle limits | Teaching defaults (brief §2.6): vehicle 5.5 M a month with driver, fuel 350 KRW/km, spot truck 550,000 a day, 48 cages, 25 stops, 250 km, 15 min per stop, 35 km/h, departure 04:00, deadline 12:00, 10 h shift with a 30 min break | Plus one assumption: a relay (second) driver costs one owned vehicle-day, 180,822 KRW (B-01) |

### 7.3 Drivers and vehicles are outputs, not inputs

- The brief gives no driver or vehicle numbers, and none are generated.
- One vehicle carries one driver (the 5.5 M a month includes the driver); the lower level decides each day how many vehicles each DC needs.
- The owned fleet per DC is the 0.671 quantile of its daily need over the sampled days (the newsvendor fractile of 5.5 M a month against 550,000 a day); days above it hire spot trucks.
- A relay route (stores beyond one driver's day) carries a second driver.
- Today's network over the 365 history days: 573 vehicles a day on average, 580 owned, 64,811 km a day, 3,502,822 deliveries, all before noon, about 190 M KRW a month of spot hire (the outcome tables `deliveries`, `vehicle_days`, `spot_hires`).
  So today's operation employs about 580 drivers, plus spot-truck drivers on peak days.

## 8. How today's network (the baseline) is computed

The brief asks for current DCs "placed plausibly, as a chain that grew over decades would have", warns that a strawman baseline is penalised (R5), and exempts the baseline from the 500-1,400 bounds (§2.3).

1. **Sites: chosen by an optimiser, not by hand** (`prep/current_network.py`, decisions D-044 then D-059).
   A capacitated p-median picks 12 of the 60 sites to minimise demand-weighted road km to the stores open before the history year, subject to every store lying within 125 road km of its DC (half of one driver's 250 km day) and no DC holding more than 1,400 stores, with **no 500-store minimum**.
   It is solved by exchange search (swap a site for a nearby one, keep the swap if the LP cost falls) on 5 km cells, each candidate scored by a transportation LP, until no swap helps.
   Result: Gangneung Gujeong, Namyangju Jingeon, Gimpo Gochon, Gwangju-si Opo, Hwaseong Hyangnam, Yeongju Munsu, Nonsan Yeonmu, Daegu Dalseong, Gyeongju Oedong, Busan Gangseo, Naju Bitgaram, Gwangyang Port; demand-weighted mean road km 31.9, farthest store 120 km.
2. **Assignment: frozen history** (`world.make_world`).
   Stores open before the history year get the planner's LP assignment (demand x road km, nothing beyond 125 km, at most 1,400 per DC); the 568 stores opened during the year join their nearest DC by road; nothing is rebalanced.
   That is why three DCs now exceed the cap (Gimpo 1,484, Namyangju 1,429, Gwangju-si 1,420) and five sit below the minimum (Gangneung 100, Yeongju 145, Gwangyang 224, Gyeongju 367, Naju 473).
3. **Operation: the same evaluation as every candidate.**
   Same lower level (savings + 2-opt + relay pass), same sampled days (common random numbers), same fleet rule, same costs.
   E = 5,874 M KRW a month on the 28 final days (fixed 1,827, owned vehicles 3,240, fuel 696, spot 112, relay 0), 579 vehicles a day, no relay route, 100% before noon.

What this means: the baseline is itself the output of a Lecture 1 optimisation (an LP inside an exchange search) on road distances with the reach rule, solved with fewer constraints than any redesign is allowed.
It is a strong, defensible baseline, but by construction it is also close to optimal for the same geography.

## 9. Why the best redesign loses to today's network - checks (2026-10-21)

Question (user): with all the methods of Lectures 1-5, how can the optimum be worse than the baseline?
Answer in one line: **it is not worse under the same rules.**
Give the optimiser the baseline's freedom (no 500-store minimum) and it beats today's network by 50 M KRW a month, while even respecting the 1,400 cap that today's network breaks; keep the minimum and nothing beats today's network.

Setting for every check: `experiments/baseline_checks.py`, laptop, one core per run (`taskset`, `nice -n 19`, pinned `code/.venv310`); run 3's full world rebuilt exactly (seed 437, 9,718 stores); the 7 search days (seed 448) and the 28 final days (seed 449) of run 3, common random numbers; same E as the pipeline (savings + 2-opt + relay pass, LP assignment, 0.671 fleet quantile).
Local searches: first improvement over drop, swap with the 6 nearest sites and add, screened on 3 of the search days (one per calendar class), 40 min budget, then re-scored on 7 and 28 days.

### 9.1 One change at a time (search days, M KRW a month)

| # | Network and rules | E | Vehicles a day | Note |
|---|---|---|---|---|
| X1 | Today, historical assignment (bounds exempt) | **5,736** | 569 | Reproduces run 3 exactly |
| X1 | Best redesign of run 3, k = 10, LP within 500-1,400 | **5,828** | 606 | Reproduces run 3 exactly; 18 relay routes a day |
| X2 | Today's 12 sites, LP assignment, no minimum, cap 1,400 | 5,767 | 573 | Forcing today's three over-cap DCs (Gimpo 1,484, Namyangju 1,429, Gwangju-si 1,420) under the cap costs 31 M |
| X2 | Today's 12 sites, LP assignment, no minimum, no cap | 5,695 | 563 | The LP beats the frozen historical assignment by 41 M when both are free of bounds: the assignment rule in E is not what hurts the redesigns |
| X3 | Best redesign k = 10, LP, no minimum | 5,777 | 600 | Dropping only the minimum saves it 51 M |
| X3 | Same plus Gangneung (k = 11), LP, no minimum | 5,795 | 597 | An east-coast DC cuts relay routes from 18 to 6 but costs 132 M of rent |

Under identical rules (LP, no minimum, cap 1,400) today's 12 sites (5,767) and the best 10-site redesign (5,777) are within 0.2%.
The 92 M gap on the search days splits into about 31 M from today's exemption from the cap, 51 M from the minimum imposed on redesigns, and 10 M from sites and k.

### 9.2 Local search on E itself (the strongest optimiser we can afford)

| # | Rules | Start | Evaluations | Moves accepted | Result, search days | Result, final 28 days | Against today (5,874 final) |
|---|---|---|---|---|---|---|---|
| X5 | Within 500-1,400 | Run 3's best redesign (k = 10) | 193 | Siheung Banwol to Incheon Namdong; Gimhae Hallim to Changwon Jinyeong | 5,805 | 5,943 | **+69 M** (still worse) |
| X4 | No minimum, cap 1,400 | Today's 12 sites | 328 | Busan Gangseo to Gimhae Hallim; Daegu Dalseong to Chilgok Waegwan; Yeongju Munsu to Jecheon Bongyang; Gimpo Gochon to Incheon Namdong; Gwangju-si Opo to Hanam Gamil (the search also tried and undid Gwangyang to Suncheon) | 5,677 | **5,824** | **-50 M** (better) |

X4's network keeps 12 DCs: Hanam Gamil, Incheon Namdong, Hwaseong Hyangnam, Namyangju Jingeon, Gangneung Gujeong (109 stores), Jecheon Bongyang (208), Nonsan Yeonmu, Naju Bitgaram (473), Gwangyang Port (222), Gimhae Hallim, Gyeongju Oedong (359), Chilgok Waegwan; no DC above 1,400; 577 vehicles a day, one relay route a day, 100% before noon.
X5's network: Gimpo Gochon, Cheonan Seobuk, Wonju Munmak, Incheon Namdong, Namyangju Jingeon, Nonsan Yeonmu, Naju Bitgaram, Changwon Jinyeong, Gyeongju Oedong, Chilgok Waegwan; 614 vehicles a day, 17 relay routes a day.

### 9.3 What the checks say

- **No bug and no unfair comparison found.** The engine reproduces run 3 to the million; today's network and every candidate get the same days, router, fleet rule and costs; E's LP assignment is better than the historical one when both are free of bounds (X2).
- **The optimiser does beat the baseline once the rules match.** X4 finds a 12-DC network 50 M a month cheaper than today's (0.9%), keeping the small east-coast and southern DCs and moving five sites.
  The user's intuition holds in this sense: an optimiser should not lose to the baseline, and on the same feasible set it does not.
- **The 500-store minimum is what makes every redesign lose.** Inside 500-1,400 even a local search on E (X5) stays 69 M above today's network; the sparse east coast (Gangwon 242 stores), the north-east inland and the south coast cannot fill a 500-store DC, so they are served from far away, with relay drivers and more vehicles.
- **The baseline is strong by construction.** It is a p-median optimum on road km without the minimum (Section 8), so it starts close to X4's optimum; X4 improves it by under 1%.
- **The pool was a little short.** X5 found 31 M (final days) beyond run 3's best candidate, which supports adding pool diversity (U4, U5); it does not change the ranking.
- Caveats: one local optimum per search (first improvement, 40 min, screened on 3 days); savings routing inside E (Section 5, E1: about 4% too high for both networks alike); no bootstrap interval on the X4 saving yet (search days -59 M and final days -50 M agree in sign and size).

### 9.4 What to do with it

1. The brief makes the bounds part of the problem for new designs, so the reported answer stays: **within the company's own bounds, no redesign beats today's network**; report X5 as the strongest bounded search.
2. Report X4 as the price of the minimum: **the 500-store rule costs about 120 M a month** (X5 at 5,943 against X4 at 5,824 on the final days), and relaxing it for kept regional DCs lets a redesign save about 50 M a month against today.
   This is business decision B-07, now with a price.
3. Next decision for the user: whether to add "hybrid" candidates (current small DCs may stay below 500) to the reported search, which would make X4's kind of network a candidate; this needs a code change and a Spark run like run 3.

## 10. Omelet research papers - what we can borrow within Lectures 1-5 (2026-10-21)

Source list: https://omelet.ai/en/research/ (14 publications, read from abstracts).
Rule (user): only algorithms introduced in Lectures 1-5 may be used, so a paper counts only if its idea can be carried out with LP/MILP, convexity, duality, least squares (L1), conjugate and Bayesian regression (L2), GP and acquisition rules (L4), or the surrogate disciplines of L5.

### 10.1 Paper by paper

| Paper | Core idea | Within Lectures 1-5? | Use for us | Verdict |
|---|---|---|---|---|
| Sobhanan, Park, Park, Kwon: Genetic algorithms with neural cost predictor for hierarchical VRPs (Transportation Science 2025, arXiv 2310.14157) | Upper level (depot choice, assignment) searched by a GA; each candidate's routing cost predicted by a graph network trained on HGS solutions instead of solving the VRPs | GA and GNN no; the idea "predict a territory's routing cost from features learned on routed territories" yes, with least squares (L1) or Bayesian regression (L2) | A territory-level cost model as a better G | **Tested (X6)** |
| Kaleem, Lee, Kwon, Subramanyam: Neural embedded mixed-integer optimization for location-routing (arXiv 2412.05665; NeurIPS 2025 workshop) | A network approximates the optimal CVRP cost of any customer subset from a facility; embedded in a MILP solved by an off-the-shelf solver; within 1% of best known on large benchmarks | Neural net no; a cost model linear in per-store sums embeds in a facility-location MILP (L1) | Choose sites and territories in one MILP with a learned cost | **Tested (X6)** |
| Ahn, Park: LPMARL, LP-based task assignment for hierarchical MARL (NeurIPS 2025 workshop; Lecture 1 extension slides "An LP inside a policy") | An LP assigns agents to tasks; its cost coefficients come from a network trained on the lower level's outcomes | RL no; "learn the LP's cost coefficients from the lower level" yes (L1 LP + L1/L2 regression) | Replace E's hand-set cost-to-serve (55 km reach, x3 penalty) by per-store costs learned from routed territories | Same model as X6; **Add only with vehicle terms** (10.3) |
| Kim, Park, Kwon: Neural separation of rounded capacity inequalities (INFORMS JoC 2024, arXiv 2306.17283) | Learned separation of cuts that give CVRP lower bounds up to 1,000 customers | The bound ⌈demand(S)/48⌉ vehicles for a store set S is plain L1 bounding; the neural separation is not needed | Certified vehicle lower bounds per territory: the router's accuracy row (E1 uses S = the whole territory) and the bound that prunes hopeless k (U9) | **Add** (bound only) |
| Son et al.: RRNCO, real-world routing (NeurIPS 2025 workshop, arXiv 2503.16159) | Neural solver for asymmetric real road distance and duration matrices from 100 cities | Neural solver no | Modelling note: we average both driving directions (D-036); the asymmetry is a fidelity row to state, not an algorithm | **Note** for the balance table |
| Hua et al.: CAMP, vehicle routing with profiles (AAMAS 2025, arXiv 2501.02977) | Multi-agent RL for fleets where vehicle profiles restrict or prefer clients | No | Confirms our relay vehicles as a second profile restricted to far stores (B-01) | **Reject** (method) |
| Berto et al.: PARCO (NeurIPS 2025), RL4CO (KDD 2025), RouteFinder (TMLR 2025); Son et al.: Equity-Transformer (AAAI 2024) | Neural and reinforcement-learning routing solvers; min-max routing | No (RL and attention models are later lectures) | Our router stays savings + 2-opt, with PyVRP as the reference (E1); our objective is total cost, not min-max | **Reject** |
| Kim et al.: Neural genetic search (ICML 2025); Kim et al.: Ant colony sampling with GFlowNets (AISTATS 2025); Seo et al.: Generative flows on synthetic pathways (ICLR 2025) | Generative and neural search over discrete spaces | No (generative design is Lecture 6 and later) | None | **Reject** |
| Tang et al.: HiMAP, multi-agent path finding (AAMAS 2024) | Learned policies for robot path finding | No; a different problem | None | **Reject** |

### 10.2 Experiment X6 - a learned territory cost, as G and inside a MILP (`experiments/territory_surrogate.py`)

Setting: run 3's full world; training territories from 30 randomly drawn pool candidates (seed 0) and today's network with two assignments (historical, and LP without the minimum): 421 territories, each routed by the engine (savings + 2-opt + relay pass) on 3 screening days (one per calendar class, run-3 search-day weights); target = day-weighted operating cost per territory (180,822 KRW per vehicle, 350 KRW/km, relay driver-days); features = sums over the territory's stores of 1, cages, road km to the DC, cage-km, stores beyond 55 km and stores beyond 125 km, plus a per-DC intercept, so the cost is linear in the assignment and embeds in a MILP.
Fit: least squares with all coefficients non-negative (Lecture 1, a convex QP); 5-fold cross-validation over networks.
A first fit with a Gaussian prior on unscaled weights was discarded: it shrank the per-DC and per-store terms to zero and gave negative costs (-3,038 KRW a day per store beyond 55 km) that a MILP would exploit.
MILP: 60 binary sites plus fractional assignment of 1,569 cells of 5 km, store-count bounds, HiGHS through `scipy.optimize.milp`, 600 s limit each; both MILPs stopped at the limit.
Laptop, one core, 46 min in all, peak memory 1.4 GB.

| Measure | Learned territory cost | G1 (current) |
|---|---|---|
| Territory level, cross-validated R² / median absolute error | 0.83 / 20% | - |
| Fitted terms (KRW a day) | 409 per road km to the DC (summed over stores), 133,137 per store beyond 125 km; every other term 0 | - |
| Rank agreement with E on 360 held-out pool networks (Spearman) | **0.92** | 0.60 |
| Mean absolute error against E | **11.1%** | 31.2% |
| Loss of its own pick against the best held-out network | 521 M (picks k = 13) | 446 M (picks k = 8); the best is k = 10 |

| Learned-cost MILP | k | E search | E final | Vehicles a day | Relay routes a day | Against today (5,874 final) |
|---|---|---|---|---|---|---|
| Within 500-1,400 | 14 | 6,739 | 6,909 | 640 | 19 | +1,035 (eight DCs at exactly 500) |
| No minimum, cap 1,400 | 14 | 5,961 | 6,128 | 568 | 2 | +254 |
| For reference: local search on E within bounds (X5) / without minimum (X4) | 10 / 12 | 5,805 / 5,677 | 5,943 / 5,824 | 614 / 577 | 17 / 1 | +69 / -50 |

### 10.3 What X6 says

- **Prediction got much better, decisions did not**: Lecture 5's central warning, measured on our own problem.
  The learned cost ranks networks far better than G1 (Spearman 0.92 against 0.60, error 11% against 31%), yet its own pick and its MILP optima are worse than G1's pick and much worse than a search on E.
- **Why**: with non-negative weights the fit kept only "road km to the DC" and "stores beyond 125 km"; it has no term that charges a territory for its own vehicles at a given size and distance, so more DCs always look cheaper apart from rent, and the MILP opens 14.
  The ranking is good on the pool because pool networks resemble the training networks; the MILP leaves that range, which is exactly where Lecture 5 says a proxy must not be trusted.
- **What the papers do differently**: both use the learned cost to steer a search and keep accurate routing behind it (Sobhanan et al. inside a GA; Kaleem et al. with a network trained on many subsets and checked against routing).
  The safe lecture versions are: the learned cost as the prior mean of the discrepancy GP (Lecture 5, Kennedy and O'Hagan), or as a second proxy whose disagreement with G1 is penalised (brief R3, uncertainty penalty); any candidate a MILP proposes must still be judged by E.
- **What it would take to put it inside the MILP**: per-territory vehicle terms with the clock in them (stores and cages per vehicle as a function of the territory's distance, the G2 of U1), and training territories spread over the size and distance range the MILP can reach (a trust region, Lecture 1).
- **Verdict**: do not replace the search; **Add** the learned cost as a better G (or GP prior mean) once G2's vehicle term exists; the bound from the separation paper and LPMARL-style learned LP coefficients come with it.

## 11. Sources

- Clarke and Wright savings gap on CVRP benchmarks: Doyuran and Çatay, enhancements of Clarke-Wright savings, https://research.sabanciuniv.edu/id/eprint/14115/ ; heumilkr benchmark vignette (mean 11% against optimal on CVRPLIB), https://cran.stat.unipd.it/web/packages/heumilkr/vignettes/clarke_wright_performance.html
- PyVRP: Wouda, Lan and Kool (2024), INFORMS Journal on Computing 36(4), 943-955, https://arxiv.org/abs/2403.13795
- HGS-CVRP: Vidal (2022), Computers & Operations Research 140, 105643, https://arxiv.org/abs/2012.10384
- OR-Tools against PyVRP on VRPTW (a few percent behind): TuneNSearch, https://arxiv.org/abs/2503.12662 ; agentic VRP framework, https://arxiv.org/abs/2510.16701
- Savings against insertion for VRPTW with fleet size in the objective: Fathi and Mesgari (2025), https://eoge.ut.ac.ir/article_103534_28ebc736fdf5001a446dff7d7e9ffec4.pdf
- Locating without routes misleads: Salhi and Rand (1989), EJOR 39(2), 150-156, https://ideas.repec.org/a/eee/ejores/v39y1989i2p150-156.html
- Location-routing surveys: Drexl and Schneider (2015), EJOR 241(2), 283-308; Schneider and Drexl (2017), as cited in https://arxiv.org/abs/1906.06750
- Continuous approximation in distribution: Franceschetti, Jabali and Laporte (2017), TOP 25(3), 413-433, https://ideas.repec.org/a/spr/topjnl/v25y2017i3d10.1007_s11750-017-0456-1.html
- La Poste network redesign with a MILP and a routing-cost approximation: Winkenbach, Roset and Spinler (2016), Interfaces 46(5), https://ideas.repec.org/a/inm/orinte/v46y2016i5p445-458.html ; Winkenbach, Kleindorfer and Spinler (2016), Transportation Science 50(2), 520-540, https://ideas.repec.org/a/inm/ortrsc/v50y2016i2p520-540.html
- Single-source capacitated facility location, exact and kernel search: https://arxiv.org/abs/2112.12974 ; Guastaroba and Speranza kernel search, https://iaorifors.com/paper/78471
- Trust-region BO: Eriksson et al. (2019), NeurIPS, https://proceedings.nips.cc/paper_files/paper/2019/file/6c990b7aca7bc7058f5e98ea909e924b-Paper.pdf
- Combinatorial BO (BOCS, COMBO): https://arxiv.org/abs/2008.08177 ; https://arxiv.org/abs/2102.07188
- Convenience-store logistics practice: Seven-Eleven Japan partner distribution centres and vehicles, Fujitsu case study, https://www.fujitsu.com/nz/about/resources/case-studies/vision/sej ; BGF Retail's Busan centre consolidating Yeongnam CU deliveries (two large hubs with Jincheon), https://www.sidae.com/article/2026091609591317837 and https://dealsite.co.kr/articles/169534

- Omelet research list: https://omelet.ai/en/research/ ; Sobhanan et al., https://arxiv.org/abs/2310.14157 ; Kaleem et al., https://arxiv.org/abs/2412.05665 ; Kim, Park and Kwon, https://arxiv.org/abs/2306.17283 ; RRNCO, https://arxiv.org/abs/2503.16159 ; CAMP, https://arxiv.org/abs/2501.02977 ; LPMARL abstract, https://www.paperswithcode.com/paper/lpmarl-linear-programming-based-implicit-task

Checked by fetching the page: the two Korean articles, the Omelet list and the arXiv abstracts of 2310.14157, 2306.17283, 2503.16159 and 2501.02977.
Known from search abstracts only, to verify before any of them enters `problem-definition.md`: the rest.

## Dated notes

- 2026-10-21: Naju Bitgaram and Gimhae Hallim rerun at 0.3 s per store (`routing_gap_recommended_0_dc40-47.json`), completing the k = 10 column of E1; the first summary (3.3% on 8 of 10 territories, "today's lead grows by about 50 M") was an extrapolation and is replaced by the measured 3.9% and about 12 M.
- 2026-11-01: exhaustive one-move neighbourhood of run 7's recommended network under E (`experiments/e_neighbourhood_check.py`, results in `e_neighbourhood_recommended.json` and `.jsonl`; laptop, 3 workers, 4,619 s).
  Scope: all 560 swaps (any open site for any closed site), drops and adds that keep 500-1,400 stores per DC feasible, scored on the 7 search days; the 14 neighbours within 25 M of the start re-scored on the 28 final days.
  The start reproduces the registry (5,981.98 M on the search days, 6,110.9 M on the final days).
  Result: the recommended network is not a one-move local optimum.
  Siheung Banwol (S18) swapped for Incheon Namdong (S12) is 28.5 M a month cheaper on the search days and 24.0 M cheaper on the final days (6,086.9 against 6,110.9), which would lift the saving from 468.7 M to about 493 M.
  Two more swaps also lower the final-days cost: Gimhae Hallim for Changwon Jinyeong (-9.8 M) and Namyangju Jingeon for Yangju Gwangjeok (-1.4 M); the other eleven close neighbours are worse.
  Meaning: the search found the best member of its pool, but the pool lacked this neighbour; the claim "best network found" holds only for the pool.
  The gain is about 0.4%, k = 10 and the sign of the saving are unchanged.
  Open for the night of 1 Nov: (a) disclose in the definition, proposal and demo as a checked limit, or (b) adopt the swap, which needs a Spark run of `run_full.py` and a rebuild of every deliverable, the trailer and the ZIP, plus a second neighbourhood round from the new network (about 75 min on the laptop).
  The Spark was unreachable (SSH timeout), so nothing shipped was changed.
