#!/bin/sh
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Installs the MT Verdant icon and cursor packs (dark and/or light) into ~/.icons ONLY.
# Usage: ./install.sh [--dark|--light|--both] [--no-activate] [--icons-only|--cursors-only|--uninstall]

set -eu

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
ICONS_DIR="${HOME}/.icons"

# Pack names live in palette/icons.json so nothing is duplicated in shell.
# Capture before eval: eval of an empty payload always succeeds, so the guard must see python fail.
PACK_VARS="$(python3 -c "
import json, shlex
doc = json.load(open('${REPO_ROOT}/palette/icons.json'))
print('PACK_NAME=' + shlex.quote(doc['meta']['name']))
print('ICONS=' + shlex.quote(doc['packs']['icons']))
print('CURSORS=' + shlex.quote(doc['packs']['cursors']))
print('ICONS_LIGHT=' + shlex.quote(doc['packs']['icons_light']))
print('CURSORS_LIGHT=' + shlex.quote(doc['packs']['cursors_light']))
" 2>/dev/null)" || {
  echo "cannot read palette/icons.json; run from a full checkout" >&2
  exit 1
}
eval "${PACK_VARS}"

WANT_DARK=0
WANT_LIGHT=0
EXPLICIT_BOTH=0
WANT_ICONS=1
WANT_CURSORS=1
ACTIVATE=1
UNINSTALL=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dark) WANT_DARK=1 ;;
    --light) WANT_LIGHT=1 ;;
    --both) WANT_DARK=1; WANT_LIGHT=1; EXPLICIT_BOTH=1 ;;
    --no-activate) ACTIVATE=0 ;;
    --icons-only) WANT_CURSORS=0 ;;
    --cursors-only) WANT_ICONS=0 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help)
      echo "Usage: ./install.sh [--dark|--light|--both] [--no-activate] [--icons-only|--cursors-only|--uninstall]"
      echo "  --dark                      install the dark packs"
      echo "  --light                     install the light packs"
      echo "  --both                      install dark and light packs"
      echo "  --no-activate               install files only"
      echo "  --icons-only                install icon packs only"
      echo "  --cursors-only              install cursor packs only"
      echo "  --uninstall                 remove every variant from ~/.icons"
      echo
      echo "Without a variant flag the installer asks which variant to install (default: both);"
      echo "non-interactive runs (pipes, CI) silently install both."
      exit 0
      ;;
    *)
      echo "unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

# --dark and --light together are ambiguous; --both says what is meant.
if [ "${WANT_DARK}" -eq 1 ] && [ "${WANT_LIGHT}" -eq 1 ] && [ "${EXPLICIT_BOTH}" -eq 0 ]; then
  echo "--dark and --light together are ambiguous; use --both" >&2
  exit 1
fi

# Excluding both pack kinds would install nothing; refuse instead of pretending success.
if [ "${WANT_ICONS}" -eq 0 ] && [ "${WANT_CURSORS}" -eq 0 ]; then
  echo "--icons-only and --cursors-only together install nothing; drop one of them" >&2
  exit 1
fi

# Interactive variant choice; only when installing and no variant flag was given.
if [ "${UNINSTALL}" -eq 0 ] && [ "${WANT_DARK}" -eq 0 ] && [ "${WANT_LIGHT}" -eq 0 ]; then
  if [ -t 0 ]; then
    printf "Which variant of %s should be installed?\n" "${PACK_NAME}"
    printf "  1) Dark   (%s + %s)\n" "${ICONS}" "${CURSORS}"
    printf "  2) Light  (%s + %s)\n" "${ICONS_LIGHT}" "${CURSORS_LIGHT}"
    printf "  3) Both\n"
    printf "Choice [1/2/3, default 3]: "
    read -r REPLY || REPLY=""
    case "${REPLY}" in
      1) WANT_DARK=1 ;;
      2) WANT_LIGHT=1 ;;
      *) WANT_DARK=1; WANT_LIGHT=1 ;;
    esac
  else
    # Non-interactive (pipe, CI): keep unattended defaults working.
    WANT_DARK=1
    WANT_LIGHT=1
  fi
fi

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
  for pack in "${ICONS}" "${CURSORS}" "${ICONS_LIGHT}" "${CURSORS_LIGHT}"; do
    if [ -d "${ICONS_DIR:?}/${pack}" ]; then
      rm -rf "${ICONS_DIR:?}/${pack}"
      echo "  ✗ removed ${pack}"
    fi
  done
  echo "Uninstalled ${PACK_NAME}. Pick another icon theme with gsettings if one is still active."
  exit 0
fi

mkdir -p "${ICONS_DIR}"
VARIANTS=""
[ "${WANT_DARK}" -eq 1 ] && VARIANTS="dark"
[ "${WANT_LIGHT}" -eq 1 ] && VARIANTS="${VARIANTS} light"
echo "Installing ${PACK_NAME} (${VARIANTS# }) into ${ICONS_DIR}"

if [ "${WANT_ICONS}" -eq 1 ]; then
  if [ "${WANT_DARK}" -eq 1 ]; then
    install_pack "${ICONS}" icons "python3 tools/icons/generate_icons.py --variant dark" || exit 1
  fi
  if [ "${WANT_LIGHT}" -eq 1 ]; then
    install_pack "${ICONS_LIGHT}" icons "python3 tools/icons/generate_icons.py --variant light" || exit 1
  fi
fi
if [ "${WANT_CURSORS}" -eq 1 ]; then
  if [ "${WANT_DARK}" -eq 1 ]; then
    install_pack "${CURSORS}" cursors "python3 tools/icons/generate_cursors.py --variant dark" || exit 1
  fi
  if [ "${WANT_LIGHT}" -eq 1 ]; then
    install_pack "${CURSORS_LIGHT}" cursors "python3 tools/icons/generate_cursors.py --variant light" || exit 1
  fi
fi

# Activation is best-effort; a headless or non-GNOME session simply skips it.
# When both variants are installed the dark packs stay active to match the Nocturne suite.
if [ "${ACTIVATE}" -eq 1 ] && command -v gsettings >/dev/null 2>&1; then
  ICONS_ACTIVE="${ICONS}"
  CURSORS_ACTIVE="${CURSORS}"
  if [ "${WANT_DARK}" -eq 0 ]; then
    ICONS_ACTIVE="${ICONS_LIGHT}"
    CURSORS_ACTIVE="${CURSORS_LIGHT}"
  fi
  if [ "${WANT_ICONS}" -eq 1 ]; then
    gsettings set org.gnome.desktop.interface icon-theme "${ICONS_ACTIVE}" 2>/dev/null || true
    echo "Activated icon theme: ${ICONS_ACTIVE}"
  fi
  if [ "${WANT_CURSORS}" -eq 1 ]; then
    gsettings set org.gnome.desktop.interface cursor-theme "${CURSORS_ACTIVE}" 2>/dev/null || true
    echo "Activated cursor theme: ${CURSORS_ACTIVE}"
  fi
fi

echo "Done. Remove later with: ./install.sh --uninstall"
