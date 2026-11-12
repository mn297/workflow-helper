#!/usr/bin/env python3
"""Check a paper-rewrite page for the rules of mn-paper-rewrite that a script can test.

    check_page.py PAGE.html      exit 1 on an error; a warning does not fail
    check_page.py --self-test    run the script's own checks

It tests structure, not truth: that every equation has a legend, that every
quantity a stage reads is accounted for, that the coverage links resolve, that
a derivation step, a glue fact and a row of numbers each carry a source mark,
and that a check a mark names exists in the checks file next to the page.
"""
from __future__ import annotations

import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

SECTIONS = ["breath", "system", "example", "stages", "objective", "evidence", "gaps", "rebuild",
            "restate", "ledger", "coverage", "open"]
KINDS = {"input", "given", "hyper", "learned", "solved", "derived", "output"}
READ_FREE = {"input", "given", "hyper", "learned"}  # a stage may read these though no earlier stage makes them
MADE = {"derived", "solved", "output", "learned"}   # the kinds a stage may make
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
RAW_MATH = re.compile(r"[Ͱ-Ͽ⁰-₟∀-⋿]")  # Greek, sub/superscripts, operators
MATHJAX = re.compile(r"\\\(.*?\\\)", re.S)
NUMBER_TABLES = {"example", "evidence", "rebuild"}  # sections whose table rows each state a number
CHECK_NAME = re.compile(r"([\w./-]+\.py)::(\w+)")  # "checks.py::jacobian" in a mine-checked mark


class Page(HTMLParser):
    """Collect what the checks need from one page: ids, links, equations, tables and marks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = [{"tag": "#root", "cls": set(), "pending_eq": None, "marks": 0}]
        self.ids: list[str] = []
        self.hrefs: list[tuple[str, int]] = []
        self.equations = 0
        self.no_legend: list[int] = []
        self.contracts: list[dict] = []
        self.ledger: list[tuple[str, str, int]] = []
        self.stages: list[dict] = []
        self.coverage: list[dict] = []
        self.has_coverage = False
        self.raw_math: list[int] = []
        self.marks = {"paper": 0, "code": 0, "mine checked": 0, "mine unchecked": 0}
        self.unmarked: list[tuple[str, int]] = []  # (what, line) of a block that must say where it comes from
        self.mark_kind = ""
        self.check_names: list[tuple[str, str, int]] = []  # (file, function, line) named by a mine-checked mark

    def _open(self, tag: str, cls: str | None = None) -> dict | None:
        for el in reversed(self.stack):
            if el["tag"] == tag and (cls is None or cls in el["cls"]):
                return el
        return None

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {k: v or "" for k, v in attrs}
        cls = set(a.get("class", "").split())
        line = self.getpos()[0]
        parent = self.stack[-1]
        if parent["pending_eq"] is not None:  # This element comes right after an equation box.
            if not (tag == "dl" and "vars" in cls):
                self.no_legend.append(parent["pending_eq"])
            parent["pending_eq"] = None
        if "id" in a:
            self.ids.append(a["id"])
        row = self._open("tr")
        if tag == "a" and a.get("href", "").startswith("#"):
            self.hrefs.append((a["href"][1:], line))
            if row is not None and self._open("table", "coverage") is not None:
                row["placed"] = True
        stage = self._open("section", "stage")
        if tag == "section" and "stage" in cls:
            self.stages.append({"id": a.get("id", f"line {line}"), "contracts": [], "marks": 0})
        if tag == "table" and "contract" in cls:
            self.contracts.append({"line": line, "rows": []})
            if stage is not None:
                stage["stage"]["contracts"].append(self.contracts[-1])
        if tag == "table" and "coverage" in cls:
            self.has_coverage = True
        if tag == "tr":
            if self._open("table", "contract") is not None and "data-io" in a and "data-q" in a:
                self.contracts[-1]["rows"].append((a["data-io"], a["data-q"], line))
            if self._open("table", "ledger") is not None and "data-q" in a:
                self.ledger.append((a["data-q"], a.get("data-kind", ""), line))
        if tag == "td" and "skip" in cls and row is not None:
            row["placed"] = True
        if "src" in cls and self._open("header") is None:  # The header's marks are the legend's samples.
            kind = ("paper" if "p" in cls else "code" if "c" in cls
                    else "mine checked" if "ok" in cls else "mine unchecked")
            self.marks[kind] += 1
            if stage is not None:
                stage["stage"]["marks"] += 1
            for el in self.stack:
                el["marks"] += 1
            self.mark_kind = kind
        if tag in VOID:
            return
        el = {"tag": tag, "cls": cls, "pending_eq": None, "line": line, "placed": False, "cells": 0, "marks": 0,
              "id": a.get("id", "")}
        if tag == "section" and "stage" in cls:
            el["stage"] = self.stages[-1]
        if tag == "td" and row is not None:
            row["cells"] += 1
        self.stack.append(el)

    def handle_endtag(self, tag: str) -> None:
        at = next((i for i in range(len(self.stack) - 1, 0, -1) if self.stack[i]["tag"] == tag), None)
        if at is None:
            return
        closed = self.stack[at]
        while len(self.stack) > at:
            el = self.stack.pop()
            if el["pending_eq"] is not None:  # An equation box was this element's last child.
                self.no_legend.append(el["pending_eq"])
            if el["tag"] == "tr" and el["cells"] and self._open("table", "coverage") is not None:
                self.coverage.append(el)
            if not el["marks"]:
                top = next((e["id"] for e in self.stack if e["tag"] == "section" and e["id"] in NUMBER_TABLES), "")
                if el["tag"] == "li" and self._open("ol", "steps") is not None:
                    self.unmarked.append(("derivation step", el["line"]))
                elif el["tag"] == "p" and "glue" in el["cls"]:
                    self.unmarked.append(("glue fact", el["line"]))
                elif el["tag"] == "tr" and el["cells"] and top:
                    self.unmarked.append((f"row of #{top}", el["line"]))
        if tag == "div" and "eq" in closed["cls"] and "s" not in closed["cls"]:
            self.equations += 1
            self.stack[-1]["pending_eq"] = closed["line"]

    def handle_data(self, data: str) -> None:
        if self.mark_kind == "mine checked" and "src" in self.stack[-1]["cls"]:
            self.check_names += [(f, fn, self.getpos()[0]) for f, fn in CHECK_NAME.findall(data)]
        if self.stack[-1]["tag"] == "dt" and self._open("dl", "vars") is not None:
            if RAW_MATH.search(MATHJAX.sub("", data)):
                self.raw_math.append(self.getpos()[0])


def check(text: str, folder: Path | None = None) -> tuple[list[str], list[str], str]:
    """Return the errors, the warnings and a one-line summary of a page's source.

    With the page's folder, also test that each check a mark names is a function of the checks file there.
    """
    p = Page()
    p.feed(text)
    p.close()
    err: list[str] = []
    warn: list[str] = []

    missing = [s for s in SECTIONS if s not in p.ids]
    err += [f"section #{s} is missing" for s in missing]
    order = [p.ids.index(s) for s in SECTIONS if s in p.ids]
    if order != sorted(order):
        err.append("the sections are out of order; want " + ", ".join(SECTIONS))
    for n, line in enumerate(text.splitlines(), 1):
        if "⟦" in line or "⟧" in line:
            err.append(f"line {n}: a template placeholder is left")
        if re.search(r"\b(TODO|TBD)\b|lorem ipsum", line):
            err.append(f"line {n}: unfinished text")
    err += [f"line {n}: the equation box has no legend (dl.vars) right after it" for n in p.no_legend]
    warn += [f"line {n}: a legend symbol is typed as raw math; write it as \\(...\\)" for n in p.raw_math]

    if not p.stages:
        err.append("no stage chapter (section.stage)")
    for st in p.stages:
        ios = {io for c in st["contracts"] for io, _, _ in c["rows"]}
        if not {"in", "out"} <= ios:
            err.append(f"{st['id']}: the stage needs a contract table with an in row and an out row")
        if not st["marks"]:
            warn.append(f"{st['id']}: no source mark")

    kinds: dict[str, str] = {}
    for q, kind, line in p.ledger:
        if kind not in KINDS:
            err.append(f"line {line}: ledger kind {kind!r} of {q!r} is not one of {sorted(KINDS)}")
        kinds[q] = kind
    made: set[str] = set()
    used: set[str] = set()
    for c in p.contracts:
        outs = {q for io, q, _ in c["rows"] if io == "out"}
        for io, q, line in c["rows"]:
            used.add(q)
            if q not in kinds:
                err.append(f"line {line}: {q!r} is not in the ledger")
            elif io == "out" and kinds[q] not in MADE:
                err.append(f"line {line}: a stage makes {q!r}, but the ledger calls it {kinds[q]}")
            elif io != "out" and kinds[q] not in READ_FREE and q not in made and not (io == "state" and q in outs):
                err.append(f"line {line}: {q!r} is read here, but no earlier stage makes it")
        made |= outs
    for q, kind in kinds.items():
        if kind in ("derived", "solved", "output") and q not in made:
            err.append(f"ledger: no stage makes {q!r} ({kind})")
        if q not in used:
            warn.append(f"ledger: no stage contract names {q!r}")

    err += [f"line {line}: the link #{t} has no target" for t, line in p.hrefs if t not in p.ids]
    if not p.has_coverage or not p.coverage:
        err.append("no coverage table (table.coverage) with rows")
    err += [f"line {r['line']}: the coverage row has no link and no td.skip" for r in p.coverage if not r["placed"]]

    for what in sorted({w for w, _ in p.unmarked}):
        lines = [line for w, line in p.unmarked if w == what]
        warn.append(f"{len(lines)} x {what} with no mark; lines {', '.join(map(str, lines[:12]))}"
                    + (" ..." if len(lines) > 12 else ""))
    for name, fn, line in p.check_names if folder is not None else []:
        f = folder / name
        if not f.exists():
            warn.append(f"line {line}: the mark names {name}, which is not next to the page")
        elif not re.search(rf"^def {fn}\b", f.read_text(encoding="utf-8"), re.M):
            err.append(f"line {line}: the mark names {name}::{fn}, but {name} has no function {fn}")

    marks = ", ".join(f"{k} {v}" for k, v in p.marks.items())
    return err, warn, f"{len(p.stages)} stages, {p.equations} equations with a legend rule, marks: {marks}"


def self_test() -> None:
    good = """<section id="breath"></section><section id="system"></section><section id="example"></section>
<section id="stages"><section class="stage" id="stage-1">
<table class="contract"><tr data-io="in" data-q="frames"><td>frames</td></tr>
<tr data-io="param" data-q="lam"><td>lam</td></tr><tr data-io="out" data-q="poses"><td>poses</td></tr></table>
<div class="eq" id="eq-1">$$a$$</div>
<dl class="vars"><dt>\\(\\theta\\)</dt><dd>turn</dd></dl><p><span class="src p">Eq. 1</span></p>
<details><ol class="steps"><li><div class="eq s">$$b_{c_{d}}$$</div><p>chain rule <span class="src m ok">mine, checked: checks.py::step</span></p></li></ol></details>
</section></section>
<section id="objective"></section><section id="evidence"></section><section id="gaps"></section>
<section id="rebuild"></section><section id="restate"></section>
<section id="ledger"><table class="ledger"><tr data-q="frames" data-kind="input"><td>f</td></tr>
<tr data-q="lam" data-kind="hyper"><td>l</td></tr><tr data-q="poses" data-kind="output"><td>p</td></tr></table></section>
<section id="coverage"><table class="coverage"><tr><th>Paper</th><th>Here</th></tr>
<tr><td>Eq. (1)</td><td><a href="#eq-1">stage 1</a></td></tr>
<tr><td>Fig. 2</td><td class="skip">skipped: a photo of the rig</td></tr></table></section>
<section id="open"></section>"""
    err, warn, _ = check(good)
    assert not err and not warn, (err, warn)
    broken = {
        "legend": good.replace('<dl class="vars"><dt>\\(\\theta\\)</dt><dd>turn</dd></dl>', ""),
        "not in the ledger": good.replace('<tr data-q="lam" data-kind="hyper"><td>l</td></tr>', ""),
        "no earlier stage": good.replace('data-q="frames" data-kind="input"', 'data-q="frames" data-kind="derived"'),
        "no target": good.replace('href="#eq-1"', 'href="#eq-9"'),
        "no link": good.replace(' class="skip"', ""),
        "is missing": good.replace('<section id="gaps"></section>', ""),
        "placeholder": good.replace("turn", "⟦meaning⟧"),
    }
    for want, text in broken.items():
        assert any(want in e for e in check(text)[0]), (want, check(text)[0])
    assert any("raw math" in w for w in check(good.replace("\\(\\theta\\)", "θ"))[1])
    assert any("derivation step" in w for w in check(good.replace('<span class="src m ok">mine, checked: checks.py::step</span>', ""))[1])
    header = '<header><span class="src m">mine, unchecked</span></header>'
    assert "mine unchecked 0" in check(header + good)[2], check(header + good)[2]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "checks.py").write_text("def other():\n    pass\n", encoding="utf-8")
        assert any("no function step" in e for e in check(good, Path(tmp))[0])
        (Path(tmp) / "checks.py").write_text("def step():\n    pass\n", encoding="utf-8")
        assert not check(good, Path(tmp))[0]
    print("self-test passed")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--self-test":
        self_test()
        return 0
    page = Path(sys.argv[1])
    err, warn, summary = check(page.read_text(encoding="utf-8"), page.parent)
    for e in err:
        print("ERROR", e)
    for w in warn:
        print("WARN ", w)
    print("OK   " if not err else "FAIL ", summary)
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
