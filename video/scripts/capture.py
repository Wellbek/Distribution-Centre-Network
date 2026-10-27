"""Capture the trailer's footage from demo.html and proposal.html (frame-exact, 1920x1080): python video/scripts/capture.py"""
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "video" / "public"
FR = PUB / "frames"


def encode(name, n):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(FR / name / "%04d.png"), "-frames:v", str(n), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(PUB / f"{name}.mp4")], check=True)
    shutil.rmtree(FR / name)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.emulate_media(reduced_motion="reduce")
    pg.goto((ROOT / "demo.html").as_uri()); pg.wait_for_timeout(1500)
    pg.screenshot(path=str(PUB / "answer_hero.png"))
    # Delivery day: the clock stepped from 04:00 to 12:40 over 300 frames
    pg.evaluate("show('day')"); pg.wait_for_timeout(1500)
    (FR / "day").mkdir(parents=True, exist_ok=True)
    for i in range(300 if not (PUB / "day.mp4").exists() else 0):
        pg.evaluate(f"T = {4.0 + i * (8.67 / 299)}; DM.draw(); kpisDay()")
        pg.screenshot(path=str(FR / "day" / f"{i:04d}.png"))
    if not (PUB / "day.mp4").exists():
        encode("day", 300)
    # Answer map: today's territories giving way to the recommended ones over 120 frames, then held
    pg.evaluate("show('answer')"); pg.wait_for_timeout(800)
    pg.evaluate("document.querySelector('#ansmap').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(500)
    pg.evaluate("morphAns()"); pg.wait_for_timeout(3600)
    (FR / "morph").mkdir(parents=True, exist_ok=True)
    box = pg.query_selector("#ansmap").bounding_box()
    clip = dict(x=box["x"], y=box["y"], width=box["width"], height=box["height"])
    for i in range(150):
        f = min(1, i / 119)
        pg.evaluate(f"ansMode('morph'); MT = {f}; ANS.draw()")
        pg.screenshot(path=str(FR / "morph" / f"{i:04d}.png"), clip=clip)
    encode("morph", 150)
    for sel, name in (("#why ~ .grid", "why"), ("#sweep", "sweep")):
        pg.evaluate(f"document.querySelector('{sel}').scrollIntoView({{block: 'center'}})"); pg.wait_for_timeout(600)
        pg.query_selector(sel).screenshot(path=str(PUB / f"{name}.png"))
    pg.evaluate("show('how')"); pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('#q5').scrollIntoView({block: 'start'})"); pg.wait_for_timeout(800)
    pg.query_selector("#q5").screenshot(path=str(PUB / "search.png"))
    # Proposal slides as stills
    pg.goto((ROOT / "proposal.html").as_uri()); pg.wait_for_timeout(1000)
    for n in (1, 12, 15):
        pg.evaluate(f"go({n - 1})"); pg.wait_for_timeout(700)
        pg.query_selector(".slide.on").screenshot(path=str(PUB / f"slide{n:02d}.png"))
    b.close()
print("captured:", sorted(x.name for x in PUB.iterdir() if x.is_file()))
