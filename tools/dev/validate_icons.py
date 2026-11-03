#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Validates the generated packs (dark and light): index.theme coverage, presence, non-empty contexts.

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ICONS_ROOT = REPO_ROOT / "src" / "icons"
CURSORS_ROOT = REPO_ROOT / "src" / "cursors"
PALETTE = REPO_ROOT / "palette" / "icons.json"


def parse_directories(index_theme: Path) -> list[str]:
    # Directories= is one comma-separated line in the [Icon Theme] section.
    for line in index_theme.read_text().splitlines():
        if line.startswith("Directories="):
            return [entry for entry in line.split("=", 1)[1].split(",") if entry]
    return []


def main() -> int:
    # Every declared context must exist and hold at least one icon, in every pack.
    palette = json.loads(PALETTE.read_text())
    problems: list[str] = []
    counts: list[str] = []

    for key, pack in palette["packs"].items():
        is_icons = key.startswith("icons")
        root = (ICONS_ROOT if is_icons else CURSORS_ROOT) / pack
        threshold = 3000 if is_icons else 50

        if not (root / "index.theme").is_file():
            problems.append(f"missing {root / 'index.theme'}")
            continue

        if is_icons:
            for context in parse_directories(root / "index.theme"):
                folder = root / context
                if not folder.is_dir():
                    problems.append(f"{pack}: index.theme lists missing directory {context}")
                elif not any(folder.iterdir()):
                    problems.append(f"{pack}: index.theme lists empty directory {context}")

        count = sum(1 for _ in root.rglob("*"))
        if count < threshold:
            problems.append(f"{pack} looks truncated ({count} entries)")
        for broken in root.rglob("*"):
            # An alias pointing at a missing icon fails lookups inside the theme.
            if broken.is_symlink() and not broken.exists():
                problems.append(f"{pack}: dangling alias {broken.name} -> {broken.readlink()}")
        counts.append(f"{pack}={count}")

    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"ok: all packs complete, index.theme coverage holds ({', '.join(counts)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
