"""Check every slide of proposal.html: errors, elements outside the slide, page width: python proposal_slides.py <html> <shot prefix>"""
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_context(viewport={"width": 1440, "height": 860}, offline=True).new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.goto(sys.argv[1]); pg.wait_for_timeout(800)
    n = pg.evaluate("document.querySelectorAll('.slide').length")
    for i in range(n):
        pg.evaluate(f"go({i})"); pg.wait_for_timeout(600)
        over = pg.evaluate("""[...document.querySelectorAll('.slide.on *')].filter(e => { const r = e.getBoundingClientRect(), s = document.querySelector('.slide.on').getBoundingClientRect(); return r.bottom > s.bottom + 1 || r.right > s.right + 1; }).length""")
        pg.screenshot(path=f"{sys.argv[2]}_{i + 1:02d}.png")
        if over: print(i + 1, "overflowing elements", over)
    print(n, "slides; errors", errs, "page wider than window by", pg.evaluate("document.documentElement.scrollWidth - innerWidth")); b.close()
