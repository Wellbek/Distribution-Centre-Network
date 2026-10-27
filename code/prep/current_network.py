"""Choose today's 12 DCs as the 2016 planner did: capacitated p-median on straight-line km over the stores open in 2016.

Every store within one driver-day (FAR_KM road km, i.e. FAR_KM / DETOUR straight-line) and no DC above the cap; no minimum
(the baseline is exempt, brief §2.3). Greedy add, then exchange search on 5 km cells. The result goes into geo.CURRENT;
run 3's p-median on today's stores and road km is kept as geo.PMEDIAN_12 for the "today is already optimal" reversal.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import config as C  # noqa: E402
from dcn import distances  # noqa: E402
from dcn import world as W  # noqa: E402

def main():
    w = W.make_world(1.0)
    st, sites = w["stores"], w["sites"]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    cur, km, n_open = W.era_design(w, W.DESIGN_YEAR)
    print(f"{n_open} stores open in {W.DESIGN_YEAR}; demand-weighted straight-line km {km:.1f}")
    plan = W.planning_mask(w)
    road = distances.site_km(st["full"], st["lat"], st["lon"], st["mountain"], slat, slon, [s["id"] for s in sites])
    a = np.array(sorted(cur))[W.era_assignment(st["lat"], st["lon"], st["rate_true"], st["year"], slat[sorted(cur)], slon[sorted(cur)], C.MAX_STORES)]
    dr = road[np.arange(len(a)), a][plan]
    print(f"today: demand-weighted road km {(st['rate_true'][plan] * dr).sum() / st['rate_true'][plan].sum():.1f}, "
          f"farthest {dr.max():.0f} km, beyond {C.FAR_KM:.0f} km {(dr > C.FAR_KM).sum()} stores")
    for j in sorted(cur, key=lambda j: -sites[j]["lat"]):
        print(f"  {sites[j]['id']:5s} {sites[j]['name']:22s} {sites[j]['province']:18s} {(a[plan] == j).sum():5d} stores")


if __name__ == "__main__":
    main()
