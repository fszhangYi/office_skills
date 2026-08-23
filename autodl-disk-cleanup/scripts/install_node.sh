#!/usr/bin/env bash
# Install official Node.js LTS to autodl-tmp (avoids broken apt npm on some images).
set -euo pipefail

VERSION="${NODE_VERSION:-22.14.0}"
ARCH="${NODE_ARCH:-linux-x64}"
DEST="/root/autodl-tmp/node-v${VERSION}-${ARCH}"
TARBALL="/root/autodl-tmp/node-v${VERSION}-${ARCH}.tar.xz"
URL="https://nodejs.org/dist/v${VERSION}/node-v${VERSION}-${ARCH}.tar.xz"

if [[ -x "${DEST}/bin/npm" ]]; then
  echo "Node already installed: ${DEST}"
  "${DEST}/bin/node" -v
  "${DEST}/bin/npm" -v
  echo "export PATH=\"${DEST}/bin:\$PATH\""
  exit 0
fi

echo "Downloading Node v${VERSION} to ${DEST}..."
curl -fsSL "$URL" -o "$TARBALL"
tar -xf "$TARBALL" -C /root/autodl-tmp
rm -f "$TARBALL"

"${DEST}/bin/node" -v
"${DEST}/bin/npm" -v
echo ""
echo "Add to shell profile:"
echo "  export PATH=\"${DEST}/bin:\$PATH\""
