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
