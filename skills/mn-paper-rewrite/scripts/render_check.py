#!/usr/bin/env python3
"""Render a rewrite page in headless Chrome, report what a reader would see broken, and save screenshots.

    render_check.py PAGE.html [OUT_DIR]    exit 1 on an error; OUT_DIR defaults to PAGE's folder + /render
    render_check.py --self-test            run the script's own checks (needs Chrome, no network)

It loads the page at a desktop width and at a phone width and reports MathJax
errors, TeX left unrendered, a page that scrolls sideways, boxes that stick out
of the page, and diagram labels that are clipped or lie on top of each other.
It saves one screenshot of the top of the page and one per figure. A script
cannot judge a drawing, so open the screenshots it lists.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DESKTOP, PHONE = 1000, 390  # px, the two layout widths tested
TILE = 1500                 # px, the tallest screenshot; a taller image is shrunk too far to read
BUDGET = 20000              # ms of virtual time for the fonts, MathJax and the page's own scripts

# Runs inside the page. It waits for MathJax, measures, and leaves the result as JSON in pre#render-probe.
PROBE = r"""<script>(function () {
  function label(e) { return e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.classList.length ? '.' + e.classList[0] : '') + ' "' + (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40) + '"'; }
  function clipped(e) { for (e = e.parentElement; e; e = e.parentElement) { if (getComputedStyle(e).overflowX !== 'visible') return true; } return false; }
  function measure() {
    var vw = document.documentElement.clientWidth, out = { width: vw, docWidth: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight };
    out.mjx = document.querySelectorAll('mjx-container').length;
    out.mjxErr = Array.from(document.querySelectorAll('[data-mjx-error], mjx-merror')).map(function (e) { return (e.getAttribute('data-mjx-error') || e.textContent).slice(0, 120); });
    out.rawTex = [];
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) { var n = w.currentNode, p = n.parentElement; if (p && !p.closest('script,style,pre,code,mjx-container,textarea') && /\\\(|\$\$|\\\[/.test(n.nodeValue)) out.rawTex.push(n.nodeValue.trim().slice(0, 80)); }
    out.wide = [];
    document.querySelectorAll('body *').forEach(function (e) { var r = e.getBoundingClientRect(); if (r.width && r.left >= 0 && r.right > vw + 1 && !clipped(e)) out.wide.push(label(e)); });
    out.svgClipped = []; out.svgOverlap = [];
    document.querySelectorAll('svg').forEach(function (svg) {
      var box = svg.getBoundingClientRect(); if (!box.width || svg.closest('mjx-container')) return;
      var ts = Array.from(svg.querySelectorAll('text')).map(function (t) { return { t: t, r: t.getBoundingClientRect() }; }).filter(function (x) { return x.r.width; });
      ts.forEach(function (x, i) {
        if (x.r.left < box.left - 1 || x.r.right > box.right + 1 || x.r.top < box.top - 1 || x.r.bottom > box.bottom + 1) out.svgClipped.push(label(x.t));
        for (var j = i + 1; j < ts.length; j++) {
          var y = ts[j], ox = Math.min(x.r.right, y.r.right) - Math.max(x.r.left, y.r.left), oy = Math.min(x.r.bottom, y.r.bottom) - Math.max(x.r.top, y.r.top);
          if (ox > 2 && oy > 2 && ox * oy > 0.15 * Math.min(x.r.width * x.r.height, y.r.width * y.r.height)) out.svgOverlap.push(label(x.t) + ' on ' + label(y.t));
        }
      });
    });
    out.figs = Array.from(document.querySelectorAll('figure')).map(function (f, i) { var r = f.getBoundingClientRect(); return { name: f.id || (f.closest('section[id]') || {}).id || 'figure', top: Math.round(r.top + scrollY), height: Math.round(r.height) }; });
    var s = JSON.stringify(out), pre = document.createElement('pre'); pre.id = 'render-probe'; pre.textContent = s; document.body.appendChild(pre);
    if (parent !== window) parent.postMessage(s, '*');
  }
  var tries = 0, wantsMathJax = !!document.querySelector('script[src*="mathjax" i]');
  (function wait() {
    var mj = window.MathJax && MathJax.startup && MathJax.startup.promise;
    if (mj) { mj.then(function () { setTimeout(measure, 300); }, measure); }
    else if (!wantsMathJax || ++tries > 60) { setTimeout(measure, 300); }
    else { setTimeout(wait, 200); }
  })();
})();</script>"""

# The phone layout: the page sits in a 390 px frame, so its media queries see a phone.
FRAME = """<!doctype html><meta charset="utf-8"><body style="margin:0;background:#888">
<iframe style="width:{w}px;height:{h}px;border:0;display:block" srcdoc="{doc}"></iframe>
<script>addEventListener('message', function (e) {{ var p = document.createElement('pre'); p.id = 'render-probe'; p.textContent = e.data; document.body.appendChild(p); }});</script>"""


def find_chrome() -> str | None:
    """Return the first Chrome or Chromium on the path."""
    return next((p for p in map(shutil.which, ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")) if p), None)


def chrome(binary: str, profile: Path, *args: str) -> str:
    """Run one headless Chrome command and return what it printed."""
    cmd = [binary, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
           f"--virtual-time-budget={BUDGET}", *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout


def inject(page: str, extra: str) -> str:
    """Return the page's source with extra markup placed at the end of its body."""
    at = page.rfind("</body>")
    return page + extra if at < 0 else page[:at] + extra + page[at:]


def framed(page: str, height: int) -> str:
    """Return a wrapper document that shows the page in a frame of phone width."""
    return FRAME.format(w=PHONE, h=height, doc=html.escape(page, quote=True))


def probe(binary: str, profile: Path, work: Path, page: str, width: int) -> dict:
    """Load the page at one width and return what the probe measured."""
    doc = inject(page, PROBE)
    f = work / f"probe-{width}.html"
    f.write_text(framed(doc, 3000) if width == PHONE else doc, encoding="utf-8")
    dom = chrome(binary, profile, f"--window-size={max(width, 500)},1400", "--dump-dom", f.as_uri())
    found = re.findall(r'<pre id="render-probe">(.*?)</pre>', dom, re.S)
    if not found:
        sys.exit(f"render_check: the probe did not report at {width} px; is the page's script broken?")
    return json.loads(html.unescape(found[-1]))


def shot(binary: str, profile: Path, work: Path, page: str, out: Path, top: int, height: int, width: int) -> None:
    """Save a screenshot of the page from `top` px down, `height` px tall."""
    doc = inject(page, f"<style>body{{margin-top:-{top}px !important}}</style>")
    f = work / "shot.html"
    f.write_text(framed(doc, height) if width == PHONE else doc, encoding="utf-8")
    chrome(binary, profile, f"--window-size={max(width, 500)},{height}", f"--screenshot={out}", f.as_uri())


def check(page: str, out_dir: Path | None) -> tuple[list[str], list[str], list[Path]]:
    """Return the errors, the warnings and the screenshots of one page's source."""
    binary = find_chrome()
    if binary is None:
        sys.exit("render_check: no Chrome or Chromium found; open the page in a browser and look at it yourself")
    err: list[str] = []
    warn: list[str] = []
    shots: list[Path] = []
    desktop: dict = {}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        work, profile = Path(tmp), Path(tmp) / "profile"
        for width in (DESKTOP, PHONE):
            r = probe(binary, profile, work, page, width)
            at = f"at {width} px"
            err += [f"{at}: MathJax error: {e}" for e in r["mjxErr"]]
            err += [f"{at}: TeX left unrendered: {t!r}" for t in r["rawTex"][:5]]
            if r["docWidth"] > r["width"] + 1:
                err.append(f"{at}: the page scrolls sideways ({r['docWidth']} px of content in {r['width']} px)")
            err += [f"{at}: a diagram label is clipped: {t}" for t in r["svgClipped"][:8]]
            warn += [f"{at}: sticks out of the page: {t}" for t in r["wide"][:8]]
            warn += [f"{at}: diagram labels overlap: {t}" for t in r["svgOverlap"][:8]]
            if width == DESKTOP:
                if "mathjax" in page.lower() and not r["mjx"]:
                    err.append("MathJax rendered nothing; did its script load?")
                desktop = r
            elif out_dir is not None and r["figs"]:
                f = r["figs"][0]
                shots.append(out_dir / f"phone-{f['name']}.png")
                shot(binary, profile, work, page, shots[-1], max(f["top"] - 20, 0), min(f["height"] + 40, TILE), PHONE)
        if out_dir is not None:
            shots.insert(0, out_dir / "top.png")
            shot(binary, profile, work, page, shots[0], 0, TILE, DESKTOP)
            for n, f in enumerate(desktop["figs"], 1):
                shots.append(out_dir / f"fig{n}-{f['name']}.png")
                shot(binary, profile, work, page, shots[-1], max(f["top"] - 20, 0), min(f["height"] + 40, TILE), DESKTOP)
    return err, warn, shots


def self_test() -> None:
    good = """<!doctype html><meta name="viewport" content="width=device-width"><body style="margin:0">
<figure id="system"><svg viewBox="0 0 300 100" style="width:100%"><text x="10" y="20">in</text><text x="10" y="60">out</text></svg></figure>
<p>plain text</p></body>"""
    err, warn, _ = check(good, None)
    assert not err and not warn, (err, warn)
    broken = {
        "scrolls sideways": good.replace("<p>", '<div style="width:1500px">wide</div><p>'),
        "label is clipped": good.replace('x="10" y="20">in', 'x="290" y="20">a long label that leaves the box'),
        "TeX left unrendered": good.replace("plain text", "the angle \\\\(\\\\theta\\\\)".replace("\\\\", "\\")),
    }
    for want, text in broken.items():
        assert any(want in e for e in check(text, None)[0]), (want, check(text, None))
    overlap = good.replace('x="10" y="60">out', 'x="10" y="20">out')
    assert any("overlap" in w for w in check(overlap, None)[1]), check(overlap, None)
    print("self-test passed")


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    if sys.argv[1] == "--self-test":
        self_test()
        return 0
    path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else path.parent / "render"
    err, warn, shots = check(path.read_text(encoding="utf-8"), out_dir)
    for e in err:
        print("ERROR", e)
    for w in warn:
        print("WARN ", w)
    print("OK   " if not err else "FAIL ", f"{len(shots)} screenshots to look at:")
    for s in shots:
        print("  ", s)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
