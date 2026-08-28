#!/usr/bin/env bash
# Repo-local GCC 11 + git-lfs toolchain for building Isaac Sim on Ubuntu 24.04.
#
# Isaac Sim 6.x requires GCC/G++ 11 (repo.toml pins version_check_gcc_version =
# "11.*.*"); Ubuntu 24.04 ships GCC 13. NVIDIA's README tells you to install
# gcc-11 and repoint /usr/bin/gcc with update-alternatives -- that changes the
# system default compiler for every other project on the machine.
#
# This script avoids that. It extracts the Ubuntu .deb payloads into
# <repo>/_toolchain and exposes them only via PATH. No sudo, no system change.
# <repo>/_toolchain is covered by Isaac Sim's existing `_*/` .gitignore rule.
#
# Usage:
#   ./isaacsim_toolchain.sh /path/to/IsaacSim
#   cd /path/to/IsaacSim && source _toolchain/activate.sh && ./build.sh --release --jobs 12
set -euo pipefail

REPO="${1:?usage: $0 /path/to/IsaacSim}"
REPO="$(cd "$REPO" && pwd -P)"
TC="${REPO}/_toolchain"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PKGS=(gcc-11 g++-11 gcc-11-base cpp-11 libgcc-11-dev libstdc++-11-dev libasan6 libtsan0 git-lfs)

echo "==> Downloading toolchain packages (no sudo, no install)"
( cd "$TMP" && apt-get download "${PKGS[@]}" )

echo "==> Extracting into ${TC}"
rm -rf "$TC"; mkdir -p "$TC"
for d in "$TMP"/*.deb; do dpkg-deb -x "$d" "$TC"; done

# The .debs ship symlinks (libstdc++.so, libgomp.so, ...) pointing at runtime
# libraries that live in SEPARATE system packages (libstdc++6, libgomp1, ...).
# Relative to the extracted prefix those dangle, and ld then silently falls back
# to the static .a -- which links libstdc++ statically and breaks exception
# propagation across shared objects. Repoint them at the system copies, which is
# what a normal `apt install g++-11` resolves to anyway.
echo "==> Repointing dangling symlinks at system runtime libs"
for l in $(find "$TC" -xtype l); do
    tgt="$(basename "$(readlink "$l")")"
    if [ -e "/usr/lib/x86_64-linux-gnu/${tgt}" ]; then
        ln -sfn "/usr/lib/x86_64-linux-gnu/${tgt}" "$l"
    else
        echo "    WARNING: unresolved ${l} -> ${tgt}" >&2
    fi
done

echo "==> Creating PATH shim"
mkdir -p "$TC/bin"
( cd "$TC/bin"
  for t in gcc g++ cpp gcc-ar gcc-nm gcc-ranlib gcov; do ln -sfn "../usr/bin/${t}-11" "$t"; done
  ln -sfn ../usr/bin/gcc-11 cc
  ln -sfn ../usr/bin/g++-11 c++
  ln -sfn ../usr/bin/gcc-11 gcc-11
  ln -sfn ../usr/bin/g++-11 g++-11
  ln -sfn ../usr/bin/git-lfs git-lfs )

cat > "$TC/activate.sh" <<'ACT'
#!/usr/bin/env bash
# source this to put the repo-local GCC 11 toolchain on PATH
_TC="$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )"
export PATH="${_TC}/bin:${PATH}"
export CC="${_TC}/bin/gcc"
export CXX="${_TC}/bin/g++"
unset _TC
ACT
chmod +x "$TC/activate.sh"

echo "==> Verifying"
# shellcheck disable=SC1090
( source "$TC/activate.sh"
  gcc --version | head -1
  g++ --version | head -1
  git lfs version
  # dynamic libstdc++ + exceptions across a shared-object boundary
  cd "$TMP"
  printf '#include <stdexcept>\nvoid boom(){throw std::runtime_error("x");}\n' > l.cpp
  printf '#include <stdexcept>\nvoid boom();\nint main(){try{boom();}catch(const std::exception&){return 0;}return 1;}\n' > m.cpp
  g++ -fPIC -shared l.cpp -o libl.so
  g++ m.cpp -L. -ll -Wl,-rpath,. -o t
  ./t && echo "  cross-.so exceptions: OK"
  ldd ./t | grep -q libstdc++ && echo "  libstdc++ dynamic: OK" || { echo "  ERROR: libstdc++ linked statically" >&2; exit 1; } )

echo
echo "Done. System /usr/bin/gcc is untouched ($(gcc --version | head -1))."
echo "Next:"
echo "  cd ${REPO}"
echo "  source _toolchain/activate.sh"
echo "  git lfs install --local && git lfs pull   # repo-local, not ~/.gitconfig"
echo "  ./build.sh --release --jobs 12"
