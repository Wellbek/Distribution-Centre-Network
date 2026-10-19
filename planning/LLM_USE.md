# LLM use - rolling record

What LLMs and coding agents were used for in this midterm, why, and how their output was checked.
Append-only: add a row whenever an LLM does a task; never rewrite old rows, correct them with a new row.
This record feeds the header line "LLM tools and use" and Section 7 (LLM Review & Key Revisions) of `problem-definition.md`, which must select three important discussions, at least one checked by a calculation or a small experiment [brief §8].

## Tools

| Tool | Model | Role |
|---|---|---|
| Claude Code (CLI) | Claude Opus 5.5 (`claude-opus-5-5`) | Context search, research, planning, role-played reviews, drafting, coding, verification |
| ECC plugin skills and agents | same model | Structured workflows (planning, review, verification, design), listed per task below |

## Guardrails in force

- Every factual claim in the plan is tagged `[SRC]` (read from a source, with the reference), `[INF]` (inference) or `[IDEA]` (proposal); unconfirmed external facts are marked for verification.
- Instructor-only material found in the public course repo is used only to prioritise work; it is never cited in the submission.
- No number enters a deliverable unless `code/` produces it (results registry); the LLM never types results by hand.
- External engines, APIs, agents or LLM features inside the product only with a proven large gain (user rule).
- Code comments terse and direct ("Compute ..."), no filler (user rule).
- A pre-tool hook (GateGuard) forces the agent to state the purpose, the callers and the user instruction before creating any file.
- Long-running jobs never on the laptop (it hard-resets under load); heavy runs go to the DGX and are started by the user.

## Log

| Date | Task | Skills / agents | What the LLM did | Why | How I checked it | Outcome and location |
|---|---|---|---|---|---|---|
| 2026-10-19 | Context search: course repo history | none | Read the last ten commits of `omeletJK/ie437`, their diffs (brief v1.0 to v2.2), the instructor README and the committed A1 grading guide | Find what the instructor changed, removed and measured in a pilot run | Quoted commit hashes and lines; verified the repo is public with `gh api` | `planning/MIDTERM_BRAIN.md` Section 2 |
| 2026-10-19 | Context search: brief and lectures | none | Read the brief, template, classification reference, format example; lecture markdown chapters 0-6 and the slide PDFs | Map the required tools to lecture slides | Checked the PDFs against the markdown source (05 identical, 00-04 older exports) | Brain Sections 1, 15 |
| 2026-10-19 | Context search: own A1 and worked examples | none | Read the A1 hand-in repo and the professor's A1 worked examples | Reuse working style; learn the grader's taste | Compared structures and verification records | Brain Section 2.6 |
| 2026-10-19 | Arithmetic checks | none | Computed reach before noon, thinning distortion, k bounds, newsvendor fractile, cost scale from the teaching defaults | Ground the plan in numbers, not guesses | Python script, values reproduced in the brain | Brain Section 4 |
| 2026-10-19 | Web research | WebSearch, WebFetch | CU brand colours and type; OSRM arm64 image; Geofabrik Korea extract; Korean convenience-store counts | Design system and infrastructure risks | Official CU page versus an unofficial lookbook; unconfirmed items marked `[RISK]` | Brain Sections 14, 18 |
| 2026-10-19 | Role assumption | none (inline role-play) | Wrote 17 stakeholder personas and played each one against plan v1.0, then a round table | Find gaps no single viewpoint sees | Every finding traced to a plan section; 27 gaps listed with status | `planning/stakeholders/`, `REVIEW-01-plan-v1.md` |
| 2026-10-19 | Drafting and tooling | none | Wrote the brain, the persona READMEs, the review, this record, the decisions record and the HTML renderer | Planning deliverable for the user | User reviews the HTML; renderer asserts no em dash | `planning/` |
| 2026-10-19 | HTML render and visual QA | none (Playwright) | Rendered the brain, panel, review and records into one offline page; screenshotted desktop and an emulated iPhone in light and dark mode; checked all 48 internal links and horizontal overflow | The user reviews the plan as HTML; the user's rule is pixel care | Overflow measured at 0 px on both widths; every link target exists; no JS errors | `planning/MIDTERM_BRAIN.html` |
| 2026-10-19 | First naive implementation (v0.1) | none | Wrote `code/` (world, demand, routing, evaluation, GP, search, pipeline, app) and the CU-inspired demo template; ran the reduced pipeline once (277 s, one capped core) and built `demo.html` | User asked for a one-shot naive core and visual demo before reviews | One end-to-end run; Playwright screenshots of all views, no JS errors; results inspected, artefacts listed for review 02 | `code/`, `demo.html` |
| 2026-10-19 | Verification and stakeholder review 02 | general-purpose agents (6, independent, read-only), Playwright | Wrote and ran `code/verify.py` (identities, route audit, exact check, engine parity, live endpoint); six persona agents reviewed v0.1 independently and wrote `planning/stakeholders/review-02/*.md`; consolidated into `REVIEW-02-v0.1.md` | Independent review of the first implementation from all stakeholder angles | Agents' numbers spot-checked against the registry (relay 803 vs 418 M, 72% of the saving, reproduced by four agents independently) | `planning/stakeholders/REVIEW-02-v0.1.md` |
| 2026-10-19 | v0.2: blockers and demo redesign | `ecc:frontend-design-direction`, WebFetch (nicetocu.com.my), Playwright | Fixed the review-02 blockers in `code/` (relay priced as a driver-day with a reversal row, east-coast DC in the current network, pinned Python 3.10 environment, stratified weighted days, empirical-Bayes prior, overdispersion, LP-aligned G, whole-pool validation band, top-5 re-scoring, store-level service); rebuilt the demo as four tabs with a zoomable map, followable trucks, shop icons, and lecture-style formula sections pre-rendered with KaTeX | User asked for v0.2, fewer tabs, CU style, zoomable map following trucks, lecture-aligned algorithm visuals, ECC skills | Ran the pipeline under Python 3.10 (pinned), `verify.py`, Playwright screenshots of every view; fixed clipped labels, nav wrapping and an evidence-contradicting headline | `code/`, `demo.html`, `tools/render_math.py` |
