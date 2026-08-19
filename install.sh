#!/usr/bin/env bash
set -euo pipefail

REPO="AmirGHaghighi/kuma-proxy-checker"
BINARY="kuma-proxy-checker"
DEFAULT_DIR="$HOME/.local/bin"

if [ "$(uname -s)" != "Linux" ]; then
  echo "Error: this installer supports Linux only."
  echo "For other platforms, download from https://github.com/$REPO/releases"
  exit 1
fi

echo "kuma-proxy-checker installer"
echo "==========================="
echo ""

# Resolve install directory
INSTALL_DIR="${1:-$DEFAULT_DIR}"

mkdir -p "$INSTALL_DIR"

# Fetch latest release
echo "Fetching latest release..."
if command -v gh &>/dev/null; then
  DOWNLOAD_URL=$(gh release view --repo "$REPO" --json assets -q '.assets[] | select(.name == "'"$BINARY"'") | .downloadUrl')
  CONFIG_URL=$(gh release view --repo "$REPO" --json assets -q '.assets[] | select(.name == "config.example.json") | .downloadUrl')
else
  API_URL="https://api.github.com/repos/$REPO/releases/latest"
  DOWNLOAD_URL=$(curl -fsSL "$API_URL" | grep -o '"browser_download_url": *"[^"]*'"$BINARY"'"' | cut -d'"' -f4)
  CONFIG_URL=$(curl -fsSL "$API_URL" | grep -o '"browser_download_url": *"[^"]*config\.example\.json"' | cut -d'"' -f4)
fi

if [ -z "$DOWNLOAD_URL" ]; then
  echo "Error: could not find download URL. Check https://github.com/$REPO/releases"
  exit 1
fi

# Download binary
echo "Downloading $BINARY..."
curl -fsSL "$DOWNLOAD_URL" -o "$INSTALL_DIR/$BINARY"
chmod +x "$INSTALL_DIR/$BINARY"

# Download example config
if [ -n "$CONFIG_URL" ]; then
  echo "Downloading config.example.json..."
  curl -fsSL "$CONFIG_URL" -o config.example.json
fi

# Create config.json if missing
if [ ! -f config.json ] && [ -f config.example.json ]; then
  cp config.example.json config.json
  echo "Created config.json from config.example.json — edit it to configure your targets."
fi

# Check PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  SHELL_RC=""
  if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
  elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
  fi

  echo ""
  echo "Installed to: $INSTALL_DIR/$BINARY"
  echo ""
  echo "Add $INSTALL_DIR to your PATH by running:"
  if [ -n "$SHELL_RC" ]; then
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $SHELL_RC"
    echo "  source $SHELL_RC"
  else
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
else
  echo ""
  echo "Installed: $INSTALL_DIR/$BINARY"
fi

echo ""
echo "Edit config.json to configure your proxy targets, then run:"
echo "  kuma-proxy-checker -c config.json"
