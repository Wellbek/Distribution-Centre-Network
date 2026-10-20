"""Add a district (si, gun or gu) to every hexagon in data/kontur_hexes.npz: python prep/districts.py <geoBoundaries KOR ADM2 geojson>"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import geo  # noqa: E402

SOURCE = "geoBoundaries gbOpen KOR ADM2 (2020, 228 units, CC BY 3.0), commit 9469f09, simplified geometry"


def rings(g):
    # (name, outer ring) for every polygon part
    for f in g["features"]:
        geom = f["geometry"]
        for p in geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]:
            yield f["properties"]["shapeName"], np.asarray(p[0])


def main(path):
    raw = Path(path).read_bytes()
    g = json.loads(raw)
    h = dict(np.load(geo.DATA / "kontur_hexes.npz"))
    lat, lon = h["lat"], h["lon"]
    out = np.full(len(lat), "", dtype=object)
    for name, ring in rings(g):
        # Test only hexagons inside the ring's bounding box
        box = np.flatnonzero((lon >= ring[:, 0].min()) & (lon <= ring[:, 0].max()) & (lat >= ring[:, 1].min()) & (lat <= ring[:, 1].max()) & (out == ""))
        if len(box):
            out[box[geo.in_ring(lon[box], lat[box], ring)]] = name
    # A district belongs to the province holding most of its hexagons; the province outline is coarser, so a hexagon
    # outside any district or in another province's district takes the nearest vertex of a district of its own province
    prov = h["province"]
    home = {}
    for d in set(out) - {""}:
        names, counts = np.unique(prov[out == d], return_counts=True)
        home[d] = names[counts.argmax()]
    vx = np.vstack([r for _, r in rings(g)])
    vn = np.concatenate([[n] * len(r) for n, r in rings(g)])
    vp = np.array([home.get(n, "") for n in vn])
    fix = np.flatnonzero([o == "" or home[o] != p for o, p in zip(out, prov)])
    for i in fix:
        m = vp == prov[i]
        out[i] = vn[m][geo.haversine(lat[i], lon[i], vx[m, 1], vx[m, 0]).argmin()]
    out = np.array([o.split(" [")[0] for o in out], dtype=object)
    print(f"{len(lat)} hexagons: {len(lat) - len(fix)} inside a district of their province, {len(fix)} by nearest vertex; {len(set(out))} districts used")
    h["district"] = out.astype(str)
    h["district_source"] = f"{SOURCE}, md5 {hashlib.md5(raw).hexdigest()}"
    np.savez_compressed(geo.DATA / "kontur_hexes.npz", **h)


if __name__ == "__main__":
    main(sys.argv[1])
