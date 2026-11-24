#!/usr/bin/env python3
"""THE HARBOUR LIGHT - NI24 entry program (Akun 13).

Copies the finished front page (entry.png, rendered in this session by
compose_harbour.py) to the grader output directory. Standard library only,
no network, deterministic: the same bytes every run.
"""
import hashlib
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    with open(SRC, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit("entry.png is not a PNG file")
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (1024, 1024):
        sys.exit("entry.png must be exactly 1024x1024, got %dx%d" % (width, height))
    size = os.path.getsize(SRC)
    if size > 1048576:
        sys.exit("entry.png exceeds 1 MiB: %d bytes" % size)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dst)
    # byte-identical copy check: the grader runs this program twice and the
    # two outputs must match, so the copy must match the source exactly.
    with open(SRC, "rb") as a, open(dst, "rb") as b:
        if hashlib.sha256(a.read()).hexdigest() != hashlib.sha256(b.read()).hexdigest():
            sys.exit("copied entry.png does not match the source byte for byte")
    print("wrote %s (%d bytes, %dx%d)" % (dst, size, width, height))


if __name__ == "__main__":
    main()
