#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Unpacks the newest dist archive, installs it into a throwaway HOME and asserts both packs land,
# then uninstalls and asserts they are gone. Usage: tools/dev/check_release_archive.py [tarball]

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


def main() -> int:
    # Extract, install, verify, uninstall and verify removal.
    palette = json.loads(PALETTE.read_text())
    tarball = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_tarball()
    packs = [palette["packs"]["icons"], palette["packs"]["cursors"]]
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        extract_root = Path(tmp) / "extract"
        extract_root.mkdir()
        with tarfile.open(tarball) as archive:
            archive.extractall(extract_root, filter="data")
        roots = [p for p in extract_root.iterdir() if p.is_dir()]
        if len(roots) != 1:
            print(f"FAIL  archive should hold one top-level directory, found {len(roots)}")
            return 1
        stage = roots[0]
        env = dict(os.environ, HOME=str(home))
        install = subprocess.run(["sh", "install.sh", "--no-activate"], cwd=stage, env=env, capture_output=True, text=True)
        if install.returncode != 0:
            problems.append(f"install failed: {install.stderr.strip()}")
        for pack in packs:
            if not (home / ".icons" / pack).is_dir():
                problems.append(f"missing installed pack {pack}")
        uninstall = subprocess.run(["sh", "install.sh", "--uninstall"], cwd=stage, env=env, capture_output=True, text=True)
        if uninstall.returncode != 0:
            problems.append(f"uninstall failed: {uninstall.stderr.strip()}")
        for pack in packs:
            if (home / ".icons" / pack).exists():
                problems.append(f"uninstall left {pack} behind")
    if problems:
        for line in problems:
            print(f"FAIL  {line}")
        return 1
    print(f"ok: {tarball.name} installs and removes both packs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
