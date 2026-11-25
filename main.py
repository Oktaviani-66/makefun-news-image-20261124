#!/usr/bin/env python3
"""Entry program for THE LANTERN GAZETTE (news-image-20261124).

Python 3 standard library only, no network. Copies the embedded
entry.png to the output directory and checks it is a 1024x1024 PNG
of at most 1 MiB. Running it twice writes byte-identical output.
"""
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
MAX_BYTES = 1048576


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(SRC, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        raise SystemExit("entry.png exceeds 1 MiB")
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("entry.png is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1024, 1024):
        raise SystemExit("entry.png is not 1024x1024")
    dest = os.path.join(out_dir, "entry.png")
    with open(dest, "wb") as fh:
        fh.write(data)
    print("wrote", dest, len(data), "bytes")


if __name__ == "__main__":
    sys.exit(main())
