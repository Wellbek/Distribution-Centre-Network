# Review 02 - demo.html v0.1: CEO, product manager, UX designer, store owner

Reviewed: `demo.html` v0.1 (2026-10-19), data from `code/results/reduced/registry.json` (reduced run, seed 437).
Method: Python Playwright on `file://`, viewports 1440x900, 1366x768, 1920x1080 and iPhone 13; screenshots in `/tmp/claude-1000/review02-shots/` (files `ceo-<size>-<view>.png`, plus `1440-day-1400.png` and `1440-live-tight.png`).
Horizontal overflow (`scrollWidth - innerWidth`) is 0 on every view at every size.
The console logs one error on every load: `Fetch API cannot load file:///api/health`.
Severity: High = blocks the decision or a brief requirement, Medium = misleads or confuses, Low = polish.

## CEO (03)

Verdict: I cannot decide in 10 minutes.
I get "12 DCs, save 532 M a month" in 5 seconds, but I cannot tell what I am approving: the count stays at 12 while 8 of the 12 sites move, and the page never says so.

1. **High - the decision is hidden inside "12 from 12 today".**
   Evidence: `ceo-1440-overview.png`, the "Recommended DCs" tile; a 12-name run-on list in grey 12 px, and no word that only 4 sites stay (DC01, DC06, DC10, DC11) and 8 are new leases.
   Smallest fix: replace the note with "keep 4, close 8, open 8" and draw closed sites as crossed-out markers on the map in the Recommended state.
2. **High - the saving is not split into "redraw territories" and "change the network".**
   Evidence: the registry already holds `finals.reassigned12` (2,543.5 M, which is 9.5 M *worse* than today), but no view shows it; so the full 532 M comes from moving sites, and 385 M of it is fewer relay trucks (penalty 803.0 to 418.2 M).
   Smallest fix: add one waterfall tile on the overview: today 2,533.9 -> redraw only 2,543.5 -> move sites 2,001.6, with the relay share named.
3. **High - the range reads as near-certainty and the scale is not stated.**
   Evidence: `ceo-1440-overview.png`, "90% interval 528.7 to 535.8"; this interval only covers day-to-day noise, on a 1-in-5 instance with placeholder distances, and the tile does not say so (the scale appears only in the sidebar footnote).
   Smallest fix: under the saving write "fictional reduced instance; covers demand noise only, not distances or the scaling to 10,000 stores", and add a "stop if" line (for example: OSRM distances remove the relay saving).
4. **Medium - "Is cut to eight wrong?" is answered with seven.**
   Evidence: the Strategy & Planning card quotes the best 7-DC network (5,766.7 M), while `finals.proxy_only` (k = 8, 2,650.0 M) is the direct answer.
   Smallest fix: quote the 8-DC number in that card.
5. **Medium - no "what you approve today".**
   Evidence: no view names a next step, a data request or a decision date; the About view lists "does not do yet" items, which is the student's backlog, not my ask.
   Smallest fix: one line under "The answer": "Approve: an OSRM distance check and 4 weeks of outcome tables before any lease."

## Product manager (12)

User: a manager's analyst checking how the recommendation was produced.

1. **High - the live view cannot show a failure, so the live controls look as if they do nothing.**
   Evidence: `1440-live-tight.png`; with the deadline at 10:00 and capacity at 30 cages the solve returns 19 vehicles and 100.0% on time, and the peak day also gives 100.0%; the in-browser solver adds vehicles without limit, so "a day the fleet cannot cover" [brief 6.3] is unreachable; there is no vehicle-limit slider either, even though the brief asks for "vehicle limits".
   Smallest fix: add a "vehicles available" slider and report the stores left uncovered in a red `.err` box.
2. **High - live and precomputed labels contradict each other.**
   Evidence: `ceo-1440-live.png`; the header pill says "precomputed · python run_reduced.py" on the live view, the engine pill says "offline: in-browser engine" in grey (it reads as broken), and the subtitle says "plus 2-opt" while the note says "no 2-opt".
   Smallest fix: make the header pill depend on the view, rename the engine state to "live · in-browser (simplified, no 2-opt)", and take the subtitle from the engine in use.
3. **Medium - stale results after a setting changes.**
   Evidence: moving `#lv-dead` and `#lv-cap` leaves the KPIs unchanged until "Solve this day" is pressed, with no hint that they are out of date (checked in the script: KPI text identical).
   Smallest fix: re-solve on `change` (it takes about 100 ms), or dim the result cards with an "out of date" pill.
4. **Medium - one label, three numbers.**
   Evidence: "Monthly cost" for the same recommended network is 2,001.6 (overview, 28 days), 1,941.8 (day view, 1 day) and 1,938.8 (sweep, 7 days).
   Smallest fix: always name the day set: "monthly cost, 28 final days", "... this day", "... 7 search days".
5. **Medium - the cases are a text page, and the failure case is not a live failure.**
   Evidence: `ceo-1440-cases.png`; the boundary case lists 3 DCs at 280 but not the 5 at the lower bound of 100 (8 of 12 DCs sit on a bound), and "Solve the peak day live" opens a solve that shows 100% on time (see finding 1).
   Smallest fix: let each case card set the state it describes (network, k, day, limits) and land on the screen that shows it.

## UX and brand designer (16)

1. **High - map labels collide and have no backing plate.**
   Evidence: `ceo-1440-overview.png`; "Incheon Namdong" sits under the Yongin marker and store dots, "Yongin Giheung", "Daejeon Daedeok" and "Gimhae Hallim" are struck through by dots; on `ceo-iphone13-overview.png` the labels pile up in the Seoul area and "Gyeongju O..." is cut off at the right edge.
   Smallest fix: draw a white rounded plate (alpha 0.85) behind each label, nudge labels to avoid overlaps, and drop the labels below 600 px width.
2. **High - chart pixel faults.**
   Evidence:
   - `ceo-1440-sweep.png`: the red "current 12 DCs, same 7 days" label runs over the k = 17-19 bars (contrast 2.1:1 on the fuel bar), the y ticks read 1,750.2 / 3,500.3 / 8,750.8, and k = 9-13 look the same because the axis runs to 8,750.
   - `ceo-1440-search.png`: "random selection" and "GP on gap + EI" overlap at the line ends; the scatter shares one range for G (1,062-1,238) and E (1,939-12,325), so all points collapse into a 5 px column; the last x tick is clipped to "12,324"; "colour = k" has no key.
   - `ceo-1440-demand.png`: "7,141" collides with the "10-04" peak label, and "2026-0" is clipped at the right edge.

   Smallest fix: round ticks (nice numbers), move the baseline label left of the bars, use separate G and E axes, put end labels at offset y, and inset the axes by 20 px.
3. **Medium - token-set breaks.**
   Evidence: the pill badges stretch to the full width of the tile (offset widths 188 px against 35-87 px for the first tile, `ceo-1440-overview.png`); the territory palette reuses the state colours (Daejeon green = "delivered", Gimhae and a live route in amber = "after 12:00", `ceo-1440-day.png`); the savings figures are large green text on white, which this persona's own rule forbids; the fonts are not embedded, so offline machines fall back to system-ui.
   Smallest fix: `.kpi { align-items: flex-start }`, remove the green and amber from `PAL`, use purple for the saving values with a green arrow icon, and inline Noto Sans and Roboto WOFF2 as base64.
4. **Medium - contrast below 4.5:1.**
   Evidence:

   | Text colour | Background | Ratio | Used for |
   |---|---|---|---|
   | muted #787878 | white | 4.42 | every `.sub`, `.note` and KPI label |
   | footer text | #f0f0f0 | 3.87 | footer |
   | offline pill | #eeeeee | 3.81 | engine pill |
   | live badge #5f7d12 | #f1f8e1 | 4.35 | live badges |
   | red #d64545 | white | 4.38 | chart labels |
   | boundary tag #b06d00 | white | 4.17 | boundary case tag |

   On the map, waiting stores are #cfc6d3 on white (1.66:1), and green (1.94:1) versus amber (2.15:1) relies on colour alone.

   Smallest fix: muted -> #6b6b6b, red -> #c03535, amber tag -> #995f00; draw late stores as a triangle or ring as well.
5. **Medium - layout, motion and brand.**
   Evidence: the overview map card is about 600 px of empty white below the legend because it stretches to the right column (`ceo-1440-overview.png`; the same on demand and search); the day animation ignores `prefers-reduced-motion` (only the view fade is disabled); the trucks are purple squares that look like the DC markers; the footer names CU, which the brand rule forbids.
   Smallest fix: `align-self: start` on the map card, start the clock paused and step by the hour under reduced motion, make trucks small circles with a white ring, and change the footer to "visual style inspired by public brand colours".

## Franchise store owner (10)

Verdict: no.
I am a mountain store far from the city, and nothing on this page tells me whether I lose.

1. **High - nothing per store.**
   Evidence: every service figure is network-level 100.0% (overview, sweep table, cases); there is no per-store on-time distribution, no worst store, and no "stores like mine" filter.
   Smallest fix: a store-level panel showing the distribution of latest arrival per store for current and recommended, with rural and mountain stores split out.
2. **High - "100% on time" hides the relay trucks.**
   Evidence: 25 routes a day in the recommended network (48 today) "violate limit" and are rescued by a relay truck, yet the on-time tile reads 100.0%, worst day 100.0%.
   Smallest fix: show "on time without relay" next to it, and colour relay-served stores on the map.
3. **High - 71% of stores change DC and nobody shows who.**
   Evidence: computed from the page's own data (`base_dc` and `rec_dc`): 1,389 of 1,955 stores move; 896 end up farther from their DC; 123 are more than 30 km farther in a straight line, the worst +73 km, all flagged mountain.
   Smallest fix: a "moved stores" toggle on the overview map (an arrow or halo where the distance grew) and a table of the 20 worst, with the change in mean arrival time.
4. **Medium - the network was chosen on ordinary weekdays only.**
   Evidence: `ceo-1440-demand.png`, "Search days": all 7 are weekdays with multipliers 0.82-1.08, while the history peaks near 1.5x on holiday eves; the peak-day tile gives one network figure (186 vehicles, 100%).
   Smallest fix: add the peak day to the day view's day selector, so I can watch the holiday-eve morning and see which stores go amber.
5. **Low - I cannot find my own store.**
   Evidence: `ceo-1440-day.png`; the day animation shows 1,955 dots with no hover and no search, so "is my truck before noon" cannot be answered even for the one day shown.
   Smallest fix: hover on a store gives its ID, DC today and after, and arrival time in both networks.

## The 3 changes that would most improve the demo

1. **Make the answer a decision.**
   Overview tile: "keep 4, close 8, open 8"; the saving split into redraw (-9.5 M) and relocate (+541.8 M, of which 385 M is fewer relays); the scale and model-risk caveat; one "approve today" line.
2. **Make the live solve able to fail, and make the labels honest.**
   Add a vehicle-limit slider with uncovered stores shown in red, re-solve on change, use a per-view header pill (live versus precomputed), and show the engine state as "live · in-browser (simplified)".
3. **Add a store-level lens.**
   A moved-stores map layer, the worst-store and rural-store arrival distribution for current against recommended, relay-served stores marked, and the peak day in the day view; together with label plates, nice ticks and the badge and contrast fixes, this answers the store owner and the UX review in one pass.
