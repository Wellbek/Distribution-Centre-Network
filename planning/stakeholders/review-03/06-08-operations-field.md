# Review 03 · 06 Delivery Operations and 08 Field Manager

Reviewers: personas 06 (Head of Delivery Operations) and 08 (DC field manager), acting together.
Material: `code/results/full/registry.json` (Spark run 2, generated 2026-10-20T10:19:15, seed 437), `code/results/full/tables/*`, `code/dcn/routing.py`, `evaluate.py`, `config.py`, `code/osrm/`, `static/demo.template.html`, `planning/DECISIONS.md`, `planning/WORK_LOG.md` "Spark run 2", brief Sections 2.1-2.7.
Method: read-only; light Python on the registry and the CSVs; no pipeline run.
The far-store estimates in Section 2 are back-of-envelope (greedy nearest-neighbour), labelled as such, and must be replaced by a rerun.

> 06: "A truck that drives 330 km to drop two cages is not a route, it is a symptom."
> 08: "Show me the road, not the crow."

## 1. The two questions the user asked

### 1.1 "So many trucks, is that right?"

Short answer: for 578 of the 672 routes, yes; for the other 94, no.

Arithmetic on the shown recommended weekday (`show.recommended_weekday`, 2026-11-04, 13 DCs):

| Quantity | Value | Source |
|---|---|---|
| Stores, cages | 9,718 stores, 20,444 cages | routes in `show.recommended_weekday` |
| Load lower bound | ceil(20,444 / 48) = 426 vehicles | same |
| Stop lower bound | ceil(9,718 / 25) = 389 vehicles | same |
| Routes driven | 672 (1.58x the load bound) | same |
| Single-stop routes | 99, of which 94 "violates limit" | same |
| Routes without the 94 far stores | 578 routes for 9,624 stores, load bound 422 (1.37x) | same |
| Those 578: stops, km, load | 16.7 stops, 122.8 km, 35.0 cages (73% full), median return 12:13 | same |
| Those 578: time used | 3.51 h driving + 4.16 h stopping = 7.67 h of the 8.5 h between 04:00 and 12:30 | same |
| Peak day (2027-09-13) | 849 routes for 31,504 cages, load bound 657 | `show.recommended_peak` |
| Owned fleet | 713, between weekday 672 and peak 849 | `finals.recommended.owned` |
| Mean vehicles/day over 28 final days | 700.9 | `finals.recommended.vehicles_day` |

Reading: outside the far stores the fleet is time-limited, not inflated.
A 15-minute stop and 35 km/h leave room for about 16-17 stores in an 8.5-hour day, which is what the routes do, and the census agrees: shift 216.5, load 274.5, geometry 53.3, stops 23.6, km 36.2, clock 2.9 routes a day (`finals.recommended.census`).
Multi-trip is not a lever under the brief's 04:00-07:00 departure window: only 4 of 672 weekday routes are back by 07:00 (16 of 849 on the peak day), so a second departure inside the window is almost never possible.
Say this in the balance table; it answers question 3 of persona 06.

The 94 far stores are the problem.
Each one is a whole truck, a second driver-day and 244-460 km of driving for about 2 cages (mean load 2.03).
By DC: Jecheon Bongyang (site 28) 87 on the shown day (91 single-stop routes in total), Hanam 5, Gyeongsan 2.
The 87 Jecheon stores are the Gangwon east coast (lat 36.68-38.44, lon 128.44-129.42): Gangneung, Sokcho, Donghae, Samcheok, Uljin.
They sit in tight clusters: median nearest-neighbour 1.5 km (crow), 172 cages in total, one-way road median 163 km, first arrival median 08:39 and at the latest 10:34, return as late as 17:24.
Today's network has the same pattern, larger: 227 far single-stop routes (Wonju 114, Iksan 55, Gwangju 42, Busan Gangseo 8, Gyeongsan 7, Daejeon 1), median nearest-neighbour 1.3-5.3 km within each group.
The history table confirms it: 28.7% of all 300,778 vehicle-days are single-stop routes, 236.8 a day, 252-384 km (5th-95th percentile), DC07 alone 117.3 a day (`vehicle_days.csv.gz`).

No dispatcher would send 87 trucks to 87 stores in the same three coastal towns.

### 1.2 "Straight lines for streets, is this right?"

The numbers are not wrong: every cost uses OSRM v6.0.0 road km (car profile, ferries excluded, extract 2026-10-18T20:25:06Z, `road_cache.npz` meta).
The picture is wrong where it matters most.
The far routes from Jecheon to the east coast are drawn as straight lines of about 101 km (crow, median) across the Taebaek range, while the truck drives 163 km by road (road/crow 1.60, range 1.20-1.95 over the 94 far routes).
That is exactly the river-and-mountain story persona 08 raised at the meeting, and the map hides it.
The legend says "lines are straight between stops (road geometry follows with OSRM)" (`demo.template.html` line 182), which reads as a promise.
`results/full/shapes.json` now exists (2.5 MB, 27,173 legs, 0 missing, built against registry 2026-10-20T10:19:15), but neither `build_demo.py` nor the template references it, so the current page still draws straight lines.
The brief allows "points and lines on latitude and longitude" (Section 6.3), so straight lines are acceptable if honestly labelled; persona 08's checklist accepts "labelled as straight segments".
The fidelity needed: road geometry for the two shown days (27,173 unique legs across the four `show` route sets), truck animation along the polyline, and a hover that shows road km next to crow km; the live solve can stay straight with a label.

## 2. What a relay route would change

### 2.1 Is the current rule realistic?

No.
The rule (D-019, D-027, `evaluate.py`): the savings merge rejects every merge that pushes a route over 250 km or past the shift, so a store beyond about 125 km road from its DC stays a one-store route, which is then charged one vehicle, one relay driver-day (180,822 KRW) and its fuel, and counted as not on time.
Three things are off.

1. Real dispatch would combine the cluster: a long stem out, then a normal multi-stop route, with a second driver or a transfer point.
2. The far stores are delivered before noon (latest first arrival 10:34 on the shown day), yet `evaluate.py` sets `good = 0` for any "violates limit" route, so they count as late.
3. D-027's rationale says "a second driver, not a whole extra truck", but `V` still counts each far store as its own truck, so each costs a truck plus two drivers.

### 2.2 A relay route class (recommended)

A relay route: same 48 cages, 25 stops and hard 12:00 deadline; km cap and shift relaxed (two drivers, for example 500 km and return by 18:00); charged a vehicle-day, one extra driver-day and its fuel; built by the same savings merge but only among stores the normal limits cannot reach; on-time counted by the clock.
Greedy estimate (nearest-neighbour from the nearest far store, OSRM stem km from the registry, store-to-store crow km x 1.54, the cache's `ratio_nn_median`, 35 km/h):

| Network, shown weekday | Far single-stop routes | Combined relay routes | Vehicles saved | km/day saved | Late after the change |
|---|---|---|---|---|---|
| Today (12 DCs) | 227 | 36 | 191 | 56,425 | 0 |
| Recommended (13 DCs) | 94 | 13 | 81 | 26,043 | 0 |

Monthly effect (vehicle at 5.5 M, relay at 180,822 x 30.42, fuel at 350 KRW/km x 30.42; weekday scaled to the month, so indicative only):

| Network | Fleet | Relay | Fuel | Total change | E now | E estimated |
|---|---|---|---|---|---|---|
| Today | -1,050 M | -1,051 M | -601 M | -2,702 M | 9,383 M | about 6,681 M |
| Recommended | -446 M | -446 M | -277 M | -1,168 M | 7,607 M | about 6,439 M |

What it changes:

- **Trucks:** about 591 routes on the recommended weekday instead of 672, and about 608 instead of 799 for today's network.
- **Service:** today's worst-day service is 97.66% = 1 - 227/9,718 exactly (`finals.baseline.service_min` 0.97664). Every far store arrives before noon, so with the clock deciding, today's network meets 98%. The "today fails 98%" finding is an artefact of the rule, not of the operation. k = 8 is in the same position: it fails at 97.96% because of 198 far routes a day (`sweep`), so the Strategy statement "cut from 12 to 8" is being judged by the artefact.
- **Saving:** 1,776 M a month falls to roughly 240 M, because today's network carries 2.4 times as many far stores as the recommended one. The reversal row (0 / 180,822 / 550,000 KRW) only changes the price of a far store, never the one-truck-per-store structure, so it does not test this.
- **k\*:** applying the same per-far-store saving (12.4 M a month, the recommended network's figure) to each sweep row gives k = 8: 6,183 M, k = 9: 6,063 M, k = 10: 6,189 M, k = 13: 6,280 M. This is a crude extrapolation (far stores at k = 8-9 may be less clustered than the east coast), but it says k\* could move from 13 to around 9 and the sweep could flip from "13 DCs" to "9-10 DCs".

The alternative real-world answer is a satellite transfer point or a small east-coast DC exempt from the 500-store minimum (D-044 dropped Gangneung with 125 stores).
Either needs its own cost row; the relay route class is the smallest change that stays inside the brief.

## 3. Findings, ranked

### Blockers

**B1. Far stores: one truck per store, and counted late although on time.**
Evidence: Sections 1.1 and 2.
Change:

- In `routing.solve`, run a second savings pass over the stores whose single route violates the limits, with relaxed relay `Params` (km and shift), keeping 48 cages, 25 stops and the 12:00 deadline; label these routes `relay`.
- In `evaluate.py`, count a relay route's stores on time by their arrival (`arr <= deadline`), not `good = 0`.
- Charge each relay route one vehicle-day plus one relay driver-day plus fuel, and drop the claim in D-027 that no extra truck is charged, or make it true.
- Rerun full and reduced, then update every headline number (saving, k\*, service of today's network, waterfall, sweep) and record a D-entry.
- Add a reversal row that switches the structure (single-store rule versus relay class), not only the price.

**B2. Outcome tables contradict the registry on service.**
`deliveries.csv.gz` has 3,502,822 rows and none delivered after 12:00, while `history_ops.service` says 97.6% before noon.
A grader who opens the table sees 100% on time; a grader who opens the registry sees a network that fails.
Change: after B1 this should agree by construction; otherwise add a `relay` flag column to `deliveries` and `vehicle_days` and say in the README which deliveries count as late and why.

### Majors

**M1. The departure-wave check moves k\* on an uncalibrated dock rule.**
Docks = ceil(1,400 x 817.3 / 9,718 / 4) = 30 for every DC, with 1 hour of loading per vehicle (D-054).
That rule does not reproduce today's operation, which by the brief is a fact: today's network overflows by 36.7 departures a day (`waves.baseline.dock_over_day`).
At k = 13 the overflow is 30 departures a day; k\* jumps to 14 at +524 M a month on the search days (7,961 versus 7,436 M with waves), which is far more than a few extra docks would cost.
Change:

- Calibrate docks so that today's network dispatches without overflow.
- Price overflow rather than declaring it infeasible: an extra dock, or a 07:00+ departure counted by the clock.
- Sweep loading time (30 versus 60 minutes) and report the break-even dock count for k = 13, as the WORK_LOG already plans.
- The plain evaluation still sends every truck at 04:00: all 300,778 `vehicle_days` rows have `departed_at` = 04:00, which persona 06 lists as a red flag. State this next to every headline number, or run the final comparison with waves.

**M2. The break is in the wrong place and probably too short.**
`ok_time` adds `BREAK_H` = 0.5 h to the return time; the break never delays a delivery.
A driver working 04:00-12:00 without a break is not a legal morning; the break must fall inside the sequence (after about 4 hours of work), so every later arrival moves 30 minutes.
The config comment says "30 min per 4 h", which over a 10-hour shift is 1 hour; the Labor Standards Act (Article 54) requires at least 1 hour for 8 hours of work.
Today the noon clock binds 2.9 of 700.9 routes a day (0.4%) and the shift 216.5 (31%): the window hardly shapes the fleet, the 12:30 return does.
Change: insert the break in `walk` after the stop that crosses 4 hours from the shift start; check 30 versus 60 minutes; rewrite the census text to say the shift, not the window, is what limits large territories.

**M3. One flat speed of 35 km/h for city streets and expressways.**
The cache is "distances only" (cache meta `profile`).
A 163 km stem from Jecheon to Gangneung by expressway takes a truck about 2.5 hours, not the model's 4.7 hours; city legs between 04:00 and 07:00 at 35 km/h are plausible.
The flat speed makes long stems look unreachable and so biases toward more DCs, the decision itself.
Change: rebuild the cache with OSRM `annotations=duration,distance`, scale car durations to a truck (for example x 1.25 with an 80 km/h cap), or use two speeds (stem legs 60 km/h, in-territory 35 km/h); rerun the final candidates as a balance-table check.

**M4. The demo map draws the crow, not the road.**
Evidence: Section 1.2.
Change: `shapes.json` is built (27,173 legs, 2.5 MB, small enough to embed); have `build_demo.py` embed it, draw legs as decoded polylines, and animate trucks along the polyline at the route's own speed.
Rebuild `shapes.json` whenever the registry changes (B1 will change the routes), and have `build_demo.py` refuse a `shapes.json` whose `meta.registry` differs from the registry's `generated` stamp.
Until then, replace the legend text with "straight segments for display; every km and time uses OSRM road distance" and show road km against crow km on hover for each leg.
Add the three named examples persona 08 asked for (for example Jecheon to the east coast, a Han river crossing, a Nakdong crossing) with their road/crow ratios.

**M5. Spot trucks are unlimited and nobody says so.**
Peak day: 849 routes against 713 owned, so 136 spot trucks at 04:00 (`show.recommended_peak`).
History: up to 174 spot trucks on one day (2025-10-04), more than 50 on 28 days, 95th percentile 69 (`spot_hires.csv`).
Change: state the assumed spot availability per DC (for example 10-15% of the owned fleet), add a shortage cost above it (stock-out or late), and report the peak-day spot need for the recommended network next to the fleet.

**M6. The outcome tables do not look like a real operation.**
In `vehicle_days.csv.gz`: 236.8 single-stop routes a day, 229.6 vehicle-days a day over the 250 km limit, 103.1 a day returning after 13:00, every departure at 04:00, and trucks such as DC01-V001 on 2025-10-01 (2 stops, 4.1 km, back at 04:37) that use a driver-day for 37 minutes.
A manager reading these tables would not recognise the operation.
Change: B1, M1 and M2 fix most of this; label over-limit rows explicitly, and let near-DC short routes take a second trip when they are back before 07:00.

### Minors

**m1.** About 9 routes on the shown weekday are under 24 cages, back by 09:00 and not far (for example 5 stops, 20 cages, 8.5 km, back 05:30); a final relocate pass would merge some of them; report the share.
**m2.** 18.1% of deliveries are zero cages and still take a full 15-minute stop; either say that the stop is for empties collection, or use a fixed plus per-cage stop time (for example 8 minutes plus 2 per cage) as a sensitivity.
**m3.** The car profile routes a 48-cage truck; state that height, weight and alley restrictions are not modelled and which way that biases km.
**m4.** Report the census as shares per k, and define "geometry" (no limit within one store's room) in the legend; it is 53.3 routes a day, which a dispatcher will ask about.
**m5.** The 250 km and 25-stop caps cannot both be reached in an 8.5-hour day: 25 stops take 6.25 hours, which leaves 2.25 hours, or 79 km at 35 km/h; the 61 routes with 25 stops drive a median 63.1 km; say this in the formulation, since the brief asks for exactly this check (Section 5).
**m6.** The distance model for non-cached store pairs has a 19.9% median error at 1-10 km (p90 44.0%, cache meta `test_error`); D-040 says 93% of route legs use OSRM values; quote both next to each other in the balance table.

## 4. Checklists

Persona 06:

- [x] Binding-constraint census: present per network (`census`), not yet per k as shares (m4).
- [~] Departure-wave check: present, but the dock rule fails on today's network (M1).
- [~] Holiday-day case: peak-day routes are shown; spot availability is not addressed (M5).
- [~] Driver breaks, empties, multi-trip: break modelled at the route's end (M2); empties not modelled; multi-trip shown to be irrelevant in the 04:00-07:00 window (Section 1.1), which should be written down.
- [ ] Red flag "routes that violate a limit": 94 a day in the recommended network, 227 in today's (B1).

Persona 08:

- [x] Distance source, version, extract date and profile stated (cache meta, `osrm/README.md`).
- [ ] Detour-ratio map layer and three named examples (M4).
- [x] Calibration error reported (cache meta `test_error`).
- [~] Routes in the demo drawn on road geometry, or labelled as straight segments: labelled, but with a promise the page cannot keep (M4).
- [ ] Red flag "a car profile with no comment on trucks" (m3).

## 5. Verdict

The lower level is sound where stores are dense: routes are time-limited, about 16-17 stops for 35 cages, and the arithmetic holds.
The far-store rule is not sound, and it is not a corner case: it carries about 2.7 billion KRW a month of today's cost, makes today's network miss 98% on paper, and probably decides both the saving and k\*.
Fix B1 and B2 before any number goes into the proposal; then M1-M3, because each one moves k\* and none has been run.
