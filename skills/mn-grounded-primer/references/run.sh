#!/usr/bin/env bash
# Rebuild the simple scripts and the reader, then serve it on http://127.0.0.1 and print its URL.
# Over http the browser keeps one zoom level for every lesson and the instruments.
# Opened as a file (file://), Chrome keeps a separate zoom for each lesson URL.
# Usage: <folder>/run.sh [--open] [port]    port defaults to $PORT or 8765
# If the port is in use, the server takes the next free one (up to 20 tries) and prints it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"  # serve the workspace, so lesson links to ../src and ../docs resolve
NAME="$(basename "$HERE")"
open=0
port="${PORT:-8765}"
for arg in "$@"; do
  case "$arg" in
    --open) open=1 ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    ''|*[!0-9]*) echo "run.sh: unknown option '$arg'. Use --open, a port number or --help." >&2; exit 2 ;;
    *) port="$arg" ;;
  esac
done
case "$port" in *[!0-9]*) echo "run.sh: PORT='$port' is not a port number." >&2; exit 2 ;; esac

# The simple scripts first, because the reader embeds them.
if [ -f "$HERE/code-simple/build_simple.py" ]; then python3 "$HERE/code-simple/build_simple.py"; fi
python3 "$HERE/viz/build_reader.py"

# http.server sends text files without a charset, and the browser then misreads UTF-8.
exec python3 - "$port" "$ROOT" "$NAME" "$open" <<'PY'
import errno, functools, http.server, subprocess, sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        kind = super().guess_type(path)
        if kind.startswith("text/x-") or path.endswith((".md", ".sh", ".toml", ".yaml", ".yml")):
            kind = "text/plain"
        return kind + "; charset=utf-8" if kind.startswith("text/") else kind

start, root, name = int(sys.argv[1]), sys.argv[2], sys.argv[3]
http.server.ThreadingHTTPServer.allow_reuse_address = True
# If the port is in use, take the next free one (up to 20 tries). The server binds the port
# itself: a separate probe left a gap in which a second run.sh took the same port.
for port in range(start, start + 20):
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=root))
        break
    except (OSError, OverflowError) as e:  # OverflowError: port above 65535
        if getattr(e, "errno", None) != errno.EADDRINUSE:
            sys.exit(f"run.sh: port {port}: {e}")
else:
    sys.exit(f"run.sh: ports {start}-{start + 19} are all in use.")
if port != start:
    print(f"Port {start} is in use, using {port}.")
url = f"http://127.0.0.1:{server.server_port}/{name}/index.html"
print(f"Reader: {url}")
print(f"Serving {root} on 127.0.0.1 only. Stop with Ctrl+C.", flush=True)
if sys.argv[4] == "1":  # the socket listens already, so the browser request waits for serve_forever
    subprocess.Popen(["sh", "-c", 'xdg-open "$1" >/dev/null 2>&1 || open "$1"', "sh", url])
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
PY
