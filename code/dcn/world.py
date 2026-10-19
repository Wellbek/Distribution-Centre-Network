"""Generate the fictional Dasol world: stores, current DCs, candidate sites, historical assignment."""
from datetime import date

import numpy as np

from . import config as C
from . import geo

TYPES = np.array(["residential", "office", "mixed", "roadside"])
TYPE_LEVEL = np.array([1.00, 0.95, 1.05, 1.10])
HIST_START = date(2025, 10, 1)
HIST_DAYS = 365


def _sample_points(n, rng, provinces):
    # Cluster stores around cities by population; 10% rural background; keep points on land
    names, _, lat0, lon0, pop = zip(*[(c[0], c[1], c[2], c[3], c[4]) for c in geo.CITIES])
    lat0, lon0, pop = np.array(lat0), np.array(lon0), np.array(pop, float)
    sigma = 1.5 + 0.09 * np.sqrt(pop)
    n_rural = int(0.10 * n)
    out_lat, out_lon, out_city, out_r = [], [], [], []
    need = n - n_rural
    while need > 0:
        k = rng.choice(len(pop), size=2 * need, p=pop / pop.sum())
        dx, dy = rng.normal(size=(2, 2 * need)) * sigma[k]
        la = lat0[k] + dy / 111.0
        lo = lon0[k] + dx / (111.0 * np.cos(np.radians(lat0[k])))
        prov = geo.province_of(lo, la, provinces)
        ok = np.flatnonzero(prov != "")[:need]
        out_lat += list(la[ok]); out_lon += list(lo[ok]); out_city += list(k[ok])
        out_r += list(np.hypot(dx, dy)[ok] / sigma[k[ok]])
        need -= len(ok)
    need = n_rural
    while need > 0:
        la = rng.uniform(34.3, 38.6, 4 * need)
        lo = rng.uniform(126.1, 129.6, 4 * need)
        prov = geo.province_of(lo, la, provinces)
        ok = np.flatnonzero(prov != "")[:need]
        out_lat += list(la[ok]); out_lon += list(lo[ok]); out_city += [-1] * len(ok); out_r += [9.0] * len(ok)
        need -= len(ok)
    lat, lon = np.array(out_lat), np.array(out_lon)
    return lat, lon, np.array(out_city), np.array(out_r), pop


def make_world(fraction=1.0, seed=C.SEED):
    """Build all input tables of brief §2.5 for one seed; fraction thins stores nationwide."""
    rng = np.random.default_rng(seed)
    provinces = geo.load_land()
    lat, lon, city, r, pop = _sample_points(C.FULL_STORES, rng, provinces)
    n = len(lat)
    prov = geo.province_of(lon, lat, provinces)

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
        lat=lat[keep], lon=lon[keep], province=prov[keep], type=t[keep], rate_true=rate[keep],
        opened=opened[keep], closed=closed[keep], mountain=np.isin(prov[keep], list(geo.MOUNTAIN)),
    )
    stores["id"] = np.array([f"ST{i:05d}" for i in keep])
    stores["full"] = keep

    # Historical assignment: nearest current DC by map distance at opening, never rebalanced
    dlat = np.array([d["lat"] for d in dcs]); dlon = np.array([d["lon"] for d in dcs])
    dm = geo.haversine(stores["lat"][:, None], stores["lon"][:, None], dlat[None, :], dlon[None, :])
    stores["current_dc"] = dm.argmin(1)

    return dict(
        seed=seed, fraction=fraction, stores=stores, dcs=dcs, sites=sites, provinces=provinces,
        min_stores=round(C.MIN_STORES * fraction), max_stores=round(C.MAX_STORES * fraction),
    )


def planning_mask(world):
    # Stores still open at the end of the history are the planning set
    return world["stores"]["closed"] >= HIST_DAYS
