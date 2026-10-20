"""Whole pipeline for one run profile: world, demand model, baseline, pool, budgeted search, checks, registry."""
import csv
import platform
import sys
import gzip
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import scipy

from . import config as C
from . import demand, distances, evaluate, routing, search
from .world import HIST_DAYS, TYPES, make_world

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _boot(eb, er, seed, n=1000, fixed_fleet=False):
    """Bootstrap the paired monthly saving: resample days within calendar strata and re-size both fleets."""
    rng = np.random.default_rng(seed)
    w = np.array(eb["w"]); groups = {}
    for i, x in enumerate(w):
        groups.setdefault(round(x, 6), []).append(i)
    out = []
    for _ in range(n):
        idx = np.concatenate([rng.choice(g, size=len(g)) for g in groups.values()])
        tot = []
        for e in (eb, er):
            V = np.array(e["V"])[:, idx]
            own = np.array(e["owned_by_dc"]) if fixed_fleet else None
            parts, _, _ = evaluate.monthly(V, np.array(e["fuel_d"])[idx], np.array(e["pen_d"])[idx], np.array(e["over_d"])[idx], w[idx], e["fixed"], own)
            tot.append(parts["total"])
        out.append(tot[0] - tot[1])
    return [float(np.percentile(out, 5)), float(np.percentile(out, 95))]


def _spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def _summary(e):
    keys = ["k", "open", "total", "fixed", "fleet", "fuel", "spot", "penalty", "relay", "owned", "loads", "census",
            "over_limit_day", "vehicles_day", "dock_over_day", "km_day", "service_min", "ok98", "lp_frac", "price_hi", "price_lo"]
    out = {k: e[k] for k in keys if k in e}
    out["service_mean"] = float(np.average(e["service"], weights=e["w"]))
    return out


def write_tables(world, model, hist, out):
    # Input tables of brief §2.5
    st, sites = world["stores"], world["sites"]
    out.mkdir(parents=True, exist_ok=True)
    start = demand.HIST_START
    with open(out / "stores.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["store_id", "region", "lat", "lon", "store_type", "opened_on", "closed_on", "current_dc_id"])
        for i in range(len(st["id"])):
            op = (start + demand.timedelta(int(st["opened"][i]))).isoformat() if st["opened"][i] >= 0 else ""
            cl = (start + demand.timedelta(int(st["closed"][i]))).isoformat() if st["closed"][i] < HIST_DAYS else ""
            w.writerow([st["id"][i], f"{st['province'][i]}, {st['district'][i]}", round(st["lat"][i], 5), round(st["lon"][i], 5), TYPES[st["type"][i]], op, cl, world["dcs"][st["current_dc"][i]]["id"]])
    with open(out / "dcs.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["dc_id", "lat", "lon", "lease_expires_on", "monthly_fixed_cost", "max_stores", "min_stores"])
        for d in world["dcs"]:
            w.writerow([d["id"], d["lat"], d["lon"], d["lease_expires_on"], d["monthly_fixed_cost"], d["max_stores"], d["min_stores"]])
    with open(out / "candidate_sites.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["site_id", "lat", "lon", "monthly_fixed_cost", "max_stores"])
        for s in sites:
            w.writerow([s["id"], s["lat"], s["lon"], s["monthly_fixed_cost"], s["max_stores"]])
    with open(out / "cost_parameters.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["parameter", "value", "unit"])
        for row in [("fuel per km", C.FUEL_KM, "KRW/km"), ("vehicle monthly cost", C.VEHICLE_MONTH, "KRW/month"),
                    ("spot-truck daily rate", C.SPOT_DAY, "KRW/day"), ("late-delivery penalty", C.LATE_PEN, "KRW"),
                    ("stock-out penalty", C.STOCKOUT_PEN, "KRW"), ("vehicle capacity", C.CAP, "roll cages")]:
            w.writerow(row)
    with gzip.open(out / "demand_history.csv.gz", "wt", newline="") as f:
        w = csv.writer(f); w.writerow(["store_id", "date", "cages_ordered"])
        y = hist["y"]
        for i in range(y.shape[0]):
            for t in np.flatnonzero(y[i] >= 0):
                w.writerow([st["id"][i], hist["cal"]["date"][t], int(y[i, t])])


def _hhmm(h):
    m = int(round(h * 60))
    return f"{m // 60:02d}:{m % 60:02d}"


def write_outcomes(world, hist, out):
    """Outcome tables of brief §2.5: the lower level run on the current network over the 365 history days."""
    st, sites = world["stores"], world["sites"]
    cur = [i for i, s in enumerate(sites) if s["current"]]
    slat = np.array([s["lat"] for s in sites]); slon = np.array([s["lon"] for s in sites])
    dsite = distances.site_km(st["full"], st["lat"], st["lon"], st["mountain"], slat, slon)
    y, dates = hist["y"], hist["cal"]["date"]
    p = routing.Params()
    jobs, terr = [], []
    for c, j in enumerate(cur):
        idx = np.flatnonzero(st["current_dc"] == c)
        days = []
        for t in range(len(dates)):
            sel = np.flatnonzero(y[idx, t] >= 0)
            days.append((sel, y[idx[sel], t].astype(float)))
        jobs.append(((dsite[idx, j], st["full"][idx], st["lat"][idx], st["lon"][idx], st["mountain"][idx]), days, p, None))
        terr.append(idx)
    res = evaluate.territories(jobs)
    V = np.array([[r["vehicles"] for r in rs] for rs in res])
    owned = np.ceil(np.quantile(V, C.FLEET_Q, axis=1, method="inverted_cdf")).astype(int)
    on = tot = 0
    with gzip.open(out / "deliveries.csv.gz", "wt", newline="") as fd, gzip.open(out / "vehicle_days.csv.gz", "wt", newline="") as fv, \
            open(out / "spot_hires.csv", "w", newline="") as fs:
        wd, wv, ws = csv.writer(fd), csv.writer(fv), csv.writer(fs)
        wd.writerow(["store_id", "date", "cages_delivered", "delivered_at", "vehicle_id"])
        wv.writerow(["vehicle_id", "dc_id", "date", "km_driven", "stops", "departed_at", "returned_at"])
        ws.writerow(["dc_id", "date", "trucks_hired", "cost"])
        for t, date in enumerate(dates):
            for c, j in enumerate(cur):
                dc, idx = world["dcs"][c]["id"], terr[c]
                sel, q = jobs[c][1][t]
                for n, rr in enumerate(res[c][t]["routes"]):
                    vid = f"{dc}-V{n + 1:03d}" if n < owned[c] else f"{dc}-S{n + 1 - owned[c]:02d}"
                    for s, a in zip(rr["seq"], rr["arr"]):
                        wd.writerow([st["id"][idx[sel[s]]], date, int(q[s]), _hhmm(a), vid])
                    wv.writerow([vid, dc, date, round(rr["km"], 1), len(rr["seq"]), _hhmm(p.depart), _hhmm(rr["ret"])])
                    ok = rr["binding"] != "violates limit"
                    on += ok * int((np.array(rr["arr"]) <= p.deadline + 1e-9).sum()); tot += len(rr["seq"])
                hired = max(int(V[c, t]) - int(owned[c]), 0)
                ws.writerow([dc, date, hired, int(hired * C.SPOT_DAY)])
    km = np.array([[r["km"] for r in rs] for rs in res])
    spot = C.SPOT_DAY * np.maximum(V - owned[:, None], 0).sum(0)
    return dict(days=len(dates), service=on / max(tot, 1), vehicles_day=float(V.sum(0).mean()), km_day=float(km.sum(0).mean()),
                owned=int(owned.sum()), spot_month=float(C.DAYS_MONTH * spot.mean()), deliveries=int(tot))


def run(profile):
    with evaluate.workers():
        return _run(profile)


def _run(profile):
    t0 = time.time()
    seed = C.SEED
    clock = lambda msg: print(f"[{time.time() - t0:6.1f}s] {msg}", flush=True)
    world = make_world(profile["fraction"], seed)
    hist = demand.make_history(world, np.random.default_rng(seed + 1))
    model = demand.fit(world, hist)
    ctx = evaluate.context(world, model)
    m = ctx["mask"]
    clock(f"world: {ctx['n']} planning stores, {len(world['sites'])} sites; prior strength {np.round(model['b0_type'], 2)}, kappa {model['kappa']:.1f}")
    write_tables(world, model, hist, RESULTS / profile["name"] / "tables")
    hist_ops = write_outcomes(world, hist, RESULTS / profile["name"] / "tables")
    clock(f"outcome tables: {hist_ops['days']} history days, service {hist_ops['service']:.4f}, {hist_ops['vehicles_day']:.0f} vehicles/day")

    d_search = demand.sample_days(model, world, C.SEARCH_DAYS, seed + 11, m)
    d_final = demand.sample_days(model, world, C.FINAL_DAYS, seed + 12, m)
    d_held = demand.sample_days(model, world, C.HELDOUT_DAYS, seed + 13, m, exclude=[d["date"] for d in d_final])
    d_avg = demand.average_day(model, world, m)
    d_peak = demand.peak_day(model, world, m, seed + 14)

    kmin = int(np.ceil(ctx["n"] / ctx["hi"])); kmax = min(int(ctx["n"] // ctx["lo"]), 20)
    ks = list(range(kmin, kmax + 1))
    pool = search.build_pool(ctx, ks, profile["pool_per_k"], seed)
    clock(f"pool: {len(pool)} candidates for k = {kmin}..{kmax}")

    cache = {}

    def ev(p):
        key = tuple(p["sites"])
        if key not in cache:
            cache[key] = evaluate.evaluate(ctx, p["sites"], d_search)
        return cache[key]

    base = evaluate.evaluate(ctx, ctx["current"], d_search, assign=ctx["hist_assign"])
    clock(f"baseline E = {base['total'] / 1e6:,.1f} M KRW/month, {base['over_limit_day']:.1f} over-limit routes/day")
    log_bo = search.run_search(pool, ev, C.BUDGET, "ei", seed)
    clock(f"reported search done, best E = {min(r['E'] for r in log_bo) / 1e6:,.1f} M")
    log_rand = search.run_search(pool, ev, C.BUDGET, "random", seed + 5)

    # Validation only, after the reported search: every pool candidate once, then the exact random-selection band
    for p in pool:
        ev(p)
    clock("whole pool evaluated (validation)")
    E_pool = np.array([cache[tuple(p["sites"])]["total"] for p in pool])
    seeds_idx = [r["cand"] for r in log_bo if r["rule"] == "G1 seed"]
    rest = np.array([i for i in range(len(pool)) if i not in seeds_idx])
    rng = np.random.default_rng(seed + 99)
    curves = []
    for _ in range(2000):
        order = np.r_[seeds_idx, rng.permutation(rest)][: C.BUDGET]
        curves.append(np.minimum.accumulate(E_pool[order]))
    curves = np.array(curves)
    band = dict(p10=np.percentile(curves, 10, 0).tolist(), p50=np.percentile(curves, 50, 0).tolist(), p90=np.percentile(curves, 90, 0).tolist())
    pool_best = float(min(E_pool[i] for i in range(len(pool)) if cache[tuple(pool[i]["sites"])]["ok98"]))

    # Recommendation: top 5 of the reported search (service >= 98%), re-scored on the 28 final days
    ranked = []
    for r in sorted(log_bo, key=lambda r: r["E"]):
        if r["ok98"] and r["cand"] not in ranked:
            ranked.append(r["cand"])
    top = ranked[:5]
    top_final = {i: evaluate.evaluate(ctx, pool[i]["sites"], d_final) for i in top}
    best_i = min(top, key=lambda i: top_final[i]["total"])
    rec = pool[best_i]["sites"]
    clock(f"top 5 re-scored on {C.FINAL_DAYS} days; recommended k = {len(rec)}")

    def best_k(k):
        cands = [i for i, p in enumerate(pool) if p["k"] == k and cache[tuple(p["sites"])]["ok98"]] or [i for i, p in enumerate(pool) if p["k"] == k]
        return min(cands, key=lambda i: E_pool[i]) if cands else None

    proxy_i = int(np.argmin([p["G1"] for p in pool]))
    k8 = best_k(8) if 8 in ks else best_k(kmin)
    b12 = best_k(12)
    finals = {
        "baseline": evaluate.evaluate(ctx, ctx["current"], d_final, assign=ctx["hist_assign"], keep_stores=True),
        "reassigned12": evaluate.evaluate(ctx, list(ctx["current"]), d_final),
        "best12": evaluate.evaluate(ctx, pool[b12]["sites"], d_final) if b12 is not None else None,
        "recommended": evaluate.evaluate(ctx, rec, d_final, keep_stores=True),
        "proxy_only": evaluate.evaluate(ctx, pool[proxy_i]["sites"], d_final),
        "best_k8": evaluate.evaluate(ctx, pool[k8]["sites"], d_final),
    }
    finals = {k: v for k, v in finals.items() if v is not None}
    fb, fr = finals["baseline"], finals["recommended"]
    held_b = evaluate.evaluate(ctx, ctx["current"], d_held, assign=ctx["hist_assign"], owned=np.array(fb["owned_by_dc"]))
    held_r = evaluate.evaluate(ctx, rec, d_held, owned=np.array(fr["owned_by_dc"]))
    clock("final and held-out comparisons done")

    # Relay reversal: the far-store charge at 0, one driver-day and the spot rate
    def relay_total(e, r):
        return e["total"] - e["relay"] + C.DAYS_MONTH * r * e["over_limit_day"]
    reversal = [dict(relay=r, baseline=relay_total(fb, r), recommended=relay_total(fr, r),
                     k_star=pool[int(np.argmin([relay_total(cache[tuple(p["sites"])], r) if cache[tuple(p["sites"])]["ok98"] else np.inf for p in pool]))]["k"])
                for r in C.RELAY_SWEEP]

    sweep = [dict(k=k, **{x: cache[tuple(pool[best_k(k)]["sites"])][x] for x in ["total", "fixed", "fleet", "fuel", "spot", "penalty", "relay", "owned", "ok98", "service_min", "km_day", "vehicles_day"]},
                  evals=sum(r["k"] == k for r in log_bo), origin=pool[best_k(k)]["origin"], cand=best_k(k)) for k in ks]

    def k_star(rows, key="total", ok="ok98"):
        good = [r for r in rows if r[ok]]
        return min(good, key=lambda r: r[key])["k"] if good else None

    # Check 1: departure waves from 04:00 to 07:00, docks for a DC at the store cap, on the best candidate of every k
    docks = int(np.ceil(ctx["hi"] * base["vehicles_day"] / ctx["n"] / len(C.WAVES)))
    wave_rows = []
    for s in sweep:
        e = evaluate.evaluate(ctx, pool[s["cand"]]["sites"], d_search, docks=docks)
        wave_rows.append(dict(k=s["k"], total=e["total"], total_plain=s["total"], ok98=e["ok98"] and e["dock_over_day"] == 0,
                              service_min=e["service_min"], dock_over_day=e["dock_over_day"], vehicles_day=e["vehicles_day"],
                              vehicles_plain=s["vehicles_day"]))
    wb = evaluate.evaluate(ctx, ctx["current"], d_search, assign=ctx["hist_assign"], docks=docks)
    waves = dict(docks=docks, waves=list(C.WAVES), rows=wave_rows, baseline=_summary(wb), baseline_plain=_summary(base),
                 k_star_plain=k_star(sweep), k_star_waves=k_star(wave_rows))
    clock(f"departure-wave check: k* {waves['k_star_plain']} -> {waves['k_star_waves']}")

    # Check 2: thinning, the reduced instance against this one (same stores, 1 in 5 kept); needs run_reduced.py first
    thinning = None
    other = RESULTS / "reduced" / "registry.json"
    if profile["name"] != "reduced" and other.exists():
        r = json.loads(other.read_text())
        n_r = r["meta"]["stores_planning"]; by_k = {s["k"]: s for s in r["sweep"]}
        rows = [dict(k=s["k"], full=s["total"] / ctx["n"], reduced=by_k[s["k"]]["total"] / n_r,
                     km_full=s["km_day"] / ctx["n"], km_reduced=by_k[s["k"]].get("km_day", np.nan) / n_r) for s in sweep if s["k"] in by_k]
        thinning = dict(fraction=r["meta"]["fraction"], stores_reduced=n_r, rows=rows, k_star_full=k_star(sweep),
                        k_star_reduced=k_star(r["sweep"]), km_ratio_pred=float(np.sqrt(1 / r["meta"]["fraction"])),
                        km_ratio_baseline=(r["finals"]["baseline"]["km_day"] / n_r) / (fb["km_day"] / ctx["n"]))
        clock(f"thinning check: k* full {thinning['k_star_full']}, reduced {thinning['k_star_reduced']}")

    # Store-level view: who moves, who is farther, who is late
    st_b, st_r = np.array(fb["store_ontime"]), np.array(fr["store_ontime"])
    assign_rec = evaluate.assign_lp(ctx, np.array(rec))["site"]
    d_b = ctx["dsite"][np.arange(ctx["n"]), ctx["hist_assign"]]; d_r = ctx["dsite"][np.arange(ctx["n"]), assign_rec]
    stores_view = dict(moved=int((assign_rec != ctx["hist_assign"]).sum()), farther=int((d_r > d_b + 0.5).sum()),
                       farther30=int((d_r > d_b + 30).sum()), worst_farther=float((d_r - d_b).max()),
                       below98_base=int((st_b < 0.98).sum()), below98_rec=int((st_r < 0.98).sum()),
                       worst_base=float(st_b.min()), worst_rec=float(st_r.min()))

    # R2: sampled days versus expected counts versus one average day
    e_sampled = cache[tuple(rec)] if tuple(rec) in cache else evaluate.evaluate(ctx, rec, d_search)
    e_mean = evaluate.evaluate(ctx, rec, [dict(d, q=d["q_mean"]) for d in d_search])
    e_avg = evaluate.evaluate(ctx, rec, [d_avg])
    e_peak = evaluate.evaluate(ctx, rec, [d_peak], owned=np.array(fr["owned_by_dc"]))
    ppc = demand.replicate_history(model, world, hist, seed + 7)
    clock("demand checks done")

    # R3 on every candidate the reported search evaluated
    evald = sorted({r["cand"] for r in log_bo})
    G = np.array([pool[i]["G1"] for i in evald]); E = E_pool[evald]
    g_pick = evald[int(np.argmin(G))]; e_pick = evald[int(np.argmin(E))]
    within = [ _spearman(G[[i for i, c in enumerate(evald) if pool[c]["k"] == k]], E[[i for i, c in enumerate(evald) if pool[c]["k"] == k]])
               for k in ks if sum(pool[c]["k"] == k for c in evald) >= 3]
    r3 = dict(spearman=_spearman(G, E), spearman_within_k=float(np.mean(within)) if within else None,
              r2=float(1 - ((E - G) ** 2).sum() / ((E - E.mean()) ** 2).sum()), rmse=float(np.sqrt(((E - G) ** 2).mean())),
              loss=float(E_pool[g_pick] - E.min()), g_pick_k=pool[g_pick]["k"], e_best_k=pool[e_pick]["k"],
              A=float(pool[e_pick]["G1"] - E_pool[e_pick]), B=float(E_pool[g_pick] - pool[g_pick]["G1"]),
              gap=float(pool[g_pick]["G1"] - pool[e_pick]["G1"]))

    # Routes for the map: an ordinary weekday and the peak day, both networks
    show_day = next((d for d in d_final if d["label"] == "weekday"), d_final[0])
    show = {}
    for name, sites_, asg, own in (("baseline", ctx["current"], ctx["hist_assign"], fb["owned_by_dc"]), ("recommended", rec, None, fr["owned_by_dc"])):
        for dname, day in (("weekday", show_day), ("peak", d_peak)):
            e = evaluate.evaluate(ctx, sites_, [day], assign=asg, owned=np.array(own), keep_routes=True)
            show[f"{name}_{dname}"] = dict(routes=e["routes"], summary=_summary(e))
    clock("map routes done")

    sizes = np.bincount(np.searchsorted(np.sort(rec), assign_rec), minlength=len(rec))
    live_dc = int(np.sort(rec)[sizes.argmax()])
    live_idx = np.flatnonzero(assign_rec == live_dc)
    weekend = next((d for d in d_final if d["label"] == "weekend"), d_final[1])
    live_days = [("ordinary weekday", show_day), ("weekend", weekend), (d_peak["label"], d_peak), ("annual average", d_avg)]

    def curve(log):
        out, b = [], np.inf
        for r in log:
            b = min(b, r["E"]); out.append(b)
        return out

    sites = world["sites"]
    reg = dict(
        meta=dict(profile=profile["name"], fraction=profile["fraction"], seed=seed, stores_planning=ctx["n"],
                  generated=datetime.now().isoformat(timespec="seconds"), runtime_s=round(time.time() - t0, 1),
                  command=f"python run_{profile['name']}.py", python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__,
                  machine=platform.machine(),
                  distance_model=distances.describe(),
                  bounds=[ctx["lo"], ctx["hi"]], k_range=[kmin, kmax], budget=C.BUDGET, days=[C.SEARCH_DAYS, C.FINAL_DAYS, C.HELDOUT_DAYS],
                  fleet_quantile=C.FLEET_Q),
        params=dict(cap=C.CAP, max_stops=C.MAX_STOPS, max_km=C.MAX_KM, stop_h=C.STOP_H, speed=C.SPEED, depart=C.DEPART,
                    deadline=C.DEADLINE, shift_end=C.SHIFT_END, break_h=C.BREAK_H, fail_at=C.FAIL_AT, detour=C.DETOUR,
                    detour_mountain=C.DETOUR_MOUNTAIN, road_coef=distances.cache() and distances.cache()['coef'].tolist(),
                    fuel_km=C.FUEL_KM, spot_day=C.SPOT_DAY, late_pen=C.LATE_PEN,
                    relay_day=C.RELAY_DAY, vehicle_month=C.VEHICLE_MONTH, days_month=C.DAYS_MONTH, fleet_q=C.FLEET_Q),
        geo=dict(provinces=[dict(name=n, rings=[np.round(r, 3).tolist() for r in rings]) for n, rings in world["provinces"]]),
        stores=dict(id=world["stores"]["id"][m].tolist(), lat=np.round(ctx["lat"], 4).tolist(), lon=np.round(ctx["lon"], 4).tolist(),
                    type=world["stores"]["type"][m].tolist(), rate=np.round(ctx["w"], 3).tolist(),
                    base_dc=ctx["hist_assign"].tolist(), rec_dc=assign_rec.tolist(), mountain=ctx["mountain"].astype(int).tolist(),
                    ontime_base=np.round(st_b, 3).tolist(), ontime_rec=np.round(st_r, 3).tolist()),
        sites=[dict(id=s_["id"], name=s_["name"], province=s_["province"], lat=s_["lat"], lon=s_["lon"], current=s_["current"],
                    fixed=s_["monthly_fixed_cost"]) for s_ in sites],
        networks=dict(baseline=ctx["current"].tolist(), recommended=rec, reassigned12=ctx["current"].tolist()),
        search_days=[dict(date=d["date"], label=d["label"], w=d["w"], chain=d["chain"]) for d in d_search],
        baseline_search=_summary(base),
        finals={k: _summary(v) for k, v in finals.items()},
        saving=dict(final_mean=fb["total"] - fr["total"], final_ci=_boot(fb, fr, 1),
                    held_mean=held_b["total"] - held_r["total"], held_ci=_boot(held_b, held_r, 2, fixed_fleet=True),
                    held_service_base=float(np.average(held_b["service"], weights=held_b["w"])),
                    held_service_rec=float(np.average(held_r["service"], weights=held_r["w"])),
                    waterfall=[dict(step="current network", total=fb["total"]),
                               dict(step="same 12 DCs, territories redrawn", total=finals["reassigned12"]["total"]),
                               dict(step="best 12 sites", total=finals["best12"]["total"]) if "best12" in finals else None,
                               dict(step=f"recommended ({fr['k']} DCs)", total=fr["total"])]),
        reversal=reversal, stores_view=stores_view,
        pool=[dict(sites=p["sites"], k=p["k"], origin=p["origin"], G1=p["G1"], features=p["features"], E=float(E_pool[i]),
                   ok98=cache[tuple(p["sites"])]["ok98"]) for i, p in enumerate(pool)],
        feature_names=search.FEATURE_NAMES, top5=[dict(cand=i, k=pool[i]["k"], search_E=E_pool[i], final_E=top_final[i]["total"]) for i in top],
        log_bo=log_bo, log_random=log_rand, curve_bo=curve(log_bo), curve_random=curve(log_rand), random_band=band, pool_best=pool_best,
        sweep=sweep, waves=waves, thinning=thinning, history_ops=hist_ops,
        r2=dict(sampled=e_sampled["total"], expected_counts=e_mean["total"], average_day=e_avg["total"], peak_vehicles=float(np.sum(e_peak["V"])),
                peak_spot_day=float(e_peak["spot"] / C.DAYS_MONTH), peak_service=float(e_peak["service"][0]), owned=fr["owned"], peak_date=d_peak["date"],
                phi=model["phi"], sigma=model["sigma"], prior_strength=model["b0_type"].tolist(), kappa=model["kappa"], m_type=model["m_type"].tolist(),
                chain_hist=[float(x) for x in (np.where(hist["y"] >= 0, hist["y"], 0).sum(0))], chain_rep=[float(x) for x in ppc],
                hist_dates=hist["cal"]["date"], example=_example_store(world, model, hist)),
        r3=r3,
        show=dict(day=dict(date=show_day["date"], label=show_day["label"]), peak=dict(date=d_peak["date"], label=d_peak["label"]), **show),
        live=dict(dc=live_dc, stores=live_idx.tolist(), days=[dict(name=nm, q=np.round(d["q"][live_idx], 2).tolist()) for nm, d in live_days]),
        cases=dict(failure=None, boundary_hi=[int(j) for j, l in zip(fr["open"], fr["loads"]) if l >= ctx["hi"]],
                   boundary_lo=[int(j) for j, l in zip(fr["open"], fr["loads"]) if l <= ctx["lo"]],
                   budget_one=log_bo[0]["E"], budget_full=min(r["E"] for r in log_bo)),
    )
    if kmin > 1:
        f = evaluate.evaluate(ctx, pool[0]["sites"][: kmin - 1], d_search[:1])
        reg["cases"]["failure"] = dict(feasible=f["feasible"], reason=f.get("reason"), k=kmin - 1)
    out = RESULTS / profile["name"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "registry.json").write_text(json.dumps(reg, default=_np))
    clock(f"registry written: {out / 'registry.json'}")
    return reg


def _example_store(world, model, hist):
    # A short-history store: prior, data and posterior in Lecture 2 terms
    m = (world["stores"]["opened"] > 300) & (world["stores"]["closed"] >= 365)
    i = int(np.flatnonzero(m)[0]) if m.any() else 0
    obs = hist["y"][i] >= 0
    return dict(store=str(world["stores"]["id"][i]), days=int(obs.sum()), cages=int(hist["y"][i][obs].sum()),
                exposure=float(model["b"][i] - model["b0"][i]),
                a0=float(model["a0"][i]), b0=float(model["b0"][i]), a=float(model["a"][i]), b=float(model["b"][i]),
                prior_mean=float(model["a0"][i] / model["b0"][i]), post_mean=float(model["a"][i] / model["b"][i]),
                data_mean=float(hist["y"][i][obs].sum() / max(model["b"][i] - model["b0"][i], 1e-9)),
                true_rate=float(world["stores"]["rate_true"][i]))


def _np(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))
