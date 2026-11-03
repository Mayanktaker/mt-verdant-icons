#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Unpacks the newest dist archive, installs it into throwaway HOMEs and asserts the variant
# selection behaves, then uninstalls and asserts everything is gone.
# Usage: tools/dev/check_release_archive.py [tarball]

import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PALETTE = REPO_ROOT / "palette" / "icons.json"


def newest_tarball() -> Path:
    # Latest built archive, so the gate works right after package.sh.
    tarballs = sorted((REPO_ROOT / "dist").glob("*.tar.xz"), key=lambda p: p.stat().st_mtime)
    if not tarballs:
        raise SystemExit("no dist/*.tar.xz found; run tools/icons/package.sh first")
    return tarballs[-1]


def run_installer(stage: Path, home: Path, *flags: str) -> subprocess.CompletedProcess:
    # Always a closed stdin and explicit variant flags: the interactive prompt is never exercised.
    env = dict(os.environ, HOME=str(home))
    return subprocess.run(
        ["sh", "install.sh", *flags], cwd=stage, env=env,
        stdin=subprocess.DEVNULL, capture_output=True, text=True,
    )


def main() -> int:
    # Extract, install both variants, verify the light-only path, then uninstall and verify removal.
    palette = json.loads(PALETTE.read_text())
    tarball = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_tarball()
    packs = list(palette["packs"].values())
    light_packs = [palette["packs"]["icons_light"], palette["packs"]["cursors_light"]]
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        extract_root = Path(tmp) / "extract"
        extract_root.mkdir()
        with tarfile.open(tarball) as archive:
            archive.extractall(extract_root, filter="data")
        roots = [p for p in extract_root.iterdir() if p.is_dir()]
        if len(roots) != 1:
            print(f"FAIL  archive should hold one top-level directory, found {len(roots)}")
            return 1
        stage = roots[0]

        # 1. Both variants install from the archive's own installer.
        home_a = Path(tmp) / "home-a"
        home_a.mkdir()
        install = run_installer(stage, home_a, "--both", "--no-activate")
        if install.returncode != 0:
            problems.append(f"install --both failed: {install.stderr.strip()}")
        for pack in packs:
            if not (home_a / ".icons" / pack).is_dir():
                problems.append(f"missing installed pack {pack}")

        # 2. Light-only selection installs exactly the light packs in a fresh HOME.
        home_b = Path(tmp) / "home-b"
        home_b.mkdir()
        light = run_installer(stage, home_b, "--light", "--no-activate")
        if light.returncode != 0:
            problems.append(f"install --light failed: {light.stderr.strip()}")
        for pack in light_packs:
            if not (home_b / ".icons" / pack).is_dir():
                problems.append(f"light install missing {pack}")
        for pack in packs:
            if pack not in light_packs and (home_b / ".icons" / pack).exists():
                problems.append(f"light install unexpectedly added {pack}")

        # 3. Uninstall removes every variant.
        uninstall = run_installer(stage, home_a, "--uninstall")
        if uninstall.returncode != 0:
            problems.append(f"uninstall failed: {uninstall.stderr.strip()}")
        for pack in packs:
            if (home_a / ".icons" / pack).exists():
                problems.append(f"uninstall left {pack} behind")
    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"ok: {tarball.name} installs both variants, honors --light, and removes all packs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
