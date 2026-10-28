"""Connection: E(candidate) = DC fixed + owned fleet + day-weighted operating cost from the lower level."""
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager

import numpy as np

from . import config as C
from . import distances
from . import routing
from .world import planning_mask, transport_lp


def context(world, model):
    """Precompute the planning stores, their weights and road km to every site."""
    m = planning_mask(world)
    st = world["stores"]
    lat, lon, mt = st["lat"][m], st["lon"][m], st["mountain"][m]
    sites = world["sites"]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    full = st["full"][m]
    dsite = distances.site_km(full, lat, lon, mt, slat, slon, [s["id"] for s in sites])
    current = np.array([i for i, s in enumerate(sites) if s["current"]])
    return dict(
        mask=m, full=full, lat=lat, lon=lon, mountain=mt, w=model["a"][m] / model["b"][m], dsite=dsite,
        fixed=np.array([s["monthly_fixed_cost"] for s in sites], float), site_lat=slat, site_lon=slon,
        lo=world["min_stores"], hi=world["max_stores"], n=int(m.sum()), current=current,
        hist_assign=current[st["current_dc"][m]],
    )


def reach_cost(ctx, open_idx):
    # Window-aware cost-to-serve: demand-weighted road km, steep beyond the noon reach, prohibitive beyond 125 km
    d = ctx["dsite"][:, open_idx]
    extra = np.where(d > C.REACH_KM, 3 * (d - C.REACH_KM), 0.0) + np.where(d > C.FAR_KM, 1e4, 0.0)
    return ctx["w"][:, None] * (d + extra)


def assign_lp(ctx, open_idx):
    """Capacitated transportation LP (HiGHS); integral because the bounds count stores. None if infeasible."""
    n, k = ctx["n"], len(open_idx)
    if k * ctx["hi"] < n or k * ctx["lo"] > n:
        return None
    res = transport_lp(reach_cost(ctx, open_idx), ctx["lo"], ctx["hi"])
    if res is None:
        return None
    z = res.x.reshape(n, k)
    du = res.ineqlin.marginals
    return dict(site=np.asarray(open_idx)[z.argmax(1)], frac=float(np.abs(z - z.round()).max()),
                price_hi=(-du[:k]).tolist(), price_lo=(-du[k:]).tolist())


def wquantile(x, w, q):
    # Weighted empirical quantile per row
    o = np.argsort(x, axis=-1, kind="stable")
    xs = np.take_along_axis(x, o, -1)
    cw = np.cumsum(w[o], -1) / w.sum()
    return np.array([xs[r][np.searchsorted(cw[r], q)] for r in range(x.shape[0])])


def monthly(V, fuel_d, pen_d, over_d, w, fixed, owned=None, relay=C.RELAY_DAY):
    """Monthly cost from per-DC daily vehicle needs; the owned fleet is the weighted 0.671 quantile unless given."""
    if owned is None:
        owned = np.ceil(wquantile(V, w, C.FLEET_Q)).astype(int)
    spot_d = C.SPOT_DAY * np.maximum(V - owned[:, None], 0).sum(0)
    wn = w / w.sum()
    parts = dict(fixed=fixed, fleet=float(owned.sum() * C.VEHICLE_MONTH), fuel=C.DAYS_MONTH * float(wn @ fuel_d),
                 spot=C.DAYS_MONTH * float(wn @ spot_d), penalty=C.DAYS_MONTH * float(wn @ pen_d),
                 relay=C.DAYS_MONTH * relay * float(wn @ over_d))
    parts["total"] = sum(parts.values())
    daily = (fixed + parts["fleet"]) / C.DAYS_MONTH + fuel_d + spot_d + pen_d + relay * over_d
    return parts, owned, daily


_POOL = None


@contextmanager
def workers(n=C.WORKERS):
    """Route territories in n processes inside this block; same numbers as one process."""
    global _POOL
    if n <= 1:
        yield
        return
    with ProcessPoolExecutor(n) as ex:
        _POOL = ex
        try:
            yield
        finally:
            _POOL = None


def _territory_days(job):
    # One DC: road matrix once, then every day (sel = the day's stores, None = all)
    geo, days, p, docks = job
    D = distances.territory(*geo)
    out = []
    for sel, q in days:
        Dd = D if sel is None else D[np.ix_(np.r_[0, sel + 1], np.r_[0, sel + 1])]
        out.append(routing.solve(Dd, q, p) if docks is None else routing.solve_waves(Dd, q, p, docks))
    return out


def territories(jobs):
    """Run territory jobs, biggest first, in the pool when one is open; results in job order."""
    order = sorted(range(len(jobs)), key=lambda i: -len(jobs[i][0][1]))
    todo = [jobs[i] for i in order]
    res = list(_POOL.map(_territory_days, todo)) if _POOL else [_territory_days(j) for j in todo]
    out = [None] * len(jobs)
    for i, r in zip(order, res):
        out[i] = r
    return out


def evaluate(ctx, open_idx, days, assign=None, owned=None, p=None, keep_routes=False, keep_stores=False, docks=None):
    """Full evaluation E over sampled days (the same days for every network, calendar-class weights); docks = departure waves."""
    p = p or routing.Params()
    open_idx = np.asarray(open_idx)
    lp = None
    if assign is None:
        lp = assign_lp(ctx, open_idx)
        if lp is None:
            return dict(feasible=False, reason=f"{len(open_idx)} DCs cannot hold {ctx['n']} stores within {ctx['lo']}-{ctx['hi']} per DC")
        assign = lp["site"]
    used = [int(j) for j in open_idx if (assign == j).any()]
    nd = len(days)
    w = np.array([d.get("w", 1.0) for d in days])
    V = np.zeros((len(used), nd)); KM = np.zeros_like(V); FAIL = np.zeros_like(V); OVER = np.zeros_like(V); MISS = np.zeros_like(V); LOST = np.zeros_like(V); DOCK = np.zeros_like(V)
    ontime = np.zeros(nd); total = np.zeros(nd)
    store_ok = np.zeros(ctx["n"]) if keep_stores else None
    census, routes_out = {}, []
    # Every store gets its daily delivery, even with zero cages ordered (brief §2.1)
    idx_by = [np.flatnonzero(assign == j) for j in used]
    jobs = [((ctx["dsite"][idx, j], ctx["full"][idx], ctx["lat"][idx], ctx["lon"][idx], ctx["mountain"][idx], ctx.get("use_cache", True)),
             [(None, day["q"][idx]) for day in days], p, docks) for j, idx in zip(used, idx_by)]
    for a_i, (j, idx_all, res) in enumerate(zip(used, idx_by, territories(jobs))):
        for d_i, r in enumerate(res):
            V[a_i, d_i], KM[a_i, d_i] = r["vehicles"], r["km"]
            # Stores without a delivery (beyond every route limit, or dropped without relay) are stock-outs [A §2.6]
            LOST[a_i, d_i] = r.get("missed", 0); total[d_i] += r.get("missed", 0)
            DOCK[a_i, d_i] = r.get("dock_over", 0)
            for rr in r["routes"]:
                census[rr["binding"]] = census.get(rr["binding"], 0) + w[d_i]
                # Relay routes pay a second driver; on time is by the clock; a route beyond even the relay limits is missed
                OVER[a_i, d_i] += rr["binding"] == "relay"
                over = rr["binding"] == "violates limit"
                MISS[a_i, d_i] += over
                LOST[a_i, d_i] += len(rr["seq"]) if over else 0
                FAIL[a_i, d_i] += 0 if over else int((np.array(rr["arr"]) > C.FAIL_AT).sum())
                good = 0 if over else int((np.array(rr["arr"]) <= p.deadline + 1e-9).sum())
                ontime[d_i] += good; total[d_i] += len(rr["seq"])
                if keep_stores and not over:
                    store_ok[idx_all[rr["seq"]][np.array(rr["arr"]) <= p.deadline + 1e-9]] += w[d_i]
            if keep_routes:
                routes_out.append(dict(dc=j, day=d_i, routes=[dict(stores=idx_all[rr["seq"]].tolist(), arr=[round(x, 3) for x in rr["arr"]],
                                       ret=round(rr["ret"], 3), depart=rr.get("depart", p.depart), km=round(rr["km"], 1), load=round(rr["load"], 1), binding=rr["binding"]) for rr in r["routes"]]))
    fuel_d = C.FUEL_KM * KM.sum(0); pen_d = C.LATE_PEN * FAIL.sum(0) + C.STOCKOUT_PEN * LOST.sum(0); over_d = OVER.sum(0)
    parts, owned, daily = monthly(V, fuel_d, pen_d, over_d, w, float(ctx["fixed"][used].sum()), owned)
    service = ontime / np.maximum(total, 1)
    wn = w / w.sum()
    out = dict(feasible=True, open=used, k=len(used), **parts, owned=int(owned.sum()), owned_by_dc=owned.tolist(),
               V=V.tolist(), KM=KM.tolist(), fuel_d=fuel_d.tolist(), pen_d=pen_d.tolist(), over_d=over_d.tolist(), w=w.tolist(),
               vehicles_day=float(wn @ V.sum(0)), dock_over_day=float(wn @ DOCK.sum(0)), km_day=float(wn @ KM.sum(0)), over_limit_day=float(wn @ over_d), missed_routes_day=float(wn @ MISS.sum(0)), stockouts_day=float(wn @ LOST.sum(0)),
               daily_total=daily.tolist(), service=service.tolist(), service_min=float(service.min()),
               ok98=bool(service.min() >= 0.98), census={k: round(v, 2) for k, v in census.items()},
               loads=[int((assign == j).sum()) for j in used])
    if lp is not None:
        out["lp_frac"] = lp["frac"]; out["price_hi"] = lp["price_hi"]; out["price_lo"] = lp["price_lo"]
    if keep_routes:
        out["routes"] = routes_out
        out["assign"] = assign.tolist()
    if keep_stores:
        out["store_ontime"] = (store_ok / w.sum()).tolist()
    return out
