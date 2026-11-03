#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Structural gate for the Xcursor packs: header/TOC/frame metadata is pure struct packing, so it
# drift-checks deterministically even though pixel bytes depend on the local Pillow build.

import argparse
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CURSORS_ROOT = REPO_ROOT / "src" / "cursors"
IMAGE_TYPE = 0xFFFD0002


def parse_frames(data: bytes, source: str) -> list[tuple[int, int, int, int, int, int]]:
    # Decode header + TOC + image chunk headers; returns (nominal, w, h, xhot, yhot, delay).
    if len(data) < 16:
        raise ValueError(f"{source}: file too short")
    magic, header_size, version, ntoc = struct.unpack_from("<4sIII", data, 0)
    if magic != b"Xcur" or header_size != 16:
        raise ValueError(f"{source}: not an Xcursor file")
    if len(data) < 16 + 12 * ntoc:
        raise ValueError(f"{source}: truncated TOC ({ntoc} entries)")
    frames: list[tuple[int, int, int, int, int, int]] = []
    end_of_last = 0
    for i in range(ntoc):
        chunk_type, nominal, offset = struct.unpack_from("<III", data, 16 + 12 * i)
        if chunk_type != IMAGE_TYPE:
            raise ValueError(f"{source}: TOC entry {i} is not an image chunk")
        if offset + 36 > len(data):
            raise ValueError(f"{source}: chunk {i} header out of bounds")
        hsize, ctype, subtype, cversion, w, h, xhot, yhot, delay = struct.unpack_from("<9I", data, offset)
        if (hsize, ctype, cversion) != (36, IMAGE_TYPE, 1):
            raise ValueError(f"{source}: chunk {i} has a malformed header")
        if subtype != nominal:
            raise ValueError(f"{source}: chunk {i} nominal/subtype mismatch")
        if w == 0 or h == 0 or xhot >= w or yhot >= h:
            raise ValueError(f"{source}: chunk {i} has impossible geometry")
        end = offset + 36 + w * h * 4
        if end > len(data):
            raise ValueError(f"{source}: chunk {i} pixel payload truncated")
        frames.append((nominal, w, h, xhot, yhot, delay))
        end_of_last = max(end_of_last, end)
    if end_of_last != len(data):
        raise ValueError(f"{source}: {len(data) - end_of_last} trailing bytes after last chunk")
    return frames


def dump_pack(pack_dir: Path) -> list[str]:
    # One canonical line per cursor file/alias so two builds diff cleanly.
    lines = []
    for path in sorted(pack_dir.rglob("*")):
        rel = path.relative_to(pack_dir.parent)
        if path.is_symlink():
            lines.append(f"{rel}: alias -> {path.readlink()}")
        elif path.is_file() and path.name != "index.theme":
            frames = parse_frames(path.read_bytes(), str(rel))
            summary = ";".join(f"{n}/{w}x{h}@({x},{y})d{delay}" for n, w, h, x, y, delay in frames)
            lines.append(f"{rel}: {summary}")
    return lines


def main() -> int:
    # Validate every committed Xcursor structurally; --dump prints the canonical form for diffs.
    parser = argparse.ArgumentParser(description="Structural gate for MT Verdant cursor packs")
    parser.add_argument("--dump", action="store_true", help="print canonical structure dump")
    args = parser.parse_args()

    packs = sorted(p for p in CURSORS_ROOT.iterdir() if p.is_dir())
    if not packs:
        print("FAIL  no cursor packs found under src/cursors", file=sys.stderr)
        return 1

    failures = 0
    for pack in packs:
        try:
            lines = dump_pack(pack)
        except ValueError as error:
            print(f"FAIL  {error}", file=sys.stderr)
            failures += 1
            continue
        if args.dump:
            for line in lines:
                print(line)
        else:
            binaries = sum(1 for line in lines if " alias -> " not in line)
            aliases = len(lines) - binaries
            print(f"ok: {pack.name}: {binaries} cursors, {aliases} aliases structurally valid")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
