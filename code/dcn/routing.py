"""Lower level: one DC's day as a capacitated VRP with a hard noon deadline; routes built step by step, then segments reversed (Lecture 0)."""
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
    relay_km: float = C.RELAY_KM
    relay_shift_end: float = C.RELAY_SHIFT_END
    relay: bool = True                     # False: the brief's limits strictly, far stores become stock-outs


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
        leg = D[prev][i]
        km += leg
        t += leg / p.speed
        arr.append(t)
        t += p.stop_h
        prev = i
    back = D[prev][0]
    return km + back, arr, t + back / p.speed


def ok_time(seq, D, p):
    # walk() without the arrival list; arrivals and km only grow along a route, so it may stop at the first breach
    t, km, prev = p.depart, 0.0, 0
    for i in seq:
        leg = D[prev][i]
        km += leg
        t += leg / p.speed
        if t > p.deadline or km > p.max_km:
            return False
        t += p.stop_h
        prev = i
    back = D[prev][0]
    return km + back <= p.max_km and t + back / p.speed + p.break_h <= p.shift_end


def reverse_segments(seq, D, p):
    # Improvement: reverse P[i..j] when the two swapped edges shorten the route and it stays feasible
    P = [0] + list(seq) + [0]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(P) - 2):
            for j in range(i + 1, len(P) - 1):
                delta = D[P[i - 1]][P[j]] + D[P[i]][P[j + 1]] - D[P[i - 1]][P[i]] - D[P[j]][P[j + 1]]
                if delta < -1e-9:
                    cand = P[:i] + P[i:j + 1][::-1] + P[j + 1:]
                    if ok_time(cand[1:-1], D, p):
                        P, improved = cand, True
    return P[1:-1]


def solve(D, q, p=None, improve=True):
    """Route one DC's stores for one day; stores no one-driver route can reach go on two-driver relay routes."""
    p = p or Params()
    routes = _construct(D, q, p, improve)
    bad = [r for r in routes if r["binding"] == "violates limit"]
    missed = 0
    if bad and not p.relay:
        missed = sum(len(r["seq"]) for r in bad)
        routes = [r for r in routes if r["binding"] != "violates limit"]
    elif bad:
        # Relay pass: the far stores share routes with a second driver (longer km and shift, same noon deadline)
        far = np.array(sorted(v for r in bad for v in r["seq"]))
        sub = np.r_[0, far + 1]
        pr = replace(p, max_km=p.relay_km, shift_end=p.relay_shift_end)
        relay = _construct(D[np.ix_(sub, sub)], q[far], pr, improve)
        for r in relay:
            r["seq"] = far[r["seq"]].tolist()
            r["binding"] = "relay" if r["binding"] != "violates limit" else "violates limit"
        routes = [r for r in routes if r["binding"] != "violates limit"] + relay
        routes.sort(key=lambda r: r["arr"][0])
    arr_all = np.concatenate([r["arr"] for r in routes]) if routes else np.zeros(0)
    return dict(
        routes=routes, vehicles=len(routes), km=float(sum(r["km"] for r in routes)),
        on_time=int((arr_all <= p.deadline + 1e-9).sum()), late=int((arr_all > p.deadline + 1e-9).sum()),
        failed=int((arr_all > C.FAIL_AT).sum()), deliveries=int(len(arr_all)), missed=missed,
    )


def _construct(D, q, p, improve, k_nn=30):
    """Step by step with infeasible stores masked: open a route at the unrouted store farthest from the DC, then insert the
    store whose cheapest feasible insertion saves the most km against its own trip (2 d0 - detour), until none fits."""
    n = len(q)
    D = np.asarray(D)
    d0 = D[0]
    nn = np.argsort(D[1:, 1:], axis=1, kind="stable")[:, : k_nn + 1] + 1
    left = np.ones(n + 1, bool)
    left[0] = False
    order = sorted(range(1, n + 1), key=lambda i: (-d0[i], i))
    eps, oi, routes = 1e-9, 0, []
    while left.any():
        while not left[order[oi]]:
            oi += 1
        r = [order[oi]]
        left[r[0]] = False
        load = float(q[r[0] - 1])
        near = np.zeros(n + 1, bool)
        near[nn[r[0] - 1]] = True
        while ok_time(r, D, p) and len(r) < p.max_stops:
            C = np.flatnonzero(near & left)
            C = C[load + q[C - 1] <= p.cap + eps]
            if not len(C):
                break
            # Position k lies between P[k] and N[k]; arrivals only grow along a route, so one slack per route decides the later stops
            km, arr, ret = walk(r, D, p)
            P, N = np.r_[0, r], np.r_[r, 0]
            dep = np.r_[p.depart, np.array(arr) + p.stop_h]
            DP = D[np.ix_(P, C)]
            detour = DP + D[np.ix_(C, N)].T - D[P, N][:, None]
            push = detour / p.speed + p.stop_h
            ok = (dep[:, None] + DP / p.speed <= p.deadline + eps) & (km + detour <= p.max_km + eps)
            ok[:-1] &= arr[-1] + push[:-1] <= p.deadline + eps
            ok &= ret + push + p.break_h <= p.shift_end + eps
            dm = np.where(ok, detour, np.inf)
            kb = dm.argmin(0)
            db = dm[kb, np.arange(len(C))]
            score = np.where(np.isfinite(db), 2 * d0[C] - db, -np.inf)
            placed = False
            while np.isfinite(score.max()):
                b = int(score.argmax())
                c, k = int(C[b]), int(kb[b])
                s = r[:k] + [c] + r[k:]
                if ok_time(s, D, p):
                    r, placed = s, True
                    load += float(q[c - 1])
                    left[c] = False
                    near[nn[c - 1]] = True
                    break
                score[b] = -np.inf
            if not placed:
                break
        routes.append(r)
    # Small territories read a list copy of D in the improvement (same floats, faster lookups)
    if n <= 400:
        D = D.tolist()
    out = []
    for seq in routes:
        if improve and len(seq) >= 4:
            seq = reverse_segments(seq, D, p)
        km, arr, ret = walk(seq, D, p)
        load = float(sum(q[v - 1] for v in seq))
        out.append(dict(seq=[v - 1 for v in seq], km=km, load=load, arr=arr, ret=ret, binding=_binding(seq, load, km, arr, ret, p)))
    out.sort(key=lambda r: r["arr"][0])
    return out


def solve_waves(D, q, p, docks, waves=C.WAVES):
    """Departure waves: at most `docks` vehicles load per hour; the least-slack routes take the earliest wave,
    the remaining stores are re-routed from the next wave; the last wave takes all that is left."""
    left = np.arange(1, len(q) + 1)
    routes, over = [], 0
    for w, t in enumerate(waves):
        sub = np.r_[0, left]
        pw = replace(p, depart=t, shift_end=p.shift_end + t - p.depart, relay_shift_end=p.relay_shift_end + t - p.depart)
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
