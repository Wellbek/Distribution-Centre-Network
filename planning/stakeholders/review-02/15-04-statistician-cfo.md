# Review 02 - Statistician (15) and CFO (04) on v0.1

Scope: assignment.md 2.2, 2.6, R2, R5; MIDTERM_BRAIN.md 4, 10, 12; code/dcn/demand.py, evaluate.py, pipeline.py, config.py; code/results/reduced/registry.json (generated 2026-10-19T13:46:33, seed 437, fraction 0.2, 1,955 planning stores); demo.html Overview and Demand views.
Checks were quick refits only (make_world(0.2), make_history, fit, sample_days with the pipeline seeds); no search or routing was rerun.
All money figures are KRW per month on the reduced instance unless stated.

## Statistician (15)

"Is that interval over days, over parameters, or over both?"

### S1 - High - The prior strength is defaulted, and about six times too strong

Evidence: config.py:37 fixes `PRIOR_STRENGTH = 14.0` store-days, while MIDTERM_BRAIN.md 10.2 promises empirical Bayes.
A moment estimate on the 365-day stores of the generated history gives between-store variance about 1.0 and b = mean / variance = 2.3 (residential), 2.5 (office), 2.3 (mixed), 2.0 (roadside).
With b = 14 a 22-day store keeps only 61% data weight instead of 90%; the store found (22 days, 53 cages, exposure 22.2) gets posterior mean 2.35 against a truth of 2.11.
The reduced instance has only 3 stores with 10-30 days of history, so the R2 "short-history" story rests on almost nothing, and registry `r2.example` shows a 64-day store, not a 20-day one.
Smallest fix: set b per type by the moment estimate above inside `fit` (demand.py:115), report it, and show prior, data and posterior for a store with about 20 days drawn from the full instance or a deliberately truncated history.

### S2 - High - The saving interval covers only daily fuel and spot noise, with the fleet fixed in-sample

Evidence: pipeline.py:19-24 bootstraps the mean of `daily_total` differences, and evaluate.py:92 adds (fixed + fleet) / 30.42 as a constant to every day.
From registry `finals`, the saving of 532.3 M splits into fixed 19.8, fleet 82.5, relay penalty 384.8, fuel 47.0 and spot -1.8.
Penalty is exactly 48 versus 25 over-limit routes on every one of the 28 days (`over_limit_day` 48.0 and 25.0, census 1,344 = 48 x 28), so 487.1 M (91.5%) of the saving is constant across days and the interval can only be about plus or minus 3.6 M.
The fleet is sized on the same 28 days it is scored on (pipeline.py:119-124 via evaluate.py:86), and the bootstrap never resizes it.
It excludes: the fleet-quantile estimate, posterior uncertainty in the store rates and the shared calendar coefficients, the routing heuristic, the distance model, the cost parameters and the generator seed.
Smallest fix: label the interval "over sampled days, fleet and parameters fixed"; inside each bootstrap replicate recompute the 0.671 quantile per DC from the resampled days; add an outer loop over a few posterior draws of (lambda, beta) so the interval is over days and parameters.

### S3 - Medium - Parameter uncertainty is drawn per day, so it washes out instead of propagating

Evidence: demand.py:141 draws `lam = rng.gamma(a, 1/b)` afresh on each sampled day, and `beta`, `phi`, `sigma` are plug-in point estimates (demand.py:107-112, 133-135).
A store's rate is one unknown for the whole planning year, so independent per-day draws turn parameter uncertainty into extra day-to-day noise that averages away over 28 days; MIDTERM_BRAIN.md 12 claims "parameter uncertainty enters through posterior draws", which it does not in any interval.
The calendar coefficients are shared by every store, so their error does not cancel at a DC.
Smallest fix: draw lambda (and, by a residual bootstrap of the log-exposure regression, beta) once per replicate and hold it across that replicate's days; that is the outer loop of S2.

### S4 - Medium - The model is overdispersed and misses the summer peak, and there is no predictive check

Evidence: demand.py:73 generates store-day Gamma(8, 1/8) noise, but the predictive is Poisson given lambda (demand.py:142).
Refit residuals: store-day variance / mean = 1.35, and DC-day total residual variance is 1.6-1.9 times the Poisson value on the first three current DCs, so the predictive understates DC-level spread by roughly 25-35% in standard deviation and the 0.671 fleet quantile is set too low.
The two annual harmonics (demand.py:86) cannot follow the true 21-day-wide summer bump (demand.py:50): fitted calendar exposure is 3.7% low for residential and 6.2% low for roadside on day-of-year 190-220, in both history and planning year.
No posterior predictive check exists in the code or in the demo Demand view.
Smallest fix: replace the count draw by a negative binomial with a dispersion fitted from the residuals (one parameter), add a summer-bump term (or 4 harmonics) to `_design`, and plot replicated versus observed chain totals, weekday profile and holiday peaks.

### S5 - Medium - Search days are not representative and the R2 decomposition is two-way, not three-way

Evidence: registry `search_days` are 7 weekdays (chain multiplier 0.82-1.08); with a weekday share of 66.3% in the planning year, P(all 7 weekdays) = 0.056.
Fitted chain exposure is 0.969 on ordinary weekdays and 1.039 on other days, so the search scored candidates on a light, office-tilted week while the finals have 18 weekdays, 6 weekend days, 3 holiday eves and 1 holiday.
Held-out days share 3 of 14 calendar dates with the final days (2026-11-16, 2027-01-07, 2027-03-15), so "days the search never saw" holds only for the search set.
R2 (pipeline.py:134-137) compares sampled 1,938.8, expected counts 1,933.4 and one average day 1,928.1 M: `q_mean` keeps each day's chain shock (demand.py:144), so calendar and shock are confounded, and with 7 weekdays the calendar part is barely exercised; the 5.3 and 10.7 M gaps have no interval and are within the plausible noise of a 7-day estimate.
Smallest fix: stratify the 7 search days (5 weekday, 2 weekend, or calendar quantiles), draw held-out dates disjoint from final dates, and add the missing comparison "expected counts with shock = 1", run on the 28 final days.

### S6 - Low - Exposure estimation details that should be stated

Evidence: demand.py:98-104 divides by each store's own mean over open days, so stores opened in summer carry a biased denominator; the fitted shock still tracks the truth well (correlation 0.92, stationary sd 0.071 versus true 0.070, phi 0.45 versus empirical 0.45).
`average_day` and `q_mean` route fractional cages (demand.py:144, 154), which packs vehicles slightly tighter than integer days.
`peak_day` hard-codes the label "peak (holiday eve)" (demand.py:166) and sets the shock to 1.
Smallest fix: one sentence each in the R2 write-up; take the argmax label from the calendar.

## CFO (04)

"Monthly, annual, or one-off?" "What is the interval on that?"

### C1 - High - 72% of the saving is the relay penalty, an assumption priced at the spot rate

Evidence: evaluate.py:90 charges `C.SPOT_DAY * OVER` for every route that "violates limit" (tagged [ASSUMPTION]); baseline penalty 803.0 M = 48 routes x 550,000 x 30.42, recommended 418.2 M = 25 routes, difference 384.8 of 532.3 M.
Service is 100% on every day for both networks, so the late and stock-out penalties never trigger and `STOCKOUT_PEN` (config.py:13) is unused.
These routes are single far stores (a route over 250 km cannot be merged), each costing an owned vehicle plus a 550,000 KRW relay every day, about 25 M per month to deliver about 2.2 cages a day; 48 of the baseline's 177 vehicles (27%) are such one-store routes.
The ex-penalty saving is 147.5 M (5.8% of the baseline, not 21.0%).
Smallest fix: show the saving with and without the relay line, cost far stores as a multi-stop relay route (or a stock-out at 500,000) and state which, and list the far stores on the map so the board sees what drives the result.

### C2 - High - The headline is a reduced-instance number with no "1 store in 5" label

Evidence: demo.html:339-341 shows "Saving, 28 final days 532 M/month" and the baseline next to it; nothing on the Overview tiles says 1,955 stores or fraction 0.2 (the scaling is mentioned only at demo.html:679 and 701).
Fixed costs scale by 0.2 but vehicles do not scale cleanly: 177 vehicles serve 1,955 stores (11 per vehicle) against about 21.8 per load in MIDTERM_BRAIN.md 4.
A board member will read 532 M as the chain-wide saving, or multiply it by 5.
Smallest fix: add "reduced instance, 1,955 of about 10,000 stores; not scaled to the chain" to each money tile, and give a per-store saving (272,000 KRW per store per month) as the scale-free figure.

### C3 - High - The interval looks precise because almost nothing in it is random

Evidence: 528.7 to 535.8 M (final) and 529.5 to 536.8 M (held-out) on 532.3 and 533.1 M; see S2: 487.1 M is deterministic given the fleet, the far-store geometry and the cost rates.
The quantities that actually move the answer are not in the interval: the spot rate (relay saving scales one-for-one, so +30% spot adds about +115 M), the detour factor 1.30/1.45 that decides which stores lie beyond 125 km road (meta `distance_model` says "placeholder until the OSRM cache"), and the fleet quantile estimated from 28 days.
Smallest fix: caption the interval "day-to-day only"; add a one-way table for spot rate +/-30%, detour factor 1.2-1.5 and the relay assumption on/off, each with the saving and its sign.

### C4 - Medium - Costs are in the right units, but the peak-day tile mixes a day with a month

Evidence: units are consistent (config.py:8-14: KRW per month, KRW per day, 365/12 = 30.42 days; daily_total x 30.42 = total, evaluate.py:91-92).
demo.html:545 shows the peak day's spot as "468 M/month-equivalent": that is one day's 28 spot trucks (15.4 M KRW) times 30.42, which no month incurs.
The live view's "Daily cost" (demo.html:660) omits the relay line that drives the result.
Smallest fix: show the peak day in KRW for that day (15.4 M) and include relay cost in the live daily cost.

### C5 - Medium - No payback, no transition cost, and the saving decomposition has a negative step unexplained

Evidence: MIDTERM_BRAIN.md 12 plans payback and break-evens; registry has none.
`reassigned12` (same 12 sites, LP assignment) costs 2,543.5 M, 9.5 M more than the baseline's 2,533.9 M, because the LP minimises a reach proxy (evaluate.py:29-33) under 100-280 bounds that the baseline is exempt from.
The recommendation keeps 12 DCs at different sites (fixed 350.7 versus 370.5 M), so lease exits and relocations are real one-off costs.
Smallest fix: one payback line, months = one-off cost / monthly saving with and without relay (for example 1 B KRW per relocated site), and one sentence explaining the negative reassignment step.

### C6 - Low - Fleet quantile is justified, but its sampling error is not

Evidence: config.py:28 gives the newsvendor fractile 1 - 180,822 / 550,000 = 0.671, as MIDTERM_BRAIN.md 4 argues; good.
With 7 search days it is the 5th order statistic per DC, with 28 days the 19th, and the held-out run reuses the 28-day fleet (pipeline.py:126-128), which is correct.
It assumes unlimited spot supply at a flat rate, and the predictive is under-dispersed (S4), so the owned fleet is probably a vehicle or so short per DC.
Smallest fix: report owned vehicles per DC with a bootstrap range, and note the unlimited-spot assumption next to the fractile.
