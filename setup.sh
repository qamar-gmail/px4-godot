#!/bin/bash
# Install mediamtx if not already on PATH
set -e

MEDIAMTX_VERSION="v1.9.1"
INSTALL_DIR="$HOME/.local/bin"
MEDIAMTX_URL="https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz"

if command -v mediamtx &>/dev/null; then
  echo "[setup] mediamtx already installed: $(command -v mediamtx)"
  exit 0
fi

echo "[setup] downloading mediamtx ${MEDIAMTX_VERSION}..."
mkdir -p "$INSTALL_DIR"
tmp=$(mktemp -d)
curl -L "$MEDIAMTX_URL" | tar -xz -C "$tmp"
mv "$tmp/mediamtx" "$INSTALL_DIR/mediamtx"
chmod +x "$INSTALL_DIR/mediamtx"
rm -rf "$tmp"

echo "[setup] installed to $INSTALL_DIR/mediamtx"
echo "[setup] ensure $INSTALL_DIR is in your PATH"

# Python deps
echo "[setup] installing Python bridge dependencies..."
pip install -r "$(dirname "$0")/bridge/requirements.txt"

echo "[setup] done."
