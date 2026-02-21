"""Library indexer for building library."""
import os
import uuid
import threading
from typing import Callable, Dict, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .models import FileRecord


class LibraryIndexer:
    """Indexes media library."""

    def __init__(self, db, metadata_engine, face_engine, event_callback: Callable):
        """Initialize indexer."""
        self.db = db
        self.metadata_engine = metadata_engine
        self.face_engine = face_engine
        self.event_callback = event_callback

        self.is_running = False
        self.progress = {
            'total': 0,
            'processed': 0,
            'errors': 0,
            'current_file': ''
        }
        self.lock = threading.Lock()
        self.cancel_flag = False

    def scan_folder(self, path: str, recursive: bool = True, progress_callback: Optional[Callable] = None) -> bool:
        """Scan folder for media files."""
        if not os.path.exists(path):
            return False

        try:
            with self.lock:
                if self.is_running:
                    return False
                self.is_running = True
                self.cancel_flag = False
                self.progress = {
                    'total': 0,
                    'processed': 0,
                    'errors': 0,
                    'current_file': ''
                }

            # Collect all files
            files = []
            for root, dirs, filenames in os.walk(path):
                if self.cancel_flag:
                    break

                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if self._is_media_file(file_path):
                        files.append(file_path)

                if not recursive:
                    break

            with self.lock:
                self.progress['total'] = len(files)

            # Process files
            with ThreadPoolExecutor(max_workers=4) as executor:
                for file_path in files:
                    if self.cancel_flag:
                        break

                    executor.submit(self._process_and_index, file_path, progress_callback)

            return True

        finally:
            with self.lock:
                self.is_running = False

    def _is_media_file(self, path: str) -> bool:
        """Check if file is a media file."""
        from .file_classifier import FileClassifier
        classifier = FileClassifier()
        result = classifier.classify(path)
        return result['file_type'] != 'unknown'

    def _process_and_index(self, path: str, progress_callback: Optional[Callable] = None):
        """Process and index a single file."""
        try:
            record = self.process_file(path)
            self.index_file(record)

            with self.lock:
                self.progress['processed'] += 1
                self.progress['current_file'] = path

            if progress_callback:
                progress_callback(self.progress)

        except Exception as e:
            with self.lock:
                self.progress['errors'] += 1
                self.progress['current_file'] = path
            print(f"Error processing {path}: {e}")

    def process_file(self, path: str) -> FileRecord:
        """Process a single file and extract metadata."""
        from .file_classifier import FileClassifier

        classifier = FileClassifier()
        classification = classifier.classify(path)

        record_id = str(uuid.uuid4())
        filename = os.path.basename(path)
        _, ext = os.path.splitext(filename)

        # Read metadata
        metadata = self.metadata_engine.read_metadata(path)

        # Create file record
        record = FileRecord(
            id=record_id,
            path=path,
            filename=filename,
            extension=ext.lstrip('.').lower(),
            file_type=classification['file_type'],
            size_bytes=classification['size_bytes'],
            modified_at=classification['modified_at'],
            indexed_at=datetime.now().isoformat(),
            title=metadata.get('title', ''),
            artist=metadata.get('artist', ''),
            album=metadata.get('album', ''),
            genre=metadata.get('genre', ''),
            year=metadata.get('year', 0),
            duration_seconds=metadata.get('duration_seconds', 0.0),
            director=metadata.get('director', ''),
            resolution=metadata.get('resolution', ''),
            codec=metadata.get('codec', ''),
            hash_md5=classifier.compute_md5(path)
        )

        # Generate thumbnail
        thumb_dir = os.path.expanduser('~/.mediaforge/thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f'{record_id}.jpg')

        if self.metadata_engine.extract_thumbnail(path, thumb_path):
            record.thumbnail_path = thumb_path

        return record

    def index_file(self, record: FileRecord) -> bool:
        """Index a file record in database."""
        return self.db.upsert_file(record)

    def build_face_db(self, people_folder: str) -> bool:
        """Build face database from People folder."""
        if not os.path.exists(people_folder):
            return False

        try:
            with self.lock:
                if self.is_running:
                    return False
                self.is_running = True
                self.cancel_flag = False

            # Walk People folder
            for person_name in os.listdir(people_folder):
                if self.cancel_flag:
                    break

                person_path = os.path.join(people_folder, person_name)
                if not os.path.isdir(person_path):
                    continue

                # Get sample images
                sample_images = []
                for filename in os.listdir(person_path):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        sample_images.append(os.path.join(person_path, filename))

                if sample_images:
                    self.face_engine.add_person(person_name, person_path, sample_images[:5])

            return True

        finally:
            with self.lock:
                self.is_running = False

    def get_progress(self) -> Dict[str, Any]:
        """Get indexing progress."""
        with self.lock:
            return self.progress.copy()

    def cancel(self) -> None:
        """Cancel indexing."""
        with self.lock:
            self.cancel_flag = True
