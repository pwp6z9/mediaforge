# MediaForge Python Sidecar

Complete Python sidecar implementation for MediaForge, a unified media management desktop app built with Tauri + Svelte.

## Architecture

The sidecar communicates with Tauri via **JSON-RPC over stdin/stdout**, enabling seamless cross-process communication for media indexing, metadata management, face recognition, and file system monitoring.

## Directory Structure

```
sidecar/
├── core/
│   ├── __init__.py           # Package initialization
│   ├── models.py             # Data classes (FileRecord, PerformerRecord, etc.)
│   ├── config.py             # YAML configuration manager
│   ├── db.py                 # SQLite database manager (media.db + faces.db)
│   ├── file_classifier.py    # File type detection (extensions + magic bytes)
│   ├── metadata_engine.py    # Metadata extraction/writing (audio/video/image)
│   ├── face_engine.py        # Face detection/recognition (face_recognition + OpenCV)
│   ├── api_client.py         # External API clients with rate limiting
│   ├── rules.py              # Watch rule engine with action execution
│   ├── watcher.py            # File system watcher (watchdog-based)
│   └── indexer.py            # Library indexer with multi-threaded scanning
├── main.py                   # JSON-RPC entry point
└── requirements.txt          # Python dependencies
```

## Components

### 1. Models (`core/models.py`)
Data classes for all entity types:
- **FileRecord**: Media file with full metadata (id, path, title, artist, duration, resolution, etc.)
- **PerformerRecord**: Performer profile (name, attributes, notes)
- **PersonRecord**: Person for face recognition
- **FaceEncoding**: Face embedding vector with source
- **FaceEncounter**: Face detection result in a file
- **WatchRule**: Rule definition with match conditions and actions
- **SentryLogEntry**: File system watcher event log
- **SidecarRequest/Response**: JSON-RPC protocol types

All include `to_dict()` methods for serialization.

### 2. Configuration (`core/config.py`)
- **ConfigManager**: Load/save YAML configuration
- Auto-creates default config if missing
- Dotted key access (e.g., `config.get('api_keys.tmdb')`)
- Supports all settings: NSFW mode, library folders, watch folders, API keys, rules, face detection, thumbnails, theme

### 3. Database (`core/db.py`)
Two SQLite databases:

**media.db**
- `files`: Full file metadata with 37 fields
- `performers`: Performer profiles
- `file_performers`: Many-to-many linking
- `tags`: Flexible tagging
- `folder_meta`: Folder scan metadata
- `files_fts`: FTS5 full-text search virtual table
- Triggers: Auto-sync FTS5 on insert/update/delete
- Indexes: file_type, artist, studio, year, rating, content_mode, tags

**faces.db**
- `people`: Person profiles
- `face_encodings`: 128-d NumPy encodings as BLOB
- `face_encounters`: Detection results per file
- Indexes: person_id, file_path

### 4. File Classification (`core/file_classifier.py`)
- **Extension mapping**: 8 audio, 10 video, 8 image types
- **Magic bytes detection**: MP3, MKV, MP4, PNG, JPEG fallback
- **Stability checking**: Poll file size over 0.5s (for Sentry)
- **MD5 hashing**: Chunked reading for large files

### 5. Metadata Engine (`core/metadata_engine.py`)
**Audio (via mutagen)**
- MP3 (ID3), FLAC, M4A, OGG, Opus, WAV, AIFF
- Reads: title, artist, album, genre, year, duration
- Writes: Full tag support

**Video (via ffprobe + ffmpeg)**
- Reads: ffprobe JSON parse (duration, resolution, codec, director)
- Writes: ffmpeg -metadata with atomic swap

**Image (via PIL)**
- Reads: EXIF data
- Writes: PNG metadata / Pillow EXIF

**Thumbnails**
- Video: ffmpeg frame extraction at 10s mark, scaled to 256x256
- Image: PIL thumbnail with LANCZOS resampling

### 6. Face Engine (`core/face_engine.py`)
- **Library**: face_recognition + OpenCV
- **Extraction**: Per-image or per-video (sampled by FPS)
- **Deduplication**: Distance-based clustering (0.4 threshold)
- **Matching**: Euclidean distance vs known encodings
- **Database**: Store/retrieve 128-d NumPy arrays as BLOB
- **Threshold**: Configurable (default 0.6)
- **Fallback**: Graceful degradation if libraries unavailable

### 7. API Clients (`core/api_client.py`)
Rate-limited token bucket per API:

| API | Rate | Purpose |
|-----|------|---------|
| **StashDB** | Unlimited | Scene/performer metadata (GraphQL) |
| **TMDB** | 50 req/s | Movie/TV metadata |
| **OMDB** | 100 req/min | Detailed movie info |
| **MusicBrainz** | 1 req/s | Audio metadata (strict) |
| **AcoustID** | 3 req/s | Audio fingerprinting |

All use `urllib.request` (no dependencies). Return `{success, data, error}` dict.

### 8. Rule Engine (`core/rules.py`)
**Matching**: file_type, extension, duration, studio, title pattern, content_mode

**Actions**:
- `copy_to`: Copy with conflict resolution
- `move_to`: Move with conflict resolution
- `notify`: Return notification dict
- `generate_thumbnail`: Extract and save
- `detect_faces`: Run face matching

**Path interpolation**: `{person_name}`, `{year}`, `{month}`, `{filename}`, `{artist}`, `{album}`, `{title}`

**Conflict resolution**: skip, overwrite, rename_increment (_001, _002, etc.)

### 9. File Watcher (`core/watcher.py`)
- **Library**: watchdog (with polling fallback for NAS)
- **Event**: on_created → classify → match rules → execute
- **Stability**: Waits for file size to stabilize before processing
- **Undo queue**: Track last 50 actions (copy/move) with atomic reversal
- **Thread-safe**: Lock around state
- **Status**: Returns watching, folder_count, processed_count, error_count, queue_size

### 10. Library Indexer (`core/indexer.py`)
- **Scanning**: Recursive walk with filtering
- **Threading**: ThreadPoolExecutor (4 workers)
- **Progress**: Track total, processed, errors, current_file
- **Incremental**: Skip if path exists and modified_at unchanged
- **Metadata extraction**: Full read_metadata pipeline
- **Thumbnails**: Auto-generate and store
- **Face DB**: Build from `/People/*/*.jpg` samples
- **Cancellation**: Flag-based cancellation support

## JSON-RPC API

### Request Format
```json
{
  "id": "request-id",
  "method": "method_name",
  "params": { "key": "value" }
}
```

### Response Format
```json
{
  "id": "request-id",
  "result": { "data": "..." },
  "error": null
}
```

### Methods

#### Core
- `ping` → `{pong: true, version: '1.0.0'}`
- `get_config` → Full config dict
- `set_config(key, value)` → `{success: bool}`
- `get_stats` → `{total_files, total_size_mb, total_performers, file_types: {}}`
- `get_face_stats` → `{total_people, total_encodings}`

#### Metadata
- `read_metadata(path)` → `{success, data: {...}}`
- `write_metadata(path, metadata)` → `{success, error}`
- `extract_thumbnail(path, output_path, size)` → `{success, path}`

#### Search & Retrieval
- `search_files(query, filters, limit, offset)` → `{results: [...], total: int}`
- `get_file(path)` → FileRecord dict
- `get_performer(name)` → PerformerRecord dict
- `upsert_performer(data)` → `{success, id}`

#### Library Management
- `scan_library(path, recursive)` → `{job_id: '...'}`
- `index_progress` → `{total, processed, errors, current_file}`
- `build_face_db(people_folder)` → `{job_id: '...'}`

#### File Watching (Sentry)
- `start_sentry` → `{success}`
- `stop_sentry` → `{success}`
- `sentry_status` → `{watching, folder_count, processed_count, error_count, queue_size}`
- `undo_last` → `{success, action}`

#### External APIs
- `lookup_api(api, query, params)` → `{success, data, error}`
  - API options: stashdb, tmdb, omdb, musicbrainz, acoustid

### Events (Async)
Events sent from sidecar to Tauri:
```json
{
  "id": null,
  "event": "event_name",
  "data": { "..." }
}
```

- `index_progress`: `{total, processed, errors, current_file}`
- `index_event`: `{timestamp, action, file_path, destination, status, message}`
- `sentry_event`: Same as index_event

## Dependencies

```
mutagen>=1.47.0           # Audio metadata
PyYAML>=6.0.1            # Config files
watchdog>=4.0.0          # File system monitoring
face_recognition>=1.3.0  # Face detection
numpy>=1.24.0            # Numerical arrays
opencv-python-headless>=4.8.0  # Image processing
Pillow>=10.0.0           # Image I/O
```

Optional (system):
- ffmpeg / ffprobe (video processing)
- libsqlite3 (Python stdlib)

## Running

```bash
cd sidecar
pip install -r requirements.txt

# Run sidecar
python3 main.py
```

Tauri communicates via stdin/stdout with JSON-RPC line protocol.

## Implementation Notes

### Error Handling
- All functions return error-safe dicts (`{success, error, data}`)
- Optional dependencies (face_recognition, cv2) degrade gracefully
- Exceptions logged to stderr, not crash

### Performance
- FTS5 for text search (2-3x faster than LIKE)
- Multi-threaded indexing (4 workers)
- Deduplication of face encodings
- Chunked MD5 for large files
- Rate limiting to prevent API throttling

### Thread Safety
- Lock around file watcher state
- Thread pool for indexing
- RateLimiter uses lock for token bucket

### Testing
All components validated:
- ✓ Imports work
- ✓ Config load/save/get/set
- ✓ Database init with FTS5 + triggers
- ✓ File classification accuracy
- ✓ Metadata extraction fallbacks
- ✓ JSON-RPC protocol
- ✓ Rate limiting (no crashes under load)
- ✓ Models serialize correctly

## Future Enhancements
- S3 support for remote files
- Caching layer for metadata
- Batch operations API
- Webhook notifications
- Streaming file upload
