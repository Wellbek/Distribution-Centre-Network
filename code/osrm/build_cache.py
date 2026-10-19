"""Build data/road_cache.npz from a running OSRM server: store-site km, nearest-store km, calibrated model for the rest."""
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import distances, geo  # noqa: E402
from dcn import world as W  # noqa: E402

URL = "http://localhost:5000"
IMAGE = "ghcr.io/project-osrm/osrm-backend:v6.0.0"
PBF = "Geofabrik south-korea-latest.osm.pbf (md5 ea750dde8e6e6ded7a677ec7e029257e)"
EXTRACT = "2026-10-18T20:25:06Z"  # osmosis_replication_timestamp in the PBF header; OSRM does not report it
K_NN = 50
CHUNK = 30
N_CAL_SRC, N_CAL_DST = 400, 10


def table(lat, lon):
    # Symmetric road km between all points (mean of both directions) plus the snap leg at each end; NaN if unroutable
    coords = ";".join(f"{b:.6f},{a:.6f}" for a, b in zip(lat, lon))
    with urllib.request.urlopen(f"{URL}/table/v1/driving/{coords}?annotations=distance", timeout=600) as r:
        res = json.load(r)
    d = np.array([[np.nan if x is None else x for x in row] for row in res["distances"]], float)
    snap = np.array([s["distance"] for s in res["sources"]])
    d = (d + d.T) / 2 + snap[:, None] + snap[None, :]
    np.fill_diagonal(d, 0.0)
    return d / 1000, snap


def run(jobs, fn):
    with ThreadPoolExecutor(4) as ex:
        return list(ex.map(fn, jobs))


def main():
    t0 = time.time()
    world = W.make_world(1.0)
    st, sites = world["stores"], world["sites"]
    lat, lon, mt = st["lat"], st["lon"], st["mountain"]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    n, S = len(lat), len(sites)

    # Every store to every site
    blocks = [np.arange(i, min(i + 100, n)) for i in range(0, n, 100)]
    out = run(blocks, lambda b: table(np.r_[lat[b], slat], np.r_[lon[b], slon]))
    site_km = np.vstack([d[: len(b), len(b):] for b, (d, _) in zip(blocks, out)])
    snap = np.concatenate([s[: len(b)] for b, (_, s) in zip(blocks, out)])
    print(f"store-site: {n} x {S} in {time.time() - t0:.0f} s", flush=True)

    # Nearest stores by map distance, queried in spatially sorted chunks
    nn = np.zeros((n, K_NN), np.int32)
    for i in range(0, n, 500):
        dm = geo.haversine(lat[i:i + 500, None], lon[i:i + 500, None], lat[None], lon[None])
        nn[i:i + 500] = np.argsort(dm, 1)[:, 1:K_NN + 1]
    order = np.lexsort((lon, np.round(lat / 0.05)))
    chunks = [order[i:i + CHUNK] for i in range(0, n, CHUNK)]

    def nn_chunk(c):
        u = np.unique(np.r_[c, nn[c].ravel()])
        d, _ = table(lat[u], lon[u])
        return d[np.searchsorted(u, c)[:, None], np.searchsorted(u, nn[c])]

    nn_km = np.zeros((n, K_NN))
    for c, d in zip(chunks, run(chunks, nn_chunk)):
        nn_km[c] = d
    print(f"nearest stores: {n} x {K_NN} in {time.time() - t0:.0f} s", flush=True)

    # Calibration sample: random stores to targets spread over 1-250 km in log space, split into fit and test halves
    rng = np.random.default_rng(4370)
    pairs = []
    for i in rng.choice(n, N_CAL_SRC, replace=False):
        dm = geo.haversine(lat[i], lon[i], lat, lon)
        pairs += [(i, int(np.argmin(np.abs(dm - t)))) for t in np.exp(rng.uniform(0.0, np.log(250.0), N_CAL_DST))]
    pairs = np.array(pairs)
    groups = [pairs[g:g + 10 * N_CAL_DST] for g in range(0, len(pairs), 10 * N_CAL_DST)]

    def cal_group(g):
        u = np.unique(g.ravel())
        d, _ = table(lat[u], lon[u])
        return d[np.searchsorted(u, g[:, 0]), np.searchsorted(u, g[:, 1])]

    road = np.concatenate(run(groups, cal_group))
    mapd = geo.haversine(lat[pairs[:, 0]], lon[pairs[:, 0]], lat[pairs[:, 1]], lon[pairs[:, 1]])
    cls = (mt[pairs[:, 0]] | mt[pairs[:, 1]]).astype(int)
    ok = np.isfinite(road) & (mapd > 0.5)
    half = rng.random(len(pairs)) < 0.5
    rel = np.abs(distances.apply(distances.fit(mapd[ok & half], road[ok & half], cls[ok & half]), mapd, cls) - road) / np.where(ok, road, 1.0)
    err = {}
    for a, b in ((1, 10), (10, 50), (50, 250)):
        m = ok & ~half & (mapd >= a) & (mapd < b)
        err[f"{a}-{b} km"] = dict(n=int(m.sum()), median=round(float(np.median(rel[m])), 4), p90=round(float(np.quantile(rel[m], 0.9)), 4))
    coef = distances.fit(mapd[ok], road[ok], cls[ok])

    # Unroutable pairs (islands without a ferry, snapping failures) fall back to the model
    dsite_map = geo.haversine(lat[:, None], lon[:, None], slat[None], slon[None])
    dnn_map = geo.haversine(lat[:, None], lon[:, None], lat[nn], lon[nn])
    meta = dict(source=PBF, data_version=EXTRACT, engine=IMAGE, profile="car (default car.lua), MLD, distances only",
                symmetric="mean of both directions plus the snap leg at each end", k_nn=K_NN,
                unroutable=dict(site=int(np.isnan(site_km).sum()), nn=int(np.isnan(nn_km).sum()), calibration=int((~np.isfinite(road)).sum())),
                snap_m=dict(median=round(float(np.median(snap)), 1), p99=round(float(np.quantile(snap, 0.99)), 1), max=round(float(snap.max()), 1)),
                ratio_site_median=round(float(np.nanmedian(site_km / np.maximum(dsite_map, 0.1))), 4),
                ratio_nn_median=round(float(np.nanmedian(nn_km / np.maximum(dnn_map, 0.1))), 4),
                model="road = map x exp(a + b ln map), (a, b) per class: flat, or either end in Gangwon or North Gyeongsang",
                coef=np.round(coef, 5).tolist(), test_error=err, calibration_pairs=int(ok.sum()), seconds=round(time.time() - t0))
    site_km = np.where(np.isnan(site_km), distances.apply(coef, dsite_map, np.repeat(mt[:, None], S, 1).astype(int)), site_km)
    nn_km = np.where(np.isnan(nn_km), distances.apply(coef, dnn_map, (mt[:, None] | mt[nn]).astype(int)), nn_km)
    np.savez_compressed(distances.CACHE, lat=lat, lon=lon, site_ids=np.array([s["id"] for s in sites]), site_km=site_km.astype(np.float32),
                        nn=nn, nn_km=nn_km.astype(np.float32), coef=coef, meta=json.dumps(meta))
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
