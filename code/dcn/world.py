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
    return lat, lon, h["province"][k].astype(object), h["district"][k].astype(object), city, r, pop


def make_world(fraction=1.0, seed=C.SEED):
    """Build all input tables of brief §2.5 for one seed; fraction thins stores nationwide."""
    rng = np.random.default_rng(seed)
    provinces = geo.load_land()
    lat, lon, prov, dist, city, r, pop = _sample_points(C.FULL_STORES, rng)
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

    dcs = [dict(id=d[0], name=d[1], province=d[2], lat=d[3], lon=d[4], lease_expires_on=d[5]) for d in geo.CURRENT_DCS]
    sites = [dict(id=d["id"], name=d["name"], province=d["province"], lat=d["lat"], lon=d["lon"], current=True) for d in dcs]
    sites += [dict(id=s_[0], name=s_[1], province=s_[2], lat=s_[3], lon=s_[4], current=False) for s_ in geo.NEW_SITES]
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

    # Historical assignment: the network planner's capacitated assignment on demand-weighted map distance for the stores
    # open before the history year; stores opened during it go to the nearest DC with room; never rebalanced
    dlat = np.array([d["lat"] for d in dcs]); dlon = np.array([d["lon"] for d in dcs])
    dm = geo.haversine(stores["lat"][:, None], stores["lon"][:, None], dlat[None, :], dlon[None, :])
    lo, hi = round(C.MIN_STORES * fraction), round(C.MAX_STORES * fraction)
    old = stores["opened"] < 0
    res = transport_lp(stores["rate_true"][old, None] * dm[old], lo, hi)
    cur = np.full(len(keep), -1)
    cur[old] = res.x.reshape(old.sum(), -1).argmax(1)
    load = np.bincount(cur[old], minlength=len(dcs))
    for i in np.flatnonzero(~old)[np.argsort(stores["opened"][~old], kind="stable")]:
        j = int(np.argmin(np.where(load < hi, dm[i], np.inf)))
        cur[i] = j; load[j] += 1
    stores["current_dc"] = cur

    return dict(
        seed=seed, fraction=fraction, stores=stores, dcs=dcs, sites=sites, provinces=provinces,
        min_stores=round(C.MIN_STORES * fraction), max_stores=round(C.MAX_STORES * fraction),
    )


def planning_mask(world):
    # Stores still open at the end of the history are the planning set
    return world["stores"]["closed"] >= HIST_DAYS
