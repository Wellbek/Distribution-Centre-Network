"""Embed a run's results registry, formulas and verification into ../demo.html: python build_demo.py"""
import json
from pathlib import Path

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
    reg = (res / "registry.json").read_text()
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


if __name__ == "__main__":
    build(C.DEMO_PROFILE)
