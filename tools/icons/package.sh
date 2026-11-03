#!/bin/sh
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Packages the MT Verdant icon pack and cursors into a standalone .tar.xz release archive.
# Usage: tools/icons/package.sh [version]  (defaults to palette/icons.json meta.version)

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Pack names and version come from the palette so nothing is duplicated in shell.
# Capture before eval: eval of an empty payload always succeeds, so the guard must see python fail.
PACK_VARS="$(python3 -c "
import json, shlex
doc = json.load(open('${REPO_ROOT}/palette/icons.json'))
print('PACK_NAME=' + shlex.quote(doc['meta']['name']))
print('PACK_SLUG=' + shlex.quote(doc['packs']['icons'].lower()))
print('VERSION_DEFAULT=' + shlex.quote(doc['meta']['version']))
print('ICONS=' + shlex.quote(doc['packs']['icons']))
print('CURSORS=' + shlex.quote(doc['packs']['cursors']))
print('ICONS_LIGHT=' + shlex.quote(doc['packs']['icons_light']))
print('CURSORS_LIGHT=' + shlex.quote(doc['packs']['cursors_light']))
")" || {
  echo "cannot read palette/icons.json; run from a full checkout" >&2
  exit 1
}
eval "${PACK_VARS}"

VERSION="${1:-${VERSION_DEFAULT}}"
DIST_ROOT="${REPO_ROOT}/dist"
STAGE="${DIST_ROOT}/${PACK_SLUG}-v${VERSION}"
TARBALL="${DIST_ROOT}/${PACK_SLUG}-v${VERSION}.tar.xz"

mkdir -p "${DIST_ROOT}"
rm -rf "${STAGE}"
mkdir -p "${STAGE}/src/icons" "${STAGE}/src/cursors"
# A failed check below must not leave the staging directory behind.
trap 'rm -rf "${STAGE}"' EXIT

# Fail loudly instead of shipping an archive without a pack.
check_pack() {
  # kind is icons or cursors; the generator of the same name builds it.
  if [ ! -d "${REPO_ROOT}/src/$1/$2" ]; then
    echo "missing src/$1/$2; run tools/icons/generate_$1.py" >&2
    exit 1
  fi
}
check_pack icons "${ICONS}"
check_pack icons "${ICONS_LIGHT}"
check_pack cursors "${CURSORS}"
check_pack cursors "${CURSORS_LIGHT}"
cp -r "${REPO_ROOT}/src/icons/${ICONS}" "${STAGE}/src/icons/"
cp -r "${REPO_ROOT}/src/icons/${ICONS_LIGHT}" "${STAGE}/src/icons/"
cp -r "${REPO_ROOT}/src/cursors/${CURSORS}" "${STAGE}/src/cursors/"
cp -r "${REPO_ROOT}/src/cursors/${CURSORS_LIGHT}" "${STAGE}/src/cursors/"

# Licenses, palette and the same installer users get from the checkout.
mkdir -p "${STAGE}/LICENSES" "${STAGE}/palette"
cp "${REPO_ROOT}"/LICENSES/* "${STAGE}/LICENSES/"
cp "${REPO_ROOT}/palette/icons.json" "${STAGE}/palette/icons.json"
cp "${REPO_ROOT}/install.sh" "${STAGE}/install.sh"
chmod +x "${STAGE}/install.sh"

# Bundle a README so the archive explains itself without the repository.
{
  echo "# ${PACK_NAME} ${VERSION}"
  echo
  echo "© Mayanktaker Computers & Web Development | https://mayanktaker.com"
  echo
  echo "Botanical Canopy icon and cursor pack for the MT Verdant Nocturne desktop suite."
  echo
  echo "## Install"
  echo
  echo '```bash'
  echo "./install.sh                # asks which variant to install (dark, light or both)"
  echo "./install.sh --light        # install the light packs only"
  echo "./install.sh --dark         # install the dark packs only"
  echo "./install.sh --icons-only   # icon packs only"
  echo "./install.sh --uninstall    # remove every variant from ~/.icons"
  echo '```'
  echo
  echo "Packs: \`${ICONS}\`, \`${CURSORS}\` (dark); \`${ICONS_LIGHT}\`, \`${CURSORS_LIGHT}\` (light)."
} > "${STAGE}/README.md"

rm -f "${TARBALL}"
tar -C "${DIST_ROOT}" -cJf "${TARBALL}" "$(basename "${STAGE}")"
rm -rf "${STAGE}"

echo "Icon pack ready: ${TARBALL}"
