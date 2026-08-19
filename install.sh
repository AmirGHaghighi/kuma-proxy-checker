#!/usr/bin/env bash
set -euo pipefail

REPO="AmirGHaghighi/kuma-proxy-checker"
BINARY="kuma-proxy-checker"
DEFAULT_DIR="$HOME/.local/bin"
RELEASE_URL="https://github.com/$REPO/releases/latest"
API_URL="https://api.github.com/repos/$REPO/releases/latest"

# --- Helpers -----------------------------------------------------------

die()  { echo "Error: $*" >&2; exit 1; }
info() { echo "$*"; }

fetch_asset_url() {
  local name="$1"
  if command -v gh &>/dev/null; then
    gh release view --repo "$REPO" --json assets \
      -q ".assets[] | select(.name == \"$name\") | .downloadUrl"
  else
    curl -fsSL "$API_URL" \
      | grep -o "\"browser_download_url\": *\"[^\"]*$name\"" \
      | cut -d'"' -f4
  fi
}

download() {
  local url="$1" dest="$2"
  info "Downloading $(basename "$dest")..."
  curl -fsSL "$url" -o "$dest"
}

# --- Pre-flight --------------------------------------------------------

[[ "$(uname -s)" == "Linux" ]] || die "Linux only. Download from $RELEASE_URL"

INSTALL_DIR="${1:-$DEFAULT_DIR}"
mkdir -p "$INSTALL_DIR"

# --- Fetch release assets ----------------------------------------------

info "Fetching latest release..."
BINARY_URL=$(fetch_asset_url "$BINARY")  || true
CONFIG_URL=$(fetch_asset_url "config.example.json") || true

[[ -n "$BINARY_URL" ]] || die "Could not find $BINARY. Check $RELEASE_URL"

download "$BINARY_URL" "$INSTALL_DIR/$BINARY"
chmod +x "$INSTALL_DIR/$BINARY"

[[ -n "$CONFIG_URL" ]] && download "$CONFIG_URL" config.example.json

if [[ ! -f config.json && -f config.example.json ]]; then
  cp config.example.json config.json
  info "Created config.json — edit it to configure your targets."
fi

# --- PATH guidance -----------------------------------------------------

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  rc=""
  [[ -f "$HOME/.bashrc" ]] && rc="$HOME/.bashrc"
  [[ -f "$HOME/.zshrc"  ]] && rc="$HOME/.zshrc"

  info ""
  info "Installed: $INSTALL_DIR/$BINARY"
  info ""
  info "Add it to your PATH:"
  if [[ -n "$rc" ]]; then
    info "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $rc"
    info "  source $rc"
  else
    info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  fi
else
  info ""
  info "Installed: $INSTALL_DIR/$BINARY"
fi

info ""
info "Edit config.json, then run:"
info "  kuma-proxy-checker -c config.json"
