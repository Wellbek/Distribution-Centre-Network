"""Best-improvement local search on E itself (swap, add, drop sites) from the pool's best candidates, to test whether the pool hides a better network: python spark_e_local_search.py."""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
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
REG = json.loads((CODE / "results" / "full" / "registry.json").read_text())
J = len(CTX["fixed"])
NEAR = np.argsort(geo.haversine(CTX["site_lat"][:, None], CTX["site_lon"][:, None], CTX["site_lat"][None], CTX["site_lon"][None]), 1)[:, 1:13]


def e_search(sites):
    e = evaluate.evaluate(CTX, sorted(sites), D_SEARCH)
    return float(e["total"]) if e["feasible"] and e["ok98"] else float("inf")


def neighbours(s):
    # Swap each open site for one of its 12 nearest closed sites; drop any site; add any closed site
    s = list(s)
    out = []
    for i, a in enumerate(s):
        out += [("swap", a, int(b), sorted(s[:i] + [int(b)] + s[i + 1:])) for b in NEAR[a] if b not in s]
        out.append(("drop", a, None, sorted(s[:i] + s[i + 1:])))
    out += [("add", None, b, sorted(s + [b])) for b in range(J) if b not in s]
    return [m for m in out if len(m[3]) * CTX["hi"] >= CTX["n"] and len(m[3]) * CTX["lo"] <= CTX["n"]]


def main():
    t0 = time.time()
    pool = REG["pool"]
    starts = {}
    for k in (9, 10, 11, 12):
        ok = [p for p in pool if p["k"] == k and p["ok98"]]
        starts[k] = min(ok, key=lambda p: p["E"])["sites"]
    log, seen = [], {}
    with ProcessPoolExecutor(min(os.cpu_count() or 1, 16)) as ex:
        for k, s in starts.items():
            cur = sorted(s)
            val = seen.setdefault(tuple(cur), e_search(cur))
            print(f"[{time.time() - t0:6.0f}s] start k={k}: E {val / 1e6:,.0f} M", flush=True)
            for step in range(6):
                moves = [m for m in neighbours(cur) if tuple(m[3]) not in seen]
                vals = list(ex.map(e_search, [m[3] for m in moves]))
                for m, v in zip(moves, vals):
                    seen[tuple(m[3])] = v
                    log.append(dict(start_k=k, step=step, move=m[0], out=m[1], inp=m[2], sites=m[3], E=v))
                best = min(range(len(moves)), key=lambda i: vals[i]) if moves else None
                if best is None or vals[best] >= val - 1e6:
                    break
                cur, val = moves[best][3], vals[best]
                print(f"[{time.time() - t0:6.0f}s]   step {step}: {moves[best][0]} -> k={len(cur)}, E {val / 1e6:,.0f} M ({len(moves)} neighbours)", flush=True)
            starts[k] = dict(sites=cur, E_search=val)
    # Re-score each local optimum and today's network on the 28 final days, same rules as the pipeline
    today = evaluate.evaluate(CTX, CTX["current"], D_FINAL, assign=CTX["hist_assign"])["total"]
    for k, r in starts.items():
        r["E_final"] = float(evaluate.evaluate(CTX, r["sites"], D_FINAL)["total"])
        print(f"local optimum from k={k}: k={len(r['sites'])} {r['sites']}  search {r['E_search'] / 1e6:,.0f} M  final {r['E_final'] / 1e6:,.0f} M  "
              f"saving vs today {(today - r['E_final']) / 1e6:,.0f} M", flush=True)
    out = dict(today_final=float(today), results=starts, evaluations=len(seen), log=log)
    Path(__file__).with_name("spark_e_local_search.json").write_text(json.dumps(out, indent=1))
    print(f"{len(seen)} E evaluations, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
