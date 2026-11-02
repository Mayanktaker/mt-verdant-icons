#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Validates the generated packs: index.theme coverage, pack presence and non-empty contexts.

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
    # Every declared context must exist and hold at least one icon.
    palette = json.loads(PALETTE.read_text())
    icons_pack = ICONS_ROOT / palette["packs"]["icons"]
    cursors_pack = CURSORS_ROOT / palette["packs"]["cursors"]
    problems: list[str] = []

    if not (icons_pack / "index.theme").is_file():
        problems.append(f"missing {icons_pack / 'index.theme'}")
    if not (cursors_pack / "index.theme").is_file():
        problems.append(f"missing {cursors_pack / 'index.theme'}")

    for context in parse_directories(icons_pack / "index.theme"):
        folder = icons_pack / context
        if not folder.is_dir():
            problems.append(f"index.theme lists missing directory {context}")
        elif not any(folder.iterdir()):
            problems.append(f"index.theme lists empty directory {context}")

    icon_count = sum(1 for _ in icons_pack.rglob("*"))
    cursor_count = sum(1 for _ in cursors_pack.rglob("*"))
    if icon_count < 3000:
        problems.append(f"icon pack looks truncated ({icon_count} entries)")
    if cursor_count < 50:
        problems.append(f"cursor pack looks truncated ({cursor_count} entries)")

    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"ok: {icon_count} icon entries, {cursor_count} cursor entries, index.theme complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
