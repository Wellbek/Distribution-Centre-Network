# IE437 Midterm Brain - Distribution-Centre Network Redesign

Version 1.2 · 2026-10-19 (day 0 of 14) · Louis Wellmeyer (20264059)

Status: planning complete, stakeholder review round 1 applied (Section 22), rolling records started (Section 25), nothing implemented yet.

This file is my working memory for the whole midterm.
It lives in `planning/` of the private hand-in repo `Wellbek/Distribution-Centre-Network` and is never part of the submission ZIP (the ZIP is built from an allowlist, Section 17.1).

**Legend used throughout**

- `[SRC]` a fact read directly from a source (brief, commit, lecture, file), with the reference.
- `[INF]` my inference from sources; plausible but not confirmed.
- `[IDEA]` a design idea of mine, to be built and checked.
- `[DECIDE]` a decision the user must take (collected in Section 23).
- `[RISK]` something that can cost marks or time.
- Citation keys: `[A §x]` = midterm brief v2.2 section x; `[T §x]` = template section; `[Ref §x]` = classification reference; `Lec n "slide"` = course deck chapter n (markdown source in `ie437/md/chNN_*.md`, same content as the slide PDFs and newer for chapters 0-4); `commit abc1234` = ie437 repo commit.

---

## 0. The fifteen things that matter most

1. The deadline is **Mon 2 Nov 2026, 10:00 KST**, submitted on KLMS as one ZIP `20264059_LouisWellmeyer.zip` of at most 200 MB [A §6].
2. 85 of 100 points sit in `problem-definition.md`; code plus demo is 10 and proposal plus LLM review is 5 [SRC: instructor README v2.2 in `teaching/midterm-depot-network/README.md`].
   The demo can be spectacular, but the marks are in the formulation, the balance table and the evidence.
3. The instructor's pilot run found that **the delivery window, not the river, creates the trade-off in the number of DCs** [SRC: commit c6e3383].
   A version of the brief that was live for about 30 minutes gave the answer outright: "with 10 minutes per stop and 45 km/h the fleet is set by load alone and fewer DCs always win" [SRC: commit bb5456a, removed in c814f0a].
   With the defaults (15 min, 35 km/h) the noon deadline leaves an out-leg reach of roughly 50-75 km, which is exactly the territory radius at 8-12 DCs (Section 4).
4. The pilot also found that **the location exploit is small** and that **a GP on raw DC coordinates cannot learn with B = 40** [SRC: instructor README v2.2, dry-run note].
   So the G-versus-E gap is expected to live in the *count* decision and in the time window, not in the exact sites.
5. **The average-day error is small unless the chain moves together on a day** [SRC: commit c6e3383].
   We must separate store noise (cancels), calendar effects (move the chain together) and chain-wide shocks (holidays, weather), and report each.
6. The 2/3 fleet quantile in the teaching defaults is not arbitrary: it is the **newsvendor critical fractile** $1 - 5.5\,\text{M}/(30.42 \times 0.55\,\text{M}) = 0.671$ (Section 4).
7. The capacity bounds 500-1,400 stores per DC give **k in [8, 20]** for 10,000 stores; "cut to eight" is exactly the capacity minimum, and k = 7 is infeasible (the natural failure case).
8. **Thinning 1-in-5 with one stop per store destroys the time-window mechanism in rural areas** (out-leg reach drops from about 52 km to about 8 km at 0.3 stores/km²) [IDEA, computed in Section 4].
   Recommendation: evaluate at full density (10,000 stores) with neighbour-list routing on the DGX, and *measure* the thinning distortion as one of the balance-table checks.
9. The baseline must be strong: plausible DC sites, same E, same days, same routing [A §2.5, R5]; a strawman is penalised [SRC: commit c814f0a].
   Decompose the saving into re-assignment of the current 12, re-siting, and changing the count, so the result cannot be an artefact of a bad historical assignment I generated.
10. The assignment's place must be argued [A §3.2]: I recommend re-solving it inside E by a capacitated transportation LP (convex, totally unimodular; Lecture 1 duality gives shadow prices of DC capacity).
11. The reported search is **one fresh run of exactly B = 40** full evaluations from logged seeds, including one G seed per k, compared with random selection on the same pool at the same budget [A §3.3].
12. The R3 analysis is Lecture 5's **signed decision bound** applied with G as the surrogate and E as the truth, with prediction quality and decision quality as two different numbers.
13. The surrogate is Lecture 5's **Kennedy and O'Hagan discrepancy**: $E(x) = G(x) + \delta(x)$ with $\delta$ a GP over pool features, which is exactly the brief's "model the gap E − G over the pool".
14. Every number in the definition, demo and proposal comes from one results registry produced by `code/`, so the three deliverables cannot disagree (the A1 grading guide says the grader traces claims across files).
15. The course repo is public and the brief changed four times on release morning; pull and diff it every day, because "any answer that changes the brief will be posted here as a new version" [SRC: `md/_ANNOUNCEMENTS.md`].

---

## 1. The assignment in one page

**What is decided.** How many DCs, at which sites, which stores each serves, how many vehicles each owns [A §2.2].
**Objective.** Lowest total monthly cost (DC fixed, vehicle fixed, fuel, spot trucks, service failures) with at least 98% of a day's deliveries before 12:00; a delivery after 14:00 is a failure [A §2.2].
**Evidence asked.** Baseline under identical conditions, cost against number of DCs, uncertainty of the saving, reversal assumptions [A §2.2].
**Data.** None supplied; eight tables specified; five inputs generated with a fixed seed, three outcome tables produced by running my own lower level on the current network over 12 months of history [A §2.5].
**Distances.** Actual road values or a model calibrated on road values; source, version, extract date, profile stated; every distance cached in `code/` [A §2.5].
**Heart of the exam.** Lower level, connection, upper level, fidelity-computation table with at least two decision-relevant checks [A §3].
**Course tools required.** R1 hierarchy and standard form (Lec 1), R2 conjugate demand with sampled days (Lec 2), R3 G kept apart from E (Lec 5), R4 budgeted surrogate search (Lec 4), R5 baseline, sweep, recommendation [A §4].

**Deliverables** [A §6]

| File | Content | Reader |
|---|---|---|
| `problem-definition.md` | Template's seven headings, §3.1-3.4 answered in full, I/O schema, evaluation log summary, LLM review | A colleague who must implement or challenge it |
| `code/` | Generator, cached distances, lower level, evaluation, search, checks; README, `requirements.txt`; three commands (install, full run, reduced run), no network | The same colleague, reproducing numbers |
| `demo.html` or local app in `code/` | Map of baseline and recommended network, sweep, log, G vs E per candidate, live lower-level solve for one DC with editable day, window, stop time, vehicle limits; normal, boundary, failure cases; precomputed numbers labelled with their command | A manager's analyst |
| `proposal.html` | 8-12 slides answering management's two questions | Management |

**Public rubric v2.2** [A §7]: structure, data and I/O 15 · lower level 15 · connection, upper level and search 15 · fidelity-computation balance 15 · demand under uncertainty 10 · evidence (G vs E, baseline, sweep, recommendation) 15 · code and demo 10 · proposal and LLM review 5 · bonus up to 10 (VOI, closure sequence, candidate generation, robustness).

**The grader's twelve things** [A "At a glance"] become the compliance matrix in Section 21.

---

## 2. Intelligence from the git history (the "secret insights")

### 2.1 Where things are

- `ie437` is the instructor's course-site repo `git@github.com:omeletJK/ie437.git`, **public**, GitHub Pages enabled [SRC: `gh api`].
- Author of the midterm commits: Jinkyoo Park (`jinkyoo`, `omeletJK`), with an AI model as co-author.
- The midterm package lives in `teaching/midterm-depot-network/student/`; the instructor notes (`instructor/grading-guide.md`, `preparation-notes.md`, `dry-run/`) are gitignored and **not** in the repo.
- `Distribution-Centre-Network/` holds a byte-identical copy of the v2.2 student package; remote `git@github.com:Wellbek/Distribution-Centre-Network.git` is **private** with no commits yet.

### 2.2 The last ten commits

| Commit | Time (KST) | What it reveals |
|---|---|---|
| 490e89b | 18 Oct 03:09 | Moves the A1 CGV teaching material in, including `movie-planning-assignment-2026-09/instructor/grading-guide.md` (see 2.5) |
| 6192ea5 | 19 Oct 09:47 | Site support for a `kind: midterm` catalogue entry |
| 6fc09e4 | 19 Oct 09:47 | v1.0: midterm as a 14-day take-home; source material is a research-engineer **hiring task on logistics hub relocation** (`/Users/jinkyoo/Teachings/midterm exam.pdf`); industry unified to one convenience chain "so grading is comparable"; R1-R5 added so the course tools are compulsory |
| c6e3383 | 19 Oct 10:59 | v2.0: three instructor corrections and the pilot findings (2.3) |
| bb5456a | 19 Oct 11:15 | v2.1: teaching defaults, thinning, approach section, an answer-giving stuck table |
| c814f0a | 19 Oct 11:49 | v2.2: student-perspective review; thinning distortions; plausible baseline; fresh reported search; hint turned into a question |
| e3a0ea1 | 19 Oct 12:25 | Midterm tab and pinned notice; nothing new about content |
| c4b9e93, a531d15, c89f0b4 | 13-14 Oct | Lecture 5 deck edits (COMs, NML, RoMA figures): Lecture 5 is fresh in the instructor's mind |

### 2.3 Instructor pilot run and corrections (commit c6e3383 message, README v2.2)

- "Rivers and mountains are not a trap to plant: the point is that routing runs on actual road travel distances."
  v1.0 asked for a planted barrier on a plane; v2.0 replaced it with real road distances.
- "The delivery window, not the river, creates the trade-off in the number of centres."
- "The average-day error is small unless the chain moves together on a day."
- "A surrogate over raw DC coordinates cannot learn from a few dozen evaluations, so the brief points to generator knobs or a gap model over a candidate pool."
- README v2.2 on the dry-run prototype (translated): the time window creates the DC-count trade-off, the location exploit is small, and the GP on raw coordinates cannot learn with budget 40; these measurements became the basis of the grading guide.
- The formulation and the solution-algorithm plan "carry 60 of 100 points; code/ is required."
- v1.0 R3 demanded "a concrete case where the network that is best under G is worse under E"; v2.0 softened it to "measure the gap and name its cause", consistent with a small location exploit.

### 2.4 Answers that were removed

- v2.1 stuck table, row "The sweep is flat or has no interior minimum": "Check whether time binds: with 10 minutes per stop and 45 km/h the fleet is set by load alone and fewer DCs always win." [commit bb5456a].
  v2.2 replaced it with: "Ask what limits a vehicle's day in your model - load, stops, kilometres or the clock - and which of those changes when a DC's territory grows." [commit c814f0a: "the stuck-table hint about the time window is a question rather than the answer"].
- v2.1 thinning only scaled the capacity bounds; v2.2 calls this "one real flaw": the DC fixed cost must scale by the same fraction, and stop density raises km per store by roughly √(thinning factor).

### 2.5 The leaked A1 grading guide, and what it says about how this course grades

The `.gitignore` pattern `/teaching/*/instructor/` matches only one directory level, so `teaching/cgv-case/movie-planning-assignment-2026-09/instructor/grading-guide.md` (an A1 draft guide in Korean, marked "do not distribute to students") was committed and is public.
Nothing comparable exists for the midterm in the repo.
What it teaches about the grader:

- **Hidden points live inside public criteria.** A1 hid "the purchaser is not the audience" inside the 10-point data criterion as 5 points (identify 2, explain the impact 2, respond 1); no deduction outside that criterion.
- **Bonus points reward self-discovered structure** (A1: schedules change demand; synthetic consumers), judged by approach, comparison and verification, never by naming a concept.
- **Levels for every criterion:** sufficient (specific, consistent across files, checkable), partial, superficial (terms only), unmet.
- An answer that identifies unresolved items with a confirmation plan is valued above one that fills values without evidence.
- Calling a problem Hierarchical from module order alone, Stateful from time-series data alone, or Feedback from repeated execution alone is reviewed critically.
- A prioritised minimal information plan beats a list of every possible request.
- The grader **traces a few main claims of the definition through the demo and the proposal**: same inputs, same objective, fair baseline, no overclaiming, demo limits leading to data requests, LLM claims visible in the files.
- The number of LLM uses, artificial error finds, style and AI-detection scores are **not** graded.
- If the demo does not run, only the demo criterion suffers; a simple implementation is credited when it explains its principle and boundary.
- Feedback format: the most valid judgment, the key assumption lacking evidence, one revision to move the proposal forward.

### 2.6 What the professor's own worked examples reveal about taste

From `teaching/assignment-01-model-answer/student/` (published A1 worked examples, release 1.8):

- Verification records with exact counts, SHA-256 hashes of artefacts, and explicit "Not run" or "not verified" for every unchecked claim.
- Paired comparisons on common validation paths with Monte Carlo intervals: "use the paired statistic rather than subtracting rounded table values".
- Clear separation of executed calculation from proposed extension ("no BO implemented; ILS named accurately").
- An operator flow: Import data → Objective & constraints → Run optimisation → Review results, with a dark sidebar, light workspace and fixed action bar.
- The professor's company (Omelet) sells routing and logistics-network products benchmarked against OR-Tools [SRC: Lec 0 "The same engine, compared with a solver baseline", "Running in the field"].
  The grader is a routing expert: lower-level accuracy claims will be read by someone who knows VRP heuristics well.
- The OI Factory rule: "each part is finished only when the next role can act on it"; "Part 2 is done when another person - or a model - could rebuild a working solver from it alone" [Lec 0 "The OI Factory"].
  This mirrors the brief's "write it so that a colleague could implement it" [A §3].

### 2.7 Reconstructed midterm grading guide (my best guess)

Confidence: H high, M medium, L low.

| Likely hidden point | Inside which public criterion | Confidence | How we earn it |
|---|---|---|---|
| Name what limits a vehicle's day (load, stops, km, clock) and show that the clock creates the interior minimum | Lower level 15 / Evidence 15 | H | Binding-constraint census per route and per k; sweep with and without the window |
| Four statements at four different levels; S&P and Ops are two terms of one objective; Data Team is a method (G) with an unearned optimality claim; Field Manager is a model-validity claim | Structure 15 | H | Section 5, with the consequences for comparison |
| G-vs-E gap lives in the count dimension and is small in location for fixed k | Evidence 15 | H | Report the gap within k and across k |
| Average-day gap small with independent noise, large when the chain moves together; the holiday spike | Demand 10 | H | Three-way decomposition (Section 10) |
| Raw coordinates fail; knobs or pool features work; the rule beats random at equal budget | Connection and search 15 | H | Pool + K&O GP + random comparison |
| Plausible baseline; same E and routing; baseline exempt from new bounds | Evidence 15 | H | Section 12 |
| Thinning distortions handled (fixed cost scaling, stop density) | Balance 15 | H | Measured, not only argued |
| Hard window versus penalty stated; realised service level reported for every network | Lower level 15 | H | Every result row carries a service level |
| Fresh reported search with B = 40 including the G seeds; development runs kept apart | Search 15 | H | Log header and seeds file |
| k = 8 is the capacity minimum; k = 7 infeasible | Structure / demo failure case | M | Failure case in the demo |
| Re-assignment alone already saves money (assignment "fixed long ago") | Evidence 15 | M | Saving decomposition |
| Two-stage timing (network before demand, routing after) decides what each level knows | Connection 15 | M | Section 8 |
| The 2/3 quantile is the newsvendor fractile | Connection 15 | L | One paragraph and a check |

---

## 3. My restatement of the problem

Dasol Retail (fictional) runs about 10,000 convenience stores and 12 DCs; one delivery per store per day in multi-temperature vehicles leaving between 04:00 and 07:00 [A §2.1, §2.3].
Leases expire over several years; management wants to know how many DCs, where, and what proves the answer [A §2.1].
At the planning horizon every current site can be kept or dropped and every candidate site can be leased; current sites are candidates [A §2.2].
The network (sites, assignment, fleet) is fixed long before demand is known; daily routes are planned the evening before, after that day's orders arrive [A §2.4].
That timing makes it a **two-stage stochastic programme**: first stage = sites, assignment, owned fleet; second stage = each day's routing as recourse.

---

## 4. Numbers that shape everything (teaching defaults, my arithmetic)

| Quantity | Value | Consequence |
|---|---|---|
| Chain demand | 10,000 × 2.2 = 22,000 cages/day | At least 459 vehicle loads/day at 48 cages |
| Stores per full load | 48 / 2.2 = 21.8 | Load binds before the 25-stop limit on average |
| Stop time per full load | 22 × 15 min = 5.5 h | Most of the noon window is stop time |
| Drive budget before noon, depart 04:00 | 8 h − 5.5 h = 2.5 h = 88 km | Out-leg plus inter-stop legs must fit in 88 km |
| Same, depart 05:00 | 1.5 h = 52 km | Departure time is a first-order lever, so dock congestion matters |
| Inter-stop km for 22 stops at density ρ (0.7124/√ρ per leg × detour 1.3) | ρ = 3/km²: 11 km; 1: 19 km; 0.3: 36 km; 0.1: 62 km | Out-leg reach 76, 68, 52, 26 km |
| Same after 1-in-5 thinning, one stop per kept store | Reach 62, 44, 8, −50 km | **Thinning option (i) breaks the window mechanism outside cities** |
| Territory radius, equal areas over about 100,000 km² | k = 8: 63 km; 10: 56; 12: 52; 16: 45 | The trade-off sits exactly where reach ≈ radius |
| 250 km/day limit | One-way road distance to the farthest store ≤ about 125 km | A coverage constraint on the upper level |
| Capacity bounds | k ∈ [⌈10000/1400⌉, ⌊10000/500⌋] = [8, 20] | "Eight" is the minimum; seven is infeasible |
| Owned vehicle per day | 5.5 M / 30.42 = 180,822 KRW | Spot (550,000 KRW) costs 3.04 times as much |
| Newsvendor fractile | Own the n-th vehicle iff P(need > n) ≥ 0.329, i.e. own the 0.671 quantile | The 2/3 default is cost-optimal with unlimited spot supply |
| Monthly cost scale, baseline | DC 1.80 B, vehicles about 2.65 B, fuel about 0.5 B KRW | Vehicles dominate; closing 4 DCs saves 0.6 B, which is lost if vehicles rise by more than about 23% |

Assumption for "month": 365/12 = 30.42 days [ASSUMPTION, to state].

---

## 5. The four statements (R1)

| Statement | Level | Decision or component | Consequence for comparison |
|---|---|---|---|
| Strategy & Planning: "12 → 8, lease and staff costs fall" | A **decision** (count = 8) argued from **one cost component** (DC fixed cost) | `D1-network`; component `C-dc-fixed` | True for its component; not comparable with Ops until both are written as total monthly cost E. Eight is also the capacity minimum, so it sits on a feasibility boundary |
| Delivery Operations: "farther, longer, more vehicles, may cost more" | An **evaluation** of the decision through the lower level | `C-operating-cost`, `evaluated_by: D4-routing` | The other half of the same objective; S&P and Ops meet on one scale, E = fixed + operating. Neither alone answers |
| Data Team: "centre of gravity, optimal, minutes" | A **method** for the location decision (a generation criterion G) plus an **optimality claim** valid only for its own criterion | `G0` (weighted squared map distance) | A method is compared by the value of what it proposes under E, not by its own score. The centre of gravity minimises weighted *squared* map distance (closed form), not distance (Weber point), road distance or cost, and it says nothing about how many DCs |
| Field Manager: "across the river, trucks drive to the bridge" | A **claim about model validity** (map distance is not road distance) | The distance model inside G and E | Checked, not compared: measure road/map ratios and the G-vs-E gap; the pilot says the barrier is not where the trade-off comes from, so the claim is likely true locally and small in aggregate |

Lecture link: under map distance the one-site problem is convex (Weber point, or the closed-form centre of gravity for squared distance); under road distance it is not, because road distance as a function of the site is not a norm [Lec 1 "Convexity - the line between easy and hard"].
The Field Manager's point is the moment the Data Team's convex shortcut stops being convex.

---

## 6. Decisions, dependencies, classification (R1)

**Boundary** [IDEA]: one redesign chosen now for a steady-state planning year at the horizon when all leases are free [A §2.2]; Jeju and other islands excluded [ASSUMPTION; consequence: their stores keep their current supply]; the fresh-food second wave out of scope [A §2.3].
The company's current practice (experience routes, fixed historical territories) is kept apart from the constructed baseline (current 12 DCs and historical assignment, routed by my lower level) [T §1].

| ID | Decision | Chosen by / approves | Time scale |
|---|---|---|---|
| `D1-network` | Number of DCs and their sites | Management | Once, years |
| `D2-assignment` | Store-to-DC territories | Logistics planning | Months |
| `D3-fleet` | Owned vehicles per DC (fleet policy quantile) | DC operations with finance | Months, contracts |
| `D4-routing` | Each day: vehicles used, store sequences, spot hires | DC dispatch, the evening before | Daily |

Dependencies:

```text
D1-network → D2-assignment: feasible-region (open DCs only), constraint (capacity bounds per open DC)
D1-network → D4-routing: parameter (DC location changes every distance and time)
D2-assignment → D3-fleet: parameter (store set and its demand distribution)
D2-assignment → D4-routing: parameter (which stores are routed from which DC)
D3-fleet → D4-routing: available-action (owned vehicles), objective (spot cost above owned)
```

Evaluation relations:

```yaml
- id: C-operating-cost      # vehicles, fuel, spot, penalties
  role: cost
  model: formulation
  evaluated_by: D4-routing
- id: C-service-level
  role: constraint
  model: formulation
  evaluated_by: D4-routing
- id: C-dc-fixed
  role: cost
  model: formulation
```

| Object | Property | Classification | Evidence |
|---|---|---|---|
| Graph | Decision Structure | Hierarchical | D1 changes D2's feasible region and D4's parameters |
| D1, D2, D3 | State | Stateless | One redesign; no state carried between epochs in this boundary (a closure sequence would make D1 Stateful: bonus) |
| D4 | State | Stateless | Days independent: missed deliveries are penalised, not backlogged; empties ignored [ASSUMPTION] |
| D1, D2, D3 | Information | Open-loop | Fixed before demand is observed; basis: operational-requirement (leases, fleet contracts) |
| D4 | Information | Open-loop | Routes fixed the evening before from known orders, no en-route re-planning; basis: operational-requirement |

Points to state from the reference: re-running D4 every day does not make it Feedback [Ref §6]; receiving an evaluation from D4 is not Feedback for D1 [Ref §4]; the demand forecast supplies parameters to formulation components and does not make them Data-driven [Ref §3].
The route-cost component is Formulation even though a heuristic computes it; the heuristic is a solution method, not a model class [IDEA, consistent with Ref §3].

---

## 7. Lower level: one DC's day (§3.1, 15 points)

### 7.1 Standard form (compact, as the brief expects)

Sets: stores $I_j$ assigned to DC $j$; vehicles $V = V^{own} \cup V^{spot}$; routes $r$ as store sequences.
Given: demand $q_i$ (cages) for the day, road distances $d_{ab}$, times $t_{ab} = d_{ab}/v + s$ with $v = 35$ km/h and $s = 15$ min, capacity $Q = 48$, stop limit 25, km limit 250, departure $\tau_0 \ge$ 04:00, deadline 12:00, shift 10 h including 1 h loading.

$$\min_{x}\; c_f \sum_{r}\sum_{(a,b)\in r} d_{ab} \;+\; c_s\,\big(|R| - n_j\big)^+ \;+\; p_{late}\, L \;+\; p_{out}\, M$$

Subject to: every store on exactly one route or counted as missed; $\sum_{i\in r} q_i \le Q$; $|r| \le 25$; $\mathrm{km}(r) \le 250$; arrival $a_i \le$ 12:00 for every served store (hard window, recommended); return within the shift; $a_{next} = a_{prev} + s + t_{prev,next}$.
$n_j$ is the owned fleet from D3 and $|R|$ the routes used; owned vehicles have zero marginal daily cost (driver included), so the lower level minimises vehicles first and km second (lexicographic), which is what fleet sizing needs.
Set-partitioning view for the exact small-instance check: $\min \sum_r c_r \lambda_r$ s.t. $\sum_r a_{ir}\lambda_r = 1$, $\lambda_r \in \{0,1\}$, over enumerated feasible routes [IDEA].

### 7.2 Window: hard constraint, with the 12:00-14:00 grey zone discussed

- Hard: no stop after 12:00 when routes are built; a long territory needs more vehicles; service level is 100% unless the fleet cannot cover or a store is unreachable.
- The brief allows 2% after noon and only penalises after 14:00, so a cost-minimising lower level could push up to 2% of stops into the free 12:00-14:00 zone [INF].
  I treat that as a known exploit of the service definition and do not use it; the balance table records it and one check (deadline 12:30 for all stops) bounds its value.
- Report the realised service level of every network compared [A §3.1].

### 7.3 Method

| Component | Choice | Why |
|---|---|---|
| Construction | Clarke-Wright parallel savings with neighbour lists (about 40 nearest by road), feasibility check on every merge (load, stops, km, deadline, shift) | Fast, deterministic, the classic for many-stop depots (Clarke and Wright 1964) |
| Improvement | 2-opt and or-opt within routes; relocate, swap and 2-opt* between neighbouring routes; route-elimination attempts | Vehicles dominate cost, so emptying routes matters more than shaving km |
| Speed | numba, typed arrays, sparse distances with calibrated detour fallback | Target ≤ 0.5 s per DC-day at 1,000 stores |
| Determinism | Fixed tie-breaks, no randomness | Common random numbers across candidates; reproducibility |
| Accuracy check 1 | Exact set partitioning (HiGHS via `scipy.optimize.milp`) on instances of at most 14 stores | Optimality gap where exact is possible |
| Accuracy check 2 | PyVRP (hybrid genetic search, Wouda, Lan and Kool 2024) with long time limits on real DC-days | Near-optimal reference at full size |
| Accuracy check 3 | Lower bounds: vehicles ≥ max(⌈Σq/48⌉, ⌈n/25⌉) | A free certificate of vehicle-count quality |
| Upper-level effect | Heuristic gap against territory size (k) | A heuristic that is worse on big territories biases the sweep toward more DCs: must be measured |

What one solve returns upward [A §3.1]: vehicles used, km, late and missed deliveries, spot trucks needed above the owned fleet, the binding constraint of every route (load, stops, km, clock), service level.

### 7.4 Modelled and omitted features

Modelled: load, stops, km, deadline, shift, departure window, road distances, stop time.
Omitted with reason (each a balance-table row): multiple trips (a second wave cannot meet noon), driver breaks (inside the 10 h shift, [ASSUMPTION] taken at the DC), time-of-day traffic (Seoul morning peak; check with 30 km/h), loading-dock congestion (check with departure waves), returns and empties (no capacity effect assumed), unloading-time variability.

---

## 8. The connection: how the lower level evaluates a candidate (§3.2)

**Passes down:** open DC set; the assignment rule's output; the fleet policy (quantile); the sampled demand days.
**Passes up:** expected monthly operating cost (vehicles, fuel, spot, penalties), owned fleet per DC, service level, binding-constraint census.

$$E(x) = \sum_{j} f_j y_j \;+\; c_v \sum_j n_j(x) \;+\; \frac{365}{12}\cdot\frac{1}{N}\sum_{n=1}^{N} Q\big(x, n(x); \xi_n\big)$$

$n_j(x)$ is the 0.671 quantile of DC $j$'s daily vehicle need over the sampled days (newsvendor), $Q$ is the daily fuel, spot and penalty cost, and $\xi_n$ are demand days sampled from the posterior predictive (sample average approximation; Kleywegt, Shapiro and Homem-de-Mello 2002).
Cost of one evaluation: k × N lower-level solves (k = 10, N = 7: 70 solves, about 30 s on the DGX with 8 workers if the 0.5 s target holds).
**Common random numbers:** the same N store-level demand days for every candidate and the baseline (demand is per store and does not depend on the network); this is what "identical conditions" means, and it makes paired differences precise.

**Where the assignment lives (recommended):** re-solved inside E by a capacitated transportation LP

$$\min_{z \ge 0} \sum_{i,j} w_i\, \tilde d_{ij}\, z_{ij}\quad \text{s.t.}\quad \sum_j z_{ij} = 1\;\;\forall i,\qquad L \le \sum_i z_{ij} \le U\;\; \forall j \text{ open}$$

with $\tilde d_{ij}$ a window-aware cost-to-serve (road distance plus a penalty beyond the noon reach radius) [IDEA].
It is an LP with a totally unimodular constraint matrix, so the optimum is integral (Lec 1 convex family), and its duals price each DC's capacity bound (Lec 1 "What is a little more freedom worth?").
Consequences to state: the candidate is just the DC set (a smaller search space); E judges "this DC set operated by this assignment rule"; a better rule could only lower E.
The baseline keeps its historical assignment (a fact of the operation, exempt from new bounds [A §2.3]); the candidate "same 12 DCs, re-assigned" isolates the assignment saving.

---

## 9. Upper level: how many DCs and where (§3.3, R4)

### 9.1 Standard form

$$\min_{y\in\{0,1\}^{J}} \; E(y) \quad\text{s.t.}\quad \sum_j y_j = k,\;\; k \in \{8,\dots,20\},\;\; \text{a feasible assignment exists},\;\; \max_i d_{i,a(i)} \le 125\ \text{km}$$

Convex or linear parts: the assignment for fixed sites (transportation LP); the one-site problem under map distance (Weber point; centre of gravity for squared distance); the LP relaxation of the capacitated facility location problem as a lower bound on G.
Combinatorial parts: the site subset ($\binom{60}{10} \approx 7.5\times10^{10}$); E itself is a black box built from heuristic routing, non-convex and noisy.
Implication: exact solution only for G (MILP on H3-aggregated stores, certified by the HiGHS gap), never for E; E is searched under a budget.

### 9.2 The criterion family

| Name | Definition | Role |
|---|---|---|
| `G0` | Weighted centre of gravity (weighted k-means on map coordinates, snapped to the nearest candidate site) | The Data Team's method; the proxy-only approach |
| `G1` | Capacitated p-median on road distance with fixed costs: $\sum f_j y_j + c \sum_i w_i d_{i,a(i)}$ | Standard generation criterion (MILP, exact on aggregated stores) |
| `G2` | G1 plus a continuous-approximation route model (Daganzo 1984; Beardwood, Halton and Hammersley 1959) with the window's effect on stops per route and regional detour ratios | Lecture 5 "system knowledge" remedy |
| `E` | Full evaluation (Section 8) | The judge |

### 9.3 Pool, features, surrogate, acquisition (parameterisation (ii) of the brief)

- **Pool** [IDEA]: for each k in 8..20, the G1 optimum, the next best G1 solutions from swap neighbourhoods, the G0 solution, and random feasible single and double swaps; about 400-600 candidates, all feasible for capacity and the 125 km coverage.
- **Features** (the brief's plus mine): k, G1, G2, mean and maximum road/map ratio of assigned legs, load imbalance (CV of stores per DC), share of demand beyond the noon reach radius, mean and 95th-percentile DC-store road distance, capacity slack.
- **Surrogate:** Kennedy and O'Hagan discrepancy $E(x) = G(x) + \delta(x)$, $\delta \sim \mathcal{GP}(0, k_{\text{Matern-5/2, ARD}})$, hyperparameters by marginal likelihood [Lec 4 "Fitting the kernel"; Lec 5 "A simulator - Kennedy & O'Hagan"].
  The prediction relaxes to G away from evaluated candidates; that is the assumption to state.
- **Acquisition:** expected improvement for minimisation, evaluated on every pool member (no inner optimiser needed on an enumerable pool [Lec 4 "Optimise the acquisition"]); noisy E handled with the posterior mean as incumbent (noisy EI practice, Letham et al. 2019).
  If the service level can fail, multiply by the probability of feasibility from a second GP (EI × PF) [Lec 4 "Expected constrained improvement"].
- **Budget:** B = 40 [A §2.6], justified by hours per candidate with the real system [A §3.3]; 13 G seeds (one per k) and 27 picks by EI.
- **Random comparison:** same pool, same 13 seeds, 27 uniform random picks.
  Because development runs are free, I also evaluate the whole pool once (validation only, clearly labelled) and compute the exact distribution of best-of-random at every budget, so the comparison is a curve with a band, not one lucky run [IDEA; Lec 4 "Two representative BO applications": "give grid search, random search and BO the same initial observations and evaluation budget"].
- **Hand-over:** the recommendation is re-scored on 28 days and on 14 held-out days; "hand over arg max μ(x), not the luckiest noisy y" [Lec 4 "Answers - the objective sets how much to explore"].
- **Log:** one row per full evaluation: index, candidate id, sites, k, G0, G1, G2, E with components, service level, the rule that chose it (seed, EI value or random), wall time, run seed [A §3.3].
- Alternative (i), generator knobs (k, volume exponent, detour penalty, minimum spacing), goes into the approaches table as the considered alternative; Lec 4 "Wall 2" (10^d cells) explains why raw coordinates fail.

---

## 10. Demand under uncertainty (R2, 10 points)

### 10.1 Generator (the truth)

- Base rate per store: lognormal with mean 2.2, clipped to [0.5, 6] [A §2.6]; store type shifts the weekly pattern (office lower at weekends, residential higher).
- Calendar: weekday profile by store type; season with a summer peak (July-August, drinks and ice); real Korean public holidays of the history and planning years (Seollal, Chuseok, Children's Day, Christmas, New Year) with chain-wide spikes on the eves and drops for office stores.
- Chain-wide shocks: a daily lognormal AR(1) factor (weather, heatwaves, typhoon days) shared by all stores: the "chain moves together" source.
- Store churn: a few percent open or close per year, giving short histories [A §2.3].
- Counts: Poisson given the day's rate (optionally negative binomial for extra store-level noise).

### 10.2 Model (what the planner fits)

Lecture 2's Poisson-Gamma update with exposure [Lec 2 "Poisson-Gamma updating - counts and exposure add"; A R2]:

$$y_{s,t} \mid \lambda_s \sim \text{Poisson}(\lambda_s e_{s,t}),\qquad \lambda_s \sim \text{Gamma}(a_{\tau(s)}, b),\qquad \lambda_s \mid D \sim \text{Gamma}\Big(a + \sum_t y_{s,t},\; b + \sum_t e_{s,t}\Big)$$

- Exposure $e_{s,t}$ = calendar multiplier of the store's type (weekday × season × holiday), estimated once for the chain [A R2]; the chain shock of each history day is estimated from chain totals and divided out.
- Prior: type-specific mean from the chain; strength $b$ in store-days (for example 14) by empirical Bayes; show how a store with 20 days of history sits between prior and data [Lec 2 "The count estimate - interpret"].
- Posterior predictive for a planning day: negative binomial with mean $e\,a'/b'$ and variance $e\,a'/b' + e^2 a'/b'^2$ [Lec 2 "Backup - the Poisson-Gamma predictive distribution"].
- Sampling a planning day: draw a calendar day from the planning year, draw the chain shock from its fitted distribution, draw each $\lambda_s$ from its posterior, draw the counts.
- Posterior predictive check: replicate the history and compare chain totals, weekday profile and holiday peaks [Lec 2 "Backup - checking a fitted probability model"].

### 10.3 The sampled-day versus average-day analysis

| Comparison | Expected size | Why |
|---|---|---|
| Store noise only (sampled counts versus expected counts on the same calendar day) | Small | Independent store noise cancels at a DC of about 800 stores (sd of DC cages about one vehicle load) |
| Calendar (sampled calendar days versus one annual-average day) | Large | Weekday, season and holidays move the whole chain; the fleet quantile and spot hires respond non-linearly |
| Chain shocks (with versus without the AR(1) factor) | Medium | Correlated across stores, so it does not cancel |

Report all three, say why the first is small (law of large numbers; near-linear cost at DC level), and show the holiday-spike day as the case where it matters [A R2 and stuck table].
Thinning note: fewer stores per DC means relatively larger DC-level noise (by √(1/fraction)), so thinning also inflates this gap; another reason for full density.

---

## 11. G versus E (R3)

- Over every evaluated candidate: prediction quality = Spearman ρ, R² and RMSE of G against E (overall and within each k); decision quality = $E(\arg\min G) - \min E$ in KRW per month and percent.
- Decomposition with Lecture 5's signed decision bound, written for minimisation with $\hat x = \arg\min G$ and $x^\star = \arg\min E$ [Lec 5 "A good fit can still make a bad decision"]:

$$E(\hat x) - E(x^\star) = \underbrace{[E(\hat x) - G(\hat x)]}_{B:\ G \text{ under-rates its own pick}} + \underbrace{[G(\hat x) - G(x^\star)]}_{\le\, 0} + \underbrace{[G(x^\star) - E(x^\star)]}_{A}$$

- Name the cause in my world: expected to be the time window (G0 and G1 ignore the clock, so they under-rate big territories and favour fewer DCs), then the distance model (G0) and demand variability (fleet quantile) [INF from the pilot].
- Remedies, at least one applied and shown: system knowledge in G2 (window-aware stops per route, detour ratio) [A R3]; optionally a conservative correction (rescale by the observed E/G, or penalise features outside the evaluated range) [Lec 5 "Conservatism is a dial - make it a budget"].
- If the location gap is small, as the pilot found, show what cancels it (G1 and E agree on which sites serve dense clusters) and what would make it appear (a coarse distance model, or candidates across barriers).

---

## 12. Baseline, sweep, recommendation (R5)

- **Baseline:** 12 current DCs placed where a chain grown over decades would have them (capital region three or four, Chungcheong, Daegu, Busan-Gimhae, Ulsan-Pohang, Gwangju, Jeonju, Wonju, Changwon-Jinju), historical assignment, same E, same days, same routing [A §2.5, R5].
- **Saving decomposition** [IDEA]: baseline → same 12 re-assigned → best 12 sites → best k, each step with its paired saving and interval.
- **Sweep:** for each k in 8..20, the best evaluated candidate's total cost with its two components (fixed versus operating, operating split into vehicles, fuel, spot, penalties) and its service level.
- **Uncertainty:** paired saving over the 28 final days (bootstrap interval) and over 14 held-out days the search never saw; parameter uncertainty enters through posterior draws of $\lambda_s$.
- **Reversal:** one-way sweeps with break-even values: stop time 10-20 min, speed 30-45 km/h, DC fixed cost 100-200 M, distance model (map × factor versus OSRM), departure waves, demand growth ±10%, a spot-availability cap.
- **Payback** (CFO gap, Section 22): monthly saving against one-off transition costs (lease exit, relocation) as a stated sensitivity, because the base design treats all sites as free [A §2.2].
- **Store fairness** (franchise-owner gap): per-store on-time share and the worst store's share, not only the network level.

Hypothesis to test, not a result: the sweep is U-shaped with a minimum near 10-12; "eight" loses because vehicles rise; G0 and G1 pick fewer DCs than E.

---

## 13. Fidelity-computation balance table (draft rows and planned checks)

| Modelling choice | Real operation | What I model | Compute cost | What it could get wrong | Planned check |
|---|---|---|---|---|---|
| Instance scale | 10,000 stores | All 10,000 stores (no thinning) | Neighbour-list routing; about 1.4 M cached pairs | Nothing from thinning; heavier runs | Measure what thinning would have done: 1-in-5 (i) and (ii) against full, on the sweep and the top-3 ranking |
| Distance model | Road network; time varies by hour | OSRM road distance for DC-store and nearest-store pairs; calibrated detour model for the rest; time = d/35 + 15 min | One-off OSRM table queries on the DGX; cache about 15 MB | Peak-hour slowdowns ignored; fallback pairs approximate | Re-run top candidates with all-pairs OSRM inside their territories and with 30 km/h |
| Demand model and days | Store demand with calendar and shocks | Poisson-Gamma with exposure, chain shocks, 7 search days, 28 final, 14 held-out | 28 days cost 4 times 7 | A quantile from 7 days is noisy; ranks may flip | Rank stability of the top 10 between 7 and 28 days |
| Routing method | Experience routes | Savings + local search, deterministic | About 0.5 s per DC-day | Heuristic gap may grow with territory size | Gap against PyVRP by k; exact on small instances |
| Delivery window | ≥ 98% before noon, failure after 14:00 | Hard 12:00 for every stop | Feasibility checks per merge | Slightly over-states vehicles (2% slack unused) | Deadline 12:30 for all; does k* change |
| Departure and docks | Waves 04:00-07:00 by dock capacity | All depart 04:00 | None | Flatters big DCs, so it favours fewer DCs: the decision itself | **Required check:** departure waves by dock throughput; does k* change |
| Assignment | Historical territories | Window-aware transportation LP inside E | One LP per evaluation | Distance-optimal is not route-optimal | Two assignment rules on the top candidates |
| Fleet policy | Contracts | 0.671 quantile over sampled days, spot above | Free | Unlimited spot supply assumed | Spot cap at 20% of the owned fleet |
| Candidate set | Real-estate options | About 60 sites near motorway interchanges and logistics zones, incl. the current 12 | Pool size | The optimum may lie off the list | Add 10 sites in the gaps; does the best per k move |
| Number of DCs swept | 8-20 feasible | 8..20 | 13 seeds of the budget | None | Complete |
| Search and budget | Hours per evaluation | Pool + K&O GP + EI, B = 40 | 40 E calls | Misses the pool optimum | Exhaustive pool evaluation (validation) and the random band |

Required argument after the table: where computation was spent (lower-level fidelity and full density, because the window mechanism lives there), which simplification to remove first (time-of-day speeds), and at least two checks with whether k* or the top-3 ranking changed [A §3.4].

---

## 14. The world I generate (§2.5 tables)

| Table | Generation | Real-world property |
|---|---|---|
| `stores` | 10,000 points sampled in proportion to population on a fine grid (Kontur population on H3, CC BY 4.0) [DECIDE: or OSM `shop=convenience` points], snapped to the road network; region from geoBoundaries ADM1/ADM2 [verify licences]; type from local density and motorway proximity; open and close dates for churn | Density follows people; roadside stores near motorways |
| `demand_history` | Section 10.1, 12 months, fixed seed | Weekday, season, holidays, shocks, short histories |
| `dcs` | 12 plausible sites (Section 12), lease expiries spread over 2027-2031, fixed cost by region | A chain grown over decades |
| `candidate_sites` | About 60 sites at motorway junctions near industrial or logistics land use (OSM), capital-region premium on fixed cost, current 12 included | Leasable logistics land |
| `cost_parameters` | Teaching defaults [A §2.6] | Finance figures |
| `deliveries`, `vehicle_days`, `spot_hires` | Produced by running my lower level on the baseline over the 12-month history, labelled as such [A §2.5] | Baseline service level, fleet, km and spot cost |

Distances: OSRM self-hosted on the DGX from the Geofabrik `south-korea-latest.osm.pbf` extract, car profile (distances only; times from distance and the stated speed) [A §2.5]; version, extract date and profile recorded; a calibration sample of about 500 pairs gives the detour model and its error.
[RISK] I could not confirm an arm64 build of `ghcr.io/project-osrm/osrm-backend`; check with `docker manifest inspect` on the DGX, or build from source.

---

## 15. Lecture tool map

| Lecture | Tool | Where used |
|---|---|---|
| 0 | Two uncertainties (aleatoric versus epistemic); OI Factory gates | Demand noise versus rate uncertainty; "the next role can act" as the definition's standard |
| 1 | Standard form; convexity watershed; LP family; KKT and duality certificates; epigraph; chance constraint convex for η ≥ 1/2; bilevel "evaluate a layout through its best operation"; "a poor controller should not make a useful design look bad"; "compare surrogates with the same optimiser"; "Formulation is a balance" | All three levels; transportation LP duals; service level as a chance constraint; fair baseline; the balance table |
| 2 | Poisson-Gamma with exposure; posterior predictive (negative binomial); prior strength; rate uncertainty versus count noise; predictive checks | R2 |
| 3 | Value of information [Lec 3 "The value of information"] | Bonus: measuring road times versus collecting more demand history |
| 4 | GP, marginal likelihood, ARD; EI, PI, UCB; acquisition on a pool; constrained EI × PF; same-budget comparison with random search; Wall 2 | R4 |
| 5 | Prediction versus decision quality; signed decision bound; conservatism as a budget; μ − κσ offline; ensembles extrapolate together; Kennedy and O'Hagan discrepancy; system knowledge | R3 and the surrogate |
| 6 | CbAS-style adaptive generator, conditioning on success | Bonus: candidate generation |

Methods outside the lectures, named and cited where used (as A1 did for the simplex): Clarke-Wright savings, local-search moves, p-median and capacitated facility location, continuous approximation of route length, sample average approximation, common random numbers, newsvendor fractile, OSRM, H3.

---

## 16. Best practice from industry and research

Adoption rule (user instruction): lecture tools first; external engines, APIs, agents or LLMs only with a proven large gain.

| Topic | Practice and source | How it shapes the plan | Adopt? |
|---|---|---|---|
| Network design with routing | Location-routing surveys (Prodhon and Prins 2014; Schneider and Drexl 2017); La Poste multi-echelon design with continuous approximation (Winkenbach, Kleindorfer and Spinler 2016) | Continuous approximation inside G, full routing inside E: the industry pattern for strategic design | Yes (G2) |
| Continuous approximation | Daganzo 1984; Beardwood, Halton and Hammersley 1959; review by Franceschetti, Jabali and Laporte 2017 | Route-length formula and constants; the √(thinning) distortion argument | Yes |
| Aggregation error | Francis, Lowe, Rayco and Tamir 2009 survey | Thinning and stop aggregation are aggregation error: measure it | Yes (check) |
| VRP heuristics | Clarke and Wright 1964; Vidal 2022 HGS-CVRP; PyVRP (Wouda, Lan and Kool 2024) | Own savings + local search inside E for speed; PyVRP as the accuracy reference | Benchmark only, unless its gap exceeds about 5% and changes the ranking |
| Stochastic network design | Sample average approximation (Kleywegt, Shapiro and Homem-de-Mello 2002); supply chain design under uncertainty (Santoso et al. 2005) | E as SAA over sampled days with common random numbers | Yes |
| Noisy constrained BO | Letham, Karrer, Ottoni and Bakshy 2019 (Meta, noisy EI); BoTorch (Balandat et al. 2020); Google Vizier (Golovin et al. 2017) | Posterior-mean incumbent, logging discipline, same-budget baselines | Ideas yes; libraries no (an own GP is lecture-faithful and small) |
| Multi-fidelity | Kennedy and O'Hagan 2000 (autoregressive co-kriging), the origin of Lec 5's discrepancy idea | G as low fidelity, E as high fidelity | Yes (discrepancy GP) |
| Retail count demand | M5 competition on Walmart data (Makridakis, Spiliotis and Assimakopoulos 2022); DeepAR negative-binomial likelihood (Salinas et al. 2020, Amazon); Prophet holidays and seasonality (Taylor and Letham 2018, Meta) | A negative-binomial predictive with explicit holiday multipliers is standard and matches Poisson-Gamma | Yes (ideas) |
| Spatial indexing | H3 hexagonal grid (Uber) | Store aggregation for G's MILP; density features | Yes (library) |
| Last-mile realism | Amazon Last Mile Routing Research Challenge (Merchán, Winkenbach et al. 2024) | Driver experience routes differ from optimised routes: keep current practice apart from the constructed baseline | Mention |
| Learned solvers and LLM agents | Neural combinatorial optimisation (Kool, van Hoof and Welling 2019, in Lec 0); LLM formulator and analyzer pattern (Lec 0 OCP) | No proven gain for a one-off strategic study of this size | No; future work only |

[RISK] Verify every citation's bibliographic details before it enters `problem-definition.md` (use the citation-check skill, Section 17.5); the list above is from memory.

---

## 17. Architecture

### 17.1 Repository layout (everything in `Distribution-Centre-Network`)

```text
Distribution-Centre-Network/          private until after 2 Nov
  assignment.md, problem-definition-template.md, ...   the brief (reference, not shipped)
  planning/                         this brain, its HTML, stakeholders/, review records (never shipped)
  problem-definition.md             deliverable
  proposal.html                     deliverable (built from code/results)
  demo.html                         deliverable: static snapshot [DECIDE]
  code/                             deliverable
    README.md                       three commands, run times, seed, distance source, what reduced omits
    requirements.txt
    run_full.py                     everything, writes results/ and the numbers registry
    run_reduced.py                  same pipeline, smaller budget and fewer days, minutes
    app.py                          local demo server (localhost only)
    dcn/
      config.py                     teaching defaults, seeds
      world.py                      stores, dcs, sites, calendar, demand history
      distances.py                  cache loader, detour model, calibration
      demand.py                     Poisson-Gamma with exposure, predictive sampler
      routing.py                    savings + local search (numba), exact small MIP, PyVRP benchmark
      evaluate.py                   assignment LP, fleet quantile, E with common random numbers
      search.py                     G0, G1, G2, pool, features, GP, EI, random, log
      analysis.py                   sweep, R2 gaps, R3 bound, checks, reversal, held-out
      numbers.py                    one registry of every reported number
    data/                           world inputs, OSRM cache, road geometry for demo DCs
    results/                        logs, tables, registry JSON
    static/                         demo front end (vendored JS, no CDN)
  tools/
    osrm/                           DGX-only scripts that rebuild the cache (shipped for transparency, not needed to run)
    make_zip.py                     builds 20264059_LouisWellmeyer.zip from an allowlist
```

Code rules (user instruction): comments terse and direct ("Compute fleet quantile per DC"), no filler, no over-commenting, one-sentence docstrings saying what and how to run; no argparse (settings in `config.py`); minimal tests (the analysis checks are the tests); deterministic seeds; Python 3.10 syntax only; no network at runtime.

### 17.2 Compute plan

- Laptop: editing, the toy instance, docs, front end; no long runs (it hard-resets under load).
- DGX Spark: OSRM build and table queries, full world generation, outcome tables over 12 months, development runs, exhaustive pool validation, the reported search, the checks.
- I prepare exact commands; the user runs them on the DGX (`ssh spark`) and copies results back with `scp` [DECIDE].

### 17.3 Demo: local app with a Python backend, plus a static snapshot

- One command from `code/`: `python app.py` serves `http://localhost:8437` and calls the same `routing.py` for live solves (same rules as the code, as the brief asks [A §6.3]).
- Map without tiles: Korea outline and provinces (geoBoundaries), motorways from OSM as lines, stores as points, DCs as icons, territories as hulls; deck.gl and the chart library vendored locally.
- Hero view: a delivery day animated on a clock from 04:00 to 14:00; trucks move along cached road geometry, stores light up when served, late stops flash; a Gantt of vehicles underneath.
- Live lower level for one DC: day (ordinary, summer, holiday), deadline, stop time, speed, capacity, maximum stops, departure; KPI tiles and the binding-constraint census update.
- Network views: baseline against recommended side by side; the sweep with its components; the search replay (each evaluation appears on the map, the G-vs-E scatter grows, the EI ranking is visible); the random band.
- Cases: normal (recommended network, ordinary day); boundary (a DC at 1,400 stores; a budget of one evaluation); failure (k = 7 infeasible with the reason; a holiday day under a spot cap where the fleet cannot cover, explained, nothing shown as valid).
- Every precomputed number carries a badge "precomputed · `python run_full.py`"; live numbers carry "live".
- Static `demo.html` snapshot: all precomputed views with the live solve replaced by recorded solves and a note [DECIDE].

### 17.4 Proposal

8-12 slides in the same design system, numbers from the registry; slide 2 answers "how many, where, how sure"; the proof runs through the sweep, the saving decomposition, held-out days and reversal thresholds; fictional demonstrated results kept apart from effects that need real data [A §6.4].

### 17.5 Skills and agents plan (ECC and the other installed skills)

Each skill is used for the step it fits; agents run only when you ask for them.

| Phase | Skill or agent | Use |
|---|---|---|
| Planning and decisions | `ecc:plan`, `ecc:blueprint` | Turn this brain into an ordered build plan per day |
| Planning and decisions | `ecc:architecture-decision-records` | One ADR per decision of Section 23; ADRs feed the LLM review records of definition §7 |
| Stakeholder reviews | `ecc:council`, `ecc:santa-method` | Structured multi-perspective verification using the personas in `planning/stakeholders/` |
| Stakeholder reviews | `ecc:team-agent-orchestration` or `ecc:dmux-workflows` | Run each persona as an independent agent for review rounds 2 and 3 (on request) |
| Product framing | `ecc:product-lens`, `ecc:plan-prd` | Demo and proposal requirements from the analyst's and management's view |
| Research | `ecc:search-first`, `ecc:deep-research`, `ecc:scientific-thinking-literature-review` | Check the best-practice table, find retail and convenience-logistics papers |
| Citations | `academic-research-skills:academic-paper` (citation-check mode) | Verify every reference before submission |
| Domain realism | `ecc:inventory-demand-planning`, `ecc:logistics-exception-management`, `ecc:carrier-relationship-management`, `ecc:returns-reverse-logistics` | Sanity of demand patterns, spot-truck market, failure handling, empties |
| Infrastructure | `ecc:docker-patterns` | OSRM on the DGX |
| Implementation | `ecc:python-patterns`, `ecc:coding-standards` | Idiomatic, plain code |
| Speed | `ecc:performance-optimizer` (agent), `ecc:benchmark`, `ecc:benchmark-methodology` | numba routing to the 0.5 s target; heuristic against PyVRP timing and gap |
| Review | `code-review`, `ecc:python-review`, `ecc:silent-failure-hunter` (agent), `simplify` | Correctness, silent feasibility failures, removing over-engineering |
| Verification | `ecc:verification-loop`, `ecc:quality-gate`, `ecc:delivery-gate` | Gates on days 4, 9 and 13; final pre-submission gate |
| Front end | `ecc:frontend-design-direction`, `ecc:design-system`, `ecc:taste`, `ecc:make-interfaces-feel-better` | CU-inspired design language and polish |
| Motion | `ecc:motion-foundations`, `ecc:motion-patterns` | Truck animation, clock, transitions |
| Charts | `dataviz` | Sweep, G-vs-E scatter, random band, cost components |
| Accessibility | `ecc:accessibility`, `ecc:frontend-a11y` | Contrast of purple and green, colour-blind safe states |
| Browser checks | `ecc:browser-qa`, `ecc:e2e-testing`, `ecc:e2e-runner` (agent), `ecc:click-path-audit` | Offline checks of the app and the snapshot, like A1's `verify.py` |
| Design loop | `ecc:gan-design` | Generator and evaluator iterations on the hero view |
| Proposal | `ecc:frontend-slides` | HTML deck |
| Walkthrough video (optional, as in A1) | `demo-video`, `ecc:remotion-video-creation` | Pitch video |
| Oral-exam preparation | `ecc:code-tour`, `interactive-study-guide` | Walk through every module; a study guide of the methods for questioning |
| Session continuity | `ecc:save-session`, `ecc:resume-session`, `ecc:checkpoint`, `ecc:strategic-compact` | Fourteen days of work across sessions |
| Git | `ecc:git-workflow`, `no-mistakes`, `gh-axi` | Commits and pushes to the private repo |

---

## 18. Design system (CU-inspired, for the fictional Dasol Retail)

| Token | Value | Source |
|---|---|---|
| Primary purple | `#751485` (RGB 117, 20, 133; Pantone 267C) | CU brand story page |
| Primary green | `#9DC92A` (RGB 157, 201, 42; Pantone 368C) | CU brand story page |
| Logo-file purple and green | `#652D8D` and `#AACE37` | Unofficial lookbook (oppadu), values from CU files |
| Neutrals | `#FFFFFF`, `#F0F0F0`, `#DDDDDD`, `#787878`, `#555555`, `#222222` | Lookbook, from CU web CSS |
| Sub colours | CU Lime, Dark Beige, Gray, Light Beige (names only; no values published) | CU brand story page; values to derive |
| Type | Noto Sans KR for text, Roboto for numbers | Lookbook, from CU web CSS |
| Shape | Rounded cards 16 px, pill badges and filters, near-flat surfaces | Lookbook |
| Icons | Outline, 1.7-2 px stroke, round caps | Lookbook (estimated) |
| Motion | Subtle; hover scale 1.1 over 0.34 s; off under reduced motion | Lookbook |
| Voice | Friendly, bright, practical; slogan "Fresh & Refresh" | CU brand story page |

The Behance case study refused automated access (HTTP 403); open it by hand for layout and signage references.
[RISK] Dasol Retail is fictional and must stay fictional: use the palette, type and shape language, never the CU name, logo or "Nice to" bubble; add the line "visual style inspired by public brand colours; company and data are fictional".
[RISK] Purple on green fails contrast for text; use purple text on white or white text on purple, keep green for accents and states, and add shapes as well as colour for colour-blind readers.

---

## 19. Bonus plan (up to 10, recorded separately)

1. **Value of information (Lec 3):** decide with the detour model versus OSRM, and with 3 versus 12 months of history; VOI = expected E loss avoided by the better information; uses the existing pipeline.
2. **Robustness:** a demand regime shift (±10% growth, office decline) and a distance-source swap; does k* move.
3. **Closure sequence:** use `lease_expires_on` to show whether moving from 12 to k* in lease order costs much against a one-shot change (a small DP over closure order, making D1 Stateful).
4. Candidate generation (Lec 6, CbAS-style adaptive Bernoulli over sites) only if time remains.

---

## 20. Schedule (14 days; brief: 40-60 h; day-7 self-check)

| Day | Date | Work | Gate |
|---|---|---|---|
| 0 | Mon 19 Oct | This plan, stakeholder review, user decisions | Decisions answered |
| 1 | Tue 20 | Repo skeleton; toy (300 stores, 2 DCs, map distances); savings v0; E on the toy baseline; DGX: OSRM build | Toy E runs |
| 2 | Wed 21 | Stores, DCs, sites; OSRM cache; demand history; Poisson-Gamma fit | Distances cached |
| 3 | Thu 22 | Routing v1 (all limits, local search, numba); exact and PyVRP accuracy; timing | ≤ 0.5 s per DC-day, else step down the scale ladder |
| 4 | Fri 23 | Connection: days, common random numbers, fleet quantile (with the vehicle-need regression), assignment LP; outcome tables; results-registry schema; stakeholder review 02 | E on the full baseline (toy end to end by day 3-4, as the brief asks) |
| 5 | Sat 24 | G0, G1 (MILP), G2; pool; features; sweep seeds and k pruning bound; demo scaffold on mock registry data | Pool built |
| 6 | Sun 25 | GP discrepancy, EI, random, log; development runs; reduced-run fidelity test | Search works; reduced run keeps the sweep's shape |
| 7 | Mon 26 | The brief's self-check; definition §1-3 drafted; R2 three-way gap | Self-check passed or scope cut |
| 8 | Tue 27 | R3 bound and remedy; balance-table checks | Two checks done |
| 9 | Wed 28 | Reported fresh run B = 40; 28 + 14 days; decomposition; reversal | All numbers frozen in the registry |
| 10 | Thu 29 | Demo back end, map, animation, live solve | Live solve works offline |
| 11 | Fri 30 | Demo cases and polish; proposal | Both front ends done |
| 12 | Sat 31 | Full definition; LLM review records; numbers consistency | Definition complete |
| 13 | Sun 1 Nov | Fresh-environment reproduction (three commands, offline); reduced-run timing; ZIP ≤ 200 MB; rubric and hidden-point pass; bonus | ZIP built |
| 14 | Mon 2 Nov | Submit before 10:00 | Submitted |

Scale ladder if routing is too slow on day 3: full density → 1-in-2 thinning → 1-in-5 with aggregated stops (option ii); never option (i) without the measured distortion.

---

## 21. Compliance matrix (the grader's twelve things)

| # | The grader looks for | Where it will be |
|---|---|---|
| 1 | Four statements, each placed at a level | Definition §1 (Section 5 here) |
| 2 | Every decision with dependencies and `evaluated_by` | Definition §1 (Section 6) |
| 3 | Lower level in standard form, method, cost per solve, measured accuracy | Definition §2a and §4 (Section 7) |
| 4 | Connection, with the assignment's place stated | Definition §2b (Section 8) |
| 5 | Upper level with G, B, rule, log, random comparison | Definition §2c, §4, §5 (Section 9) |
| 6 | Balance table with two checks | Definition §4 (Section 13) |
| 7 | Demand model driving sampled-day evaluation | Definition §3 (Section 10) |
| 8 | G-vs-E gap measured and explained | Definition §4 and §5 (Section 11) |
| 9 | Baseline under identical conditions | Definition §5 (Section 12) |
| 10 | Number-of-DCs sweep | Definition §5 and the demo |
| 11 | Recommendation with uncertainty and reversal assumptions | Definition §6 and the proposal |
| 12 | Three LLM discussions with checks | Definition §7 |

Planned LLM discussions (the real ones will replace these): (1) where the assignment lives, checked by evaluating both placements on the top candidates; (2) whether thinning is acceptable, checked by the measured distortion; (3) an LLM claim that the centre of gravity is optimal, rejected by the Weber-versus-squared-distance argument and by E.

---

## 22. Stakeholder review round 1 (role-played discussion of plan v1.0)

The personas live in `planning/stakeholders/`, one README each with personality, priorities, questions and red flags.
The transcript is `planning/stakeholders/REVIEW-01-plan-v1.md`; the changes it caused are already in this version (v1.1).

| Persona | Gap found in v1.0 | Change in v1.1 |
|---|---|---|
| Examiner | Full-scale ambition could eat the time the formulation needs | Scale ladder with a day-3 speed gate; definition drafting starts on day 7, not day 12 |
| Examiner | Re-solving the assignment by a distance LP lets a proxy into E | Window-aware cost-to-serve in the LP and a check comparing two assignment rules |
| TA / reproducer | PyVRP and numba must install on an unknown laptop; reduced-run time unknown | Pinned versions, a fresh-venv test on day 13, PyVRP only in the full run |
| CEO | No single slide answers both questions | Proposal slide 2 answers "how many, where, how sure" |
| CFO | The saving ignores one-off transition costs | Payback sensitivity (Section 12) |
| Strategy & Planning | k = 8 might be under-searched and look like a strawman | Every k gets a G seed and can receive EI picks; best-of-8 shown explicitly |
| Delivery Operations | Docks, traffic and breaks missing | Departure-wave and 30 km/h checks; breaks as a stated assumption |
| Data Team | The centre of gravity is not given a fair shot under E | G0 evaluated under E as the proxy-only approach |
| Field Manager | The river claim needs concrete examples | A detour-ratio map layer and named examples in the demo |
| Real estate and leases | Lease timing ignored | Lease expiries in `dcs`; closure sequence as a bonus |
| Franchise store owner | 98% at network level can hide one store that is late every day | Per-store on-time distribution and worst-store share |
| Project manager | No go/no-go points, no cut list | Gates in Section 20; cut list in Section 24 |
| Product manager | Demo user and first screen undefined | Hero view and operator flow (17.3) |
| Lead developer | Numbers could drift between files | One registry read by the definition, demo and proposal |
| OR scientist | The heuristic gap may depend on k and bias the sweep | Gap-versus-k analysis (7.3) |
| Bayesian statistician | Calendar multipliers treated as known; no predictive check | State that their estimation error is small at chain level; add the predictive check |
| UX and brand designer | CU look-alike risk; contrast | Section 18 rules |
| Red team | The saving could be an artefact of the historical assignment I invented | Saving decomposition and a plausible history rule (nearest DC at each store's opening year, never rebalanced) whose badness is measured |
| Delivery Operations (blocker) | All vehicles leaving at 04:00 flatters big DCs, which favours fewer DCs | The departure-wave check is promoted to one of the two required balance-table checks |

**Still open after round 1** (owner, due gate; full list in the review file):

| # | Open item | Owner | Due |
|---|---|---|---|
| 3 | Prune k values with a certified lower bound (fixed cost plus a vehicle lower bound already above the best E) so 13 seeds do not eat a third of B | Examiner | Day 5 |
| 6 | Test whether the reduced run reproduces the sweep's shape, the baseline comparison and the G-vs-E gap | TA | Day 6 |
| 11 | Regional rents around the 150 M mean as a stated rule, plus a uniform-150 M comparability check | CFO | Day 2 |
| 19 | Results-registry schema fixed on day 4; demo built against mock data from day 5 | Project manager | Day 4 |
| 23 | Fleet quantile from 7 days is the 5th order statistic: fit vehicle need on the solved days, take the quantile over many cheap simulated days, check against 28 days | OR scientist | Day 4 |
| 24 | Mild misspecification in the generated truth so the predictive check means something | Statistician | Day 2 |
| 27 | Regenerate the world with two more seeds; do k* and the sign of the saving hold | Red team | Day 9 |
| 9, 15, 16, 20, 21, 22, 25, 7 | Measurements to request first; distinct-site snapping for G0; car-profile assumption; user stories; offline fonts; TU wording; derived sub-colours; port fallback | Various | Days 2-12 |

---

## 23. Decisions for the user

1. **Instance scale:** full 10,000 stores (recommended) or thinned from the start.
2. **Static snapshot:** ship a static `demo.html` next to the local app (recommended) or the app only.
3. **Store locations:** population-weighted (Kontur H3, recommended, complete) or OSM convenience-store points (realistic, possibly patchy).
4. **Brand use:** CU palette and type for the fictional Dasol (recommended) or literal CU branding (not recommended).
5. **Bonus scope:** VOI and robustness (recommended), plus the closure sequence if time allows.
6. **Who runs the DGX:** I prepare commands and you run them (as for TinyShop), or you give me a way to run them.

---

## 24. Flags, risks and gotchas

- [RISK] The brief may change again; pull `ie437` daily and diff `teaching/midterm-depot-network/student/`.
- [RISK] Keep `Wellbek/Distribution-Centre-Network` private until after 2 Nov; this is an individual exam.
- [RISK] Do not cite instructor-only material (the A1 grading guide, README notes) in the submission; every argument must follow from the public brief and our own measurements.
- [RISK] "You may be asked to explain any part of your code or design" [A §8]: keep the code readable and walk through it before submission (code tour).
- [RISK] No em dashes in any deliverable; the brief uses them, so never paste its text.
- [RISK] One sentence per line in long Markdown, including `problem-definition.md`.
- [RISK] Keep the template's seven headings verbatim [A §6.1].
- [RISK] Mark `[ASSUMPTION]`, `TBD`, `N/A - reason` [A §6.1]; compare baseline, proxy-only and the selected approach [T §4].
- [RISK] Never describe an unimplemented feature or an untested saving as achieved [A §5].
- [RISK] Call the reported search one fresh run of exactly 40 including the seeds; keep development runs out of the reported log [A §3.3].
- [RISK] State OSRM's source, version, extract date and profile; cache every distance; the grader runs offline.
- [RISK] ZIP size: distance cache, vendored JS and road geometry must stay well under 200 MB; `planning/` and the brief files are excluded by the allowlist.
- [RISK] The laptop crashes under load: no long runs locally.
- Cut list if behind on day 7: closure-sequence bonus → exhaustive pool validation (keep one random run) → static snapshot → extra thinning levels (keep one) → search-replay animation.

---

## 25. Rolling records (user instruction)

Two append-only files in `planning/`, updated in the same session as the work they describe, every day:

| File | What goes in | Feeds |
|---|---|---|
| `LLM_USE.md` | Every task an LLM or agent did: context search, research, guardrails, role assumption, coding, review, drafting; the skill or agent used; why; how I checked it; where the result went | The definition's header line "LLM tools and use" and Section 7 (three discussions, at least one checked by calculation or experiment [A §8]) |
| `DECISIONS.md` | Every decision with alternatives, reason, evidence and status (proposed, accepted, superseded, rejected), including the "we realised X was inefficient, so we did Y" moments | The balance table's reasoning, the approaches table, Section 7, and an ADR for each major decision |

Rules: a row is added when the event happens, never reconstructed at the end; a reversed decision gets a new row pointing back; both files stay out of the ZIP, and the definition quotes only what it needs.
