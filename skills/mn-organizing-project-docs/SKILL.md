---
name: mn-organizing-project-docs
description: >
  Project docs layout for every HTML page that you make, save, or publish for
  a project: an explainer, a report, a results or methodology page, a
  claude.ai artifact, a landing page. Also for a request for a docs folder, a
  docs site, a page to serve locally, or a tidy-up of where pages and
  artifacts live. Gives every project one docs/ layout: index.html, run.sh,
  one folder per topic.
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Docs, Artifacts, HTML, Layout, Projects"
  category: "organization"
---

# mn-organizing-project-docs

A project is any folder with its own README: a full repository, or a subfolder such as `tree_perception/experiments/<name>`. Every page about a project lives in that project's `docs/` folder, so the user can find, serve, and republish it later.

## The layout

```
<project>/docs/
  index.html        landing page: one card for each page, grouped by topic
  run.sh            serves docs/ on localhost
  assets/           CSS and JS that the pages share (optional)
  <topic>/          one folder for each topic, for example svelto/ or champ/
    <page>.html     one page
```

- A **topic folder** groups the pages about one part of the project. Use a short lowercase name.
- A page loads shared CSS and JS from `../assets/`, or keeps them inline. External scripts come only from the CDNs that the artifact contract allows, so the Artifact tool can publish the same files.
- Every page has the same top navigation bar: a link to `../index.html` and links to the other pages of its topic. All links are relative.
- Generated data, recordings and large outputs stay outside `docs/`. A page links to them or embeds a small extract.

## Steps

1. Find the project root: the nearest folder above the work that has its own README. If two folders qualify, ask the user which one owns the page.
2. If `docs/` does not exist, make `index.html` and `run.sh` from the templates below. Loose HTML pages at the project root belong in a topic folder. Propose the move, and fix the links that it breaks.
3. Load `artifact-design` and write the page to `docs/<topic>/<page>.html` under the artifact contract (title, color tokens with dark mode, CDN list, phone width). The file in `docs/` is the source of truth. Never keep the only copy in a scratchpad.
4. Add one card for the page to the `PAGES` list in `docs/index.html`: topic, title, one line on what the page shows, `href`, and the `artifact` URL of a published page.
5. To publish one page with inline CSS and JS, call the Artifact tool with its file in `docs/` as `file_path`. To publish pages that share `assets/`, publish the whole site: `docs/index.html` as `file_path`, and every other page and asset in `files`, keyed by its path inside `docs/`. Publish later updates from the same paths, so the URL stays. Open the link, and make sure that the styles and charts load. Write the URL into the `artifact` field of each card that it covers.
6. Make sure that the project README names `docs/run.sh` and `docs/index.html` in one line. Make sure that git tracks `docs/`.
7. Serve the folder with `run.sh` in the background, and read the port from the `Landing page:` line that it prints. Fetch every page and every internal link with curl, and stop the server.

Three checks end the work. Every page in `docs/` has a card in `index.html`. Every internal link returns 200. Every published page has its URL in its card.

## Template: run.sh

```bash
#!/usr/bin/env bash
# Serve this docs folder on localhost.
#   ./docs/run.sh [port]        default port 8000, or set PORT
# If the port is in use, the server takes the next free one (up to 20 tries) and prints it.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 - "${1:-${PORT:-8000}}" <<'PY'
import errno
import http.server
import sys

if not sys.argv[1].isdecimal():
    sys.exit(f"not a port number: {sys.argv[1]}")
start = int(sys.argv[1])
for port in range(start, start + 20):
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), http.server.SimpleHTTPRequestHandler)
        break
    except (OSError, OverflowError) as e:  # OverflowError: port above 65535
        if getattr(e, "errno", None) != errno.EADDRINUSE:
            sys.exit(f"port {port}: {e}")
else:
    sys.exit(f"ports {start}-{start + 19} are all in use")
if port != start:
    print(f"Port {start} is in use, using {port}.")
print(f"Landing page: http://127.0.0.1:{server.server_port}/", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
PY
```

Make it executable (`chmod +x`). If the port is in use, for example by the docs server of another project, the script takes the next free port and prints it. In the same case, `python3 -m http.server` stops with `OSError: [Errno 98] Address already in use`.

## Template: the card list in index.html

The landing page renders its cards from one inline list, so a new page is one new entry. Keep the list inline, not in a separate JSON file. An inline list also works for a page opened from disk.

```html
<script>
const PAGES = [
  // { topic: "Svelto", title: "Methodology", blurb: "How the experiments ran, with the metric math.",
  //   href: "svelto/methodology.html", artifact: "https://claude.ai/artifact/..." },
];
</script>
```

Group the cards by `topic`, in list order. For a card with an `artifact` URL, show a link to the published page. If the user plans more pages, keep a last group "More pages to come".
