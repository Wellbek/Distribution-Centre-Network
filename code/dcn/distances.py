"""Road distances: OSRM cache for store-site and nearest-store pairs, calibrated map-distance model for the rest."""
import json
import warnings
from functools import lru_cache

import numpy as np

from . import config as C
from . import geo

CACHE = geo.DATA / "road_cache.npz"


@lru_cache(1)
def cache():
    # None until osrm/build_cache.py has written the file; the runs then use the uncalibrated placeholder
    if not CACHE.exists():
        warnings.warn(f"{CACHE} missing: distances fall back to map distance x {C.DETOUR}; results are not the reported ones")
        return None
    z = np.load(CACHE)
    return {k: z[k] for k in z.files} | dict(meta=json.loads(str(z["meta"])))


def fit(mapd, road, cls):
    """Least squares of ln(road / map) on ln(map), one line per class; returns a 2 x 2 array [class, (a, b)]."""
    out = np.zeros((2, 2))
    for c in (0, 1):
        m = cls == c
        X = np.c_[np.ones(m.sum()), np.log(mapd[m])]
        out[c] = np.linalg.lstsq(X, np.log(road[m] / mapd[m]), rcond=None)[0]
    return out


def apply(coef, mapd, cls):
    d = np.maximum(mapd, 0.5)
    return d * np.exp(coef[cls, 0] + coef[cls, 1] * np.log(d))


def model_km(lat1, lon1, lat2, lon2, mountain):
    # Calibrated model when the cache exists, else the v0.1 placeholder factors
    d = geo.haversine(lat1, lon1, lat2, lon2)
    z = cache()
    if z is None:
        return d * np.where(mountain, C.DETOUR_MOUNTAIN, C.DETOUR)
    return np.where(d > 0, apply(z["coef"], d, np.asarray(mountain).astype(int)), 0.0)


def local_ratio():
    # Median road/map ratio of nearest-store legs, the detour inside a territory
    z = cache()
    return C.DETOUR if z is None else z["meta"]["ratio_nn_median"]


def describe():
    # One line for the registry and the demo
    z = cache()
    if z is None:
        return f"map distance x {C.DETOUR} (x {C.DETOUR_MOUNTAIN} in Gangwon and North Gyeongsang), uncalibrated placeholder"
    m = z["meta"]
    return (f"OSRM {m['engine'].split(':')[-1]} car profile on {m['source']} (data {m['data_version']}): every store-DC pair and "
            f"{m['k_nn']} nearest stores per store; other pairs by a model calibrated on {m['calibration_pairs']} road distances")


def site_km(full, lat, lon, mountain, slat, slon, ids):
    """Store x site road km for the sites named in ids: cached OSRM values, model if no cache."""
    z = cache()
    if z is None:
        return model_km(lat[:, None], lon[:, None], slat[None], slon[None], mountain[:, None])
    if not (np.allclose(z["lat"][full], lat) and np.allclose(z["lon"][full], lon)):
        raise RuntimeError("road_cache.npz was built for another world; rerun osrm/build_cache.py")
    col = {s: i for i, s in enumerate(z["site_ids"].tolist())}
    return z["site_km"][full][:, [col[i] for i in ids]].astype(float)


def territory(dc_km, full, lat, lon, mountain, use_cache=True):
    """DC + stores matrix (index 0 = DC): cached DC legs and nearest-store legs, model for the remaining store pairs."""
    n = len(full)
    D = np.zeros((n + 1, n + 1))
    D[0, 1:] = D[1:, 0] = dc_km
    D[1:, 1:] = model_km(lat[:, None], lon[:, None], lat[None], lon[None], mountain[:, None] | mountain[None])
    np.fill_diagonal(D, 0.0)
    z = cache() if use_cache else None
    if z is not None:
        local = np.full(len(z["lat"]), -1)
        local[full] = np.arange(n)
        j = local[z["nn"][full]]
        i = np.repeat(np.arange(n)[:, None], j.shape[1], 1)
        m = j >= 0
        D[i[m] + 1, j[m] + 1] = D[j[m] + 1, i[m] + 1] = z["nn_km"][full][m]
        D = (D + D.T) / 2
    return D
