"""Unclog a slow desktop: reap orphan headless browsers, then free the busiest iGPU clients.

  python3 ~/workflow-helper/ubuntu/gpu_clean.py [seconds]      default 3, the iGPU sample length

Both monitors hang off the iGPU, so one client that keeps its gfx queue full stalls every
window. An orphan is a headless Chrome or Chromium whose driver script died, so the user's
systemd adopted it; one prompt kills them all. Then each iGPU client at OFFER or more gets
a y/N prompt: a Chromium or Electron GPU process is restarted (the browser process launches a
new one and the windows redraw), a media player is closed. Xwayland and gnome-shell cannot be
restarted here, so for them the script names the apps that drive their load.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from gpu_load import sample

OFFER = 10.0  # % of the iGPU gfx engine; restarting a client below this frees little
BROWSERS = {"chrome", "chromium", "chromium-browser", "headless_shell"}
PLAYERS = {"vlc", "spotify", "totem", "mpv", "celluloid"}


def procs() -> dict:
    out = {}
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            if os.stat(f"/proc/{pid}").st_uid != os.getuid():
                continue
            args = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").split("\0")
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            continue
        args = [a for a in args if a]
        # Chromium and Electron rewrite their process title into one space-joined string.
        if len(args) == 1:
            args = args[0].split()
        # The comm field in stat may hold spaces, so split after its closing bracket.
        out[int(pid)] = (args, int(stat.rsplit(")", 1)[1].split()[1]))
    return out


def orphans(ps: dict) -> list:
    systemd = {p for p, (a, _) in ps.items() if a and a[0].endswith("systemd") and "--user" in a}
    found = []
    for pid, (args, ppid) in ps.items():
        name = Path(args[0]).name if args else ""
        if (name in BROWSERS and ppid in systemd
                and not any(a.startswith("--type=") for a in args)
                and (name == "headless_shell" or any(a.startswith("--headless") for a in args))):
            found.append(pid)
    return found


def pss_kb(pid: int) -> int:
    # PSS splits each shared page across the processes that map it, so a sum is not inflated.
    try:
        text = Path(f"/proc/{pid}/smaps_rollup").read_text()
    except OSError:
        return 0
    return next((int(x.split()[1]) for x in text.splitlines() if x.startswith("Pss:")), 0)


def tree_gib(ps: dict, roots: list) -> float:
    tree, grown = set(roots), True
    while grown:
        kids = {p for p, (_, pp) in ps.items() if pp in tree} - tree
        tree |= kids
        grown = bool(kids)
    return sum(map(pss_kb, tree)) / 2**20


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def stop(pids: list) -> None:
    for p in pids:
        if alive(p):
            os.kill(p, signal.SIGTERM)
    deadline = time.monotonic() + 3
    while any(map(alive, pids)) and time.monotonic() < deadline:
        time.sleep(0.1)
    for p in filter(alive, pids):
        os.kill(p, signal.SIGKILL)


def ask(question: str, default: bool = False) -> bool:
    if not sys.stdin.isatty():
        print(f"{question} skipped: no terminal to answer")
        return False
    try:
        reply = input(f"{question} [{'Y/n' if default else 'y/N'}] ").strip().lower()
    except EOFError:
        return False
    return reply.startswith("y") if reply else default


def igpu(dt: float) -> list:
    a = sample()
    time.sleep(dt)
    b = sample()
    share = {}
    for key, v in b.items():
        pid, drv, _, eng = key
        if drv == "amdgpu" and eng == "gfx":
            share[int(pid)] = share.get(int(pid), 0) + 100 * (v - a.get(key, 0)) / (dt * 1e9)
    return sorted(((s, p) for p, s in share.items() if s >= 0.5), reverse=True)


def show(rows: list, ps: dict) -> None:
    for s, pid in rows:
        args = ps.get(pid, ([],))[0]
        print(f"  {s:6.1f}%  {pid:>8}  {Path(args[0]).name if args else '?'}")


def available() -> float:
    line = next(x for x in Path("/proc/meminfo").read_text().splitlines()
                if x.startswith("MemAvailable"))
    return int(line.split()[1]) / 2**20


def main() -> None:
    dt = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    ram0 = available()
    ps = procs()

    dead = orphans(ps)
    if dead:
        print(f"{len(dead)} orphan headless browsers, about {tree_gib(ps, dead):.1f} GiB:")
        for p in dead:
            print(f"  {p:>8}  {next((a for a in ps[p][0] if 'user-data-dir' in a), ps[p][0][0])}")
        if ask("Kill them?", default=True):
            stop(dead)
    else:
        print("No orphan headless browsers.")

    print(f"\niGPU gfx share over {dt:g} s:")
    rows = igpu(dt)
    show(rows, ps)
    acted = []
    for s, pid in rows:
        if s < OFFER or pid not in ps:
            continue
        args = ps[pid][0]
        name = Path(args[0]).name
        if "--type=gpu-process" in args:
            if ask(f"Restart {name}'s GPU process ({s:.0f} %)? Its windows flash and redraw."):
                acted.append(pid)
        elif name in PLAYERS:
            if ask(f"Close {name} ({s:.0f} %)?"):
                acted.append(pid)
        elif name == "Xwayland":
            x11 = subprocess.run(["xlsclients"], capture_output=True, text=True, check=False)
            apps = sorted({w[1] for w in map(str.split, x11.stdout.splitlines()) if len(w) > 1})
            print(f"Xwayland ({s:.0f} %) copies every frame of these X11 apps; pause the one"
                  f" that animates (WebGL tab, video, Rerun viewer): {', '.join(apps)}")
        elif name == "gnome-shell":
            print(f"gnome-shell ({s:.0f} %) composites every window; it drops once the others stop.")

    if acted:
        stop(acted)
        time.sleep(2)
        print(f"\niGPU gfx share after, over {dt:g} s:")
        show(igpu(dt), procs())
    print(f"\nRAM available: {ram0:.1f} GiB before, {available():.1f} GiB after")


if __name__ == "__main__":
    main()
