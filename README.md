# Dasol network lab: how many distribution centres, and where

[![Trailer: the Dasol distribution-centre redesign in 80 seconds](media/trailer-preview.gif)](media/trailer.mp4)

**[Watch the full trailer (80 s, MP4)](media/trailer.mp4)**

A convenience-store chain of 9,718 stores runs 12 distribution centres, and their leases expire one by one from 2027 to 2029.
This project decides how many DCs to run, at which sites, which stores each serves and how many vehicles each owns, with every delivery before noon.
Every candidate network is priced the same full way: road distances from OpenStreetMap, each store's demand as a Bayesian belief, every DC routed on sampled demand days, and a budgeted Bayesian-optimisation search over the site choice; every method comes from the course (Lectures 0-6).

**The answer in the fictional instance:** run 10 DCs instead of 12, keeping 3 sites and opening 7, which saves about 524 M KRW a month (535 M on days the search never saw).
The quick estimate that ignores the noon clock would have picked 8 DCs and cost 412 M KRW a month more.
The saving rests on how far the real network has drifted from a good design, so the first step is a check against Dasol's real delivery records.
All figures come from the reported run (`code/results/full/registry.json`); Dasol Retail is fictional, the geography and road distances are real.

## Results (run 8, `code/results/full/registry.json`)

| Quantity | Value |
|---|---|
| Recommended network | 10 DCs: keep Gimpo Gochon, Cheonan Seobuk, Incheon Namdong; open Yangju Gwangjeok, Wonju Munmak, Nonsan Yeonmu, Naju Bitgaram, Changwon Jinyeong, Gyeongju Oedong, Gumi Sandong |
| Monthly cost, 28 final days | 6,055.1 M KRW (baseline network 6,579.6 M) |
| Saving, 28 final days | 524.5 M KRW a month, 90% paired bootstrap interval 511.6-541.3 |
| Saving, 14 held-out days the search never saw | 534.9 M KRW a month, 90% interval 521.6-554.0 |
| Deliveries before 12:00 | 100% on every final and held-out day, both networks |
| Vehicles | 623 a day, 631 owned (baseline 644 a day, 654 owned) |
| Saving with PyVRP's routes instead of ours | about 507 M KRW a month; 10 DCs stay cheapest |
| Quick estimate without the clock (`G1`) | picks 8 DCs, 412.4 M KRW a month dearer |
| Range across the model checks | about 390-530 M KRW a month |

Costs are quoted on two sets of demand days: the 7 search days on which the search and the refinement compare networks (the recommendation costs 5,926.9 M there), and the 28 final days on which the reported saving is measured (6,055.1 M).

## How it works

The decision is a hierarchy.
The upper level (`D1-network`) chooses how many DCs and which of 60 candidate sites; the assignment of stores to DCs (`D2-assignment`) and the owned fleet (`D3-fleet`) follow from it; the lower level (`D4-routing`) routes each DC every day, after that day's demand is known.
The upper level is judged by the lower level (`D1-network evaluated_by D4-routing`), so every candidate network is priced by routing it.

### Lower level: one DC's day

For DC $j$ with $n_j$ owned vehicles and that day's demand $q_i$, choose a set of routes $R$:

$$\min_{R}\; c_v\min(|R|, n_j) + c_s(|R|-n_j)^+ + c_f\sum_{r\in R}\mathrm{km}(r) + p_{late}L + p_{out}M$$

subject to, for every route: load $\sum_{i\in r} q_i \le 48$ cages, at most 25 stops, at most 250 km, every arrival by 12:00, back by 13:00 including a 30-minute break, and arrivals chained by $a_{next} = a_{prev} + s + d_{prev,next}/v$ (15 min per stop, 35 km/h).
$c_v$ = 180,822 KRW per owned vehicle-day, $c_s$ = 550,000 KRW per spot truck, $c_f$ = 350 KRW per km, $p_{late}$ and $p_{out}$ the brief's penalties.
The deadline is a hard constraint; stores no one-driver route can reach get a two-driver relay route (up to 500 km, on duty until 19:00), an assumption for the business to confirm.

Method (Lecture 0's construct and improve, `dcn/routing.py`): open a route at the farthest unrouted store, then repeatedly insert the nearby store whose cheapest feasible insertion saves most against serving it alone ($2d_{0c}$ minus the insertion detour), with every infeasible store masked; then shorten each route by segment reversal.
One territory-day costs about 0.18 core-seconds.

### Connection: the full evaluation E

$$E(x) = \sum_{j\in x} f_j + c_m\sum_{j\in x} n_j(x) + \frac{365}{12}\sum_{t=1}^{N} w_t\,Q(x, n(x); \xi_t)$$

$f_j$ is the site's monthly rent, $c_m$ = 5.5 M KRW per owned vehicle, $Q$ the day's fuel, spot, relay and penalty cost from the lower level, $\xi_t$ demand day $t$ drawn from the posterior predictive, $w_t$ its calendar weight.
Every network sees the same demand days (common random numbers), so differences between networks are paired.

- **Assignment** (`dcn/world.py`, Lecture 1): for fixed sites, a transportation LP, solved exactly (HiGHS through SciPy):
  $\min_{z\ge 0}\sum_{i,j} w_i\tilde d_{ij} z_{ij}$ s.t. $\sum_j z_{ij} = 1$ for every store and $500 \le \sum_i z_{ij} \le 1{,}400$ for every open DC, with $\tilde d$ the road km plus a penalty beyond the 55 km noon reach and a prohibitive cost beyond the 125 km one-driver reach.
  The constraint matrix is totally unimodular, so the LP optimum is integral (every store goes to exactly one DC), and its duals price the store bounds.
- **Fleet** (newsvendor fractile): each DC owns the $q$-quantile of its daily vehicle need with $q = 1 - c_v/c_s = 1 - 180{,}822/550{,}000 = 0.671$; an owned vehicle pays only if it is needed on more than 32.9% of days.
- **Demand** (`dcn/demand.py`, Lecture 2): Poisson-Gamma with calendar exposure,
  $y_{s,t}\mid\lambda_s \sim \mathrm{Poisson}(\lambda_s e_{s,t}\gamma_t)$, $\lambda_s \sim \mathrm{Gamma}(a_\tau, b_\tau)$, $\lambda_s\mid\mathcal D \sim \mathrm{Gamma}(a + \sum_t y_{s,t},\ b + \sum_t e_{s,t}\gamma_t)$,
  with the exposure $e_{s,t}$ estimated once per store type (weekday × month × holiday), the chain shock $\gamma_t$ an AR(1) process ($\varphi$ = 0.46, $\sigma$ = 0.061), and a prior worth about two store-days.
  Demand days are drawn from the posterior predictive (negative binomial with gamma overdispersion, $\kappa$ = 8.1): 7 search days, 28 final days, 14 held-out days.
  One average day would understate E by 75.2 M a month (1.3%), because the owned fleet is a quantile over days.

### Upper level: how many DCs, and where

$$\min_{y\in\{0,1\}^{60}} E(y)\quad\text{s.t.}\quad \sum_j y_j = k,\; k\in\{7,\dots,19\},\; \text{the assignment LP is feasible}$$

For fixed sites the assignment is linear and solved exactly; the site choice is combinatorial ($\binom{60}{10} \approx 7.5\times 10^{10}$ sets for $k = 10$ alone) and is searched.

- **Cheap criteria G** (`dcn/search.py`): `G0` is the centre of gravity (the Data Team's method); `G1` adds a load-based fleet and the continuous approximation of route length $c\sqrt{nA}$ on road distances, with $c$ = 1.08 fitted by least squares on routed days; `G2` adds the noon clock: a store at road distance $d$ can share a route with at most $s_{max}(d) = \min\{25,\ (8\,\mathrm{h} - d/v)/(s + \ell/v),\ (250 - 2d)/\ell\}$ stores.
- **Pool**: 390 candidates for $k$ = 7 to 19 from `G2`, `G1`, `G0`, the baseline sites adjusted, and one- and two-site swaps of these.
- **Budgeted search** (Lectures 4-5): $B$ = 40 full evaluations; first the `G2` optimum of every $k$, then expected improvement on a Kennedy-O'Hagan model $E(x) = G_2(x) + \delta(x)$, with $\delta$ a Gaussian process (Matérn 5/2, one length scale per summary feature, hyperparameters by marginal likelihood) on seven features: $k$, mean, 95th-percentile and maximum road km to the DC, load imbalance, demand share beyond 55 km, store share beyond 125 km.
  The next evaluation maximises $\mathrm{EI}(x) = (f^\ast - \mu(x))\Phi(z) + \sigma(x)\varphi(z)$, $z = (f^\ast - \mu(x))/\sigma(x)$.
- **Refinement** (after the search, outside $B$; Lecture 0's improve role and Lecture 1's descent): best-improvement local search on E over every one-move neighbour of the search's pick (any open site swapped for any of the 50 closed ones, one dropped, one added; 560 networks a round) until no move saves 1 M KRW a month.
  It ran 5 rounds and 2,800 evaluations, affordable because E costs about a second here; each accepted move ranked within the 33 best of its round's 560 neighbours by the cheap criterion `G2`, so screening each round to the 40 `G2`-best neighbours would take the same path with 200 full evaluations (`code/checks/refinement_screen.py`), the version for a real system at hours per evaluation. The moves: Siheung Banwol replaced by Incheon Namdong, Namyangju Jingeon by Yangju Gwangjeok, Gimhae Hallim by Changwon Jinyeong, Chilgok Waegwan by Gumi Sandong, 55.7 M a month cheaper on the final days.

### What is proven, what is checked, what is not

| Claim | Evidence | Status |
|---|---|---|
| The assignment is optimal for the chosen sites | Transportation LP solved exactly; its constraint matrix is totally unimodular, so the LP optimum is an integral assignment | Proven (LP optimality and integrality) |
| The router is accurate enough to rank networks | Exact enumeration on 25 territories of 7 stores: 0 extra vehicles, day cost 0.3% above the optimum; PyVRP (hybrid genetic search) on every territory: our routes cost 7.2% more on the baseline network and 6.9% more on the recommended one, nearly the same, so the saving moves from 524 to about 507 M and 10 DCs stay cheapest | Measured |
| The search finds the best network of its pool | All 390 pool networks evaluated afterwards: the search reached the pool's best at evaluation 14 of 40 | Verified |
| The selection rule beats random selection | Replayed from random starts: GP + EI finds the pool's best in 98% (5 starts) and 88% (13 starts) of 100 replays, 40 random picks with probability 40/390 = 10.3% | Measured |
| The recommended network is optimal under the model | No single swap, drop or add improves it (the best neighbour costs 6.2 M more): a one-move local optimum of E | Local optimum only; global optimality among $7.5\times10^{10}$ sets is not proven |
| The number of DCs is 10 | The sweep is U-shaped with its minimum at 10; 9 and 11 lie within 37 M on unrefined networks; the refinement keeps 10; PyVRP's routes keep 10 | Near-tie with 9 and 11, stated as such |
| The saving holds beyond the days the search used | 14 held-out days with the fleet fixed from the final days: 534.9 M (521.6-554.0) | Verified on held-out days |
| The saving survives the assumptions | 9 of 11 one-at-a-time changes keep it positive; it reverses if today's network were already optimal for today's stores (−59 M) or under the strict brief without relay routes (−452 M) | Conditional: two reversals are business facts to measure |

`python verify.py` re-checks the shown run independently (32 checks, all pass): every store served once, no unflagged limit violation, cost identities, the paired saving, the LP bounds, determinism, the router against exact enumeration, the page's JavaScript engines against Python, and more.

## What is here

| File | What it is |
|---|---|
| `demo.html` | Interactive demonstration: the answer, a delivery day on real roads with a live solve of one DC or the whole network, the method lecture by lecture with a live run of the search, the data, the checks and the extensions; opens offline |
| `proposal.html` | The proposal to management, 17 slides in project-management order |
| `problem-definition.md` | The full problem definition: formulation, data, method, evidence, proposal and the review of the AI assistance |
| `code/` | Everything that produces the numbers; three commands (see `code/README.md`) |
| `media/` | The trailer and its preview |
| `video/` | The trailer's source (Remotion) |

## Reproduce

```sh
cd code
pip install -r requirements.txt
python run_full.py      # the reported run
python run_reduced.py   # one store in five, about 8 minutes on two cores
```

## Rebuild the trailer

The trailer is built with [Remotion](https://www.remotion.dev) from footage captured frame by frame in `demo.html` and from numbers read out of the registry, so no figure in it is typed by hand.

```sh
python video/scripts/capture.py   # footage and stills from demo.html and proposal.html (Playwright)
python video/scripts/data.py      # the trailer's numbers and map geometry from the registry
cd video && npm install && npm run render
```
