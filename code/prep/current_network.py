"""Choose the 12 current DCs from the 60 sites: capacitated p-median on demand-weighted map distance, by exchange search."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import config as C  # noqa: E402
from dcn import geo  # noqa: E402
from dcn import world as W  # noqa: E402


def main():
    w = W.make_world(1.0)
    st, sites = w["stores"], w["sites"]
    m = st["opened"] < 0  # the stores the planner saw
    lat, lon, q = st["lat"][m], st["lon"][m], st["rate_true"][m]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])

    # Search on 5 km cells (demand-weighted centre, store count); the final check uses every store
    cell = np.floor(lat / 0.045).astype(int) * 100_000 + np.floor(lon / 0.056).astype(int)
    _, inv = np.unique(cell, return_inverse=True)
    wq, cnt = np.bincount(inv, q), np.bincount(inv)
    clat, clon = np.bincount(inv, q * lat) / wq, np.bincount(inv, q * lon) / wq
    D = geo.haversine(clat[:, None], clon[:, None], slat[None], slon[None])

    def cost(open_):
        res = W.transport_lp(wq[:, None] * D[:, open_], C.MIN_STORES, C.MAX_STORES, size=cnt)
        return np.inf if res is None else res.fun

    cur = [i for i, s in enumerate(sites) if s["current"]]
    best = cost(cur)
    print(f"{len(cnt)} cells; start (old 12): {best:,.0f}")
    near = np.argsort(geo.haversine(slat[:, None], slon[:, None], slat[None], slon[None]), 1)[:, 1:13]
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

    dm = geo.haversine(lat[:, None], lon[:, None], slat[None, cur], slon[None, cur])
    res = W.transport_lp(q[:, None] * dm, C.MIN_STORES, C.MAX_STORES)
    a = res.x.reshape(len(lat), -1).argmax(1)
    load = np.bincount(a, minlength=len(cur))
    print(f"final {best:,.0f} on cells, {res.fun:,.0f} on stores; demand-weighted mean map km {res.fun / q.sum():.1f}")
    for j, i in sorted(zip(cur, range(len(cur))), key=lambda t: -sites[t[0]]["lat"]):
        print(f"  {sites[j]['id']:5s} {sites[j]['name']:22s} {sites[j]['province']:18s} {load[i]:5d} stores")


if __name__ == "__main__":
    main()
