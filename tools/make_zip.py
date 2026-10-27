"""Build the hand-in ZIP from an allowlist (planning/, tools/ and the brief stay out): python3 tools/make_zip.py"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "20264059_LouisWellmeyer"
FILES = ["problem-definition.md", "demo.html", "proposal.html"]
SKIP = {".venv310", "__pycache__", ".ruff_cache", ".pytest_cache"}

out = ROOT.parent / f"{NAME}.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        z.write(ROOT / f, f"{NAME}/{f}")
    for f in sorted((ROOT / "code").rglob("*")):
        if f.is_file() and not SKIP & set(f.relative_to(ROOT).parts):
            z.write(f, f"{NAME}/{f.relative_to(ROOT)}")
print(f"{out}: {out.stat().st_size / 1e6:.1f} MB, {len(zipfile.ZipFile(out).namelist())} files")
