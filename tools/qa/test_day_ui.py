"""Click through the strip tooltip and the Delivery day live solve offline: python tools/qa/test_day_ui.py out_dir."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(("file:", "data:", "blob:")) else r.continue_())
    pg.goto((ROOT / "demo.html").as_uri() + "#answer"); pg.wait_for_timeout(2500)
    s = pg.locator("#whystrip"); s.scroll_into_view_if_needed(); pg.wait_for_timeout(800); bb = s.bounding_box()
    found = None
    for fx in [i / 60 for i in range(6, 58)]:
        pg.mouse.move(bb["x"] + bb["width"] * fx, bb["y"] + bb["height"] * 0.3); pg.wait_for_timeout(15)
        if pg.evaluate("getComputedStyle(document.querySelector('#tip')).display") == "block": found = pg.inner_text("#tip"); break
    print("strip tooltip:", found)
    pg.goto((ROOT / "demo.html").as_uri() + "#day"); pg.wait_for_timeout(3000)
    pg.click("#play"); pg.wait_for_timeout(2500); pg.click("#play"); pg.locator("#daymap").screenshot(path=str(OUT / "day_network.png"))
    pg.click("#lv-solve"); pg.wait_for_timeout(150); print("during:", pg.inner_text("#lv-solve"), "|", pg.inner_text("#lv-status"))
    pg.wait_for_function("() => !document.querySelector('#lv-solve').disabled", timeout=60000)
    print("after:", pg.inner_text("#lv-status"), "| banner:", pg.inner_text("#live-banner-text"))
    pg.locator("#daymap").screenshot(path=str(OUT / "day_live_done.png"))
    pg.click("#play"); pg.wait_for_timeout(3000); print("play label:", pg.inner_text("#play"), "| clock:", pg.inner_text("#clock"))
    pg.locator("#daymap").screenshot(path=str(OUT / "day_live_play.png"))
    pg.click("#play"); pg.click("#live-back"); pg.wait_for_timeout(500); print("banner hidden after back:", pg.evaluate("document.querySelector('#live-banner').hidden"))
    print("errors:", errs); b.close()
