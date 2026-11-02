# MT Verdant Icon Pack

© Mayanktaker Computers & Web Development | https://mayanktaker.com

A botanical dark icon and cursor suite for Linux desktops — GNOME, KDE Plasma, XFCE, Cinnamon and
Hyprland. Companion artwork for the [MT Verdant Nocturne](https://github.com/Mayanktaker/mt-verdant-nocturne)
theme, maintained and versioned separately.

## Packs

| Pack | Technical name | Contents |
| --- | --- | --- |
| Icons | `MT-Verdant-Icons` | 100+ application icons, folder artwork, devices, MIME types and full symbolic coverage |
| Cursors | `MT-Verdant-Cursors` | 12 crisp Xcursor categories with sage and emerald detailing |

## Install

From a release archive:

```bash
curl -sSLO https://github.com/Mayanktaker/mt-verdant-icons/releases/latest/download/mt-verdant-icons-v1.0.0.tar.xz
tar -xf mt-verdant-icons-v1.0.0.tar.xz
cd mt-verdant-icons-v1.0.0
./install.sh
```

From a checkout:

```bash
git clone https://github.com/Mayanktaker/mt-verdant-icons.git
cd mt-verdant-icons
./install.sh
```

`install.sh` writes to `~/.icons` only — no sudo and no system directories.

| Flag | Effect |
| --- | --- |
| *(none)* | Install and activate both packs |
| `--icons-only` | Install the icon pack only |
| `--cursors-only` | Install the cursor pack only |
| `--no-activate` | Copy files without changing `gsettings` |
| `--uninstall` | Remove both packs from `~/.icons` |

## Requirements

- Python 3 with PyGObject (`gi`), `Rsvg`, `pycairo`, `numpy` and `Pillow` to regenerate artwork.
- `gtk-update-icon-cache` (optional) so new icons appear without re-login.
- Nothing beyond `install.sh` is needed to install a prebuilt release.

## Build from source

```bash
python3 tools/icons/generate_icons.py     # -> src/icons/MT-Verdant-Icons
python3 tools/icons/generate_cursors.py   # -> src/cursors/MT-Verdant-Cursors
sh tools/icons/package.sh 1.0.0            # -> dist/mt-verdant-icons-v1.0.0.tar.xz
```

Generated SVG and cursor output is committed so a clone is installable without Python. CI rebuilds
and fails on any drift.

### Upstream glyphs

GNOME Shell, libadwaita and shell-extension symbolics are vendored under `tools/icons/upstream/`
so builds never read the host desktop. Refresh them deliberately:

```bash
python3 tools/dev/vendor_upstream_icons.py --force
python3 tools/dev/check_upstream_assets.py
```

## Palette

Every brand colour lives in `palette/icons.json`. Artwork literals listed under `aliases` are
remapped to the current token value at build time, so changing a token updates every icon that
uses it. The theme repo keeps its own palette; colour changes do not flow between the two repos.

## Layout

```
palette/icons.json      palette tokens, pack names, version
src/icons/              generated icon theme (committed)
src/cursors/            generated cursor theme (committed)
tools/icons/            generators, artwork catalog, packaging
tools/icons/upstream/   vendored upstream glyphs + provenance.json
tools/dev/              gates (vendor, structure, archive)
install.sh              user installer
docs/release-notes/     user-facing changelog
```

## License

- Code and generators: [GPL-3.0](LICENSES/GPL-3.0.txt)
- Artwork, icons and cursors: [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt)

Vendored upstream glyphs keep their own licenses; see `tools/icons/upstream/provenance.json` and
each set's `LICENSE` file.
