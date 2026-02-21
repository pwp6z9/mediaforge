# MediaForge

A unified, intelligent media management system for organizing, discovering, and managing your entire digital media library. Built with Tauri (Rust + Svelte) and a Python backend for high-performance media processing.

## Features

- **Unified Media Management**: Organize photos, videos, music, documents, and archives in one place
- **Intelligent Organization**: Auto-organization rules based on metadata, content analysis, and face detection
- **NSFW Detection**: Optional NSFW mode with content filtering
- **Metadata Integration**: Support for StashDB, TMDB, OMDB, MusicBrainz, and AcoustID APIs
- **Sentry Mode**: Real-time file watching and auto-organization
- **Face Detection**: Optional facial recognition for photo organization
- **Thumbnail Generation**: Fast, cached thumbnail generation for performance
- **Duplicate Detection**: Smart duplicate detection and conflict resolution
- **Cross-Platform**: Windows, macOS, and Linux support

## Prerequisites

Before building or running MediaForge, ensure you have:

- **Node.js** 18.0.0 or later
- **Rust** 1.77.2 or later (install from https://rustup.rs/)
- **Python** 3.11.0 or later
- **System dependencies**:
  - Ubuntu/Debian: `sudo apt-get install libssl-dev libgit2-dev libxcb-render0-dev libxcb-shape0-dev libxcb-xfixes0-dev`
  - macOS: Xcode Command Line Tools (`xcode-select --install`)
  - Windows: Visual Studio Build Tools or Visual Studio Community

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-repo/mediaforge.git
cd mediaforge
```

2. Install Node dependencies:
```bash
npm install
```

3. Set up Python virtual environment:
```bash
cd sidecar
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

4. Start development server:
```bash
npm run tauri:dev
```

This will start:
- Vite dev server on http://localhost:5173
- Tauri application with hot-reload
- Python sidecar process for backend operations

## Build

### Development Build
```bash
npm run tauri:build
```

### Platform-Specific Builds

**Linux**:
```bash
npm run tauri:build -- --target x86_64-unknown-linux-gnu
```

**macOS**:
```bash
npm run tauri:build -- --target aarch64-apple-darwin  # Apple Silicon
npm run tauri:build -- --target x86_64-apple-darwin   # Intel
```

**Windows**:
```bash
npm run tauri:build -- --target x86_64-pc-windows-msvc
```

## Architecture

MediaForge uses a modern multi-process architecture:

```
┌─────────────────────────────────────────┐
│     Svelte UI (Frontend)                │
│     - React to user interactions        │
│     - Display results and progress      │
└──────────────┬──────────────────────────┘
               │
    Tauri IPC  │  JSON-RPC Protocol
               │
┌──────────────▼──────────────────────────┐
│     Tauri Window (Rust Backend)         │
│     - Command handling                  │
│     - File dialogs                      │
│     - System tray integration           │
└──────────────┬──────────────────────────┘
               │
     Stdout/   │  JSONL Messages
     Stdin     │
┌──────────────▼──────────────────────────┐
│     Python Sidecar Process              │
│     - Media file processing             │
│     - Metadata extraction               │
│     - Face detection                    │
│     - Thumbnail generation              │
│     - API integrations                  │
└─────────────────────────────────────────┘
```

### Frontend (Svelte)
- UI components for media library management
- Real-time progress updates
- File drag-and-drop support
- Settings and configuration interface

### Backend (Rust + Tauri)
- Cross-platform native window management
- File system dialogs
- System tray integration
- IPC command routing to Python sidecar
- Configuration management

### Sidecar (Python)
- Media file parsing and analysis
- Metadata extraction (EXIF, ID3, etc.)
- Face detection and recognition
- Thumbnail generation
- External API integrations
- Database management

## Configuration

Configuration is stored in `data/config.yaml`. Key settings:

```yaml
# Enable NSFW content filtering
nsfw_mode: false

# Watch folders for automatic organization
watch_folders: []

# Library folders to index
library_folders: []

# Conflict resolution strategy (rename_increment, overwrite, skip)
conflict_resolution: rename_increment

# API Keys for external services
api_keys:
  stashdb: ''
  tmdb: ''
  omdb: ''

# Face detection settings
face_detection:
  enabled: true
  threshold: 0.6
```

## API Configuration

### StashDB
For adult content metadata enrichment:
1. Visit https://stashdb.org/settings/api
2. Generate an API key
3. Add to `api_keys.stashdb` in config

### TMDB (Movies/TV Shows)
1. Sign up at https://www.themoviedb.org/settings/api
2. Get your API key
3. Add to `api_keys.tmdb` in config

### OMDB (General Metadata)
1. Visit https://www.omdbapi.com/apikey.aspx
2. Choose a plan and get key
3. Add to `api_keys.omdb` in config

### MusicBrainz & AcoustID
No registration required, but AcoustID needs a client ID:
1. Visit https://acoustid.org/api/
2. Register an application
3. Add `acoustid_client` to config

## NSFW Mode

When enabled, MediaForge will:
- Filter adult content from general searches
- Provide separate adult-oriented metadata sources (StashDB, Adult DBs)
- Flag suspicious content based on confidence thresholds
- Enable additional privacy protections

To enable:
1. Set `nsfw_mode: true` in `data/config.yaml`
2. (Optional) Configure StashDB API key for enhanced metadata

## Development Commands

- `npm run dev` - Start Vite dev server (frontend only)
- `npm run build` - Build frontend for production
- `npm run preview` - Preview production build
- `npm run tauri:dev` - Full development environment with Tauri
- `npm run tauri:build` - Build full desktop application

## Project Structure

```
mediaforge/
├── src/                      # Frontend (Svelte + TypeScript)
│   ├── lib/                  # Reusable components and utilities
│   ├── routes/               # Page routes
│   └── app.svelte            # Root component
├── src-tauri/               # Tauri backend (Rust)
│   ├── src/
│   │   ├── main.rs          # Entry point
│   │   ├── commands.rs      # IPC command handlers
│   │   ├── sidecar.rs       # Python process management
│   │   └── tray.rs          # System tray integration
│   ├── tauri.conf.json      # Tauri configuration
│   └── Cargo.toml           # Rust dependencies
├── sidecar/                 # Python backend
│   ├── main.py              # Entry point
│   ├── core/                # Core processing modules
│   └── requirements.txt      # Python dependencies
├── data/                    # Runtime data (config, db, cache)
│   └── config.yaml          # Configuration file
└── README.md                # This file
```

## Troubleshooting

### Python sidecar won't start
- Ensure Python 3.11+ is installed and in PATH
- Check that sidecar/requirements.txt dependencies are installed
- Look for error messages in terminal or `data/logs/`

### Tauri app won't build
- Update Rust: `rustup update`
- Ensure all system dependencies are installed
- Delete `src-tauri/target/` and try again
- Check Tauri docs: https://tauri.app/v1/guides/getting-started/prerequisites

### Media files not being recognized
- Verify file permissions are readable
- Check `data/logs/` for processing errors
- Ensure file extensions are supported

### High memory usage with large libraries
- Reduce `thumbnail_cache_size` in config
- Increase `watch_interval` to reduce file watching frequency
- Disable face detection if not needed

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MediaForge is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- Built with [Tauri](https://tauri.app/) for cross-platform desktop support
- [Svelte](https://svelte.dev/) for the modern reactive UI framework
- [Rust](https://www.rust-lang.org/) for performance and safety
- Community-maintained media processing libraries

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/your-repo/mediaforge/issues
- Discussions: https://github.com/your-repo/mediaforge/discussions
- Documentation: https://mediaforge.dev/docs

---

**Happy organizing!** MediaForge makes media management effortless.
