# Review 01 · The plan (MIDTERM_BRAIN v1.0 → v1.1)

Date: 2026-10-19 (day 0).
Artefact: `planning/MIDTERM_BRAIN.md` v1.0 (before this review); the applied changes produced v1.1.
Mode: inline role-play, one persona at a time from its README, then a round table.
Severity: **B** blocker, **M** major, **m** minor.

---

## 1. Independent passes

### 01 Examiner

1. **M** Full density is ambitious; if routing is slow, the formulation sections get written in a hurry on day 12. Fix: a day-3 speed gate with a scale ladder, and definition drafting from day 7. *(Applied.)*
2. **M** Re-solving the assignment by a pure distance LP puts a proxy inside E; the assignment then optimises G's criterion. Fix: a window-aware cost-to-serve in the LP, and a check with a second assignment rule on the top candidates. *(Applied.)*
3. **M** Thirteen G seeds (k = 8..20) spend a third of B before the rule chooses anything. Fix: prune k values with a certified lower bound (fixed cost plus a vehicle lower bound already exceeds the best E found), and say so in the log. *(Open, Section 3 below.)*
4. **m** "Exhaustive pool evaluation" may read as ignoring the brief's "treat E as expensive". Fix: run it after the reported search, label it as validation of the method, never feed it back. *(Applied in the label; keep watching.)*
5. Good: the four statements analysis and the convexity link (centre of gravity is convex only under map distance) is exactly the kind of lecture use I reward.

### 02 TA reproducer

1. **M** PyVRP and numba must install from wheels on Windows and macOS for Python 3.10-3.12. Fix: pin versions, test a fresh venv on day 13, keep PyVRP out of the reduced run. *(Applied.)*
2. **M** Nobody has measured whether the reduced run reproduces the sweep's shape. Fix: test the reduced configuration on day 6, not day 13. *(Open.)*
3. **m** The demo port can collide with another service. Fix: fall back to the next free port and print the URL. *(Open, minor.)*

### 03 CEO

1. **M** No slide answers both questions at once. Fix: slide 2 "how many, where, how sure". *(Applied.)*
2. **m** "What to measure first with real data" is not concrete. Fix: name the three measurements with the largest reversal leverage (stop time, morning speed, real territories) and tie them to the VOI bonus. *(Open.)*

### 04 CFO

1. **M** The saving ignores one-off transition costs. Fix: payback sensitivity. *(Applied.)*
2. **M** Regional rents for candidate sites conflict with the single 150 M default; numbers stop being comparable across students. Fix: state the rule (national mean 150 M, capital-region premium) as an assumption, and report a uniform-150 M check. *(Open.)*
3. **m** Interval wording: say "paired, over days" every time. *(Applied in Section 12.)*

### 05 Head of Strategy & Planning

1. **M** k = 8 could be searched less than the others and look like a strawman. Fix: every k gets a seed; report evaluations per k; show the best eight-DC network. *(Applied.)*
2. **m** Break-even stop time and speed at which eight would win. *(Applied in the reversal list.)*

### 06 Head of Delivery Operations

1. **B** All vehicles leaving at 04:00 flatters large DCs, which favours fewer DCs, which is exactly the decision. Fix: the departure-wave check is mandatory, not optional. *(Applied as a balance-table row; promoted to one of the two required checks.)*
2. **M** Spot trucks unlimited. Fix: spot cap scenario and the failure case. *(Applied.)*
3. **m** Driver breaks and empties: stated assumptions. *(Applied.)*

### 07 Data Team lead

1. **M** My method must be evaluated under E for every k. *(Applied.)*
2. **m** Snapping k centroids to the nearest candidate site can produce duplicates. Fix: assign centroids to distinct sites by a small assignment problem. *(Open, minor.)*

### 08 DC field manager

1. **M** Concrete river and mountain examples. Fix: detour-ratio layer and three named examples. *(Applied.)*
2. **m** OSRM's car profile uses roads trucks avoid. Fix: state it as an assumption; note it biases distances slightly low. *(Open, wording.)*

### 09 Real estate and leases

1. **M** Lease timing absent. Fix: `lease_expires_on` used in the discussion; closure sequence as bonus. *(Applied.)*

### 10 Franchise store owner

1. **M** Network-level 98% hides chronically late stores. Fix: per-store on-time distribution, worst-store share, stores that change DC. *(Applied.)*

### 11 Project manager

1. **M** No gates, no cut list. *(Applied.)*
2. **M** The demo is scheduled after the results freeze, but the user wants a very visual demo; it will be squeezed. Fix: define the results-registry schema on day 4 and build the demo against mock data from day 5 in parallel. *(Open.)*
3. **m** No slot for a brief update from the instructor. Fix: daily pull and diff; half a day of buffer on day 13. *(Applied.)*

### 12 Product manager

1. **M** Demo users and first screen were undefined. *(Applied: hero view and operator flow.)*
2. **m** Write the two user stories before building. *(Open.)*

### 13 Lead developer

1. **M** Numbers could drift between files. Fix: one registry and a consistency check. *(Applied.)*
2. **m** Fonts must be vendored (Noto Sans KR, Roboto, both OFL) and subset, since the demo runs offline. *(Open.)*

### 14 OR scientist

1. **M** The heuristic's gap may depend on k. Fix: gap against PyVRP by k. *(Applied.)*
2. **m** The transportation LP stays totally unimodular only because the DC bounds count stores, not cages; say so, because a cage-based bound would break integrality. *(Open, wording.)*
3. **M** A 0.67 quantile from 7 sampled days is the 5th order statistic: very noisy. Fix: fit vehicle need against DC cages and the window-binding share on the 7 solved days, then take the quantile over many cheaply simulated days (a control-variate style shortcut), and check it against the 28-day quantile. *(Open.)*

### 15 Bayesian statistician

1. **M** If the generator and the model are the same family, the predictive check is trivially passed. Fix: put mild misspecification into the truth (negative-binomial store noise, type-specific seasonality) and show the check still holds or say where it fails. *(Open.)*
2. **m** Calendar multipliers treated as known. Fix: say their standard error is negligible at chain level and show one number. *(Applied.)*

### 16 UX and brand designer

1. **M** CU look-alike risk; contrast of purple and green. *(Applied: Section 18 rules.)*
2. **m** Sub-colour values unknown. Fix: derive lime, beige and grey tints and document them as derived. *(Open.)*

### 17 Red team

1. **B** The saving can be manufactured by generating a bad historical assignment. Fix: saving decomposition, and generate the history by a plausible rule (nearest DC at each store's opening year, never rebalanced) whose badness is measured and stated. *(Applied.)*
2. **M** One world seed. Fix: regenerate the world with two other seeds and check that k* and the sign of the saving hold, at least under G2 and a short E. *(Open.)*
3. **m** Proposal claims must trace to registry numbers. *(Applied through the registry.)*

---

## 2. Round table

- **Examiner vs Product manager and UX designer** on where effort goes.
  Examiner: 85 points sit in the definition. Product manager: the user explicitly wants a very visual demo.
  Resolution: both, by decoupling. The registry schema is fixed on day 4, the demo is built against mock data from day 5, real numbers drop in after the day-9 freeze; definition gates have priority on any day they conflict.
- **OR scientist vs Lead developer** on PyVRP.
  OR scientist wants a strong reference; Lead developer wants a light install.
  Resolution: PyVRP pinned, used only in the full run's accuracy step; the reduced run skips it and says so.
- **Strategy & Planning vs Delivery Operations** on departure times.
  Both agree the departure-wave check decides who is right; it becomes one of the two required checks.
- **Red team vs Examiner** on exhaustive pool evaluation.
  Red team wants ground truth; Examiner warns about the "treat E as expensive" framing.
  Resolution: run it after the reported search, as a validation of the selection rule, clearly separated in the log and the text.
- **CFO vs Real estate** on rents.
  Resolution: regional rents as a stated rule around the 150 M mean, uniform 150 M as a comparability check.
- **Data Team vs Field manager**: agree that G0 stays the map-based centre of gravity (the claim as stated), and G1 is its road-distance correction; both are evaluated under E.

---

## 3. Gap list

| # | Gap | Owner | Sev. | Decision | Status |
|---|---|---|---|---|---|
| 1 | Speed gate and scale ladder | Examiner | M | Day-3 gate | Applied |
| 2 | Proxy inside E through the assignment | Examiner | M | Window-aware LP + second rule check | Applied |
| 3 | Thirteen seeds consume a third of B | Examiner | M | Certified lower-bound pruning of k | Open, day 5 |
| 4 | Exhaustive pool evaluation framing | Examiner | m | Validation only, after the reported run | Applied |
| 5 | Wheels and versions | TA | M | Pin, fresh venv day 13 | Applied |
| 6 | Reduced run fidelity unknown | TA | M | Test on day 6 | Open, day 6 |
| 7 | Port collision | TA | m | Next free port | Open |
| 8 | Both questions on one slide | CEO | M | Slide 2 | Applied |
| 9 | What to measure first | CEO | m | Three measurements tied to VOI | Open, day 12 |
| 10 | Transition costs | CFO | M | Payback sensitivity | Applied |
| 11 | Regional rents versus comparability | CFO | M | Rule + uniform check | Open, day 2 |
| 12 | k = 8 strawman risk | Strategy | M | Seeds and evaluations per k | Applied |
| 13 | Departure at 04:00 for all | Ops | B | Required departure-wave check | Applied |
| 14 | Unlimited spot | Ops | M | Spot cap case | Applied |
| 15 | Centroid snapping duplicates | Data Team | m | Distinct-site assignment | Open, day 5 |
| 16 | Car profile for trucks | Field manager | m | State as assumption | Open, day 2 |
| 17 | Lease timing | Real estate | M | Discussion + bonus | Applied |
| 18 | Chronically late stores | Store owner | M | Per-store distribution | Applied |
| 19 | Demo squeezed after the freeze | PM | M | Registry schema day 4, mock-data demo from day 5 | Open, day 4 |
| 20 | User stories | Product manager | m | Write before building | Open, day 5 |
| 21 | Offline fonts | Lead developer | m | Vendor and subset OFL fonts | Open, day 10 |
| 22 | TU condition of the assignment LP | OR scientist | m | State that bounds count stores | Open, wording |
| 23 | Noisy 7-day quantile | OR scientist | M | Vehicle-need regression + many cheap days, checked against 28 days | Open, day 4 |
| 24 | Trivially passed predictive check | Statistician | M | Mild misspecification in the truth | Open, day 2 |
| 25 | Sub-colour values | UX designer | m | Derived tints documented | Open, day 10 |
| 26 | Manufactured saving | Red team | B | Plausible history rule + decomposition | Applied |
| 27 | One world seed | Red team | M | Two more seeds, G2 + short E | Open, day 9 |

Rejected suggestions, with reasons:

- Use BoTorch or Ax for the search: an own GP with EI is short, lecture-faithful and easier to explain in an oral check; BoTorch adds no proven gain at B = 40.
- Model multiple trips per vehicle: a second trip cannot meet the noon deadline; recorded as omitted with this reason.
- Use an LLM agent to formulate or tune the model: no proven gain for a one-off strategic study; mentioned only as future work.

---

## 4. Next review

Review 02 at the day-4 gate: the toy pipeline and E on the full baseline, with the Examiner, OR scientist, Lead developer, Delivery Operations and Field manager.
