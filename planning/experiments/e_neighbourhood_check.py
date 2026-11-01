"""Exhaustive one-move neighbourhood of a network under E (swap with every closed site, drop, add): python e_neighbourhood_check.py [network] [workers].

Run 7 settings: the 7 search days of the pipeline; any neighbour within 25 M of the start is re-scored on the 28 final days.
Results are appended to e_neighbourhood_<network>.jsonl so an interrupted run can be resumed.
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate  # noqa: E402
from dcn.world import make_world  # noqa: E402

WORLD = make_world(C.FULL["fraction"], C.SEED)
HIST = demand.make_history(WORLD, np.random.default_rng(C.SEED + 1))
MODEL = demand.fit(WORLD, HIST)
CTX = evaluate.context(WORLD, MODEL)
D_SEARCH = demand.sample_days(MODEL, WORLD, C.SEARCH_DAYS, C.SEED + 11, CTX["mask"])
D_FINAL = demand.sample_days(MODEL, WORLD, C.FINAL_DAYS, C.SEED + 12, CTX["mask"])
REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
J = len(CTX["fixed"])


def score(args):
    sites, days = args
    e = evaluate.evaluate(CTX, list(sites), D_SEARCH if days == "search" else D_FINAL)
    return (float(e["total"]), bool(e["ok98"])) if e["feasible"] else (float("inf"), False)


def neighbours(s):
    out = [("swap", a, b, sorted([x for x in s if x != a] + [b])) for a in s for b in range(J) if b not in s]
    out += [("drop", a, None, sorted(x for x in s if x != a)) for a in s]
    out += [("add", None, b, sorted(s + [b])) for b in range(J) if b not in s]
    return [m for m in out if len(m[3]) * CTX["hi"] >= CTX["n"] and len(m[3]) * CTX["lo"] <= CTX["n"]]


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "recommended"
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    start = sorted(REG["networks"][name])
    path = Path(__file__).with_name(f"e_neighbourhood_{name}.jsonl")
    done = {tuple(json.loads(line)["sites"]) for line in path.read_text().splitlines()} if path.exists() else set()
    moves = [m for m in neighbours(start) if tuple(m[3]) not in done]
    print(f"{name}: k={len(start)}, {len(moves)} neighbours to score, {len(done)} already done", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex, path.open("a") as f:
        if not done:
            e0 = score((tuple(start), "search"))
            f.write(json.dumps(dict(move="start", out=None, inp=None, sites=start, E=e0[0], ok98=e0[1])) + "\n")
        for i, (m, v) in enumerate(zip(moves, ex.map(score, [(tuple(m[3]), "search") for m in moves], chunksize=1))):
            f.write(json.dumps(dict(move=m[0], out=m[1], inp=m[2], sites=m[3], E=v[0], ok98=v[1])) + "\n")
            f.flush()
            if i % 20 == 0:
                print(f"[{time.time() - t0:6.0f}s] {i + 1}/{len(moves)}", flush=True)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    base = next(r for r in rows if r["move"] == "start")["E"]
    ok = sorted((r for r in rows if r["move"] != "start" and r["ok98"]), key=lambda r: r["E"])
    print(f"start {base / 1e6:,.1f} M; best neighbours:")
    for r in ok[:8]:
        print(f"  {r['move']:4s} out {r['out']} in {r['inp']} k={len(r['sites'])}  {r['E'] / 1e6:,.1f} M  ({(r['E'] - base) / 1e6:+.1f})")
    close = [r for r in ok if r["E"] < base + 25e6]
    with ProcessPoolExecutor(workers) as ex:
        sc = list(ex.map(score, [(tuple(start), "final")] + [(tuple(r["sites"]), "final") for r in close], chunksize=1))
    start_final = sc[0][0]
    for r, v in zip(close, sc[1:]):
        r["E_final"] = v[0]
    out = dict(network=name, start_E_search=base, start_E_final=start_final, evaluated=len(rows) - 1,
               improving_search=[r for r in ok if r["E"] < base - 1e5], near=close)
    path.with_suffix(".json").write_text(json.dumps(out, indent=1))
    print(f"final-days start {start_final / 1e6:,.1f} M; within 25 M on search days: {len(close)}; improving on search days: {len(out['improving_search'])}")
    for r in close:
        print(f"  {r['move']:4s} out {r['out']} in {r['inp']}: search {r['E'] / 1e6:,.1f} final {r['E_final'] / 1e6:,.1f} ({(r['E_final'] - start_final) / 1e6:+.1f})")
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
