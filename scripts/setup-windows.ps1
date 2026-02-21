# MediaForge Windows Setup Script
# Run as: powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1
#
# Prerequisites: Git, Node.js 20+, Python 3.11+
# This script installs Rust and builds MediaForge on Windows.

$ErrorActionPreference = "Stop"

Write-Host "`n===== MediaForge Windows Build Setup =====" -ForegroundColor Magenta
Write-Host ""

# ---- Check prerequisites ----
function Check-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

if (-not (Check-Command "node")) {
    Write-Host "ERROR: Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Node.js $(node --version)" -ForegroundColor Green

if (-not (Check-Command "python")) {
    Write-Host "ERROR: Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python $(python --version)" -ForegroundColor Green

# ---- Install Rust if missing ----
if (-not (Check-Command "cargo")) {
    Write-Host "`nInstalling Rust toolchain..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile "$env:TEMP\rustup-init.exe"
    & "$env:TEMP\rustup-init.exe" -y --default-toolchain stable
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
}
Write-Host "[OK] Rust $(rustc --version)" -ForegroundColor Green

# ---- Install Python sidecar deps ----
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
pip install pyinstaller pyyaml numpy --quiet
Write-Host "[OK] Python deps installed" -ForegroundColor Green

# ---- Install Node.js deps ----
Write-Host "`nInstalling frontend dependencies..." -ForegroundColor Yellow
npm ci
Write-Host "[OK] npm deps installed" -ForegroundColor Green

# ---- Build Python sidecar ----
Write-Host "`nBuilding Python sidecar binary..." -ForegroundColor Yellow
Push-Location sidecar
pyinstaller --onefile --name sidecar main.py --distpath ..\src-tauri\binaries 2>$null
# Rename to Tauri target triple
$sidecarPath = "..\src-tauri\binaries\sidecar.exe"
$targetPath = "..\src-tauri\binaries\sidecar-x86_64-pc-windows-msvc.exe"
if (Test-Path $sidecarPath) {
    Move-Item -Force $sidecarPath $targetPath
}
Pop-Location
Write-Host "[OK] Sidecar built" -ForegroundColor Green

# ---- Build frontend ----
Write-Host "`nBuilding frontend..." -ForegroundColor Yellow
npm run build
Write-Host "[OK] Frontend built" -ForegroundColor Green

# ---- Build Tauri app ----
Write-Host "`nBuilding Tauri desktop app (this takes a few minutes)..." -ForegroundColor Yellow
npx tauri build

Write-Host "`n===== Build Complete! =====" -ForegroundColor Magenta
Write-Host "Installer: src-tauri\target\release\bundle\nsis\" -ForegroundColor Cyan
Write-Host "MSI:       src-tauri\target\release\bundle\msi\" -ForegroundColor Cyan
Write-Host ""
