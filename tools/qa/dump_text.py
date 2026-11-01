"""Dump the rendered text of every demo tab and proposal slide, for consistency checks: python tools/qa/dump_text.py out_dir."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(); out = []
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith(("file:", "data:", "blob:")) else r.continue_())
    for tab in ("answer", "day", "how", "data", "checks", "ext"):
        pg.goto((ROOT / "demo.html").as_uri() + f"#{tab}"); pg.wait_for_timeout(2500)
        out.append(f"\n===== DEMO {tab}\n" + pg.evaluate("document.querySelector('#v-' + location.hash.slice(1)) ? document.querySelector('#v-' + location.hash.slice(1)).innerText : document.querySelector('main').innerText"))
    (OUT / "demo.txt").write_text("".join(out)); out = []
    n = pg.goto((ROOT / "proposal.html").as_uri()) and pg.evaluate("document.querySelectorAll('.slide, section').length")
    for s in range(1, 18):
        q = b.new_page(viewport={"width": 1600, "height": 900}); q.goto((ROOT / "proposal.html").as_uri() + f"#{s}"); q.wait_for_timeout(700)
        out.append(f"\n===== SLIDE {s}\n" + q.evaluate("(() => { const v = [...document.querySelectorAll('.slide, section')].filter(e => e.offsetParent !== null && getComputedStyle(e).visibility !== 'hidden' && +getComputedStyle(e).opacity > 0.5); return v.map(e => e.innerText).join('\\n') || document.body.innerText; })()")); q.close()
    (OUT / "proposal.txt").write_text("".join(out)); b.close()
print("ok")
