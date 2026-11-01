"""Is the recommended network a local optimum of E? Best-improvement descent over every one-move neighbour (swap, drop, add) on the search days.

Run after run_full.py: python checks/local_search.py [workers] (about 25 core-seconds per evaluation, 560 evaluations a round).
Every evaluation is cached in results/checks/local_search_cache.jsonl, so an interrupted run resumes; the summary goes to results/checks/local_search.json.
The shipped files are the cached results quoted in problem-definition.md Section 5.
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, search  # noqa: E402
from dcn.world import make_world  # noqa: E402

OUT = CODE / "results" / "checks"
WORLD = make_world(C.FULL["fraction"], C.SEED)
MODEL = demand.fit(WORLD, demand.make_history(WORLD, np.random.default_rng(C.SEED + 1)))
CTX = evaluate.context(WORLD, MODEL)
M = CTX["mask"]
DAYS = dict(search=demand.sample_days(MODEL, WORLD, C.SEARCH_DAYS, C.SEED + 11, M),
            final=demand.sample_days(MODEL, WORLD, C.FINAL_DAYS, C.SEED + 12, M))
DAYS["held"] = demand.sample_days(MODEL, WORLD, C.HELDOUT_DAYS, C.SEED + 13, M, exclude=[d["date"] for d in DAYS["final"]])


def _score(args):
    sites, days = args
    e = evaluate.evaluate(CTX, list(sites), DAYS[days])
    return (float(e["total"]), bool(e["ok98"])) if e["feasible"] else (float("inf"), False)


def _final_held(sites):
    # As the pipeline: the fleet is sized on the final days and kept on the held-out days
    f = evaluate.evaluate(CTX, list(sites), DAYS["final"])
    h = evaluate.evaluate(CTX, list(sites), DAYS["held"], owned=np.array(f["owned_by_dc"]))
    return float(f["total"]), float(h["total"])


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    reg = json.loads((CODE / "results" / "full" / "registry.json").read_text())
    cache_f = OUT / "local_search_cache.jsonl"
    cache = {}
    if cache_f.exists():
        for line in cache_f.read_text().splitlines():
            r = json.loads(line)
            cache[tuple(r["sites"])] = (r["E"], r["ok98"])
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex, cache_f.open("a") as f:
        def score(nets):
            todo = [n for n in dict.fromkeys(tuple(n) for n in nets) if n not in cache]
            for n, v in zip(todo, ex.map(_score, [(n, "search") for n in todo], chunksize=1)):
                cache[n] = v
                f.write(json.dumps(dict(sites=list(n), E=v[0], ok98=v[1])) + "\n")
                f.flush()
            print(f"[{time.time() - t0:6.0f}s] {len(nets)} networks scored", flush=True)
            return [cache[tuple(n)] for n in nets]
        res = search.local_search(CTX, reg["networks"]["recommended"], score)
        ends = [res["path"][0], res["path"][-1]]
        for p, (f_, h_) in zip(ends, ex.map(_final_held, [tuple(p["sites"]) for p in ends])):
            p["E_final"], p["E_held"] = f_, h_
    rec, opt = ends
    assert abs(rec["E"] - reg["pool_best"]) < 1 and abs(rec["E_final"] - reg["finals"]["recommended"]["total"]) < 1, "start does not reproduce the registry"
    out = dict(path=res["path"], best_neighbour=res["best_neighbour"], rounds=len(res["path"]), evaluations=len(res["log"]),
               start=rec, optimum=opt, gain_search=rec["E"] - opt["E"], gain_final=rec["E_final"] - opt["E_final"], gain_held=rec["E_held"] - opt["E_held"],
               k_optimum=len(opt["sites"]), sites_optimum=[reg["sites"][j]["name"] for j in opt["sites"]])
    (OUT / "local_search.json").write_text(json.dumps(out, indent=1))
    for p in res["path"]:
        print(f"{p['move']:16s} {p['E'] / 1e6:,.1f} M")
    print(f"local optimum after {len(res['path']) - 1} moves; best neighbour {res['best_neighbour'] / 1e6:,.1f} M; "
          f"gain {out['gain_search'] / 1e6:.1f} M search, {out['gain_final'] / 1e6:.1f} M final, {out['gain_held'] / 1e6:.1f} M held-out days")


if __name__ == "__main__":
    main()
