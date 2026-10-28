# Problem Definition: How Many Distribution Centres for Dasol Retail, and Where

**IE437 Midterm Project · Distribution-Centre Network Redesign - Formulating and Solving a Hierarchical Decision**

Author / student ID: Louis Wellmeyer / 20264059  
Date / version: 2026-10-28 / v1.2 (code run 7)  
Summary: Run ten DCs instead of twelve (keep Gimpo Gochon and Cheonan Seobuk, open eight new sites); in the fictional instance this saves 469 M KRW a month (90% interval over demand days 456-482; about 390-470 M across the model checks, 442 M with routes from a stronger solver) with every delivery before noon, and the saving rests on how far today's real network has drifted from a good design, which the real outcome tables must measure first  
Files: `problem-definition.md`, `code/` (README, three commands), `demo.html` (offline; the live solve also runs from `code/app.py`), `proposal.html`  
LLM tools and use: Claude Opus 5.5 in Claude Code, 19 Oct to 2 Nov 2026, for problem discussion, OSRM setup, code, checks, the demo and slides; every number in this file comes from `code/` (Section 5) and three discussions are reviewed in Section 7.

All company data are fictional and generated from seed 437 (Section 3).
Road distances are real OpenStreetMap values.
`[ASSUMPTION]` marks a working assumption, `TBD` an open fact with a plan, `N/A` an inapplicable item.
Bracketed brief references such as [A §2.3] point to the midterm brief v2.2.

## 1. Decision, Scope & Problem Structure

Several DC leases expire over the next three years, so the network can be redrawn now at little extra cost [A §2.1].

> Dasol's logistics planning and management use store locations, a year of store orders, road distances, site costs and the vehicle rules, before the first lease expires, to decide how many DCs to run, at which sites, which stores each serves and how many vehicles each owns, in order to lower total monthly logistics cost while keeping at least 98% of deliveries before noon.

**The four statements.**
They are four different kinds of claim, so they cannot be ranked against each other directly.

| Statement | Level | Decision or component it concerns | Consequence for comparison |
|---|---|---|---|
| Strategy & Planning: "from twelve to eight, lease and staff costs fall" | A **decision** (k = 8) argued from **one cost component** | `D1-network`; component `C-dc-fixed` | True for its component and incomplete: it is comparable with the Operations statement only once both are written as the same total, E = fixed + operating (Section 2b). Eight is also close to the smallest k the 1,400-store cap allows for 9,718 stores (seven), so it sits near a feasibility boundary |
| Delivery Operations: "wider areas, longer drives, more vehicles, may cost more" | An **evaluation** of the decision through the lower level | `C-operating-cost`, `evaluated_by: D4-routing` | The other half of the same objective; the two meet on one scale, E. Which one wins is an empirical question answered by the sweep (Section 5) |
| Data Team: "centre of gravity is optimal, minutes" | A **method** for `D1-network` (a generation criterion, our `G0`) with an optimality claim that holds only for its own criterion | `G0` | A method is judged by the value of what it proposes under E, not by its own score. The weighted centre of gravity minimises weighted *squared straight-line* distance; it is not the point that minimises the sum of distances, of road distances or of cost, and it does not choose k. Compared in Section 4 as one of the approaches |
| Field Manager: "across the river, trucks drive to the bridge" | A **claim about model validity** (straight-line distance is not road distance) | The distance model inside every criterion | Checked, not ranked: every distance is a road value or calibrated against one (Section 3), and the road-to-straight-line ratio enters the surrogate's features (Section 4). The one-site location problem is convex in straight-line distance and loses convexity under road distance, which is where the Data Team's shortcut stops being exact |

**Boundary.**
One redesign chosen now for a steady-state planning year in which every baseline site can be kept or given up and every candidate site can be leased [A §2.2].
In scope: the 9,718 stores open at the end of the history year, ambient and chilled deliveries in one wave, 60 candidate sites including the 12 baseline sites.
Out of scope, with consequence: the fresh-food second wave (its routes and docks are not costed); Jeju and ferry-only islands (their stores keep today's supply); one-off moving, lease-exit and opening costs (Section 6 treats them as a payback question); the order in which leases expire (the sequence of closures is an extension: Section 5 computes it, Section 6 turns it into the plan).
**Company practice versus our baseline.**
The company's practice is experience-based routing on territories fixed long ago [A §2.1]; it is not available to us.
Our baseline is the 12 generated DCs with their historical territories, routed by our own lower level under exactly the same evaluation as every candidate (Section 5); how the 12 were placed is described in Section 3.

**Decisions and dependencies.**

| ID | What is chosen | Who approves | Time scale |
|---|---|---|---|
| `D1-network` | Number of open DCs k and their sites | Management | Once per redesign, years |
| `D2-assignment` | Which DC serves each store | Logistics planning | Months |
| `D3-fleet` | Owned vehicles per DC (the fleet-policy quantile) | DC operations with finance | Months (vehicle contracts) |
| `D4-routing` | Each day: vehicles used, store sequences, departure times, spot trucks | DC dispatch, the evening before | Daily |

```text
D1-network    → D2-assignment : feasible region (only open DCs), constraint (500-1,400 stores per open DC)
D1-network    → D4-routing    : parameter (the DC location changes every out-leg distance and time)
D2-assignment → D3-fleet      : parameter (the stores, hence the daily vehicle-need distribution)
D2-assignment → D4-routing    : parameter (which stores are routed from which DC)
D3-fleet      → D4-routing    : available action (owned vehicles), objective (spot trucks above the owned fleet)
```

```yaml
evaluated_by:
  - C-operating-cost: D4-routing      # vehicles, fuel, spot trucks, relay drivers, penalties
  - C-service-level:  D4-routing      # share delivered before 12:00, failures after 14:00
  - C-fleet-cost:     D4-routing      # owned vehicles x 5.5 M KRW a month: D3's quantile of D4's daily vehicle need
```

A demand forecast, a distance lookup and a route-length estimate are not decisions; they supply parameters (Section 2, components).

**Classification.**

| Object | Property | Classification | Structural evidence |
|---|---|---|---|
| Decision dependency graph | Decision Structure | Hierarchical | `D1-network` changes the feasible region of `D2` and the parameters of `D4`, and is evaluated through them; the order of modules alone is not the evidence |
| `D1-network`, `D2-assignment`, `D3-fleet` | State Structure | Stateless | One redesign inside the boundary; no decision carries a state to a later decision of the same kind. A closure sequence following lease expiries makes `D1` Stateful (Section 5, extensions) |
| `D4-routing` | State Structure | Stateless | Days are independent: a missed delivery is penalised, not backlogged; empties and returns do not carry over `[ASSUMPTION]` |
| `D1`, `D2`, `D3` | Information Structure | Open-loop | Fixed before any planning-day demand is observed; basis: operational requirement (leases, contracts) |
| `D4-routing` | Information Structure | Open-loop | Routes are planned the evening before from the day's known orders and are not re-planned en route; re-running it every day does not make it Feedback |

Execution frequency (daily routing, a one-off redesign) and triggers (lease expiries) are kept separate from these labels.

## 2. Computable Problem

### 2a · The lower level: one DC's daily operation

**Given:** DC j, its stores $I_j$, that day's orders $q_i$ (roll cages), road distances $d_{ab}$, travel time $d_{ab}/v$ with $v$ = 35 km/h, stop time $s$ = 15 min, vehicle capacity $Q$ = 48 cages, at most 25 stops and 250 km per vehicle, departure 04:00, deadline 12:00, shift ending 13:00 (10 h from 03:00 including 1 h loading) plus a 30 min break, the owned fleet $n_j$ from `D3`.
**Decided:** the set of routes $R$ (each an ordered store sequence) covering every store once.

$$\min_{R}\;\; c_v\,|R| \;+\; c_f \sum_{r\in R} \mathrm{km}(r) \;+\; c_s\,(|R|-n_j)^+ \;+\; p_{late} L + p_{out} M$$

subject to, for every route $r$: $\sum_{i\in r} q_i \le Q$; $|r| \le 25$; $\mathrm{km}(r) \le 250$; arrival $a_i \le$ 12:00 at every stop; return plus break $\le$ 13:00; arrivals chained by $a_{next} = a_{prev} + s + d_{prev,next}/v$.
$c_v$ = 180,822 KRW is an owned vehicle-day (5.5 M KRW a month / 30.42 days), $c_f$ = 350 KRW per km, $c_s$ = 550,000 KRW per spot truck, $p_{late}$ = 120,000 KRW per delivery after 14:00, $p_{out}$ = 500,000 KRW per missed store.
A vehicle-day costs as much as 517 km of fuel, so the problem is vehicles first, kilometres second.

**The delivery window is a hard constraint** when routes are built: no route may reach a store after 12:00, so a long territory needs more vehicles.
The brief tolerates 2% after noon and penalises only after 14:00 [A §2.2]; a cost-minimiser could push up to 2% of stops into that free zone.
We do not use that slack and report the realised service level of every network (Section 5).

**Far stores.** A store that no one-driver route can reach and return from within 250 km and the shift goes on a **relay route** with a second driver: up to 500 km, on duty until 19:00, the noon deadline unchanged, each relay route paying one extra owned vehicle-day (180,822 KRW) for the second driver `[ASSUMPTION; business decision B-01]`.
This price is an upper bound: the truck and its fuel are already counted, and the brief prices a driver only together with a vehicle; since the baseline network runs fewer relay routes than the redesign, the true saving is, on this point, at least the one reported.
The brief itself has no relay route; the register in Section 3 lists this and every other deviation, and the strict reading (far stores become stock-outs at 500,000 KRW) is a reversal row in Section 5.
Only a store beyond even the relay limits counts as missed.

**Modelled:** load, stops, km, the noon deadline, the shift and break, road distances, stop time, relay drivers for far stores, a departure-wave check under a dock limit (Section 4).
**Omitted, with reason:** multiple trips per vehicle (a second trip cannot meet noon); time-of-day traffic (checked with 30 km/h in Section 4); returns and empty cages (no capacity effect `[ASSUMPTION]`); variable unloading times.

**Method** (Lecture 0's two roles of a routing solver, construct step by step and then improve, with hand-written rules instead of learned ones; `code/dcn/routing.py`).
*Construct:* open a route at the unrouted store farthest from the DC; then, among the unrouted stores near the route (each member's 30 nearest), insert the one whose cheapest insertion saves the most kilometres against driving it on its own trip, $2d_{0c} - \min_k (d_{p_k c} + d_{c\,p_{k+1}} - d_{p_k p_{k+1}})$, at that position; a store is masked whenever inserting it would break load, stops, km, the noon deadline or the shift (the constraints of the standard form above); close the route when no store fits.
Far stores go first because a far store left for last needs a vehicle of its own.
*Improve:* inside each route, reverse a segment whenever that shortens the route and all limits still hold.
Then the relay pass for stores no one-driver route can serve.
It is deterministic, so every candidate sees exactly the same procedure.
**Cost of one solve:** about 0.2-0.4 s per territory-day on one core at full scale (1,400 stores) (run 7: 91 territory-days per evaluation in 1.03 s on 16 processes, 0.18 core-seconds each).
**Accuracy**, measured three ways:

| Check | Instance | Result | Source |
|---|---|---|---|
| Exact enumeration (Lecture 3): every feasible route of every store subset, then every split of the stores into routes | 25 random 7-store instances | 0.00 extra vehicles on average (never more); kilometres 8.9% above the optimum on average (32.5% at most), day cost 0.5% above on average (2.1% at most), because vehicles dominate the cost and they match | `code/verify.py` |
| Load lower bound $\lceil \sum q_i / 48 \rceil$ | Every territory of the showcase day | 41-44% above the bound max(load / 48, stores / 25), because the binding limit is the clock, which the bound ignores; the bound is too weak to measure accuracy here, so PyVRP is the real comparison | `code/verify.py` |
| PyVRP 0.11.3 (a genetic algorithm with local search, Lecture 5's family of black-box optimisers), same matrix, limits and relay structure | Full territories, one search day, the baseline network, the recommendation, the baseline sites redrawn and the best 9- and 11-DC networks | Baseline network: 653 vehicles by our router against 610 by PyVRP, day cost 7.2% higher (3.0% to 13.8% per territory, worst on Daejeon 49 against 43 vehicles and Daegu 66 against 59). Recommended network: 636 against 598, 6.6% higher (3.5% to 9.7%). PyVRP left stores unrouted on eleven territories of the five networks at 0.1 s per store; a second pass at 0.5 s per store routed them all | `code/checks/routing_gap.py` (optional dependency; cached results) |

**What its error does to the upper level:** our router over-states operating cost by 7.2% on the baseline network and 6.6% on the recommended one, nearly the same, so the error mostly cancels in the comparison.
With PyVRP's routes on the same day the day's operating saving falls from 2.7 M to 1.9 M KRW, so the monthly saving would be about 27 M lower, about 442 M instead of 469 M; most of what remains is rent (two DCs fewer).
The redraw step alone (baseline sites, territories redrawn) is worth 9.6 M a day with our routes and 7.1 M with PyVRP's.
Does the error move k?
The best 9-, 10- and 11-DC networks routed by PyVRP on the same day cost 187.6, 187.0 and 187.9 M a day including rent (ours: 197.5, 196.2 and 197.2 M): ten stays best with better routes, by 0.6 and 0.9 M a day.
The earlier savings router was closer to PyVRP (6.6% and 2.9%) but biased between the networks, so it over-stated the saving by about 155 M a month; the course-based router is about as far from PyVRP on both networks (Section 7, discussion 1).

**What one solve returns upward:** vehicles used, km, relay routes, late and missed deliveries, the binding limit of every route (load, stops, km or clock) and the service level.

### 2b · The connection

**Down:** the open sites (from `D1`), the assignment produced by the rule below (`D2`), the fleet-policy quantile (`D3`) and the sampled demand days.
**Up:** monthly operating cost, owned fleet per DC, service level, relay and dock counts.

$$E(x) \;=\; \sum_{j\in x} f_j \;+\; c_m \sum_{j\in x} n_j(x) \;+\; \frac{365}{12}\,\sum_{t=1}^{N} w_t\, Q\big(x, n(x);\, \xi_t\big)$$

$f_j$ is the site's monthly fixed cost, $c_m$ = 5.5 M KRW per owned vehicle, $n_j(x)$ the owned fleet, $Q$ the day's fuel, spot, relay and penalty cost from the lower level, $\xi_t$ demand day t drawn from the posterior predictive (Section 3) and $w_t$ its calendar weight, so the sum is a Monte Carlo average over planning days.
**Fleet policy.** $n_j$ is the $1 - c_m/(30.42\,c_s) = 0.671$ quantile of DC j's daily vehicle need over the sampled days: one more owned vehicle costs 180,822 KRW every day and saves a 550,000 KRW spot truck only on the days it is needed, so it pays when it is needed on more than 33% of days; this is where the brief's two-thirds default comes from.
**Demand uncertainty enters here:** E routes N sampled days, not one average day, because the fleet quantile and the spot hires are not linear in demand (Section 3 measures the difference).
**The same days for every network:** every candidate and the baseline see the same store-level demand days, so differences between networks are paired.
**Cost of one evaluation:** k × N lower-level solves: about 70 territory-days for k = 10 and N = 7, 1.0 s with 16 worker processes, about 16 core-seconds (run 7, `meta.timing`).

**Where the assignment lives: re-solved inside E.**
The candidate is only the set of open sites; E assigns stores by a capacitated transportation LP

$$\min_{z\ge 0}\;\sum_{i,j} w_i\,\tilde d_{ij}\,z_{ij}\quad\text{s.t.}\quad \sum_j z_{ij}=1\;\;\forall i,\qquad 500 \le \sum_i z_{ij} \le 1{,}400\;\;\forall j\in x,$$

with $\tilde d_{ij}$ the road distance plus a penalty beyond the 55 km noon reach of a full route and a prohibitive cost beyond the 125 km one-driver reach.
The constraint matrix is totally unimodular, so the LP optimum is integral (every store goes to one DC), and its duals price each binding store bound.
Why inside E rather than part of the candidate: the search space shrinks from site sets times assignments to site sets, a good assignment for given sites is a convex problem we can solve exactly, and E then judges "these sites, operated by this assignment rule"; a better rule could only lower E.
The baseline keeps its historical assignment, a fact of the operation exempt from the bounds [A §2.3]; "baseline sites, re-assigned" is reported as a separate step (Section 5).

`D1-network evaluated_by D4-routing` through E, separately from the dependencies of Section 1.

### 2c · The upper level

$$\min_{y\in\{0,1\}^{60}}\; E(y) \quad\text{s.t.}\quad \sum_j y_j = k,\;\; k\in\{\lceil 9{,}718/1{,}400\rceil,\dots,\lfloor 9{,}718/500\rfloor\} = \{7,\dots,19\},\;\; \text{the assignment LP is feasible}$$

$y_j = 1$ opens candidate site j; the fleet follows from the policy and the assignment from the LP, so neither is a free upper-level variable.
**Convex or linear:** the assignment for fixed sites (the LP above); the one-site location problem under straight-line distance (a sum of norms, convex); the LP relaxation of the capacitated facility-location problem.
**Combinatorial:** the site subset (about $7.5\times 10^{10}$ sets for k = 10 among 60), and E itself is a black box built from heuristic routing, non-convex and noisy in the days drawn.
**Implication:** E cannot be optimised exactly; it is searched under a budget of full evaluations with a cheap criterion proposing candidates (Section 4).
A k below 7 is infeasible (six DCs at the cap hold at most 8,400 stores), which is the demo's failure case.

**I/O schema.**

| Input / output | Table or parameter | Field | Type / unit | Meaning; one row is … |
|---|---|---|---|---|
| Input | `stores` | `store_id`, `region`, `lat`, `lon`, `store_type`, `opened_on`, `closed_on`, `current_dc_id` | text; degrees; category; date; text | one store (10,000 generated, 9,718 open at the horizon) |
| Input | `demand_history` | `store_id`, `date`, `cages_ordered` | integer, roll cages | one store's order on one day (365 days) |
| Input | `dcs` | `dc_id`, `lat`, `lon`, `lease_expires_on`, `monthly_fixed_cost`, `max_stores`, `min_stores` | KRW / month | one baseline DC (12) |
| Input | `candidate_sites` | `site_id`, `lat`, `lon`, `monthly_fixed_cost`, `max_stores` | KRW / month | one leasable site (60, the 12 baseline sites included) |
| Input | `cost_parameters` | `parameter`, `value`, `unit` | mixed | one finance figure (teaching defaults [A §2.6] plus the relay-driver assumption) |
| Input | road distance cache | store-to-site km, store-to-50-nearest-store km, calibration coefficients | km | `code/data/road_cache.npz` (Section 3) |
| Input | outcome tables `deliveries`, `vehicle_days`, `spot_hires` | as in [A §2.5] | | produced by our lower level on the baseline network over the history year; used for the baseline's service level and fleet check, not as inputs to E |
| Output | recommended network | open sites, k, stores per DC, owned fleet per DC | | the decision |
| Output | cost breakdown | fixed, owned fleet, fuel, spot, relay, penalties; saving against the baseline with its 90% interval on final and held-out days | M KRW / month | the evidence |
| Output | evaluation log | step, candidate, sites, k, G1, G2, E, service level, rule that chose it | | one full evaluation (Section 5) |
| Output | registry | every number shown in the three deliverables | JSON | `code/results/full/registry.json` |

**The two criteria.**
**G (generation)** proposes candidates in milliseconds.
`G0` is the Data Team's method, applied to k DCs: each store goes to its nearest centre, each centre moves to its stores' demand-weighted centre of gravity on the map, repeated until the centres stop; the centres are then snapped to k distinct sites by an assignment LP (Lecture 1).
`G1` = fixed cost + a load-based fleet (routes = cages / (0.92 × 48)) + line-haul and continuous-approximation local km on road distances ($c\sqrt{nA}$ for the stops inside a territory of n stores spread over area A), with far stores priced as relay routes; it ignores the clock.
The constant c is fitted by least squares (Lecture 2) on the baseline's routed search days before the search starts: routed km minus the out-and-back legs, against $\sqrt{nA}$ times the local road-to-map ratio, giving c = 1.08 (0.84 in the reduced run).
`G2` = `G1` plus the routes the clock forces: a store at road distance d from its DC can share a route with at most $s_{max}(d) = \min\{25,\ (8\,\mathrm{h} - d/v)/(s + \ell/v),\ (250 - 2d)/\ell\}$ stores, with $\ell$ the territory's mean inter-stop leg, so routes = max(load routes, $\sum_i 1/s_{max}(d_i)$).
`G2` is the criterion the search uses (Section 4, the remedy).
**E (evaluation)** is Section 2b: the lower level routed on every territory of every sampled day.
What G ignores: the exact sequencing of stops, the interaction of load, stops and clock on one route, the fleet quantile over days, and the integrality of vehicles.

**Components.**

| Component ID | Decision ID | Role | Model | Definition, units, and evidence / assumption / unknown |
|---|---|---|---|---|
| `C-dc-fixed` | `D1-network` | Cost | Formulation | $\sum_j f_j y_j$, M KRW a month; 180 M capital region, 157.5 M metro, 132 M regional (150 M × 1.20 / 1.05 / 0.88) `[ASSUMPTION]` |
| `C-fleet-cost` | `D3-fleet` | Cost | Formulation | 5.5 M KRW a month per owned vehicle, driver included [A §2.6]; fleet = 0.671 quantile of daily need |
| `C-operating-cost` | `D4-routing` | Cost | Formulation | fuel 350 KRW/km, spot 550,000 KRW/day, relay driver 180,822 KRW/route-day `[ASSUMPTION; upper bound]`, late 120,000 and missed 500,000 KRW each; computed by the routing heuristic, which is a solution method, not a model class |
| `C-vehicle-limits` | `D4-routing` | Constraint | Formulation | load 48 cages, 25 stops, 250 km, shift (hard) |
| `C-service-level` | `D4-routing` | Constraint | Formulation | every stop by 12:00 (hard when routes are built); realised share before noon reported, at least 98% required |
| `C-store-bounds` | `D2-assignment` | Constraint | Formulation | 500 to 1,400 stores per open DC for new designs; the baseline exempt [A §2.3] |
| `C-demand` | (parameter supplier) | n/a, supplies parameters | Data-driven estimate feeding Formulation components | Poisson-Gamma posterior predictive of each store's order (Section 3); supplying parameters does not make the cost components Data-driven |

Hard constraints: vehicle limits, the noon deadline, the store bounds for new designs.
Preferences: none beyond cost; store fairness is reported, not optimised (Section 5).
**Infeasible inputs:** a k whose bounds cannot hold (k × 1,400 < stores or k × 500 > stores) returns "infeasible: capacity bounds" with no cost; a day the owned fleet cannot cover hires spot trucks and reports how many; a store beyond even the relay limits is reported as missed and penalised, never shown as served.
Applicable follow-up questions from the reference: the evaluation relation is stated above; no component is a State-transition (Stateless); the routing heuristic's accuracy is Section 2a.

## 3. Information & Uncertainty

**What one row represents, and what it cannot tell us.**
This is the reading every later number depends on, so it comes first.

| Table | One row is … | What it does identify | What it does not identify | Consequence we draw |
|---|---|---|---|---|
| `demand_history` | the cages one store **ordered** for delivery the next day | the load a DC must pick and carry: exactly what the lower level needs | shelf demand: a store holds about two days of stock [A §2.3], so a sell-out or a delayed delivery shifts orders between days, and lost sales leave no trace | We plan on orders, not on consumer demand, and say so; the day-to-day variance of orders may be smaller than that of sales (the back room smooths it), which makes the fleet quantile slightly optimistic, and a catch-up order after a late delivery counts as extra demand, so stores served late in the baseline look busier than they are and their fitted rates run high: a request below |
| `demand_history` | an order placed **under the baseline network** (the baseline's delivery time at that store) | the order pattern of the baseline operation | how a store would order if its delivery moved from 06:00 to 11:30 under another DC; a late arrival may raise safety orders | Orders are treated as independent of the network `[ASSUMPTION]`; a redesign moves stores to later slots, so the real-data check of Section 6 includes the share of stores whose delivery moves later by more than 2 h |
| `deliveries`, `vehicle_days`, `spot_hires` | an **outcome of the baseline network**: the baseline's assignment, routes and fleet on one day | the baseline's service level, kilometres, vehicles and spot hires | what any other assignment or network would cost: the rows carry the baseline's choices, so they cannot score a redesign or calibrate a cost per store that transfers to another territory | Used only to describe and check the baseline (Section 5); every candidate is costed by routing it, never by extrapolating these rows. The real tables will also record the company's experience-based routing, so comparing their cost with our routed redesign would credit the redesign with a routing-method gain as well: the check of Section 6 therefore re-routes today's real territories with our lower level and compares like with like, and uses the real tables separately to measure how far our router is from today's practice. Our own generated tables cannot validate our router (they are its output) |
| `stores` | one store, with the DC that serves it in the baseline | location, type, opening date | why it is assigned there; stores opened recently have a short history | Short histories borrow strength from the prior (below) |
| `demand_history`, summed over stores | the chain's daily total, a mix of store types | the chain's calendar | each store's own weekly shape: an office store orders 0.70 of its weekday level at weekends, a residential or roadside store about 1.12 [A §2.3]; a single chain multiplier (1.04) would put an office store's weekend orders about 70% too high and a residential store's 7% too low | Calendar multipliers are estimated over the whole chain but **per store type** (four types × weekday, month, holiday), the unit that carries the weekly shape; see below |

**The instantiated data** (all from `code/dcn/world.py` and `code/dcn/demand.py`, seed 437; tables in `code/results/full/tables/`).

| Table | How it is generated | Real-world property it reflects |
|---|---|---|
| `stores` | 10,000 points drawn in proportion to population on 71,015 Kontur Population hexagons (H3 resolution 8, 2023-11-01, CC BY 4.0), jittered inside the hexagon; Jeju, sea points and ferry-only islands removed; province and district from geoBoundaries ADM1/ADM2; type by location (office and mixed near big-city centres, roadside and residential in the countryside); 6% opened and 3% closed during the history year; 9,718 open at the horizon | Stores follow people: Gyeonggi 3,059, Seoul 1,732, Gangwon 242 stores |
| store opening year | Pre-history stores open along a growth curve (12% by 2000, 41% by 2010, 62% by 2016, 76% by 2020) with denser hexagons earlier `[ASSUMPTION: the shape of a Korean convenience chain's growth]` | A chain that grew from city centres outwards |
| `dcs` | The 12 sites a planner chose in 2016, see "Baseline network" below; leases of ten years from move-ins 2016-2019, expiring quarterly from March 2027 to December 2029 `[ASSUMPTION]` | Leases expiring one after another [A §2.1] |
| `candidate_sites` | 60 hand-placed sites at motorway interchanges and logistics zones (`code/dcn/geo.py`), the 12 baseline sites among them; 180 M KRW a month in the capital region, 157.5 M in metro cities, 132 M elsewhere | Leasable logistics land, dearer near Seoul |
| `cost_parameters` | Teaching defaults [A §2.6] plus one assumption: a relay driver costs one owned vehicle-day | Finance's figures |
| `demand_history` | 365 days from 2025-10-01: store level (lognormal, mean 2.2 cages, clipped to 0.5-6) × weekday profile by store type × summer peak × Korean holidays and their eves × a chain-wide AR(1) shock (weather) × store-day gamma noise, Poisson counts | Weekends, summer, holidays, chain-wide moves, short histories |
| outcome tables | Our lower level on the baseline network over the 365 days, owned fleet = 0.671 quantile of that year's daily need | Labelled as produced by our own model [A §2.5] |

**Distances.**
Self-hosted OSRM v6.0.0, car profile, Geofabrik `south-korea-latest.osm.pbf` (OpenStreetMap data of 2026-10-18), ferries excluded.
Computed: every store-to-site pair (9,718 × 60) and each store's 50 nearest stores; cached in `code/data/road_cache.npz` (5 MB), so no network access is needed to reproduce anything.
Other store pairs use a model calibrated on 3,959 OSRM distances (straight-line km × a factor by distance band and a mountain class for Gangwon and North Gyeongsang; median error 20% for pairs of 1-10 km, 9% for 10-50 km and 4% for 50-250 km on a held-out half); 89-99% of the legs a route actually drives are OSRM values.
Travel time is road km / 35 km/h; engine durations are not used.
**Instance: not thinned.**
All 10,000 stores are kept, one stop per store, because thinning changes stop density and with it the clock mechanism that creates the trade-off in k [A §2.7]; the reduced run (1 store in 5, fixed cost and bounds scaled to 30 M and 100-280) is the thinning check of Section 4.

**Baseline network, and why it is plausible.**
A chain that grew over decades does not sit on today's optimum [A §2.5].
We model the last network redesign as done in 2016 by the same planning rule we would use, with the tools and stores of the time: a capacitated p-median on straight-line km over the 6,178 stores open in 2016, every store within one driver-day (125 road km, 96 straight-line km), at most 1,400 stores per DC, no minimum, built by adding one site at a time and then local moves between nearby sites, each assignment solved by the transportation LP (`code/prep/current_network.py`).
Stores opened since joined the nearest DC with room, in order of opening, and nothing was rebalanced.
The rule was fixed and recorded (decision D-069) before any redesign was scored against it, but it was adopted after an earlier baseline (a p-median on today's stores and road km) had beaten every redesign, so it is not blind to that result; the earlier baseline is kept as the reversal row that tests exactly this choice (Section 5), and the year of the last redesign is swept in Section 5 (the saving stays positive for every year from 2010 to 2026).
Plausibility evidence: every site is a candidate logistics site; the demand-weighted road distance from store to DC is 32.8 km against 31.8 km for the p-median optimum on today's stores and road km; the capital-region DCs carry 1,170-1,366 stores and the regional ones 116-789, as a grown network would.
What the decade of growth did: 38.3% of today's stores opened after 2016 and sit on average 45.6 road km from their DC, against 25.0 km for the stores the network was designed for; the capital-region DCs filled to 1,170-1,366 stores while Gangneung kept 116.
Redrawing the baseline's own territories by the assignment LP moves 1,098 stores and saves 268 M KRW a month (Section 5), and the same number of DCs placed for today's stores would cost 532 M a month less than the baseline network on the search days (5,922 against 6,454 M).
The opposite case, a network already optimal for today's stores, is reported as a reversal (Section 5).

**The demand model** (Lecture 2, `code/dcn/demand.py`).

$$y_{s,t}\mid\lambda_s \sim \mathrm{Poisson}(\lambda_s\, e_{s,t}\, \gamma_t),\qquad \lambda_s \sim \mathrm{Gamma}(a_{\tau(s)},\, b_{\tau(s)}),\qquad \lambda_s \mid \mathcal D \sim \mathrm{Gamma}\Big(a + \sum_t y_{s,t},\; b + \sum_t e_{s,t}\gamma_t\Big)$$

The exposure $e_{s,t}$ is the calendar multiplier of the store's type (weekday × month × holiday), estimated once over the whole chain for each of the four types; $\gamma_t$ is the chain-wide shock of day t, estimated from chain totals and divided out.
**Why per type, not one multiplier for the chain.** "Once for the chain" can be read as one weekday profile for all stores, but a row of `demand_history` means something different at an office store (weekend orders 0.70 of weekday) than at a residential one (1.12).
One profile would be wrong for every store in the same direction by type, and the error lands on DCs in proportion to their mix: up to 2.7% of a territory's weekend need for the baseline DCs (Andong, Gangneung) and up to 1.6% for the redesign (Wonju).
The owned fleet is the 0.671 quantile of each territory's daily vehicle need, so an error of that size moves the DC's owned fleet or its spot hires by about the same share; and because the error follows the type mix, it changes when stores are reassigned, so it would differ between the networks being compared and bias the comparison instead of cancelling.
Store type is a safe unit because it is a fixed attribute of the `stores` table, independent of the network, with hundreds to thousands of stores per type, so its profile is estimated precisely and travels with the store to whichever DC serves it.
The prior mean per store type comes from the chain; its strength $b$ is set from the long-history stores of each type (the spread of their rates beyond Poisson noise, matched to the Gamma's variance): 1.8-2.2 (residential 2.09, office 2.17, mixed 1.92, roadside 1.84) store-days.
The prior is worth about two days of a store's own orders, so after one week a new store's posterior already puts about 80% of its weight on its own data, and a store opened yesterday moves about a third of the way from its type's mean towards its first order; store ST00211 opened 61 days before the horizon and ordered 135 cages against 63.2 store-days of exposure; its prior Gamma(4.55, 1.92) (mean 2.37, mixed stores) becomes Gamma(139.6, 65.1), posterior mean 2.14 against its own data mean 2.14 (its true rate, hidden from the model, is 1.89).
Extra store-day variation beyond Poisson is gamma with shape κ = 8.1; the chain shock is AR(1) with φ = 0.46 and σ = 0.061.
**Posterior predictive for a planning day:** draw a calendar day of the planning year, the chain shock from its AR(1), each $\lambda_s$ from its posterior, then the counts.
A posterior predictive check replicates the history's chain totals (shown in the demo, Data & baseline tab).

**Sampled days versus one average day.**
On the recommended network and the 7 search days, sampled days give E = 5,982.0 M a month; the same days with each store's expected count instead of its sampled count give 5,956.9 M (25 M less: store-level noise largely cancels at the DC); one average day gives 5,923.7 M (58 M less, 1.0%).
The rest of the gap comes from chain-wide variation: weekday, weekend and holiday levels and the AR(1) chain shock move every store of a DC together, and the owned fleet is the 0.671 quantile over days, which an average day cannot see.
The peak day (2027-09-13) needs 763 vehicles against 642 owned.
The gap would grow with a stronger chain-wide shock (φ or σ) or a sharper holiday peak, which is why the fleet is sized on sampled days.

**Facts, assumptions, unknowns and requests.**

| Fact / assumption / unknown or request | Evidence or reason for current treatment | Why it matters | How to confirm or obtain it; priority | Fallback or limit until confirmed |
|---|---|---|---|---|
| Request: the real `deliveries`, `vehicle_days` and `spot_hires` for 12 months | Not handed over [A §2.5] | They measure the baseline network, and the saving is the distance between the baseline and the redesign (Section 5, reversals) | Logistics IT export; **highest** | The saving is a property of the fictional network; nothing is promised in KRW |
| Request: store sales (POS) next to orders | Orders are not shelf demand (table above) | Fleet sizing on smoothed orders may under-own vehicles | Merchandising data; **high** | Peak-day fleet and spot hires reported (Section 4, fleet row) |
| Request: real DC rents, dock counts and lease terms per site | Rents and docks are `[ASSUMPTION]` | The reversal in DC fixed cost; with 23 docks per DC the departure-wave check moves the best k from 10 to 12 (Sections 4 and 5) | Real-estate team and DC managers; **high** | Rent swept 100-200 M; docks checked at 23 and 29 |
| `[ASSUMPTION]` relay (two-driver) routes for stores beyond one driver-day, one extra driver-day each | Business decision B-01 | Prices far stores in both the baseline network and every redesign | Operations; **medium** | Relay price swept: free, one driver-day, the spot rate (Section 5) |
| `[ASSUMPTION]` orders do not depend on the delivery time slot | No data on ordering behaviour by slot | A redesign that delivers later could change orders | Real-data check (Section 6); **medium** | Report the share of stores whose delivery moves later by more than 2 h |
| `[ASSUMPTION]` 15 min per stop, 35 km/h | Teaching defaults [A §2.6] | They set the noon reach, which drives the k trade-off | GPS traces of one DC for a month; **medium** | Reversals at 10/20 min and 30/45 km/h, and their value of information (Section 5) |
| `TBD`: the after-14:00 penalty for stock-outs at 24-hour stores | Teaching default used | Only matters if a network misses deliveries; none of the compared networks does | Store operations | Default |
| Fact: road distances | OSRM on OpenStreetMap, cached | The Field Manager's point | Re-run with a newer extract | Calibrated model for pairs outside the cache |

**Register: where we deviate from the brief or assume what it does not give** (to be confirmed with the business; the brief's own values are used everywhere else).

| Item | Brief | We use | Why, in one line | Effect or check |
|---|---|---|---|---|
| Stores beyond one driver-day | About 250 km and a 10-hour shift per vehicle [A §2.3] | A relay route with a second driver: up to 500 km, on duty until 19:00, every stop still by noon `[ASSUMPTION; B-01]` | Without it, stores on the far east coast and in the mountains could not get their daily delivery from any DC the 500-1,400 bounds allow | Strict brief instead (no relay, those stores are stock-outs at 500,000 KRW): 48 stores of the baseline network and 126 of the recommendation lie beyond one driver-day (`checks/routing_gap.py`), and the best network checked (k = 11) costs 452 M a month **more** than the baseline, so the redesign reverses; with the minimum also dropped: a network that keeps a small coastal DC is allowed, and the best one (k = 12) saves 699 M a month |
| Price of the second driver | No price (the 5.5 M a month covers a vehicle with its driver) | 180,822 KRW per relay route-day, a full owned vehicle-day `[ASSUMPTION]` | The brief prices drivers only together with a vehicle; this is an **upper bound**, because the truck and its fuel are already counted and only a driver is added | Baseline network runs fewer relay routes than the redesign, so a lower price raises the saving: free 491 M, our price 469 M, at the spot rate 424 M (k = 11) |
| Shift timing | A 10-hour shift including loading | Loading 03:00-04:00, departure 04:00, return plus a 30-minute break by 13:00 `[ASSUMPTION]` | The brief does not time the shift, and a driver needs a break | Departure-wave check (next row) |
| Departure time | Vehicles leave between 04:00 and 07:00 | All leave at 04:00 inside E `[ASSUMPTION]` | The earliest start gives the most reach before noon and needs no dock schedule | Waves 04:00-07:00: with 23 docks per DC the best k moves to 12, with 29 it stays at 10 (Section 4) |
| Docks per DC | Not given | 23 (store cap × the baseline's vehicles per store ÷ 4 waves) `[ASSUMPTION]` | Needed only for the wave check, which it decides | With 23 docks the 10-DC network overflows the docks of its largest DCs by 3.3 vehicles a day; 25% more docks (29): best k back to 10. Real dock counts are a first data request (Section 6) |
| Delivery window | At least 98% before 12:00; failure after 14:00 | Every stop by 12:00 when routes are built | Simpler and conservative; the 2% slack is not used | All compared networks at 100% before noon |
| DC rent | 150 M a month per DC; higher in the capital region [A §2.5] | 180 M capital region, 157.5 M metro, 132 M elsewhere (150 M × 1.20 / 1.05 / 0.88) `[ASSUMPTION]` | The brief asks for dearer capital-region sites without a figure | Rent reversal at 100 M and 200 M |
| Spot trucks | 550,000 KRW a day; supply not stated | Unlimited at that rate `[ASSUMPTION]` | No limit is given | Peak day: 121 spot trucks above 642 owned |
| Fleet quantile | Two-thirds | 0.671, computed from the brief's own prices (one owned vehicle-day against the spot rate) | The same rule, computed exactly | None needed |
| Orders and the network | Not addressed | Orders do not change when a store's delivery time changes `[ASSUMPTION]` | No data on ordering by delivery slot | 24% of stores would be served more than 2 h later: first real-data check (Section 6) |
| Baseline network | Placed plausibly, as a chain that grew [A §2.5] | The 2016 planner's design with growth since (Section 3) | The brief gives no real network; this rule was fixed before scoring | Baseline network at the optimum instead: −60 M, the reversing row |
| Scope | Fresh food out of scope unless brought in; one-off costs not mentioned | Fresh food, Jeju and ferry-only islands, moving and opening costs left out | Allowed by the brief or not costable without data | Moving cost as a payback condition (Section 6) |
| Closure sequence | Leases expire one after another | First month a redesign can operate: January 2027; leases end on the fictional dates of `dcs` `[ASSUMPTION]` | Two months to fit out a site | Extensions (Section 5) |
| Value-of-information prior | Not given | 0.25 / 0.5 / 0.25 on low / reported / high stop time and speed `[ASSUMPTION]` | A neutral prior around the teaching defaults | EVPI reported as a lower bound |
| Traffic by time of day | One stated average speed [A §2.3] | 35 km/h at every hour `[ASSUMPTION]` | The brief allows one average speed; no hourly data | Speed reversal: at 30 km/h the best k is 11; GPS traces |
| Winter roads and closures | Not mentioned | Roads always open, no seasonal speed `[ASSUMPTION]` | No weather or closure data | Longer far routes; seasonal speeds from the GPS study |
| Driver hours and breaks | A 10-hour shift | A 30-minute break, no further limit `[ASSUMPTION]` | The brief gives no break rule | 262 of the recommendation's 633 routes a day are shift-bound and would lose stops under a longer break; confirm with HR |
| Drivers for new DCs | Not mentioned | Available wherever a DC opens `[ASSUMPTION]` | Hiring is outside the monthly model | Could delay a lease step, not change the target |
| Store unloading | 15 minutes per stop [A §2.6] | The same at every store `[ASSUMPTION]` | No store-level data | Stop-time reversal: at 20 min the saving is 427 M |
| Several trips per vehicle | Not mentioned | One trip per vehicle and day `[ASSUMPTION]` | Keeps the lower level a single-trip routing problem | Would lower vehicles in large territories; dispatch practice at one DC |
| Returns and empty cages | The driver collects empty cages [A §2.4] | They ride back at no capacity cost `[ASSUMPTION]` | Returns travel on the emptied vehicle | Only binds on full return legs |
| Breakdowns and spare vehicles | Not mentioned | No breakdowns `[ASSUMPTION]` | No fleet records | A failure is covered by a spot truck at 550,000 KRW a day |
| Fuel price and staff transfers | 350 KRW per km; no transfer cost given | Fixed fuel price; no transfer cost `[ASSUMPTION]` | Teaching default; transfers are one-off | Fuel moves every network alike; transfers belong to the moving cost (Section 6) |

**Main uncertainties and when not to trust the recommendation.**
The decision rests on how far today's real network is from the optimum (Section 5, last reversal row), on the stop time and speed that fix the noon reach, and on the rent level; demand noise moves the saving far less (Section 5 intervals).
Do not act on the recommendation before the real outcome tables have scored the baseline network under the same evaluation.

## 4. Alternatives & Selected Approach

**Approaches.**

| Approach | Mechanism and required information | Strengths, limitations, and effort | Selection and reason |
|---|---|---|---|
| Baseline | Keep the 12 baseline DCs and territories; renew leases as they expire | No transition cost or risk; carries a decade of drift (Section 3) | The reference every candidate is scored against, under the same E (Section 5) |
| Proxy-only: centre of gravity (`G0`) | The Data Team's method: centres of gravity on straight-line coordinates for a chosen k (Section 2), snapped to sites | Minutes; no road distances, no clock, no choice of k; optimal only for its own criterion | Rejected as the decider; scored under E for comparison: its best network (k = 13) costs 6,480.9 M a month on the search days, 498.9 M more than the best network found; 5 of its 13 networks miss 98% before noon |
| Proxy-only: best network under the cheap criterion | Search the pool by `G1` and pick its minimum, without any full evaluation | Milliseconds per candidate; ignores the noon deadline, so it favours fewer, larger territories | Rejected; its pick loses 356.7 M a month on the final days (it picks eight DCs, 6,467.5 against 6,110.9 M) under E (Section 5) |
| Generator knobs with BO (brief option i) | k, a volume exponent, a detour penalty and a minimum spacing as four continuous inputs to the generator, GP + EI on them | The GP's home ground; still produces G-optimal networks, so it shares G's blind spot unless G knows the clock | Considered, not built: the pool option below covers the same budget and lets us use `G2` directly |
| **Selected: pool + discrepancy GP + EI under a budget** | A pool of candidates per k from `G2`, `G1`, `G0`, baseline sites adjusted and random swaps; a Gaussian-process model of the gap E − `G2` over seven summary features; expected improvement picks the next full evaluation; B = 40 | Spends full evaluations where the cheap criterion is least trusted; needs the pool to contain good candidates (checked: the whole pool is also evaluated once for validation) | Chosen: it is the course's default (Lectures 4 and 5), it keeps G and E apart, and it beat random selection at the same budget (Section 5) |

**The solution-algorithm plan** (calculation flow, `code/dcn/pipeline.py`).

1. Build the world and fit the demand model (Section 3); draw 7 search days, 28 final days and 14 held-out days from the posterior predictive (seeds 448, 449, 450), the held-out days disjoint from the final ones.
2. Score the baseline: baseline sites and historical territories through E on the search days.
3. **Pool.** For every k from 7 to 19: the `G2` optimum (sites added one at a time from the k − 1 solution, then local moves to the 12 nearest sites), the `G1` optimum, the `G0` solution, baseline sites adjusted to k (drop or add one site at a time by `G2`, the natural move as leases expire one by one), and random one- or two-site swaps of these four, 390 candidates in all, each with its LP assignment, `G1`, `G2` and seven features: k, mean, 95th-percentile and maximum road km to the DC, load imbalance, the demand share beyond the 55 km noon reach and the store share beyond 125 km.
4. **Reported search, one fresh run of B = 40 full evaluations.** First the `G2` seed of every k (13 evaluations, one per number of DCs, as the brief requires); then 27 picks, each the pool member with the largest expected improvement under a Kennedy-O'Hagan model E(x) = `G2`(x) + δ(x), δ a Gaussian process (Matérn 5/2, one length scale per feature, hyperparameters by marginal likelihood) refitted after every evaluation.
   The pool is enumerable, so the acquisition is maximised exactly.
   Every evaluation is logged with the rule that chose it.
5. **Random selection at the same budget** on the same pool from the same 13 seeds (one run is logged; Section 5 also gives the distribution over 2,000 random orders, computed from the validation pass).
6. **Hand-over:** the five best candidates of the reported search that keep 98% before noon are re-scored on the 28 final days; the best becomes the recommendation, and is then checked on the 14 held-out days with the fleet fixed from the final days.
7. **Validation only, after the reported search:** every pool member is evaluated once on the search days, to measure G against E over the whole pool and to know the pool's best.

Budget justification: with the company's real routing system one evaluation would take hours [A §3.3]; 40 is the brief's default and here costs about 41 s on the 16 worker processes of the Spark (1.0 s per evaluation).
Randomness: only the demand days (fixed seeds) and the random swaps and random selection (seed 437 + offsets); the routing, the LP and the GP are deterministic, so the run reproduces exactly.
What is computed, what is precomputed: everything in this file is computed by `run_full.py`; the demo shows those precomputed results and runs the lower level live (Section 5).
No optimality is claimed for the recommended network: it is the best of 40 evaluations in the reported search, checked against the whole pool (balance table, search row).

**The fidelity-computation balance.**
The first row is the choice the conclusion hangs on most.

| Modelling choice | What the real operation does | What we model | What it costs to compute | What the simplification could get wrong | How we checked whether it changes the decision |
|---|---|---|---|---|---|
| Baseline network | A network grown and patched over decades, unknown to us in detail | The 2016 planner's design with growth since (Section 3) | Free | If the real network is closer to optimal, the saving shrinks | Re-scored with the baseline network placed at the optimum for today's stores: a 12-DC p-median on today's stores and road km costs 5,922 M a month on the search days, 60 M less than the best redesign: one of the two rows that reverse the recommendation; between the two, the year of the last redesign is swept from 2010 to 2026 (the saving stays between 220 and 643 M for every year; only the road-km design reverses it) (Section 5) |
| Distance model | Trucks drive roads; speed varies by hour | OSRM road km for every store-site pair and each store's 50 nearest stores, a calibrated model for other pairs; time = km / 35 km/h + 15 min per stop | One-off: 0.6 M site pairs and 0.5 M store pairs on the Spark, cached (5 MB) | Peak-hour slowdowns ignored, which flatters long routes; model pairs off by 20% for pairs of 1-10 km, 9% for 10-50 km and 4% for 50-250 km on a held-out half | Re-scored the best network of every k and the baseline with the calibrated model only and at 30 km/h: calibrated model only: k* = 9, saving 391 M; 30 km/h: k* = 11, saving 658 M; the saving keeps its sign and k moves by one |
| Instance size | 10,000 stores | All 10,000 (not thinned) | Full run 1,172 s on a DGX Spark with 16 worker processes: 876 s for the pipeline, 296 s for the extensions; reduced run (1 in 5) 8 min on a laptop with two worker processes | Nothing from thinning; slower development | Reduced run against full run, k by k: the reduced sweep's minimum is at k = 11 against 10 for the full instance (after re-scoring its top five on 28 days the reduced run recommends 9; 9, 10 and 11 lie within 1.2 M of each other there); cost per store 1.19-1.24 times the full run's for k = 8 to 19 (1.44 at k = 7); km per store 1.50 times the full run's for the baseline network, below the √5 = 2.24 the continuous approximation predicts because the out-leg does not shrink with density; the reduced instance cannot separate 9, 10 and 11 |
| Demand model and days | Store orders with calendar, shocks, short histories | Poisson-Gamma with chain exposure and AR(1) shock; 7 search days, 28 final, 14 held-out | 28 days cost four times 7 | A 0.671 quantile from 7 days is noisy; rankings may change with more days | Top five re-scored on 28 days: the search's best stays first on 28 days (6,110.9 M); the next three (k = 9, 11 and another 10) lie within 45 M of it; sampled versus average day: one average day understates E by 58 M a month (1.0%) |
| Routing method | Experienced dispatchers | Step-by-step construction with masked stores, segment reversal, relay pass (Lecture 0's construct and improve), deterministic | 0.18 core-seconds per territory-day | 7.2% of operating cost above PyVRP on the baseline network and 6.6% on the recommended one; on 7-store cases 0.5% above the exact optimum | PyVRP on every territory of both networks, one search day (Section 2a): the saving falls from 469 to about 442 M a month and keeps its sign; the best 9-, 10- and 11-DC networks under PyVRP: ten stays best |
| Delivery window | ≥ 98% before 12:00, failure after 14:00 | Every stop by 12:00 (hard) | A check on every insertion | Leaves the 2% tolerance unused, over-stating vehicles slightly | Every compared network reaches 100% before noon on every final day; the slack is a saving we do not claim |
| Departure and docks | Waves 04:00-07:00 limited by docks | Every vehicle leaves at 04:00 | None | Flatters large DCs, so it favours fewer DCs | Departure waves with 23 docks per DC: k* 10 → 12, because the 10- and 11-DC networks overflow the docks of their largest DCs by 3.3 vehicles a day (the 12-DC network costs 66 M a month more than ten under waves and still saves 417 M against the baseline); with 25% more docks (29): k* 10. The dock count decides k between 10 and 12, so it is a data request (Section 3) |
| Assignment | Historical territories | Window-aware transportation LP inside E (Section 2b) | One LP per evaluation | Distance-optimal is not route-optimal | The LP beats the historical assignment on the baseline's own sites (Section 5, saving decomposition) |
| Fleet policy | Vehicle contracts, spot market | 0.671 quantile of daily need, unlimited spot trucks at 550,000 KRW | Free | Spot supply may be capped on peak days | Peak day reported: 2027-09-13, a holiday eve: 763 vehicles needed against 642 owned, 121 spot trucks (66.5 M that day), 100% before noon |
| Candidate set | Real-estate options | 60 sites at interchanges and logistics zones, the 12 baseline sites included | Pool size | The optimum may sit off the list, or among site sets the pool never held | Inside the list: a learned generator samples site sets the pool never held (Section 5, candidate generation); off the list: `TBD` with the real-estate team (Section 3, requests) |
| Number of DCs swept | Any k the bounds allow | k = 7 to 19, one `G2` seed each | 13 of the 40 evaluations | Wasted evaluations on hopeless k | All 13 reported in the sweep (Section 5) |
| Search and budget | Hours per real evaluation | Pool + discrepancy GP + EI, B = 40 | 40 evaluations | Misses the pool's best | The whole pool evaluated once for validation: all 390 candidates evaluated; the search found the pool's best at evaluation 14 |

**Where computation was spent and why.**
On the lower level and on full density, because the trade-off in k comes from the clock: a route that leaves at 04:00 must reach its last stop by noon, so the out-leg of a large territory eats the time for stops, and that mechanism only shows with real stop density and real road distances.
The upper level gets the cheapest adequate tool, a pool and a surrogate, because the location effect within a given k is small next to the count effect (Section 5).
**First simplification to remove with more time:** time-of-day speeds (the 04:00-07:00 departure lies before the morning peak, but returns to capital-region DCs do not).
**The two checks above that could have changed the decision**, distance model and departure waves: the calibrated distance model moves k* from 10 to 9 (keeping ten costs 8 M a month in that case) and keeps a 391 M saving, so it changes the size and the best k by one but not the sign; departure waves move k* to 12 with 23 docks per DC and leave it at 10 with 29, so the real dock count at the largest DCs is needed before the number of DCs is fixed (Section 6).

**The remedy for the G-E gap.**
`G1` ignores the clock, so it rates large territories too well and picks too few DCs (a least-squares line from `G1` to E explains R² = 0.25 of E over the evaluated candidates; searched over the whole pool, its pick has eight DCs and loses 356.7 M a month).
We applied the remedy the brief names as system knowledge: `G2` adds the routes the noon deadline and the 250 km limit force (Section 2).
On the evaluated candidates the line from `G2` explains R² = 0.57 of E (0.70 over the whole pool, 0.44 within one k), and its pick loses 36.5 M a month, picking k = 10 as E does.
`G2` still misses the level (it over-states E by a median of 924 M, more for poor candidates: standard deviation 3,155 M over the pool), so the discrepancy GP models E − `G2` over the seven features rather than trusting `G2`'s value.

## 5. Demonstration & Evaluation

**Running the code.**
From `code/`: `pip install -r requirements.txt` (numpy 2.2.6, scipy 1.15.3), `python run_full.py` (all 9,718 planning stores, the reported run; 1,172 s on a DGX Spark with 16 worker processes: 876 s for the pipeline, 296 s for the extensions), `python run_reduced.py` (1 store in 5, 8 min 8 s with two worker processes on a laptop).
Seed 437; distances from the shipped cache, no network access.
The reduced run repeats the network search and the evaluation (pool, search, validation, final and held-out days, the R2 and R3 measures) with 1,938 stores and leaves out what only the full run reports (outcome tables, departure waves, reversals, extensions); it has fixed costs and store bounds scaled by one fifth (30 M a month, 100-280 stores) and a pool of 14 candidates per k instead of 30; it reproduces the structure of the results (Section 4, thinning row).
Each run writes `results/<profile>/registry.json` and the input tables of [A §2.5]; the full run also writes the outcome tables, holds every number in the three deliverables and rebuilds `demo.html` and `proposal.html`.
`python verify.py` re-checks the shown run independently: 29 of 29 checks pass (`results/full/verification.json`): every store of the shown day served once on both networks, no route breaking a limit unflagged, cost identities, the paired saving, the LP within its bounds, a deterministic evaluation that is the same with one or two worker processes, departure waves, the outcome tables, the router against exact enumeration, the page's JavaScript engine against the Python one, no external resources in the page, the local app's live solve, the embedded registry, both least-squares R² values, the extensions, and the drift sweep reproducing the baseline network in its 2016 row.
The hand-in ZIP, extracted into a fresh Python 3.10 environment from `requirements.txt` and run offline (`unshare -rn`, `run_reduced.py`, two workers, 8 min 8 s on a laptop), reproduces an earlier laptop run of the same code in all 57,807 values of the registry; the shipped reduced registry is this fresh run's.

**The demonstration.**
`demo.html` opens offline from the extracted folder (checked in Chromium 149 (Playwright 1.61) with the network disabled: every request other than `file://` blocked, none attempted; no console error on any tab; no horizontal scrolling at any of ten widths from 390 px (phone) to 1920 px; the delivery-day animation runs at 60 frames per second).
Its tabs follow the decision, and a *Find an answer* index in the navigation bar jumps from 28 business and analyst questions to the card that answers each.
*The answer* maps the baseline and the recommended network (`D1-network`, `D2-assignment`) and can play the change from the baseline territories to the new ones; it shows the saving's decomposition, every evaluated network on one cost axis with the six tests the recommendation passed, the recommended network DC by DC, the reversal table, the sweep with its two components against k and the four statements.
*Delivery day* animates every route of one day on the road network for either network, with each DC's share of stores served and the day against the clock, and solves one DC live (`D4-routing` with the owned fleet of `D3-fleet`) while the reader changes the demand day, the deadline, the stop time, the speed, capacity, stops and the fleet.
*How it works* steps through the formulation by lecture (Q1-Q7): the I/O schema; the demand model and the sampled against average-day cost; the lower level and what one solve returns; the connection and what passes down and up; the upper level with its linear and combinatorial parts, the 40 evaluations with the rule that chose each, a log table and random selection; `G2` or `G1` against E for every evaluated candidate (R3); and the balance table of Section 4.
*Data & baseline* explains how and why the data were generated, lists the eight tables with what one row cannot tell, holds the assumption register and shows how the baseline network grew from 1990.
*Checks* holds the normal, boundary and failure cases, the balance-table checks, the router check, the outcome tables, the store-level view and the verification record; *Extensions* shows the closure sequence, robustness, the value of information, the drift sweep and candidate generation.
The page's live solve is a simplified copy of `dcn/routing.py` in JavaScript (no segment reversal, the calibrated distance model instead of the road cache) and says so; on the shipped day it gives the same vehicles and kilometres as the Python engine without the segment reversal (`verify.py`).
`python app.py` serves the same page on `http://localhost:8437` and answers the live solve with `dcn/routing.py` on the cached road distances, the exact rules of the reported run.
Every precomputed number on the page carries a tag naming the command that reproduces it.

**Comparison conditions shared by every network.**
The same lower level, the same road distances, the same sampled days, the same fleet policy and the same E; the baseline differs only in keeping its historical territories, as the brief prescribes [A §2.3], and the step "baseline sites, re-assigned" isolates that difference.
Information used to choose and outcomes used to report are kept apart: the 7 search days choose the network; the 28 final days only re-score the top five and measure the reported saving; the 14 held-out days, disjoint from the final ones, are never seen by the search, and on them the owned fleet stays as sized on the final days.

| Case | Inputs / reproduction steps | Expected result / pass criterion | Observed result and supported conclusion |
|---|---|---|---|
| Normal | *Delivery day* tab, "Solve one DC live": Gimpo Gochon (1,400 stores of the recommendation), ordinary weekday 2026-11-04, default limits; or `python app.py` and the same request | Every store visited once; no route breaks load, stops, km, the shift or the noon deadline; vehicles at or above the load and stop bound | In the page: 68 vehicles, 5,271 km, 100% before the deadline, 0 uncovered stores (in-browser engine, no segment reversal, calibrated distances); with `python app.py`: 71 vehicles, 5,329 km on the cached road distances, the same as `routing.solve` (`verify.py`). Every route audited from coordinates and demand: 0 violations. The routing works on a full 1,400-store territory in about a second |
| Boundary | *Checks* tab, boundary card; *How it works* Q5, search step slider at 1 | The DCs at a bound are named; with B = 1 only the first seed is evaluated | Gimpo, Namyangju and Siheung sit at the 1,400-store cap and Wonju and Gyeongju at the 500 minimum; the assignment LP's duals (`price_hi`, `price_lo` in the registry) value one more store of cap at 97-116 and one store less of minimum at 31-120 cage-km a day. With B = 1 the search returns the k = 7 seed at 8,605 M a month, worse than the baseline (6,454 M); with B = 40 it returns 5,982 M |
| Failure | *Checks* tab, failure card, and its button "Show the peak day with 12 vehicles"; or `evaluate.evaluate(ctx, sites[:6], days)` | No cost shown; the reason stated; uncovered stores named as such | "6 DCs cannot hold 9,718 stores within 500-1,400 per DC": the bounds make k ≤ 6 infeasible, and the page shows the reason instead of a number. A second failure mode, a day the fleet cannot cover: on the peak day (2027-09-13) the model hires 121 spot trucks above the 642 owned; capping the live solve at 12 vehicles shows the uncovered stores and their stock-out penalty instead of a valid-looking plan |

**Baseline and recommendation, on the 28 final days** (M KRW a month).

| Network | k | Fixed | Owned fleet | Fuel | Spot | Relay | Total | Vehicles a day | Before noon |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline (historical territories) | 12 | 1,878.0 | 3,597.0 | 909.3 | 112.8 | 82.5 | **6,579.6** | 644 | 100% |
| Baseline sites, territories redrawn by the LP | 12 | 1,878.0 | 3,476.0 | 823.5 | 111.6 | 22.0 | 6,311.2 | 623 | 100% |
| Best 12 sites | 12 | 1,728.0 | 3,476.0 | 851.2 | 109.1 | 88.0 | 6,252.3 | 621 | 100% |
| **Recommended** | 10 | 1,464.0 | 3,531.0 | 899.4 | 111.9 | 104.5 | **6,110.9** | 633 | 100% |
| Strategy's eight (best k = 8), also the proxy's pick (lowest `G1` in the pool) | 8 | 1,248.0 | 3,789.5 | 1,094.6 | 110.0 | 225.5 | 6,467.5 | 681 | 100% |

The saving of the recommendation is **468.7 M KRW a month** on the final days (90% bootstrap interval over days 456.0-482.1; the days are resampled within their calendar class, as Lecture 5 resamples data for an ensemble) and **469.3 M** on the held-out days (462.6-475.7), with 100% of deliveries before noon on every day for both networks.
It decomposes into 268.4 M from redrawing the baseline territories (the decade of growth without rebalancing), 58.9 M from moving to the best 12 sites and 141.5 M from running 10 DCs instead of 12.
The Strategy team's eight DCs save 112 M against the baseline but cost 357 M more than ten: fewer DCs save rent and lose more on longer drives, as Delivery Operations warned.
The recommendation moves 8,154 stores to another DC; 1,075 of them end up more than 30 km farther from their DC, all still served before noon.

**Prediction quality and decision quality (R3).**
Prediction quality, as Lecture 5 measures it, is the error of G as a predictor of E; we fit a least-squares line E ≈ a + b·G (Lecture 2) and report its R² and RMSE, so a G that is biased but well ordered still scores well. Over the 40 candidates the search evaluated, the line from `G2` explains R² = 0.57 of E (RMSE 355 M; 0.70 over the whole pool of 390, 0.44 within one k); its own pick is the k = 10 network E also prefers, and loses 36.5 M a month against the best evaluated candidate (decision quality).
`G1`, the same criterion without the clock, explains R² = 0.25 (RMSE 470 M; 0.14 over the pool), picks k = 8 among the evaluated candidates and loses 359.5 M there, and, searched over the whole pool, picks an eight-DC network that loses 356.7 M a month on the final days.
Neither criterion gets the level right (taken at face value, `G1` under-states E by a median of 749 M, $R^2$ −2.55; `G2` over-states it by 924 M, $R^2$ −2.88), which is why the search models the gap E − `G2` instead of trusting G's value.
The cause of the gap is the noon deadline: a route out of a large territory spends its morning on the out-leg, so for 262 of the recommendation's 633 routes a day the binding limit is the driver's shift and for 2 more the noon deadline, about as many as are full (282), while `G1` counts only load.

**The sweep** (search days, M KRW a month): for each k the best network of the whole pool, from the validation pass that evaluates all 390 candidates after the reported search, not only the 40 the search chose.

| k | 7 | 8 | 9 | **10** | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | 1,116 | 1,248 | 1,332 | 1,464 | 1,596 | 1,728 | 1,860 | 1,992 | 2,316 | 2,496 | 2,628 | 2,760 | 2,988 |
| Operating | 6,923 | 5,093 | 4,687 | 4,518 | 4,406 | 4,373 | 4,383 | 4,531 | 4,412 | 4,441 | 4,418 | 4,588 | 4,466 |
| Total | 8,039 | 6,341 | 6,019 | **5,982** | 6,002 | 6,101 | 6,243 | 6,523 | 6,728 | 6,937 | 7,046 | 7,348 | 7,454 |

Operating cost falls steeply up to ten DCs and is flat beyond twelve, while rent rises by about 150 M per DC, so the total is U-shaped with its minimum at k = 10; k = 9 and k = 11 are within 37 M (0.6%), less than a 5-minute change in stop time moves the costs, so the recommendation is "ten, with nine or eleven as near-ties", not a sharp optimum.
Baseline network costs 6,454 M on the same days.

**The log and the rule's worth (R4).**
The reported search spent B = 40: the `G2` seed of every k from 7 to 19 (13 evaluations; the best, k = 10, at 6,018.5 M), then 27 expected-improvement picks; the 14th evaluation found the pool's best, a k = 10 network at 5,982.0 M, which no later pick beat.
Random selection with the same seeds and the same budget ended at 6,018.5 M, the best seed: in 87% of 2,000 random orders the 27 random picks never improved on the seeds, because 1 of 377 remaining candidates is the best.
The rule's worth is therefore 36.5 M a month on the search days and, more usefully, a guarantee the brief asks for: the whole pool was evaluated afterwards for validation, and the search had found its best member.
Most of the value of the search sits in the generation step, not the selection step: the clock-aware seeds alone come within 0.6% of the best.
Every evaluation is in `registry.json` (`log_bo`, `log_random`) with step, candidate, sites, k, `G1`, `G2`, E, service and the rule that chose it.

**Sampled days versus one average day (R2)** is reported in Section 3.

**When the recommendation reverses (R5).**
Baseline network and the best evaluated network of every k re-scored on the search days with one assumption changed.

| Changed assumption | k* | Saving against the baseline (M a month) |
|---|---:|---:|
| As reported | 10 | 472 |
| Stop time 10 min / 20 min | 10 / 10 | 478 / 427 |
| Speed 30 km/h / 45 km/h | 11 / 9 | 658 / 461 |
| Calibrated distance model for every pair | 9 | 391 |
| DC fixed cost 100 M / 200 M a month | 11 / 9 | 358 / 618 |
| Relay driver free / at the spot rate (final days) | 10 / 11 | 491 / 424 |
| 500-store minimum dropped for redesigns | 11 | 553 |
| **Strict brief: no relay routes, stores beyond one driver-day are stock-outs** | 11 | **−452** |
| Strict brief and no 500-store minimum for redesigns | 12 | 699 |
| Departure waves 04:00-07:00 with 23 docks per DC / 29 docks | 12 / 10 | 417 / (k* unchanged) |
| Routes built by PyVRP instead of ours (day 0, measured; k not re-searched) | (10) | about 442 |
| **Baseline network already optimal for today's stores** (p-median on road km, 12 DCs) | 10 | **−60** |

Two rows reverse the conclusion.
First, if today's real network were already as good as a p-median design for today's stores, keeping it would be 60 M a month cheaper than the best redesign: the redesign's value lies in how far today's real network is from a design on road km for today's stores (swept by design year below).
Second, if the business holds every vehicle to the brief's one-driver limits and also keeps the 500-store minimum, the far east-coast and mountain stores can be served neither by relay routes nor by a small DC near them, and the best redesign checked costs 452 M a month more than the baseline (126 of the recommendation's stores lie beyond one driver-day against 48 of the baseline's); allowing either the second driver (the main case, 472 M) or a small coastal DC below 500 stores (12 DCs, 699 M) restores the saving.
Which of the two the business accepts is a decision to make before any lease (register, Section 3).

**How far must the baseline network have drifted? (the first reversal, swept).** Baseline network rebuilt by the same planning rule as if the last redesign had been in another year (straight-line p-median over the stores open then, later stores added without rebalancing), each scored under E on the search days against the best redesign (`dcn/extensions.py`; the 2016 row reproduces the baseline network exactly).

| Year of the last redesign | 2010 | 2013 | **2016** | 2019 | 2022 | 2026 |
|---|---:|---:|---:|---:|---:|---:|
| Stores open then | 4,197 | 5,188 | 6,178 | 7,168 | 8,300 | 10,000 |
| Baseline cost (M a month) | 6,625 | 6,399 | 6,454 | 6,227 | 6,202 | 6,235 |
| Saving of the best redesign (M a month) | 643 | 417 | **472** | 245 | 220 | 253 |

The saving stays positive for every year: even a network drawn in 2026 for all of today's stores keeps 253 M, because it is planned on straight-line km and without the noon clock.
The saving is not monotone in the year, because each year's design is a different discrete set of sites.
Only a design on road km for today's stores (the reversal row, −60 M) removes it, so the saving rests on how the baseline network was planned as much as on when; the first real-data check (Section 6) measures both, by scoring today's real network under the same E.
The number of DCs moves between 9 and 11 under every single changed input, never to 8; two inputs give 12: the strict brief with the minimum dropped (a small coastal DC kept) and departure waves with 23 docks per DC.

**Extensions (additional points).**

*A sequence of closures.* The leases end one after another (Gimpo 2027-03 to Gangneung 2029-12), so the redesign is a sequence of decisions with a state: the set of open sites and the end date of each lease (`D1` becomes Stateful when the boundary includes time).
`dcn/extensions.py` follows the twelve expiries from January 2027: at each, the site is renewed for ten years or closed, and sites of the recommendation are opened, whichever gives the lower monthly E (search days, territories redrawn by the LP, no store minimum while the network is in transition).
Four policies over 36 months, in bn KRW: keep everything as it is 232.3; redraw the baseline territories only, no lease touched 222.3; follow the leases committed to the recommendation 220.1; switch to the recommendation at once 246.0, because the released sites' rent (30.7 bn) runs until their leases end.
Switching at once therefore costs 13.7 bn more than changing nothing, while following the leases saves 12.2 bn, 10.0 bn of it from redrawing territories, which needs no lease at all.
A myopic policy (whatever is cheapest at each expiry) renews Incheon, Yongin and Gangneung for ten more years and ends at 11 DCs; it is 1.5 bn cheaper over the 36 months, because it skips the months in which a closed DC's replacement is not yet open, and its end state even costs 6.0 M a month less than the committed one under the same pricing (5,918.1 against 5,924.1 M).
But it keeps Gangneung with 123 stores, far below the 500 a redesign must hold [A §2.3], so it ends in a network the brief's bounds do not allow; what dropping the minimum is worth is the reversal row above (553 M with 11 DCs).
Conclusion: the one-shot design is the right target but not the right plan; within the brief's bounds the plan is the committed sequence (Section 6).

*Robustness.* The best network of every k from 7 to 13 and the baseline network re-scored on the same search days with demand scaled (`dcn/extensions.py`).

| Scenario | Best k | Saving of k = 10 (M a month) | Regret of k = 10 (M a month) |
|---|---:|---:|---:|
| As reported | 10 | 472 | 0 |
| Chain volume −15% | 10 | 430 | 0 |
| Chain volume +20% | 10 | 481 | 0 |
| Capital region +30% (Seoul, Gyeonggi, Incheon) | 10 | 489 | 0 |
| Calibrated distance model for every pair | 9 | 383 | 8 |

A demand regime shift never moves the best k, and the saving stays between 430 and 489 M a month.
The distance source matters more (the saving falls by about a fifth with the calibrated model only), but the decision moves by one DC and costs 8 M a month if taken anyway.
These scenarios change the regime, not the unobserved quantity behind the records, so they show robustness, not a second world consistent with the same history; the one such world we test is the baseline network being already optimal (Section 5, reversals).

*Value of information.* Lecture 3's expected value of perfect information, with today's decision taken under a prior and the decision after measuring taken per scenario: $\mathrm{EVPI} = \sum_s p_s E_s(a^\star) - \sum_s p_s \min_a E_s(a)$, over the networks of the sweep for k = 7-13 (a lower bound, since better networks per scenario may exist).
*Measure travel times:* stop time 10/15/20 min × speed 30/35/45 km/h, prior 0.25/0.5/0.25 on each, independently `[ASSUMPTION]`; nine re-scorings of every k.
The best k ranges from 9 (45 km/h) to 11 (30 km/h); under the prior the best decision now is eleven DCs (expected regret 25.1 M a month), with ten close behind (38.8 M), so EVPI = 25.1 M a month, about 3.0 bn over a ten-year lease, against a GPS study of one DC for one month.
*Collect more demand history:* EVPI over chain volume −15% / as now / +20% is 0 (k = 10 is best in all three), and evaluating every network on days drawn from the true store rates, which the generator knows and the model does not, leaves k = 10 best with a saving of 470 M (regret 0).
More history cannot change the decision because the network depends on where stores are and how long a stop and a kilometre take, not on each store's exact rate.
**Decision, reconciled with the recommendation:** under the prior, eleven DCs has the lower expected cost (by 14 M a month), while at the reported 15 min and 35 km/h ten is best.
The choice between them does not have to be made now: the best 9-, 10- and 11-DC networks take the same action at every one of the twelve lease expiries (keep Gimpo and Cheonan, give up the other ten), and eleven is ten plus Jinju Sabong.
So the plan follows the leases now and decides whether to add Jinju after the GPS study has measured stop time and speed; that is exactly the information the EVPI says is worth having first.

*Candidate generation (Lecture 6).* A learned generator, after Lecture 6's CbAS: for k = 9, 10 and 11 a product of per-site inclusion probabilities, fitted to that k's pool, then refitted four times on 200 proposals each toward networks the search's own surrogate (G2 plus the GP on its 40 evaluations) predicts below a rising bar (the 20th percentile of its predictions), each draw weighted by the prior ratio (`dcn/extensions.py`).
The four best new networks of each k, all absent from the pool, were evaluated in full on the search days: the best costs 6,063 M against the pool's best 5,982 M (1.4% more); between 53% and 75% of the sites in the two networks together are not shared with the pool's best network of its k, and the surrogate's prediction missed E by up to 5.7% in either direction.
What it buys the search here is diversity, not a better optimum: the clock-aware seeds and their local moves already hold the best networks of this instance, and the generator's refits drift towards where the surrogate is wrong, the lecture's warning, which is why every generated network is judged by E.
It would pay with a weaker pool (no clock-aware G, or a longer candidate list), where local moves never reach the good regions.

**Register of runs and tests.**

| What | Where, how | Result |
|---|---|---|
| Road-distance cache | Self-hosted OSRM v6.0.0 on a DGX Spark, queried from the laptop (extract in Section 3) | 9,718 × 60 store-site pairs and each store's 50 nearest stores, 0 unroutable; calibrated model error 20% / 9% / 4% by distance band |
| Baseline network (2016 planner) | `prep/current_network.py` | The 12 sites of `geo.CURRENT`, unchanged after the stable-sort fix |
| Full and reduced pipelines | Seven full runs on the Spark (16 workers), reduced runs on the laptop (two workers) | Run history in Section 7; the reported run is run 7 |
| Cross-machine reproducibility | Run 5's reduced run on aarch64 (Spark) and x86_64 (laptop), the same pipeline with the earlier router | 52,205 of 52,206 numbers equal to 1e-9; one expected-improvement value 0.07% apart |
| Fresh-environment reproduction | The hand-in ZIP extracted, a new Python 3.10 environment from `requirements.txt`, network cut off | All 57,807 registry values equal to an earlier run of the same code; 8 min 8 s on two laptop cores |
| Router against an exact solver | Exact enumeration on 25 territories of 7 stores (`verify.py`) | 0 extra vehicles; km 8.9% above the optimum on average (at most 32.5%); day cost 0.5% above on average (2.1% at most) |
| Router against PyVRP 0.11.3 | Every territory of the baseline, the recommendation, the redrawn baseline and the best 9- and 11-DC networks, one search day; a second pass at 0.5 s per store where PyVRP left stores unrouted | 653 against 610 vehicles on the baseline, 636 against 598 recommended; the saving would be about 442 M; ten stays the best k |
| Router choice and speed-up | Four course-based routers on 44 territory-days of both networks against the earlier savings router; the chosen one sped up (nearest-store sets by partition, plain indexing) | Chosen router 2.0% more vehicles than savings, about the same on both networks; after the speed-up routes identical bit for bit on the 44 territory-days and a tie-heavy case, a third faster; JavaScript copy identical on five territories |
| Reversal rows, departure waves, thinning, extensions | Inside the full run | Sections 4 and 5 |
| `verify.py` | Independent re-check of the shown run | 29 of 29 pass |
| Demo and proposal in a browser | Playwright, Chromium 149, offline, ten widths, every tab and all 17 slides | No console errors, no blocked requests, no overflow; 60 frames per second on the delivery day |
| Lint | `ruff` on `dcn/`, `verify.py`, the run scripts | No errors in the error classes (F, E9) |

**What the demonstration establishes and what it does not.**
It establishes, in the fictional instance, that the evaluation is consistent (every route audited, cost identities hold, the saving is paired), that a stronger router would cut the saving by about 6% but not remove it, that the search finds the best network of its pool, that the cheap criterion without the clock would have chosen eight DCs and lost 357 M a month, and that ten DCs beat the baseline network by about 470 M a month on days the search never saw.
It does not establish any saving for Dasol's real network: the baseline's distance from a good design is an assumption (Section 3), and the first reversal above shows that this distance carries the saving.
`Not run`: time-of-day traffic, the fresh-food second wave, moving and opening costs.

## 6. Client Proposal

**Management's two questions, answered for the fictional instance.**
*How many DCs?* Ten, with nine and eleven as near-ties (within 37 M a month of ten); eight, the Strategy team's proposal, costs about 360 M a month more than ten, and twelve or more cost more in rent than they save on the road, unless the DCs have fewer loading docks than assumed (with 23 docks per DC the departure-wave check prefers twelve).
*Where?* Gimpo Gochon and Cheonan Seobuk (kept), and Namyangju Jingeon, Siheung Banwol, Wonju Munmak, Nonsan Yeonmu, Naju Bitgaram, Gimhae Hallim, Gyeongju Oedong and Chilgok Waegwan (new); Namyangju and Nonsan appear in all five best networks and every other site except Gyeongju in four; the best networks for 9, 10, 11 and 12 DCs all keep Gimpo and Cheonan and give up the other ten leases.
**Estimated saving:** 469 M KRW a month against the baseline network, with every store still served before noon.
The 90% interval 456-482 (469 M on held-out days) covers only the sampled demand days; the model checks move it much more: about 442 M with routes from a stronger solver (PyVRP; our router is about 7% dearer on both networks, Section 2a), 391 M with the calibrated distance model for every pair and 417 M with departure waves at 23 docks per DC (12 DCs).
A fair range for the fictional instance is therefore about 390-470 M a month, positive under every check except a baseline already at the optimum and the strict reading of the brief.
This is a demonstrated result of the fictional instance only.
For Dasol's real network the saving is unknown: it equals how far today's real network is from a design on road km for today's stores, which only the real outcome tables can measure (Section 3); in the fictional instance it stays positive whatever year the last redesign was made (Section 5).

**What would reverse it.**
A real network already close to the optimum for today's stores (−60 M a month), or a business that accepts neither relay drivers on far routes nor a small coastal DC below 500 stores (−452 M a month; Section 5, reversals); short of reversing it, a measured stop time or road speed far from the defaults (they move the best number of DCs between nine and eleven) or fewer loading docks than assumed (twelve DCs with 23 docks per DC).
Rent, the distance model, the relay price, the store minimum, departure waves, demand shifts and the routing method change the size of the saving, not its sign (Section 5 and the extensions).

**Risks and mitigations** (likelihood: my guess for the real chain; impact: measured in the fictional instance).

| Risk | Likelihood | Measured impact | Mitigation |
|---|---|---|---|
| Today's real network is already close to a good design | Medium | Reverses: keeping it is 60 M a month cheaper | Real-data check before any new lease |
| Neither a second driver on far routes nor a small coastal DC is allowed | Unknown, a business rule | Reverses: −452 M a month | Decide the rule now |
| Stop time or speed differ from 15 min and 35 km/h | Medium | Best k between 9 and 11; saving 427-658 M | GPS study; the best 9- to 12-DC networks take the same lease steps until 2029 |
| Our router is weaker than a state-of-the-art one | High (measured) | About 7% of operating cost on both networks; saving about 442 M instead of 469 M | Re-score with a stronger router before the 2027-12 steps |
| Rents differ from the assumed tiers | Medium | Best k 9-11; saving 358-618 M | Real rents |
| The largest DCs have fewer loading docks than 29 | Medium | With 23 docks the departure-wave check prefers 12 DCs; saving 417 M | Dock counts from the DC managers before the second lease step; 9-12 DCs take the same first steps |
| One-off moving and opening costs | Certain | Not costed; 5.6 bn KRW pays back within a year | Finance prices them; proceed gate |
| Stores served later order differently | Medium | About a quarter of stores served two hours or more later | Store sales next to orders |
| Demand shifts (−15% to +20%, capital region +30%) | Medium | Best k stays 10, saving at least 430 M | None needed; follow at the next expiry |
| Spot trucks short on peak days | Medium | 121 spot trucks on the peak day | A framework contract, or a higher owned quantile |

**What to obtain first, and the first real-data check** (requests in Section 3).
1. The 12 months of `deliveries`, `vehicle_days` and `spot_hires`, with today's real territories: re-route today's real territories with our lower level under the same E and compare that with the best redesign, so that both sides use the same router; this is the check the whole saving hangs on.
   The real tables are compared with our routing of the same days separately: that gap is what better dispatching alone would save, and it must not be counted as part of the redesign.
   The same check asks the stores that would be served later: on the shown weekday 2,295 stores (24%) receive their delivery more than two hours later under the recommendation and 3,272 more than an hour earlier (from the routes stored in `registry.json`, `show`); if late delivery raises their orders, the assumption that orders do not depend on the network (Section 3) fails for them.
2. One month of GPS traces of one DC: the real stop time and speed, the two inputs that move k.
3. Real rents, lease terms and loading-dock counts of the 12 baseline sites and of the shortlisted new sites: the dock count decides between 10 and 12 DCs (Section 4, departure waves).

**Conditions.**
*Proceed* with the lease sequence below if today's real network, scored under the same E, costs more than the best redesign by more than the one-off cost of moving (to be priced by finance; at 469 M a month, a one-off cost of 5.6 bn KRW pays back within a year).
*Revise* the number of DCs if the measured stop time or speed lies outside 10-20 min or 30-45 km/h, or if the largest DCs have fewer than 29 docks: re-run `run_full.py` with the measured values, three commands and about 20 minutes.
*Stop* and renew leases as they expire if the real network comes within the moving cost of the best redesign.

**How to implement: follow the lease expiries.**
Renew Gimpo Gochon (lease ends March 2027; it is in the best network for every number of DCs from 9 to 12).
From June 2027, close each site outside the recommendation when its lease ends and open the new sites as they pay: Namyangju Jingeon when Hanam closes (2027-06), Siheung Banwol when Incheon Namdong closes (2027-09), Wonju Munmak and Gyeongju Oedong when Yongin closes (2027-12), then Gimhae, Chilgok, Nonsan and Naju as Busan, Daegu, Daejeon and Gwangju close (2028-03 to 2029-03); Namwon, Andong and Gangneung close without replacement in 2029.
Redraw territories at once: that step needs no lease and carries 10.0 of the 12.2 bn the sequence saves over 36 months (Section 5, extensions).
Each step is reconsidered with the real data at hand; the first lease the plan gives up is Hanam Gamil in June 2027.

**The decision requested from management now.**
Approve the three data requests above, to be delivered by the end of February 2027; confirm one business rule, whether far routes may carry a second driver or, failing that, whether a small coastal DC may stay below 500 stores (one of the two is needed for any redesign to pay; register, Section 3); renew the Gimpo Gochon lease that expires in March 2027 (it is in the best network for every number of DCs from 9 to 12, so renewing it is right whichever of them the real data settle on); and defer the Hanam Gamil renewal (June 2027), the first site the recommendation gives up, until the real-data check is done in April 2027.
No new site is leased before that check.

## 7. LLM Review & Key Revisions

**Tools and roles.**

| Tool | Version | Role | What it was not trusted with |
|---|---|---|---|
| Claude Code, a coding agent | Claude Opus 5.5 (Anthropic) | Reading the brief, template, classification reference and course script; arithmetic checks; writing every module of `code/`, the demo and the proposal; diagnosing run anomalies; arguing against the formulation; playing a panel of stakeholders; grading drafts against the rubric; drafting this document | Choosing scope and assumptions; typing any number (only `code/` produces them); accepting its own claims without a check |
| Tools the agent ran | Playwright 1.61 with Chromium 149; PyVRP 0.11.3; cProfile; ruff | Offline browser checks of the demo and the slides; the router accuracy check; profiling; lint | |

**What the LLM was used for, and how each use was checked.**

| Use | What the LLM did | How it was checked |
|---|---|---|
| Reading the task | Mapped every requirement of the brief to a course tool and later audited the demo and the proposal item by item against the brief | Against the source text; gaps were added to the demo (Section 5) |
| Course-method audit | Checked every method in `code/` against the algorithm atlas of the course script (Lectures 0-6) | Four methods were outside the course: savings with 2-opt as the router, a set-partitioning MILP as the exact check, Spearman correlation for G against E, and a literature constant in `G1`; each was replaced by a course method and every number re-run (discussion 1, run 7) |
| Arithmetic before code | Noon reach of a route, the thinning distortion, the bounds on k, the own-or-hire quantile | Recomputed in Python; values in Sections 2 and 3 |
| Road distances | Set up OSRM on a DGX Spark, built the cache through an SSH tunnel, read the extract date from the file header | 0 unroutable pairs; calibration error by distance band (Section 3) |
| The pipeline | Wrote the generator, demand model, router, assignment LP, fleet rule, E, `G0`/`G1`/`G2`, the pool, the GP with EI and the extensions | `verify.py` (29 checks), route audits, cost identities, reproduction on two machines |
| Run anomalies | Traced a non-monotone sweep, one-truck-per-far-store routes, a baseline at the search's own optimum and processor-dependent pools to their causes | Each cause confirmed by a targeted re-run before the fix (run history below) |
| Stakeholder role-play | Played 17 written personas (the examiner, a TA who reproduces the code, the CEO and CFO, the four voices of the meeting, real estate, a store owner, project and product managers, a lead developer, an OR scientist, a statistician, a UX designer and a red team) in three review rounds: the plan, the first build (six independent agents) and Spark run 2 (seven independent agents reading the brief's text) | A finding counted only once traced to a file and line or a registry number. Six agents found independently that a relay charge made 72% of the first saving (803 against 418 M, checked in the registry), which led to the relay route class; the plan review listed 27 gaps, each closed or answered (`planning/stakeholders/`, not in the hand-in) |
| Grading against the rubric | Wrote a grading prompt from the brief alone and calibrated it on Assignment 1 until three blind graders matched its real grade (mean 92.8 + 5.7 bonus against 94.5 + 6) and two deliberately broken copies lost what the rubric implies (72 with a broken demo, 88 without documentation); then {{GRADER_ROUNDS}} rounds of three fresh, blind graders on the hand-in ZIP | Every grader finding was checked against the files before anything changed; their findings drove the per-type demand reasoning, the design-year sweep, the candidate generator, the PyVRP rows and a faster reduced run; scores in the run history below |
| Arguing against the formulation [A §5] | Was asked to argue against the formulation and the evidence, at the plan, after the first version and after run 2 | Each objection traced to a section and either fixed (departure waves as a balance check, service to the east coast, stop density under thinning) or answered |
| Router accuracy | Exact enumeration on small territories; PyVRP on every territory | Section 2a; discussion 1 |
| Speed | Profiled the runs; made the router and the assignment faster without changing any result | Routes identical bit for bit; `verify.py` |
| Demo and proposal | Built both from the results registry, every precomputed number tagged with the command that produces it | Offline browser checks at ten widths; every slide; frame rate of the animation |
| This document | Drafted from the registry and the decision log | Every sentence with a number re-read against `registry.json` |

**Three discussions that changed the result.**
Each was checked by a calculation or an experiment, not by the model's word.

| Discussion / purpose | LLM suggestion | My assessment and verification evidence | Final decision or revision; location |
|---|---|---|---|
| 1. Which router, and is it good enough to rank networks? | Clarke-Wright savings with 2-opt, "close to optimal for depots of this size"; later, PyVRP inside E | Savings and 2-opt aren't in the course, so I asked for a router built from what we covered. Before switching we tested it: on 44 territory-days of both networks the new router (Lecture 0's construct-then-improve, hand-written rules) needs 2.0% more vehicles than savings and costs 2.7% more a day, about the same on both networks (2.5% and 2.8%), so it shouldn't tilt the comparison. An LP that joins routes in rounds (Lecture 1) was tried too and needed 15% more vehicles. Then PyVRP on every territory: our router is 7.2% dearer on the baseline and 6.6% on the recommendation, so the saving would be about 442 M instead of 469 M, and ten stays the best number. Savings had been closer to PyVRP but more lopsided (6.6% against 2.9%), which had inflated the saving by about 155 M. PyVRP inside E stays out: hundreds of times slower and random | The course-based router inside E, PyVRP only as a check; the saving with PyVRP's routes is reported next to the headline (Section 2a, balance table, reversal table; `code/checks/routing_gap.py`, `routing_summary.py`) |
| 2. The baseline: why did every redesign lose to the baseline network? | First version: "today's network is simply good; recommend keeping it" (run 3: best redesign 100 M a month worse) | Didn't buy it: a chain that grew for decades shouldn't sit on the optimum. Checks on the same E: under identical rules baseline sites and the best redesign were within 0.2%, and the 12 baseline sites had been placed by a p-median on today's own stores and road km, the search's own objective. That's a near-optimum, not "a chain that grew over decades" [A §2.5] | Rebuilt the baseline network as the 2016 planner's design with growth since (Section 3), a rule fixed and recorded before any redesign was scored against it, though adopted after the earlier baseline had won; the old optimum kept as a reversal row and the design year swept (Section 5) |
| 3. A better cheap criterion G | Learn a territory cost from routed territories and choose the network by a MILP on it (after published learned-cost location-routing work) | Fitted by bounded least squares on 421 routed territories, it predicted held-out networks far better than `G1`, yet its own pick and its MILP optima lost 254-1,035 M a month under E: no vehicle-per-territory term, and the MILP left the region it was trained on. Better prediction, worse decisions, as Lecture 5 warns | Rejected as the decider; built `G2` instead, the clock-aware criterion the brief names as system knowledge, and used it in the search (Section 4, the remedy) |

Other suggestions accepted after checking: the fleet quantile computed from the brief's own prices (verified: 1 − 5.5 M / (30.42 × 0.55 M) = 0.671); the transportation LP's integrality (verified on every evaluation: the largest fractional part is reported as `lp_frac` in the registry).
Rejected: thinning to 2,000 stores to save time (it changes stop density, the mechanism that sets k; Section 4 measures how much).

**Where the LLM was wrong, and what caught it.**

| Claim or output | Caught by | Correction |
|---|---|---|
| Savings with 2-opt as the router, a MILP as the exact check, Spearman for G against E, a literature constant in `G1`: all outside the course | My check of every method against the course script | Replaced by course methods and re-run (discussion 1, run 7) |
| "Savings is close to optimal", later "its error is similar on both networks, so it cannot move the ranking" | PyVRP on every territory of run 5's networks | Not similar: 6.6% of operating cost on the baseline, 2.9% on the recommendation; the router is now checked per network on every run |
| "Today's network is simply good; keep it" (run 3) | Checks of the baseline under identical rules | The baseline was the search's own optimum; rebuilt (discussion 2) |
| A learned territory cost as the decider | Its own picks priced under E lost 254-1,035 M a month | Rejected; `G2` built instead (discussion 3) |
| Run 2: "today's network misses the noon deadline for geographic reasons" | Arithmetic: only 227 of 9,718 stores lie beyond one driver-day, so geography could not explain missing the 98% (1 − 227 / 9,718 = 97.7% within reach) | It was a late label on relay deliveries; relabelled, then the relay class was modelled properly |
| The stock-out penalty was written to `cost_parameters` but never charged in E | Re-reading E against the brief's cost list | Charged (500,000 KRW per store without a delivery) |
| `G2`'s remaining bias "nearly constant" | Recomputed on the reported run | Not constant; the text now says it grows for poor candidates (Section 4) |
| "A one-week-old store sits close to its type's mean" | The fitted prior strength is about two store-days | Rewritten: after a week about 80% of the weight is on the store's own data (Section 3) |
| The myopic lease policy's end state at 9,308 M a month | Priced with the store minimum while the transition months were not | Priced like for like (Section 5) |
| "The saving is entirely today's drift since 2016" | The design-year sweep | Rewritten: the saving rests on how the baseline network was planned as much as on when (Section 5) |
| Page slips: tabs named that do not exist, unrendered template text, clipped labels, horizontal scrolling | Re-reading and browser screenshots at several widths | Fixed; the browser checks are now part of every rebuild |

**My calls.**
The LLM proposed and built; these were my decisions, and several reversed what it had done.

| Decision or correction | Why | Effect |
|---|---|---|
| All stores, thinning only as a check | Thinning changes stop density, and that sets k | The reported run uses all stores (Section 4, instance size) |
| The live solve has to follow the code's rules | Brief §6.3 | `app.py` on the Python engine; the page's engine states its simplification and is checked equal (`verify.py`) |
| No outside engine inside E | We should use the course's tools | PyVRP stays a check |
| Far stores get a second driver, flagged as an assumption | Otherwise they get no daily delivery | Relay route class; register row (Section 3) |
| "Today's network is simply good" didn't convince me | A chain that grew for decades shouldn't be optimal | Baseline rebuilt (discussion 2) |
| Brief values first; every deviation goes in a register, here and in the proposal | The brief is the client's spec | Register in Section 3 and proposal slide 10 |
| Relay driver at a full vehicle-day, but called an upper bound | Only a driver is added; truck and fuel are already counted | The saving is conservative on this point |
| Everything the brief asks for has to be visible in the demo | The demo is what the analyst reads | Proof section, per-DC table, balance table, log, data story, question index (Section 5) |
| Say clearly what the model leaves out | Be upfront about the edges | Must/should/could/won't scope: proposal slide 6, `code/README.md` |
| No laggy effects; proposal in project-management form | Management is the audience | 60 frames per second; proposal regenerated |
| Only methods from the lectures | Clarke-Wright and the rest weren't in my slides | Router, exact check, G-versus-E statistic and `G1`'s constant replaced; run 7 |
| Heavy runs on the DGX Spark, started by me | The laptop resets under sustained load | Every reported number comes from a run I started |

**Key revisions: how the answer changed, run by run.**

| Run | Result | What it exposed, and what changed |
|---|---|---|
| v0.1-v0.2 (laptop) | First end-to-end pipeline on placeholder distances | Replaced by OSRM road distances and population-based stores |
| Run 1 | Saving 1,776 M, k = 13 | A non-monotone sweep (the 500-store minimum forced 515 km routes) and `G1` near random: `G1`, the pool and the dock count fixed |
| Run 2 | Saving 1,776 M, k = 13 | Most of the saving came from one-truck-per-far-store routes counted late: the relay route class added, the baseline rebuilt |
| Run 3 | Saving −100 M: every redesign lost | The baseline was the optimum of the search's own objective (discussion 2) |
| Algorithm review | Router about 4% above PyVRP on both networks; GP with EI sound; `G1` lacks the clock | `G2` built (discussion 3) |
| Run 4 | Saving 590 M, k = 10 | The Spark and the laptop produced different pools: every sort made stable |
| Run 5 | Saving 592 M, k = 10; extensions added | Identical on both machines; graders 92, 94, 92 |
| Run 6 | Saving 592 M, k = 10 | Stock-out penalty charged; strict-brief rows; PyVRP on every territory (about 437 M with its routes); design-year sweep and candidate generation added; graders 99.5, 96.5, 97, then 99.5, 99, 99 |
| Run 7, reported | Saving 469 M, k = 10, the same ten sites | Course methods only: the new router, exact enumeration, R² for G against E, `G1`'s constant fitted; {{RUN7_GRADERS}} |

**Guardrails.**
No number enters a deliverable unless `code/` produces it; the LLM never types results.
Instructor-only material was never used as a source.
Data sources and software versions are named where they are used (Sections 3 and 5).
