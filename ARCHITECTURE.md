# MediaForge Architecture

## Overview

MediaForge is a cross-platform desktop application for unified media management. It uses a modular architecture with clear separation of concerns:

- **Frontend**: Svelte 5 + TypeScript for reactive UI
- **Desktop Runtime**: Tauri 2 for cross-platform window management and OS integration
- **Backend**: Python 3.11+ sidecar for heavy computational work
- **IPC**: JSON-RPC over JSONL for process communication

## Design Principles

1. **Performance First**: Compute-heavy operations in Python subprocess, UI remains responsive
2. **Modularity**: Each component has a single responsibility
3. **Cross-Platform**: Code works identically on Windows, macOS, and Linux
4. **User Privacy**: All processing can be local, no telemetry
5. **Extensibility**: Plugin system for custom organization rules and processors

## Component Architecture

### 1. Frontend (src/)

Svelte 5 application with runes and reactive components.

**Key Directories**:
- `src/routes/` - SvelteKit page routes
- `src/lib/` - Reusable components and utilities
- `src/lib/api.ts` - IPC communication layer
- `src/lib/stores/` - Global state management

**Responsibilities**:
- User interface and interactions
- Real-time progress display
- Settings and configuration UI
- Library browsing and search
- File drag-and-drop handling

**Technologies**:
- Svelte 5 (runes, reactive variables)
- Tailwind CSS (styling)
- TypeScript (type safety)
- Vite (build tool)

### 2. Tauri Backend (src-tauri/src/)

Rust application providing desktop integration.

**Structure**:
```
src-tauri/src/
├── main.rs          # Application entry point
├── commands.rs      # IPC command handlers
├── sidecar.rs       # Python process lifecycle
├── tray.rs          # System tray integration
└── lib.rs           # Library exports
```

**Responsibilities**:
- Window management and rendering
- System tray icon and menu
- File dialogs (open files, folders, save)
- Shell integration (open files in default app)
- Python sidecar process spawning and communication
- IPC message routing

**Key Modules**:

#### main.rs
- Initializes Tauri application
- Sets up plugins and handlers
- Configures system tray
- Starts Python sidecar

#### commands.rs
- `ipc_call`: Routes IPC requests to Python sidecar
- `open_file_dialog`: Shows file picker
- `open_folder_dialog`: Shows folder picker
- `open_in_default`: Opens file with default app

#### sidecar.rs
- `SidecarState`: Manages Python process I/O
- `start_sidecar`: Spawns and connects to Python process
- `call_sidecar`: Routes async calls to Python with request/response correlation
- Message routing with UUID-based request tracking

#### tray.rs
- System tray setup and menu
- Tray icon click handling
- Menu item callbacks

### 3. Python Sidecar (sidecar/)

Backend service handling all media processing.

**Entry Point**: `sidecar/main.py`

**Responsibilities**:
- Media file parsing and analysis
- Metadata extraction (EXIF, ID3, file properties)
- Face detection and recognition
- Thumbnail generation
- Image optimization
- Duplicate detection
- API integrations
- Database management
- File organization and movement
- Rule evaluation and application

**Communication Protocol**:
- Standard input: JSON-RPC 2.0 requests (JSONL format)
- Standard output: JSON responses and events (JSONL format)
- Standard error: Log output (for debugging)

**Request Format**:
```json
{
  "id": "uuid-string",
  "method": "method.name",
  "params": { "param1": "value1" }
}
```

**Response Format**:
```json
{
  "id": "uuid-string",
  "result": { "data": "result" },
  "error": null
}
```

**Event Format**:
```json
{
  "event": "event_name",
  "data": { "details": "..." }
}
```

## IPC Communication Flow

1. **Frontend** initiates action (e.g., "organize library")
2. **Frontend** calls Tauri command via `invoke()` with method name and parameters
3. **Tauri** `ipc_call` command receives request
4. **Tauri** generates UUID and sends JSON-RPC request to Python sidecar
5. **Python** processes request, may emit progress events
6. **Python** sends response with result or error
7. **Tauri** forwards response back to frontend
8. **Frontend** updates UI with result

```
┌─────────────┐
│   Frontend  │
│  invoke()   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Tauri    │
│  ipc_call   │
└──────┬──────┘
       │
   JSON-RPC
   (JSONL)
       │
       ▼
┌─────────────┐
│   Python    │
│   Process   │
└─────────────┘
```

## Media Processing Pipeline

### File Organization

```
User selects files/folders
        │
        ▼
Extract metadata
        │
        ├─ EXIF (images)
        ├─ ID3 (audio)
        ├─ File properties
        └─ File hashes
        │
        ▼
Apply organization rules
        │
        ├─ Filename patterns
        ├─ Folder structures
        └─ API enrichment
        │
        ▼
Check for duplicates
        │
        ├─ Hash comparison
        ├─ Metadata matching
        └─ Conflict resolution
        │
        ▼
Move/Copy files
        │
        ▼
Generate thumbnails
        │
        ▼
Update database
        │
        ▼
Notify frontend
```

### Face Detection

When enabled:
1. Extract images from video frames
2. Run face detection model
3. Generate face embeddings
4. Store face metadata in database
5. Group similar faces for identification
6. Allow user tagging and organization by person

## State Management

### Frontend State (Svelte Stores)

```typescript
// Global state
export const mediaLibrary = writable([])
export const selectedMedia = writable([])
export const organizationRules = writable([])
export const settings = writable({})
export const isProcessing = writable(false)
export const progress = writable(0)
```

### Backend State (Python)

```python
# Configuration
config = load_config()

# Active processes
active_jobs = {}

# Caches
thumbnail_cache = {}
metadata_cache = {}
face_embedding_cache = {}
```

## Event System

### Frontend Events (Tauri emit)

```typescript
// Progress events
emit('progress:update', { current: 100, total: 1000 })

// Completion events
emit('operation:complete', { success: true, message: '...' })

// Error events
emit('error:occurred', { code: 'ERR_001', message: '...' })
```

### Python Events (stdout)

```json
{"event": "progress", "data": {"current": 100, "total": 1000}}
{"event": "file_processed", "data": {"path": "...", "media_type": "image"}}
{"event": "operation_complete", "data": {"status": "success"}}
```

## Configuration

### config.yaml Structure

```yaml
# Application
nsfw_mode: false
theme: dark-pink

# Libraries
library_folders: ["/path/to/library"]
watch_folders: ["/path/to/watch"]

# Processing
parallel_workers: 4
default_action: copy
conflict_resolution: rename_increment

# APIs
api_enabled:
  stashdb: false
  tmdb: false

# Features
face_detection:
  enabled: true
  threshold: 0.6
thumbnails:
  enabled: true
  size: 256
```

## Database Schema

SQLite database stores:

### tables
- `media_files` - File metadata and properties
- `organizations` - File organization history
- `faces` - Detected faces and embeddings
- `duplicates` - Duplicate detection records
- `thumbnails` - Cache metadata
- `api_cache` - External API response cache
- `processing_queue` - Pending operations

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Load media library incrementally
2. **Caching**: Thumbnails, metadata, API responses
3. **Worker Threads**: Python uses multiprocessing for parallel tasks
4. **Database Indexing**: Fast lookups on file paths, hashes
5. **Event Throttling**: Limit UI updates from progress events
6. **Memory Management**: Stream large files instead of loading fully

### Benchmarks (Target Performance)

- Library scan: 10,000 files in <30 seconds
- Thumbnail generation: 500 images in <5 seconds
- Duplicate detection: 10,000 files in <2 minutes
- Face detection: 100 images in <30 seconds

## Security Considerations

### Design

- No network communication without user approval
- API keys stored locally (not transmitted)
- Hash verification for duplicate detection
- User can enable/disable each API individually
- Configuration file includes security settings

### Implementation

- Never log sensitive data (API keys, passwords)
- Use https for external APIs
- Validate all file paths
- Sandboxed Python subprocess
- Clear temporary files after processing

## Extensibility

### Plugin Architecture (Future)

Custom rules and processors:

```python
class CustomOrganizer(Processor):
    def process(self, media_file):
        # Custom logic
        return new_path

class CustomRule(Rule):
    def evaluate(self, media_file):
        # Return True if rule matches
        return condition
```

## Deployment

### Development

```bash
npm run tauri:dev
```

Runs with:
- Vite dev server on port 5173
- Python sidecar from `sidecar/main.py`
- Hot reload for frontend
- Debug logging enabled

### Production

```bash
npm run tauri:build
```

Creates:
- Single executable bundle for target platform
- Embedded Python binary (PyInstaller)
- Bundled resources
- Signed executables (where applicable)
- Installer (Windows MSI, macOS DMG, Linux AppImage)

## Error Handling

### Error Categories

1. **File System**: Permission denied, file not found, disk full
2. **Processing**: Invalid file format, corrupted data
3. **API**: Network error, invalid key, rate limit
4. **Configuration**: Invalid settings, missing required fields

### Error Flow

```
Error occurs in Python
        │
        ▼
Log with context
        │
        ▼
Return error response
        │
        ▼
Tauri forwards to frontend
        │
        ▼
Frontend displays user-friendly message
```

## Testing Strategy

### Unit Tests
- Rust: Cargo tests
- Python: pytest
- TypeScript: Vitest

### Integration Tests
- Frontend + Tauri communication
- Tauri + Python sidecar
- File operations

### E2E Tests
- Full workflow testing
- Multiple platform scenarios

## Future Enhancements

1. **Plugin System**: Allow custom processors
2. **Cloud Sync**: Optional cloud backup
3. **Collaborative Tagging**: Multi-user support
4. **Advanced ML**: Custom trained models
5. **Mobile Companion**: Remote access
6. **Streaming**: Direct playback from library
