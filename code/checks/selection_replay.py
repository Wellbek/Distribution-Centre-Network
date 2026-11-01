"""Does the selection rule earn its keep without the G2 seeds? EI against random selection from random starts, replayed on the evaluated pool.

Run after run_full.py: python checks/selection_replay.py [reps] (about 3 minutes on one core; no routing, every pool candidate already has its E).
The replay first reproduces the reported search exactly (G2 seeds, EI, B = 40), then starts EI and random selection from the same 5 or 13 random pool candidates.
The summary goes to results/checks/selection_replay.json, the cached result quoted in problem-definition.md Section 5.
"""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from dcn.search import run_search  # noqa: E402

B = 40


def replay(pool, starts, rule, seed):
    """Best E with at least 98% before noon after each evaluation of one budgeted search."""
    for i, p in enumerate(pool):
        p["seed"] = i in starts
    best, curve = float("inf"), []
    for r in run_search(pool, lambda p: dict(total=p["E"], ok98=p["ok98"]), B, rule, seed):
        best = min(best, r["E"]) if r["ok98"] else best
        curve.append(best)
    return curve


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    reg = json.loads((CODE / "results" / "full" / "registry.json").read_text())
    pool = reg["pool"]
    best = min(p["E"] for p in pool if p["ok98"])
    reported = replay(pool, {i for i, p in enumerate(pool) if p["origin"] == "G2-best"}, "ei", 0)
    assert np.allclose(reported, reg["curve_bo"]), "replay does not reproduce the reported search"
    out = dict(budget=B, reps=reps, pool=len(pool), pool_best=best, reported_reproduced=True, runs=[])
    for n0 in (5, 13):
        for rule in ("ei", "random"):
            c = np.array([replay(pool, set(np.random.default_rng(1000 + s).choice(len(pool), n0, replace=False).tolist()), rule, 2000 + s) for s in range(reps)])
            found = c <= best + 1
            first = [int(np.argmax(f)) + 1 for f in found if f.any()]
            out["runs"].append(dict(starts=n0, rule=rule, found=float(found[:, -1].mean()), first_median=float(np.median(first)) if first else None,
                                    regret_median=float(np.median(c[:, -1] - best)), regret_p90=float(np.percentile(c[:, -1] - best, 90)),
                                    curve_median=np.median(c, 0).tolist()))
            r = out["runs"][-1]
            print(f"{n0:2d} random starts, {rule:6s}: pool best found in {r['found']:.0%} of {reps}, median regret {r['regret_median'] / 1e6:.1f} M "
                  f"(90th percentile {r['regret_p90'] / 1e6:.1f} M), median first hit {r['first_median']}", flush=True)
    (CODE / "results" / "checks" / "selection_replay.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
