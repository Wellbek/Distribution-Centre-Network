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
if REG["live"]["days"][0].get("q_all"):
    wkend = next((d for d in d_final if d["label"] == "weekend"), d_final[1])
    lv = [show_day, wkend, demand.peak_day(model, world, ctx["mask"], C.SEED + 14), demand.average_day(model, world, ctx["mask"])]
    check("live demand days of every store match the sampler", all(np.allclose(np.round(d["q"], 2), r["q_all"]) for d, r in zip(lv, REG["live"]["days"])), f"{len(lv)} days x {len(lv[0]['q'])} stores")
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
            # Relay routes (two drivers) are held to the relay km and shift, everything else to one driver's limits
            relay = r["binding"] == "relay"
            km_max, end = (p.relay_km, p.relay_shift_end) if relay else (p.max_km, p.shift_end)
            ok = load <= p.cap + 1e-9 and len(idx) <= p.max_stops and km <= km_max and arr[-1] <= p.deadline and ret + p.break_h <= end
            if r["binding"] == "violates limit":
                viol += 1
                bad += len(idx) > 1 and ok
            else:
                bad += not ok
    check(f"{net.split('_')[0]}: every store served once", (seen == 1).all(), f"{(seen == 1).sum()}/{ctx['n']} stores")
    check(f"{net.split('_')[0]}: route limits", bad == 0 and kmerr < 0.2, f"{bad} unflagged violations, {viol} beyond even the relay limits, max km mismatch {kmerr:.3f}")
    # Vehicles against the lower bound max(load / 48, stores / 25) of every territory
    used = sum(len(blk["routes"]) for blk in REG["show"][net]["routes"])
    lb = sum(max(np.ceil(show_day["q"][np.concatenate([r["stores"] for r in blk["routes"]])].sum() / p.cap - 1e-9),
                 np.ceil(sum(len(r["stores"]) for r in blk["routes"]) / p.max_stops)) for blk in REG["show"][net]["routes"])
    check(f"{net.split('_')[0]}: vehicles against the load and stop bound", used >= lb, f"{used} vehicles, bound {lb:.0f} (+{100 * (used / lb - 1):.1f}%)")

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

# Heuristic accuracy against exact enumeration on small instances (Lecture 3): every route, then every split of the stores
rng = np.random.default_rng(7)
gaps_v, gaps_km, gaps_c = [], [], []
for trial in range(25):
    j = int(rng.choice(rec))
    near = np.argsort(ctx["dsite"][:, j])[:60]
    idx = rng.choice(near, size=7, replace=False)
    q = rng.uniform(4, 12, size=7)  # heavier demand so several vehicles are needed
    D = routing.territory_matrix(ctx, j, idx)
    h = routing.solve(D, q, p)
    route = {}
    for size in range(1, 8):
        for sub in itertools.combinations(range(1, 8), size):
            if q[[s - 1 for s in sub]].sum() > p.cap:
                continue
            for perm in itertools.permutations(sub):
                km, arr, ret = routing.walk(list(perm), D, p)
                if km <= p.max_km and arr[-1] <= p.deadline and ret + p.break_h <= p.shift_end and km < route.get(sub, np.inf):
                    route[sub] = km

    def splits(rest):
        # Every way to split the stores into routes: the first store's route, then the rest
        if not rest:
            yield []
            return
        for size in range(len(rest)):
            for others in itertools.combinations(rest[1:], size):
                sub = (rest[0],) + others
                if sub in route:
                    for tail in splits(tuple(x for x in rest[1:] if x not in others)):
                        yield [sub] + tail

    best = min(((len(sp), sum(route[r] for r in sp)) for sp in splits(tuple(range(1, 8)))), default=None)
    if best is None:
        continue
    ev, ekm = best
    gaps_v.append(h["vehicles"] - ev); gaps_km.append((h["km"] - ekm) / ekm)
    cost = lambda v, km: C.VEHICLE_MONTH / C.DAYS_MONTH * v + C.FUEL_KM * km
    gaps_c.append(cost(h["vehicles"], h["km"]) / cost(ev, ekm) - 1)
check("heuristic vs exact (7 stores, 25 instances)", np.mean(gaps_v) <= 0.2,
      f"extra vehicles mean {np.mean(gaps_v):.2f} (max {max(gaps_v)}), km gap mean {100 * np.mean(gaps_km):.1f}% (max {100 * max(gaps_km):.1f}%), "
      f"day cost gap mean {100 * np.mean(gaps_c):.1f}% (max {100 * max(gaps_c):.1f}%)")

# JavaScript fallback against Python without the segment reversal on the live DC day
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
            const r = solveJS([s.lat, s.lon], st, {deadline: 12, stop_h: 0.25, speed: 35, cap: 48, max_stops: 25, depart: 4, max_km: 250, shift_end: 13, break_h: 0.5, relay_km: 500, relay_shift_end: 19});
            return [r.vehicles, r.km]; }""")
        external = pg.evaluate("[...document.querySelectorAll('script[src],link[href],img[src]')].length")
        live = pg.evaluate("""() => { const P = R.pool, s = P.map((p, i) => (p.origin === "G2-best" ? i : -1)).filter(i => i >= 0); let l = []; for (const x of LIVE_SEARCH.run(P, s, R.log_bo.length, "ei", 1)) l = x; return l.map(x => x.cand); }""")
        b.close()
    check("JS engine = Python engine without the segment reversal", js[0] == py0["vehicles"] and abs(js[1] - py0["km"]) / py0["km"] < 1e-3,
          f"JS {js[0]} vehicles {js[1]:.1f} km; Python {py0['vehicles']} vehicles {py0['km']:.1f} km; with the segment reversal {py1['km']:.1f} km")
    check("demo has no external resources", external == 0, f"{external} external script/link/img tags")
    check("live search in the page repeats the reported search", live == [r["cand"] for r in REG["log_bo"]], f"{sum(x == r['cand'] for x, r in zip(live, REG['log_bo']))} of {len(REG['log_bo'])} picks equal")
except ImportError:
    print("SKIP  demo checks: playwright not installed (pip install playwright && playwright install chromium)")

# Local app: live solve answers with the Python engine
proc = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, stdout=subprocess.PIPE, text=True)
try:
    line = proc.stdout.readline()
    url = re.search(r"http://localhost:\d+", line).group(0)
    body = json.dumps(dict(dc=[float(ctx["site_lat"][j]), float(ctx["site_lon"][j])], site=int(j), ids=idx.tolist(),
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
E = np.array([c["E"] for c in ev])
for key, r3 in (("G2", REG["r3"]), ("G1", REG["r3_g1"])):
    G = np.array([c[key] for c in ev])
    b = np.polyfit(G, E, 1)
    r2 = 1 - ((E - np.polyval(b, G)) ** 2).sum() / ((E - E.mean()) ** 2).sum()
    check(f"least-squares R² of E on {key} recomputes", abs(r2 - r3["r2_line"]) < 1e-9, f"{r2:.3f}")

# Extensions: the sequence's months add up, and the unchanged scenario reproduces the sweep
x = REG.get("extensions")
if x:
    s = x["sequence"]
    c, m = s["committed"], s["myopic"]
    check("closure sequence adds up", all(abs(sum(p_["monthly"]) - p_["cum"]) < 1 and len(p_["monthly"]) == s["months"] for p_ in (c, m)) and c["final_is_rec"],
          f"{s['months']} months; committed path ends at the recommendation, {c['cum'] / 1e9:,.2f} bn KRW")
    sw = {r["k"]: r["total"] for r in REG["sweep"]}
    rows = x["robustness"][0]["totals"]
    check("extensions reuse the sweep", all(abs(v - sw[int(k)]) < 1 for k, v in rows.items()), f"k = {', '.join(rows)} equal to the sweep")
    if x.get("drift"):
        d16 = next(d for d in x["drift"] if d["year"] == 2016)
        check("drift sweep reproduces today's network in 2016", abs(d16["total"] - REG["baseline_search"]["total"]) < 1,
              f"{d16['total'] / 1e6:,.1f} M = baseline {REG['baseline_search']['total'] / 1e6:,.1f} M")

out = ROOT / "results" / PROFILE["name"] / "verification.json"
out.write_text(json.dumps(dict(generated=time.strftime("%Y-%m-%dT%H:%M:%S"), registry=REG["meta"]["generated"], checks=checks), indent=1))
print(f"\n{sum(c['ok'] for c in checks)}/{len(checks)} passed -> {out}")
