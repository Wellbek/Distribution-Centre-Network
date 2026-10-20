"""Upper level: generation criteria G0 (centre of gravity) and G1 (p-median + route approximation), pool, budgeted search."""
import numpy as np
from scipy.optimize import linear_sum_assignment

from . import config as C
from . import distances
from . import geo
from .evaluate import assign_lp
from .gp import GP, expected_improvement


def greedy_assign(ctx, open_idx):
    # Nearest open site, then move the cheapest stores out of overloaded DCs
    d = ctx["dsite"][:, open_idx]
    a = d.argmin(1)
    load = np.bincount(a, minlength=len(open_idx))
    for _ in range(3):
        over = np.flatnonzero(load > ctx["hi"])
        if not len(over):
            break
        for o in over:
            members = np.flatnonzero(a == o)
            alt = d[members].copy(); alt[:, o] = np.inf
            alt[:, load >= ctx["hi"]] = np.inf
            extra = alt.min(1) - d[members, o]
            move = members[np.argsort(extra)[: load[o] - ctx["hi"]]]
            for m in move:
                t = int(np.argmin(np.where(load >= ctx["hi"], np.inf, d[m])))
                load[a[m]] -= 1; a[m] = t; load[t] += 1
    # Fill DCs below the minimum with the stores that cost least to move, as the LP will
    for u in np.flatnonzero(load < ctx["lo"]):
        donors = np.flatnonzero(load[a] > ctx["lo"])
        extra = d[donors, u] - d[donors, a[donors]]
        for m in donors[np.argsort(extra)]:
            if load[u] >= ctx["lo"]:
                break
            if load[a[m]] > ctx["lo"]:
                load[a[m]] -= 1; a[m] = u; load[u] += 1
    return a


def g1(ctx, open_idx, a=None):
    """Cheap criterion: fixed cost + load-based fleet + line-haul and continuous-approximation local km.
    Ignores the clock, except that stores beyond the 125 km reach ride relay routes by load, each with a second driver, as in E."""
    open_idx = np.asarray(open_idx)
    k = len(open_idx)
    if a is None:
        a = greedy_assign(ctx, open_idx)
    d = ctx["dsite"][np.arange(ctx["n"]), open_idx[a]]
    w, n_j = ctx["w"], np.bincount(a, minlength=k)
    W = np.bincount(a, w, k)
    routes = W / (0.92 * C.CAP)
    rbar = np.bincount(a, w * d, k) / np.maximum(W, 1e-9)
    x, y = ctx["lon"] * 111 * np.cos(np.radians(36)), ctx["lat"] * 111
    sx = np.sqrt(np.maximum(np.bincount(a, x * x, k) / np.maximum(n_j, 1) - (np.bincount(a, x, k) / np.maximum(n_j, 1)) ** 2, 1))
    sy = np.sqrt(np.maximum(np.bincount(a, y * y, k) / np.maximum(n_j, 1) - (np.bincount(a, y, k) / np.maximum(n_j, 1)) ** 2, 1))
    km = (2 * rbar * routes + 0.7124 * np.sqrt(n_j * 4 * np.pi * sx * sy) * distances.local_ratio()).sum()
    veh = np.ceil(routes * 1.08).sum()
    far = d > C.FAR_KM
    Wf = np.bincount(a[far], w[far], k)
    relay = np.ceil(Wf / (0.92 * C.CAP) - 1e-9)
    km += (2 * np.bincount(a[far], w[far] * d[far], k) / np.maximum(Wf, 1e-9) * relay).sum()
    veh += relay.sum()
    total = ctx["fixed"][open_idx].sum() + veh * C.VEHICLE_MONTH + C.DAYS_MONTH * (C.FUEL_KM * km + C.RELAY_DAY * relay.sum())
    return float(total), a


def g0_sites(ctx, k, seed):
    """Data Team's method: demand-weighted centre of gravity (k-means on map coordinates), snapped to distinct sites."""
    rng = np.random.default_rng(seed)
    X = np.c_[ctx["lon"] * np.cos(np.radians(36)), ctx["lat"]]
    w = ctx["w"]
    cent = X[rng.choice(len(X), k, replace=False, p=w / w.sum())]
    for _ in range(50):
        lab = ((X[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
        new = np.array([np.average(X[lab == c], axis=0, weights=w[lab == c]) if (lab == c).any() else cent[c] for c in range(k)])
        if np.allclose(new, cent):
            break
        cent = new
    S = np.c_[ctx["site_lon"] * np.cos(np.radians(36)), ctx["site_lat"]]
    cost = ((cent[:, None, :] - S[None]) ** 2).sum(-1)
    _, col = linear_sum_assignment(cost)
    return sorted(col.tolist())


def g1_best(ctx, k, start=None, n_near=12):
    """Greedy add from a warm start, then swaps between nearby candidate sites on G1."""
    J = len(ctx["fixed"])
    open_ = list(start or [])
    while len(open_) < k:
        open_.append(min((j for j in range(J) if j not in open_), key=lambda j: g1(ctx, open_ + [j])[0]))
    near = np.argsort(geo.haversine(ctx["site_lat"][:, None], ctx["site_lon"][:, None], ctx["site_lat"][None], ctx["site_lon"][None]), 1)[:, 1:n_near + 1]
    val = g1(ctx, open_)[0]
    for _ in range(2):
        improved = False
        for i in range(k):
            for j in near[open_[i]]:
                if j in open_:
                    continue
                cand = open_[:i] + [int(j)] + open_[i + 1:]
                v = g1(ctx, cand)[0]
                if v < val - 1e3:
                    open_, val, improved = cand, v, True
        if not improved:
            break
    return sorted(open_)


def feasible(ctx, sites):
    k = len(sites)
    return not (k * ctx["hi"] < ctx["n"] or k * ctx["lo"] > ctx["n"])


def build_pool(ctx, ks, per_k, seed):
    """Candidate pool: G1-best, G0 and random 1-2 swap neighbours for every k."""
    rng = np.random.default_rng(seed)
    J = len(ctx["fixed"])
    pool, seen = [], set()

    def add(s, origin):
        key = tuple(sorted(s))
        if key not in seen and feasible(ctx, list(key)):
            seen.add(key)
            pool.append(dict(sites=list(key), k=len(key), origin=origin))

    seeds, prev = {}, None
    for k in ks:
        best = g1_best(ctx, k, start=prev)
        prev = best
        seeds[k] = tuple(best)
        g0 = g0_sites(ctx, k, seed + k)
        add(best, "G1-best")
        add(g0, "G0 centre of gravity")
        # Today's sites are a candidate of their own k, and a third base for swaps
        bases = [(best, "G1-best"), (g0, "G0")]
        if k == len(ctx["current"]):
            add(ctx["current"].tolist(), "current sites")
            bases.append((ctx["current"].tolist(), "current sites"))
        tries = 0
        while sum(p["k"] == k for p in pool) < per_k and tries < 50 * per_k:
            base, name = bases[tries % len(bases)]
            tries += 1
            s = list(base)
            for _ in range(rng.integers(1, 3)):
                out_ = rng.integers(len(s)); new = rng.integers(J)
                if new not in s:
                    s[out_] = int(new)
            add(s, f"swap of {name}")
    for p in pool:
        lp = assign_lp(ctx, np.array(p["sites"]))
        a = np.searchsorted(np.array(p["sites"]), lp["site"]) if lp else greedy_assign(ctx, np.array(p["sites"]))
        p["G1"], _ = g1(ctx, p["sites"], a)
        p["features"] = features(ctx, p["sites"], a)
        p["seed"] = tuple(p["sites"]) == seeds[p["k"]]
    return pool


def features(ctx, sites, a):
    # Summary features the surrogate works on (raw coordinates fail at B = 40)
    sites = np.asarray(sites)
    d = ctx["dsite"][np.arange(ctx["n"]), sites[a]]
    loads = np.bincount(a, minlength=len(sites))
    w = ctx["w"]
    return [len(sites), float((w * d).sum() / w.sum()), float(np.percentile(d, 95)), float(d.max()),
            float(loads.std() / loads.mean()), float(w[d > 55].sum() / w.sum()), float((d > 125).mean())]


FEATURE_NAMES = ["k", "mean km to DC", "p95 km to DC", "max km to DC", "load imbalance (CV)", "demand share beyond 55 km", "store share beyond 125 km"]


def run_search(pool, evaluate, budget, rule, seed):
    """One budgeted search: G1 seeds first, then EI on a Kennedy-O'Hagan discrepancy GP (or random picks)."""
    rng = np.random.default_rng(seed)
    order = [i for i, p in enumerate(pool) if p["seed"]]
    log, done = [], set()
    for i in order[:budget]:
        e = evaluate(pool[i])
        done.add(i)
        log.append(dict(step=len(log) + 1, cand=i, rule="G1 seed", E=e["total"], G1=pool[i]["G1"], k=pool[i]["k"], ei=None, ok98=e["ok98"]))
    X = np.array([p["features"] for p in pool]); G = np.array([p["G1"] for p in pool])
    while len(log) < budget:
        rest = [i for i in range(len(pool)) if i not in done]
        if not rest:
            break
        if rule == "random":
            i = int(rng.choice(rest)); ei = None
        else:
            ev = np.array(sorted(done))
            y = np.array([next(r["E"] for r in log if r["cand"] == c) for c in ev]) - G[ev]
            gp = GP().fit(X[ev], y / 1e6)
            mu_r, sd_r = gp.predict(X[rest])
            mu = G[rest] / 1e6 + mu_r
            mu_ev = G[ev] / 1e6 + gp.predict(X[ev])[0]
            score = expected_improvement(mu, sd_r, mu_ev.min())
            pick = int(np.argmax(score)); i = rest[pick]; ei = float(score[pick])
        e = evaluate(pool[i])
        done.add(i)
        log.append(dict(step=len(log) + 1, cand=i, rule="EI on GP gap" if rule != "random" else "random", E=e["total"], G1=pool[i]["G1"], k=pool[i]["k"], ei=ei, ok98=e["ok98"]))
    return log
