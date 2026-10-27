"""Offline browser check of demo.html: every tab at 1440 and 390 px, errors, blocked requests, overflow, cut formulas: python demo_offline.py <html> <shot prefix>"""
import sys
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch(); print("chromium", b.version)
    for w in (1440, 390):
        ctx = b.new_context(viewport={"width": w, "height": 900})
        blocked = []
        ctx.route("**/*", lambda r: (blocked.append(r.request.url), r.abort()) if not r.request.url.startswith("file://") else r.continue_())
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(url); pg.wait_for_timeout(1200)
        for t in ["answer", "day", "how", "data", "checks", "ext"]:
            pg.evaluate(f"show('{t}')"); pg.wait_for_timeout(2600)
            ov = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            cut = pg.evaluate("[...document.querySelectorAll('.view.on .formula')].filter(e => e.scrollWidth > e.clientWidth + 2).length")
            pg.screenshot(path=f"{out}_{w}_{t}.png", full_page=(w == 1440))
            if ov > 0: print(w, t, "page overflow", ov)
            if cut and w == 1440: print(w, t, "formulas wider than their box:", cut)
        print(w, "errors", errs, "blocked", blocked[:3])
    b.close()
