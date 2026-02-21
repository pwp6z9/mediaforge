#!/bin/bash
# MediaForge Linux Setup Script
# Run as: bash scripts/setup-linux.sh
#
# Prerequisites: Git, Node.js 20+, Python 3.11+
# This script installs system deps, Rust, and builds MediaForge on Ubuntu/Debian.

set -e

echo ""
echo "===== MediaForge Linux Build Setup ====="
echo ""

# ---- Install system dependencies ----
echo "Installing system dependencies (requires sudo)..."
sudo apt-get update
sudo apt-get install -y \
    libgtk-3-dev \
    libwebkit2gtk-4.1-dev \
    libjavascriptcoregtk-4.1-dev \
    libsoup-3.0-dev \
    librsvg2-dev \
    libayatana-appindicator3-dev \
    pkg-config \
    python3 \
    python3-pip \
    python3-yaml \
    python3-numpy \
    curl \
    build-essential
echo "[OK] System deps installed"

# ---- Install Rust if missing ----
if ! command -v cargo &> /dev/null; then
    echo ""
    echo "Installing Rust toolchain..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi
echo "[OK] Rust $(rustc --version)"

# ---- Install Python sidecar deps ----
echo ""
echo "Installing Python dependencies..."
pip install pyinstaller pyyaml numpy --break-system-packages --quiet 2>/dev/null || \
    pip install pyinstaller pyyaml numpy --quiet
echo "[OK] Python deps installed"

# ---- Install Node.js deps ----
echo ""
echo "Installing frontend dependencies..."
npm ci
echo "[OK] npm deps installed"

# ---- Run tests ----
echo ""
echo "Running Python sidecar tests..."
python3 tests/test_sidecar.py
echo "[OK] Tests passed"

# ---- Build Python sidecar ----
echo ""
echo "Building Python sidecar binary..."
mkdir -p src-tauri/binaries
cd sidecar
pyinstaller --onefile --name sidecar main.py
cp dist/sidecar ../src-tauri/binaries/sidecar-x86_64-unknown-linux-gnu
chmod +x ../src-tauri/binaries/sidecar-x86_64-unknown-linux-gnu
cd ..
echo "[OK] Sidecar built"

# ---- Build frontend ----
echo ""
echo "Building frontend..."
npm run build
echo "[OK] Frontend built"

# ---- Build Tauri app ----
echo ""
echo "Building Tauri desktop app (this takes a few minutes)..."
npx tauri build

echo ""
echo "===== Build Complete! ====="
echo "DEB:      src-tauri/target/release/bundle/deb/"
echo "AppImage: src-tauri/target/release/bundle/appimage/"
echo ""
