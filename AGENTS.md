# AGENTS.md — MT Verdant Icon Pack

© Mayanktaker Computers & Web Development | https://mayanktaker.com

Standalone icon and cursor pack for the MT Verdant Nocturne desktop suite. Split out of the theme
repository so artwork can be versioned and released independently — **this repo must not read the
theme's `palette/` or build files**.

## Stack & toolchain (verify before assuming; update when versions change)
- Python 3.14 runtime, PyGObject (`Rsvg`), pycairo, `numpy` (cursor rasterisation), Pillow.
- Output: FreeDesktop/KDE icon theme (`index.theme`, scalable SVG + 32/48/64/128 PNG) and Xcursor.
- Repo: git 2.56, `gh` authenticated as `Mayanktaker`, default branch `main`, public.
- Installation policy: user packs go to the user's `~/.icons` ONLY. No sudo, no system dirs.

## Single source of truth
- `palette/icons.json` — pack names, version and every brand colour. No magic values in new code;
  add tokens instead. Existing artwork literals are listed under `aliases` and remapped at build
  time, so editing a token reaches every icon that used the original hex.
- Upstream glyphs are vendored under `tools/icons/upstream/`; never harvest them at build time.

## Commands
- Build icons: `python3 tools/icons/generate_icons.py` → `src/icons/MT-Verdant-Icons`.
- Build cursors: `python3 tools/icons/generate_cursors.py` → `src/cursors/MT-Verdant-Cursors`.
- Vendor gate: `python3 tools/dev/check_upstream_assets.py` (hashes match `provenance.json`).
- Structure gate: `python3 tools/dev/validate_icons.py` (index.theme coverage, pack size).
- Refresh vendor tree: `python3 tools/dev/vendor_upstream_icons.py --force` (host-only, commit the diff).
- Package: `sh tools/icons/package.sh [version]` → `dist/mt-verdant-icons-v<version>.tar.xz`.
- Archive gate: `python3 tools/dev/check_release_archive.py` (install + uninstall in a throwaway HOME).
- Install: `./install.sh [--no-activate] [--icons-only|--cursors-only|--uninstall]`.
- CI: `.github/workflows/gates.yml` (PR/push) and `release.yml` (v* tags).

## Layout
- `palette/icons.json` — tokens, pack names, version
- `src/icons/` — generated `MT-Verdant-Icons` (committed artifact)
- `src/cursors/` — generated `MT-Verdant-Cursors` (committed artifact)
- `tools/icons/` — generators, artwork catalog, `palette_tokens.py`, `upstream_assets.py`, `package.sh`
- `tools/icons/upstream/` — vendored GNOME Shell / libadwaita / extension glyphs + `provenance.json`
- `tools/dev/` — vendor, structure and archive gates
- `docs/release-notes/` — user-facing changelog
- `dist/` — generated archives (gitignored)

## Artwork rules
- Every SVG write goes through `palette_tokens.resolve()`; placeholders and aliases must resolve to
  a value in `palette/icons.json`.
- Vendored upstream glyphs are never edited by hand; refresh them with the vendoring tool and
  review the diff. Glyphs dropped by newer upstream releases go to `upstream/retained/` so users
  keep them.
- Generated SVG and cursor output is committed; PNGs are not compared byte for byte in CI because
  rasterisation depends on the local librsvg build.
- Keep pack names and version in `palette/icons.json`; scripts read them from there.

## Conventions
- Every file starts with the © header line; executable scripts keep `#!` on line 1 with the © line
  immediately after it.
- Every function/block gets one ≤1-line comment.
- License: GPL-3.0 (code) + CC BY-SA 4.0 (artwork). Commit at verified milestones, never force-push.
