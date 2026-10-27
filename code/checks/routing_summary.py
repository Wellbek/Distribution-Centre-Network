"""Summarise the cached PyVRP comparisons (results/checks/) per network: python checks/routing_summary.py"""
import json
from pathlib import Path

CHECKS = Path(__file__).resolve().parents[1] / "results" / "checks"
DAYS_MONTH = 30.4167


def summary(folder=CHECKS):
    """Per network: vehicles and day cost under savings and under PyVRP (savings where PyVRP left stores unrouted); None without results."""
    rows = {}
    # The pass with the longer time limit for a territory (a file named with its DCs) overrides the first pass
    for f in sorted(folder.glob("routing_gap_*_0*.json"), key=lambda f: len(f.name)):
        for r in json.loads(f.read_text()):
            rows[(r["net"], r["dc"])] = r
    if not rows:
        return None
    out = {}
    for net in ("baseline", "recommended"):
        rs = [r for (n, _), r in sorted(rows.items()) if n == net]
        ok = [r for r in rs if r["hgs_bad"] == 0]
        out[net] = dict(territories=len(rs), pyvrp_feasible=len(ok), unrouted=[r["dc"] for r in rs if r["hgs_bad"] > 0],
                        cw_veh=sum(r["cw_veh"] for r in rs), hgs_veh=sum(r["hgs_veh"] if r["hgs_bad"] == 0 else r["cw_veh"] for r in rs),
                        cw_cost=sum(r["cw_cost"] for r in rs), hgs_cost=sum(r["hgs_cost"] if r["hgs_bad"] == 0 else r["cw_cost"] for r in rs),
                        gaps=sorted(r["cw_cost"] / r["hgs_cost"] - 1 for r in ok),
                        per_dc=[dict(dc=r["dc"], stores=r["stores"], cw_veh=r["cw_veh"], hgs_veh=r["hgs_veh"] if r["hgs_bad"] == 0 else None) for r in rs])
    rd = [r for (n, _), r in sorted(rows.items()) if n == "redrawn"]
    if rd:
        out["redrawn"] = dict(cw_cost=sum(r["cw_cost"] for r in rd), hgs_cost=sum(r["hgs_cost"] if r["hgs_bad"] == 0 else r["cw_cost"] for r in rd),
                              unrouted=[r["dc"] for r in rd if r["hgs_bad"] > 0])
    b, r = out["baseline"], out["recommended"]
    out["saving_day_cw"] = b["cw_cost"] - r["cw_cost"]
    out["saving_day_hgs"] = b["hgs_cost"] - r["hgs_cost"]
    out["saving_month_shift"] = (out["saving_day_cw"] - out["saving_day_hgs"]) * DAYS_MONTH
    # k check: the recommendation and any other network checked (files named by their sites), rent per day plus routed cost
    reg = json.loads((folder.parent / "full" / "registry.json").read_text())
    fixed = [x["fixed"] for x in reg["sites"]]
    nets = {"recommended": reg["networks"]["recommended"]}
    nets.update({n: [int(x) for x in n.split("-")] for (n, _) in rows if n[0].isdigit()})
    out["k_check"] = []
    for n, sites in nets.items():
        rs = [r for (m, _), r in rows.items() if m == n]
        if len(rs) != len(sites):
            continue
        rent = sum(fixed[j] for j in sites) / DAYS_MONTH
        out["k_check"].append(dict(k=len(sites), cw=rent + sum(r["cw_cost"] for r in rs),
                                   hgs=rent + sum(r["hgs_cost"] if r["hgs_bad"] == 0 else r["cw_cost"] for r in rs),
                                   unrouted=sum(r["hgs_bad"] > 0 for r in rs)))
    out["k_check"].sort(key=lambda x: x["k"])
    return out


if __name__ == "__main__":
    s = summary()
    for net in ("baseline", "recommended"):
        x = s[net]
        print(f"{net}: {x['cw_veh']} vehicles by savings, {x['hgs_veh']} by PyVRP; day cost {x['cw_cost'] / 1e6:.1f} vs {x['hgs_cost'] / 1e6:.1f} M; "
              f"PyVRP feasible on {x['pyvrp_feasible']} of {x['territories']} territories")
    print(f"day-0 operating saving: {s['saving_day_cw'] / 1e6:.1f} M a day by savings, {s['saving_day_hgs'] / 1e6:.1f} M by PyVRP; "
          f"monthly saving lower by about {s['saving_month_shift'] / 1e6:.0f} M with PyVRP routes")
    if "redrawn" in s:
        x = s["redrawn"]
        print(f"redraw step, day cost: savings {(s['baseline']['cw_cost'] - x['cw_cost']) / 1e6:.1f} M, PyVRP {(s['baseline']['hgs_cost'] - x['hgs_cost']) / 1e6:.1f} M ({len(x['unrouted'])} territories unrouted by PyVRP)")
    for x in s["k_check"]:
        print(f"k = {x['k']}: day cost with rent {x['cw'] / 1e6:.1f} M by savings, {x['hgs'] / 1e6:.1f} M by PyVRP ({x['unrouted']} territories unrouted by PyVRP)")
