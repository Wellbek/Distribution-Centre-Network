# Review 03 - demo.html: UX designer (16), CEO (03), store owner (10)

Reviewed: `demo.html` of 2026-10-20 10:28 (full run, `python run_full.py`, seed 437, 9,718 stores, 13 DCs recommended).
Method: Python Playwright, Chromium headless, `file://`, 1440x900 and iPhone 13 emulation, plus one 1440x900 context with `reduced_motion="reduce"`.
Screenshots: `/tmp/claude-1000/-home-louis-GitHub-Repos-KAIST-GSDS-IE-437-Data-Driven-Decision-Making-and-Control/dcf6814e-5a68-4e90-b25e-0f72fb5cc916/scratchpad/review03-ux/` (`desk-*`, `phone-*`, `day-*`, `live-*`, `crop-*`).
Exercised: wheel zoom, Play, scrub to 07:00 / 09:30 / 12:30 / 13:54, Follow a truck, Stop following, Current 12 / Recommended, Weekday / Peak day, every live slider, the demand-day select, Defaults, the failure-case button.
Health: no console errors, horizontal overflow 0 on every tab at both sizes; animation runs at about 21 fps at 1440x900 with 672 trucks.
Template references are to `code/static/demo.template.html`.

## Verdicts

- UX designer: the system is clean and on-brand, but the map tab is a wall of 672 identical trucks and red spokes, and three numbers contradict each other across tabs.
- CEO: I get "13 DCs, keep 7, close 5, open 6" in five seconds, which is a real improvement; I cannot tell how sure "13" is, and I see three different monthly costs for the same network.
- Store owner: the page says 99.0% on time, but 94 stores are never on time in the recommended network, and the delivery-day tab tells me "0 after 12:00" while it draws them red.

## Brief 6.3, line by line

| Requirement | Status | Evidence |
|---|---|---|
| Baseline and recommended network on a plotted map | Met | Answer tab map with What changes / Current 12 / Recommended |
| Sweep with its two cost components | Partly | Sweep shows six stacked parts; the brief's two (fixed vs operating) are never named as two |
| The evaluation log | Partly | Only a one-step-at-a-time slider under Q5 (`figSearch`, `#step`); no table of the 40 calls |
| G versus E for every evaluated candidate | Met, weak | Scatter in Q6 (`figScatter`); colour = k with no key, no hover |
| Live lower level for one DC with day, window, stop time, vehicle limits | Met, but broken at defaults | See B1 |
| Simplified static version states the difference | Met | "in-browser engine (same savings rules, no 2-opt)" |
| Normal, boundary and failure cases | Met | Checks tab cards |
| Every precomputed number labelled, with the command | Partly | See B3 |

## Blockers

**B1 - The live solve fails at its own defaults.**
Evidence: `live-default.png`; Hanam Gamil has 1,400 stores, the solver needs 72 vehicles, the `#lv-fleet` slider stops at 40, so the default result is "537 stores (38.4%) get no delivery, a stock-out penalty of 268,500,000 KRW" and "Before the deadline 61.6%".
The peak day needs 102 vehicles; no slider position can cover it.
An examiner opening the required live solve sees the "normal" case render as a failure, which contradicts "Recommended network, ordinary weekday ... 99.0% before noon" on the Checks tab.
Fix: in `initLive()` set `#lv-fleet` `max` to about 1.5 x the peak-day need and its default to the DC's owned fleet from the registry (for example `R.live.owned`), and keep the failure button on the Checks card (`value=12`) as the deliberate failure case.
Fix: make `#lv-reset` also reset `#lv-day` to 0; today Defaults leaves "peak (holiday eve)" selected and still fails (`reset:` 792 uncovered).

**B2 - 94 stores are never on time, and two tabs disagree about it.**
Evidence: in the registry `S.ontime_rec` is 0 for 94 stores (227 today); each is a one-store relay route (`DAY.routes.filter(r => r.over)` = 94 routes, 94 stores).
Checks tab: "Worst store today 0.0% · recommended 0.0%", "Relay deliveries count as late".
Delivery-day tab: "Delivered 9,718 / 9,718, 0 after 12:00" at 13:54, while the legend paints those same stores red.
Hero: "On time before noon 99.0%, worst day 99.0%", with no word about the 94.
As a store owner far from the city, I am one of the 94, every day, and the headline hides me.
Fix in `kpisDay()`: count relay stores as late, or show a third line "94 by relay driver (counted late)" next to "after 12:00".
Fix in `RENDER.answer` hero stats: change the fourth tile note to "94 stores always late (relay); today 227".

**B3 - Precomputed labels and the reproducing command are invisible at the reviewed sizes.**
Evidence: `@media (max-width: 1560px) { .nav-right .pill.pre { display: none; } }` hides `#run-pill` at 1440 and on phone; `setEngine()` gives `#engine` the class `pill pre`, so the engine pill disappears too (`desk-answer-full.png` shows an empty nav right).
The hero tiles, the waterfall, the reversal table and the sweep carry no "precomputed" badge; only the delivery-day KPIs do.
The command appears only at the bottom of the Checks tab.
Fix: drop that media rule and instead shorten the pill text below 1560 px (for example "precomputed · run_full.py"); add `<span class="badge">precomputed · python run_full.py</span>` to the `.stitle .chip` of each answer-tab section and under the hero stats.

## Majors

**M1 - Three monthly costs for the same 13-DC network.**
Hero 7,606.8 M (28 final days), delivery-day KPI 7,478.7 M ("fleet sized on the 28 final days"), sweep bar and "Budget of one" 7,447.5 M (7 search days).
The peak-day toggle turns the same KPI into 9,829.7 M "Monthly cost", which a CEO reads as a monthly bill.
Fix in `kpisDay()`: rename to "This day, as a monthly rate" or replace it with "Cost of this day" in M KRW per day.
Fix in `sweep()`: print the axis caption "7 search days, so about 2% below the 28-day figure in the hero".

**M2 - "Saving, 28 days 1,776.2 M" reads as a saving over 28 days.**
It is a monthly saving estimated on 28 sampled days; the unit "per month" is missing and the "M" has no KRW.
The CEO asked per year: 1,776 M a month is about 21.3 bn KRW a year, and nowhere on the page.
Fix in the `#hero-stats` array: labels "Saving per month (28 test days)" and "Saving per month (14 unseen days)", unit "M KRW / month", note "about 21 bn KRW a year".

**M3 - The confidence is about demand noise, not about the answer.**
The 90% interval 1,770.8 to 1,782.0 M looks like near-certainty, yet on the same page the departure-wave check says "The decision moves: k* = 13 with one 04:00 start, 14 with waves", the thinning check picks 12, and the sweep bars for k = 10 to 13 are within about 2% of each other.
The waterfall shows that 1,689.6 M of the 1,776.2 M comes from redrawing and moving 12 sites; the 13th DC adds only 86.6 M.
A CEO would sign "13" when the robust message is "move the sites; 10 to 14 DCs all save".
Fix: one line under `#hero-h1`: "The count is flat from 10 to 14 DCs; the saving comes from where the DCs are. 13 is best here, 14 with departure waves."
Fix in `waterfall()`: rename the last step to "add a 13th DC" and add a fifth bar with the recommended total 7,606.8.

**M4 - The waterfall axis is truncated and the last bar is a delta.**
`lo = Math.min(...vals) * 0.9` starts the axis near 6,800, so the 630 M and 1,059 M steps look like half the cost; the purple bar labelled "recommended (13 DCs)" shows "-86.6", which reads as the recommended network's value.
Fix: start the y axis at 0 or draw an explicit axis break, use `f0` instead of `fM` for ticks ("9,000.0" becomes "9,000"), and draw the total bar as in M3.

**M5 - Straight legs drawn over the mountains mislead.**
The relay spokes from the central DC fan across the Taebaek range to the east coast as bright red straight lines (`desk-day-full.png`, `day-baseline-peak.png`); the costs behind them are OSRM road km, so the eye under-reads distance and reads red as "broken".
The legend says "lines are straight between stops (road geometry follows with OSRM)", which promises a feature that does not exist in this build.
Fix: draw legs as thin dashed chords (`setLineDash([4,4])` in `drawDay`) and show road km on hover; draw one-store relay routes as dotted spokes in amber with a small "relay" tag rather than solid red; say "straight lines connect stops; distances and times are road km from OSRM" in the legend.
Better: store simplified OSRM polylines (Douglas-Peucker, about 20 points a leg) for the two showcase days only; that is a few hundred kB.

**M6 - 672 animated trucks are clutter, and the followed truck is lost.**
At zoom 1 the trucks merge into purple blobs; after Follow a truck the followed one sits among hundreds of identical icons (`day-follow.png`), its lime halo at 35% alpha is hard to find, and DC labels are painted under the trucks.
Fix in `drawDay`: below zoom 3 draw trucks as 3 px dots and only show icons for the hovered or followed DC; when `FOLLOW >= 0` draw all other routes and trucks at 15% alpha; draw `drawDC` labels last.
Fix: add a per-DC count plate at low zoom ("Hanam Gamil: 61 on the road") instead of 61 icons.

**M7 - "Stop following" is always visible.**
`.btn { all: unset; display: inline-flex }` overrides the `hidden` attribute, so `#unfollow` shows from page load (`is_visible` true, display flex).
Fix: add `[hidden] { display: none !important; }` to the stylesheet.

**M8 - The live result and the map disagree about what is shown.**
After a live solve the clock still reads "14:00 · peak (holiday eve) · recommended network · 849 routes" and the KPI card above still shows network-wide precomputed numbers, while the map shows one DC on a different demand day; the live KPIs sit below the fold.
The `.maptag` style exists but is never used.
Fix in `solveLive()`: put a `.maptag` on `#daymap` reading "LIVE: Hanam Gamil, ordinary weekday, 72 vehicles" with a close button that clears `LIVE_ROUTES`, and scroll `#live-out` into view on phones.

**M9 - The evaluation log is a slider, not a log.**
The analyst can see one call at a time (`#step-label`); there is no table of the 40 evaluations with step, rule, k, G, E and best so far.
Fix: add a `.scroll` table under the Q5 figure built from `R.log_bo`, with the chosen candidate highlighted (`tr.hl`), and let a row click set `#step`.

**M10 - Phone: the map traps scrolling and the tabs hide "Checks".**
`.mapbox { touch-action: none }` at `height: 62vh` turns most of the iPhone screen into a pan surface, so a finger swipe over the map does not scroll the page.
`#tabs` scrolls horizontally (552 px content in 354 px) with no cue; "How it works" is cut to "Ho" and "Checks" is not visible.
Fix: on `(pointer: coarse)` use `touch-action: pan-y` and pan only with two fingers or after a tap on the map; use icon-only tabs below 420 px or a fade mask on the right edge of `.tabs`.

## Minors

1. Chart text on phone is 5 to 6 px: the sweep (`viewBox 780`), waves and thinning charts scale down to 330 px; give them a phone-specific viewBox or a min-width with horizontal scroll.
2. Hero decoration `.hero::after` sits over the h1 and the kept-site list on phone ("keep 7", "Gimpo Gochon") and gives the two right stat tiles a two-tone background on desktop; hide it below 1100 px and make `.hstat` opaque.
3. The logo pill `.logo .bubble` uses `border-radius: 14px 14px 14px 3px`, a speech bubble, and the footer names CU; the brand brief says no CU name or bubble; use a full pill and "Look and feel inspired by Korean convenience-store design".
4. Census bar in Q3 (`figCensus`): only "load" and "shift" are labelled; the black 13.4% (violates limit) and four smaller segments have no names; add a legend row.
5. Newsvendor chart in Q4 (`figNews`): "own up to the 0.671 quantile" overlaps "P(need > n): spot hire avoided" (`crop-news.png`); move one label below the line.
6. Q4 flow: six boxes wrap so "E(x) KRW/month" sits alone on a second row; set `.flow div { min-width: 0 }` in that card or drop to five boxes.
7. G vs E scatter (`figScatter`): colour encodes k with no key and default-looking teal, orange and pink from `PAL`; add a k legend or label k next to each cluster.
8. PPC caption promises lime replicated totals that are barely visible; raise their stroke width or opacity.
9. Store histogram (`#storehist`): every non-perfect store sits in the 0 to 5% bin and 95% of the axis is empty; replace with three numbers per network: always on time, sometimes late, never on time (9,491 / 0 / 227 today, 9,624 / 0 / 94 recommended).
10. Counts with decimals: "Over-limit routes a day: today 227.0, recommended 94.0" in `reversal()`; use `f0`.
11. Numbers without thousands separators: "1400 stores" in `#live-sub` and "9718 stores within 500-1400 per DC" in the failure card; use `f0`.
12. Units missing: waterfall and sweep y axes ("M KRW / month" only in a caption), waves chart y axis, Q5 chart y axis; reversal table header "Today" and "Recommended" without "M KRW / month".
13. The "Field Manager" card on the answer tab prints an md5 and a timestamp; for the CEO show "Road distances from OpenStreetMap (OSRM), calibrated on 3,959 pairs" and keep the hash on the Checks tab.
14. The truck tooltip says "limit: shift" and the follow card "next stop ST08327"; say "stops because the driver's shift ends" and "next store at 07:31".
15. The day header hard-codes "deadline 12:00 · back by 13:00 incl. a 30 min break" while the live deadline slider moves to 10:00; bind it to the live values when a live result is on the map.
16. Reduced motion: with `prefers-reduced-motion` the Play button still animates (clock reached 04:04 after 1.5 s); under reduced motion, step the clock in 30-minute jumps without moving trucks.
17. The left sweep card has about 200 px of empty space under its legend because the right card is taller; align the cards to start, or move the "four voices" card below.
18. The "decision requested" asks for "real road times" although the hero says distances already come from OSRM; say "measured drive times and stop times" so the CEO does not think distances are still fake.

## What works

- The hero now answers both questions in one line, with keep / close / open and a concrete decision request.
- The waterfall separates "redraw territories" (630 M) from "move sites" (1,059 M), which answers the CEO's split question.
- Store hover tooltips give each store its DC today, DC recommended and on-time share; the "Stores like mine" section exists.
- Clean token use: purple anchor, lime for delivered and saving, red only for failures, 18 px cards, no default chart colours outside `PAL`.

## Priority order for the next build

1. B1 live fleet range and Defaults.
2. B2 relay stores counted late everywhere, and the hero tile.
3. B3 visible precomputed labels and command.
4. M1, M2, M3 one cost per network, per-month units, robust-range wording.
5. M7 `[hidden]` rule (one line).
6. M5, M6 map legibility, then M8 to M10.
