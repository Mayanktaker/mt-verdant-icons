#!/usr/bin/env python3
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# One-time (and repeatable) harvest of the upstream symbolic glyphs the build used to read from
# the machine it ran on: GNOME Shell, libadwaita and the local GNOME Shell extensions.
# Writes tools/icons/upstream/<set>/*.svg plus a hashed provenance manifest so builds are hermetic.
# Usage: tools/dev/vendor_upstream_icons.py [--force]

import hashlib
import json
import platform
import shutil
import sys
from pathlib import Path

import gi

gi.require_version("Gio", "2.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

REPO_ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_ROOT = REPO_ROOT / "tools" / "icons" / "upstream"
MANIFEST = UPSTREAM_ROOT / "provenance.json"

# Sets the build reads instead of the host, with the licence each one carries upstream.
SETS = {
    "gnome-shell": {
        "origin": "gnome-shell-icons.gresource",
        "license": "GPL-2.0-or-later",
        "license_files": ("LICENSES/GPL-2.0.txt",),
        "subpaths": ("/org/gnome/shell/icons/scalable/actions", "/org/gnome/shell/icons/scalable/status"),
    },
    "adwaita": {
        "origin": "libadwaita GResource",
        "license": "LGPL-3.0-or-later for the code, CC-BY-SA-3.0 for the artwork",
        "license_files": ("LICENSES/LGPL-3.0.txt", "LICENSES/CC-BY-SA-3.0.txt"),
        "subpaths": ("/org/gnome/Adwaita/icons/scalable/actions",),
    },
}

# Extensions whose icon sets were previously folded into the pack at build time.
EXTENSIONS = {
    "blur-my-shell": {
        "home": "blur-my-shell@aunetx",
        "folder": Path.home() / ".local/share/gnome-shell/extensions/blur-my-shell@aunetx/icons/hicolor/scalable/actions",
        "license": "GPL-3.0",
        "license_files": ("LICENSES/GPL-3.0.txt",),
    },
    "tiling-shell": {
        "home": "tilingshell@ferrarodomenico.com",
        "folder": Path.home() / ".local/share/gnome-shell/extensions/tilingshell@ferrarodomenico.com/icons",
        "license": "GPL-3.0",
        "license_files": ("LICENSES/GPL-3.0.txt",),
    },
}


# Upstream glyphs dropped by a newer extension/shell release but kept for pack compatibility.
# Files are never re-harvested; this block only re-hashes what is already vendored.
RETAINED = {
    "origin": "previous pack harvest retained for compatibility",
    "license": "mixed upstream licenses retained from the originating sets",
    "license_files": ("LICENSES/GPL-3.0.txt", "LICENSES/CC-BY-SA-4.0.txt"),
}


def adw_version() -> str:
    # Best-effort libadwaita version for the provenance record.
    try:
        return f"{Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}"
    except Exception:
        return "unknown"


def gnome_shell_version() -> str:
    # Shell version as reported by the installed binary, if there is one.
    try:
        import subprocess

        return subprocess.run(["gnome-shell", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def write_set(name: str, icons: dict[str, str], manifest: dict, record: dict) -> int:
    # Write one vendored set, its licence note and a hash per file.
    target = UPSTREAM_ROOT / name
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    hashes = {}
    for filename, text in sorted(icons.items()):
        (target / filename).write_text(text)
        hashes[filename] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (target / "LICENSE").write_text(
        f"{name} — {record['license']}\n"
        f"Source: {record['origin']}\n"
        f"Full text: {', '.join(record['license_files'])}\n"
        "These files keep their upstream terms; they are not relicensed by this project.\n"
        "Vendored by tools/dev/vendor_upstream_icons.py — do not edit by hand.\n"
    )
    manifest["sets"][name].update(record)
    manifest["sets"][name]["icons"] = hashes
    manifest["sets"][name]["count"] = len(hashes)
    return len(hashes)


def harvest_resources(name: str, errors: list[str]) -> dict[str, str]:
    # Read every SVG from the named gresource subpaths.
    spec = SETS[name]
    icons: dict[str, str] = {}
    if name == "gnome-shell":
        path = Path("/usr/share/gnome-shell/gnome-shell-icons.gresource")
        if not path.exists():
            errors.append(f"{path} is missing; cannot harvest {name}")
            return icons
        Gio.resources_register(Gio.Resource.load(str(path)))
    else:
        Adw.init()
    for subpath in spec["subpaths"]:
        try:
            children = Gio.resources_enumerate_children(subpath, Gio.ResourceLookupFlags.NONE)
        except Exception as exc:
            errors.append(f"{name}: cannot enumerate {subpath} ({exc})")
            continue
        for child in children:
            try:
                data = Gio.resources_lookup_data(f"{subpath}/{child}", Gio.ResourceLookupFlags.NONE)
                icons[child] = data.get_data().decode("utf-8")
            except Exception as exc:
                errors.append(f"{name}: cannot read {subpath}/{child} ({exc})")
    return icons


def harvest_extension(name: str, folder: Path, errors: list[str]) -> dict[str, str]:
    # Read the SVG icons an extension ships in its own icon directory.
    if not folder.is_dir():
        print(f"  note: {name} not installed at {folder}; skipping")
        return {}
    icons = {}
    for svg in sorted(folder.glob("*.svg")):
        icons[svg.name] = svg.read_text()
    return icons


def main() -> int:
    # Rebuild the vendored tree and its manifest from this host's resources.
    force = "--force" in sys.argv[1:]
    if UPSTREAM_ROOT.exists() and not force:
        sys.exit(f"{UPSTREAM_ROOT} already exists; pass --force to re-harvest")
    errors: list[str] = []
    manifest = {
        "generated_by": "tools/dev/vendor_upstream_icons.py",
        "host": {"platform": platform.platform(), "gnome_shell": gnome_shell_version(), "libadwaita": adw_version()},
        "sets": {},
    }
    total = 0
    for name, spec in SETS.items():
        manifest["sets"][name] = {}
        icons = harvest_resources(name, errors)
        total += write_set(name, icons, manifest, {
            "origin": spec["origin"],
            "license": spec["license"],
            "license_files": list(spec["license_files"]),
        })
        print(f"  {name}: {len(icons)} icon(s)")
    for name, spec in EXTENSIONS.items():
        manifest["sets"][name] = {}
        icons = harvest_extension(name, spec["folder"], errors)
        if icons:
            total += write_set(name, icons, manifest, {
                "origin": f"~/.local/share/gnome-shell/extensions/{spec['home']}",
                "license": spec["license"],
                "license_files": list(spec["license_files"]),
            })
            print(f"  {name}: {len(icons)} icon(s)")
    retained_dir = UPSTREAM_ROOT / "retained"
    if retained_dir.is_dir():
        retained = {svg.name: svg.read_text() for svg in sorted(retained_dir.glob("*.svg"))}
        manifest["sets"]["retained"] = {}
        manifest["sets"]["retained"].update(RETAINED)
        manifest["sets"]["retained"]["icons"] = {
            filename: hashlib.sha256(text.encode("utf-8")).hexdigest() for filename, text in retained.items()
        }
        manifest["sets"]["retained"]["count"] = len(retained)
        total += len(retained)
        print(f"  retained: {len(retained)} icon(s)")
    if errors:
        for line in errors:
            print(f"FAIL  {line}")
        return 1
    UPSTREAM_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Vendored {total} upstream icon(s) into {UPSTREAM_ROOT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
