"""Re-score today's network and the best pool candidates with PyVRP routing instead of savings, same days and cost rules: python spark_hgs_rescore.py [sec_per_store]."""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from routing_gap import CODE, audit, hgs, world_ctx

sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import evaluate, routing  # noqa: E402

CTX, DAYS = world_ctx()
REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
PER_STORE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05


def networks():
    # Today's network, the top 5 of the reported search and the pool's best candidate of every k from 8 to 13
    pool = REG["pool"]
    nets = {"today": (CTX["current"], CTX["hist_assign"])}
    picks = [t["cand"] for t in REG["top5"]]
    for k in range(8, 14):
        ok = [i for i, p in enumerate(pool) if p["k"] == k and p["ok98"]]
        if ok:
            picks.append(min(ok, key=lambda i: pool[i]["E"]))
    for i in dict.fromkeys(picks):
        sites = np.array(pool[i]["sites"])
        nets[f"pool{i}-k{len(sites)}"] = (sites, evaluate.assign_lp(CTX, sites)["site"])
    return nets


NETS = networks()


def job(args):
    # One territory on one day: savings and PyVRP on the same matrix and demand
    name, j, d = args
    sites, assign = NETS[name]
    idx = np.flatnonzero(assign == j)
    D = routing.territory_matrix(CTX, j, idx)
    q = DAYS[d]["q"][idx]
    p = routing.Params()
    cw = routing.solve(D, q, p)
    routes, _, far = hgs(D, q, p, max(10.0, PER_STORE * len(idx)))
    h = audit(routes, D, q, p, far)
    return dict(net=name, dc=int(j), day=d, stores=len(idx), cw_veh=cw["vehicles"], cw_km=cw["km"], cw_fail=cw["failed"],
                cw_relay=sum(r["binding"] == "relay" for r in cw["routes"]), cw_miss=sum(r["binding"] == "violates limit" for r in cw["routes"]),
                hgs_veh=h["vehicles"], hgs_km=h["km"], hgs_relay=h["relay"], hgs_bad=h["bad"])


def total(rows, key):
    # Same monthly cost rules as E: owned fleet at the 0.671 quantile, spot above, fuel, relay driver-days
    used = sorted({r["dc"] for r in rows})
    nd = len(DAYS)
    V = np.zeros((len(used), nd)); KM = np.zeros(nd); OVER = np.zeros(nd); FAIL = np.zeros(nd)
    for r in rows:
        V[used.index(r["dc"]), r["day"]] = r[f"{key}_veh"]
        KM[r["day"]] += r[f"{key}_km"]; OVER[r["day"]] += r[f"{key}_relay"]
        FAIL[r["day"]] += r.get(f"{key}_fail", 0)
    w = np.array([d["w"] for d in DAYS])
    parts, owned, _ = evaluate.monthly(V, C.FUEL_KM * KM, C.LATE_PEN * FAIL, OVER, w, float(CTX["fixed"][used].sum()))
    return {k: float(v) for k, v in parts.items()} | dict(owned=int(owned.sum()), vehicles_day=float(w @ V.sum(0) / w.sum()))


def main():
    t0 = time.time()
    jobs = [(name, int(j), d) for name, (sites, assign) in NETS.items() for j in sites if (assign == j).any() for d in range(len(DAYS))]
    jobs.sort(key=lambda a: -int((NETS[a[0]][1] == a[1]).sum()))
    print(f"{len(NETS)} networks, {len(jobs)} territory-days, {PER_STORE} s per store", flush=True)
    rows = []
    with ProcessPoolExecutor(min(os.cpu_count() or 1, 16)) as ex:
        for r in ex.map(job, jobs):
            rows.append(r)
            if len(rows) % 20 == 0:
                print(f"[{time.time() - t0:6.0f}s] {len(rows)}/{len(jobs)}", flush=True)
    out = {}
    for name, (sites, _) in NETS.items():
        rs = [r for r in rows if r["net"] == name]
        out[name] = dict(k=len(sites), sites=[int(s) for s in sites], savings=total(rs, "cw"), hgs=total(rs, "hgs"),
                         hgs_bad=sum(r["hgs_bad"] for r in rs), cw_missed=sum(r["cw_miss"] for r in rs))
        print(f"{name:14s} k={len(sites):2d}  E savings {out[name]['savings']['total'] / 1e6:8,.0f} M  E PyVRP {out[name]['hgs']['total'] / 1e6:8,.0f} M  "
              f"vehicles/day {out[name]['savings']['vehicles_day']:6.1f} -> {out[name]['hgs']['vehicles_day']:6.1f}  bad routes {out[name]['hgs_bad']}", flush=True)
    base = out["today"]
    for key in ("savings", "hgs"):
        best = min((n for n in out if n != "today"), key=lambda n: out[n][key]["total"])
        print(f"{key}: best alternative {best} saving vs today {(base[key]['total'] - out[best][key]['total']) / 1e6:,.0f} M/month")
    Path(__file__).with_name("spark_hgs_rescore.json").write_text(json.dumps(dict(per_store=PER_STORE, days=[d["date"] for d in DAYS], networks=out, rows=rows), indent=1))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
