"""Render the midterm brain, rolling records and stakeholder panel into one offline HTML page: python3 planning/build_plan.py"""
import base64
import json
import re
import subprocess
from pathlib import Path

from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
KATEX = HERE.parents[1] / "HW01" / "src" / "node_modules" / "katex"
OUT = HERE / "MIDTERM_BRAIN.html"

MATH = re.compile(r"\$\$(.+?)\$\$|\$(?!\s)([^$\n]+?)(?<!\s)\$", re.S)


def render_math(exprs):
    # Render every formula in one node call
    js = (
        f"const k=require({json.dumps(str(KATEX))});"
        "const xs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
        "console.log(JSON.stringify(xs.map(([t,d])=>k.renderToString(t,{displayMode:d,throwOnError:true}))));"
    )
    res = subprocess.run(["node", "-e", js], input=json.dumps(exprs), capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def protect_math(text, store):
    def sub(m):
        display = m.group(1) is not None
        store.append([m.group(1) if display else m.group(2), display])
        return f"MATHPH{len(store) - 1:04d}X"
    return MATH.sub(sub, text)


def slug(text, seen):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"
    base, n = s, 2
    while s in seen:
        s, n = f"{base}-{n}", n + 1
    seen.add(s)
    return s


def to_html(md_text, store, seen, toc=None):
    md = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")
    tokens = md.parse(protect_math(md_text, store))
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            title = tokens[i + 1].content
            hid = slug(title, seen)
            tok.attrSet("id", hid)
            if toc is not None and tok.tag == "h2":
                toc.append((hid, title))
    return md.renderer.render(tokens, md.options, {})


def drop_title(path):
    # Drop the file's own H1, the appendix heading replaces it
    return path.read_text().split("\n", 1)[1]


def katex_css():
    # Inline KaTeX css with woff2 fonts so the page works offline
    css = (KATEX / "dist" / "katex.min.css").read_text()
    def font(m):
        f = KATEX / "dist" / m.group(1)
        return f"url(data:font/woff2;base64,{base64.b64encode(f.read_bytes()).decode()})"
    css = re.sub(r"url\((fonts/[^)]+\.woff2)\)", font, css)
    return re.sub(r",\s*url\(fonts/[^)]+\.(woff|ttf)\)\s*format\(\"(woff|truetype)\"\)", "", css)


def persona_cards(store, seen):
    cards = []
    for p in sorted((HERE / "stakeholders").glob("*/README.md")):
        title = p.read_text().splitlines()[0].lstrip("# ").strip()
        pid = f"persona-{p.parent.name[:2]}"
        cards.append(f'<details class="persona" id="{pid}"><summary>{title}</summary>{to_html(drop_title(p), store, seen)}</details>')
    return "\n".join(cards)


def main():
    store, seen, toc = [], set(), []
    brain = to_html((HERE / "MIDTERM_BRAIN.md").read_text(), store, seen, toc)
    appendices = [
        ("appendix-a", "A. Stakeholder panel",
         to_html(drop_title(HERE / "stakeholders" / "README.md"), store, seen) + f'<div class="cards">{persona_cards(store, seen)}</div>'),
        ("appendix-b", "B. Review 01 transcript", to_html(drop_title(HERE / "stakeholders" / "REVIEW-01-plan-v1.md"), store, seen)),
        ("appendix-c", "C. Rolling record: LLM use", to_html(drop_title(HERE / "LLM_USE.md"), store, seen)),
        ("appendix-d", "D. Rolling record: decisions", to_html(drop_title(HERE / "DECISIONS.md"), store, seen)),
    ]
    toc += [(a, t) for a, t, _ in appendices]

    rendered = render_math(store)
    body = brain + "".join(f'<h2 id="{a}">{t}</h2>{h}' for a, t, h in appendices)
    body = re.sub(r"MATHPH(\d{4})X", lambda m: rendered[int(m.group(1))], body)
    # Point file links of the panel at the cards and appendices on this page
    body = re.sub(r'href="(\d\d)-[^"/]+/README\.md"', r'href="#persona-\1"', body)
    body = body.replace('href="REVIEW-01-plan-v1.md"', 'href="#appendix-b"')
    # Wrap tables so wide ones scroll inside their card
    body = body.replace("<table>", '<div class="table"><table>').replace("</table>", "</table></div>")
    nav = "\n".join(f'<a href="#{h}">{t}</a>' for h, t in toc)

    html = TEMPLATE.replace("{{CSS}}", katex_css()).replace("{{NAV}}", nav).replace("{{BODY}}", body)
    assert "\u2014" not in html, "em dash in output"
    OUT.write_text(html)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.2f} MB, {len(store)} formulas)")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Midterm Brain</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;700&family=Noto+Sans+KR:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
{{CSS}}
:root {
  --purple: #751485; --purple-deep: #5a0f66; --purple-tint: #f4ecf6;
  --green: #9dc92a; --green-tint: #f2f8e3;
  --ink: #222222; --ink-soft: #555555; --muted: #787878; --line: #dddddd;
  --paper: #ffffff; --canvas: #f0f0f0; --code: #f7f5f8; --nav: #5a0f66; --th: #5a0f66;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --purple: #c58fd3; --purple-deep: #e2c3ea; --purple-tint: #2a1f2e; --green-tint: #1f2614;
    --ink: #ececec; --ink-soft: #c4c4c4; --muted: #9a9a9a; --line: #3a3a3a;
    --paper: #18161a; --canvas: #101012; --code: #221f25; --nav: #241a28; --th: #c58fd3;
  }
}
:root[data-theme="dark"] {
  --purple: #c58fd3; --purple-deep: #e2c3ea; --purple-tint: #2a1f2e; --green-tint: #1f2614;
  --ink: #ececec; --ink-soft: #c4c4c4; --muted: #9a9a9a; --line: #3a3a3a;
  --paper: #18161a; --canvas: #101012; --code: #221f25; --nav: #241a28; --th: #c58fd3;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 16px; }
body { margin: 0; background: var(--canvas); color: var(--ink);
  font: 15px/1.6 "Noto Sans", "Noto Sans KR", "Noto Sans CJK KR", system-ui, sans-serif; }
.toc summary { list-style: none; cursor: pointer; color: #fff; font-weight: 700; font-size: 13px;
  padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,.1); margin-bottom: 8px; }
.toc summary::-webkit-details-marker { display: none; }
.toc summary::after { content: " +"; }
.toc[open] summary::after { content: " -"; }
.shell { display: grid; grid-template-columns: 280px minmax(0, 1fr); min-height: 100vh; }
nav { position: sticky; top: 0; height: 100vh; overflow-y: auto; background: var(--nav); padding: 24px 16px; }
.brand { display: flex; align-items: center; gap: 10px; color: #fff; font-weight: 700; font-size: 17px; margin: 0 8px 4px; }
.dot { width: 12px; height: 12px; border-radius: 50%; background: var(--green); flex: none; }
.sub { color: #d9c3de; font-size: 12px; margin: 0 8px 18px; }
nav a { display: block; color: #f3e9f5; text-decoration: none; font-size: 13px; padding: 6px 10px;
  border-radius: 999px; line-height: 1.35; }
nav a:hover, nav a:focus-visible { background: rgba(255,255,255,.12); outline: none; }
main { padding: 32px 40px 80px; max-width: 1180px; }
.hero { background: #751485; color: #fff; border-radius: 16px; padding: 28px 32px; margin-bottom: 28px; }
.hero h1 { margin: 0 0 6px; font-size: 28px; line-height: 1.2; color: #fff; }
.hero p { margin: 4px 0; color: #f1e4f4; }
.pill { display: inline-block; background: var(--green); color: #1b2a05; font-weight: 700; font-size: 12px;
  border-radius: 999px; padding: 3px 12px; margin: 0 6px 6px 0; }
.toggle { float: right; background: rgba(255,255,255,.16); color: #fff; border: 0; border-radius: 999px;
  padding: 6px 14px; font: inherit; font-size: 12px; cursor: pointer; }
article { background: var(--paper); border-radius: 16px; padding: 8px 32px 32px; }
article > h1:first-child { display: none; }
h2 { color: var(--purple); font-size: 22px; margin: 40px 0 12px; padding-top: 16px; border-top: 1px solid var(--line); }
h3 { font-size: 17px; margin: 28px 0 8px; }
h3::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: var(--green); margin-right: 8px; vertical-align: middle; }
a { color: var(--purple); }
code { font-family: ui-monospace, Consolas, "Roboto Mono", monospace; font-size: .88em; background: var(--code);
  padding: 1px 6px; border-radius: 6px; }
pre { background: var(--code); border-radius: 12px; padding: 14px 16px; overflow-x: auto; border: 1px solid var(--line); }
pre code { background: none; padding: 0; }
.table { overflow-x: auto; margin: 14px 0; border: 1px solid var(--line); border-radius: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th { background: var(--purple-tint); color: var(--th); text-align: left; font-weight: 700; }
th, td { padding: 8px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
td { font-variant-numeric: tabular-nums; }
blockquote { margin: 12px 0; padding: 10px 16px; background: var(--green-tint); border-left: 4px solid var(--green);
  border-radius: 0 12px 12px 0; color: var(--ink-soft); }
hr { border: 0; margin: 8px 0; }
.katex-display { overflow-x: auto; overflow-y: hidden; padding: 6px 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; margin-top: 16px; }
details.persona { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 12px 16px; }
details.persona[open] { grid-column: 1 / -1; }
details.persona summary { cursor: pointer; font-weight: 700; color: var(--purple); list-style: none; }
details.persona summary::-webkit-details-marker { display: none; }
details.persona summary::before { content: "+"; display: inline-block; width: 22px; height: 22px; line-height: 22px;
  text-align: center; border-radius: 50%; background: var(--purple-tint); margin-right: 8px; }
details.persona[open] summary::before { content: "-"; }
details.persona h2 { font-size: 15px; color: var(--ink); border-top: 0; margin: 18px 0 6px; padding-top: 0; }
details.persona p { margin: 6px 0; }
footer { color: var(--muted); font-size: 12px; margin-top: 24px; }
@media (min-width: 901px) { .toc summary { display: none; } }
@media (max-width: 900px) {
  .shell { display: block; }
  nav { position: static; height: auto; padding: 16px; }
  .sub { margin-bottom: 10px; }
  main { padding: 16px; }
  .hero { padding: 20px; }
  .hero h1 { font-size: 23px; }
  article { padding: 4px 16px 24px; }
  h2 { font-size: 19px; }
  .cards { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
</style>
</head>
<body>
<div class="shell">
<nav aria-label="Contents">
<div class="brand"><span class="dot"></span>Midterm Brain</div>
<div class="sub">IE437 · Distribution-Centre Network</div>
<details class="toc" id="toc" open><summary>Contents</summary>
{{NAV}}
</details>
</nav>
<main>
<header class="hero">
<button class="toggle" id="theme" type="button">Theme</button>
<h1>Distribution-Centre Network Redesign</h1>
<p><span class="pill">Plan v1.2</span><span class="pill">Day 0 of 14</span><span class="pill">Due Mon 2 Nov 10:00 KST</span></p>
<p>Working brain for the IE437 midterm: git-history findings, formulation, solution plan, lecture map, best practice, design system, schedule, stakeholder review and the rolling records.</p>
</header>
<article>
{{BODY}}
</article>
<footer>Private planning document, never part of the submission. Dasol Retail is fictional; the visual style is inspired by public CU brand colours.</footer>
</main>
</div>
<script>
const toc = document.getElementById("toc");
if (matchMedia("(max-width: 900px)").matches) toc.open = false;
toc.addEventListener("click", e => { if (e.target.tagName === "A" && matchMedia("(max-width: 900px)").matches) toc.open = false; });
const openCard = () => { const el = document.getElementById(location.hash.slice(1)); if (el && el.tagName === "DETAILS") el.open = true; };
addEventListener("hashchange", openCard); openCard();
document.getElementById("theme").addEventListener("click", () => {
  const r = document.documentElement;
  const dark = r.dataset.theme ? r.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  r.dataset.theme = dark ? "light" : "dark";
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
