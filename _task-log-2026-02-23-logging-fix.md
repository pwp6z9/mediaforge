# MediaForge Logging & Bug Fix Task Log
**Date:** 2026-02-23
**Commit:** `e8c4f2d` on `main`
**Pushed to:** https://github.com/pwp6z9/mediaforge

---

## What Was Done

Diagnosed why MediaForge failed to open. Found zero logging infrastructure and 7 critical bugs across Rust, Python, and Svelte layers. Added comprehensive file-based logging throughout the stack and fixed all 7 bugs. Rebuilt frontend, committed on top of existing remote HEAD (`95cc1b3`), and pushed to GitHub.

---

## 7 Bugs Fixed

| # | Layer | File | Issue | Fix |
|---|-------|------|-------|-----|
| 1 | Rust | `main.rs` | No logging anywhere — crashes silent | Added `init_logging()` with file + console output to `~/.mediaforge/logs/` |
| 2 | Rust | `main.rs` | `.expect()` calls cause silent panics | Replaced with `match` blocks + graceful error handling + crash.log |
| 3 | Rust | `sidecar.rs` | No Windows `.exe` path for sidecar binary | Added `cfg!(target_os = "windows")` conditional |
| 4 | Rust | `sidecar.rs` | Sidecar stderr inherited (lost) | Piped stderr + dedicated reader thread routing to Rust logger |
| 5 | Python | `metadata_engine.py` | `from mutagen.oggtheorav import OggTheoraV` — module doesn't exist | Removed non-existent `OggTheoraV` and `OggFLAC` imports |
| 6 | Python | `watcher.py` | `self.metadata_engine.file_classifier.is_stable()` — MetadataEngine has no `file_classifier` | Created local `FileClassifier()` instance in `_wait_for_stable()` |
| 7 | Frontend | `App.svelte` | Dead-end error screen with no retry | Added 5-attempt retry with linear backoff, spinner, error display, retry button |

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/build-sidecar.py` | PyInstaller build script with auto target-triple detection for Tauri bundling |
| `sidecar/_task-log.md` | Sub-agent task log from Python fix phase |
| `_task-log-2026-02-23-logging-fix.md` | This file |

## Files Modified

| File | Changes |
|------|---------|
| `.gitignore` | Added `sidecar-build/`, `vite.config.ts.timestamp-*.mjs` |
| `src-tauri/Cargo.toml` | Added `log`, `env_logger`, `chrono`, `dirs` dependencies |
| `src-tauri/src/main.rs` | Complete rewrite with logging + graceful error handling |
| `src-tauri/src/sidecar.rs` | Complete rewrite with logging, Windows fix, stderr capture |
| `src-tauri/src/tray.rs` | Added `use log::{info, warn};` |
| `src-tauri/src/commands.rs` | Added `use log::{debug, info, error};` |
| `sidecar/main.py` | Added `setup_logging()` with RotatingFileHandler |
| `sidecar/core/metadata_engine.py` | Removed 2 bad import lines |
| `sidecar/core/watcher.py` | Rewrote `_wait_for_stable()` method |
| `src/App.svelte` | Added retry logic, connection state, error UI |

---

## Decisions Made on My Behalf

- **Logging location**: `~/.mediaforge/logs/` && `./logs/` in project dir && stdout only — chose `~/.mediaforge/logs/` because it persists across installs and matches existing config dir convention.
- **Rust logging crate**: `env_logger` + `log` && `tracing` && `slog` — chose `env_logger` for simplicity and zero-config; tracing is overkill for current scale.
- **Python log rotation**: `RotatingFileHandler(5MB, 3 backups)` && `TimedRotatingFileHandler` && no rotation — chose size-based rotation because media processing can be chatty; time-based doesn't cap disk usage.
- **Sidecar stderr handling**: dedicated reader thread && async tokio task && inherited to parent — chose dedicated thread because sidecar.rs already uses std::thread for the stdout reader; consistency wins.
- **Frontend retry strategy**: 5 attempts × linear backoff (1.5s × i) && exponential backoff && fixed interval — chose linear for faster recovery on typical slow-start scenarios without overwhelming a dead backend.
- **Git merge strategy**: rebase local onto remote && force push local && merge with conflict resolution — chose `reset --hard origin/main` + re-apply fixes because local had divergent root commit; cleanest path.
- **OggTheoraV removal**: delete import entirely && replace with try/except && add as optional — chose delete because OggTheoraV doesn't exist in mutagen at all; it's a typo, not an optional feature.

---

## Installer Status

Tauri handles all installers via `cargo tauri build` with `"targets": "all"` in `tauri.conf.json`. No custom installer scripts needed. The `"externalBin": ["binaries/sidecar"]` config requires a compiled sidecar binary with target-triple suffix — handled by `scripts/build-sidecar.py`.

**To build for release:**
```bash
python scripts/build-sidecar.py   # Compile Python sidecar
cargo tauri build                  # Build app + installers
```

---

## API Key Configuration

Keys are stored in `~/.mediaforge/config.yaml` (never in source). Supported APIs: StashDB, TMDB, OMDB, AcoustID. The Settings UI allows in-app key entry. `.env.example` has empty placeholders for reference. No credentials found hardcoded anywhere.

---

## Validation Results

| Check | Result |
|-------|--------|
| Python py_compile (all 11 sidecar files) | PASS |
| Frontend `npm run build` | PASS (a11y warnings only) |
| Rust source review (no cargo in VM) | Manual review PASS |
| Git push to GitHub | PASS (`95cc1b3..e8c4f2d`) |
| Token cleaned from git remote | PASS |

---

## Issues Flagged for Review

1. **No compiled sidecar binary exists** — `scripts/build-sidecar.py` is ready but needs to be run on the target platform with PyInstaller installed. Run `pip install pyinstaller && python scripts/build-sidecar.py` before `cargo tauri build`.
2. **Rust compilation not tested** — VM has no Rust toolchain. Run `cargo check` locally to verify the new deps and rewrites compile.
3. **CI/CD pipeline** — The existing GitHub Actions workflow (from earlier commits) may need updating to install the new Cargo deps and run the sidecar build step.
4. **Settings.svelte a11y warnings** — 3 `a11y_label_has_associated_control` warnings in the build output. Non-blocking but should be cleaned up.

---

## CI/CD Build Results

**Run:** https://github.com/pwp6z9/mediaforge/actions/runs/22292372241
**Release:** https://github.com/pwp6z9/mediaforge/releases/tag/build-43e4bf2

| Platform | Job | Result | Duration |
|----------|-----|--------|----------|
| Linux (ubuntu-22.04) | build-linux | ✅ SUCCESS | ~10 min |
| Windows (windows-latest) | build-windows | ✅ SUCCESS | ~10 min |
| Release | release | ✅ SUCCESS | auto |

### Release Artifacts

| File | Size | Format |
|------|------|--------|
| `MediaForge_0.1.0_x64-setup.exe` | 10.2 MB | NSIS installer (Windows) |
| `MediaForge_0.1.0_x64_en-US.msi` | 10.9 MB | MSI installer (Windows) |
| `MediaForge_0.1.0_amd64.AppImage` | 83.1 MB | AppImage (Linux) |
| `MediaForge_0.1.0_amd64.deb` | 8.9 MB | Debian package (Linux) |

### CI/CD Iteration
1. First attempt: `pip --break-system-packages` not supported on GH Actions runner → fixed with fallback pattern
2. Second attempt: All jobs passed, release created automatically

---

## Next Steps

1. Download `MediaForge_0.1.0_x64-setup.exe` from the release and test on Windows
2. Verify the app opens, connects to sidecar, and logs appear in `~/.mediaforge/logs/`
3. Fix a11y warnings in Settings.svelte (low priority)
4. Promote release from pre-release to full release once tested
