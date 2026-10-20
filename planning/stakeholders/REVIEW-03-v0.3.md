# Review 03: Spark run 2 and the full-scale demo (v0.3)

Date: 2026-10-20.
Seven independent reviewers (general-purpose agents, read-only, one persona card each) reviewed Spark run 2, the demo and every markdown file against the brief (`assignment.md`, the template, the classification reference and the example).
The individual reports are in `review-03/`.
The user asked two questions before the round: are straight lines on the map right, and are about 700 trucks a day right.

| Report | Personas | Blockers | Majors | Minors |
|---|---|---|---|---|
| `01-examiner.md` | Examiner | 2 | many | many |
| `02-13-ta-developer.md` | TA, lead developer | 2 | 8 | 10 |
| `06-08-operations-field.md` | Delivery operations, field manager | 2 | 6 | several |
| `14-or-scientist.md` | OR scientist | 2 | 8 | 11 |
| `15-04-statistician-cfo.md` | Statistician, CFO | 2 | 6 | 10 |
| `16-03-10-ux-ceo-store.md` | UX designer, CEO, store owner | 3 | 10 | 18 |
| `17-redteam-markdown-audit.md` | Red team (markdown audit) | 5 | 12 | 6 |

## The two questions

**Straight lines.**
Every kilometre and minute in the engine is an OSRM road value; only the drawing was straight.
The brief allows points and lines on latitude and longitude (`assignment.md` 6.3), but the east-coast legs drew about 101 km over the Taebaek mountains where trucks drive 163 km, and the legend promised road geometry that did not exist.
Fix: `osrm/build_shapes.py` fetched all 27,173 legs the demo draws (0 missing); the demo draws them and moves trucks along them; the legend text was corrected.

**Truck count.**
About 578 of 672 weekday routes are right: 16.7 stops and 35 cages each, 7.7 h of the 8.5 h between 04:00 and 12:30, so the shift binds, and the load bound alone is about 430-470 trucks.
The other 94 (227 in today's network) each carried one far store: a store beyond 125 km cannot join any one-driver route (250 km cap), so the savings merge never touched it.
They are the problem, not the count.

## Consolidated findings

| # | Finding | Raised by | Severity | Resolution |
|---|---|---|---|---|
| F1 | Far stores each get a truck and a relay driver; 227 routes a day today, 94 recommended; worth roughly the whole saving | all seven | Blocker | Relay route class: far stores share multi-stop two-driver routes (500 km, on duty to 19:00, noon deadline hard); user decision 2026-10-20 (D-058) |
| F2 | Those deliveries arrive 07:35-10:34 but were counted late; today's "97.7%, fails 98%" was a label; `deliveries.csv` showed 100% before noon against 97.6% in the registry | examiner, TA, ops, stat, red team | Blocker | Service by the clock for every route; relay routes reported as a separate compliance count; routes beyond even the relay limits count as missed (D-058) |
| F3 | Today's network was built with the 500-store minimum, which the brief exempts the baseline from (`assignment.md` 71), so it had no east-coast DC (a strawman under R5) | red team, ops | Blocker | P-median on road km with every store within one driver-day, no minimum, cap kept; new stores to the nearest DC; user decision (D-059) |
| F4 | Only the relay-price reversal exists; R5 asks for stop time, speed, DC fixed cost and the distance model | examiner, OR, red team | Blocker | Reversals added to the pipeline (D-060) |
| F5 | `problem-definition.md` and `proposal.html` do not exist (about 60 marks) | examiner | Blocker | Next work package |
| F6 | The saving band covers day sampling only and is quoted without saying so; 41% of the saving was the relay line | statistician | Blocker | Label the band in every document; rerun changes the relay share |
| F7 | Leases: the run-2 design closed the DCs with the most lease left; no one-off costs or payback | CFO | Blocker (proposal) | Business decision log; payback table in the proposal |
| F8 | Departure waves move k* 13 to 14 at 30 docks; today's network overflows too; departed_at is 04:00 everywhere | ops, OR, examiner | Major | Second dock count (x1.25) reported; docks in the business decision log |
| F9 | Sweep, k*, checks and reversals use the 390-candidate validation, not the B = 40 search | examiner, TA, OR | Major | Label as validation in the demo and the definition |
| F10 | R3 Spearman over 40 points (0.60) differs from the whole pool (0.98, examiner); within-k groups have 3 points | examiner, OR | Major | Pool-wide Spearman added to the registry; both reported |
| F11 | README: no run times, says Python 3.10 while runs used 3.12.3 aarch64, says the G remedy is not in, wrong run order note | TA, red team, examiner | Major | README rewrite after run 3 |
| F12 | Demo: fleet slider max 40 < 72 vehicles needed; precomputed pills hidden at 1,440 px; three different costs for one network; waterfall axis; `[hidden]` ignored; phone scroll and tiny chart text | UX | Blocker/Major | Demo pass after run 3 |
| F13 | Formula section states km and shift as hard while relay routes break them; late penalty and bounds missing | OR, examiner | Major | Rewrite formulas with the relay class |
| F14 | Posterior predictive check is circular (in-sample exposure with realised shocks) | statistician | Major | Replace with a held-out year-end check |
| F15 | Break rule: 30 min only added to the return; Labor Standards Act Art. 54 gives 1 h for an 8 h+ day; flat 35 km/h | ops | Major | Business decision log; stop-time and speed reversals cover the effect on k* |
| F16 | MIDTERM_BRAIN.md still says v1.2, nothing implemented; DECISIONS statuses not updated (no "Superseded") | red team | Major | Status banner and status pass in this round |
| F17 | Spot trucks unlimited (136 on the peak day) | ops | Major | Business decision log; spot cap as a later reversal |
| F18 | Missing road cache silently fell back to placeholder distances | TA | Major | Warning added |
| F19 | verify.py needs playwright, not in requirements; stale `results/reduced/verification.json` | TA | Major | Skip with a message; rerun after run 3 |
| F20 | `.venv310` (189 MB) inside `code/` would break the 200 MB ZIP | TA | Major | ZIP allowlist builder |
| F21 | Smaller code issues: unused `model` parameter, `app.py` NameError when ports are busy, relay price missing from `cost_parameters.csv` | TA | Minor | Fixed |

## What the reviewers found sound

- The cost identity, paired saving, LP integrality and the 0.671 newsvendor quantile.
- The search is reported honestly (13 seeds plus 27 EI picks, random selection on the same pool, validation after the search); EI reached the pool best at step 18.
- Three independent day sets agree on the saving (1,769 / 1,776 / 1,778 M); the WORK_LOG run-2 numbers match the registry.
- The outcome tables match the Section 2.5 schemas.

## Consequence

F1 to F3 change the world and the lower level, so no run-2 number survives (as with D-025).
Run 3 on the Spark follows the fixes; the demo, README and documents are updated on run 3's numbers.
