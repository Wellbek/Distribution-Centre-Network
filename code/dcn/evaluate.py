"""Connection: E(candidate) = DC fixed + owned fleet + day-weighted operating cost from the lower level."""
import numpy as np
from scipy import sparse
from scipy.optimize import linprog

from . import config as C
from . import geo
from . import routing
from .world import planning_mask


def context(world, model):
    """Precompute the planning stores, their weights and road km to every site."""
    m = planning_mask(world)
    st = world["stores"]
    lat, lon, mt = st["lat"][m], st["lon"][m], st["mountain"][m]
    sites = world["sites"]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    dsite = geo.road_km(lat[:, None], lon[:, None], slat[None, :], slon[None, :], mountain1=mt[:, None])
    current = np.array([i for i, s in enumerate(sites) if s["current"]])
    return dict(
        mask=m, lat=lat, lon=lon, mountain=mt, w=model["a"][m] / model["b"][m], dsite=dsite,
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
    c = reach_cost(ctx, open_idx).ravel()
    A_eq = sparse.csr_matrix((np.ones(n * k), (np.repeat(np.arange(n), k), np.arange(n * k))), shape=(n, n * k))
    A_cap = sparse.csr_matrix((np.ones(n * k), (np.tile(np.arange(k), n), np.arange(n * k))), shape=(k, n * k))
    res = linprog(c, A_ub=sparse.vstack([A_cap, -A_cap]), b_ub=np.r_[np.full(k, ctx["hi"]), np.full(k, -ctx["lo"])],
                  A_eq=A_eq, b_eq=np.ones(n), bounds=(0, 1), method="highs")
    if res.status != 0:
        return None
    z = res.x.reshape(n, k)
    du = res.ineqlin.marginals
    return dict(site=np.asarray(open_idx)[z.argmax(1)], frac=float(np.abs(z - z.round()).max()),
                price_hi=(-du[:k]).tolist(), price_lo=(-du[k:]).tolist())


def wquantile(x, w, q):
    # Weighted empirical quantile per row
    o = np.argsort(x, axis=-1)
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


def evaluate(ctx, open_idx, days, assign=None, owned=None, p=None, keep_routes=False, keep_stores=False):
    """Full evaluation E over sampled days (common random numbers, calendar-stratum weights)."""
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
    V = np.zeros((len(used), nd)); KM = np.zeros_like(V); FAIL = np.zeros_like(V); OVER = np.zeros_like(V)
    ontime = np.zeros(nd); total = np.zeros(nd)
    store_ok = np.zeros(ctx["n"]) if keep_stores else None
    census, routes_out = {}, []
    for a_i, j in enumerate(used):
        idx_all = np.flatnonzero(assign == j)
        D_all = routing.dist_matrix(ctx["site_lat"][j], ctx["site_lon"][j], ctx["lat"][idx_all], ctx["lon"][idx_all], ctx["mountain"][idx_all])
        for d_i, day in enumerate(days):
            sel = np.arange(len(idx_all))  # every store gets its daily delivery, even with zero cages ordered (brief §2.1)
            D = D_all[np.r_[0, sel + 1]][:, np.r_[0, sel + 1]]
            r = routing.solve(D, day["q"][idx_all[sel]], p)
            V[a_i, d_i], KM[a_i, d_i], FAIL[a_i, d_i] = r["vehicles"], r["km"], r["failed"]
            for rr in r["routes"]:
                census[rr["binding"]] = census.get(rr["binding"], 0) + w[d_i]
                over = rr["binding"] == "violates limit"
                OVER[a_i, d_i] += over
                good = 0 if over else int((np.array(rr["arr"]) <= p.deadline + 1e-9).sum())
                ontime[d_i] += good; total[d_i] += len(rr["seq"])
                if keep_stores and not over:
                    store_ok[idx_all[sel[rr["seq"]]][np.array(rr["arr"]) <= p.deadline + 1e-9]] += w[d_i]
            if keep_routes:
                routes_out.append(dict(dc=j, day=d_i, routes=[dict(stores=idx_all[sel[rr["seq"]]].tolist(), arr=[round(x, 3) for x in rr["arr"]],
                                       ret=round(rr["ret"], 3), km=round(rr["km"], 1), load=round(rr["load"], 1), binding=rr["binding"]) for rr in r["routes"]]))
    fuel_d = C.FUEL_KM * KM.sum(0); pen_d = C.LATE_PEN * FAIL.sum(0); over_d = OVER.sum(0)
    parts, owned, daily = monthly(V, fuel_d, pen_d, over_d, w, float(ctx["fixed"][used].sum()), owned)
    service = ontime / np.maximum(total, 1)
    wn = w / w.sum()
    out = dict(feasible=True, open=used, k=len(used), **parts, owned=int(owned.sum()), owned_by_dc=owned.tolist(),
               V=V.tolist(), fuel_d=fuel_d.tolist(), pen_d=pen_d.tolist(), over_d=over_d.tolist(), w=w.tolist(),
               vehicles_day=float(wn @ V.sum(0)), km_day=float(wn @ KM.sum(0)), over_limit_day=float(wn @ over_d),
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
