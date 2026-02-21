"""Data models for MediaForge."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class FileRecord:
    """Represents a media file in the library."""
    id: str
    path: str
    filename: str
    extension: str
    file_type: str  # audio, video, image, unknown
    content_mode: str = ""
    size_bytes: int = 0
    modified_at: str = ""
    indexed_at: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    album_artist: str = ""
    genre: str = ""
    year: int = 0
    duration_seconds: float = 0.0
    director: str = ""
    studio: str = ""
    cast_list: List[str] = field(default_factory=list)
    synopsis: str = ""
    rating: float = 0.0
    season: int = 0
    episode: int = 0
    resolution: str = ""
    codec: str = ""
    bitrate: str = ""
    positions: List[Dict[str, Any]] = field(default_factory=list)
    acts: List[Dict[str, Any]] = field(default_factory=list)
    scene_setting: str = ""
    series_name: str = ""
    scene_number: int = 0
    source_url: str = ""
    camera: str = ""
    gps_lat: float = 0.0
    gps_lon: float = 0.0
    thumbnail_path: str = ""
    hash_md5: str = ""
    favorite: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PerformerRecord:
    """Represents a performer in the library."""
    id: str
    name: str
    hair_color: str = ""
    eye_color: str = ""
    body_type: str = ""
    ethnicity: str = ""
    chest_type: str = ""
    butt_type: str = ""
    folder_path: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PersonRecord:
    """Represents a person for face recognition."""
    id: str
    name: str
    folder_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FaceEncoding:
    """Represents a face encoding."""
    id: str
    person_id: str
    encoding: bytes
    source_file: str
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding bytes."""
        d = asdict(self)
        d['encoding'] = None  # Can't serialize bytes
        return d


@dataclass
class FaceEncounter:
    """Represents a face detection in a file."""
    id: str
    file_path: str
    person_id: str
    matched: bool
    distance: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WatchRule:
    """Represents a file watch rule."""
    name: str
    match: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SentryLogEntry:
    """Represents a Sentry log entry."""
    timestamp: str
    action: str
    file_path: str
    destination: str = ""
    person_name: str = ""
    rule_name: str = ""
    status: str = ""  # success, error, skipped
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SidecarRequest:
    """Represents a JSON-RPC request from Tauri."""
    id: str
    method: str
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SidecarResponse:
    """Represents a JSON-RPC response to Tauri."""
    id: str
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
