"""Turn a dark-fill cursor theme into a red cursor with a black outline.

Copies every Xcursor file of the source theme (Yaru on Ubuntu 24.04: black fill,
white outline) and keeps the symlinks. Opaque pixels map from dark to red and
from light to black. Translucent pixels (shadow, outer edge) turn black. A
theme with a white fill comes out inverted: black fill, red outline.

Usage: python3 red-cursor.py /usr/share/icons/Yaru ~/.icons/Yaru-Red Yaru-Red
"""

import os
import struct
import sys

IMAGE_TYPE = 0xFFFD0002


def recolor_pixel(p):
    a = p >> 24
    r = (p >> 16) & 0xFF
    g = (p >> 8) & 0xFF
    b = p & 0xFF
    if a < 250:
        return a << 24
    # Xcursor pixels are premultiplied ARGB, so `a - lum` is red scaled by alpha.
    lum = min(a, round(0.299 * r + 0.587 * g + 0.114 * b))
    return (a << 24) | ((a - lum) << 16)


def recolor_file(src, dst):
    data = bytearray(open(src, "rb").read())
    if data[:4] == b"Xcur":
        ntoc = struct.unpack_from("<I", data, 12)[0]
        for i in range(ntoc):
            kind, _, pos = struct.unpack_from("<III", data, 16 + 12 * i)
            if kind != IMAGE_TYPE:
                continue
            w, h = struct.unpack_from("<II", data, pos + 16)
            pixels = struct.unpack_from(f"<{w * h}I", data, pos + 36)
            struct.pack_into(f"<{w * h}I", data, pos + 36, *map(recolor_pixel, pixels))
    open(dst, "wb").write(data)


def main(src_theme, dst_theme, name):
    src_dir = os.path.join(src_theme, "cursors")
    dst_dir = os.path.join(dst_theme, "cursors")
    os.makedirs(dst_dir, exist_ok=True)
    for entry in sorted(os.listdir(src_dir)):
        s, d = os.path.join(src_dir, entry), os.path.join(dst_dir, entry)
        if os.path.lexists(d):
            os.remove(d)
        if os.path.islink(s):
            os.symlink(os.readlink(s), d)
        else:
            recolor_file(s, d)
    with open(os.path.join(dst_theme, "index.theme"), "w") as f:
        f.write(f"[Icon Theme]\nName={name}\nComment=Red fill, black outline\n"
                f"Inherits={os.path.basename(os.path.normpath(src_theme))}\n")
    print(f"{name}: {len(os.listdir(dst_dir))} cursors in {dst_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__.rsplit("\n\n", 1)[-1].strip())
    main(*sys.argv[1:])
