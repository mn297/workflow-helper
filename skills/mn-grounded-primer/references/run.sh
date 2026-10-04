#!/usr/bin/env bash
# Rebuild the reader, then serve it on http://127.0.0.1 and print its URL.
# Over http the browser keeps one zoom level for every lesson and the instruments.
# Opened as a file (file://), Chrome keeps a separate zoom for each lesson URL.
# Usage: <folder>/run.sh [--open] [port]    port defaults to $PORT or 8765
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"  # serve the workspace, so lesson links to ../src and ../docs resolve
NAME="$(basename "$HERE")"
open=0
port="${PORT:-8765}"
for arg in "$@"; do
  case "$arg" in
    --open) open=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    ''|*[!0-9]*) echo "run.sh: unknown option '$arg'. Use --open, a port number or --help." >&2; exit 2 ;;
    *) port="$arg" ;;
  esac
done

url="http://127.0.0.1:$port/$NAME/index.html"
probe="import socket, sys; s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('127.0.0.1', int(sys.argv[1])))"
if ! python3 -c "$probe" "$port" 2>/dev/null; then
  echo "run.sh: port $port is in use. If run.sh already runs, open $url. Otherwise pass another port." >&2
  exit 1
fi

python3 "$HERE/viz/build_reader.py"
echo "Reader: $url"
echo "Serving $ROOT on 127.0.0.1 only. Stop with Ctrl+C."
if [ "$open" = 1 ]; then (sleep 1; xdg-open "$url" >/dev/null 2>&1 || open "$url") & fi
# http.server sends text files without a charset, and the browser then misreads UTF-8.
exec python3 - "$port" "$ROOT" <<'PY'
import functools, http.server, sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        kind = super().guess_type(path)
        if kind.startswith("text/x-") or path.endswith((".md", ".sh", ".toml", ".yaml", ".yml")):
            kind = "text/plain"
        return kind + "; charset=utf-8" if kind.startswith("text/") else kind

port, root = int(sys.argv[1]), sys.argv[2]
http.server.ThreadingHTTPServer.allow_reuse_address = True
server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=root))
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
PY
