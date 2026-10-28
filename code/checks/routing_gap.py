"""Router accuracy: our lower level against PyVRP (a genetic algorithm with local search) on the same territories and days.

Optional check, needs `pip install pyvrp==0.11.3`; run after run_full.py: python checks/routing_gap.py [baseline|redrawn|recommended|site-list] [days] [sec_per_store] [dcs].
Results go to results/checks/; the shipped JSON files are the cached results quoted in problem-definition.md Section 2a.
"""
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import pyvrp
from pyvrp.stop import MaxRuntime

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, routing  # noqa: E402
from dcn.world import make_world  # noqa: E402

UNIT = 20  # cost units per KRW, so 350 KRW/km = 7 per metre


def world_ctx():
    # Rebuild the full run's world, model, context and search days exactly as the pipeline does
    world = make_world(C.FULL["fraction"], C.SEED)
    hist = demand.make_history(world, np.random.default_rng(C.SEED + 1))
    model = demand.fit(world, hist)
    ctx = evaluate.context(world, model)
    days = demand.sample_days(model, world, C.SEARCH_DAYS, C.SEED + 11, ctx["mask"])
    return ctx, days


def far_stores(D, p):
    # Stores no one-driver route can serve: the singleton route already breaks a limit
    return {i for i in range(1, len(D)) if not routing.ok_time([i], D, p)}


def _pyvrp(D, q, p, fixed, seconds, seed):
    # One capacitated VRP with load and stop dimensions, noon deadline, shift and km limits; D index 0 = DC.
    # Fleet = our router's count + 25% (at least 5): with one vehicle per store PyVRP stalls on rural territories (all singleton routes)
    n = len(q)
    fleet = len(routing._construct(D, q, p, False))
    vt = pyvrp.VehicleType(min(n, fleet + max(5, fleet // 4)), capacity=[C.CAP, p.max_stops], fixed_cost=round(fixed * UNIT), start_late=0,
                           max_duration=int((p.shift_end - p.break_h - p.depart) * 3600), max_distance=int(p.max_km * 1000),
                           unit_distance_cost=round(C.FUEL_KM * UNIT / 1000))
    late = int((p.deadline - p.depart) * 3600)
    clients = [pyvrp.Client(0, 0, delivery=[int(round(q[i])), 1], service_duration=int(p.stop_h * 3600), tw_late=late) for i in range(n)]
    km = np.ceil(D * 1000).astype(np.int64)
    sec = np.ceil(D / p.speed * 3600).astype(np.int64)
    np.fill_diagonal(km, 0); np.fill_diagonal(sec, 0)
    data = pyvrp.ProblemData(clients, [pyvrp.Depot(0, 0)], [vt], [km], [sec])
    res = pyvrp.solve(data, stop=MaxRuntime(seconds), seed=seed, display=False)
    return [[int(v) for v in r.visits()] for r in res.best.routes()], res.is_feasible()


def hgs(D, q, p, seconds, seed=1):
    """One DC-day in PyVRP, structured like E: one-driver routes for the stores one driver can reach, relay routes for the far ones."""
    n = len(q)
    far = far_stores(D, p)
    near = [i for i in range(1, n + 1) if i not in far]
    routes, feasible = [], True
    veh = C.VEHICLE_MONTH / C.DAYS_MONTH
    for group, pp, fixed, t in ((near, p, veh, 0), (sorted(far), replace(p, max_km=p.relay_km, shift_end=p.relay_shift_end), veh + C.RELAY_DAY, 1)):
        if not group:
            continue
        sub = np.r_[0, group]
        secs = seconds * len(group) / n
        rs, ok = _pyvrp(D[np.ix_(sub, sub)], q[np.array(group) - 1], pp, fixed, max(secs, 2.0), seed)
        routes += [([group[v - 1] for v in r], t) for r in rs]
        feasible &= ok
    return routes, feasible, far


def audit(routes, D, q, p, far):
    # Re-check every PyVRP route with the engine's own walk() and limits; return vehicles, km, relay routes
    pr = replace(p, max_km=p.relay_km, shift_end=p.relay_shift_end)
    seen, km, relay, bad = [], 0.0, 0, 0
    for seq, t in routes:
        pp = pr if t == 1 else p
        ok = routing.ok_time(seq, D, pp) and q[[s - 1 for s in seq]].sum() <= p.cap + 1e-9 and len(seq) <= p.max_stops
        ok = ok and (t == 0 or all(s in far for s in seq))
        bad += not ok
        km += routing.walk(seq, D, pp)[0]
        relay += t == 1
        seen += seq
    assert sorted(seen) == list(range(1, len(q) + 1)), "every store exactly once"
    return dict(vehicles=len(routes), km=km, relay=relay, bad=bad)


def day_cost(v, km, relay):
    return C.VEHICLE_MONTH / C.DAYS_MONTH * v + C.FUEL_KM * km + C.RELAY_DAY * relay


def main():
    net = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    day_ids = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0]
    per_store = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    only = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
    t0 = time.time()
    ctx, days = world_ctx()
    reg = json.loads((CODE / "results" / "full" / "registry.json").read_text())
    if net == "baseline":
        sites, assign = ctx["current"], ctx["hist_assign"]
    elif net == "redrawn":
        sites = ctx["current"]
        assign = evaluate.assign_lp(dict(ctx, lo=0), sites)["site"]
    else:
        sites = np.array(reg["networks"]["recommended"] if net == "recommended" else [int(x) for x in net.split("-")])
        assign = evaluate.assign_lp(ctx, sites)["site"]
    print(f"[{time.time() - t0:5.0f}s] world rebuilt, {ctx['n']} stores; network {net}: {len(sites)} DCs", flush=True)
    p = routing.Params()
    rows = []
    for d in day_ids:
        day = days[d]
        for j in sites:
            if only is not None and int(j) not in only:
                continue
            idx = np.flatnonzero(assign == j)
            D = routing.territory_matrix(ctx, j, idx)
            q = day["q"][idx]
            t1 = time.time()
            ours = routing.solve(D, q, p)
            t_ours = time.time() - t1
            ours_relay = sum(r["binding"] == "relay" for r in ours["routes"])
            secs = max(10.0, per_store * len(idx))
            routes, feas, far = hgs(D, q, p, secs)
            h = audit(routes, D, q, p, far)
            row = dict(net=net, day=d, label=day["label"], dc=int(j), stores=len(idx), cages=float(q.sum()), lb_load=int(np.ceil(q.sum() / C.CAP)),
                       far=len(far), ours_veh=ours["vehicles"], ours_km=round(ours["km"], 1), ours_relay=ours_relay, ours_s=round(t_ours, 2),
                       hgs_veh=h["vehicles"], hgs_km=round(h["km"], 1), hgs_relay=h["relay"], hgs_bad=h["bad"], hgs_feasible=feas, hgs_s=secs,
                       ours_cost=day_cost(ours["vehicles"], ours["km"], ours_relay), hgs_cost=day_cost(h["vehicles"], h["km"], h["relay"]))
            rows.append(row)
            print(f"[{time.time() - t0:5.0f}s] day {d} DC {j:2d} n={len(idx):4d} LB {row['lb_load']:3d} | ours {ours['vehicles']:3d} veh {ours['km']:8.0f} km "
                  f"({ours_relay} relay) | PyVRP {h['vehicles']:3d} veh {h['km']:8.0f} km ({h['relay']} relay, bad {h['bad']}) | "
                  f"cost gap {(row['ours_cost'] / row['hgs_cost'] - 1) * 100:5.1f}%", flush=True)
    tag = "-".join(map(str, day_ids)) + ("" if only is None else "_dc" + "-".join(map(str, only)))
    out = CODE / "results" / "checks" / f"routing_gap_{net}_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1))
    o_v, h_v = sum(r["ours_veh"] for r in rows), sum(r["hgs_veh"] for r in rows)
    o_c, h_c = sum(r["ours_cost"] for r in rows), sum(r["hgs_cost"] for r in rows)
    print(f"total: ours {o_v} vehicles, PyVRP {h_v}; daily cost ours {o_c / 1e6:.1f} M, PyVRP {h_c / 1e6:.1f} M ({(o_c / h_c - 1) * 100:.1f}%); written {out.name}")


if __name__ == "__main__":
    main()
