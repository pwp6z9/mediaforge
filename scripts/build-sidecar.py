#!/usr/bin/env python3
"""Build the MediaForge Python sidecar into a standalone binary using PyInstaller.

Usage:
    python scripts/build-sidecar.py

The output binary is placed in src-tauri/binaries/ with the Tauri-required
target-triple suffix so `cargo tauri build` picks it up automatically.
"""
import platform
import subprocess
import shutil
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDECAR_DIR = os.path.join(PROJECT_ROOT, "sidecar")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "src-tauri", "binaries")


def get_target_triple() -> str:
    """Return the Rust-style target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system().lower()

    arch_map = {
        "x86_64": "x86_64", "amd64": "x86_64",
        "aarch64": "aarch64", "arm64": "aarch64",
    }
    arch = arch_map.get(machine, machine)

    if system == "windows":
        return f"{arch}-pc-windows-msvc"
    elif system == "darwin":
        return f"{arch}-apple-darwin"
    elif system == "linux":
        return f"{arch}-unknown-linux-gnu"
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")


def main():
    triple = get_target_triple()
    ext = ".exe" if platform.system().lower() == "windows" else ""
    final_name = f"sidecar-{triple}{ext}"

    print(f"Building sidecar for {triple}...")
    print(f"  Source: {SIDECAR_DIR}/main.py")
    print(f"  Output: {OUTPUT_DIR}/{final_name}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    build_dir = os.path.join(PROJECT_ROOT, "sidecar-build")
    os.makedirs(build_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "sidecar",
        "--distpath", build_dir,
        "--workpath", os.path.join(build_dir, "work"),
        "--specpath", build_dir,
        "--clean",
        os.path.join(SIDECAR_DIR, "main.py"),
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print("PyInstaller build FAILED", file=sys.stderr)
        sys.exit(1)

    src_binary = os.path.join(build_dir, f"sidecar{ext}")
    dst_binary = os.path.join(OUTPUT_DIR, final_name)

    if not os.path.exists(src_binary):
        print(f"Expected binary not found: {src_binary}", file=sys.stderr)
        sys.exit(1)

    shutil.copy2(src_binary, dst_binary)
    os.chmod(dst_binary, 0o755)

    size_mb = os.path.getsize(dst_binary) / (1024 * 1024)
    print(f"\nSidecar built successfully!")
    print(f"  Binary: {dst_binary}")
    print(f"  Size:   {size_mb:.1f} MB")
    print(f"  Triple: {triple}")


if __name__ == "__main__":
    main()
