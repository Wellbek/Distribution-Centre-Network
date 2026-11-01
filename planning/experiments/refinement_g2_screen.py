"""Could the refinement run on G2-screened neighbours? Rank of each accepted move among its round's 560 neighbours by G2: python refinement_g2_screen.py."""
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
model = demand.fit(world, demand.make_history(world, np.random.default_rng(C.SEED + 1)))
ctx = evaluate.context(world, model)
d_search = demand.sample_days(model, world, C.SEARCH_DAYS, C.SEED + 11, ctx["mask"])
ctx["tour_c"] = search.fit_tour(ctx, evaluate.evaluate(ctx, ctx["current"], d_search, assign=ctx["hist_assign"]))
cache = {tuple(json.loads(l)["sites"]): json.loads(l) for l in (Path(__file__).parents[1] / "archive" / "local_search_check" / "local_search_cache.jsonl").read_text().splitlines()}
path = R["refinement"]["path"]
out = []
for r, (cur, nxt) in enumerate(zip(path[:-1], path[1:]), 1):
    moves = search.one_move(ctx, cur["sites"])
    g = np.array([search.g1(ctx, n, clock=True)[0] for _, n in moves])
    e = np.array([cache[tuple(n)]["E"] if tuple(n) in cache else np.inf for _, n in moves])
    i = next(i for i, (_, n) in enumerate(moves) if n == nxt["sites"])
    rank_g = int((g < g[i]).sum()) + 1
    improving = [int((g < g[j]).sum()) + 1 for j in np.flatnonzero(e < cur["E"] - 1e6)]
    out.append(dict(round=r, move=nxt["move"], g2_rank=rank_g, improving_g2_ranks=sorted(improving)))
    print(f"round {r}: {nxt['move']}: G2 rank {rank_g} of {len(moves)}; improving neighbours' G2 ranks {sorted(improving)}", flush=True)
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1))
