"""Click through the live search panel of demo.html offline: python tools/qa/test_live_ui.py out_dir."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(("file:", "data:", "blob:")) else r.continue_())
    pg.goto((ROOT / "demo.html").as_uri() + "#how"); pg.wait_for_timeout(2500)
    def run(label):
        pg.click("#ls-run"); pg.wait_for_function("() => document.querySelector('#ls-status').textContent.startsWith('Done')", timeout=120000)
        print(label, "|", pg.inner_text("#ls-status"), "|", pg.inner_text("#ls-out"))
    run("seeds B=40")
    pg.locator("#live-search").scroll_into_view_if_needed(); pg.locator("#live-search").screenshot(path=str(OUT / "live_seeds.png"))
    pg.fill("#ls-budget", "1"); pg.dispatch_event("#ls-budget", "input"); run("seeds B=1")
    pg.fill("#ls-budget", "40"); pg.dispatch_event("#ls-budget", "input"); pg.click("#ls-start button[data-n='5']"); run("5 random")
    pg.locator("#live-search").screenshot(path=str(OUT / "live_random.png"))
    print("errors:", errs); b.close()
