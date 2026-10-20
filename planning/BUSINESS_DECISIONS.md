# Business decisions the model cannot make

Rolling list of operating choices the network design rests on but the company has to decide.
Each item names what we assumed, why, what it changes, and where the proposal and the demo must flag it.
User instruction 2026-10-20: realistic workarounds (two drivers, longer shifts) are modelled, disclaimed in the demo and listed here for the proposal.

| # | Decision | What the model assumes | Why | What it changes | Flag in |
|---|---|---|---|---|---|
| B-01 | Two-driver (relay) vehicles for stores beyond one driver's 250 km day | Far stores share multi-stop routes with a second driver: up to 500 km, on duty until 19:00, noon deadline unchanged; each relay route pays one extra driver-day (180,822 KRW) | Brief limit is "about 250 km per vehicle per day within a 10-hour shift"; real chains run team drivers or regional cross-docks for remote stores | Number of vehicles, relay cost, service by the clock; the price is swept (0, driver-day, spot rate) | Demo map legend and live solve; proposal risks |
| B-02 | Dock count per DC | Docks for a DC at the 1,400-store cap dispatching today's vehicles per store in four hourly waves (about 30); checked again with 25% more docks | Brief ties the cap to "loading docks and staff" | k* moved 13 to 14 in run 2 at 30 docks | Checks tab; proposal: confirm dock counts with DC managers |
| B-03 | Driver break | 30 min, added to the shift end, not to the delivery clock | Brief silent; Labor Standards Act Art. 54 asks 1 h for an 8 h+ working day | Shift-bound routes (about a third) lose stops if the break grows | Proposal assumptions |
| B-04 | Truck speed and stop time | 35 km/h flat, 15 min per stop including zero-cage stops | Brief teaching defaults | Swept as reversals (30/45 km/h, 10/20 min) | Checks tab reversal table |
| B-05 | Spot-truck availability | Unlimited at 550,000 KRW/day | Brief default | Peak days hire 130+ trucks; a cap would raise the owned fleet | Proposal risks |
| B-06 | Lease exits and one-off costs | Steady state only; no closure, move or opening cost | Brief asks monthly cost | Run 2 closed the DCs with the most lease left; payback and sequencing needed | Proposal: payback table, closure sequence |
| B-07 | Today's small regional DCs (below 500 stores) | Kept in the baseline (exempt), not allowed in new designs (500-1,400 bounds) | Brief §2.3 | New designs must serve the east coast from larger DCs or relay routes | Proposal: whether to keep a small east-coast DC outside the bounds |
