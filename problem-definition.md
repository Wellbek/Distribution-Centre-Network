# Problem Definition: How Many Distribution Centres for Dasol Retail, and Where

**IE437 Midterm Project · Distribution-Centre Network Redesign - Formulating and Solving a Hierarchical Decision**

Author / student ID: Louis Wellmeyer / 20264059  
Date / version: 2026-10-27 / v1.0 (code run 6, `run_full.py` of 2026-10-27T11:24:50)  
Summary: Run ten DCs instead of twelve (keep Gimpo Gochon and Cheonan Seobuk, open eight new sites); in the fictional instance this saves 592 M KRW a month (90% interval over demand days 584-601; about 400-600 M across the model checks, 437 M with routes from a stronger solver) with every delivery before noon, and the saving rests on how far today's real network has drifted from a good design, which the real outcome tables must measure first  
Files: `problem-definition.md`, `code/` (README, three commands), `demo.html` (offline; the live solve also runs from `code/app.py`), `proposal.html`  
LLM tools and use: Claude (Anthropic) in Claude Code, 19 Oct to 2 Nov 2026, for problem discussion, OSRM setup, code, checks, the demo and slides; every number in this file comes from `code/` (Section 5) and three discussions are reviewed in Section 7.

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
| Data Team: "centre of gravity is optimal, minutes" | A **method** for `D1-network` (a generation criterion, our `G0`) with an optimality claim that holds only for its own criterion | `G0` | A method is judged by the value of what it proposes under E, not by its own score. The weighted centre of gravity minimises weighted *squared straight-line* distance; it is not the minimiser of distance (the Weber point), of road distance or of cost, and it does not choose k. Compared in Section 4 as one of the approaches |
| Field Manager: "across the river, trucks drive to the bridge" | A **claim about model validity** (straight-line distance is not road distance) | The distance model inside every criterion | Checked, not ranked: every distance is a road value or calibrated against one (Section 3), and the road-to-straight-line ratio enters the surrogate's features (Section 4). The one-site location problem is convex in straight-line distance and loses convexity under road distance, which is where the Data Team's shortcut stops being exact |

**Boundary.**
One redesign chosen now for a steady-state planning year in which every current site can be kept or given up and every candidate site can be leased [A §2.2].
In scope: the 9,718 stores open at the end of the history year, ambient and chilled deliveries in one wave, 60 candidate sites including today's 12.
Out of scope, with consequence: the fresh-food second wave (its routes and docks are not costed); Jeju and ferry-only islands (their stores keep today's supply); one-off moving, lease-exit and opening costs (Section 6 treats them as a payback question); the order in which leases expire (the sequence of closures is an extension: Section 5 computes it, Section 6 turns it into the plan).
**Company practice versus our baseline.**
The company's practice is experience-based routing on territories fixed long ago [A §2.1]; it is not available to us.
Our baseline is today's 12 DCs with their historical territories, routed by our own lower level under exactly the same evaluation as every candidate (Section 5); how the 12 were placed is described in Section 3.

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
This price is an upper bound: the truck and its fuel are already counted, and the brief prices a driver only together with a vehicle; since today's network runs fewer relay routes than the redesign, the true saving is, on this point, at least the one reported.
The brief itself has no relay route; the register in Section 3 lists this and every other deviation, and the strict reading (far stores become stock-outs at 500,000 KRW) is a reversal row in Section 5.
Only a store beyond even the relay limits counts as missed.

**Modelled:** load, stops, km, the noon deadline, the shift and break, road distances, stop time, relay drivers for far stores, a departure-wave check under a dock limit (Section 4).
**Omitted, with reason:** multiple trips per vehicle (a second trip cannot meet noon); time-of-day traffic (checked with 30 km/h in Section 4); returns and empty cages (no capacity effect `[ASSUMPTION]`); variable unloading times.

**Method.** Clarke-Wright parallel savings (all pairs up to 400 stores, the 40 nearest neighbours above), merging two routes only if load, stops, km, deadline and shift all hold; 2-opt inside each route; then the relay pass for stores left unserved (`code/dcn/routing.py`).
It is deterministic, so every candidate sees exactly the same procedure.
**Cost of one solve:** about 0.15-0.3 s per territory-day on one core at full scale (1,400 stores) (run 6: 91 territory-days per evaluation in 1.27 s on 16 processes, 0.22 core-seconds each).
**Accuracy**, measured three ways:

| Check | Instance | Result | Source |
|---|---|---|---|
| Exact set partitioning (HiGHS) | 25 random 7-store instances | 0.00 extra vehicles on average (never more), kilometres 0.4% above the optimum on average (3.7% at most) | `code/verify.py` |
| Load lower bound $\lceil \sum q_i / 48 \rceil$ | Every territory of the showcase day | 37-45% above the bound max(load / 48, stores / 25), because the binding limit is the clock, which the bound ignores; the bound is too weak to measure accuracy here, so PyVRP is the real comparison | `code/verify.py` |
| PyVRP 0.11.3 (hybrid genetic search), same matrix, limits and relay structure | Full territories, one search day, today's network and the k = 10 alternative | Today's network: 654 vehicles by savings against 608 by PyVRP (11 of 12 territories; on Yongin PyVRP left stores unrouted even at 0.5 s per store, so savings is used there); per territory savings costs 0.1% less to 35.5% more than PyVRP, worst on small rural territories (Andong 33 against 24 vehicles, Gangneung 17 against 14, Daejeon 51 against 43). Recommended network: 620 against 599, all ten territories feasible, 0.3% less to 7.0% more | `code/checks/routing_gap.py` (optional dependency; cached result) |

**What its error does to the upper level:** the heuristic over-states operating cost by 6.6% on today's network and 2.9% on the recommended one, because it is weakest where stores are sparse and far from their DC, and today's network has more such territories.
The error therefore does not shift every candidate alike: it favours networks without small rural DCs.
With PyVRP's routes on the same day, the day's operating saving falls from 6.3 M to 1.2 M KRW, so the monthly saving would be about 156 M lower, about 437 M instead of 592 M; it stays positive, and most of what remains is rent (two DCs fewer).
The redraw step alone (today's sites, territories redrawn) is worth 12.4 M a day with savings routes and 8.9 M with PyVRP's, about 270 M a month instead of 375 M.
Two cheap repairs (dissolving the smallest routes into others, and a sweep construction) gained at most one vehicle on the worst territories, so the measured gap is reported instead (Section 5, reversals; `checks/routing_summary.py`).
Does the bias move k?
The best 9-, 10- and 11-DC networks routed by PyVRP on the same day cost 189.0, 187.3 and 187.0 M a day including rent (savings: 192.8, 191.4 and 192.0 M): with better routes eleven edges ten by about 9 M a month, the same near-tie the value of information finds, and nine stays worse; the lease plan is the same for all three (Section 5, value of information).

**What one solve returns upward:** vehicles used, km, relay routes, late and missed deliveries, the binding limit of every route (load, stops, km or clock) and the service level.

### 2b · The connection

**Down:** the open sites (from `D1`), the assignment produced by the rule below (`D2`), the fleet-policy quantile (`D3`) and the sampled demand days.
**Up:** monthly operating cost, owned fleet per DC, service level, relay and dock counts.

$$E(x) \;=\; \sum_{j\in x} f_j \;+\; c_m \sum_{j\in x} n_j(x) \;+\; \frac{365}{12}\,\sum_{t=1}^{N} w_t\, Q\big(x, n(x);\, \xi_t\big)$$

$f_j$ is the site's monthly fixed cost, $c_m$ = 5.5 M KRW per owned vehicle, $n_j(x)$ the owned fleet, $Q$ the day's fuel, spot, relay and penalty cost from the lower level, $\xi_t$ demand day t drawn from the posterior predictive (Section 3) and $w_t$ its calendar weight (sample average approximation).
**Fleet policy.** $n_j$ is the $1 - c_m/(30.42\,c_s) = 0.671$ quantile of DC j's daily vehicle need over the sampled days: the newsvendor critical fractile of owning a vehicle (5.5 M a month) against hiring one (550,000 a day), which is where the brief's two-thirds default comes from.
**Demand uncertainty enters here:** E routes N sampled days, not one average day, because the fleet quantile and the spot hires are not linear in demand (Section 3 measures the difference).
**Common random numbers:** every candidate and the baseline see the same store-level demand days, so differences between networks are paired.
**Cost of one evaluation:** k × N lower-level solves: about 70 territory-days for k = 10 and N = 7, 1.3 s with 16 worker processes, about 20 core-seconds (run 6, `meta.timing`).

**Where the assignment lives: re-solved inside E.**
The candidate is only the set of open sites; E assigns stores by a capacitated transportation LP

$$\min_{z\ge 0}\;\sum_{i,j} w_i\,\tilde d_{ij}\,z_{ij}\quad\text{s.t.}\quad \sum_j z_{ij}=1\;\;\forall i,\qquad 500 \le \sum_i z_{ij} \le 1{,}400\;\;\forall j\in x,$$

with $\tilde d_{ij}$ the road distance plus a penalty beyond the 55 km noon reach of a full route and a prohibitive cost beyond the 125 km one-driver reach.
The constraint matrix is totally unimodular, so the LP optimum is integral (every store goes to one DC), and its duals price each binding store bound.
Why inside E rather than part of the candidate: the search space shrinks from site sets times assignments to site sets, a good assignment for given sites is a convex problem we can solve exactly, and E then judges "these sites, operated by this assignment rule"; a better rule could only lower E.
The baseline keeps its historical assignment, a fact of the operation exempt from the bounds [A §2.3]; "today's sites, re-assigned" is reported as a separate step (Section 5).

`D1-network evaluated_by D4-routing` through E, separately from the dependencies of Section 1.

### 2c · The upper level

$$\min_{y\in\{0,1\}^{60}}\; E(y) \quad\text{s.t.}\quad \sum_j y_j = k,\;\; k\in\{\lceil 9{,}718/1{,}400\rceil,\dots,\lfloor 9{,}718/500\rfloor\} = \{7,\dots,19\},\;\; \text{the assignment LP is feasible}$$

$y_j = 1$ opens candidate site j; the fleet follows from the policy and the assignment from the LP, so neither is a free upper-level variable.
**Convex or linear:** the assignment for fixed sites (the LP above); the one-site location problem under straight-line distance (Weber point); the LP relaxation of the capacitated facility-location problem.
**Combinatorial:** the site subset (about $7.5\times 10^{10}$ sets for k = 10 among 60), and E itself is a black box built from heuristic routing, non-convex and noisy in the days drawn.
**Implication:** E cannot be optimised exactly; it is searched under a budget of full evaluations with a cheap criterion proposing candidates (Section 4).
A k below 7 is infeasible (six DCs at the cap hold at most 8,400 stores), which is the demo's failure case.

**I/O schema.**

| Input / output | Table or parameter | Field | Type / unit | Meaning; one row is … |
|---|---|---|---|---|
| Input | `stores` | `store_id`, `region`, `lat`, `lon`, `store_type`, `opened_on`, `closed_on`, `current_dc_id` | text; degrees; category; date; text | one store (10,000 generated, 9,718 open at the horizon) |
| Input | `demand_history` | `store_id`, `date`, `cages_ordered` | integer, roll cages | one store's order on one day (365 days) |
| Input | `dcs` | `dc_id`, `lat`, `lon`, `lease_expires_on`, `monthly_fixed_cost`, `max_stores`, `min_stores` | KRW / month | one current DC (12) |
| Input | `candidate_sites` | `site_id`, `lat`, `lon`, `monthly_fixed_cost`, `max_stores` | KRW / month | one leasable site (60, today's 12 included) |
| Input | `cost_parameters` | `parameter`, `value`, `unit` | mixed | one finance figure (teaching defaults [A §2.6] plus the relay-driver assumption) |
| Input | road distance cache | store-to-site km, store-to-50-nearest-store km, calibration coefficients | km | `code/data/road_cache.npz` (Section 3) |
| Input | outcome tables `deliveries`, `vehicle_days`, `spot_hires` | as in [A §2.5] | | produced by our lower level on today's network over the history year; used for the baseline's service level and fleet check, not as inputs to E |
| Output | recommended network | open sites, k, stores per DC, owned fleet per DC | | the decision |
| Output | cost breakdown | fixed, owned fleet, fuel, spot, relay, penalties; saving against the baseline with its 90% interval on final and held-out days | M KRW / month | the evidence |
| Output | evaluation log | step, candidate, sites, k, G1, G2, E, service level, rule that chose it | | one full evaluation (Section 5) |
| Output | registry | every number shown in the three deliverables | JSON | `code/results/full/registry.json` |

**The two criteria.**
**G (generation)** proposes candidates in milliseconds.
`G0` is the Data Team's method: weighted k-means on straight-line coordinates, snapped to distinct sites.
`G1` = fixed cost + a load-based fleet (routes = cages / (0.92 × 48)) + line-haul and continuous-approximation local km on road distances (Daganzo's $0.7124\sqrt{nA}$ for the stops inside a territory), with far stores priced as relay routes; it ignores the clock.
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
| `demand_history` | the cages one store **ordered** for delivery the next day | the load a DC must pick and carry: exactly what the lower level needs | shelf demand: a store holds about two days of stock [A §2.3], so a sell-out or a delayed delivery shifts orders between days, and lost sales leave no trace | We plan on orders, not on consumer demand, and say so; the day-to-day variance of orders may be smaller than that of sales (the back room smooths it), which makes the fleet quantile slightly optimistic, and a catch-up order after a late delivery counts as extra demand, so stores served late today look busier than they are and their fitted rates run high: a request below |
| `demand_history` | an order placed **under today's network** (today's delivery time at that store) | the order pattern of today's operation | how a store would order if its delivery moved from 06:00 to 11:30 under another DC; a late arrival may raise safety orders | Orders are treated as independent of the network `[ASSUMPTION]`; a redesign moves stores to later slots, so the real-data check of Section 6 includes the share of stores whose delivery moves later by more than 2 h |
| `deliveries`, `vehicle_days`, `spot_hires` | an **outcome of today's network**: today's assignment, routes and fleet on one day | today's service level, kilometres, vehicles and spot hires | what any other assignment or network would cost: the rows carry today's choices, so they cannot score a redesign or calibrate a cost per store that transfers to another territory | Used only to describe and check the baseline (Section 5); every candidate is costed by routing it, never by extrapolating these rows. The real tables will also record the company's experience-based routing, so comparing their cost with our routed redesign would credit the redesign with a routing-method gain as well: the check of Section 6 therefore re-routes today's real territories with our lower level and compares like with like, and uses the real tables separately to measure how far our router is from today's practice. Our own generated tables cannot validate our router (they are its output) |
| `stores` | one store, with the DC that serves it today | location, type, opening date | why it is assigned there; stores opened recently have a short history | Short histories borrow strength from the prior (below) |
| `demand_history`, summed over stores | the chain's daily total, a mix of store types | the chain's calendar | each store's own weekly shape: an office store orders 0.70 of its weekday level at weekends, a residential or roadside store about 1.12 [A §2.3]; a single chain multiplier (1.04) would put an office store's weekend orders about 70% too high and a residential store's 7% too low | Calendar multipliers are estimated over the whole chain but **per store type** (four types × weekday, month, holiday), the unit that carries the weekly shape; see below |

**The instantiated data** (all from `code/dcn/world.py` and `code/dcn/demand.py`, seed 437; tables in `code/results/full/tables/`).

| Table | How it is generated | Real-world property it reflects |
|---|---|---|
| `stores` | 10,000 points drawn in proportion to population on 71,015 Kontur Population hexagons (H3 resolution 8, 2023-11-01, CC BY 4.0), jittered inside the hexagon; Jeju, sea points and ferry-only islands removed; province and district from geoBoundaries ADM1/ADM2; type by location (office and mixed near big-city centres, roadside and residential in the countryside); 6% opened and 3% closed during the history year; 9,718 open at the horizon | Stores follow people: Gyeonggi 3,059, Seoul 1,732, Gangwon 242 stores |
| store opening year | Today's pre-history stores open along a growth curve (12% by 2000, 41% by 2010, 62% by 2016, 76% by 2020) with denser hexagons earlier `[ASSUMPTION: the shape of a Korean convenience chain's growth]` | A chain that grew from city centres outwards |
| `dcs` | The 12 sites a planner chose in 2016, see "Today's network" below; leases of ten years from move-ins 2016-2019, expiring quarterly from March 2027 to December 2029 `[ASSUMPTION]` | Leases expiring one after another [A §2.1] |
| `candidate_sites` | 60 hand-placed sites at motorway interchanges and logistics zones (`code/dcn/geo.py`), today's 12 among them; 180 M KRW a month in the capital region, 157.5 M in metro cities, 132 M elsewhere | Leasable logistics land, dearer near Seoul |
| `cost_parameters` | Teaching defaults [A §2.6] plus one assumption: a relay driver costs one owned vehicle-day | Finance's figures |
| `demand_history` | 365 days from 2025-10-01: store level (lognormal, mean 2.2 cages, clipped to 0.5-6) × weekday profile by store type × summer peak × Korean holidays and their eves × a chain-wide AR(1) shock (weather) × store-day gamma noise, Poisson counts | Weekends, summer, holidays, chain-wide moves, short histories |
| outcome tables | Our lower level on today's network over the 365 days, owned fleet = 0.671 quantile of that year's daily need | Labelled as produced by our own model [A §2.5] |

**Distances.**
Self-hosted OSRM v6.0.0, car profile, Geofabrik `south-korea-latest.osm.pbf` (OpenStreetMap data of 2026-10-18), ferries excluded.
Computed: every store-to-site pair (9,718 × 60) and each store's 50 nearest stores; cached in `code/data/road_cache.npz` (5 MB), so no network access is needed to reproduce anything.
Other store pairs use a model calibrated on 3,959 OSRM distances (straight-line km × a factor by distance band and a mountain class for Gangwon and North Gyeongsang; median error 20% for pairs of 1-10 km, 9% for 10-50 km and 4% for 50-250 km on a held-out half); 89-99% of the legs a route actually drives are OSRM values.
Travel time is road km / 35 km/h; engine durations are not used.
**Instance: not thinned.**
All 10,000 stores are kept, one stop per store, because thinning changes stop density and with it the clock mechanism that creates the trade-off in k [A §2.7]; the reduced run (1 store in 5, fixed cost and bounds scaled to 30 M and 100-280) is the thinning check of Section 4.

**Today's network, and why it is plausible.**
A chain that grew over decades does not sit on today's optimum [A §2.5].
We model the last network redesign as done in 2016 by the same planning rule we would use, with the tools and stores of the time: a capacitated p-median on straight-line km over the 6,178 stores open in 2016, every store within one driver-day (125 road km, 96 straight-line km), at most 1,400 stores per DC, no minimum, solved by greedy add and exchange search (`code/prep/current_network.py`).
Stores opened since joined the nearest DC with room, in order of opening, and nothing was rebalanced.
The rule was fixed and recorded (decision D-069) before any redesign was scored against it, but it was adopted after an earlier baseline (a p-median on today's stores and road km) had beaten every redesign, so it is not blind to that result; the earlier baseline is kept as the reversal row that tests exactly this choice (Section 5), and the year of the last redesign is swept in Section 5 (the saving stays positive for every year from 2010 to 2026).
Plausibility evidence: every site is a candidate logistics site; the demand-weighted road distance from store to DC is 32.8 km against 31.8 km for the p-median optimum on today's stores and road km; the capital-region DCs carry 1,170-1,366 stores and the regional ones 116-789, as a grown network would.
What the decade of growth did: 38.3% of today's stores opened after 2016 and sit on average 45.6 road km from their DC, against 25.0 km for the stores the network was designed for; the capital-region DCs filled to 1,170-1,366 stores while Gangneung kept 116.
Redrawing today's own territories by the assignment LP moves 1,098 stores and saves 375 M KRW a month (Section 5), and the same number of DCs placed for today's stores would cost 652 M a month less than today's network on the search days (5,767 against 6,419 M).
The opposite case, a network already optimal for today's stores, is reported as a reversal (Section 5).

**The demand model** (Lecture 2, `code/dcn/demand.py`).

$$y_{s,t}\mid\lambda_s \sim \mathrm{Poisson}(\lambda_s\, e_{s,t}\, \gamma_t),\qquad \lambda_s \sim \mathrm{Gamma}(a_{\tau(s)},\, b_{\tau(s)}),\qquad \lambda_s \mid \mathcal D \sim \mathrm{Gamma}\Big(a + \sum_t y_{s,t},\; b + \sum_t e_{s,t}\gamma_t\Big)$$

The exposure $e_{s,t}$ is the calendar multiplier of the store's type (weekday × month × holiday), estimated once over the whole chain for each of the four types; $\gamma_t$ is the chain-wide shock of day t, estimated from chain totals and divided out.
**Why per type, not one multiplier for the chain.** "Once for the chain" can be read as one weekday profile for all stores, but a row of `demand_history` means something different at an office store (weekend orders 0.70 of weekday) than at a residential one (1.12).
One profile would be wrong for every store in the same direction by type, and the error lands on DCs in proportion to their mix: up to 2.7% of a territory's weekend need for today's DCs (Andong, Gangneung) and up to 1.6% for the redesign (Wonju).
The owned fleet is the 0.671 quantile of each territory's daily vehicle need, so an error of that size moves the DC's owned fleet or its spot hires by about the same share; and because the error follows the type mix, it changes when stores are reassigned, so it would differ between the networks being compared and bias the comparison instead of cancelling.
Store type is a safe unit because it is a fixed attribute of the `stores` table, independent of the network, with hundreds to thousands of stores per type, so its profile is estimated precisely and travels with the store to whichever DC serves it.
The prior mean per store type comes from the chain; its strength $b$ is fitted by empirical Bayes: 1.8-2.2 (residential 2.09, office 2.17, mixed 1.92, roadside 1.84) store-days.
The prior is worth about two days of a store's own orders, so after one week a new store's posterior already puts about 80% of its weight on its own data, and a store opened yesterday moves about a third of the way from its type's mean towards its first order; store ST00211 opened 61 days before the horizon and ordered 135 cages against 63.2 store-days of exposure; its prior Gamma(4.55, 1.92) (mean 2.37, mixed stores) becomes Gamma(139.6, 65.1), posterior mean 2.14 against its own data mean 2.14 (its true rate, hidden from the model, is 1.89).
Extra store-day variation beyond Poisson is gamma with shape κ = 8.1; the chain shock is AR(1) with φ = 0.46 and σ = 0.061.
**Posterior predictive for a planning day:** draw a calendar day of the planning year, the chain shock from its AR(1), each $\lambda_s$ from its posterior, then the counts.
A posterior predictive check replicates the history's chain totals (shown in the demo, Data & baseline tab).

**Sampled days versus one average day.**
On the recommended network and the 7 search days, sampled days give E = 5,827.6 M a month; the same days with each store's expected count instead of its sampled count give 5,809.9 M (18 M less: store-level noise largely cancels at the DC); one average day gives 5,758.3 M (69 M less, 1.2%).
The rest of the gap comes from chain-wide variation: weekday, weekend and holiday levels and the AR(1) chain shock move every store of a DC together, and the owned fleet is the 0.671 quantile over days, which an average day cannot see.
The peak day (2027-09-13) needs 752 vehicles against 627 owned.
The gap would grow with a stronger chain-wide shock (φ or σ) or a sharper holiday peak, which is why the fleet is sized on sampled days.

**Facts, assumptions, unknowns and requests.**

| Fact / assumption / unknown or request | Evidence or reason for current treatment | Why it matters | How to confirm or obtain it; priority | Fallback or limit until confirmed |
|---|---|---|---|---|
| Request: the real `deliveries`, `vehicle_days` and `spot_hires` for 12 months | Not handed over [A §2.5] | They measure today's network, and the saving is the distance between today and the redesign (Section 5, reversals) | Logistics IT export; **highest** | The saving is a property of the fictional network; nothing is promised in KRW |
| Request: store sales (POS) next to orders | Orders are not shelf demand (table above) | Fleet sizing on smoothed orders may under-own vehicles | Merchandising data; **high** | Peak-day fleet and spot hires reported (Section 4, fleet row) |
| Request: real DC rents, dock counts and lease terms per site | Rents by region class are `[ASSUMPTION]` | The reversal in DC fixed cost (Section 5) | Real-estate team; **high** | Sweep 100-200 M |
| `[ASSUMPTION]` relay (two-driver) routes for stores beyond one driver-day, one extra driver-day each | Business decision B-01 | Prices far stores in both today's network and every redesign | Operations; **medium** | Relay price swept: free, one driver-day, the spot rate (Section 5) |
| `[ASSUMPTION]` orders do not depend on the delivery time slot | No data on ordering behaviour by slot | A redesign that delivers later could change orders | Real-data check (Section 6); **medium** | Report the share of stores whose delivery moves later by more than 2 h |
| `[ASSUMPTION]` 15 min per stop, 35 km/h | Teaching defaults [A §2.6] | They set the noon reach, which drives the k trade-off | GPS traces of one DC for a month; **medium** | Reversals at 10/20 min and 30/45 km/h, and their value of information (Section 5) |
| `TBD`: the after-14:00 penalty for stock-outs at 24-hour stores | Teaching default used | Only matters if a network misses deliveries; none of the compared networks does | Store operations | Default |
| Fact: road distances | OSRM on OpenStreetMap, cached | The Field Manager's point | Re-run with a newer extract | Calibrated model for pairs outside the cache |

**Register: where we deviate from the brief or assume what it does not give** (to be confirmed with the business; the brief's own values are used everywhere else).

| Item | Brief | We use | Why, in one line | Effect or check |
|---|---|---|---|---|
| Stores beyond one driver-day | About 250 km and a 10-hour shift per vehicle [A §2.3] | A relay route with a second driver: up to 500 km, on duty until 19:00, every stop still by noon `[ASSUMPTION; B-01]` | Without it, stores on the far east coast and in the mountains could not get their daily delivery from any DC the 500-1,400 bounds allow | Strict brief instead (no relay, those stores are stock-outs at 500,000 KRW): today's network then has 3 stock-outs a day and the best network checked (k = 11) costs 511 M a month **more** than today, so the redesign reverses; with the minimum also dropped: a network that keeps a small coastal DC is allowed, and the best one (k = 12) saves 625 M a month |
| Price of the second driver | No price (the 5.5 M a month covers a vehicle with its driver) | 180,822 KRW per relay route-day, a full owned vehicle-day `[ASSUMPTION]` | The brief prices drivers only together with a vehicle; this is an **upper bound**, because the truck and its fuel are already counted and only a driver is added | Today's network runs fewer relay routes than the redesign, so a lower price raises the saving: free 636 M, our price 592 M, at the spot rate 503 M (k = 11) |
| Shift timing | A 10-hour shift including loading | Loading 03:00-04:00, departure 04:00, return plus a 30-minute break by 13:00 `[ASSUMPTION]` | The brief does not time the shift, and a driver needs a break | Departure-wave check (next row) |
| Departure time | Vehicles leave between 04:00 and 07:00 | All leave at 04:00 inside E `[ASSUMPTION]` | The earliest start gives the most reach before noon and needs no dock schedule | Waves 04:00-07:00 with 23 or 29 docks per DC: best k unchanged (Section 4) |
| Docks per DC | Not given | 23 (store cap × today's vehicles per store ÷ 4 waves) `[ASSUMPTION]` | Needed only for the wave check | 25% more docks: best k unchanged |
| Delivery window | At least 98% before 12:00; failure after 14:00 | Every stop by 12:00 when routes are built | Simpler and conservative; the 2% slack is not used | All compared networks at 100% before noon |
| DC rent | 150 M a month per DC; higher in the capital region [A §2.5] | 180 M capital region, 157.5 M metro, 132 M elsewhere (150 M × 1.20 / 1.05 / 0.88) `[ASSUMPTION]` | The brief asks for dearer capital-region sites without a figure | Rent reversal at 100 M and 200 M |
| Spot trucks | 550,000 KRW a day; supply not stated | Unlimited at that rate `[ASSUMPTION]` | No limit is given | Peak day: 125 spot trucks above 627 owned |
| Fleet quantile | Two-thirds | 0.671, the newsvendor fractile of the brief's own prices | The same rule, computed exactly | None needed |
| Orders and the network | Not addressed | Orders do not change when a store's delivery time changes `[ASSUMPTION]` | No data on ordering by delivery slot | 24% of stores would be served more than 2 h later: first real-data check (Section 6) |
| Today's network | Placed plausibly, as a chain that grew [A §2.5] | The 2016 planner's design with growth since (Section 3) | The brief gives no real network; this rule was fixed before scoring | Today's network at the optimum instead: −61 M, the reversing row |
| Scope | Fresh food out of scope unless brought in; one-off costs not mentioned | Fresh food, Jeju and ferry-only islands, moving and opening costs left out | Allowed by the brief or not costable without data | Moving cost as a payback condition (Section 6) |
| Closure sequence | Leases expire one after another | First month a redesign can operate: January 2027; leases end on the fictional dates of `dcs` `[ASSUMPTION]` | Two months to fit out a site | Extensions (Section 5) |
| Value-of-information prior | Not given | 0.25 / 0.5 / 0.25 on low / reported / high stop time and speed `[ASSUMPTION]` | A neutral prior around the teaching defaults | EVPI reported as a lower bound |

**Main uncertainties and when not to trust the recommendation.**
The decision rests on how far today's real network is from the optimum (Section 5, last reversal row), on the stop time and speed that fix the noon reach, and on the rent level; demand noise moves the saving far less (Section 5 intervals).
Do not act on the recommendation before the real outcome tables have scored today's network under the same evaluation.

## 4. Alternatives & Selected Approach

**Approaches.**

| Approach | Mechanism and required information | Strengths, limitations, and effort | Selection and reason |
|---|---|---|---|
| Baseline | Keep today's 12 DCs and territories; renew leases as they expire | No transition cost or risk; carries a decade of drift (Section 3) | The reference every candidate is scored against, under the same E (Section 5) |
| Proxy-only: centre of gravity (`G0`) | The Data Team's method: weighted k-means on straight-line coordinates for a chosen k, snapped to sites | Minutes; no road distances, no clock, no choice of k; optimal only for its own criterion | Rejected as the decider; scored under E for comparison: its best network (k = 13) costs 6,348.5 M a month on the search days, 520.9 M more than the best network found; 5 of its 13 networks miss 98% before noon |
| Proxy-only: best network under the cheap criterion | Search the pool by `G1` and pick its minimum, without any full evaluation | Milliseconds per candidate; ignores the noon deadline, so it favours fewer, larger territories | Rejected; its pick loses 425.5 M a month on the final days (it picks eight DCs, 6,400.0 against 5,974.5 M) under E (Section 5) |
| Generator knobs with BO (brief option i) | k, a volume exponent, a detour penalty and a minimum spacing as four continuous inputs to the generator, GP + EI on them | The GP's home ground; still produces G-optimal networks, so it shares G's blind spot unless G knows the clock | Considered, not built: the pool option below covers the same budget and lets us use `G2` directly |
| **Selected: pool + discrepancy GP + EI under a budget** | A pool of candidates per k from `G2`, `G1`, `G0`, today's sites adjusted and random swaps; a Gaussian-process model of the gap E − `G2` over seven summary features; expected improvement picks the next full evaluation; B = 40 | Spends full evaluations where the cheap criterion is least trusted; needs the pool to contain good candidates (checked: the whole pool is also evaluated once for validation) | Chosen: it is the course's default (Lectures 4 and 5), it keeps G and E apart, and it beat random selection at the same budget (Section 5) |

**The solution-algorithm plan** (calculation flow, `code/dcn/pipeline.py`).

1. Build the world and fit the demand model (Section 3); draw 7 search days, 28 final days and 14 held-out days from the posterior predictive (seeds 448, 449, 450), the held-out days disjoint from the final ones.
2. Score the baseline: today's sites and historical territories through E on the search days.
3. **Pool.** For every k from 7 to 19: the `G2` optimum (greedy add from the k − 1 solution, then swaps with the 12 nearest sites), the `G1` optimum, the `G0` solution, today's sites adjusted to k (drop or add one site at a time by `G2`, the natural move as leases expire one by one), and random one- or two-site swaps of these four, 390 candidates in all, each with its LP assignment, `G1`, `G2` and seven features: k, mean, 95th-percentile and maximum road km to the DC, load imbalance, the demand share beyond the 55 km noon reach and the store share beyond 125 km.
4. **Reported search, one fresh run of B = 40 full evaluations.** First the `G2` seed of every k (13 evaluations, one per number of DCs, as the brief requires); then 27 picks, each the pool member with the largest expected improvement under a Kennedy-O'Hagan model E(x) = `G2`(x) + δ(x), δ a Gaussian process (Matérn 5/2, one length scale per feature, hyperparameters by marginal likelihood) refitted after every evaluation.
   The pool is enumerable, so the acquisition is maximised exactly.
   Every evaluation is logged with the rule that chose it.
5. **Random selection at the same budget** on the same pool from the same 13 seeds (one run is logged; Section 5 also gives the distribution over 2,000 random orders, computed from the validation pass).
6. **Hand-over:** the five best candidates of the reported search that keep 98% before noon are re-scored on the 28 final days; the best becomes the recommendation, and is then checked on the 14 held-out days with the fleet fixed from the final days.
7. **Validation only, after the reported search:** every pool member is evaluated once on the search days, to measure G against E over the whole pool and to know the pool's best.

Budget justification: with the company's real routing system one evaluation would take hours [A §3.3]; 40 is the brief's default and here costs about 40 s on the 16 worker processes of the Spark (1.3 s per evaluation).
Randomness: only the demand days (fixed seeds) and the random swaps and random selection (seed 437 + offsets); the routing, the LP and the GP are deterministic, so the run reproduces exactly.
What is computed, what is precomputed: everything in this file is computed by `run_full.py`; the demo shows those precomputed results and runs the lower level live (Section 5).
No optimality is claimed for the recommended network: it is the best of 40 evaluations in the reported search, checked against the whole pool (balance table, search row).

**The fidelity-computation balance.**
The first row is the choice the conclusion hangs on most.

| Modelling choice | What the real operation does | What we model | What it costs to compute | What the simplification could get wrong | How we checked whether it changes the decision |
|---|---|---|---|---|---|
| Today's network | A network grown and patched over decades, unknown to us in detail | The 2016 planner's design with growth since (Section 3) | Free | If the real network is closer to optimal, the saving shrinks | Re-scored with today's network placed at the optimum for today's stores: a 12-DC p-median on today's stores and road km costs 5,767 M a month on the search days, 61 M less than the best redesign: one of the two rows that reverse the recommendation; between the two, the year of the last redesign is swept from 2010 to 2026 (the saving stays between 302 and 675 M for every year; only the road-km design reverses it) (Section 5) |
| Distance model | Trucks drive roads; speed varies by hour | OSRM road km for every store-site pair and each store's 50 nearest stores, a calibrated model for other pairs; time = km / 35 km/h + 15 min per stop | One-off: 0.6 M site pairs and 0.5 M store pairs on the Spark, cached (5 MB) | Peak-hour slowdowns ignored, which flatters long routes; model pairs off by 20% for pairs of 1-10 km, 9% for 10-50 km and 4% for 50-250 km on a held-out half | Re-scored the best network of every k and the baseline with the calibrated model only and at 30 km/h: calibrated model only: k* = 9, saving 396 M; 30 km/h: k* = 11, saving 805 M; the saving keeps its sign and k moves by one |
| Instance size | 10,000 stores | All 10,000 (not thinned) | Full run 1,127 s on a DGX Spark with 16 worker processes: 966 s for the pipeline, 160 s for the extensions; reduced run (1 in 5) 7 min with two worker processes on a laptop | Nothing from thinning; slower development | Reduced run against full run, k by k: the reduced sweep's minimum is at k = 11 against 10 for the full instance (after re-scoring its top five on 28 days the reduced run recommends 12); cost per store 1.19-1.32 times the full run's at every k; km per store 1.48 times the full run's for today's network, below the √5 = 2.24 the continuous approximation predicts because the out-leg does not shrink with density; the reduced instance would have recommended one DC more |
| Demand model and days | Store orders with calendar, shocks, short histories | Poisson-Gamma with chain exposure and AR(1) shock; 7 search days, 28 final, 14 held-out | 28 days cost four times 7 | A 0.671 quantile from 7 days is noisy; rankings may change with more days | Top five re-scored on 28 days: the search's best stays first on 28 days (5,974.5 M); the next three (k = 9, 10, 11) lie within 22 M of it; sampled versus average day: one average day understates E by 69 M a month (1.2%) |
| Routing method | Experienced dispatchers | Savings + 2-opt + relay pass, deterministic | 0.22 core-seconds per territory-day | 6.6% of operating cost above PyVRP on today's network and 2.9% on the recommended one, worst on sparse rural territories; biased towards networks without small rural DCs | PyVRP on every territory of both networks, one search day (Section 2a): the saving falls from 592 to about 437 M a month and keeps its sign; the best 9-, 10- and 11-DC networks under PyVRP: eleven edges ten by about 9 M a month, nine stays worse, so the bias moves k at most within the 10-11 near-tie |
| Delivery window | ≥ 98% before 12:00, failure after 14:00 | Every stop by 12:00 (hard) | A check on every merge | Leaves the 2% tolerance unused, over-stating vehicles slightly | Every compared network reaches 100% before noon on every final day; the slack is a saving we do not claim |
| Departure and docks | Waves 04:00-07:00 limited by docks | Every vehicle leaves at 04:00 | None | Flatters large DCs, so it favours fewer DCs | Departure waves with 23 docks per DC: k* 10 → 10; with 25% more docks: 29 docks, k* 10 |
| Assignment | Historical territories | Window-aware transportation LP inside E (Section 2b) | One LP per evaluation | Distance-optimal is not route-optimal | The LP beats the historical assignment on today's own sites (Section 5, saving decomposition) |
| Fleet policy | Vehicle contracts, spot market | 0.671 quantile of daily need, unlimited spot trucks at 550,000 KRW | Free | Spot supply may be capped on peak days | Peak day reported: 2027-09-13, a holiday eve: 752 vehicles needed against 627 owned, 125 spot trucks (68.8 M that day), 100% before noon |
| Candidate set | Real-estate options | 60 sites at interchanges and logistics zones, today's 12 included | Pool size | The optimum may sit off the list, or among site sets the pool never held | Inside the list: a learned generator samples site sets the pool never held (Section 5, candidate generation); off the list: `TBD` with the real-estate team (Section 3, requests) |
| Number of DCs swept | Any k the bounds allow | k = 7 to 19, one `G2` seed each | 13 of the 40 evaluations | Wasted evaluations on hopeless k | All 13 reported in the sweep (Section 5) |
| Search and budget | Hours per real evaluation | Pool + discrepancy GP + EI, B = 40 | 40 evaluations | Misses the pool's best | The whole pool evaluated once for validation: all 390 candidates evaluated; the search found the pool's best at evaluation 16 |

**Where computation was spent and why.**
On the lower level and on full density, because the trade-off in k comes from the clock: a route that leaves at 04:00 must reach its last stop by noon, so the out-leg of a large territory eats the time for stops, and that mechanism only shows with real stop density and real road distances.
The upper level gets the cheapest adequate tool, a pool and a surrogate, because the location effect within a given k is small next to the count effect (Section 5).
**First simplification to remove with more time:** time-of-day speeds (the 04:00-07:00 departure lies before the morning peak, but returns to capital-region DCs do not).
**The two checks above that could have changed the decision**, distance model and departure waves: the calibrated distance model moves k* from 10 to 9 (keeping ten costs 4 M a month in that case) and keeps a 396 M saving, so it changes the size and the best k by one but not the sign; departure waves leave k* at 10 with 23 or 29 docks.

**The remedy for the G-E gap.**
`G1` ignores the clock, so it rates large territories too well and picks too few DCs (Spearman 0.58 with E over the evaluated candidates; searched over the whole pool, its pick has eight DCs and loses 425.5 M a month).
We applied the remedy the brief names as system knowledge: `G2` adds the routes the noon deadline and the 250 km limit force (Section 2).
On every evaluated candidate `G2` predicts E with Spearman 0.83 (0.91 over the whole pool, 0.72 within one k), and its pick loses 23.6 M a month, picking k = 10 as E does.
`G2` still misses the level (it over-states E by a median of 463 M, more for poor candidates: standard deviation 1,566 M), so the discrepancy GP models E − `G2` over the seven features rather than trusting `G2`'s value.

## 5. Demonstration & Evaluation

**Running the code.**
From `code/`: `pip install -r requirements.txt` (numpy 2.2.6, scipy 1.15.3), `python run_full.py` (all 9,718 planning stores, the reported run; 1,127 s on a DGX Spark with 16 worker processes: 966 s for the pipeline, 160 s for the extensions), `python run_reduced.py` (1 store in 5, 6 min 48 s with two worker processes on a laptop).
Seed 437; distances from the shipped cache, no network access.
The reduced run repeats the network search and the evaluation (pool, search, validation, final and held-out days, the R2 and R3 measures) with 1,938 stores and leaves out what only the full run reports (outcome tables, departure waves, reversals, extensions); it has fixed costs and store bounds scaled by one fifth (30 M a month, 100-280 stores) and a pool of 14 candidates per k instead of 30; it reproduces the structure of the results (Section 4, thinning row).
Each run writes `results/<profile>/registry.json` and the input tables of [A §2.5]; the full run also writes the outcome tables, holds every number in the three deliverables and rebuilds `demo.html` and `proposal.html`.
`python verify.py` re-checks the shown run independently: 29 of 29 checks pass (`results/full/verification.json`): every store of the shown day served once on both networks, no route breaking a limit unflagged, cost identities, the paired saving, the LP within its bounds, a deterministic evaluation that is the same with one or two worker processes, departure waves, the outcome tables, the heuristic against exact set partitioning, the page's JavaScript engine against the Python one, no external resources in the page, the local app's live solve, the embedded registry, both Spearman values, the extensions, and the drift sweep reproducing today's network in its 2016 row.
The hand-in ZIP, extracted into a fresh Python 3.10 environment from `requirements.txt` and run offline (`run_reduced.py`, 2 workers, 17 min on a laptop), reproduces the reduced registry produced on the Spark (aarch64, Python 3.12): of 54,642 numbers only 27 expected-improvement values differ by more than 1e-9 (at most 0.07%), and every search choice and result is the same.

**The demonstration.**
`demo.html` opens offline from the extracted folder (checked in Chromium 149 (Playwright 1.61) with the network disabled: every request other than `file://` blocked, none attempted; no console error on any tab at 1440 px and at 390 px (phone); no horizontal overflow).
Its tabs follow the decision: *The answer* maps today's and the recommended network (`D1-network`, `D2-assignment`), with the saving's decomposition, the reversal table, the sweep with its two components against k and the four statements; *Delivery day* animates every route of one day on the road network for either network and solves one DC live (`D4-routing` with the owned fleet of `D3-fleet`) while the reader changes the demand day, the deadline, the stop time, the speed, capacity, stops and the fleet; *How it works* steps through the formulation by lecture, replays the 40 evaluations with the rule that chose each against random selection, and plots `G2` or `G1` against E for every evaluated candidate (R3); *Data & baseline* shows the instantiated data, the demand model, the posterior predictive check and how today's network grew from 1990; *Checks* holds the normal, boundary and failure cases, the two balance-table checks, the outcome tables, the store-level view and the verification record; *Extensions* shows the closure sequence, the robustness runs and the value of information.
The page's live solve is a simplified copy of `dcn/routing.py` in JavaScript (no 2-opt, the calibrated distance model instead of the road cache) and says so; on the shipped day it gives the same vehicles and kilometres as the Python engine without 2-opt (`verify.py`).
`python app.py` serves the same page on `http://localhost:8437` and answers the live solve with `dcn/routing.py` on the cached road distances, the exact rules of the reported run.
Every precomputed number on the page carries a tag naming the command that reproduces it.

**Comparison conditions shared by every network.**
The same lower level, the same road distances, the same sampled days (common random numbers), the same fleet policy and the same E; the baseline differs only in keeping its historical territories, as the brief prescribes [A §2.3], and the step "today's sites, re-assigned" isolates that difference.
Information used to choose and outcomes used to report are kept apart: the 7 search days choose the network; the 28 final days only re-score the top five and measure the reported saving; the 14 held-out days, disjoint from the final ones, are never seen by the search, and on them the owned fleet stays as sized on the final days.

| Case | Inputs / reproduction steps | Expected result / pass criterion | Observed result and supported conclusion |
|---|---|---|---|
| Normal | *Delivery day* tab, "Solve one DC live": Gimpo Gochon (1,400 stores of the recommendation), ordinary weekday 2026-11-04, default limits; or `python app.py` and the same request | Every store visited once; no route breaks load, stops, km, the shift or the noon deadline; vehicles at or above the load and stop bound | In the page: 67 vehicles, 4,878 km, 100% before the deadline, 0 uncovered stores (in-browser engine, no 2-opt); with `python app.py`: 69 vehicles, 4,847 km, the same as `routing.solve` (`verify.py`). Every route audited from coordinates and demand: 0 violations. The routing works on a full 1,400-store territory in under a second |
| Boundary | *Checks* tab, boundary card; *How it works* Q5, search step slider at 1 | The DCs at a bound are named; with B = 1 only the first seed is evaluated | Gimpo, Namyangju and Siheung sit at the 1,400-store cap and Wonju and Gyeongju at the 500 minimum; the assignment LP's duals (`price_hi`, `price_lo` in the registry) value one more store of cap at 97-116 and one store less of minimum at 31-120 cage-km a day. With B = 1 the search returns the k = 7 seed at 8,686 M a month, worse than today (6,419 M); with B = 40 it returns 5,828 M |
| Failure | *Checks* tab, failure card, and its button "Show the peak day with 12 vehicles"; or `evaluate.evaluate(ctx, sites[:6], days)` | No cost shown; the reason stated; uncovered stores named as such | "6 DCs cannot hold 9,718 stores within 500-1,400 per DC": the bounds make k ≤ 6 infeasible, and the page shows the reason instead of a number. A second failure mode, a day the fleet cannot cover: on the peak day (2027-09-13) the model hires 125 spot trucks above the 627 owned; capping the live solve at 12 vehicles shows the uncovered stores and their stock-out penalty instead of a valid-looking plan |

**Baseline and recommendation, on the 28 final days** (M KRW a month).

| Network | k | Fixed | Owned fleet | Fuel | Spot | Relay | Total | Vehicles a day | Before noon |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Today (baseline, historical territories) | 12 | 1,878.0 | 3,624.5 | 895.8 | 113.6 | 55.0 | **6,566.9** | 648 | 100% |
| Today's sites, territories redrawn by the LP | 12 | 1,878.0 | 3,410.0 | 772.7 | 119.9 | 11.0 | 6,191.6 | 610 | 100% |
| Best 12 sites | 12 | 1,776.0 | 3,327.5 | 774.6 | 120.2 | 110.0 | 6,108.4 | 594 | 100% |
| **Recommended** | 10 | 1,464.0 | 3,448.5 | 848.1 | 114.8 | 99.0 | **5,974.5** | 617 | 100% |
| Strategy's eight (best k = 8) | 8 | 1,273.5 | 3,767.5 | 1,078.5 | 105.2 | 143.0 | 6,367.7 | 678 | 100% |
| Proxy only (lowest `G1` in the pool) | 8 | 1,200.0 | 3,894.0 | 1,095.5 | 89.5 | 121.0 | 6,400.0 | 696 | 100% |

The saving of the recommendation is **592.4 M KRW a month** on the final days (90% bootstrap interval over days 584.0-601.0) and **582.6 M** on the held-out days (570.9-593.7), with 100% of deliveries before noon on every day for both networks.
It decomposes into 375.3 M from redrawing today's territories (the decade of growth without rebalancing), 83.2 M from moving to the best 12 sites and 133.9 M from running 10 DCs instead of 12.
The Strategy team's eight DCs save 199 M against today but cost 393 M more than ten: fewer DCs save rent and lose more on longer drives, as Delivery Operations warned.
The recommendation moves 8,154 stores to another DC; 1,075 of them end up more than 30 km farther from their DC, all still served before noon.

**Prediction quality and decision quality (R3).**
Over the 40 candidates the search evaluated, `G2` ranks E with Spearman 0.83 (0.91 over the whole pool of 390, 0.72 within one k); its own pick is the k = 10 network E also prefers, and loses 23.6 M a month against the best evaluated candidate.
`G1`, the same criterion without the clock, ranks E with Spearman 0.58 (0.53 over the pool), picks k = 9 among the evaluated candidates and, searched over the whole pool, picks an eight-DC network that loses 425.5 M a month on the final days.
Neither criterion gets the level right (`G1` under-states E by a median of 788 M, $R^2$ −0.46; `G2` over-states it by 463 M, $R^2$ 0.36), which is why the search models the gap E − `G2` instead of trusting G's value.
The cause of the gap is the noon deadline: a route out of a large territory spends its morning on the out-leg, so for 253 of the recommendation's 617 routes a day the binding limit is the driver's shift and for 4 more the noon deadline, about as many as are full (257), while `G1` counts only load.

**The sweep** (search days, M KRW a month): for each k the best network of the whole pool, from the validation pass that evaluates all 390 candidates after the reported search, not only the 40 the search chose.

| k | 7 | 8 | 9 | **10** | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | 1,116 | 1,274 | 1,332 | 1,464 | 1,596 | 1,776 | 1,860 | 2,136 | 2,316 | 2,496 | 2,532 | 2,834 | 2,940 |
| Operating | 6,691 | 4,986 | 4,526 | 4,364 | 4,260 | 4,186 | 4,258 | 4,214 | 4,213 | 4,250 | 4,446 | 4,498 | 4,526 |
| Total | 7,807 | 6,259 | 5,858 | **5,828** | 5,856 | 5,962 | 6,118 | 6,350 | 6,529 | 6,746 | 6,978 | 7,331 | 7,466 |

Operating cost falls steeply up to ten DCs and is flat beyond twelve, while rent rises by about 150 M per DC, so the total is U-shaped with its minimum at k = 10; k = 9 and k = 11 are within 30 M (0.5%), less than a 5-minute change in stop time moves the costs, so the recommendation is "ten, with nine or eleven as near-ties", not a sharp optimum.
Today's network costs 6,419 M on the same days.

**The log and the rule's worth (R4).**
The reported search spent B = 40: the `G2` seed of every k from 7 to 19 (13 evaluations; the best, k = 10, at 5,851.2 M), then 27 expected-improvement picks; the 14th evaluation found a k = 11 network at 5,856.2 M and the 16th the pool's best, a k = 10 network at 5,827.6 M, which no later pick beat.
Random selection with the same seeds and the same budget ended at 5,851.2 M, the best seed: in 90% of 2,000 random orders the 27 random picks never improved on the seeds, because 1 of 377 remaining candidates is the best.
The rule's worth is therefore 23.6 M a month on the search days and, more usefully, a guarantee the brief asks for: the whole pool was evaluated afterwards for validation, and the search had found its best member.
Most of the value of the search sits in the generation step, not the selection step: the clock-aware seeds alone come within 0.4% of the best.
Every evaluation is in `registry.json` (`log_bo`, `log_random`) with step, candidate, sites, k, `G1`, `G2`, E, service and the rule that chose it.

**Sampled days versus one average day (R2)** is reported in Section 3.

**When the recommendation reverses (R5).**
Today's network and the best evaluated network of every k re-scored on the search days with one assumption changed.

| Changed assumption | k* | Saving against today (M a month) |
|---|---:|---:|
| As reported | 10 | 591 |
| Stop time 10 min / 20 min | 9 / 10 | 605 / 560 |
| Speed 30 km/h / 45 km/h | 11 / 9 | 805 / 578 |
| Calibrated distance model for every pair | 9 | 396 |
| DC fixed cost 100 M / 200 M a month | 11 / 9 | 469 / 743 |
| Relay driver free / at the spot rate (final days) | 10 / 11 | 636 / 503 |
| 500-store minimum dropped for redesigns | 11 | 671 |
| **Strict brief: no relay routes, stores beyond one driver-day are stock-outs** | 11 | **−511** |
| Strict brief and no 500-store minimum for redesigns | 12 | 625 |
| Departure waves 04:00-07:00 with 23 docks per DC / 29 docks | 10 / 10 | (k* unchanged) |
| Routes built by PyVRP instead of savings (day 0, measured; k not re-searched) | (10) | about 437 |
| **Today's network already optimal for today's stores** (p-median on road km, 12 DCs) | 10 | **−61** |

Two rows reverse the conclusion.
First, if today's real network were already as good as a p-median design for today's stores, keeping it would be 61 M a month cheaper than the best redesign: the redesign's value lies in how far today's real network is from a design on road km for today's stores (swept by design year below).
Second, if the business holds every vehicle to the brief's one-driver limits and also keeps the 500-store minimum, the far east-coast and mountain stores can be served neither by relay routes nor by a small DC near them, and the best redesign checked costs 511 M a month more than today; allowing either the second driver (the main case, 591 M) or a small coastal DC below 500 stores (12 DCs, 625 M) restores the saving.
Which of the two the business accepts is a decision to make before any lease (register, Section 3).

**How far must today's network have drifted? (the first reversal, swept).** Today's network rebuilt by the same planning rule as if the last redesign had been in another year (straight-line p-median over the stores open then, later stores added without rebalancing), each scored under E on the search days against the best redesign (`dcn/extensions.py`; the 2016 row reproduces today's network exactly).

| Year of the last redesign | 2010 | 2013 | **2016** | 2019 | 2022 | 2026 |
|---|---:|---:|---:|---:|---:|---:|
| Stores open then | 4,197 | 5,188 | 6,178 | 7,168 | 8,300 | 10,000 |
| Today's cost (M a month) | 6,502 | 6,316 | 6,419 | 6,151 | 6,129 | 6,185 |
| Saving of the best redesign (M a month) | 675 | 488 | **591** | 323 | 302 | 357 |

The saving stays positive for every year: even a network drawn in 2026 for all of today's stores keeps 357 M, because it is planned on straight-line km and without the noon clock.
The saving is not monotone in the year, because each year's design is a different discrete set of sites.
Only a design on road km for today's stores (the reversal row, −61 M) removes it, so the saving rests on how today's network was planned as much as on when; the first real-data check (Section 6) measures both, by scoring today's real network under the same E.
The number of DCs moves between 9 and 11 under every single changed input, never to 8; only the strict brief with the minimum dropped (a small coastal DC kept) gives 12.

**Extensions (additional points).**

*A sequence of closures.* The leases end one after another (Gimpo 2027-03 to Gangneung 2029-12), so the redesign is a sequence of decisions with a state: the set of open sites and the end date of each lease (`D1` becomes Stateful when the boundary includes time).
`dcn/extensions.py` follows the twelve expiries from January 2027: at each, the site is renewed for ten years or closed, and sites of the recommendation are opened, whichever gives the lower monthly E (search days, territories redrawn by the LP, no store minimum while the network is in transition).
Four policies over 36 months, in bn KRW: keep everything as it is 231.1; redraw today's territories only, no lease touched 217.6; follow the leases committed to the recommendation 214.5; switch to the recommendation at once 240.5, because the released sites' rent (30.7 bn) runs until their leases end.
Switching at once therefore costs 9.4 bn more than changing nothing, while following the leases saves 16.6 bn, 13.5 bn of it from redrawing territories, which needs no lease at all.
A myopic policy (whatever is cheapest at each expiry) renews Yongin, Andong and Gangneung for ten more years and ends at 12 DCs; it is 1.0 bn cheaper over the 36 months, because it skips the months in which a closed DC's replacement is not yet open, but its end state costs 15.8 M a month more than the committed one (5,792.9 against 5,777.1 M under the same pricing), so it gives the difference back within six years of a ten-year lease.
Conclusion: the one-shot design is the right target but not the right plan; the plan is the committed sequence (Section 6).

*Robustness.* The best network of every k from 7 to 13 and today's network re-scored on the same search days with demand scaled (`dcn/extensions.py`).

| Scenario | Best k | Saving of k = 10 (M a month) | Regret of k = 10 (M a month) |
|---|---:|---:|---:|
| As reported | 10 | 591 | 0 |
| Chain volume −15% | 10 | 581 | 0 |
| Chain volume +20% | 10 | 580 | 0 |
| Capital region +30% (Seoul, Gyeonggi, Incheon) | 10 | 602 | 0 |
| Calibrated distance model for every pair | 9 | 393 | 4 |

A demand regime shift moves neither the best k nor the size of the saving by more than 2%: volume changes every network's cost alike, and the capital-region shift falls on the region where the recommendation adds two DCs.
The distance source matters more (the saving falls by a third with the calibrated model only), but the decision moves by one DC and costs 4 M a month if taken anyway.
These scenarios change the regime, not the unobserved quantity behind the records, so they show robustness, not a second world consistent with the same history; the one such world we test is today's network being already optimal (Section 5, reversals).

*Value of information.* Lecture 3's expected value of perfect information, with today's decision taken under a prior and the decision after measuring taken per scenario: $\mathrm{EVPI} = \sum_s p_s E_s(a^\star) - \sum_s p_s \min_a E_s(a)$, over the networks of the sweep for k = 7-13 (a lower bound, since better networks per scenario may exist).
*Measure travel times:* stop time 10/15/20 min × speed 30/35/45 km/h, prior 0.25/0.5/0.25 on each, independently `[ASSUMPTION]`; nine re-scorings of every k.
The best k ranges from 8 (10 min, 45 km/h) to 11 (30 km/h); under the prior the best decision now is eleven DCs (expected regret 27.2 M a month), with ten close behind (40.4 M), so EVPI = 27.2 M a month, about 3.3 bn over a ten-year lease, against a GPS study of one DC for one month.
*Collect more demand history:* EVPI over chain volume −15% / as now / +20% is 0 (k = 10 is best in all three), and evaluating every network on days drawn from the true store rates, which the generator knows and the model does not, leaves k = 10 best with a saving of 599 M (regret 0).
More history cannot change the decision because the network depends on where stores are and how long a stop and a kilometre take, not on each store's exact rate.
**Decision, reconciled with the recommendation:** under the prior, eleven DCs has the lower expected cost (by 13 M a month), while at the reported 15 min and 35 km/h ten is best.
The choice between them does not have to be made now: the best 9-, 10- and 11-DC networks take the same action at every one of the twelve lease expiries (keep Gimpo and Cheonan, give up the other ten), and eleven is ten plus Jinju Sabong.
So the plan follows the leases now and decides whether to add Jinju after the GPS study has measured stop time and speed; that is exactly the information the EVPI says is worth having first.

*Candidate generation (Lecture 6).* A learned generator, after Lecture 6's CbAS: for k = 9, 10 and 11 a product of per-site inclusion probabilities, fitted to that k's pool, then refitted four times on 200 proposals each toward networks the search's own surrogate (G2 plus the GP on its 40 evaluations) predicts below a rising bar (the 20th percentile of its predictions), each draw weighted by the prior ratio (`dcn/extensions.py`).
The four best new networks of each k, all absent from the pool, were evaluated in full on the search days: the best costs 6,009 M against the pool's best 5,828 M (3% more), at a Jaccard distance of 0.46-1.0 from the pool's best network of its k, and the surrogate's prediction missed E by up to 3.6% in either direction.
What it buys the search here is diversity, not a better optimum: the clock-aware seeds and their local moves already hold the best networks of this instance, and the generator's refits drift towards where the surrogate is wrong, the lecture's warning, which is why every generated network is judged by E.
It would pay with a weaker pool (no clock-aware G, or a longer candidate list), where local moves never reach the good regions.

**What the demonstration establishes and what it does not.**
It establishes, in the fictional instance, that the evaluation is consistent (every route audited, cost identities hold, the saving is paired), that a stronger router would cut the saving by about a quarter but not remove it, that the search finds the best network of its pool, that the cheap criterion without the clock would have chosen eight DCs and lost 425 M a month, and that ten DCs beat today's network by about 580 M a month on days the search never saw.
It does not establish any saving for Dasol's real network: the baseline's distance from a good design is an assumption (Section 3), and the first reversal above shows that this distance carries the saving.
`Not run`: time-of-day traffic, the fresh-food second wave, moving and opening costs.

## 6. Client Proposal

**Management's two questions, answered for the fictional instance.**
*How many DCs?* Ten, with nine and eleven as near-ties (within 30 M a month of ten); eight, the Strategy team's proposal, costs about 400 M a month more than ten, and twelve or more cost more in rent than they save on the road.
*Where?* Gimpo Gochon and Cheonan Seobuk (kept), and Namyangju Jingeon, Siheung Banwol, Wonju Munmak, Nonsan Yeonmu, Naju Bitgaram, Gimhae Hallim, Gyeongju Oedong and Chilgok Waegwan (new); Gimpo, Namyangju and Naju appear in all five best networks, the other sites vary among them.
**Estimated saving:** 592 M KRW a month against today's network, with every store still served before noon.
The 90% interval 584-601 (583 M on held-out days) covers only the sampled demand days; the model checks move it much more: about 437 M with routes from a stronger solver (PyVRP), which our heuristic beats less on today's small rural territories (Section 2a), and 396 M with the calibrated distance model for every pair.
A fair range for the fictional instance is therefore about 400-600 M a month, positive under every check except a baseline already at the optimum.
This is a demonstrated result of the fictional instance only.
For Dasol's real network the saving is unknown: it equals how far today's real network is from a design on road km for today's stores, which only the real outcome tables can measure (Section 3); in the fictional instance it stays positive whatever year the last redesign was made (Section 5).

**What would reverse it.**
A real network already close to the optimum for today's stores (−61 M a month), or a business that accepts neither relay drivers on far routes nor a small coastal DC below 500 stores (−511 M a month; Section 5, reversals); short of reversing it, a measured stop time or road speed far from the defaults (they move the best number of DCs between nine and eleven).
Rent, the distance model, the relay price, the store minimum, departure waves, demand shifts and the routing method change the size of the saving, not its sign (Section 5 and the extensions).

**What to obtain first, and the first real-data check** (requests in Section 3).
1. The 12 months of `deliveries`, `vehicle_days` and `spot_hires`, with today's real territories: re-route today's real territories with our lower level under the same E and compare that with the best redesign, so that both sides use the same router; this is the check the whole saving hangs on.
   The real tables are compared with our routing of the same days separately: that gap is what better dispatching alone would save, and it must not be counted as part of the redesign.
   The same check asks the stores that would be served later: on the shown weekday 2,346 stores (24%) receive their delivery more than two hours later under the recommendation and 3,219 more than an hour earlier (from the routes stored in `registry.json`, `show`); if late delivery raises their orders, the assumption that orders do not depend on the network (Section 3) fails for them.
2. One month of GPS traces of one DC: the real stop time and speed, the two inputs that move k.
3. Real rents and lease terms of today's 12 sites and of the shortlisted new sites.

**Conditions.**
*Proceed* with the lease sequence below if today's real network, scored under the same E, costs more than the best redesign by more than the one-off cost of moving (to be priced by finance; at 592 M a month, a one-off cost of 7 bn KRW pays back within a year).
*Revise* the number of DCs if the measured stop time or speed lies outside 10-20 min or 30-45 km/h: re-run `run_full.py` with the measured values, three commands and about 20 minutes.
*Stop* and renew leases as they expire if the real network comes within the moving cost of the best redesign.

**How to implement: follow the lease expiries.**
Renew Gimpo Gochon (lease ends March 2027; it is in every one of the five best networks).
From June 2027, close each site outside the recommendation when its lease ends and open the new sites as they pay: Namyangju Jingeon when Hanam closes (2027-06), Siheung Banwol when Incheon Namdong closes (2027-09), Wonju Munmak and Gyeongju Oedong when Yongin closes (2027-12), then Gimhae, Chilgok, Nonsan and Naju as Busan, Daegu, Daejeon and Gwangju close (2028-03 to 2029-03); Namwon, Andong and Gangneung close without replacement in 2029.
Redraw territories at once: that step needs no lease and carries 13.5 of the 16.6 bn the sequence saves over 36 months (Section 5, extensions).
Each step is reconsidered with the real data at hand; the first lease the plan gives up is Hanam Gamil in June 2027.

**The decision requested from management now.**
Approve the three data requests above, to be delivered by the end of February 2027; confirm one business rule, whether far routes may carry a second driver or, failing that, whether a small coastal DC may stay below 500 stores (one of the two is needed for any redesign to pay; register, Section 3); renew the Gimpo Gochon lease that expires in March 2027 (it is in every one of the five best networks, so renewing it is right whatever the real data show); and defer the Hanam Gamil renewal (June 2027), the first site the recommendation gives up, until the real-data check is done in April 2027.
No new site is leased before that check.

## 7. LLM Review & Key Revisions

Tool: Claude (Anthropic) in Claude Code, used as a coding agent and as a sparring partner; role-played stakeholder reviews (operations, finance, a franchise owner, an examiner) were run at three gates.
The three discussions below changed the result; each was checked by a calculation or an experiment, not by the model's word.

| Discussion / purpose | LLM suggestion | My assessment and verification evidence | Final decision or revision; location |
|---|---|---|---|
| 1. Is the routing heuristic good enough to rank networks? | Clarke-Wright savings with 2-opt is "close to optimal for depots of this size"; alternatively, put PyVRP (hybrid genetic search) inside E | Neither accepted without measurement. On run 3's networks PyVRP used 4.9% and 3.9% fewer vehicles than savings, a similar error on both networks, so I first concluded it could not move the ranking. I repeated the check on the reported networks of run 5, every territory, with a longer time limit where PyVRP left stores unrouted: the error is now 6.6% of operating cost on today's network and 2.9% on the recommended one, because savings is weakest on today's small rural territories (Andong 33 against 24 vehicles). The "error cancels" argument held for one pair of networks and failed for another. PyVRP inside E stays out: it is 300-700 times slower and stochastic; two cheap repairs gained at most one vehicle | Kept savings inside E; reported the measured gap per network and its effect: the saving would be about 437 M instead of 592 M a month with PyVRP's routes, still positive (Section 2a, balance table, reversal table; `code/checks/routing_gap.py`, `routing_summary.py`) |
| 2. The baseline: why did every redesign lose to today's network? | First version: "today's network is simply good; recommend keeping it" (run 3: best redesign 100 M a month worse) | I suspected the setup, not the network. Checks on the same E: under identical rules today's sites and the best redesign were within 0.2%; the gap came from today's exemption from the cap and the minimum, and from today's 12 having been placed by a p-median on today's own stores and road km, the search's own objective. That is a near-optimum, not "a chain that grew over decades" [A §2.5] | Rebuilt today's network as the 2016 planner's design with growth since (Section 3), pre-registered before scoring (D-069); the old optimum kept as a reversal row (Section 5) |
| 3. A better cheap criterion G | Learn a territory cost from routed territories and choose the network by a MILP on it (after published learned-cost location-routing work) | Fitted by non-negative least squares on 421 routed territories: it ranks held-out networks far better than G1 (Spearman 0.92 against 0.60) yet its own pick and its MILP optima lose 254-1,035 M a month under E, because it had no vehicle-per-territory term and the MILP left the region it was trained on: better prediction, worse decisions (Lecture 5) | Rejected as the decider; built G2 instead, the clock-aware criterion the brief names as system knowledge (Spearman 0.93 on that pool; in run 6, 0.83 on the evaluated candidates and 0.91 over the pool, and it picks the k E picks) and used it in the search (Section 4, the remedy) |

Other suggestions accepted after checking: the newsvendor reading of the two-thirds fleet quantile (verified: 1 − 5.5 M / (30.42 × 0.55 M) = 0.671); the transportation LP's integrality (verified on every evaluation: the largest fractional part is reported as `lp_frac` in the registry).
Rejected: thinning to 2,000 stores to save time (it changes stop density, the mechanism that sets k; Section 4 measures how much).
