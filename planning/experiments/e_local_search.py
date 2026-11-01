"""Best-improvement local search on E to a one-move local optimum, from run 7's recommended network: python e_local_search.py [workers].

Each round scores the full one-move neighbourhood (swap with every closed site, drop, add, within 500-1,400 stores per DC) on the 7 search days and takes the best move if it saves more than 1 M; the last round certifies the local optimum.
Every evaluation is appended to e_local_search.jsonl (resumable); the path is re-scored on the 28 final days at the end.
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from e_neighbourhood_check import REG, neighbours, score

PATH = Path(__file__).with_name("e_local_search.jsonl")


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seen = {}
    if PATH.exists():
        for line in PATH.read_text().splitlines():
            r = json.loads(line)
            seen[tuple(r["sites"])] = (r["E"], r["ok98"])
    cur = tuple(sorted(REG["networks"]["recommended"]))
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex, PATH.open("a") as f:
        def run(nets):
            todo = [s for s in dict.fromkeys(nets) if s not in seen]
            for s, v in zip(todo, ex.map(score, [(s, "search") for s in todo], chunksize=1)):
                seen[s] = v
                f.write(json.dumps(dict(sites=list(s), E=v[0], ok98=v[1])) + "\n")
                f.flush()
        run([cur])
        path = [dict(sites=list(cur), E=seen[cur][0], move="start")]
        while True:
            moves = neighbours(list(cur))
            print(f"[{time.time() - t0:6.0f}s] round {len(path)}: {len(moves)} neighbours of {cur} ({seen[cur][0] / 1e6:,.1f} M)", flush=True)
            run([tuple(m[3]) for m in moves])
            ok = [m for m in moves if seen[tuple(m[3])][1]]
            best = min(ok, key=lambda m: seen[tuple(m[3])][0])
            if seen[tuple(best[3])][0] >= seen[cur][0] - 1e6:
                print(f"local optimum: best neighbour {seen[tuple(best[3])][0] / 1e6:,.1f} M", flush=True)
                break
            cur = tuple(best[3])
            path.append(dict(sites=list(cur), E=seen[cur][0], move=f"{best[0]} out {best[1]} in {best[2]}"))
            print(f"  move {path[-1]['move']}: {seen[cur][0] / 1e6:,.1f} M", flush=True)
        fin = list(ex.map(score, [(tuple(p["sites"]), "final") for p in path], chunksize=1))
    for p, v in zip(path, fin):
        p["E_final"] = v[0]
        print(f"{p['move']:22s} search {p['E'] / 1e6:,.1f}  final {v[0] / 1e6:,.1f}", flush=True)
    Path(__file__).with_suffix(".json").write_text(json.dumps(dict(path=path, evaluated=len(seen)), indent=1))
    print(f"done in {time.time() - t0:.0f}s, {len(seen)} evaluations")


if __name__ == "__main__":
    main()
