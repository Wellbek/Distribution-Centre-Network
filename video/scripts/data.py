"""Write the trailer's numbers from the shipped registry, so no figure in the video is typed by hand: python video/scripts/data.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "code" / "results" / "full" / "registry.json").read_text())
sys.path.insert(0, str(ROOT / "code"))
from checks.routing_summary import summary  # noqa: E402
r["routing_check"] = summary()
F, sv, sites, q = r["finals"], r["saving"], r["sites"], r["extensions"]["sequence"]
base, rec = r["networks"]["baseline"], r["networks"]["recommended"]
M = lambda v: round(v / 1e6, 1)
d = dict(
    stores=r["meta"]["stores_planning"], sites=len(sites), today_k=len(base), k=F["recommended"]["k"],
    kept=[sites[j]["name"] for j in rec if j in base], opened=[sites[j]["name"] for j in rec if j not in base],
    saving=M(sv["final_mean"]), ci=[M(x) for x in sv["final_ci"]], held=M(sv["held_mean"]), redraw=M(sv["waterfall"][0]["total"] - sv["waterfall"][1]["total"]),
    today=M(F["baseline"]["total"]), recommended=M(F["recommended"]["total"]), eight=M(F["best_k8"]["total"] - F["recommended"]["total"]),
    proxy_k=F["proxy_only"]["k"], proxy_loss=M(F["proxy_only"]["total"] - F["recommended"]["total"]), r2_g1=round(r["r3_g1"]["r2_line"], 2), r2_g2=round(r["r3"]["r2_line"], 2),
    networks=len(r["pool"]) + len(r["extensions"]["generation"]["evaluated"]), budget=r["meta"]["budget"],
    found_at=next(i + 1 for i, v in enumerate(r["curve_bo"]) if v <= r["pool_best"] + 1), random_gap=M(r["random_band"]["p50"][-1] - r["pool_best"]),
    pyvrp=M(sv["final_mean"] - r["routing_check"]["saving_month_shift"]) if r.get("routing_check") else None,
    moved=r["stores_view"]["moved"], service=round(100 * F["recommended"]["service_mean"], 1),
    seq_saving=round((q["cum_never"] - q["committed"]["cum"]) / 1e9, 1), seq_redraw=round((q["cum_never"] - q["cum_redrawn"]) / 1e9, 1), one_shot=round((q["cum_one_shot"] - q["cum_never"]) / 1e9, 1),
    steps=[dict(date=s["date"][:7], site=s["site"].split(" ")[0], action=s["action"], opened=[o.split(" ")[0] for o in s["opened"]]) for s in q["committed"]["steps"]],
    evpi=M(r["extensions"]["voi"]["travel"]["evpi"]), reversals=sum(x["saving"] > 0 for x in r["reversals"][1:]), reversal_rows=len(r["reversals"]) - 1,
    sweep=[dict(k=s["k"], fixed=M(s["fixed"]), total=M(s["total"])) for s in r["sweep"]], today_search=M(r["baseline_search"]["total"]),
)
# Geography for the trailer's own map: province outlines (every third point), one store in six, both networks' DCs
st = r["stores"]
d["provinces"] = [[[round(x, 3) for x in pt] for pt in ring[::3]] for pr in r["geo"]["provinces"] for ring in pr["rings"] if len(ring) > 12]
d["stores_sample"] = [[round(st["lat"][i], 3), round(st["lon"][i], 3), int(st["base_dc"][i] != st["rec_dc"][i])] for i in range(0, len(st["lat"]), 6)]
d["dcs_today"] = [[sites[j]["lat"], sites[j]["lon"], sites[j]["name"], int(j in rec)] for j in base]
d["dcs_rec"] = [[sites[j]["lat"], sites[j]["lon"], sites[j]["name"], int(j in base)] for j in rec]
(ROOT / "video" / "src" / "data.json").write_text(json.dumps(d))
print({k: d[k] for k in ("saving", "held", "k", "networks", "found_at", "pyvrp", "seq_saving", "proxy_loss")})
