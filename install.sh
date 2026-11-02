#!/bin/sh
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Installs the MT Verdant icon and cursor packs into the user's ~/.icons ONLY.
# Usage: ./install.sh [--no-activate] [--icons-only|--cursors-only|--uninstall]

set -eu

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
ICONS_DIR="${HOME}/.icons"

# Pack names live in palette/icons.json so nothing is duplicated in shell.
eval "$(python3 -c "
import json, shlex
doc = json.load(open('${REPO_ROOT}/palette/icons.json'))
print('PACK_NAME=' + shlex.quote(doc['meta']['name']))
print('ICONS=' + shlex.quote(doc['packs']['icons']))
print('CURSORS=' + shlex.quote(doc['packs']['cursors']))
" 2>/dev/null)" || {
  echo "cannot read palette/icons.json; run from a full checkout" >&2
  exit 1
}

WANT_ICONS=1
WANT_CURSORS=1
ACTIVATE=1
UNINSTALL=0

while [ $# -gt 0 ]; do
  case "$1" in
    --no-activate) ACTIVATE=0 ;;
    --icons-only) WANT_CURSORS=0 ;;
    --cursors-only) WANT_ICONS=0 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help)
      echo "Usage: ./install.sh [--no-activate] [--icons-only|--cursors-only|--uninstall]"
      echo "  --no-activate               install files only"
      echo "  --icons-only                install the icon pack only"
      echo "  --cursors-only              install the cursor pack only"
      echo "  --uninstall                 remove both packs from ~/.icons"
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

# Reuse the icon cache so a newly installed pack appears without a re-login.
refresh_cache() {
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${ICONS_DIR:?}/$1" >/dev/null 2>&1 || true
  fi
}

# Copy one pack next to its final location, then swap it in, so a failed copy never
# leaves the user without icons.
install_pack() {
  pack="${1:?missing pack name}"
  src="${REPO_ROOT}/src/${2:?missing pack kind}/${pack}"
  if [ ! -d "${src}" ]; then
    echo "  ! missing ${src} (build it first: $3)" >&2
    return 1
  fi
  staging="${ICONS_DIR:?}/.${pack}.tmp"
  rm -rf "${staging}"
  cp -r "${src}" "${staging}"
  rm -rf "${ICONS_DIR:?}/${pack}"
  mv "${staging}" "${ICONS_DIR:?}/${pack}"
  refresh_cache "${pack}"
  echo "  ✓ ${pack}"
}

# Removal only deletes packs this repository owns; the active theme is left to the user.
if [ "${UNINSTALL}" -eq 1 ]; then
  for pack in "${ICONS}" "${CURSORS}"; do
    if [ -d "${ICONS_DIR:?}/${pack}" ]; then
      rm -rf "${ICONS_DIR:?}/${pack}"
      echo "  ✗ removed ${pack}"
    fi
  done
  echo "Uninstalled ${PACK_NAME}. Pick another icon theme with gsettings if one is still active."
  exit 0
fi

mkdir -p "${ICONS_DIR}"
echo "Installing ${PACK_NAME} into ${ICONS_DIR}"

if [ "${WANT_ICONS}" -eq 1 ]; then
  install_pack "${ICONS}" icons "python3 tools/icons/generate_icons.py" || exit 1
fi
if [ "${WANT_CURSORS}" -eq 1 ]; then
  install_pack "${CURSORS}" cursors "python3 tools/icons/generate_cursors.py" || exit 1
fi

# Activation is best-effort; a headless or non-GNOME session simply skips it.
if [ "${ACTIVATE}" -eq 1 ] && command -v gsettings >/dev/null 2>&1; then
  if [ "${WANT_ICONS}" -eq 1 ]; then
    gsettings set org.gnome.desktop.interface icon-theme "${ICONS}" 2>/dev/null || true
    echo "Activated icon theme: ${ICONS}"
  fi
  if [ "${WANT_CURSORS}" -eq 1 ]; then
    gsettings set org.gnome.desktop.interface cursor-theme "${CURSORS}" 2>/dev/null || true
    echo "Activated cursor theme: ${CURSORS}"
  fi
fi

echo "Done. Remove later with: ./install.sh --uninstall"
