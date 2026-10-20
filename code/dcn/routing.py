"""Lower level: one DC's day as a capacitated VRP with a hard noon deadline, Clarke-Wright savings plus 2-opt."""
from dataclasses import dataclass, replace

import numpy as np

from . import config as C
from . import distances


@dataclass
class Params:
    cap: float = C.CAP
    max_stops: int = C.MAX_STOPS
    max_km: float = C.MAX_KM
    stop_h: float = C.STOP_H
    speed: float = C.SPEED
    depart: float = C.DEPART
    deadline: float = C.DEADLINE
    shift_end: float = C.SHIFT_END
    break_h: float = C.BREAK_H


def dist_matrix(dc_lat, dc_lon, lat, lon, mountain):
    # Road km from coordinates alone (live demo), index 0 = DC, 1..n = stores; calibrated model
    la, lo = np.r_[dc_lat, lat], np.r_[dc_lon, lon]
    mt = np.r_[False, mountain]
    return distances.model_km(la[:, None], lo[:, None], la[None, :], lo[None, :], mt[:, None] | mt[None, :])


def territory_matrix(ctx, j, idx):
    # Road km for site j and planning stores idx: cached DC and nearest-store legs, model for the rest
    return distances.territory(ctx["dsite"][idx, j], ctx["full"][idx], ctx["lat"][idx], ctx["lon"][idx], ctx["mountain"][idx])


def walk(seq, D, p):
    # Drive 0 -> seq -> 0; return km, arrival times, return time
    t, km, prev, arr = p.depart, 0.0, 0, []
    for i in seq:
        leg = D[prev, i]
        km += leg
        t += leg / p.speed
        arr.append(t)
        t += p.stop_h
        prev = i
    back = D[prev, 0]
    return km + back, arr, t + back / p.speed


def ok_time(seq, D, p):
    km, arr, ret = walk(seq, D, p)
    return km <= p.max_km and arr[-1] <= p.deadline and ret + p.break_h <= p.shift_end


def _pairs(D, n, k_nn=40):
    # Savings for all pairs on small territories, k nearest neighbours on large ones
    d0 = D[0, 1:]
    if n <= 400:
        i, j = np.triu_indices(n, 1)
    else:
        nn = np.argpartition(D[1:, 1:], k_nn, axis=1)[:, : k_nn + 1]
        i = np.repeat(np.arange(n), nn.shape[1])
        j = nn.ravel()
        keep = i != j
        i, j = np.minimum(i, j)[keep], np.maximum(i, j)[keep]
        ij = np.unique(np.stack([i, j], 1), axis=0)
        i, j = ij[:, 0], ij[:, 1]
    s = d0[i] + d0[j] - D[i + 1, j + 1]
    order = np.lexsort((j, i, -s))
    return i[order] + 1, j[order] + 1, s[order]


def two_opt(seq, D, p):
    # Reverse P[i..j] when the two swapped edges shorten the route and it stays feasible
    P = [0] + list(seq) + [0]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(P) - 2):
            for j in range(i + 1, len(P) - 1):
                delta = D[P[i - 1], P[j]] + D[P[i], P[j + 1]] - D[P[i - 1], P[i]] - D[P[j], P[j + 1]]
                if delta < -1e-9:
                    cand = P[:i] + P[i:j + 1][::-1] + P[j + 1:]
                    if ok_time(cand[1:-1], D, p):
                        P, improved = cand, True
    return P[1:-1]


def solve(D, q, p=None, improve=True):
    """Route one DC's stores for one day; returns routes and day totals."""
    p = p or Params()
    n = len(q)
    routes = {k: [k] for k in range(1, n + 1)}
    of = list(range(n + 1))
    load = {k: float(q[k - 1]) for k in range(1, n + 1)}
    for i, j, s in zip(*_pairs(D, n)):
        if s <= 0:
            break
        ri, rj = of[i], of[j]
        if ri == rj:
            continue
        A, B = routes[ri], routes[rj]
        if (A[0] != i and A[-1] != i) or (B[0] != j and B[-1] != j):
            continue
        if load[ri] + load[rj] > p.cap or len(A) + len(B) > p.max_stops:
            continue
        cand = (A if A[-1] == i else A[::-1]) + (B if B[0] == j else B[::-1])
        if not ok_time(cand, D, p):
            cand = cand[::-1]
            if not ok_time(cand, D, p):
                continue
        routes[ri] = cand
        load[ri] += load.pop(rj)
        del routes[rj]
        for v in cand:
            of[v] = ri
    out = []
    for k, seq in routes.items():
        if improve and len(seq) >= 4:
            seq = two_opt(seq, D, p)
        km, arr, ret = walk(seq, D, p)
        out.append(dict(seq=[v - 1 for v in seq], km=km, load=load[k], arr=arr, ret=ret, binding=_binding(seq, load[k], km, arr, ret, p)))
    out.sort(key=lambda r: r["arr"][0])
    arr_all = np.concatenate([r["arr"] for r in out]) if out else np.zeros(0)
    return dict(
        routes=out, vehicles=len(out), km=float(sum(r["km"] for r in out)),
        on_time=int((arr_all <= p.deadline + 1e-9).sum()), late=int((arr_all > p.deadline + 1e-9).sum()),
        failed=int((arr_all > C.FAIL_AT).sum()), deliveries=int(len(arr_all)),
    )


def solve_waves(D, q, p, docks, waves=C.WAVES):
    """Departure waves: at most `docks` vehicles load per hour; the least-slack routes take the earliest wave,
    the remaining stores are re-routed from the next wave; the last wave takes all that is left."""
    left = np.arange(1, len(q) + 1)
    routes, over = [], 0
    for w, t in enumerate(waves):
        sub = np.r_[0, left]
        pw = replace(p, depart=t, shift_end=p.shift_end + t - p.depart)
        r = solve(D[np.ix_(sub, sub)], q[left - 1], pw)
        rs = sorted(r["routes"], key=lambda x: x["arr"][-1] - pw.deadline, reverse=True)
        keep = rs if w == len(waves) - 1 else rs[:docks]
        over = max(len(keep) - docks, 0)
        done = []
        for rr in keep:
            rr["seq"] = (left[rr["seq"]] - 1).tolist()
            rr["depart"] = t
            done += rr["seq"]
        routes += keep
        left = np.setdiff1d(left, np.array(done, int) + 1)
        if not len(left):
            break
    arr_all = np.concatenate([r["arr"] for r in routes]) if routes else np.zeros(0)
    return dict(
        routes=routes, vehicles=len(routes), km=float(sum(r["km"] for r in routes)), dock_over=over,
        on_time=int((arr_all <= p.deadline + 1e-9).sum()), late=int((arr_all > p.deadline + 1e-9).sum()),
        failed=int((arr_all > C.FAIL_AT).sum()), deliveries=int(len(arr_all)),
    )


def _binding(seq, load, km, arr, ret, p):
    # Tightest of the five limits, in units of "room for one more store"
    if km > p.max_km or arr[-1] > p.deadline or ret + p.break_h > p.shift_end or len(seq) > p.max_stops:
        return "violates limit"
    room = dict(load=(p.cap - load) / 2.2, stops=p.max_stops - len(seq), km=(p.max_km - km) / 15,
                clock=(p.deadline - arr[-1]) / (p.stop_h + 0.25), shift=(p.shift_end - p.break_h - ret) / (p.stop_h + 0.25))
    k = min(room, key=room.get)
    return k if room[k] < 1 else "geometry"
