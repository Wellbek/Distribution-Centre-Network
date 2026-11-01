"""Road shapes of the routes the demo draws, from a running OSRM server: python osrm/build_shapes.py [full|reduced]

Writes results/<profile>/shapes.json: one encoded polyline (precision 5) per leg the shown days drive, plus each store to its 12 nearest stores and to its DC in both networks, so that live solves draw on roads too; display only, costs use the cache.
A leg is stored in one direction; the demo reverses it for the other.
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
URL = "http://localhost:5000"
NEAR = 12


def leg(job):
    key, a, b = job
    q = f"{URL}/route/v1/driving/{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}?overview=simplified&geometries=polyline&exclude=ferry"
    with urllib.request.urlopen(q, timeout=60) as r:
        res = json.load(r)
    return key, res["routes"][0]["geometry"] if res.get("code") == "Ok" else None


def main(profile):
    reg = json.loads((ROOT / "results" / profile / "registry.json").read_text())
    S, sites = reg["stores"], reg["sites"]
    pos = lambda n: (sites[n[1]]["lat"], sites[n[1]]["lon"]) if n[0] == "d" else (S["lat"][n[1]], S["lon"][n[1]])
    # Leg keys "d12>s345": DC or store index at each end, as the demo looks them up
    jobs = {}
    for name, v in reg["show"].items():
        if not isinstance(v, dict) or "routes" not in v:
            continue
        for blk in v["routes"]:
            for r in blk["routes"]:
                nodes = [("d", blk["dc"])] + [("s", i) for i in r["stores"]] + [("d", blk["dc"])]
                for a, b in zip(nodes, nodes[1:]):
                    key = f"{a[0]}{a[1]}>{b[0]}{b[1]}"
                    jobs.setdefault(key, (key, pos(a), pos(b)))
    # Legs a live solve can use: each store to its nearest stores, and to its DC in either network
    lat, lon = np.array(S["lat"]), np.array(S["lon"])
    xy = np.c_[lat, lon * np.cos(np.radians(lat.mean()))]
    _, nn = cKDTree(xy).query(xy, NEAR + 1)
    have = lambda a, b: f"{a[0]}{a[1]}>{b[0]}{b[1]}" in jobs or f"{b[0]}{b[1]}>{a[0]}{a[1]}" in jobs
    for i, row in enumerate(nn):
        for j in row[1:]:
            a, b = ("s", int(min(i, j))), ("s", int(max(i, j)))
            if not have(a, b):
                key = f"s{a[1]}>s{b[1]}"; jobs[key] = (key, pos(a), pos(b))
        for dc in {S["base_dc"][i], S["rec_dc"][i]}:
            a, b = ("d", int(dc)), ("s", i)
            if not have(a, b):
                key = f"d{a[1]}>s{i}"; jobs[key] = (key, pos(a), pos(b))
    print(f"{len(jobs)} legs to fetch", flush=True)
    with ThreadPoolExecutor(8) as ex:
        out = dict(ex.map(leg, jobs.values()))
    miss = sum(v is None for v in out.values())
    (ROOT / "results" / profile / "shapes.json").write_text(json.dumps(dict(
        meta=dict(source="OSRM route service, same server and extract as data/road_cache.npz, overview=simplified, ferries excluded",
                  legs=len(out), missing=miss, registry=reg["meta"]["generated"]),
        legs={k: v for k, v in out.items() if v})))
    print(f"wrote results/{profile}/shapes.json: {len(out) - miss} legs, {miss} without a route")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
