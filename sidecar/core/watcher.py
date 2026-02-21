"""File system watcher daemon."""
import os
import threading
import time
from collections import deque
from datetime import datetime
from typing import Callable, Dict, Any, Optional, List
from pathlib import Path
import sys

try:
    from watchdog.observers import Observer
    from watchdog.observers.polling import PollingObserver
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed", file=sys.stderr)


class FileWatcher(FileSystemEventHandler if WATCHDOG_AVAILABLE else object):
    """Watches for new files and processes them."""

    def __init__(self, config, db, metadata_engine, face_engine, rule_engine, event_callback: Callable):
        """Initialize file watcher."""
        super().__init__()
        self.config = config
        self.db = db
        self.metadata_engine = metadata_engine
        self.face_engine = face_engine
        self.rule_engine = rule_engine
        self.event_callback = event_callback

        self.observer = None
        self.watching = False
        self.processed_count = 0
        self.error_count = 0
        self.undo_queue = deque(maxlen=50)
        self.lock = threading.Lock()

    def start(self) -> bool:
        """Start watching configured folders."""
        if not WATCHDOG_AVAILABLE:
            print("Error: watchdog not available", file=sys.stderr)
            return False

        try:
            watch_folders = self.config.get('watch_folders', [])

            if not watch_folders:
                print("No watch folders configured", file=sys.stderr)
                return False

            # Try regular observer first, fall back to polling
            try:
                self.observer = Observer()
            except Exception:
                print("Falling back to polling observer", file=sys.stderr)
                self.observer = PollingObserver(timeout=10)

            for folder in watch_folders:
                if os.path.exists(folder):
                    self.observer.schedule(self, folder, recursive=True)
                    print(f"Watching: {folder}", file=sys.stderr)

            self.observer.start()
            self.watching = True
            return True

        except Exception as e:
            print(f"Error starting watcher: {e}", file=sys.stderr)
            return False

    def stop(self) -> bool:
        """Stop watching."""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
            self.watching = False
            return True
        except Exception as e:
            print(f"Error stopping watcher: {e}", file=sys.stderr)
            return False

    def on_created(self, event):
        """Handle file creation event."""
        if event.is_directory:
            return

        file_path = event.src_path

        # Wait for file to stabilize
        if not self._wait_for_stable(file_path):
            return

        self.process_file(file_path)

    def _wait_for_stable(self, file_path: str, timeout: float = 30) -> bool:
        """Wait for file to stabilize."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if self.metadata_engine.file_classifier.is_stable(file_path, 0.5):
                    return True
            except Exception:
                pass

            time.sleep(0.5)

        return False

    def process_file(self, file_path: str) -> bool:
        """Process a single file."""
        try:
            with self.lock:
                # Classify file
                from .file_classifier import FileClassifier
                classifier = FileClassifier()
                classification = classifier.classify(file_path)

                if classification['file_type'] == 'unknown':
                    self.error_count += 1
                    return False

                # Check for duplicates
                existing = self.db.get_file(file_path)
                if existing and existing.hash_md5:
                    # Could check duplicate by hash here
                    pass

                # Extract metadata
                metadata = self.metadata_engine.read_metadata(file_path)

                # Build file info dict
                file_info = {
                    'path': file_path,
                    'filename': os.path.basename(file_path),
                    'extension': classification['extension'],
                    'file_type': classification['file_type'],
                    'size_bytes': classification['size_bytes'],
                }

                # Evaluate rules
                matched_rules = self.rule_engine.evaluate(file_info, metadata)

                # Execute matched rules
                for rule in matched_rules:
                    context = {
                        'filename': os.path.basename(file_path),
                        'person_name': metadata.get('artist', ''),
                        'year': metadata.get('year', ''),
                        'artist': metadata.get('artist', ''),
                        'album': metadata.get('album', ''),
                        'title': metadata.get('title', ''),
                        'face_engine': self.face_engine,
                    }

                    results = self.rule_engine.execute_rule(rule, file_path, context)

                    # Log actions
                    for result in results:
                        log_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'action': result.get('action_type'),
                            'file_path': file_path,
                            'destination': result.get('destination', ''),
                            'person_name': context.get('person_name', ''),
                            'rule_name': rule.name,
                            'status': 'success' if result.get('success') else 'error',
                            'message': result.get('error', '')
                        }

                        self.event_callback(log_entry)

                        if result.get('success') and result.get('destination'):
                            # Track undo info
                            undo_entry = {
                                'action': result.get('action_type'),
                                'src': file_path,
                                'dst': result.get('destination'),
                                'timestamp': datetime.now().isoformat()
                            }
                            self.undo_queue.append(undo_entry)

                self.processed_count += 1
                return True

        except Exception as e:
            self.error_count += 1
            print(f"Error processing file {file_path}: {e}", file=sys.stderr)
            return False

    def undo_last(self) -> Dict[str, Any]:
        """Undo the last action."""
        with self.lock:
            if not self.undo_queue:
                return {'success': False, 'error': 'Nothing to undo'}

            undo_entry = self.undo_queue.pop()
            action = undo_entry['action']
            src = undo_entry['src']
            dst = undo_entry['dst']

            try:
                if action == 'copy_to':
                    # Just delete the copy
                    if os.path.exists(dst):
                        os.unlink(dst)
                    return {'success': True, 'action': action}

                elif action == 'move_to':
                    # Move back
                    if os.path.exists(dst):
                        import shutil
                        shutil.move(dst, src)
                    return {'success': True, 'action': action}

                return {'success': False, 'error': 'Unknown action'}

            except Exception as e:
                return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get watcher status."""
        with self.lock:
            return {
                'watching': self.watching,
                'folder_count': len(self.config.get('watch_folders', [])),
                'processed_count': self.processed_count,
                'error_count': self.error_count,
                'queue_size': len(self.undo_queue)
            }
