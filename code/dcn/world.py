"""Generate the fictional Dasol world: stores, current DCs, candidate sites, historical assignment."""
from datetime import date

import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from . import config as C
from . import geo

TYPES = np.array(["residential", "office", "mixed", "roadside"])
TYPE_LEVEL = np.array([1.00, 0.95, 1.05, 1.10])
HIST_START = date(2025, 10, 1)
HIST_DAYS = 365
RURAL_HEX = 500                             # people per hexagon (about 700 per km2): 15% of stores are rural
# Share of today's pre-history stores open by each year [ASSUMPTION: the shape of a Korean convenience chain's growth]
GROWTH = np.array([[1990, 0.0], [2000, 0.12], [2010, 0.41], [2016, 0.62], [2020, 0.76], [2026, 1.0]])
DESIGN_YEAR = 2016                          # the network was last designed ten years ago (prep/current_network.py)
HIST_YEAR = 2026                            # stores opened during the history year


def transport_lp(cost, lo, hi, size=None):
    """Capacitated transportation LP (HiGHS): rows to columns, column loads (in row sizes) within [lo, hi]; None if infeasible."""
    n, k = cost.shape
    size = np.ones(n) if size is None else size
    A_eq = sparse.csr_matrix((np.ones(n * k), (np.repeat(np.arange(n), k), np.arange(n * k))), shape=(n, n * k))
    A_cap = sparse.csr_matrix((np.repeat(size, k), (np.tile(np.arange(k), n), np.arange(n * k))), shape=(k, n * k))
    res = linprog(cost.ravel(), A_ub=sparse.vstack([A_cap, -A_cap]), b_ub=np.r_[np.full(k, hi), np.full(k, -lo)],
                  A_eq=A_eq, b_eq=np.ones(n), bounds=(0, 1), method="highs")
    return res if res.status == 0 else None


def _sample_points(n, rng):
    # Stores in proportion to population on Kontur H3 hexagons, jittered inside the hexagon (resolution 8, edge 0.46 km);
    # the nearest city and the distance in units of its spread only drive the store types; sparse hexagons are rural
    h = np.load(geo.DATA / "kontur_hexes.npz")
    k = rng.choice(len(h["pop"]), size=n, p=h["pop"] / h["pop"].sum())
    ang, rad = rng.uniform(0, 2 * np.pi, n), 0.4 * np.sqrt(rng.random(n))
    lat = h["lat"][k] + rad * np.sin(ang) / 111.0
    lon = h["lon"][k] + rad * np.cos(ang) / (111.0 * np.cos(np.radians(h["lat"][k])))
    lat0, lon0, pop = (np.array([c[i] for c in geo.CITIES], float) for i in (2, 3, 4))
    sigma = 1.5 + 0.09 * np.sqrt(pop)
    d = geo.haversine(lat[:, None], lon[:, None], lat0[None], lon0[None])
    city = d.argmin(1)
    r = d[np.arange(n), city] / sigma[city]
    city = np.where(h["pop"][k] < RURAL_HEX, -1, city)
    return lat, lon, h["province"][k].astype(object), h["district"][k].astype(object), city, r, pop, h["pop"][k]


def opening_years(hexpop, opened, seed):
    """Year each store opened: denser hexagons earlier, following the chain's growth curve; history-year openings get HIST_YEAR."""
    rng = np.random.default_rng(seed + 7)
    n = len(hexpop)
    score = (np.argsort(np.argsort(hexpop, kind="stable"), kind="stable") + 0.5) / n + rng.normal(0, 0.25, n)
    old = np.flatnonzero(opened < 0)
    rank = np.empty(n)
    rank[old[np.argsort(-score[old], kind="stable")]] = (np.arange(len(old)) + 0.5) / len(old)
    return np.where(opened < 0, np.floor(np.interp(rank, GROWTH[:, 1], GROWTH[:, 0])), HIST_YEAR).astype(int)


def era_assignment(lat, lon, rate, year, dlat, dlon, hi, design_year=DESIGN_YEAR):
    """The design-year planner's assignment on straight-line km (every store within one driver-day, at most hi per DC);
    stores opened since join the nearest DC with room, in order of opening; nothing is rebalanced."""
    d = geo.haversine(lat[:, None], lon[:, None], dlat[None], dlon[None])
    m = year <= design_year
    res = transport_lp(rate[m, None] * d[m] + 1e12 * (d[m] > C.FAR_KM / C.DETOUR), 0, hi)
    a = np.full(len(lat), -1)
    a[m] = res.x.reshape(m.sum(), -1).argmax(1)
    load = np.bincount(a[m], minlength=len(dlat))
    for i in np.flatnonzero(~m)[np.argsort(year[~m], kind="stable")]:
        o = np.argsort(d[i], kind="stable")
        room = o[load[o] < hi]
        a[i] = room[0] if len(room) else o[0]
        load[a[i]] += 1
    return a


def era_design(world, year, k=12):
    """The planner of `year`: capacitated p-median on straight-line km over the stores open then, every store within one
    driver-day, at most MAX_STORES per DC, no minimum; greedy add, then exchange search on 5 km cells (prep/current_network.py)."""
    st, sites = world["stores"], world["sites"]
    m = st["year"] <= year
    lat, lon, q = st["lat"][m], st["lon"][m], st["rate_true"][m]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    d = geo.haversine(lat[:, None], lon[:, None], slat[None], slon[None])
    cell = np.floor(lat / 0.045).astype(int) * 100_000 + np.floor(lon / 0.056).astype(int)
    _, inv = np.unique(cell, return_inverse=True)
    wq, cnt = np.bincount(inv, q), np.bincount(inv)
    D = np.array([np.bincount(inv, q * d[:, j]) for j in range(len(sites))]).T / wq[:, None]
    far = np.array([np.maximum.reduceat(d[np.argsort(inv, kind="stable"), j], np.r_[0, np.cumsum(cnt)[:-1]]) for j in range(len(sites))]).T > C.FAR_KM / C.DETOUR
    ban = 1e12

    def cost(open_):
        res = transport_lp(wq[:, None] * D[:, open_] + ban * far[:, open_], 0, round(C.MAX_STORES * world["fraction"]), size=cnt)
        return np.inf if res is None else res.fun

    cur, best_d = [], np.full(len(wq), np.inf)
    for _ in range(k):
        s_ = min((j for j in range(len(sites)) if j not in cur), key=lambda j: (wq * np.minimum(best_d, D[:, j] + ban * far[:, j])).sum())
        cur.append(s_); best_d = np.minimum(best_d, D[:, s_] + ban * far[:, s_])
    best = cost(cur)
    near = np.argsort(geo.haversine(slat[:, None], slon[:, None], slat[None], slon[None]), 1, kind="stable")[:, 1:13]
    improved = True
    while improved:
        improved = False
        for o in list(cur):
            for s_ in near[o]:
                if o not in cur or s_ in cur:
                    continue
                cand = [s_ if x == o else x for x in cur]
                c = cost(cand)
                if c < best - 1e-6:
                    cur, best, improved = cand, c, True
    return sorted(cur), best / q.sum(), int(m.sum())


def make_world(fraction=1.0, seed=C.SEED):
    """Build all input tables of brief §2.5 for one seed; fraction thins stores nationwide."""
    rng = np.random.default_rng(seed)
    provinces = geo.load_land()
    lat, lon, prov, dist, city, r, pop, hexpop = _sample_points(C.FULL_STORES, rng)
    n = len(lat)

    # Store types from location: office near big-city centres, roadside in the countryside
    u = rng.random(n)
    big = (city >= 0) & (pop[np.maximum(city, 0)] > 800) & (r < 0.6)
    rural = city < 0
    t = np.where(u < 0.62, 0, np.where(u < 0.87, 2, np.where(u < 0.95, 3, 1)))
    t = np.where(big, np.where(u < 0.45, 1, np.where(u < 0.70, 2, 0)), t)
    t = np.where(rural, np.where(u < 0.55, 3, 0), t)

    # Base rate: lognormal around 2.2 cages/day, clipped to [0.5, 6]
    s = 0.45
    rate = np.exp(rng.normal(np.log(2.2) - s * s / 2, s, n)) * TYPE_LEVEL[t]
    rate = np.clip(rate * 2.2 / rate.mean(), 0.5, 6.0)

    # Churn: 6% opened during the history year, 3% closed during it
    opened = np.full(n, -1)
    new = rng.random(n) < 0.06
    opened[new] = rng.integers(0, HIST_DAYS - 20, new.sum())
    closed = np.full(n, 10_000)
    gone = (~new) & (rng.random(n) < 0.03)
    closed[gone] = rng.integers(30, HIST_DAYS, gone.sum())

    # Thin nationwide with a fixed permutation so geography survives
    order = rng.permutation(n)
    keep = np.sort(order[: int(round(fraction * n))])

    sites = [dict(id=s_[0], name=s_[1], province=s_[2], lat=s_[3], lon=s_[4], current=s_[0] in geo.CURRENT) for s_ in geo.SITES]
    dcs = [dict(id=x["id"], name=x["name"], province=x["province"], lat=x["lat"], lon=x["lon"], lease_expires_on=geo.CURRENT[x["id"]])
           for x in sites if x["current"]]
    for st in sites:
        st["monthly_fixed_cost"] = round(C.DC_FIXED * geo.site_cost_factor(st["province"]) * fraction)
        st["max_stores"] = round(C.MAX_STORES * fraction)
    for d in dcs:
        d["monthly_fixed_cost"] = next(x["monthly_fixed_cost"] for x in sites if x["id"] == d["id"])
        d["max_stores"], d["min_stores"] = round(C.MAX_STORES * fraction), round(C.MIN_STORES * fraction)

    stores = dict(
        lat=lat[keep], lon=lon[keep], province=prov[keep], district=dist[keep], type=t[keep], rate_true=rate[keep],
        opened=opened[keep], closed=closed[keep], mountain=np.isin(prov[keep], list(geo.MOUNTAIN)),
    )
    stores["id"] = np.array([f"ST{i:05d}" for i in keep])
    stores["full"] = keep
    stores["year"] = opening_years(hexpop, opened, seed)[keep]

    # Historical assignment: the 2016 planner's (prep/current_network.py), then growth without rebalancing;
    # the baseline is exempt from the bounds imposed on new designs (brief §2.3)
    dlat = np.array([d["lat"] for d in dcs]); dlon = np.array([d["lon"] for d in dcs])
    stores["current_dc"] = era_assignment(stores["lat"], stores["lon"], stores["rate_true"], stores["year"], dlat, dlon,
                                          round(C.MAX_STORES * fraction))

    return dict(
        seed=seed, fraction=fraction, stores=stores, dcs=dcs, sites=sites, provinces=provinces,
        min_stores=round(C.MIN_STORES * fraction), max_stores=round(C.MAX_STORES * fraction),
    )


def planning_mask(world):
    # Stores still open at the end of the history are the planning set
    return world["stores"]["closed"] >= HIST_DAYS
