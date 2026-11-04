"""Show which processes keep each GPU's graphics engine busy, from the kernel's per-client DRM counters.

  python3 ~/workflow-helper/ubuntu/gpu_load.py [seconds]        default 3

Reads drm-engine-* from /proc/<pid>/fdinfo twice and prints each process's share of every engine over
the interval, for amdgpu, i915/xe and any other driver that exports the counters. NVIDIA's driver does
not export them, so its rows come from `nvidia-smi pmon`. A share above 100 % means the process kept
more than one hardware queue of that engine busy.
"""

import collections
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def sample() -> dict:
    out = collections.defaultdict(int)
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            fds = os.listdir(f"/proc/{pid}/fdinfo")
        except OSError:
            continue
        seen = set()
        for fd in fds:
            try:
                text = Path(f"/proc/{pid}/fdinfo/{fd}").read_text()
            except OSError:
                continue
            if "drm-driver" not in text:
                continue
            d = dict(re.findall(r"^(drm-[\w-]+):\s+(.*)$", text, re.MULTILINE))
            # Several fds can share one DRM client; count each client once.
            client = (d.get("drm-pdev"), d.get("drm-client-id"))
            if client in seen:
                continue
            seen.add(client)
            for k, v in d.items():
                if k.startswith("drm-engine-") and not k.startswith("drm-engine-capacity"):
                    out[(pid, d.get("drm-driver"), d.get("drm-pdev"), k[11:])] += int(v.split()[0])
    return out


def main() -> None:
    dt = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    a = sample()
    time.sleep(dt)
    b = sample()
    rows = []
    for key, v in b.items():
        share = 100 * (v - a.get(key, 0)) / (dt * 1e9)  # counters are ns of engine time
        if share >= 0.5:
            try:
                comm = Path(f"/proc/{key[0]}/comm").read_text().strip()
            except OSError:
                comm = "?"
            rows.append((share, key[0], comm, *key[1:]))
    print(f"{'share':>7}  {'pid':>8}  {'process':<16} {'driver':<8} {'device':<13} engine")
    for share, pid, comm, drv, dev, eng in sorted(rows, reverse=True):
        print(f"{share:6.1f}%  {pid:>8}  {comm:<16} {drv:<8} {dev:<13} {eng}")
    busy = "/sys/class/drm/card2/device/gpu_busy_percent"
    if os.path.exists(busy):
        print(f"\namdgpu gpu_busy_percent now: {Path(busy).read_text().strip()} %")
    try:
        pmon = subprocess.run(["nvidia-smi", "pmon", "-c", "1", "-s", "u"], capture_output=True, text=True, timeout=10, check=False)
        print("\nnvidia-smi pmon (sm % per process):\n" + pmon.stdout.rstrip())
    except (OSError, subprocess.TimeoutExpired):
        pass


if __name__ == "__main__":
    main()
