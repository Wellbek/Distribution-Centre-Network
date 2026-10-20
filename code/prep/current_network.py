"""Choose the 12 current DCs from the 60 sites: p-median on demand-weighted road km with a reach rule, by exchange search.

The planner keeps every store within one driver-day (REACH_LIMIT road km) of its DC and no DC above the store cap;
the 500-store minimum does not apply to the baseline (brief §2.3). Road km from data/road_cache.npz.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import config as C  # noqa: E402
from dcn import distances, geo  # noqa: E402
from dcn import world as W  # noqa: E402


REACH_LIMIT = C.MAX_KM / 2   # one driver's 250 km day, out and back
BAN = 1e12


def main():
    w = W.make_world(1.0)
    st, sites = w["stores"], w["sites"]
    m = st["opened"] < 0  # the stores the planner saw
    lat, lon, q = st["lat"][m], st["lon"][m], st["rate_true"][m]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])

    # Search on 5 km cells (demand-weighted road km, farthest store per cell); the final check uses every store
    cell = np.floor(lat / 0.045).astype(int) * 100_000 + np.floor(lon / 0.056).astype(int)
    _, inv = np.unique(cell, return_inverse=True)
    wq, cnt = np.bincount(inv, q), np.bincount(inv)
    road = distances.site_km(st["full"][m], lat, lon, st["mountain"][m], slat, slon, [s["id"] for s in sites])
    D = np.array([np.bincount(inv, q * road[:, j]) for j in range(len(sites))]).T / wq[:, None]
    far = np.array([np.maximum.reduceat(road[np.argsort(inv), j], np.r_[0, np.cumsum(cnt)[:-1]]) for j in range(len(sites))]).T > REACH_LIMIT

    def cost(open_):
        res = W.transport_lp(wq[:, None] * D[:, open_] + BAN * far[:, open_], 0, C.MAX_STORES, size=cnt)
        # Out-of-reach cells cost BAN each, so the search first removes them, then shortens distance
        return np.inf if res is None else res.fun

    cur = [i for i, s in enumerate(sites) if s["current"]]
    best = cost(cur)
    print(f"{len(cnt)} cells; start (current 12): {best:,.0f}")
    near = np.argsort(geo.haversine(slat[:, None], slon[:, None], slat[None], slon[None]), 1)[:, 1:]
    improved = True
    while improved:
        improved = False
        for o in list(cur):
            for s in near[o]:
                if o not in cur or s in cur:
                    continue
                cand = [s if x == o else x for x in cur]
                c = cost(cand)
                if c < best - 1e-6:
                    print(f"  {sites[o]['name']} -> {sites[s]['name']}: {c:,.0f}")
                    cur, best, improved = cand, c, True

    dm = road[:, cur]
    res = W.transport_lp(q[:, None] * dm + BAN * (dm > REACH_LIMIT), 0, C.MAX_STORES)
    a = res.x.reshape(len(lat), -1).argmax(1)
    load = np.bincount(a, minlength=len(cur))
    print(f"final {best:,.0f} on cells, {res.fun:,.0f} on stores; demand-weighted mean road km {res.fun / q.sum():.1f}; farthest store {dm[np.arange(len(q)), a].max():.0f} km")
    for j, i in sorted(zip(cur, range(len(cur))), key=lambda t: -sites[t[0]]["lat"]):
        print(f"  {sites[j]['id']:5s} {sites[j]['name']:22s} {sites[j]['province']:18s} {load[i]:5d} stores")


if __name__ == "__main__":
    main()
