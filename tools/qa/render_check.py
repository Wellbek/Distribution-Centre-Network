"""Render demo.html and proposal.html offline, print the key texts and errors, save slide 9: python tools/qa/render_check.py out_dir."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    errs, ext = [], []
    for name in ("demo", "proposal"):
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        pg.on("console", lambda m: errs.append(f"{name}: {m.text}") if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(f"{name}: {e}"))
        pg.route("**/*", lambda r: (ext.append(r.request.url), r.abort()) if not r.request.url.startswith(("file:", "data:", "blob:")) else r.continue_())
        if name == "demo":
            pg.goto((ROOT / "demo.html").as_uri() + "#answer"); pg.wait_for_timeout(2500)
            print("WHY-SUB:", pg.inner_text("#why-sub")); print("LADDER:", pg.inner_text("#ladder"))
            pg.locator("#whystrip").scroll_into_view_if_needed(); pg.wait_for_timeout(1500); pg.locator("#whystrip").screenshot(path=str(OUT / "demo_strip.png"))
            pg.goto((ROOT / "demo.html").as_uri() + "#how"); pg.wait_for_timeout(2500)
            t = pg.inner_text("main"); i = t.find("Refinement after"); print("Q5:", t[i:i + 900] if i >= 0 else "NOT FOUND")
            print("demo horizontal overflow:", pg.evaluate("() => document.documentElement.scrollWidth > innerWidth"))
        else:
            pg.set_viewport_size({"width": 1600, "height": 900})
            for s in (5, 9):
                q = b.new_page(viewport={"width": 1600, "height": 900}); q.goto((ROOT / "proposal.html").as_uri() + f"#{s}"); q.wait_for_timeout(1500); q.screenshot(path=str(OUT / f"proposal_{s}.png")); q.close()
    print("errors:", errs); print("external:", ext)
    b.close()
