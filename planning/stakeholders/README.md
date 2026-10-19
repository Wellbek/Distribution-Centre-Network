# Stakeholder panel

Seventeen personas that review every artefact of the midterm from their own angle.
Each folder holds one README: who the persona is, how they think, what they check, the questions they ask, the red flags that stop them, and a prompt to role-play them.
The panel exists so that no gap survives because nobody in the room cared about it.

## The panel

| # | Persona | Angle | Reads first |
|---|---|---|---|
| 01 | [Examiner](01-examiner/README.md) | Course instructor and grader | `problem-definition.md` §2-4 |
| 02 | [TA reproducer](02-ta-reproducer/README.md) | Runs the three commands in a fresh environment | `code/README.md` |
| 03 | [CEO](03-ceo/README.md) | Business owner who asked the two questions | `proposal.html` slide 2 |
| 04 | [CFO](04-cfo/README.md) | Money, uncertainty, payback | Cost breakdown and saving interval |
| 05 | [Head of Strategy & Planning](05-strategy-planning/README.md) | "Cut to eight" | Sweep at k = 8 |
| 06 | [Head of Delivery Operations](06-delivery-operations/README.md) | Vehicles, drivers, the clock | Lower level and binding constraints |
| 07 | [Data Team lead](07-data-team/README.md) | Centre of gravity, speed of analysis | G versus E |
| 08 | [DC field manager](08-field-manager/README.md) | Roads, bridges, docks, mornings | Distance model and the live solve |
| 09 | [Real estate and leases](09-real-estate/README.md) | Sites that can actually be leased | `candidate_sites`, lease dates |
| 10 | [Franchise store owner](10-store-owner/README.md) | Delivery before noon at *my* store | Service level per store |
| 11 | [Project manager](11-project-manager/README.md) | Deadline, scope, risk | Schedule and gates |
| 12 | [Product manager](12-product-manager/README.md) | Users, flows, the story | Demo first screen |
| 13 | [Lead developer](13-lead-developer/README.md) | Code quality, reproducibility | `code/` |
| 14 | [OR scientist](14-or-scientist/README.md) | Formulation rigour, heuristic accuracy | Lower and upper level |
| 15 | [Bayesian statistician](15-statistician/README.md) | Demand model, sampling, intervals | R2 and the saving interval |
| 16 | [UX and brand designer](16-ux-designer/README.md) | CU-inspired look, accessibility, motion | Demo and proposal |
| 17 | [Red team](17-red-team/README.md) | Tries to break the conclusion | The recommendation |

## Discussion protocol

1. **Freeze the artefact** under review (a commit hash or a file version) and name it in the review file.
2. **Independent pass.** Each persona reviews alone, in their own voice, and returns at most five findings.
   Every finding has: severity (blocker, major, minor), evidence (file and line, or the number), the fix, and which rubric criterion it touches.
3. **Round table.** Personas react to each other's findings: agree, disagree with a reason, or merge.
   Conflicts are written down, not smoothed over (for example Examiner versus Product manager on where effort goes).
4. **Gap list.** One consolidated table: gap, owner persona, severity, decision, status.
5. **Apply and record.** Changes go into the artefact; the review file links the commit that applied them.
   Rejected findings keep their reason.

Review files are named `REVIEW-NN-<artefact>.md` in this folder.
Round 1 reviewed the plan: [REVIEW-01-plan-v1.md](REVIEW-01-plan-v1.md).

## When to convene the panel

| Gate | Artefact | Personas that must sign off |
|---|---|---|
| Day 0 | Plan | All |
| Day 4 | Toy pipeline and E on the baseline | Examiner, OR scientist, Lead developer, Delivery Operations, Field manager |
| Day 7 | Definition §1-3 draft, brief's self-check | Examiner, Statistician, Project manager, Red team |
| Day 9 | Frozen results registry | Examiner, CFO, Strategy & Planning, Red team, Statistician |
| Day 11 | Demo and proposal | CEO, Product manager, UX designer, TA reproducer, Store owner |
| Day 13 | Full ZIP in a fresh environment | All |

## Running the panel

- **Inline role-play** (default): one session plays each persona in turn from its README, then writes the round table.
- **Independent agents** (on request): run each persona as its own agent with its README as the brief, for example through `ecc:council`, `ecc:santa-method` or `ecc:team-agent-orchestration`, so the passes cannot influence each other.
- Personas never invent facts about the course; where they speculate about grading they say so.
