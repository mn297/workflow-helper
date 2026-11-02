#!/usr/bin/env python3
"""Paste a film's JSON data over the <!--DATA--> mark of its template and write the page.

    python3 build.py <template.html> <data.json> <out.html>

Refuses data that holds ``</script`` (it would end the data block), reports the page size against
the artifact limit, and runs a JavaScript syntax check with node when node is installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

LIMIT_MB = 16  # the artifact limit; data URIs count


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    template, data, out = (Path(a) for a in sys.argv[1:])
    tpl = template.read_text()
    js = data.read_text()
    if "<!--DATA-->" not in tpl:
        print(f"{template}: no <!--DATA--> mark")
        return 1
    if "</script" in js:
        print(f"{data}: holds '</script', which would end the data block")
        return 1
    page = tpl.replace("<!--DATA-->", js, 1)
    out.write_text(page)
    size = len(page.encode()) / 1e6
    print(f"{out}: {size:.2f} MB" + (f" (over the {LIMIT_MB} MB artifact limit)" if size > LIMIT_MB else ""))
    node = shutil.which("node")
    if node:
        head, _, tail = page.rpartition("<script>")
        script = tail[: tail.rfind("</script>")]
        check = subprocess.run([node, "-e", "new Function(require('fs').readFileSync(0,'utf8'))"], input=script, text=True, capture_output=True)
        print("script parses" if check.returncode == 0 else f"JS SYNTAX ERROR: {check.stderr.strip()[:400]}")
        return check.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
