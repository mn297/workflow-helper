# Out-of-memory kills that end the GNOME session

Run the fix once:

```bash
~/workflow-helper/ubuntu/oom_fix.sh
```

Then start heavy jobs under a RAM cap:

```bash
memcap 40G pixi run trials --workers 16
memcap 50% python train.py      # percent of physical RAM
```

## Symptom

The desktop closes and the login screen opens. The PC does not reboot: `uptime` still counts days. The kernel log shows an out-of-memory (OOM) kill a few seconds before:

```text
kernel: Out of memory: Killed process 1039613 (cursor) total-vm:1520879056kB, anon-rss:620076kB ...
systemd[13100]: org.gnome.Shell@ubuntu.service: Failed with result 'oom-kill'.
```

## Cause

Two things combine.

1. **A job fills RAM.** The machine has 89.7 GiB usable RAM, 8 GB swap file and 4 GB zram. At the 11:11 kill, 20 trial workers held 52 GB (2.5 to 2.7 GB each) and Cursor held 15 GB. Kernel memory was small: slab 4 GB, page cache under 1 GB. So no kernel leak: processes used the RAM.
2. **The kill takes the desktop with it.** The OOM killer picks the process with the highest score. Cursor and Chrome run at `oom_score_adj` 300, so they go first. GNOME Shell runs at -1000, so the kernel never picks it. But the kernel can pick an app that runs inside the shell's cgroup (the group of processes systemd tracks as one unit). systemd's default `OOMPolicy=stop` then stops the whole shell unit, and the unit's `OnFailure=` ends the session.

systemd-oomd does not act first. It watches only memory pressure on `user@1000.service`, at 50 % for 20 s. RAM filled in about 78 s, and the kernel acted before oomd.

## Fix

[`oom_fix.sh`](oom_fix.sh) does two things:

| Step | Effect |
|---|---|
| Writes `~/.config/systemd/user/org.gnome.Shell@.service.d/oom.conf` with `OOMPolicy=continue` | An OOM kill inside the shell's cgroup ends only that app. The shell keeps running. |
| Links [`memcap`](memcap) into `~/.local/bin` | `memcap SIZE CMD` runs `CMD` in its own cgroup with a RAM cap. |

`memcap` sets three things on the job:

| Setting | Why |
|---|---|
| `MemoryMax=SIZE` | The kernel kills inside the job at the cap, not across the whole machine. |
| `MemorySwapMax=0` | The job dies at the cap instead of pushing the desktop into swap. |
| `OOMPolicy=kill` | One kill ends every process of the job. A `multiprocessing.Pool` that loses one worker otherwise waits forever. |

Exit code 137 means the cap killed the job. Tested: a 4-worker pool at 200 MB each under `memcap 300M` dies in under 1 s with exit 137, and under `memcap 2G` it finishes with exit 0.

## Check

```bash
systemctl --user show org.gnome.Shell@ubuntu.service -p OOMPolicy    # OOMPolicy=continue
journalctl -k | grep -E "invoked oom-killer|Out of memory: Killed"
```

Sum resident memory per process name at the last machine-wide OOM kill. `memcap` kills also print a dump, and the `global_oom` filter skips them.

```bash
journalctl -k -o cat | awk '/invoked oom-killer/{buf=""} /^\[ *[0-9]+\]/{buf=buf"\n"$0} /oom-kill:constraint/ && /global_oom/{last=buf} END{print last}' |
  sed -E 's/^\[ *[0-9]+\] +//' | awk 'NF>8{r[$NF]+=$4} END{for(k in r) printf "%6.1f GB %s\n", r[k]*4/1048576, k}' | sort -rn | head
```

## Not fixed here

- **Job size.** Cap the job with `memcap`, or lower its worker count. In `b2_ws/sim/brick_stack`, each trial worker keeps up to 8 compiled scenes of 130 MB each, held by `lru_cache(maxsize=8)` on `_kin` and `_scratch`.
- **Cursor.** It held 28 GB with 11 windows open. Each window runs two Pyright servers: Cursor Pyright (heap cap 32 GB) and `ms-pyright` (heap cap 3 GB). Disable Cursor Pyright in the Extensions panel.
- **oomd tuning and earlyoom.** Both would pick Cursor first too, because of its higher score. Not set up.
