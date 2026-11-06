# Isaac Sim

## Install Isaac Sim 6.2 and Isaac Lab 3.0 on a fresh Ubuntu

The latest releases are Isaac Sim 6.2.0 and Isaac Lab v3.0.0 (commit `e3f7d9f`,
2026-10-19). They are made to work together. Isaac Lab runs on the Python that
ships inside Isaac Sim, so you need no conda, venv or pixi for it.

Known to work: Ubuntu 26.04, RTX 5070 Ti, driver 580.178.04, with Isaac Sim
6.1.0 and an Isaac Lab 3.0 pre-release. The steps for 6.2.0 have not run end to
end on a fresh machine. Isaac Lab 3.0 needs glibc 2.35 or later, so Ubuntu
22.04 or later.

`isaacsim_install.sh` installs 6.1.0 into a plain `~/isaacsim` folder. The steps
below put each version in its own folder and point the link `~/isaacsim` at one.
To go back, point the link at the old folder.

```bash
# 0. NVIDIA driver. RTX needs 550.90.07 or later; 580 is recommended.
#    Skip this step if nvidia-smi already lists the GPU.
sudo ubuntu-drivers install            # or: sudo apt install nvidia-driver-580
sudo reboot
nvidia-smi

# 1. System tools and inotify limits (see "inotify limits" below)
sudo apt update
sudo apt install -y git git-lfs curl unzip build-essential cmake
sudo cp ~/workflow-helper/ubuntu/99-inotify.conf /etc/sysctl.d/99-inotify.conf
sudo sysctl --system

# 2. Isaac Sim 6.2.0: a 13 GB download, about 30 GB unzipped
cd ~/Downloads
curl -L -C - -O https://downloads.isaacsim.nvidia.com/isaac-sim-standalone-6.2.0-linux-x86_64.zip
unzip -tq isaac-sim-standalone-6.2.0-linux-x86_64.zip       # prints "No errors detected"
mkdir ~/isaacsim-6.2.0
unzip -q isaac-sim-standalone-6.2.0-linux-x86_64.zip -d ~/isaacsim-6.2.0
cat ~/isaacsim-6.2.0/VERSION
# If ~/isaacsim is an old install folder (not a link), rename it first:
#   mv ~/isaacsim ~/isaacsim-6.1.0
ln -sfn ~/isaacsim-6.2.0 ~/isaacsim
~/isaacsim/post_install.sh

# 2b. Ubuntu 26.04 only. 26.04 ships libxml2.so.16 only, but the FBX SDK of the
#     asset converter links libxml2.so.2, so the converter and the asset importer
#     fail to load. The .so.16 next to the FBX SDK exports every symbol it uses.
for d in ~/isaacsim/extscache/omni.kit.asset_converter-*/asset_converter_native_bindings/libs; do
  [ -e "$d/libxml2.so.2" ] || ln -s libxml2.so.16 "$d/libxml2.so.2"
done

# 3. Isaac Lab v3.0.0, linked to Isaac Sim and installed into its Python (about 10 min)
git clone --branch v3.0.0 https://github.com/isaac-sim/IsaacLab.git ~/IsaacLab
cd ~/IsaacLab
ln -sfn ~/isaacsim _isaac_sim
env -u PYTHONPATH ./isaaclab.sh -i 'rl[rsl-rl]'   # core modules plus RSL-RL; plain -i adds no extras

# 4. Check: open an empty stage in a Kit window, then close the window
env -u PYTHONPATH ./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
```

Notes:

- Run your own scripts with `env -u PYTHONPATH ~/IsaacLab/isaaclab.sh -p your_script.py`.
  Add `--viz kit` for the window; with no flag the run is headless.
- `env -u PYTHONPATH` keeps a ROS or other Python path out of Isaac Sim's Python.
- `isaaclab.sh` warns that it is deprecated in favour of `uv run isaaclab`. It
  still works in 3.0.
- The first start takes a few minutes while Kit builds its shader cache.
- Kit logs `No space left on device for creating change watches` when the
  inotify limits are too low. Step 1 sets them.
- Isaac Lab inside a repo: add it as a git submodule at the tag, and link
  `_isaac_sim` the same way.

Sources: [Isaac Sim 6.2 GA](https://forums.developer.nvidia.com/t/isaac-sim-6-2-general-availability/386512),
[Isaac Lab 3.0 installation](https://docs.nvidia.com/isaaclab/3.0/isaac-lab/installation).

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
