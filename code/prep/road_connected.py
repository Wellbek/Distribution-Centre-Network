"""Keep only the hexagons in data/kontur_hexes.npz that reach Seoul by road without a ferry (needs the OSRM server)."""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import geo  # noqa: E402

URL = "http://localhost:5000"
SEOUL = (126.978, 37.5665)


def main():
    path = geo.DATA / "kontur_hexes.npz"
    h = dict(np.load(path))
    n = len(h["pop"])
    ok = np.zeros(n, bool)
    for i in range(0, n, 1000):
        lat, lon = h["lat"][i:i + 1000], h["lon"][i:i + 1000]
        coords = ";".join(f"{b:.6f},{a:.6f}" for a, b in zip(lat, lon)) + f";{SEOUL[0]},{SEOUL[1]}"
        src = ";".join(map(str, range(len(lat))))
        q = f"{URL}/table/v1/driving/{coords}?annotations=distance&sources={src}&destinations={len(lat)}&exclude=ferry"
        with urllib.request.urlopen(q, timeout=600) as r:
            d = json.load(r)["distances"]
        ok[i:i + len(lat)] = [row[0] is not None for row in d]
    drop = ~ok
    print(f"{drop.sum()} of {n} hexagons ({h['pop'][drop].sum():,.0f} people) have no road to Seoul without a ferry; dropped")
    for p in sorted(set(h["province"][drop])):
        print(f"  {p}: {np.sum(drop & (h['province'] == p))} hexagons, {h['pop'][drop & (h['province'] == p)].sum():,.0f} people")
    np.savez_compressed(path, **{k: (v[ok] if k != "source" else v) for k, v in h.items()})


if __name__ == "__main__":
    main()
