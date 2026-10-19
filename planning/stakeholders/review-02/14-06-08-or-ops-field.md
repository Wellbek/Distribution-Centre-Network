# Review 02 - OR scientist, delivery operations, field manager (v0.1 code)

Scope: assignment.md 2.3-3.4, MIDTERM_BRAIN.md 4, 7, 8, 9, 13, code/dcn/{routing,evaluate,search,geo,config}.py, code/results/reduced/registry.json, demo.html.
No pipeline was re-run.
Measurements came from single routing.solve calls and an exact subset DP; the script is at /tmp/claude-1000/-home-louis-GitHub-Repos-KAIST-GSDS-IE-437-Data-Driven-Decision-Making-and-Control/dcf6814e-5a68-4e90-b25e-0f72fb5cc916/scratchpad/gap.py and gap2.py.

## What is correct

Every merge and every 2-opt move is checked against load, stops, 250 km, last arrival by 12:00 and return by 13:00 (routing.py:43-45, 98-104, 77).
Arrival times are monotone, so checking only the last arrival is enough.
The time model (depart 04:00, leg/35 km/h, 15 min per stop, return leg included in km) matches the brief.
In the showcase day, every multi-stop route is within limits: max 250.0 km, 25 stops, 48 cages, last arrival 11:59, return 12:59.
Every limit violation is a single-store route that is infeasible on its own.

## 14 - OR scientist

1. **High - the heuristic misses vehicles, and the vehicle count is what drives cost.**
   I solved 20 instances exactly: 11 stores drawn at random within 120 km of a recommended DC, with a Held-Karp route DP and a set-partition DP, lexicographic on vehicles then km.
   Clarke-Wright + 2-opt used one vehicle too many on 2 of the 20 instances (3 vs 2, 4 vs 3), which is 2 extra on 44 optimal vehicles (+4.5%).
   On the instances where the vehicle count matched, km was +0.37% on average and +4.8% at worst.
   On 18 clustered instances (9 and 12 nearest stores), the vehicle count was always optimal and km was within +0.9% at the median and +10.9% at worst.
   A 4.5% vehicle error is about 7 vehicles, or 40 M KRW/month, at k = 12, which is larger than several gaps between neighbouring k in the sweep.
   Fix: add a route-elimination or relocate pass between routes (planned in plan 7.3 but not built) and report this exact table by k.
2. **High - the k curve is shaped by the over-limit penalty, not by the routing.**
   The penalty term is 418 M (k = 12) to 2,911 M (k = 7) per month, and it is entirely 550,000 KRW per over-limit singleton (evaluate.py:90).
   Total minus penalty, best per k: k = 8 1,734; 9 1,533; 10 1,639; 11 1,531; 12 1,521; 13 1,556; 14 1,655 M.
   That is flat within 1% from 9 to 12, and only 1-7 evaluations per k back each point.
   The recommendation "k = 12" therefore rests on the penalty and on search luck.
   Fix: report the sweep without the penalty term and with the best G1 seed per k evaluated on common days, and show per-k search noise.
3. **Medium - the binding labels are slack heuristics and miss the shift.**
   _binding (routing.py:125-137) has no shift-end test.
   Taking the smallest slack in hours on the recommended showcase day, the 13:00 return is the tightest constraint on 54 of 126 feasible routes, and none of them is labelled shift: 27 are labelled "geometry", 19 "clock" and 7 "km".
   The 12:00 deadline is the tightest on only 20 routes.
   Fix: compute all five slacks (load, stops, km, deadline, shift) in common units and label the smallest; better still, label by which constraint rejected the last merge attempt.
4. **Low - the k-NN savings list drops pairs.**
   routing.py:57 keeps pair (i, j) only if i < j and j is in NN(i), so a pair where only i is in NN(j) is lost.
   Fix: use np.minimum / np.maximum on (i, j) before np.unique.
5. **Low - the LP's integrality is assumed, not checked.**
   The matrix is TU, but evaluate.py:53 rounds by argmax, and only the upper-bound duals are reported.
   Fix: assert that max |z - round(z)| < 1e-6, and report the lower-bound duals too.

## 06 - Head of Delivery Operations

1. **Critical - over-limit stores are charged three times, which inflates the saving.**
   Every store more than about 125 road km from its DC becomes its own route and is counted in V, in the owned fleet and in fuel, and is also charged a 550,000 KRW "relay".
   That is 48 singletons per day in the baseline (35 of them at Wonju Munmak; km 250-413) and 25 in the recommended network (19 at Yeongju Munsu).
   The penalty is 803 M (baseline) vs 418 M (recommended), so 385 M of the 532 M monthly saving (72%) is relay penalty.
   No dispatcher sends 35 trucks to 35 Gangneung stores; one or two relay or satellite routes would do it.
   Fix: model a relay as a line-haul to a transfer point plus a normal route from there, or forbid such assignments in the LP (they are a design failure, not a cost); never count a store as both a fleet vehicle and a relay.
2. **High - service level 100% hides limit violations.**
   The finals report service_mean = 1.0 even though 25-48 routes per day exceed 250 km, because service counts only arrivals before noon (routing.py:120).
   Fix: report "deliveries on feasible routes" next to service, and list the over-limit count per network in every table.
3. **High - the shift end, not noon, is what limits the day, and there is no break in it.**
   With all vehicles leaving at 04:00 and returning by 13:00, a route whose last store is more than 26 km from the DC is limited by the return, not the deadline (see OR 3).
   The plan's assumption that the break is "taken at the DC" (plan 7.4) does not fit 9 hours on the road; the Labour Standards Act requires a 1 h break in an 8 h day.
   Fix: put the break inside the shift (SHIFT_END 12:00 or a 30-60 min break inside walk) and say so in the balance table.
4. **Medium - everything leaves at 04:00 and spot supply is unlimited.**
   Up to 40 vehicles per DC leave at the same minute in the reduced instance.
   The peak day needs about 28 spot trucks at 04:00 (468 M/month equivalent) on top of 158 owned.
   Fix: run the departure-wave check from the plan (dock throughput, 04:00-06:00) and a cap on spot trucks before claiming k*.
5. **Medium - routes run at half load because of thinning.**
   The recommended showcase day uses 151 routes for 1,955 stores, against a load bound of 77, with a mean of 13 stops and 24.4 cages per route.
   At full density, routes should be load-bound at about 22 stops.
   The fleet per store is therefore about doubled, and the clock binds much sooner than it would in the real chain (plan section 4 already predicted this).
   Fix: use thinning option (ii), merging 5 neighbours into one stop with 5x stop time, or check one DC at full density, and record the distortion in the balance table.

## 08 - DC field manager

1. **High - the baseline is a strawman, and the brief penalises that under R5.**
   A chain that grew over decades would not leave 2.5% of its stores (about 245 at full scale) beyond its own trucks' daily km limit.
   In the current set, nothing covers the Gangwon east coast (Gangneung, Sokcho, Donghae, Samcheok) or the Uljin/Yeongdeok coast.
   Fix: place current DCs so that every store is within about 120 road km, for example a Gangneung DC instead of one of the four capital-region DCs, and justify each site.
2. **High - a single mountain factor overstates expressway legs.**
   geo.py:171 applies x1.45 to every pair that touches Gangwon or North Gyeongsang.
   Wonju Munmak to Gangneung is about 96 km on the map, so the model says about 139 km.
   From recollection, the Yeongdong Expressway is closer to 110 km, but this was not checked against a routing engine.
   This one factor is what turns most of Wonju's east-coast stores into over-limit routes.
   Fix: calibrate on an OSRM sample with detour falling with distance, before trusting any over-limit count.
3. **Medium - 35 km/h is applied to motorway out-legs.**
   A 100 km out-leg costs 2.9 h, which pushes the shift and deadline limits onto far territories and favours more DCs.
   Fix: use two speeds (line-haul to the first stop, local between stops), or cover it in the 30-45 km/h check.
4. **Medium - the demo draws straight lines without saying so.**
   demo.html has no "straight" or "map line" label, and "relay" never appears even though the cost hinges on it.
   Fix: add a one-line legend ("legs drawn as straight segments; road km = map km x factor") and mark over-limit singletons in red.
5. **Low - some site names do not match their coordinates.**
   S31 "Sejong Bugang" (36.53, 127.25) lies about 11 km west of Bugang-myeon.
   S30 "Okcheon Cheongsan" sits at Okcheon town, not Cheongsan.
   S34 "Seosan Daesan" sits at Seosan city, not Daesan.
   DC04 Hanam Gamil is now a housing district.
   Fix: correct the coordinates or the names, and prefer industrial or logistics zones.
