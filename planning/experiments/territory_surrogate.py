"""Learned territory cost (non-negative least squares on per-store sums) as G and inside a facility-location MILP: python territory_surrogate.py."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, lsq_linear, milp

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, routing  # noqa: E402
from dcn.world import make_world  # noqa: E402

WORLD = make_world(C.FULL["fraction"], C.SEED)
HIST = demand.make_history(WORLD, np.random.default_rng(C.SEED + 1))
MODEL = demand.fit(WORLD, HIST)
CTX = evaluate.context(WORLD, MODEL)
D_SEARCH = demand.sample_days(MODEL, WORLD, C.SEARCH_DAYS, C.SEED + 11, CTX["mask"])
D_FINAL = demand.sample_days(MODEL, WORLD, C.FINAL_DAYS, C.SEED + 12, CTX["mask"])
D_SCREEN = [next(d for d in D_SEARCH if d["label"] == lab) for lab in ("weekday", "weekend", "holiday or eve")]
W_SCREEN = np.array([d["w"] for d in D_SCREEN]) / sum(d["w"] for d in D_SCREEN)
REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
POOL = REG["pool"]
NAMES = [s["name"] for s in WORLD["sites"]]
VEH_DAY = C.VEHICLE_MONTH / C.DAYS_MONTH
FEAT = ["DC (intercept)", "stores", "cages", "road km", "cage-km", "stores beyond 55 km", "stores beyond 125 km"]
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def per_store(j):
    # Per-store feature rows for DC j: the territory feature is their sum, so the learned cost is linear in the assignment
    d = CTX["dsite"][:, j]
    w = CTX["w"]
    return np.c_[np.ones(CTX["n"]), w, d, w * d, d > C.REACH_KM, d > C.FAR_KM].astype(float)


def territory_rows(sites, assign):
    # Route every territory on the screening days; return features and the day-weighted operating cost per DC
    X, y = [], []
    for j in sites:
        idx = np.flatnonzero(assign == j)
        if not len(idx):
            continue
        D = routing.territory_matrix(CTX, j, idx)
        cost = 0.0
        for w, day in zip(W_SCREEN, D_SCREEN):
            r = routing.solve(D, day["q"][idx])
            relay = sum(rr["binding"] == "relay" for rr in r["routes"])
            cost += w * (VEH_DAY * r["vehicles"] + C.FUEL_KM * r["km"] + C.RELAY_DAY * relay)
        X.append(np.r_[1.0, per_store(j)[idx].sum(0)])
        y.append(cost)
    return X, y


def fit(X, y):
    # Least squares with bounds (Lecture 1, a convex QP): every per-DC and per-store cost term non-negative, so a MILP
    # cannot exploit a negative coefficient (an unconstrained fit gave -3,038 KRW/day per store beyond 55 km)
    return lsq_linear(X, y, bounds=(0, np.inf)).x


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def g_learned(m, sites, assign):
    tot = CTX["fixed"][sites].sum()
    for j in sites:
        idx = np.flatnonzero(assign == j)
        if len(idx):
            tot += C.DAYS_MONTH * (m[0] + per_store(j)[idx].sum(0) @ m[1:])
    return float(tot)


def learned_milp(m, lo, time_limit=600):
    """Choose sites and territories at once: fixed + learned cost, on 5 km cells, store-count bounds; HiGHS MILP (Lecture 1)."""
    cell = np.floor(CTX["lat"] / 0.045).astype(int) * 100_000 + np.floor(CTX["lon"] / 0.056).astype(int)
    _, inv = np.unique(cell, return_inverse=True)
    nc, J = inv.max() + 1, len(CTX["fixed"])
    cnt = np.bincount(inv, minlength=nc).astype(float)
    cost = np.zeros((nc, J))
    for j in range(J):
        cost[:, j] = np.bincount(inv, per_store(j) @ m[1:], minlength=nc)
    cost *= C.DAYS_MONTH
    ny, nz = J, nc * J
    obj = np.r_[CTX["fixed"] + C.DAYS_MONTH * m[0], cost.ravel()]
    zi = np.arange(nz)
    A_as = sparse.csr_matrix((np.ones(nz), (zi // J, ny + zi)), shape=(nc, ny + nz))
    load = sparse.csr_matrix((np.repeat(cnt, J), (zi % J, ny + zi)), shape=(J, ny + nz))
    ydiag = sparse.csr_matrix((np.ones(J), (np.arange(J), np.arange(J))), shape=(J, ny + nz))
    cons = [LinearConstraint(A_as, 1, 1), LinearConstraint(load - CTX["hi"] * ydiag, -np.inf, 0), LinearConstraint(load - lo * ydiag, 0, np.inf)]
    res = milp(obj, constraints=cons, integrality=np.r_[np.ones(ny), np.zeros(nz)], bounds=Bounds(0, 1),
               options=dict(time_limit=time_limit, mip_rel_gap=1e-4, disp=False))
    sites = sorted(np.flatnonzero(res.x[:ny] > 0.5).tolist())
    return dict(sites=sites, names=[NAMES[j] for j in sites], objective=float(res.fun), status=res.message, cells=int(nc))


def E(sites, days, lo):
    e = evaluate.evaluate(dict(CTX, lo=lo), sites, days)
    return dict(total=float(e["total"]), vehicles_day=e["vehicles_day"], relay_day=e["over_limit_day"], ok98=e["ok98"], loads=e["loads"]) if e["feasible"] else None


def main():
    rng = np.random.default_rng(0)
    train_idx = sorted(rng.choice(len(POOL), 30, replace=False).tolist())
    nets = [(POOL[i]["sites"], None, CTX["lo"]) for i in train_idx]
    nets += [(CTX["current"].tolist(), CTX["hist_assign"], None), (CTX["current"].tolist(), None, 0)]
    cache = Path(__file__).with_name("territory_surrogate_train.npz")
    if cache.exists():
        z = np.load(cache)
        X, y, groups = z["X"], z["y"], z["groups"]
    else:
        X, y, groups = [], [], []
        for g, (sites, assign, lo) in enumerate(nets):
            if assign is None:
                assign = evaluate.assign_lp(dict(CTX, lo=lo), np.array(sites))["site"]
            Xi, yi = territory_rows(sites, assign)
            X += Xi; y += yi; groups += [g] * len(yi)
        X, y, groups = np.array(X), np.array(y), np.array(groups)
        np.savez(cache, X=X, y=y, groups=groups)
    log(f"training: {len(y)} territories from {len(nets)} networks (30 pool candidates, today's network with two assignments; 3 screening days each)")

    # Territory-level accuracy by leave-networks-out cross-validation
    folds = np.arange(len(nets)) % 5
    pred = np.zeros_like(y)
    for f in range(5):
        tr, te = folds[groups] != f, folds[groups] == f
        pred[te] = X[te] @ fit(X[tr], y[tr])
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    mape = float(np.median(np.abs(pred - y) / y))
    m = fit(X, y)
    coef = {FEAT[i]: float(m[i]) for i in range(len(FEAT))}
    log(f"territory cost model: cross-validated R2 {r2:.3f}, median abs error {100 * mape:.1f}%")
    for k, v in coef.items():
        log(f"  {k:22s} {v:12,.1f} KRW/day")

    # Network level: learned G against E on the pool candidates not used for training
    G_L = []
    for p in POOL:
        a = evaluate.assign_lp(CTX, np.array(p["sites"]))
        G_L.append(g_learned(m, p["sites"], a["site"]) if a else np.inf)
    G_L = np.array(G_L); E_pool = np.array([p["E"] for p in POOL]); G1 = np.array([p["G1"] for p in POOL]); ok = np.array([p["ok98"] for p in POOL])
    h = np.array([i for i in range(len(POOL)) if i not in train_idx])
    res = dict(train=train_idx, territories=len(y), cv_r2=float(r2), cv_median_abs_err=mape, coef=coef,
               spearman_learned=spearman(G_L[h], E_pool[h]), spearman_G1=spearman(G1[h], E_pool[h]))
    pick_L, pick_1 = h[np.argmin(G_L[h])], h[np.argmin(G1[h])]
    best = h[np.argmin(np.where(ok[h], E_pool[h], np.inf))]
    res.update(loss_learned=float(E_pool[pick_L] - E_pool[best]), loss_G1=float(E_pool[pick_1] - E_pool[best]),
               pick_learned_k=POOL[pick_L]["k"], pick_G1_k=POOL[pick_1]["k"], best_k=POOL[best]["k"],
               mean_abs_err_learned=float(np.mean(np.abs(G_L[h] - E_pool[h]) / E_pool[h])), mean_abs_err_G1=float(np.mean(np.abs(G1[h] - E_pool[h]) / E_pool[h])))
    log(f"held-out pool ({len(h)}): Spearman learned {res['spearman_learned']:.2f} vs G1 {res['spearman_G1']:.2f}; "
        f"mean abs error {100 * res['mean_abs_err_learned']:.1f}% vs {100 * res['mean_abs_err_G1']:.1f}%; "
        f"pick loss learned {res['loss_learned'] / 1e6:,.0f} M (k={res['pick_learned_k']}) vs G1 {res['loss_G1'] / 1e6:,.0f} M (k={res['pick_G1_k']}), best k={res['best_k']}")

    # The learned cost embedded in a facility-location MILP, with and without the 500-store minimum
    res["milp"] = {}
    for lo, name in ((CTX["lo"], "within 500-1,400"), (0, "no minimum, cap 1,400")):
        sol = learned_milp(m, lo)
        log(f"MILP {name}: k={len(sol['sites'])} {sol['names']} ({sol['status']}, {sol['cells']} cells)")
        sol["E_search"] = E(sol["sites"], D_SEARCH, lo)
        sol["E_final"] = E(sol["sites"], D_FINAL, lo)
        log(f"  E search {sol['E_search']['total'] / 1e6:,.0f} M, final {sol['E_final']['total'] / 1e6:,.0f} M, "
            f"{sol['E_final']['vehicles_day']:.0f} veh/day, {sol['E_final']['relay_day']:.0f} relay routes/day, loads {sol['E_final']['loads']}")
        res["milp"][name] = sol
    Path(__file__).with_name("territory_surrogate.json").write_text(json.dumps(res, indent=1, default=float))
    log("written territory_surrogate.json")


if __name__ == "__main__":
    main()
