"""Upper level: generation criteria G0 (centre of gravity) and G1, G2 (route approximation), pool, budgeted search."""
import numpy as np

from . import config as C
from . import distances
from . import geo
from .evaluate import assign_lp
from .gp import GP, expected_improvement
from .world import transport_lp


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
            move = members[np.argsort(extra, kind="stable")[: load[o] - ctx["hi"]]]
            # Each store goes to its nearest DC not yet full (plain lists: a numpy call per store is slow)
            ld = load.tolist()
            for m, row in zip(move.tolist(), d[move].tolist()):
                t = min(((v, j) for j, v in enumerate(row) if ld[j] < ctx["hi"]), default=(0, 0))[1]
                ld[a[m]] -= 1; a[m] = t; ld[t] += 1
            load = np.array(ld)
    # Fill DCs below the minimum with the stores that cost least to move, as the LP will
    for u in np.flatnonzero(load < ctx["lo"]):
        donors = np.flatnonzero(load[a] > ctx["lo"])
        extra = d[donors, u] - d[donors, a[donors]]
        for m in donors[np.argsort(extra, kind="stable")]:
            if load[u] >= ctx["lo"]:
                break
            if load[a[m]] > ctx["lo"]:
                load[a[m]] -= 1; a[m] = u; load[u] += 1
    return a


def _spread(ctx, a, k):
    # Stores per territory and the standard deviations of their east-west and north-south km
    x, y = ctx["lon"] * 111 * np.cos(np.radians(36)), ctx["lat"] * 111
    n_j = np.bincount(a, minlength=k)
    sx = np.sqrt(np.maximum(np.bincount(a, x * x, k) / np.maximum(n_j, 1) - (np.bincount(a, x, k) / np.maximum(n_j, 1)) ** 2, 1))
    sy = np.sqrt(np.maximum(np.bincount(a, y * y, k) / np.maximum(n_j, 1) - (np.bincount(a, y, k) / np.maximum(n_j, 1)) ** 2, 1))
    return n_j, sx, sy


def fit_tour(ctx, base):
    """Constant c of the local km c sqrt(n A) by least squares on the baseline's routed days (Lecture 2): routed km minus
    the out-and-back legs 2 rbar V, against sqrt(n A) times the local road-to-map ratio, day-weighted, through the origin."""
    open_idx = np.asarray(base["open"])
    a = np.searchsorted(open_idx, ctx["hist_assign"])
    k = len(open_idx)
    d, w = ctx["dsite"][np.arange(ctx["n"]), ctx["hist_assign"]], ctx["w"]
    n_j, sx, sy = _spread(ctx, a, k)
    rbar = np.bincount(a, w * d, k) / np.bincount(a, w, k)
    L = np.sqrt(n_j * 4 * np.pi * sx * sy) * distances.local_ratio()
    y = np.asarray(base["KM"]) - 2 * rbar[:, None] * np.asarray(base["V"])
    wd = np.asarray(base["w"])
    return float((wd * L[:, None] * y).sum() / (wd * L[:, None] ** 2).sum())


def g1(ctx, open_idx, a=None, clock=False):
    """Cheap criterion: fixed cost + load-based fleet + line-haul and continuous-approximation local km (c from fit_tour).
    Stores beyond the 125 km reach ride relay routes by load, each with a second driver, as in E.
    G1 ignores the clock; G2 (clock=True) also counts the routes the noon deadline and the km limit force:
    a store at road distance d can share a route with at most s_max(d) stores (system knowledge, brief R3)."""
    open_idx = np.asarray(open_idx)
    k = len(open_idx)
    if a is None:
        a = greedy_assign(ctx, open_idx)
    d = ctx["dsite"][np.arange(ctx["n"]), open_idx[a]]
    w, c = ctx["w"], ctx["tour_c"]
    n_j, sx, sy = _spread(ctx, a, k)
    W = np.bincount(a, w, k)
    routes = W / (0.92 * C.CAP)
    rbar = np.bincount(a, w * d, k) / np.maximum(W, 1e-9)
    if clock:
        leg = c * np.sqrt(4 * np.pi * sx * sy / np.maximum(n_j, 1)) * distances.local_ratio()
        dd, lg = np.minimum(d, C.FAR_KM), leg[a]
        s_max = np.minimum.reduce([np.full_like(d, C.MAX_STOPS), (C.DEADLINE - C.DEPART - dd / C.SPEED) / (C.STOP_H + lg / C.SPEED),
                                   (C.MAX_KM - 2 * dd) / np.maximum(lg, 1e-6)])
        routes = np.maximum(routes, np.bincount(a, 1 / np.maximum(s_max, 1), k))
    km = (2 * rbar * routes + c * np.sqrt(n_j * 4 * np.pi * sx * sy) * distances.local_ratio()).sum()
    veh = np.ceil(routes * 1.08).sum()
    far = d > C.FAR_KM
    Wf = np.bincount(a[far], w[far], k)
    relay = np.ceil(Wf / (0.92 * C.CAP) - 1e-9)
    km += (2 * np.bincount(a[far], w[far] * d[far], k) / np.maximum(Wf, 1e-9) * relay).sum()
    veh += relay.sum()
    total = ctx["fixed"][open_idx].sum() + veh * C.VEHICLE_MONTH + C.DAYS_MONTH * (C.FUEL_KM * km + C.RELAY_DAY * relay.sum())
    return float(total), a


def g0_sites(ctx, k, seed):
    """Data Team's method: each store to its nearest centre, each centre moved to its stores' demand-weighted centre of
    gravity on the map, repeated until the centres stop; then snapped to k distinct sites by the assignment LP (Lecture 1)."""
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
    res = transport_lp(cost, 0, 1)
    return sorted(res.x.reshape(k, -1).argmax(1).tolist())


def g1_best(ctx, k, start=None, n_near=12, clock=False):
    """Greedy add from a warm start, then swaps between nearby candidate sites on G1 (G2 with clock=True)."""
    J = len(ctx["fixed"])
    open_ = list(start or [])
    while len(open_) < k:
        open_.append(min((j for j in range(J) if j not in open_), key=lambda j: g1(ctx, open_ + [j], clock=clock)[0]))
    near = np.argsort(geo.haversine(ctx["site_lat"][:, None], ctx["site_lon"][:, None], ctx["site_lat"][None], ctx["site_lon"][None]), 1, kind="stable")[:, 1:n_near + 1]
    val = g1(ctx, open_, clock=clock)[0]
    for _ in range(2):
        improved = False
        for i in range(k):
            for j in near[open_[i]]:
                if j in open_:
                    continue
                cand = open_[:i] + [int(j)] + open_[i + 1:]
                v = g1(ctx, cand, clock=clock)[0]
                if v < val - 1e3:
                    open_, val, improved = cand, v, True
        if not improved:
            break
    return sorted(open_)


def hybrid(ctx, k):
    """Today's sites with the fewest changes: drop (k < 12) or add (k > 12) sites one at a time by G2, as leases expire."""
    s = ctx["current"].tolist()
    J = len(ctx["fixed"])
    while len(s) > k:
        s.remove(min(s, key=lambda j: g1(ctx, [x for x in s if x != j], clock=True)[0]))
    while len(s) < k:
        s.append(min((j for j in range(J) if j not in s), key=lambda j: g1(ctx, s + [j], clock=True)[0]))
    return sorted(s)


def feasible(ctx, sites):
    k = len(sites)
    return not (k * ctx["hi"] < ctx["n"] or k * ctx["lo"] > ctx["n"])


def build_pool(ctx, ks, per_k, seed):
    """Candidate pool for every k: G2-best (the search's seed), G1-best, G0, today's sites adjusted (hybrid), and random 1-2 swaps of these."""
    rng = np.random.default_rng(seed)
    J = len(ctx["fixed"])
    pool, seen = [], set()

    def add(s, origin):
        key = tuple(sorted(s))
        if key not in seen and feasible(ctx, list(key)):
            seen.add(key)
            pool.append(dict(sites=list(key), k=len(key), origin=origin))

    seeds, prev, prev2 = {}, None, None
    for k in ks:
        best = g1_best(ctx, k, start=prev)
        best2 = g1_best(ctx, k, start=prev2, clock=True)
        prev, prev2 = best, best2
        seeds[k] = tuple(best2)
        g0 = g0_sites(ctx, k, seed + k)
        hy = hybrid(ctx, k)
        add(best2, "G2-best")
        add(best, "G1-best")
        add(g0, "G0 centre of gravity")
        add(hy, "current sites" if k == len(ctx["current"]) else "today's sites adjusted")
        bases = [(best2, "G2-best"), (best, "G1-best"), (g0, "G0"), (hy, "today's sites")]
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
        p["G2"], _ = g1(ctx, p["sites"], a, clock=True)
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
    """One budgeted search: G2 seeds first, then EI on a Kennedy-O'Hagan discrepancy GP of E - G2 (or random picks)."""
    rng = np.random.default_rng(seed)
    order = [i for i, p in enumerate(pool) if p["seed"]]
    log, done = [], set()
    for i in order[:budget]:
        e = evaluate(pool[i])
        done.add(i)
        log.append(dict(step=len(log) + 1, cand=i, rule="G2 seed", E=e["total"], G1=pool[i]["G1"], G2=pool[i]["G2"], k=pool[i]["k"], ei=None, ok98=e["ok98"]))
    X = np.array([p["features"] for p in pool]); G = np.array([p["G2"] for p in pool])
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
        log.append(dict(step=len(log) + 1, cand=i, rule="EI on GP gap" if rule != "random" else "random", E=e["total"], G1=pool[i]["G1"], G2=pool[i]["G2"], k=pool[i]["k"], ei=ei, ok98=e["ok98"]))
    return log


def one_move(ctx, sites):
    """Every network one move away: swap an open site for any closed one, drop one, add one; only sizes the store bounds allow."""
    s, J = sorted(sites), len(ctx["fixed"])
    out = [(f"swap {a} for {b}", sorted([x for x in s if x != a] + [b])) for a in s for b in range(J) if b not in s]
    out += [(f"drop {a}", [x for x in s if x != a]) for a in s]
    out += [(f"add {b}", sorted(s + [b])) for b in range(J) if b not in s]
    return [(m, n) for m, n in out if len(n) * ctx["hi"] >= ctx["n"] and len(n) * ctx["lo"] <= ctx["n"]]


def local_search(ctx, start, score, min_gain=1e6):
    """Best-improvement descent on E over one_move until no neighbour saves min_gain; score maps a list of networks to (E, ok98) pairs."""
    cur = sorted(start)
    val = score([cur])[0][0]
    path, log = [dict(move="start", sites=cur, E=val)], []
    while True:
        moves = one_move(ctx, cur)
        vals = score([n for _, n in moves])
        log += [dict(round=len(path), move=m, sites=n, E=v, ok98=ok) for (m, n), (v, ok) in zip(moves, vals)]
        best = min((i for i, (_, ok) in enumerate(vals) if ok), key=lambda i: vals[i][0])
        if vals[best][0] > val - min_gain:
            return dict(path=path, log=log, best_neighbour=vals[best][0])
        cur, val = moves[best][1], vals[best][0]
        path.append(dict(move=moves[best][0], sites=cur, E=val))
