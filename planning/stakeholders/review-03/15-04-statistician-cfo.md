# Review 03 - Statistician (15) and CFO (04) on Spark run 2 (v0.3)

Reviewed: `code/results/full/registry.json` (generated 2026-10-20T10:19:15, seed 437), `code/dcn/demand.py`, `evaluate.py`, `pipeline.py`, `config.py`, `tables/dcs.csv`, `planning/WORK_LOG.md` "Spark run 2", `planning/DECISIONS.md`.
Method: reading plus small one-liners on the registry; nothing was re-run.

## Verdict in one paragraph

The 90% band 1,771-1,782 M is an honest number for what it measures: day-to-day sampling noise of a paired saving, conditional on one posterior draw of store rates, the cost defaults, the distances, the routing heuristic and the relay price.
Three independent day sets agree (search 7 days 1,769 M, final 28 days 1,776 M, held-out 14 days 1,778 M), so the narrowness is real and not a bootstrap artefact.
It is not the uncertainty of the saving, and a board member will read it as such.
41% of the saving (731.5 M) is the relay line, which is identical on every day (227 and 94 over-limit routes every day) and therefore contributes zero width to any day bootstrap, while the relay price alone moves the saving from 1,045 M to 3,270 M.
As CFO I cannot sign the recommendation because it closes the five DCs with the longest remaining leases (26-56 months) and keeps the four that expire first; the lease overhang is up to 32.6 bn KRW, about 18 months of saving, and no one-off cost or payback appears anywhere.
Every number in the WORK_LOG "Spark run 2" table matches the registry.

## Blockers

### B1 - The band is stated without its scope, next to a 3x wider assumption range

- Code: `_boot` resamples the 28 (or 14) realised days within calendar strata, re-sizes both fleets, and differences the totals; it never redraws rates, shocks or parameters.
- `sample_days` draws one rate vector `lam` per call, so inside one day set the posterior rate uncertainty is frozen.
- The relay line is deterministic: `over_limit_day` is 227.000 (baseline) and 94.000 (recommended) on every final day, so 731.5 M of the 1,776 M has no sampling variance at all.
- Paired decomposition (final 28 days, M KRW/month): fleet +709.5, relay +731.5, fuel +395.4, spot -4.7, fixed -55.5, penalty 0.0, total +1,776.2.
- Relay reversal (registry `reversal`): saving 1,044.7 / 1,776.2 / 3,269.7 M at 0 / 180,822 / 550,000 KRW per over-limit route-day.
- Fix: every place the band appears must say "over sampled days (paired, stratified bootstrap); excludes rate, parameter, cost, distance and relay-price uncertainty".
- Fix: put the relay range on the same line as the band, for example "1,776 M (days: 1,771-1,782; relay price 0 to spot rate: 1,045-3,270)".
- Fix: add the three-set agreement (1,769 / 1,776 / 1,778) as the evidence that day and rate-draw noise is small; it is the strongest statistical result in the run and is not reported.

### B2 - Lease timing and one-off costs are missing, and they point against the recommended sites

- The recommendation keeps DC01-04, DC08, DC10, DC12 and closes DC05, DC06, DC07, DC09, DC11.
- Months of lease left at plan start (2026-11-01), from `dcs.csv` `lease_expires_on`:

| DC | Site | Lease ends | Months left | Fixed (M/month) | Decision |
|---|---|---|---|---|---|
| DC01 | Yongin Giheung | 2027-03-31 | 5 | 180.0 | keep |
| DC10 | Gyeongsan Jillyang | 2027-09-30 | 11 | 132.0 | keep |
| DC04 | Hanam Gamil | 2027-12-31 | 14 | 180.0 | keep |
| DC02 | Gimpo Gochon | 2028-06-30 | 20 | 180.0 | keep |
| DC12 | Incheon Namdong | 2028-09-30 | 23 | 180.0 | keep |
| DC06 | Daejeon Daedeok | 2028-12-31 | 26 | 157.5 | close |
| DC08 | Iksan Wanggung | 2029-03-31 | 29 | 132.0 | keep |
| DC03 | Yangju Gwangjeok | 2029-09-30 | 35 | 180.0 | keep |
| DC05 | Cheonan Seobuk | 2030-03-31 | 41 | 132.0 | close |
| DC09 | Gwangju Pyeongdong | 2030-09-30 | 47 | 157.5 | close |
| DC11 | Busan Gangseo | 2031-03-31 | 53 | 157.5 | close |
| DC07 | Wonju Munmak | 2031-06-30 | 56 | 132.0 | close |

- If the whole monthly fixed cost of a closed DC runs to lease expiry, the overhang is 32,649 M KRW, which is 18.4 months of the 1,776 M saving.
- This is an upper bound: staff and equipment inside the 150 M are partly avoidable, and a lease may be sublet or bought out; state the share that is rent.
- Not modelled at all: opening six new sites (fit-out, racking, WMS), double running during cut-over, re-routing 4,053 moved stores, redundancy for closed-site staff.
- Fix (minimum): one slide and one registry block with "payback months = (lease overhang x rent share + one-off opening cost x 6) / monthly saving" as a small table over rent share 30/60/100% and opening cost 0/2/5 bn per DC.
- Fix (better, Section 7 extension): a closure sequence that closes DC06 first (Dec 2028) and moves the long-lease closures to their expiry dates, with the monthly saving reached step by step.
- The steady-state saving is reached only after mid-2031 unless leases are bought out; the proposal must say "monthly, steady state" every time it quotes 1,776 M.

## Majors

### M1 - The posterior predictive check is circular

- `replicate_history` uses `model["e_hist"]`, the in-sample ratio exposure per type and day, which already contains each day's realised chain shock.
- The replicated chain total therefore tracks the observed one by construction: correlation 0.998, log ratio sd 0.8%, against a history chain CV of 11.9%.
- It checks only the store-rate and kappa layer, not the calendar regression (`beta`) or the AR(1) shock model, which are what the planning days use.
- Fix: replicate with `calendar_multiplier(model, hist_cal)` times freshly simulated AR(1) shocks with the fitted phi and sigma, 50-100 replicates, and show the observed series inside the replicate band, plus a weekday panel and a holiday panel.
- Expected finding to discuss: the generator has phi 0.6, sigma 0.06 and 1.5% storm days at 0.85, while the fit gives phi 0.464 and sigma 0.061 (stationary sd 0.069 against the generator's 0.075, storms absent), so the planning days are slightly too calm.

### M2 - The average-day gap is measured on a light 7-day set, and the decomposition is two-way

- Registry `r2`: sampled 7,447.5 M, expected counts 7,435.0 M, average day 7,373.3 M, so the gap is 74.3 M (1.0%).
- These are the 7 search days, whose chain factors are 1.057, 0.961, 0.912, 0.855, 0.967, 0.984, 1.005 (weighted mean below 1).
- The same network on the 28 final days costs 7,606.8 M, so the 28-day gap is 233.6 M (3.1%), and the 7-versus-28 difference (159 M) is larger than the reported gap.
- Fix: compute all three R2 rows on the 28 final days, and report the 7-day version only as a footnote.
- Fix: split "expected counts minus average day" into calendar and chain shock by adding one row with calendar exposure but shock fixed at 1; the persona checklist and R2 ask for store noise, calendar and chain shock separately.
- Count noise is 12.5 M (sampled minus expected counts), which supports the brief's "store noise cancels at the DC"; say so with the number.

### M3 - Service is deterministic, failures are free, and the baseline is infeasible

- Recommended service is 0.990327 on every final day, every held-out day and the peak day, which is exactly 1 - 94/9,718; the baseline is 1 - 227/9,718 = 0.976641.
- So the 98% rule is decided by geography (stores on over-limit routes), not by demand; "worst-day service 97.7% / 99.0%" is not a statistical statement and should not be presented as one.
- The 94 stores (east coast, lat 36.5-38.4, lon 128.4-129.4) get 0% before noon on every day in the recommended network; today 227 stores do.
- Penalty is 0.0 for every network, because these routes arrive before 14:00; the CFO red flag "penalties that never trigger" applies.
- The model charges a relay driver-day for each such route and still counts all its stores as late; either the second driver fixes the route (then count it on time) or it does not (then say what the 180,822 KRW buys).
- The baseline fails the 98% rule by 33 stores (227 against an allowance of 194), so part of the saving is the price of restoring service, which deserves one sentence.

### M4 - The waterfall steps are not what their labels say

- "best 12 sites" (pool candidate 154: sites 0, 2, 3, 9, 11, 13, 34, 40, 44, 46, 52, 59) and the recommended 13 (0, 1, 2, 3, 7, 9, 11, 28, 29, 31, 40, 44, 46) share only 7 sites.
- The step "13th DC -87" is therefore a different network, not one added DC.
- -87 M is also within the selection noise of the final step: the five finalists on the 28 days span 7,607-7,693 M, and the recommendation is the minimum of those five on the same 28 days.
- Its held-out check exists only for the recommended network; best12 was not scored on held-out days.
- Fix: label the last step "best 12 to best 13 (different sites)", and add a cost-line decomposition (fleet, relay, fuel, spot, fixed) beside the waterfall, since that is what a CFO reads.
- Fix: score best12 on the 14 held-out days with its own fixed fleet, and report the paired 12-versus-13 band; if it covers zero, the proposal should say k = 12 or 13 is a tie, as the work log already says for 10-13.

### M5 - Variance sources outside the band, with a size estimate for each

| Source | In the band? | Size, from the registry or a bound | What to do |
|---|---|---|---|
| Daily counts, shocks, overdispersion | yes | band half-width about 5.6 M | keep |
| Posterior rate draw | no within a set; yes across sets | 1,769 / 1,776 / 1,778 across three independent sets | report the three sets |
| Calendar `beta`, prior hyperparameters | no (plug-in) | small at 365 days and 9,718 stores | one sentence |
| Chain-shock model (phi, storms) | no | planning days slightly too calm (M1) | M1 replicates |
| Demand level or growth | no | fleet, fuel and relay scale with volume: a 10% rise plausibly moves the saving by the order of 100-180 M | demand x0.9 / x1.1 reversal row (already planned) |
| Relay price | no | 1,045 to 3,270 M | on the headline line (B1) |
| Distance model | no | over-limit counts sit on cliffs at 55, 125 and 250 km, so a few % of distance can move the 94 and 227 | detour x0.95 / x1.05 on baseline and recommended only |
| Routing heuristic | partly cancels (paired, same heuristic) | unknown | state it |
| Cost defaults | no | see the CFO section | break-even table |
| Search seed | no (decision, not saving) | random band and top-5 spread | already shown |

### M6 - CFO questions the deliverables cannot answer yet

- Spot +30%: spot lines are 111.8 M (baseline) and 116.5 M (recommended), so at fixed fleets the saving falls by about 1.4 M; the fractile would move from 0.671 to 0.747; one row settles it, and the answer is "irrelevant".
- Break-even DC fixed cost against the baseline: the recommendation has one more DC, so the per-DC cost would have to rise by about 1,776 M/month, which never happens; against best12, about +87 M per DC (to about 240 M) flips 13 to 12.
- Break-even relay price: none in 0-550,000 KRW (saving positive throughout); k* moves 13 to 12 at the spot rate.
- Vehicle cost: 5.5 M "driver included" for a truck that runs 30.4 days a month implies one driver working seven days a week; with about 1.4 drivers per truck the fleet line and the saving would both rise, so the default is conservative for the saving; say so.
- Fleet quantile 0.671 is the correct critical fractile 1 - 180,822 / 550,000; good, keep the derivation on the slide.

## Minors

1. Held-out days exclude the final dates but not the search dates (`exclude=[d["date"] for d in d_final]`); every call draws fresh counts and shocks so nothing is reused, but say so or exclude both.
2. Strata sizes: holiday-or-eve gets 1 of 7, 2 of 28 and 1 of 14 days; a one-day stratum contributes zero bootstrap variance at 7.4% weight; use at least two per stratum in the held-out set or state it.
3. The registry `finals` blocks drop `V`, `fuel_d`, `over_d` and `w` per day (`_summary`), so the bands cannot be recomputed from the registry and `verify.py` cannot check them; store the per-day vectors for baseline and recommended.
4. D-030 says the prior strength is "about 2.3 store-days"; the registry gives 2.09 / 2.17 / 1.92 / 1.84 by type; update D-030 to "about 2 (1.8-2.2 by type)".
5. The example store ST00211 has 61 days, so the prior is 3% of the posterior and the shrinkage is invisible; pick a store with 10-20 days; also explain why its posterior 2.14 is 1.4 posterior sd above the true 1.89 (calendar exposure, overdispersion).
6. Kappa 8.13 against the generator's 8.0 is a good recovery; report it as a check that the model's overdispersion is right.
7. DC fixed costs are tiered 180 / 157.5 / 132 M, not the brief's flat 150 M; today's 12 average 158.4 M, the 60 sites 145.75 M, the recommended 13 average 150.5 M; the brief asks for a reason when a default changes, and all six new sites are in the 132 M tier, which is part of the "move sites" step.
8. Fuel 350 KRW/km is plausible (diesel about 1,600 KRW/L at about 4.5 km/L); 147 km per vehicle-day (102,936 km / 701 vehicles) is plausible; no change.
9. The k = 13 to 14 jump (7,448 to 8,012 M) is not smooth, which points at pool coverage for k >= 14 rather than cost; the sweep's right side is pool-limited and should be labelled as such.
10. "Monthly" is 365/12 = 30.42 days throughout and seven delivery days a week; consistent, state it once in the cost table.

## WORK_LOG "Spark run 2" against the registry

| Work-log figure | Registry | Match |
|---|---|---|
| Today's network 9,383 | finals.baseline.total 9,383.06 M | yes |
| 13 DCs, keep 7, close 5, open 6, 7,607 | networks.recommended (7 current + 6 new), 7,606.85 M | yes |
| Saving 1,776 [1,771, 1,782] | final_mean 1,776.21; final_ci 1,770.84-1,782.04 | yes |
| Held-out 1,778 [1,771, 1,784] | held_mean 1,777.75; held_ci 1,771.01-1,783.85 | yes |
| Worst-day service 97.7% / 99.0% | 0.97664 / 0.99033 | yes |
| Waterfall -630 / -1,059 / -87 | 9,383.1 to 8,752.8 to 7,693.5 to 7,606.8 | yes (labels: M4) |
| Sweep 9: 7,964 to 14: 8,012 | sweep totals 7,964 / 7,593 / 7,563 / 7,550 / 7,448 / 8,012 | yes |
| Waves 30 docks, k* 13 to 14, overflow 13-34, today 37 | docks 30; 31.7 / 34 / 13 / 32 / 30 for k = 9-13; baseline 36.7 | yes |
| Thinning k* 13 / 12, 1.26x vs 2.24x | 13 / 12; 1.259 / 2.236 | yes |
| Spearman 0.60, within k 0.25, G-pick loss 116 | 0.601 / 0.250 / 115.9 M | yes |
| Search vs random 7,448 vs 7,929 | curve_bo min 7,447.5; random final and median 7,928.5 | yes |
| Relay k* 13 / 13 / 12; saving 1,045 / 1,776 / 3,270 | 13 / 13 / 12; 1,044.7 / 1,776.2 / 3,269.7 | yes |
| History 3,502,822, 97.6%, 824, 139,919 | history_ops identical | yes |
| 13 G seeds + 27 EI | 13 seed rows of 40 | yes |
| Relay 517 M recommended, 1,249 M today | 517.0 / 1,248.5 | yes |
| Reduced: 2,069, 12 DCs 1,775, 294 [291, 297], held 296, 97.9% / 99.1%, relay k* 11 / 12 / 12 | all identical in reduced/registry.json | yes |

One wording issue: "the number of DCs is a flat choice between 10 and 13 (within 150 M)" is on the 7 search days; on the 28 final days only k = 11, 12, 13 were re-scored, so add "search days".

## What I would accept as the headline

"Steady-state saving 1,776 M KRW per month (28 sampled days, paired; 90% day band 1,771-1,782; held-out 14 days 1,778).
The band covers day-to-day demand only; the relay price for far stores moves the saving between 1,045 and 3,270 M, and lease overhang of up to 32.6 bn KRW delays it (payback table, slide N)."
