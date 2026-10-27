"""Embed a run's results registry, formulas and verification into ../demo.html and ../proposal.html: python build_demo.py"""
import json
from pathlib import Path

from checks.routing_summary import summary
from dcn import config as C

ROOT = Path(__file__).resolve().parent


def _shapes(res, reg):
    # Road shapes from osrm/build_shapes.py, only if fetched for this registry's routes
    f = res / "shapes.json"
    if not f.exists():
        return "null"
    s = json.loads(f.read_text())
    return json.dumps(s["legs"]) if s["meta"]["registry"] == json.loads(reg)["meta"]["generated"] else "null"


def build(profile="reduced"):
    res = ROOT / "results" / profile
    # The cached PyVRP comparison (optional check) travels with the registry so both pages can show it
    r = json.loads((res / "registry.json").read_text())
    r["routing_check"] = summary() if profile == "full" else None
    reg = json.dumps(r)
    ver = (res / "verification.json").read_text() if (res / "verification.json").exists() else "null"
    tpl = (ROOT / "static" / "demo.template.html").read_text()
    html = (tpl.replace("/*__KATEX__*/", (ROOT / "static" / "katex.css").read_text())
               .replace("/*__MATH__*/null", (ROOT / "static" / "math.json").read_text())
               .replace("/*__VERIFY__*/null", ver)
               .replace("/*__SHAPES__*/null", _shapes(res, reg))
               .replace("/*__DATA__*/null", reg))
    out = ROOT.parent / "demo.html"
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")
    # The proposal reads the same registry, slimmed to what its slides show
    keep = ["meta", "routing_check", "finals", "saving", "sweep", "reversals", "r3", "r3_g1", "extensions", "networks", "sites", "geo", "top5", "pool_best",
            "baseline_search", "stores_view", "log_bo", "random_band"]
    slim = {k: r.get(k) for k in keep}
    slim["stores"] = {k: r["stores"][k] for k in ("lat", "lon", "base_dc", "rec_dc")}
    slim["params"] = r["params"]
    ver = ROOT / "results" / "full" / "verification.json"
    slim["exact"] = next((c["detail"] for c in json.loads(ver.read_text())["checks"] if c["check"].startswith("heuristic vs exact")), None) if ver.exists() else None
    slim["r2"] = {k: r["r2"][k] for k in ("peak_vehicles", "owned", "peak_date")}
    slim["pool"] = [dict(sites=p["sites"], k=p["k"], origin=p["origin"], E=p["E"], ok98=p["ok98"]) for p in r["pool"]]
    tpl = (ROOT / "static" / "proposal.template.html").read_text()
    out = ROOT.parent / "proposal.html"
    out.write_text(tpl.replace("/*__DATA__*/null", json.dumps(slim)))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    build(C.DEMO_PROFILE)
