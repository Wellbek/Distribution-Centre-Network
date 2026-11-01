"""Could the refinement run with far fewer full evaluations? Rank by G2 of each accepted move among its round's one-move neighbours: python checks/refinement_screen.py.

Each accepted move is the best of all its round's neighbours under E, so a refinement that fully evaluates only the top-m neighbours by G2
takes the same path whenever every accepted move ranks within m, and stops where the full one stops.
About 20 minutes on one core (one assignment LP per neighbour); writes results/checks/refinement_screen.json, quoted in problem-definition.md Section 5.
"""
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from dcn import config as C  # noqa: E402
from dcn import demand, evaluate, search  # noqa: E402
from dcn.world import make_world  # noqa: E402


def g2(ctx, sites):
    # G2 exactly as the pool computes it: the assignment LP's territories, then the clock-aware route approximation
    lp = evaluate.assign_lp(ctx, np.array(sites))
    if lp is None:
        return float("inf")
    return search.g1(ctx, sites, np.searchsorted(np.array(sites), lp["site"]), clock=True)[0]


def main():
    R = json.loads((CODE / "results" / "full" / "registry.json").read_text())
    world = make_world(C.FULL["fraction"], C.SEED)
    model = demand.fit(world, demand.make_history(world, np.random.default_rng(C.SEED + 1)))
    ctx = evaluate.context(world, model)
    d_search = demand.sample_days(model, world, C.SEARCH_DAYS, C.SEED + 11, ctx["mask"])
    ctx["tour_c"] = search.fit_tour(ctx, evaluate.evaluate(ctx, ctx["current"], d_search, assign=ctx["hist_assign"]))
    path, rounds = R["refinement"]["path"], []
    for cur, nxt in zip(path[:-1], path[1:]):
        moves = search.one_move(ctx, cur["sites"])
        g = np.array([g2(ctx, n) for _, n in moves])
        i = next(i for i, (_, n) in enumerate(moves) if n == nxt["sites"])
        rounds.append(dict(move=nxt["move"], neighbours=len(moves), g2_rank=int((g < g[i]).sum()) + 1))
        print(f"{nxt['move']}: G2 rank {rounds[-1]['g2_rank']} of {len(moves)}", flush=True)
    m = max(r["g2_rank"] for r in rounds)
    out = dict(rounds=rounds, worst_rank=m, screened_evaluations_top40=40 * len(path), full_evaluations=R["refinement"]["evaluations"])
    (CODE / "results" / "checks" / "refinement_screen.json").write_text(json.dumps(out, indent=1))
    print(f"every accepted move within the G2 top {m}; a top-40 screen needs {out['screened_evaluations_top40']} full evaluations against {out['full_evaluations']}")


if __name__ == "__main__":
    main()
