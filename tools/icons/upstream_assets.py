# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Loads the vendored upstream symbolic glyphs (GNOME Shell, libadwaita, shell extensions) so the
# build never reads the host desktop. Refresh with tools/dev/vendor_upstream_icons.py.

from pathlib import Path

UPSTREAM_ROOT = Path(__file__).resolve().parent / "upstream"

# Sets merged into the symbolic tree, in precedence order (later sets win on a name clash).
# "retained" holds glyphs a newer upstream release dropped; live sets override them on a clash.
SET_NAMES = ("retained", "gnome-shell", "adwaita", "blur-my-shell", "tiling-shell")


def load_set(name: str) -> dict[str, str]:
    # Every vendored SVG of one upstream set, keyed by file name.
    folder = UPSTREAM_ROOT / name
    if not folder.is_dir():
        raise SystemExit(f"missing vendored upstream set {folder}; run tools/dev/vendor_upstream_icons.py --force")
    return {svg.name: svg.read_text() for svg in sorted(folder.glob("*.svg"))}


def load_all() -> dict[str, str]:
    # Merged glyph map across sets; later sets override earlier ones, matching the old harvest order.
    icons: dict[str, str] = {}
    for name in SET_NAMES:
        icons.update(load_set(name))
    return icons


UPSTREAM_ICONS = load_all()
