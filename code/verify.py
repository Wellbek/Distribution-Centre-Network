"""Independent checks of a run's results registry and the engines: python verify.py (about a minute)."""
import csv
import gzip
import itertools
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from dcn import config as C
from dcn import demand, evaluate, routing
from dcn.world import make_world

ROOT = Path(__file__).resolve().parent
PROFILE = C.FULL if C.DEMO_PROFILE == "full" else C.REDUCED
REG = json.loads((ROOT / "results" / PROFILE["name"] / "registry.json").read_text())
checks = []


def check(name, ok, detail):
    checks.append(dict(check=name, ok=bool(ok), detail=detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")


# Rebuild the world, model and the showcase day exactly as the pipeline did
world = make_world(PROFILE["fraction"], C.SEED)
hist = demand.make_history(world, np.random.default_rng(C.SEED + 1))
model = demand.fit(world, hist)
ctx = evaluate.context(world, model)
d_final = demand.sample_days(model, world, C.FINAL_DAYS, C.SEED + 12, ctx["mask"])
show_day = next((d for d in d_final if d["label"] == "weekday"), d_final[0])
check("world rebuilt", show_day["date"] == REG["show"]["day"]["date"] and ctx["n"] == REG["meta"]["stores_planning"],
      f"{ctx['n']} stores, showcase day {show_day['date']}")

# Route audit: recompute every showcase route from coordinates and demand
p = routing.Params()
for net in ("baseline_weekday", "recommended_weekday"):
    seen = np.zeros(ctx["n"], int)
    bad, viol, kmerr = 0, 0, 0.0
    for blk in REG["show"][net]["routes"]:
        j = blk["dc"]
        for r in blk["routes"]:
            idx = np.array(r["stores"])
            seen[idx] += 1
            D = routing.territory_matrix(ctx, j, idx)
            km, arr, ret = routing.walk(list(range(1, len(idx) + 1)), D, p)
            load = show_day["q"][idx].sum()
            kmerr = max(kmerr, abs(km - r["km"]))
            ok = load <= p.cap + 1e-9 and len(idx) <= p.max_stops and km <= p.max_km and arr[-1] <= p.deadline and ret + p.break_h <= p.shift_end
            if r["binding"] == "violates limit":
                viol += 1
                bad += len(idx) > 1 and ok
            else:
                bad += not ok
    check(f"{net.split('_')[0]}: every store served once", (seen == 1).all(), f"{(seen == 1).sum()}/{ctx['n']} stores")
    check(f"{net.split('_')[0]}: route limits", bad == 0 and kmerr < 0.2, f"{bad} unflagged violations, {viol} flagged over-limit routes, max km mismatch {kmerr:.3f}")

# Cost identities
for name, f in REG["finals"].items():
    s = f["fixed"] + f["fleet"] + f["fuel"] + f["spot"] + f["penalty"] + f["relay"]
    check(f"cost identity {name}", abs(s - f["total"]) < 1, f"components {s / 1e6:,.1f} M = total {f['total'] / 1e6:,.1f} M")
diff = REG["finals"]["baseline"]["total"] - REG["finals"]["recommended"]["total"]
check("paired saving equals total difference", abs(diff - REG["saving"]["final_mean"]) < 1e3,
      f"{REG['saving']['final_mean'] / 1e6:,.1f} M vs {diff / 1e6:,.1f} M")

# Transportation LP: integral, within bounds
rec = REG["networks"]["recommended"]
a = evaluate.assign_lp(ctx, np.array(rec))
loads = np.bincount(np.searchsorted(np.sort(rec), a["site"]), minlength=len(rec))
check("assignment LP within bounds", loads.min() >= ctx["lo"] and loads.max() <= ctx["hi"], f"loads {loads.min()}-{loads.max()} in [{ctx['lo']}, {ctx['hi']}]")

# Determinism: same candidate, same days, same cost
days2 = demand.sample_days(model, world, 3, C.SEED + 11, ctx["mask"])
e1 = evaluate.evaluate(ctx, rec, days2)["total"]; e2 = evaluate.evaluate(ctx, rec, days2)["total"]
check("deterministic evaluation", e1 == e2, f"{e1 / 1e6:,.3f} M twice")
with evaluate.workers(2):
    e3 = evaluate.evaluate(ctx, rec, days2)["total"]
check("worker pool = one process", e3 == e1, f"{e3 / 1e6:,.3f} M with 2 workers")

# Departure waves: every store once, no wave above the dock limit except the last
j = int(rec[0]); idx = np.flatnonzero(a["site"] == j)
wv = routing.solve_waves(routing.territory_matrix(ctx, j, idx), days2[0]["q"][idx], p, docks=4)
per = {t: sum(r["depart"] == t for r in wv["routes"]) for t in C.WAVES}
served = np.sort(np.concatenate([r["seq"] for r in wv["routes"]]))
check("departure waves", np.array_equal(served, np.arange(len(idx))) and all(per[t] <= 4 for t in C.WAVES[:-1]),
      f"{len(idx)} stores once; departures per wave {list(per.values())} with 4 docks")

# Outcome tables against the run's summary
tab = ROOT / "results" / PROFILE["name"] / "tables"
with gzip.open(tab / "vehicle_days.csv.gz", "rt") as f:
    vd = list(csv.DictReader(f))
with gzip.open(tab / "deliveries.csv.gz", "rt") as f:
    n_del = sum(1 for _ in f) - 1
ho = REG["history_ops"]
km_day = sum(float(r["km_driven"]) for r in vd) / ho["days"]
check("outcome tables", n_del == ho["deliveries"] == int((hist["y"] >= 0).sum()) and abs(km_day - ho["km_day"]) / ho["km_day"] < 1e-3,
      f"{n_del:,} deliveries = open store-days; {len(vd):,} vehicle-days, {km_day:,.0f} km/day")

# Heuristic accuracy against exact set partitioning on small instances
rng = np.random.default_rng(7)
gaps_v, gaps_km = [], []
for trial in range(25):
    j = int(rng.choice(rec))
    near = np.argsort(ctx["dsite"][:, j])[:60]
    idx = rng.choice(near, size=7, replace=False)
    q = rng.uniform(4, 12, size=7)  # heavier demand so several vehicles are needed
    D = routing.territory_matrix(ctx, j, idx)
    h = routing.solve(D, q, p)
    cols, cost = [], []
    for size in range(1, 8):
        for sub in itertools.combinations(range(1, 8), size):
            if q[[s - 1 for s in sub]].sum() > p.cap:
                continue
            best = None
            for perm in itertools.permutations(sub):
                km, arr, ret = routing.walk(list(perm), D, p)
                if km <= p.max_km and arr[-1] <= p.deadline and ret + p.break_h <= p.shift_end and (best is None or km < best):
                    best = km
            if best is not None:
                cols.append(sub); cost.append(1e4 + best)
    A = np.zeros((7, len(cols)))
    for c, sub in enumerate(cols):
        A[[s - 1 for s in sub], c] = 1
    res = milp(np.array(cost), constraints=LinearConstraint(A, 1, 1), integrality=np.ones(len(cols)), bounds=Bounds(0, 1))
    if res.status != 0:
        continue
    ev, ekm = int(round(res.x.sum())), float(res.fun - 1e4 * round(res.x.sum()))
    gaps_v.append(h["vehicles"] - ev); gaps_km.append((h["km"] - ekm) / ekm)
check("heuristic vs exact (7 stores, 25 instances)", np.mean(gaps_v) <= 0.2,
      f"extra vehicles mean {np.mean(gaps_v):.2f} (max {max(gaps_v)}), km gap mean {100 * np.mean(gaps_km):.1f}% (max {100 * max(gaps_km):.1f}%)")

# JavaScript fallback against Python without 2-opt on the live DC day
live = REG["live"]; j = live["dc"]; idx = np.array(live["stores"]); q = np.array(live["days"][0]["q"])
D = routing.territory_matrix(ctx, j, idx)
py1 = routing.solve(D, q, p)
Dr = routing.dist_matrix(ctx["site_lat"][j], ctx["site_lon"][j], np.round(ctx["lat"][idx], 4), np.round(ctx["lon"][idx], 4), ctx["mountain"][idx])
py0 = routing.solve(Dr, q, p, improve=False)  # the page stores coordinates to 4 decimals
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        pg.goto((ROOT.parent / "demo.html").resolve().as_uri()); pg.wait_for_timeout(300)
        js = pg.evaluate("""() => { const d = LIVE.days[0], s = SITES[LIVE.dc];
            const st = LIVE.stores.map((i, k) => [S.lat[i], S.lon[i], S.mountain[i], d.q[k]]);
            const r = solveJS([s.lat, s.lon], st, {deadline: 12, stop_h: 0.25, speed: 35, cap: 48, max_stops: 25, depart: 4, max_km: 250, shift_end: 13, break_h: 0.5});
            return [r.vehicles, r.km]; }""")
        external = pg.evaluate("[...document.querySelectorAll('script[src],link[href],img[src]')].length")
        b.close()
    check("JS engine = Python engine without 2-opt", js[0] == py0["vehicles"] and abs(js[1] - py0["km"]) / py0["km"] < 1e-3,
          f"JS {js[0]} vehicles {js[1]:.1f} km; Python {py0['vehicles']} vehicles {py0['km']:.1f} km; with 2-opt {py1['km']:.1f} km")
    check("demo has no external resources", external == 0, f"{external} external script/link/img tags")
except Exception as e:  # noqa: BLE001
    check("JS engine = Python engine without 2-opt", False, f"not run: {e}")

# Local app: live solve answers with the Python engine
proc = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, stdout=subprocess.PIPE, text=True)
try:
    line = proc.stdout.readline()
    url = re.search(r"http://localhost:\d+", line).group(0)
    body = json.dumps(dict(dc=[float(ctx["site_lat"][j]), float(ctx["site_lon"][j])],
                           stores=[[float(ctx["lat"][i]), float(ctx["lon"][i]), int(ctx["mountain"][i]), float(qq)] for i, qq in zip(idx, q)],
                           params=dict(deadline=12, stop_h=0.25, speed=35, cap=48, max_stops=25, depart=4, max_km=250, shift_end=13, break_h=0.5))).encode()
    t0 = time.time()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url + "/api/solve", body, {"Content-Type": "application/json"})).read())
    check("app.py live solve = routing.solve", r["vehicles"] == py1["vehicles"] and abs(r["km"] - py1["km"]) < 0.05,
          f"{r['vehicles']} vehicles {r['km']:.1f} km in {1000 * (time.time() - t0):.0f} ms")
finally:
    proc.terminate(); proc.wait()

# Embedded data equals the registry; G-vs-E statistic recomputes
html = (ROOT.parent / "demo.html").read_text()
emb = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1))
check("demo embeds this registry", emb["meta"]["generated"] == REG["meta"]["generated"], REG["meta"]["generated"])
ev = [c for c in REG["pool"] if c["E"] is not None and any(r["cand"] == REG["pool"].index(c) for r in REG["log_bo"])]
G = np.array([c["G1"] for c in ev]); E = np.array([c["E"] for c in ev])
sp = np.corrcoef(np.argsort(np.argsort(G)), np.argsort(np.argsort(E)))[0, 1]
check("Spearman recomputes", abs(sp - REG["r3"]["spearman"]) < 1e-9, f"{sp:.3f}")

out = ROOT / "results" / PROFILE["name"] / "verification.json"
out.write_text(json.dumps(dict(generated=time.strftime("%Y-%m-%dT%H:%M:%S"), registry=REG["meta"]["generated"], checks=checks), indent=1))
print(f"\n{sum(c['ok'] for c in checks)}/{len(checks)} passed -> {out}")
