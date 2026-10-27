"""Why does the best redesign lose to today's network? Consistency, assignment, bound and local-search checks on E: python baseline_checks.py [fixed|relaxed|bounded]."""
import json
import sys
import time
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, geo  # noqa: E402
from dcn.world import make_world  # noqa: E402

WORLD = make_world(C.FULL["fraction"], C.SEED)
HIST = demand.make_history(WORLD, np.random.default_rng(C.SEED + 1))
MODEL = demand.fit(WORLD, HIST)
CTX = evaluate.context(WORLD, MODEL)
D_SEARCH = demand.sample_days(MODEL, WORLD, C.SEARCH_DAYS, C.SEED + 11, CTX["mask"])
D_FINAL = demand.sample_days(MODEL, WORLD, C.FINAL_DAYS, C.SEED + 12, CTX["mask"])
# Screening days for the local searches: one per calendar class, weighted as in the 7-day set
D_SCREEN = [next(d for d in D_SEARCH if d["label"] == lab) for lab in ("weekday", "weekend", "holiday or eve")]
REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
REC = REG["networks"]["recommended"]
NAMES = [s["name"] for s in WORLD["sites"]]
NEAR = np.argsort(geo.haversine(CTX["site_lat"][:, None], CTX["site_lon"][:, None], CTX["site_lat"][None], CTX["site_lon"][None]), 1)[:, 1:7]
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def E(sites, days, lo=None, hi=None, assign=None):
    ctx = dict(CTX, lo=CTX["lo"] if lo is None else lo, hi=CTX["hi"] if hi is None else hi)
    e = evaluate.evaluate(ctx, sorted(sites), days, assign=assign)
    if not e["feasible"]:
        return dict(total=float("inf"), ok98=False)
    keys = ["total", "fixed", "fleet", "fuel", "spot", "relay", "vehicles_day", "km_day", "over_limit_day", "missed_routes_day", "service_min", "ok98", "loads"]
    return {k: e[k] for k in keys}


def show(name, e):
    if not np.isfinite(e["total"]):
        log(f"{name}: infeasible")
        return
    log(f"{name}: E {e['total'] / 1e6:,.0f} M (fixed {e['fixed'] / 1e6:,.0f}, fleet {e['fleet'] / 1e6:,.0f}, fuel {e['fuel'] / 1e6:,.0f}, "
        f"spot {e['spot'] / 1e6:,.0f}, relay {e['relay'] / 1e6:,.0f}); {e['vehicles_day']:.0f} veh/day, {e['over_limit_day']:.0f} relay routes/day, "
        f"min service {e['service_min']:.3f}, loads {e['loads']}")


def fixed_checks():
    """X1-X3 on the 7 search days: reproduce run 3, then change one thing at a time."""
    cur = CTX["current"].tolist()
    rows = {}
    for name, sites, kw in [
        ("X1 today, historical assignment (run 3: 5,736)", cur, dict(assign=CTX["hist_assign"])),
        ("X1 best redesign k=10, LP 500-1,400 (run 3: 5,828)", REC, {}),
        ("X2 today's sites, LP assignment, no minimum, cap 1,400", cur, dict(lo=0)),
        ("X2 today's sites, LP assignment, no minimum, no cap", cur, dict(lo=0, hi=CTX["n"])),
        ("X3 best redesign k=10, LP, no minimum", REC, dict(lo=0)),
        ("X3 best redesign k=10 + Gangneung, LP, no minimum", sorted(REC + [21]), dict(lo=0)),
    ]:
        rows[name] = E(sites, D_SEARCH, **kw)
        show(name, rows[name])
    return rows


def local_search(start, lo, label, budget_s=2400):
    """First-improvement search on E over site sets (drop, swap with the 6 nearest, add) on 3 screening days."""
    cur = sorted(start)
    val = E(cur, D_SCREEN, lo=lo)["total"]
    seen, steps = {tuple(cur): val}, []
    log(f"{label}: start k={len(cur)} screen E {val / 1e6:,.0f} M")
    improved = True
    while improved and time.time() - T0 < budget_s:
        improved = False
        moves = [("drop", a, None, [x for x in cur if x != a]) for a in cur]
        moves += [("swap", a, int(b), sorted([x for x in cur if x != a] + [int(b)])) for a in cur for b in NEAR[a] if b not in cur]
        moves += [("add", None, b, sorted(cur + [b])) for b in range(len(NAMES)) if b not in cur]
        for kind, out_, in_, cand in moves:
            if time.time() - T0 > budget_s:
                break
            if tuple(cand) in seen or len(cand) * CTX["hi"] < CTX["n"] or len(cand) * lo > CTX["n"]:
                continue
            v = E(cand, D_SCREEN, lo=lo)["total"]
            seen[tuple(cand)] = v
            if v < val - 1e6:
                steps.append(dict(move=kind, out=None if out_ is None else NAMES[out_], inp=None if in_ is None else NAMES[in_], k=len(cand), screen_E=v))
                log(f"  {kind}: -{'' if out_ is None else NAMES[out_]} +{'' if in_ is None else NAMES[in_]} -> k={len(cand)}, screen E {v / 1e6:,.0f} M")
                cur, val, improved = cand, v, True
                break
    log(f"{label}: stop after {len(seen)} evaluations, k={len(cur)}, screen E {val / 1e6:,.0f} M")
    return dict(sites=cur, names=[NAMES[i] for i in cur], screen_E=val, evaluations=len(seen), steps=steps)


def confirm(res, lo):
    # Re-score a local optimum on the 7 search and 28 final days against today's network
    res["search"] = E(res["sites"], D_SEARCH, lo=lo)
    res["final"] = E(res["sites"], D_FINAL, lo=lo)
    show("  search days", res["search"]); show("  final days", res["final"])
    return res


def main():
    part = sys.argv[1] if len(sys.argv) > 1 else "fixed"
    out = Path(__file__).with_name(f"baseline_checks_{part}.json")
    if part == "fixed":
        res = fixed_checks()
        res["today_final"] = E(CTX["current"].tolist(), D_FINAL, assign=CTX["hist_assign"])
        show("today, final 28 days", res["today_final"])
    elif part == "relaxed":
        res = confirm(local_search(CTX["current"].tolist(), 0, "X4 no minimum, from today's sites"), 0)
    else:
        res = confirm(local_search(REC, CTX["lo"], "X5 within 500-1,400, from the best redesign"), CTX["lo"])
    out.write_text(json.dumps(res, indent=1, default=float))
    log(f"written {out.name}")


if __name__ == "__main__":
    main()
