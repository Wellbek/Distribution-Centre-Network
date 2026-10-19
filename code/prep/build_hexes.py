"""Build data/kontur_hexes.npz (centre, population, province per H3 hexagon) from the Kontur Population GeoPackage."""
import sqlite3
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcn import geo  # noqa: E402

SOURCE = "Kontur Population: South Korea, 2023-11-01, H3 resolution 8, CC BY 4.0 (kontur_population_KR_20231101.gpkg.gz, md5 20f836be6e87ac3344d68b4a9fb31d7a)"


def centre(blob):
    # GeoPackage blob: 8-byte header then the envelope (minx, maxx, miny, maxy); a hexagon's centre is the envelope's centre
    minx, maxx, miny, maxy = struct.unpack("<4d" if blob[3] & 1 else ">4d", blob[8:40])
    return (minx + maxx) / 2, (miny + maxy) / 2


def main(gpkg):
    rows = sqlite3.connect(gpkg).execute("select geom, population from population").fetchall()
    x, y = np.array([centre(g) for g, _ in rows]).T
    pop = np.array([p for _, p in rows], np.float32)
    # Web Mercator (EPSG:3857) to degrees
    lon = np.degrees(x / 6378137.0)
    lat = np.degrees(2 * np.arctan(np.exp(y / 6378137.0)) - np.pi / 2)
    land = geo.load_land()
    prov = geo.province_of(lon, lat, land)
    # The outline is coarse at the coast: a hexagon within 5 km of it takes the province of the nearest outline point;
    # farther ones are offshore islands without a bridge, which Dasol does not serve [ASSUMPTION]
    vx = np.vstack([r for _, rings in land for r in rings])
    vp = np.concatenate([[name] * len(r) for name, rings in land for r in rings])
    for i in np.flatnonzero(prov == ""):
        d = geo.haversine(lat[i], lon[i], vx[:, 1], vx[:, 0])
        prov[i] = vp[d.argmin()] if d.min() <= 5.0 else ""
    keep = prov != ""
    print(f"{len(pop)} hexagons, {pop.sum():,.0f} people; kept {keep.sum()} on the mainland and nearby islands ({pop[keep].sum():,.0f} people)")
    np.savez_compressed(geo.DATA / "kontur_hexes.npz", lat=lat[keep], lon=lon[keep], pop=pop[keep],
                        province=prov[keep].astype(str), source=SOURCE)


if __name__ == "__main__":
    main(sys.argv[1])
