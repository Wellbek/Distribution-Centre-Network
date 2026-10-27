"""Replay selection rules on run 3's fully evaluated pool and check G1's own site search: python upper_level_replay.py [reps]."""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, search  # noqa: E402
from dcn.gp import GP, expected_improvement  # noqa: E402
from dcn.world import make_world  # noqa: E402

REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
POOL = REG["pool"]
X = np.array([p["features"] for p in POOL]); G = np.array([p["G1"] for p in POOL]) / 1e6; E = np.array([p["E"] for p in POOL]) / 1e6
K = np.array([p["k"] for p in POOL]); OK = np.array([p["ok98"] for p in POOL])
E_ok = np.where(OK, E, np.inf)
SEEDS = [i for i, p in enumerate(POOL) if p["origin"] == "G1-best"]


def blr(Xe, ye, Xr, alpha=1.0):
    # Bayesian linear regression on standardised features (Lecture 2), predictive mean and sd
    mx, sx = Xe.mean(0), Xe.std(0) + 1e-9
    A = np.c_[np.ones(len(Xe)), (Xe - mx) / sx]; Ar = np.c_[np.ones(len(Xr)), (Xr - mx) / sx]
    v = max(ye.var(), 1e-6)
    s2 = 0.1 * v
    S = np.linalg.inv(A.T @ A / s2 + alpha * np.eye(A.shape[1]) / v)
    m = S @ A.T @ ye / s2
    return Ar @ m, np.sqrt(np.einsum("ij,jk,ik->i", Ar, S, Ar) + s2)


def run(rule, init, budget, rng):
    done = list(init)
    while len(done) < budget:
        rest = np.array([i for i in range(len(POOL)) if i not in done])
        ev = np.array(done)
        if rule == "random":
            i = int(rng.choice(rest))
        elif rule == "G1 order":
            i = int(rest[np.argmin(G[rest])])
        else:
            y = E[ev] - G[ev]
            if rule == "BLR-EI":
                mu_r, sd = blr(X[ev], y, X[rest]); mu = G[rest] + mu_r
                inc = (G[ev] + blr(X[ev], y, X[ev])[0]).min()
                score = expected_improvement(mu, sd, inc)
            else:
                gp = GP().fit(X[ev], y)
                mu_r, sd = gp.predict(X[rest]); mu = G[rest] + mu_r
                inc = (G[ev] + gp.predict(X[ev])[0]).min()
                if rule == "GP-EI":
                    score = expected_improvement(mu, sd, inc)
                elif rule == "GP-LCB":
                    score = -(mu - 2.0 * sd)
                elif rule == "GP-TS":
                    score = -(mu + sd * rng.standard_normal(len(mu)))
                else:  # pure exploitation of the posterior mean
                    score = -mu
            i = int(rest[np.argmax(score)])
        done.append(i)
    return np.minimum.accumulate(E_ok[done])


def replay(reps):
    rules = ["random", "G1 order", "GP-EI", "GP-LCB", "GP-TS", "GP-mean", "BLR-EI"]
    best, top3 = E_ok.min(), np.sort(E_ok)[2]
    out = {}
    for init_name in ("13 G1 seeds", "5 random"):
        for rule in rules:
            deterministic = init_name == "13 G1 seeds" and rule in ("G1 order", "GP-EI", "GP-LCB", "GP-mean", "BLR-EI")
            curves = []
            for r in range(1 if deterministic else reps):
                rng = np.random.default_rng(r)
                init = SEEDS if init_name == "13 G1 seeds" else [int(x) for x in rng.choice(len(POOL), 5, replace=False)]
                curves.append(run(rule, init, C.BUDGET, rng))
            c = np.array(curves)
            row = dict(best_at_10=float(np.median(c[:, 9])), best_at_20=float(np.median(c[:, 19])), best_at_40=float(np.median(c[:, -1])),
                       p_pool_best=float(np.mean(c[:, -1] <= best + 1e-9)), p_top3=float(np.mean(c[:, -1] <= top3 + 1e-9)), reps=len(c))
            out[f"{init_name} | {rule}"] = row
            print(f"{init_name:12s} {rule:9s} median best after 10/20/40: {row['best_at_10']:7.0f} {row['best_at_20']:7.0f} {row['best_at_40']:7.0f}  "
                  f"P(pool best) {row['p_pool_best']:.2f}  P(top 3) {row['p_top3']:.2f}  ({len(c)} runs)", flush=True)
    return out


def pool_stats():
    # How diverse is the pool: the best candidates and how many sites they share
    order = np.argsort(E_ok)[:10]
    core = set(POOL[order[0]]["sites"])
    for i in order[1:]:
        core &= set(POOL[i]["sites"])
    per_k = {int(k): dict(n=int((K == k).sum()), best=float(E_ok[K == k].min()), median=float(np.median(E[K == k]))) for k in np.unique(K)}
    origins = {}
    for i in order:
        origins[POOL[i]["origin"]] = origins.get(POOL[i]["origin"], 0) + 1
    return dict(top10_shared_sites=sorted(core), top10_origins=origins, per_k=per_k, baseline_search=REG["baseline_search"]["total"] / 1e6)


def g1_search_check():
    # Is g1_best a local optimum of G1 under the full swap neighbourhood (every closed site), not only the 12 nearest?
    world = make_world(C.FULL["fraction"], C.SEED)
    hist = demand.make_history(world, np.random.default_rng(C.SEED + 1))
    ctx = evaluate.context(world, demand.fit(world, hist))
    J = len(ctx["fixed"])
    rows = []
    for k in range(8, 14):
        start = sorted(next(p["sites"] for p in POOL if p["k"] == k and p["origin"] == "G1-best"))
        cur = list(start); val = v0 = search.g1(ctx, start)[0]
        improved = True
        while improved:
            improved = False
            for i in range(k):
                for j in range(J):
                    if j in cur:
                        continue
                    cand = sorted(cur[:i] + [j] + cur[i + 1:])
                    v = search.g1(ctx, cand)[0]
                    if v < val - 1e3:
                        cur, val, improved = cand, v, True
                        break
                if improved:
                    break
        in_pool = any(sorted(p["sites"]) == cur for p in POOL)
        rows.append(dict(k=k, g1_start=v0 / 1e6, g1_full_swap=val / 1e6, changed=cur != start, sites=cur, in_pool=in_pool))
        print(f"k={k}: G1 {v0 / 1e6:,.0f} -> {val / 1e6:,.0f} M with full swaps; changed {cur != start}; in pool {in_pool}", flush=True)
    return rows


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    res = dict(pool=pool_stats())
    print(json.dumps(res["pool"], indent=1))
    res["g1_search"] = g1_search_check()
    res["replay"] = replay(reps)
    Path(__file__).with_name("upper_level_replay.json").write_text(json.dumps(res, indent=1))
