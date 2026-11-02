#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Verifies the vendored upstream glyphs match tools/icons/upstream/provenance.json.
# Refresh the vendor tree with tools/dev/vendor_upstream_icons.py --force.

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_ROOT = REPO_ROOT / "tools" / "icons" / "upstream"
MANIFEST = UPSTREAM_ROOT / "provenance.json"


def main() -> int:
    # Compare every recorded glyph hash with the file on disk.
    if not MANIFEST.is_file():
        print(f"FAIL  missing {MANIFEST}")
        return 1
    manifest = json.loads(MANIFEST.read_text())
    problems: list[str] = []
    checked = 0
    for set_name, record in sorted(manifest.get("sets", {}).items()):
        folder = UPSTREAM_ROOT / set_name
        if not folder.is_dir():
            problems.append(f"missing set directory {folder}")
            continue
        expected = record.get("icons", {})
        actual = {svg.name for svg in folder.glob("*.svg")}
        for filename, digest in sorted(expected.items()):
            path = folder / filename
            if not path.is_file():
                problems.append(f"{set_name}: missing {filename}")
                continue
            current = hashlib.sha256(path.read_text().encode("utf-8")).hexdigest()
            if current != digest:
                problems.append(f"{set_name}: changed {filename}")
            checked += 1
        for filename in sorted(actual - set(expected)):
            problems.append(f"{set_name}: unrecorded {filename}")
    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"ok: {checked} vendored upstream glyph(s) match provenance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
