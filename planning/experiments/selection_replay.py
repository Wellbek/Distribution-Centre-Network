"""Selection rule against random selection from random starts, replayed on run 7's fully evaluated pool: python selection_replay.py [reps].

No routing: every pool candidate already has its E on the 7 search days (the validation pass), so a replay only fits the GP.
First reproduces the reported search (G2 seeds, EI) exactly, then runs EI and random from the same random starts of 5 and 13 candidates, budget 40.
"""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn.search import run_search  # noqa: E402

REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
POOL = REG["pool"]
B = 40
BEST = min(p["E"] for p in POOL if p["ok98"])


def ev(p):
    return dict(total=p["E"], ok98=p["ok98"])


def search(starts, rule, seed):
    for i, p in enumerate(POOL):
        p["seed"] = i in starts
    log = run_search(POOL, ev, B, rule, seed)
    best, curve = float("inf"), []
    for r in log:
        if r["ok98"]:
            best = min(best, r["E"])
        curve.append(best)
    return curve


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    seeds = {i for i, p in enumerate(POOL) if p["origin"] == "G2-best"}
    rep = search(seeds, "ei", 437)
    assert np.allclose(rep, REG["curve_bo"]), "replay does not reproduce the reported search"
    print(f"reported search reproduced: best {rep[-1] / 1e6:,.1f} M, pool best {BEST / 1e6:,.1f} M", flush=True)
    out = dict(pool_best=BEST, budget=B, reps=reps, runs={})
    for n0 in (5, 13):
        for rule in ("ei", "random"):
            curves = []
            for s in range(reps):
                starts = set(np.random.default_rng(1000 + s).choice(len(POOL), n0, replace=False).tolist())
                curves.append(search(starts, rule, 2000 + s))
            c = np.array(curves)
            fin = c[:, -1]
            hit = np.argmax(c <= BEST + 1, axis=1).astype(float)
            hit[fin > BEST + 1] = np.nan
            out["runs"][f"{rule}_{n0}"] = dict(final=fin.tolist(), curves=c.tolist())
            print(f"{n0:2d} random starts, {rule:6s}: best after 40 median {np.median(fin) / 1e6:,.1f} M (p10 {np.percentile(fin, 10) / 1e6:,.1f}, p90 {np.percentile(fin, 90) / 1e6:,.1f}); "
                  f"median regret {np.median(fin - BEST) / 1e6:,.1f} M; pool best found {np.mean(fin <= BEST + 1):.0%}"
                  f"{f', median at evaluation {np.nanmedian(hit) + 1:.0f}' if np.any(~np.isnan(hit)) else ''}; "
                  f"median best after 20 {np.median(c[:, 19]) / 1e6:,.1f} M", flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
