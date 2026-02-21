"""MediaForge JSON-RPC sidecar entry point."""
import sys
import json
import os
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional

# Import core modules
from core.config import ConfigManager
from core.db import DatabaseManager
from core.file_classifier import FileClassifier
from core.metadata_engine import MetadataEngine
from core.face_engine import FaceEngine
from core.api_client import ApiClient
from core.rules import RuleEngine
from core.watcher import FileWatcher
from core.indexer import LibraryIndexer
from core.models import SidecarResponse


class MediaForgeSidecar:
    """JSON-RPC sidecar for MediaForge."""

    def __init__(self):
        """Initialize sidecar."""
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.classifier = FileClassifier()
        self.metadata_engine = MetadataEngine()
        self.api_client = ApiClient(self.config)
        self.rule_engine = RuleEngine(self.config)
        self.face_engine = FaceEngine(self.db, self.config.get('face_detection.threshold', 0.6))
        
        self.watcher = None
        self.indexer = None
        self.indexing_jobs = {}
        
        # Load face encodings
        self.face_engine.load_encodings()

    def handle_request(self, request: Dict[str, Any]) -> SidecarResponse:
        """Handle a JSON-RPC request."""
        request_id = request.get('id', '')
        method = request.get('method', '')
        params = request.get('params', {})

        try:
            if method == 'ping':
                result = {'pong': True, 'version': '1.0.0'}

            elif method == 'get_config':
                result = self.config.get_all()

            elif method == 'set_config':
                key = params.get('key')
                value = params.get('value')
                success = self.config.set(key, value)
                result = {'success': success}

            elif method == 'scan_library':
                path = params.get('path')
                recursive = params.get('recursive', True)
                result = self._start_scan(path, recursive)

            elif method == 'index_progress':
                result = self._get_index_progress()

            elif method == 'write_metadata':
                path = params.get('path')
                metadata = params.get('metadata', {})
                result = self.metadata_engine.write_metadata(path, metadata)

            elif method == 'read_metadata':
                path = params.get('path')
                data = self.metadata_engine.read_metadata(path)
                result = {'success': True, 'data': data}

            elif method == 'search_files':
                query = params.get('query', '')
                filters = params.get('filters', {})
                limit = params.get('limit', 50)
                offset = params.get('offset', 0)
                results, total = self.db.search_files(query, filters, limit, offset)
                result = {
                    'results': [r.to_dict() for r in results],
                    'total': total
                }

            elif method == 'get_file':
                path = params.get('path')
                file_record = self.db.get_file(path)
                if file_record:
                    result = file_record.to_dict()
                else:
                    result = None

            elif method == 'get_performer':
                name = params.get('name')
                performer = self.db.get_performer(name)
                if performer:
                    result = performer.to_dict()
                else:
                    result = None

            elif method == 'upsert_performer':
                data = params.get('data', {})
                from core.models import PerformerRecord
                record = PerformerRecord(
                    id=data.get('id', str(uuid.uuid4())),
                    name=data.get('name', ''),
                    hair_color=data.get('hair_color', ''),
                    eye_color=data.get('eye_color', ''),
                    body_type=data.get('body_type', ''),
                    ethnicity=data.get('ethnicity', ''),
                    chest_type=data.get('chest_type', ''),
                    butt_type=data.get('butt_type', ''),
                    folder_path=data.get('folder_path', ''),
                    notes=data.get('notes', '')
                )
                success = self.db.upsert_performer(record)
                result = {'success': success, 'id': record.id}

            elif method == 'get_stats':
                result = self.db.get_stats()

            elif method == 'start_sentry':
                success = self._start_watcher()
                result = {'success': success}

            elif method == 'stop_sentry':
                success = self._stop_watcher()
                result = {'success': success}

            elif method == 'sentry_status':
                if self.watcher:
                    result = self.watcher.get_status()
                else:
                    result = {'watching': False}

            elif method == 'undo_last':
                if self.watcher:
                    result = self.watcher.undo_last()
                else:
                    result = {'success': False, 'error': 'Watcher not active'}

            elif method == 'lookup_api':
                api = params.get('api')
                query = params.get('query')
                api_params = params.get('params', {})
                result = self._lookup_api(api, query, api_params)

            elif method == 'extract_thumbnail':
                path = params.get('path')
                output_path = params.get('output_path')
                size = params.get('size', 256)
                success = self.metadata_engine.extract_thumbnail(path, output_path, size)
                result = {'success': success, 'path': output_path if success else None}

            elif method == 'build_face_db':
                people_folder = params.get('people_folder')
                result = self._start_face_db_build(people_folder)

            elif method == 'get_face_stats':
                stats = self.db.get_stats()
                result = {
                    'total_people': stats.get('total_people', 0),
                    'total_encodings': stats.get('total_encodings', 0)
                }

            else:
                return SidecarResponse(request_id, None, f'Unknown method: {method}')

            return SidecarResponse(request_id, result)

        except Exception as e:
            print(f"Error handling {method}: {e}", file=sys.stderr)
            return SidecarResponse(request_id, None, str(e))

    def _start_scan(self, path: str, recursive: bool) -> Dict[str, Any]:
        """Start a library scan."""
        job_id = str(uuid.uuid4())
        
        self.indexer = LibraryIndexer(self.db, self.metadata_engine, self.face_engine, self._on_index_event)
        
        # Run in background thread
        thread = threading.Thread(target=self.indexer.scan_folder, args=(path, recursive, self._on_index_progress))
        thread.daemon = True
        thread.start()
        
        self.indexing_jobs[job_id] = {
            'started': datetime.now().isoformat(),
            'thread': thread
        }
        
        return {'job_id': job_id}

    def _get_index_progress(self) -> Dict[str, Any]:
        """Get indexing progress."""
        if self.indexer:
            return self.indexer.get_progress()
        return {'total': 0, 'processed': 0, 'errors': 0, 'current_file': ''}

    def _on_index_progress(self, progress: Dict[str, Any]):
        """Called on indexing progress."""
        # Send progress event to frontend
        event = {
            'id': None,
            'event': 'index_progress',
            'data': progress
        }
        self._send_event(event)

    def _on_index_event(self, event: Dict[str, Any]):
        """Called on indexing event."""
        rpc_event = {
            'id': None,
            'event': 'index_event',
            'data': event
        }
        self._send_event(rpc_event)

    def _start_watcher(self) -> bool:
        """Start file system watcher."""
        if self.watcher:
            return True
        
        try:
            self.watcher = FileWatcher(
                self.config,
                self.db,
                self.metadata_engine,
                self.face_engine,
                self.rule_engine,
                self._on_sentry_event
            )
            return self.watcher.start()
        except Exception as e:
            print(f"Error starting watcher: {e}", file=sys.stderr)
            return False

    def _stop_watcher(self) -> bool:
        """Stop file system watcher."""
        if self.watcher:
            success = self.watcher.stop()
            self.watcher = None
            return success
        return True

    def _on_sentry_event(self, event: Dict[str, Any]):
        """Called on Sentry event."""
        rpc_event = {
            'id': None,
            'event': 'sentry_event',
            'data': event
        }
        self._send_event(rpc_event)

    def _start_face_db_build(self, people_folder: str) -> Dict[str, Any]:
        """Start building face database."""
        job_id = str(uuid.uuid4())
        
        self.indexer = LibraryIndexer(self.db, self.metadata_engine, self.face_engine, self._on_index_event)
        
        # Run in background thread
        thread = threading.Thread(target=self.indexer.build_face_db, args=(people_folder,))
        thread.daemon = True
        thread.start()
        
        self.indexing_jobs[job_id] = {
            'started': datetime.now().isoformat(),
            'thread': thread
        }
        
        return {'job_id': job_id}

    def _lookup_api(self, api: str, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup external API."""
        if api == 'stashdb':
            search_type = params.get('search_type', 'scene')
            return self.api_client.search_stashdb(query, search_type)

        elif api == 'tmdb':
            year = params.get('year')
            media_type = params.get('media_type', 'movie')
            return self.api_client.search_tmdb(query, year, media_type)

        elif api == 'omdb':
            year = params.get('year')
            return self.api_client.search_omdb(query, year)

        elif api == 'musicbrainz':
            title = params.get('title')
            album = params.get('album')
            return self.api_client.search_musicbrainz(query, title, album)

        elif api == 'acoustid':
            fingerprint = params.get('fingerprint', '')
            duration = params.get('duration', 0)
            return self.api_client.lookup_acoustid(fingerprint, duration)

        return {'success': False, 'data': {}, 'error': f'Unknown API: {api}'}

    def _send_event(self, event: Dict[str, Any]):
        """Send an event to frontend."""
        try:
            json.dump(event, sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()
        except Exception as e:
            print(f"Error sending event: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    sidecar = MediaForgeSidecar()
    
    # Read JSON lines from stdin
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            response = sidecar.handle_request(request)
            
            # Send response
            json.dump(response.to_dict(), sys.stdout)
            sys.stdout.write('\n')
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue


if __name__ == '__main__':
    main()
