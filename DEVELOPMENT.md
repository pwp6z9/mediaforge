# MediaForge Development Guide

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/mediaforge.git
cd mediaforge
npm install
```

### 2. Python Setup

```bash
cd sidecar
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 3. Run Development Server

```bash
npm run tauri:dev
```

This starts:
- Vite on http://localhost:5173
- Tauri app with hot-reload
- Python sidecar process

## Project Structure

```
mediaforge/
├── src/                          # Svelte Frontend
│   ├── app.svelte               # Root component
│   ├── app.postcss              # Global styles
│   ├── routes/                  # SvelteKit pages
│   │   ├── +page.svelte         # Home page
│   │   ├── library/
│   │   │   ├── +page.svelte     # Library view
│   │   │   └── +layout.svelte   # Library layout
│   │   ├── settings/
│   │   │   └── +page.svelte     # Settings page
│   │   └── +layout.svelte       # Root layout
│   └── lib/
│       ├── api.ts               # IPC communication
│       ├── stores/              # Svelte stores
│       │   ├── library.ts
│       │   ├── settings.ts
│       │   └── progress.ts
│       └── components/          # Reusable components
│           ├── Header.svelte
│           ├── MediaGrid.svelte
│           └── ...
├── src-tauri/                   # Rust Backend
│   ├── src/
│   │   ├── main.rs
│   │   ├── commands.rs
│   │   ├── sidecar.rs
│   │   ├── tray.rs
│   │   └── lib.rs
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── build.rs
├── sidecar/                     # Python Backend
│   ├── main.py                  # Entry point
│   ├── core/
│   │   ├── media.py             # Media file handling
│   │   ├── metadata.py          # Metadata extraction
│   │   ├── processor.py         # Processing pipeline
│   │   ├── organizer.py         # File organization
│   │   ├── face_detect.py       # Face detection
│   │   └── api/
│   │       ├── stashdb.py
│   │       ├── tmdb.py
│   │       └── ...
│   ├── requirements.txt
│   └── venv/                    # Virtual environment
├── data/
│   ├── config.yaml              # Configuration
│   ├── mediaforge.db            # SQLite database
│   ├── logs/                    # Log files
│   └── thumbnails/              # Cached thumbnails
├── public/                      # Static assets
├── package.json
├── vite.config.ts
├── svelte.config.js
├── tsconfig.json
└── README.md
```

## Development Workflow

### Making Changes to Frontend

1. Edit files in `src/`
2. Vite automatically hot-reloads
3. Check browser console for errors
4. Commit changes

### Making Changes to Rust Backend

1. Edit files in `src-tauri/src/`
2. App automatically recompiles
3. Check terminal for build errors
4. Commit changes

### Making Changes to Python Sidecar

1. Edit files in `sidecar/`
2. Restart app to pick up changes
3. Check terminal for Python errors
4. Commit changes

## Building

### Linux/macOS

```bash
# Debug build
npm run tauri:build -- --debug

# Release build
npm run tauri:build

# Specific target (macOS)
npm run tauri:build -- --target universal-apple-darwin
```

### Windows

```bash
npm run tauri:build
```

## Testing

### Frontend Unit Tests

```bash
npm run test:svelte
```

### Rust Tests

```bash
cd src-tauri
cargo test
```

### Python Tests

```bash
cd sidecar
pytest
```

### End-to-End Testing

Manual testing checklist:
- [ ] File dialogs open correctly
- [ ] File selection works
- [ ] Library loads and displays
- [ ] Settings are saved
- [ ] File organization completes
- [ ] Thumbnails generate correctly
- [ ] Tray icon works
- [ ] Keyboard shortcuts work
- [ ] Error messages display properly

## Debugging

### Frontend Debugging

```bash
# Browser DevTools
F12  # Open DevTools
Ctrl+Shift+I  # Windows/Linux
Cmd+Option+I  # macOS
```

Console shows:
- JavaScript errors
- Network requests
- Frontend logs

### Rust Backend Debugging

```bash
# Enable debug logging in Tauri
RUST_LOG=debug npm run tauri:dev

# View backtrace on panic
RUST_BACKTRACE=1 npm run tauri:dev
```

### Python Debugging

```bash
# Check stderr output (terminal)
# Python errors appear there

# Add debug logging
python -m pdb sidecar/main.py  # Step through execution
```

## Common Tasks

### Adding a New Frontend Page

1. Create `src/routes/new-page/+page.svelte`
2. Add navigation link in `src/routes/+layout.svelte`
3. Import any necessary stores
4. Style with Tailwind

### Adding a New IPC Command

**Python side** (sidecar/main.py):
```python
def handle_new_command(params):
    # Process request
    return {"result": data}
```

**Rust side** (src-tauri/src/commands.rs):
```rust
#[tauri::command]
pub async fn new_command(
    app: AppHandle,
    param: String,
) -> Result<Value, String> {
    let state = app.state::<SidecarState>();
    call_sidecar(&state, "new_command", json!({ "param": param })).await
}
```

**Frontend** (src/lib/api.ts):
```typescript
export async function newCommand(param: string) {
  return invoke('new_command', { param });
}
```

### Adding External API Integration

1. Create `sidecar/core/api/new_service.py`
2. Implement service class with API key support
3. Add to configuration in `data/config.yaml`
4. Call from appropriate processor

### Adding Configuration Option

1. Update schema in `data/config.yaml`
2. Create settings UI in `src/routes/settings/+page.svelte`
3. Update settings store: `src/lib/stores/settings.ts`
4. Use setting in app logic

## Code Style

### Rust
- Use `cargo fmt` for formatting
- Run `cargo clippy` for linting
- Follow standard Rust naming (snake_case for functions)

### TypeScript/JavaScript
- 2-space indentation
- Use `const` and `let` (no `var`)
- Proper type annotations in TypeScript files
- Use async/await instead of promises

### Python
- 4-space indentation
- Follow PEP 8 style guide
- Use type hints (Python 3.11+)
- Use docstrings for functions

## Git Workflow

### Branch Naming

```
feature/feature-name       # New features
fix/issue-number           # Bug fixes
docs/documentation-name    # Documentation
refactor/area-name         # Refactoring
```

### Commit Messages

```
feat: add new feature
fix: resolve issue with X
docs: update README
refactor: improve performance
test: add test coverage

Format: type: description (lower case, present tense)
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring

## Testing
How to test these changes

## Screenshots (if UI change)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] No new compiler warnings
- [ ] Tests added/updated
- [ ] Documentation updated
```

## Performance Optimization

### Frontend

- Use `<svelte:window>` for event delegation
- Implement virtual scrolling for large lists
- Lazy-load routes with `+page.ts?ssr=false`
- Memoize expensive computations

### Backend (Python)

- Use `multiprocessing.Pool` for parallel tasks
- Cache API responses (1 hour default)
- Batch database operations
- Use generators for large file processing

### Rust

- Profile with `cargo build --release`
- Use `rayon` for parallelization where needed
- Minimize lock contention
- Stream large files instead of buffering

## Troubleshooting

### Tauri app won't start

```bash
# Check Rust build
cd src-tauri && cargo check

# Check frontend build
npm run build

# Check Python
python3 sidecar/main.py
```

### Python sidecar crashing

```bash
# Test sidecar directly
cd sidecar && source venv/bin/activate
python3 main.py
```

### Hot reload not working

- Restart dev server: `Ctrl+C` and `npm run tauri:dev`
- Check vite.config.ts watch settings
- Ensure file changes are saved

### Database locked error

- Close other instances of app
- Delete `data/.db-lock` if exists
- Restart app

## Environment Variables

Create `.env.local` for dev overrides:

```
VITE_API_TIMEOUT=30000
VITE_LOG_LEVEL=debug
TAURI_DEV_HOST=127.0.0.1
```

## Resources

- Tauri Docs: https://tauri.app/
- Svelte Docs: https://svelte.dev/
- Rust Book: https://doc.rust-lang.org/book/
- Python Docs: https://docs.python.org/3/

## Support

For development questions:
1. Check existing documentation
2. Search GitHub issues
3. Ask in discussions
4. Create new issue if needed
