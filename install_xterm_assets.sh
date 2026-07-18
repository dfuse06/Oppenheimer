#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$HOME/Projects/DFUSE-Kernel-Forge}"
ASSET_DIR="$PROJECT_DIR/ui/assets/terminal"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

command -v npm >/dev/null || {
  echo "npm is required. On Arch: sudo pacman -S --needed npm"
  exit 1
}

mkdir -p "$ASSET_DIR"
cd "$TMP_DIR"
npm init -y >/dev/null 2>&1
npm install --silent @xterm/xterm@5.5.0 @xterm/addon-fit@0.10.0

cp node_modules/@xterm/xterm/css/xterm.css "$ASSET_DIR/xterm.css"
cp node_modules/@xterm/xterm/lib/xterm.js "$ASSET_DIR/xterm.js"
cp node_modules/@xterm/addon-fit/lib/addon-fit.js "$ASSET_DIR/addon-fit.js"

echo "xterm.js assets installed in $ASSET_DIR"
