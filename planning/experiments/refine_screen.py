"""Would a G2 screen have found the refinement path? Rank every one-move neighbour of each round by G2: python refine_screen.py."""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, search  # noqa: E402
from dcn.world import make_world  # noqa: E402

R = json.loads((CODE / "results" / "full" / "registry.json").read_text())
world = make_world(C.FULL["fraction"], C.SEED)
ctx = evaluate.context(world, demand.fit(world, demand.make_history(world, np.random.default_rng(C.SEED + 1))))
ctx["tour_c"] = R["meta"]["tour_c"]
cache = {}
for line in (Path(__file__).parents[1] / "archive" / "local_search_check" / "local_search_cache.jsonl").read_text().splitlines():
    r = json.loads(line); cache[tuple(r["sites"])] = (r["E"], r["ok98"])


def g2(sites):
    lp = evaluate.assign_lp(ctx, np.array(sites))
    if lp is None:
        return float("inf")
    return search.g1(ctx, sites, np.searchsorted(np.array(sites), lp["site"]), clock=True)[0]


out = []
path = R["refinement"]["path"]
for rnd, p in enumerate(path):
    moves = search.one_move(ctx, p["sites"])
    G = np.array([g2(n) for _, n in moves])
    E = np.array([cache[tuple(n)][0] if cache[tuple(n)][1] else np.inf for _, n in moves])
    best = int(np.argmin(E)); rank_g2 = int((G < G[best]).sum()) + 1
    rho = float(np.corrcoef(np.argsort(np.argsort(G[np.isfinite(E)])), np.argsort(np.argsort(E[np.isfinite(E)])))[0, 1])
    top = {n: float(E[np.argsort(G)[:n]].min()) for n in (5, 10, 20, 40)}
    out.append(dict(round=rnd + 1, start=p["sites"], best_move=moves[best][0], best_E=float(E[best]), start_E=p["E"], g2_rank_of_best=rank_g2,
                    rank_corr=rho, best_E_in_g2_top=top))
    print(f"round {rnd + 1}: best move {moves[best][0]} ({E[best] / 1e6:,.1f} M, start {p['E'] / 1e6:,.1f}) ranks {rank_g2} of {len(moves)} by G2; "
          f"rank correlation {rho:.2f}; best E among G2 top 5/10/20/40: " + ", ".join(f"{v / 1e6:,.1f}" for v in top.values()), flush=True)
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1))
