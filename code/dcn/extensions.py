"""Bonus extensions on a finished run: a closure sequence along the lease expiries, robustness, value of information.

Called by run_full.py and run_reduced.py after the pipeline; adds "extensions" to results/<profile>/registry.json.
"""
import json
import time
from datetime import date

import numpy as np
from scipy.stats import norm

from . import config as C
from . import demand, distances, evaluate, routing, search
from .gp import GP
from .pipeline import RESULTS, _np
from .world import era_assignment, era_design, make_world

START = date(2027, 1, 1)                    # first month a redesign can operate [ASSUMPTION: two months to fit out a site]
MONTHS = 36                                 # to December 2029, when the last of today's leases expires
CAPITAL = ("Seoul", "Gyeonggi", "Incheon")
P3 = (0.25, 0.5, 0.25)                      # prior on low / reported / high value of each uncertain input [ASSUMPTION]


def _month(iso):
    # Months from START to the first month after a lease ending on iso
    y, m, _ = map(int, iso.split("-"))
    return (y - START.year) * 12 + m - START.month + 1


def generate(ctx, pool, log, E, ks, seed, rounds=4, n=200, q_pct=20, top=4):
    """Lecture 6's CbAS on site sets: propose from q, weight by prior ratio x P(E <= gamma), refit by weighted maximum likelihood."""
    rng = np.random.default_rng(seed)
    J = len(ctx["fixed"])
    # Success model: the search's own surrogate, G2 plus a GP on the gap, fitted on its evaluations only
    ev = sorted({r["cand"] for r in log})
    y = np.array([next(r["E"] for r in log if r["cand"] == i) for i in ev])
    gp = GP().fit(np.array([pool[i]["features"] for i in ev]), (y - np.array([pool[i]["G2"] for i in ev])) / 1e6)
    target = y.min() / 1e6
    seen = {tuple(sorted(p["sites"])) for p in pool}
    loglik = lambda S, pi: np.array([np.log(pi[x]).sum() + np.log(1 - pi[np.setdiff1d(np.arange(J), x)]).sum() for x in S])

    def score(S):
        A = [search.greedy_assign(ctx, np.array(x)) for x in S]
        g2 = np.array([search.g1(ctx, x, a, clock=True)[0] for x, a in zip(S, A)]) / 1e6
        mu, sd = gp.predict(np.array([search.features(ctx, x, a) for x, a in zip(S, A)]))
        return g2 + mu, sd

    out, rounds_by_k = [], {}
    for k in ks:
        # Prior: per-site inclusion probabilities of this k's pool (the generator's training data), lightly smoothed
        cnt = np.full(J, 0.2)
        for p in pool:
            if p["k"] == k:
                cnt[p["sites"]] += 1
        prior = np.clip(cnt / cnt.sum() * k, 1e-3, 0.999)
        q, hist = prior.copy(), []
        for t in range(rounds):
            S = [np.sort(rng.choice(J, k, replace=False, p=q / q.sum())) for _ in range(n)]
            mu, sd = score(S)
            gamma = max(np.percentile(mu, q_pct), target)          # the bar rises each round, capped at the target
            lw = loglik(S, prior) - loglik(S, q) + norm.logcdf((gamma - mu) / np.maximum(sd, 1e-6))
            w = np.exp(lw - lw.max())
            inc = np.zeros(J)
            for x, wi in zip(S, w):
                inc[x] += wi
            q = np.clip(inc / inc.sum() * k, 1e-3, 0.999)
            hist.append(dict(round=t + 1, gamma=float(gamma * 1e6), best_pred=float(mu.min() * 1e6), distinct=len({tuple(x) for x in S})))
        S = [np.sort(rng.choice(J, k, replace=False, p=q / q.sum())) for _ in range(n)]
        mu, sd = score(S)
        new, picks = set(), []
        for i in np.argsort(mu, kind="stable"):
            key = tuple(int(v) for v in S[i])
            if key not in seen and key not in new:
                new.add(key); picks.append((key, float(mu[i] * 1e6)))
            if len(picks) == top:
                break
        best_pool = min((p for p in pool if p["k"] == k), key=lambda p: p["E"])
        for key, pred in picks:
            e = E(list(key), ctx)
            jac = 1 - len(set(key) & set(best_pool["sites"])) / len(set(key) | set(best_pool["sites"]))
            out.append(dict(k=k, sites=list(key), predicted=pred, E=e["total"] if e.get("feasible") else None, ok98=e.get("ok98"),
                            distance_to_pool_best=jac, pool_best_k=best_pool["E"]))
        rounds_by_k[str(k)] = hist
    return dict(evaluated=out, history=rounds_by_k, target=float(target * 1e6), pool_best=min(p["E"] for p in pool), rounds=rounds, n=n, q_pct=q_pct)


def run(profile):
    """Compute the three extensions for one profile and add them to its registry."""
    with evaluate.workers():
        return _run(profile)


def _run(profile):
    t0 = time.time()
    clock = lambda msg: print(f"[{time.time() - t0:6.1f}s] extensions: {msg}", flush=True)
    path = RESULTS / profile["name"] / "registry.json"
    reg = json.loads(path.read_text())
    world = make_world(profile["fraction"], C.SEED)
    hist = demand.make_history(world, np.random.default_rng(C.SEED + 1))
    model = demand.fit(world, hist)
    ctx = evaluate.context(world, model)
    ctx["tour_c"] = reg["meta"]["tour_c"]
    days = demand.sample_days(model, world, C.SEARCH_DAYS, C.SEED + 11, ctx["mask"])
    pool = reg["pool"]
    nets = {s["k"]: pool[s["cand"]]["sites"] for s in reg["sweep"]}
    rec = sorted(reg["networks"]["recommended"])
    k_rec = len(rec)
    ks = [k for k in nets if abs(k - k_rec) <= 3]
    open_ctx = dict(ctx, lo=0)
    cache = {}

    def E(sites, c=open_ctx, d=days, p=None, tag=""):
        key = (tuple(sorted(sites)), c["lo"], tag)
        if key not in cache:
            cache[key] = evaluate.evaluate(c, sorted(sites), d, p=p)
        return cache[key]

    def base(c=ctx, d=days, p=None):
        return evaluate.evaluate(c, c["current"], d, assign=c["hist_assign"], p=p)

    def table(c=ctx, d=days, p=None, tag=""):
        # Today's network and the sweep's best network of every k near the recommendation, under one changed input
        rows = {k: E(nets[k], c, d, p, tag) for k in ks}
        b = base(c, d, p)
        ok = {k: r["total"] for k, r in rows.items() if r.get("feasible") and r["ok98"]}
        kb = min(ok, key=ok.get)
        return dict(totals={str(k): r["total"] if r.get("feasible") else None for k, r in rows.items()},
                    baseline=b["total"], k_star=kb, best=ok[kb], rec=rows[k_rec]["total"], saving=b["total"] - rows[k_rec]["total"],
                    regret=rows[k_rec]["total"] - ok[kb])

    # 1. Closure sequence: the state is the set of open sites and their leases; territories are redrawn at once (no lease
    #    involved), then at each expiry the site is renewed for ten years or closed, and sites of the recommendation opened,
    #    whichever gives the lower monthly cost on E; "committed" may not renew a site outside the recommendation
    sites = world["sites"]
    idx = {s["id"]: i for i, s in enumerate(sites)}
    leases = sorted(((d["lease_expires_on"], idx[d["id"]]) for d in world["dcs"]))
    last = max(n_ for n_, (_, j) in enumerate(leases) if j not in rec)
    e_base = base()["total"]
    e_re = E(ctx["current"])["total"]

    def follow(committed):
        state, todo, steps = set(ctx["current"].tolist()), [j for j in rec if j not in ctx["current"]], []
        for n_, (iso, j) in enumerate(leases):
            if j in rec:
                steps.append(dict(date=iso, site=sites[j]["name"], action="renew", opened=[], total=E(state)["total"], k=len(state)))
                continue
            closed = state - {j}
            g = sorted(todo, key=lambda r: search.g1(open_ctx, sorted(closed | {r}), clock=True)[0])[:3]
            if committed and n_ == last:
                opts = [("close and open", closed | set(todo), list(todo))]
            else:
                opts = ([] if committed else [("renew", state, [])]) + [("close", closed, [])] + [("close and open", closed | {r}, [r]) for r in g]
            e = {i: E(s) for i, (_, s, _) in enumerate(opts)}
            ok = [i for i in e if e[i].get("feasible")]
            best1 = min((i for i in ok if len(opts[i][2]) == 1), key=lambda i: e[i]["total"], default=None)
            if best1 is not None:
                r1 = opts[best1][2][0]
                for r in [x for x in g if x != r1][:2]:
                    opts.append(("close and open", closed | {r1, r}, [r1, r]))
                    e[len(opts) - 1] = E(opts[-1][1])
                    if e[len(opts) - 1].get("feasible"):
                        ok.append(len(opts) - 1)
            pick = min(ok, key=lambda i: e[i]["total"])
            action, state, opened = opts[pick]
            state = set(state)
            todo = [r for r in todo if r not in opened]
            steps.append(dict(date=iso, site=sites[j]["name"], action=action, opened=[sites[r]["name"] for r in opened],
                              total=e[pick]["total"], k=len(state), options=len(opts)))
            clock(f"{'committed' if committed else 'myopic'} {iso} {sites[j]['name']}: {action} {[sites[r]['name'] for r in opened]} "
                  f"-> {e[pick]['total'] / 1e6:,.1f} M, k = {len(state)}")
        # The end state priced as in the months before (no minimum), and the DCs it leaves below the 500 a redesign must meet
        final = sorted(state)
        lp = evaluate.assign_lp(open_ctx, np.array(final))
        loads = {j: int((lp["site"] == j).sum()) for j in final}
        monthly = [e_re] * MONTHS
        for s in steps:
            for m in range(max(_month(s["date"]), 0), MONTHS):
                monthly[m] = s["total"]
        return dict(steps=steps, monthly=monthly, final=final, final_names=[sites[j]["name"] for j in final],
                    final_total=steps[-1]["total"], below_min=[dict(site=sites[j]["name"], stores=loads[j]) for j in final if loads[j] < ctx["lo"]],
                    final_is_rec=final == rec, cum=float(sum(monthly)))

    # One-shot: the recommendation from the first month, paying rent on released sites until their leases end
    e_rec = E(rec, ctx)
    one_shot = [e_rec["total"] + sum(sites[j]["monthly_fixed_cost"] for iso, j in leases if j not in rec and m < _month(iso)) for m in range(MONTHS)]
    sequence = dict(start=START.isoformat(), months=MONTHS, base_total=e_base, redrawn_total=e_re, rec_total=e_rec["total"],
                    leases=[dict(date=iso, site=sites[j]["name"], in_rec=j in rec) for iso, j in leases],
                    committed=follow(True), myopic=follow(False), one_shot=one_shot, cum_never=MONTHS * e_base, cum_redrawn=MONTHS * e_re,
                    cum_one_shot=float(sum(one_shot)), rent_left=float(sum(one_shot) - MONTHS * e_rec["total"]))
    clock(f"sequence: myopic ends at k = {len(sequence['myopic']['final'])}, committed at the recommendation: {sequence['committed']['final_is_rec']}")

    # 2. Robustness: demand regime shifts and a different distance source, today's network and the best network of each k
    st = world["stores"]
    capital = np.isin(st["province"][ctx["mask"]], CAPITAL)
    shift = lambda f: [dict(d, q=d["q"] * f) for d in days]
    ctx_model = dict(ctx, use_cache=False, dsite=distances.model_km(ctx["lat"][:, None], ctx["lon"][:, None], ctx["site_lat"][None],
                                                                     ctx["site_lon"][None], ctx["mountain"][:, None]))
    robust = [dict(name="as reported", **table())]
    for name, f in (("chain volume -15%", 0.85), ("chain volume +20%", 1.2), ("capital region +30%", np.where(capital, 1.3, 1.0))):
        robust.append(dict(name=name, **table(d=shift(f), tag=name)))
        clock(f"robustness {name}: k* {robust[-1]['k_star']}, saving {robust[-1]['saving'] / 1e6:,.1f} M")
    robust.append(dict(name="calibrated distance model only", **table(ctx_model, tag="model")))

    # 3. Value of information: expected regret of deciding now under a prior, for travel times and for demand
    def evpi(tables, probs):
        acts = [str(k) for k in ks]
        exp = {a: sum(p * t["totals"][a] for t, p in zip(tables, probs)) for a in acts if all(t["totals"][a] is not None for t in tables)}
        a_star = min(exp, key=exp.get)
        return dict(a_star=int(a_star), expected=exp[a_star],
                    evpi=float(sum(p * (t["totals"][a_star] - t["best"]) for t, p in zip(tables, probs))))

    grid = []
    for s_min, ps in zip((10, 15, 20), P3):
        for v, pv in zip((30.0, 35.0, 45.0), P3):
            pp = routing.Params(stop_h=s_min / 60, speed=v)
            t = table(p=pp, tag=f"{s_min}-{v}") if (s_min, v) != (15, 35.0) else robust[0]
            grid.append(dict(stop_min=s_min, speed=v, p=ps * pv, **{k: t[k] for k in ("totals", "baseline", "k_star", "best", "rec", "saving", "regret")}))
            clock(f"travel grid {s_min} min, {v:.0f} km/h: k* {t['k_star']}, regret of k = {k_rec}: {t['regret'] / 1e6:,.1f} M")
    travel = dict(grid=grid, **evpi(grid, [g["p"] for g in grid]))
    volume = dict(rows=[robust[1], robust[0], robust[2]], **evpi([robust[1], robust[0], robust[2]], P3))
    oracle = dict(model, a=st["rate_true"] * 1e6, b=np.full(len(st["rate_true"]), 1e6))
    t_true = table(d=demand.sample_days(oracle, world, C.SEARCH_DAYS, C.SEED + 11, ctx["mask"]), tag="true rates")
    rates = dict(row=t_true, evpi=t_true["regret"])
    clock(f"VOI: travel times {travel['evpi'] / 1e6:,.1f} M/month, chain volume {volume['evpi'] / 1e6:,.1f}, store rates {rates['evpi'] / 1e6:,.1f}")

    # 5. Drift: today's network as if its last redesign had been in another year, the assumption the saving rests on
    best_red = min(x["total"] for x in reg["sweep"] if x["ok98"])
    slat, slon = ctx["site_lat"], ctx["site_lon"]
    drift = []
    for yr in (2010, 2013, 2016, 2019, 2022, 2026):
        sy, _, n_open = era_design(world, yr)
        a = np.array(sy)[era_assignment(st["lat"], st["lon"], st["rate_true"], st["year"], slat[sy], slon[sy], world["max_stores"], design_year=yr)]
        e = evaluate.evaluate(ctx, sy, days, assign=a[ctx["mask"]])
        drift.append(dict(year=yr, stores_open=n_open, sites=[sites[j]["name"] for j in sy], total=e["total"], ok98=e["ok98"], saving=e["total"] - best_red))
        clock(f"drift: designed in {yr} ({n_open} stores open): today's cost {e['total'] / 1e6:,.1f} M, saving of the best redesign {(e['total'] - best_red) / 1e6:,.1f} M")

    # 4. Candidate generation (Lecture 6, CbAS), evaluated in full on the search days
    gen = generate(ctx, pool, reg["log_bo"], E, [k for k in (k_rec - 1, k_rec, k_rec + 1) if k in nets], C.SEED + 21)
    best_gen = min((g for g in gen["evaluated"] if g["E"] is not None and g["ok98"]), key=lambda g: g["E"], default=None)
    clock(f"generation: {len(gen['evaluated'])} new networks evaluated, best {best_gen['E'] / 1e6 if best_gen else float('nan'):,.1f} M against the pool's best {gen['pool_best'] / 1e6:,.1f} M")

    reg["extensions"] = dict(sequence=sequence, robustness=robust, voi=dict(travel=travel, volume=volume, rates=rates, prior=P3), generation=gen, drift=drift,
                             ks=ks, evaluations=len(cache), runtime_s=round(time.time() - t0, 1))
    path.write_text(json.dumps(reg, default=_np))
    clock(f"{len(cache)} evaluations, written to {path}")
    return reg["extensions"]


if __name__ == "__main__":
    import sys
    run(C.FULL if (sys.argv[1:] or ["full"])[0] == "full" else C.REDUCED)
