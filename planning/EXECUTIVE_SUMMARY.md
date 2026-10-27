# Executive summary - IE437 midterm, Dasol distribution-centre network

Reference document for the author; not part of the hand-in ZIP.
State as of 2026-10-27; deadline Monday 2 November 2026, 10:00 KST; ZIP `20264059_LouisWellmeyer.zip`.
Details live in `WORK_LOG.md` (what happened), `DECISIONS.md` (why), `LLM_USE.md` (what the LLM did and how it was checked), `ALGORITHM_REVIEW.md` (experiments of 21 Oct) and `../../grading/GRADING_LOG.md` (grader calibration).

## 1. The answer

Run ten distribution centres instead of twelve: keep Gimpo Gochon and Cheonan Seobuk, open Namyangju Jingeon, Siheung Banwol, Wonju Munmak, Nonsan Yeonmu, Naju Bitgaram, Gimhae Hallim, Gyeongju Oedong and Chilgok Waegwan.
In the fictional instance this saves 592 M KRW a month (90% interval 584-601) and 583 M on days the search never saw, with every delivery before noon.
Our routing heuristic over-states today's small rural territories more than the redesign's: with PyVRP's routes the saving would be about 437 M a month, still positive and then mostly rent.
Nine and eleven DCs are near-ties; eight (Strategy's proposal) costs 393 M a month more than ten.
The best 9-, 10- and 11-DC networks take the same action at every lease expiry, so the choice between ten and eleven (adding Jinju Sabong) waits for the GPS study; under uncertain speeds eleven is marginally cheaper in expectation (13 M a month) and with PyVRP's routes by about 9 M a month.
375 M of the saving needs no lease at all: today's territories were last drawn in 2016 and never rebalanced.
Two conditions reverse the answer: if today's real network were already as good as a p-median design for today's stores (keeping it is 61 M a month cheaper), or if the business allows neither a second driver on far routes nor a small coastal DC below 500 stores (the best redesign then costs 511 M a month more; allowing either restores the saving).
The relay driver is priced at a full owned vehicle-day (180,822 KRW), an upper bound: only a driver is added, so the saving is conservative on that point; every deviation from the brief is in a register (definition Section 3, proposal slide 6).
Implementation follows the lease expiries (March 2027 to December 2029); switching at once costs 9.4 bn more over 36 months than changing nothing, because released leases must be paid out.
First data to obtain: the real outcome tables (they measure today's network), one month of GPS traces (stop time and speed are the only inputs worth measuring: EVPI 27 M a month; demand history is worth 0), real rents.

| Headline number | Value | Source |
|---|---|---|
| Today's network, 28 final days | 6,566.9 M KRW a month | run 5 registry `finals.baseline` |
| Recommended, 10 DCs | 5,974.5 M | `finals.recommended` |
| Saving, final / held-out days | 592.4 (584.0-601.0) / 582.6 (570.9-593.7) M | `saving` |
| Saving decomposition | redraw territories 375.3, best 12 sites 83.2, ten DCs 133.9 M | `saving.waterfall` |
| Cheap criterion without the clock (G1) | picks 8 DCs, loses 425.5 M | `finals.proxy_only` |
| Clock-aware criterion (G2) | Spearman 0.83 (G1 0.58), picks k = 10 | `r3`, `r3_g1` |
| Search | finds the pool's best at evaluation 16 of 40; random selection does not | `log_bo`, `random_band` |

## 2. What was built

| Deliverable | Content |
|---|---|
| `problem-definition.md` | Seven template sections: four statements placed, D1-D4 with dependencies and `evaluated_by`, standard forms of the three levels, I/O schema, data reading table (orders are not shelf demand; outcome tables are outcomes of today's network), demand model, approaches, balance table, cases, evidence, reversals, extensions, client proposal, three LLM discussions |
| `code/` | Generator, OSRM road cache, Poisson-Gamma demand, savings + 2-opt + relay router, transportation-LP assignment, newsvendor fleet, E over sampled days, G0/G1/G2, pool, discrepancy GP + EI, reversals, checks, extensions, `verify.py`, local app; three commands |
| `demo.html` | Six tabs in CU style: answer map and sweep, animated delivery day on real road shapes with a live solve, lecture-by-lecture method, data and baseline with a 1990-2026 growth animation, cases and checks, extensions; offline, every precomputed number tagged with its command |
| `proposal.html` | 17 slides in project-management order, built from the same registry; visible controls; each evidence slide links to its demo tab; each claim tagged "shown in the fictional instance" or "needs real data" |

## 3. How the answer changed, run by run

| Run | Date, machine | Result | What it exposed, what changed |
|---|---|---|---|
| v0.1-v0.2 | 19 Oct, laptop | First end-to-end pipeline, uncalibrated distances | Replaced by OSRM road distances and population-based stores |
| Spark run 1 | 20 Oct | Saving 1,776 M, k = 13 | Non-monotone sweep (500-store minimum forced 515 km routes), G1 near-random (Spearman 0.20); G1, pool and dock count fixed |
| Spark run 2 | 20 Oct | Saving 1,776 M, k = 13 | Review 03: most of the saving came from one-truck-per-far-store routes counted late; relay route class added, baseline rebuilt |
| Spark run 3 | 20 Oct | Saving -100 M: every redesign lost | Baseline was the optimum of the search's own objective (p-median on today's stores and road km) |
| Algorithm review, X1-X6 | 21 Oct, laptop | Router about 4% above PyVRP on both networks; GP + EI fine; G1 lacks the clock; minimum and exemption explain run 3 | `ALGORITHM_REVIEW.md` |
| Laptop reduced run | 27 Oct | 2016 baseline and G2: saving 124.5 M at reduced scale | Plan from the critique implemented (D-069 to D-074) |
| Spark run 4 | 27 Oct | Saving 590 M, k = 10 | Spark and laptop gave different pools from the same code: unstable sorts (D-075) |
| Spark run 5 | 27 Oct | Saving 592 M, k = 10; extensions | Same numbers on both machines |
| Spark run 6 (reported) | 27 Oct | Saving 592 M, k = 10; stock-out penalty applied; strict-brief rows | Search log and G-versus-E statistics shifted slightly; strict brief reverses (-511 M) unless a small coastal DC is allowed (+625 M) |

## 4. Register of runs and tests

| What | Where, how | Result |
|---|---|---|
| Road-distance cache | OSRM v6.0.0 on the Spark, Geofabrik extract of 2026-10-18, laptop through an SSH tunnel | 9,718 x 60 store-site and 50 nearest-store distances, 0 unroutable; calibrated model error 20% / 9% / 4% by distance band |
| 2016 planner | `prep/current_network.py`, laptop, 40 s | The 12 sites of `geo.CURRENT`; unchanged after the stable-sort fix |
| Full and reduced pipelines | Spark runs 1-5 (16 workers); laptop reduced runs (1-2 workers) | Section 3 |
| Extensions | Spark (run 5) and laptop (2 workers, after the myopic-pricing fix) | Identical apart from the fixed field |
| `verify.py` | Laptop, run 5 | 28/28: route audit, cost identities, paired saving, LP bounds, determinism, worker independence, departure waves, outcome tables, exact set partitioning (25 instances: 0 extra vehicles, km 0.4% above optimum), JS = Python engine, no external resources, local app, embedded registry, both Spearman values, extensions |
| Cross-machine reproducibility | Reduced run on aarch64 and x86_64 | 52,205 of 52,206 numbers equal to 1e-9; one EI value 0.07% apart |
| Fresh-environment reproduction | ZIP extracted, new Python 3.10 venv from `requirements.txt`, `run_reduced.py` with the network cut off (`unshare -rn`), 2 workers | 17 min 15 s; 54,642 registry numbers, only 27 expected-improvement values differ by more than 1e-9 (at most 0.07%); every search choice and result identical |
| Router against PyVRP 0.11.3 | Laptop, one core each, run 5 networks, day 0; 0.1 s per store, then 0.5 s per store for territories PyVRP could not route | Today's network 654 vs 608 vehicles (6.6% of operating cost; Andong 33 vs 24, Gangneung 17 vs 14, Daejeon 51 vs 43; Yongin unrouted by PyVRP even at 0.5 s per store); recommended 620 vs 599 (2.9%); the saving would fall by about 156 M to about 437 M a month; route elimination and a sweep construction gained at most one vehicle |
| Departure waves, thinning, relay price, stop time, speed, distance model, rent, minimum, p-median baseline, strict brief | Inside every full run (reversal rows) | Two rows flip the sign: the p-median baseline (-61 M) and the strict brief with the minimum kept (-511 M) |
| Demo in a browser | Playwright, Chromium 149, offline (all non-file requests blocked), 1440 and 390 px, every tab, live solve | No console errors, no requests, no overflow |
| Proposal in a browser | Playwright, every slide | No errors, no overflow |
| Lint | `ruff` (E, F, W) on `dcn/`, `verify.py`, run scripts | Clean |
| Stakeholder reviews | 01 (17 personas, plan), 02 (6 agents, v0.1), 03 (7 agents, run 2) | `stakeholders/` |
| Grader calibration | 6 fresh graders on A1 plus 2 degraded copies, prompt v1 and v2 | v2 mean 92.8 against the real 94.5; frozen for the midterm |
| Midterm grader round 1 | 3 fresh graders on the hand-in ZIP, frozen prompt v2 | Base 92 / 94 / 92, bonus 6.5 / 6 / 6: stop rule met; fixes applied (hidden point on per-type multipliers, faster reduced run, model-uncertainty range, VoI reconciled, wording) |
| PyVRP on the best 9- and 11-DC networks | Laptop, 0.3 s per store | Day cost with rent 189.0 / 187.3 / 187.0 M for k = 9 / 10 / 11 (savings 192.8 / 191.4 / 192.0): the router bias moves k at most within the 10-11 near-tie |
| Reduced profile without report-only steps | Laptop, 2 workers | 10 min 22 s; 53,902 numbers equal to run 5's except 27 EI values |
| Midterm grader round 2 (confirmation) | 3 fresh graders on the run-6 ZIP | Base 99.5 / 96.5 / 97, bonus 7 / 6.5 / 6.5: stop rule met again; remaining points: drift not swept, reduced run slow on two cores, candidate generation missing, slips (all addressed after the round) |
| Midterm grader round 3 | 3 fresh graders on the ZIP after the round-2 fixes | Base 99.5 / 99 / 99, bonus 6.5 / 7.5 / 7; remaining points: reduced run slow on two cores (all three), demo caveat on the baseline history (fixed), headline uses the router measured as biased (PyVRP figure beside it, not in it) |
| Router and pool speedups | Route fingerprints of 108 territory-days x 3 parameter sets at both scales; 2,400 random networks; reduced pool; reduced run | Routes, assignments and pool identical bit for bit; reduced run 6 min 48 s on two laptop cores (was 10 min 22 s), registry equal except 16 EI values |

## 5. How the LLM was used

Claude (Anthropic, Claude Opus 5.5) in Claude Code was used as a coding agent, analyst and reviewer throughout; every task is a row in `LLM_USE.md`.
Roles: context search (course repo, brief, lectures), arithmetic checks, web research (CU design, OSRM, extracts), stakeholder role-play and independent review agents, code for every module, debugging run anomalies, the demo and proposal, the definition text, Playwright QA, grader calibration and grading.
Guardrails: no number enters a deliverable unless `code/` produces it; instructor-only material is never cited; heavy runs go to the Spark and are started by the user; a pre-tool hook makes the agent state purpose and callers before writing a file.

Where the LLM was wrong and the check caught it:

| Claim or output | Caught by | Correction |
|---|---|---|
| "Savings is close to optimal", and later "its error is similar on both networks, so it cannot move the ranking" (true on run 3's networks) | PyVRP on every territory of run 5's networks | Not similar: 6.6% on today's network, 2.9% on the recommended one; the saving falls by about 156 M; reported in every deliverable |
| "Today's network is simply good" (run 3) | Baseline checks X1-X5 | The baseline was the search's own optimum; rebuilt as the 2016 design (D-069) |
| A learned territory cost as the decider | Its MILP picks lost 254-1,035 M under E | Rejected; G2 built instead |
| Run 2: today misses 98% for geographic reasons | Review 03 arithmetic (1 - 227/9,718) | It was a late label on relay deliveries |
| G2's remaining bias "nearly constant" | Recomputed on run 5 (sd 1,437 M) | Sentence rewritten |
| A one-week-old store "sits close to its type's mean" | Prior strength is about 2 store-days | Sentence rewritten (80% data weight after a week) |
| Myopic sequence end state 9,308 M | Priced with the minimum while transition months were not | Like-for-like pricing (5,793 vs 5,777 M) |
| A function named `path` shadowing the registry path | Reduced test crashed at the write | Renamed |
| Demo text naming tabs that do not exist; an unrendered `${ALT}`; clipped timeline | Re-reading and screenshots | Fixed |

## 6. Open items

- Decide with the user whether the headline should carry the PyVRP-corrected saving (437 M) instead of beside it.
- Final ZIP after `verify.py` passes on the faster code; push only when the user asks.
