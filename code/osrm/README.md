# Road-distance cache

`build_cache.py` writes `../data/road_cache.npz`, the only distance source of the runs.
It is shipped for transparency; the three commands in `../README.md` never touch the network.

## What is cached

| Pairs | Source |
|---|---|
| Every store to every site (10,000 x 60) | OSRM table service |
| Every store to its 50 nearest stores by map distance | OSRM table service |
| All other store pairs | `road = map x exp(a + b ln map)`, one line for flat pairs and one for pairs touching Gangwon or North Gyeongsang, fitted on about 4,000 OSRM pairs spread over 1-250 km; error measured on a held-out half |

Each value is the mean of both driving directions plus the snap leg from each point to the nearest road.
The file's `meta` holds the extract timestamp, engine, profile, snap statistics, unroutable counts, model coefficients and test error.

## Rebuild

OSRM preprocessing needs about 4 GB of memory, so it runs on a larger machine (here the DGX Spark); the queries run from the laptop through an SSH tunnel.
Engine `ghcr.io/project-osrm/osrm-backend:v6.0.0` (amd64 and arm64), default car profile with ferries excluded, MLD.

On the Spark (prefix `docker` with `sudo` if needed), after copying the extract into `~/osrm-korea/`:

```sh
cd ~/osrm-korea
docker run --rm -t -v "$PWD:/data" ghcr.io/project-osrm/osrm-backend:v6.0.0 osrm-extract -p /opt/car.lua /data/south-korea-latest.osm.pbf
docker run --rm -t -v "$PWD:/data" ghcr.io/project-osrm/osrm-backend:v6.0.0 osrm-partition /data/south-korea-latest.osrm
docker run --rm -t -v "$PWD:/data" ghcr.io/project-osrm/osrm-backend:v6.0.0 osrm-customize /data/south-korea-latest.osrm
docker run -d --name osrm -p 127.0.0.1:5000:5000 -v "$PWD:/data" ghcr.io/project-osrm/osrm-backend:v6.0.0 \
  osrm-routed --algorithm mld --max-table-size 2000 /data/south-korea-latest.osrm
curl -s "http://localhost:5000/route/v1/driving/126.978,37.5665;129.0756,35.1796?overview=false" | head -c 300
```

On the laptop, in `code/`:

```sh
ssh -N -L 5000:localhost:5000 spark      # keep open in a second terminal
python osrm/build_cache.py               # about 10-20 minutes, mostly waiting on the server
```

Stop the server afterwards with `docker stop osrm && docker rm osrm` on the Spark.
Rerun `build_cache.py` whenever the generated stores or sites change; the engine refuses a cache built for another world.
