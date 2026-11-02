#!/bin/sh
# © Mayanktaker Computers & Web Development | https://mayanktaker.com
# Packages the MT Verdant icon pack and cursors into a standalone .tar.xz release archive.
# Usage: tools/icons/package.sh [version]  (defaults to palette/icons.json meta.version)

set -eu

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Pack names and version come from the palette so nothing is duplicated in shell.
eval "$(python3 -c "
import json, shlex
doc = json.load(open('${REPO_ROOT}/palette/icons.json'))
print('PACK_NAME=' + shlex.quote(doc['meta']['name']))
print('PACK_SLUG=' + shlex.quote(doc['packs']['icons'].lower()))
print('VERSION_DEFAULT=' + shlex.quote(doc['meta']['version']))
print('ICONS=' + shlex.quote(doc['packs']['icons']))
print('CURSORS=' + shlex.quote(doc['packs']['cursors']))
")"

VERSION="${1:-${VERSION_DEFAULT}}"
DIST_ROOT="${REPO_ROOT}/dist"
STAGE="${DIST_ROOT}/${PACK_SLUG}-v${VERSION}"
TARBALL="${DIST_ROOT}/${PACK_SLUG}-v${VERSION}.tar.xz"

mkdir -p "${DIST_ROOT}"
rm -rf "${STAGE}"
mkdir -p "${STAGE}/src/icons" "${STAGE}/src/cursors"

# Fail loudly instead of shipping an archive without a pack.
if [ ! -d "${REPO_ROOT}/src/icons/${ICONS}" ]; then
  echo "missing src/icons/${ICONS}; run tools/icons/generate_icons.py" >&2
  exit 1
fi
if [ ! -d "${REPO_ROOT}/src/cursors/${CURSORS}" ]; then
  echo "missing src/cursors/${CURSORS}; run tools/icons/generate_cursors.py" >&2
  exit 1
fi
cp -r "${REPO_ROOT}/src/icons/${ICONS}" "${STAGE}/src/icons/"
cp -r "${REPO_ROOT}/src/cursors/${CURSORS}" "${STAGE}/src/cursors/"

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
  echo "./install.sh                # install and activate both packs"
  echo "./install.sh --icons-only   # icon pack only"
  echo "./install.sh --uninstall    # remove both packs from ~/.icons"
  echo '```'
  echo
  echo "Packs: \`${ICONS}\`, \`${CURSORS}\`."
} > "${STAGE}/README.md"

rm -f "${TARBALL}"
tar -C "${DIST_ROOT}" -cJf "${TARBALL}" "$(basename "${STAGE}")"
rm -rf "${STAGE}"

echo "Icon pack ready: ${TARBALL}"
