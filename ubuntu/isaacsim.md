# Isaac Sim

## inotify limits

Isaac Sim watches many files. Copy the sysctl file. Then load it:

```bash
sudo cp ~/workflow-helper/ubuntu/99-inotify.conf /etc/sysctl.d/99-inotify.conf
sudo sysctl --system
```

Make sure that the values match:

```bash
sysctl fs.inotify.max_user_watches fs.inotify.max_user_instances
```

## Delete Isaac Sim

NVIDIA docs: user config and cache can cause conflicts between versions.

```bash
# The install itself
rm -rf ~/isaacsim

# User config + cache (these can cause "internal conflicts" between versions, per NVIDIA docs)
rm -rf ~/.local/share/ov
rm -rf ~/.cache/ov
rm -rf ~/.nvidia-omniverse
rm -rf ~/Documents/Kit  # only if you don't have other Kit-based apps
```

## IsaacLab torch (CUDA 13.0)

```bash
uv pip uninstall --python env_isaaclab/bin/python torch torchvision torchaudio triton

uv pip install --python env_isaaclab/bin/python \
  torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu130

uv pip uninstall --python env_isaaclab/bin/python torch torchvision torchaudio triton
```

## Build from source on Ubuntu 24.04

Built Isaac Sim `6.0.1-rc.7` from source on this machine (i9-13980HX, RTX 4070
Laptop 8 GB, Ubuntu 24.04.4, kernel 6.17.0-14-generic).

Two things needed patching: the compiler, and the GPU driver.

### 1. GCC 11 without touching the system compiler

Isaac Sim pins GCC 11 (`repo.toml`: `version_check_gcc_version = "11.*.*"`).
Ubuntu 24.04 ships GCC 13. NVIDIA's README says to install `gcc-11` and repoint
`/usr/bin/gcc` via `update-alternatives` — that changes the default compiler for
every other project on the machine.

Instead, extract the `.deb` payloads into a repo-local prefix and expose them
only through `PATH`:

```bash
~/workflow-helper/ubuntu/isaacsim_toolchain.sh ~/IsaacSim
cd ~/IsaacSim
source _toolchain/activate.sh
```

No `sudo`, no system change. `_toolchain/` is already ignored by Isaac Sim's
existing `_*/` rule in `.gitignore`.

The build's check runs a plain `gcc --version` off `PATH`
(`_repo/deps/repo_build/omni/repo/build/dependencies.py:219`) and regex-matches
the last token, so the shim satisfies it honestly — no
`--skip-compiler-version-check` needed.

**Gotcha the script handles.** The extracted `.deb`s leave 8 dangling symlinks
(`libstdc++.so`, `libgomp.so`, `libatomic.so`, ...) pointing at runtime libraries
that ship in *separate* system packages. Relative to the extracted prefix they
dangle, and `ld` then silently falls back to the static `.a` — linking libstdc++
statically and breaking exception propagation across shared objects, which Kit
relies on everywhere. A hello-world still compiles, so this passes a naive smoke
test. The script repoints them at the system copies and verifies both dynamic
linking and a throw across an `.so` boundary.

### 2. Git LFS without touching `~/.gitconfig`

```bash
git lfs install --local   # writes .git/config, not ~/.gitconfig
git lfs pull              # 902 objects, ~600 MB
```

### 3. Build

```bash
cd ~/IsaacSim
source _toolchain/activate.sh
./build.sh --release --jobs 12
```

- `--jobs 12`, not 32. Kit's link steps spike to several GB each; a full-width
  link on 32 threads OOMs a 32 GB machine.
- **`--no-docker` does not exist** in this repo's build tool — `repo.toml`
  already sets `[repo_build.docker] enabled = false`. Passing it makes `build.sh`
  print help and build nothing while still exiting 0. The
  `.cursor/rules/build_instructions.mdc` rule is stale on this point.
- Run it detached (`setsid nohup ...`) if driving from an agent/CI harness that
  may reap background jobs.

Output: `_build/linux-x86_64/release/`, ~11 GB, 92 C++ targets.

### 4. NVIDIA driver — 535 is NOT enough

```bash
~/workflow-helper/ubuntu/isaacsim_nvidia_driver.sh
sudo reboot
```

`omni.rtx` enforces **driver >= 550.90.07** on Linux and rejects 535.288.01:

```
Reason for failure: R550 Omniverse RTX driver requirement on Linux
Installed driver: 535.288.01
The unsupported driver range: [0.00, 550.90.07)
The recommended drivers: 580.95.05
```

Result is `HydraEngine rtx failed creating scene renderer` — no viewport, no
cameras, no RTX sensors, no synthetic data generation. Physics, USD and Warp
still work headless, and `SimulationApp.close()` hangs when RTX failed to init.

**`isaac-sim.compatibility_check.sh` is wrong here.** It reports 535.288.01 as
`[supported]` against a stale `535.161` minimum. The renderer disagrees. Trust
the renderer.

**Precompiled signed modules, not DKMS.** This machine uses
`linux-modules-nvidia-*-generic-hwe-24.04`. The 580 HWE metapackage currently
resolves to `7.0.0-30.30` — modules for kernel **7.0.0-30-generic**, not the
running 6.17.0-14. Installing that alone leaves no `nvidia.ko` for the running
kernel and no GPU after reboot. Pin to the running kernel:

```bash
sudo apt-get install -y nvidia-driver-580 "linux-modules-nvidia-580-$(uname -r)"
```

The script checks that package exists and that an `nvidia.ko` is present for the
running kernel *before* telling you to reboot. Secure Boot is disabled on this
machine, so no MOK enrollment is needed.

### 5. Known hardware ceiling

`compatibility_check` reports VRAM **8.59 GB against a 10 GB minimum** — the one
item no driver fixes. Small scenes are fine; factory/warehouse-scale stages will
thrash or OOM the GPU.

Also flagged: CPU governor is `Powersave`, `Performance` recommended.

### Verifying it actually works

Headless smoke test — boots `SimulationApp`, authors a stage, drops a rigid cube
from z=2.0, steps PhysX 150 frames, asserts it rests at the expected height:

```bash
cd ~/IsaacSim/_build/linux-x86_64/release
./python.sh ~/workflow-helper/ubuntu/isaacsim_smoke.py
# expect: STAGE1..STAGE5 then  final_z=0.2500  PHYSICS_PLAUSIBLE
```

Note `isaacsim.core.api` **no longer exists** in 6.0.1 — use
`isaacsim.core.experimental.*` plus `isaacsim.core.simulation_manager`
(see `.cursor/rules/usd_prefer_experimental_api.mdc`).
