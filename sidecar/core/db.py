"""SQLite database manager for MediaForge."""
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from .models import FileRecord, PerformerRecord, PersonRecord


class DatabaseManager:
    """Manages SQLite databases for media and faces."""

    def __init__(self, data_dir: str = None):
        """Initialize database manager."""
        if data_dir is None:
            data_dir = os.path.expanduser('~/.mediaforge/db')
        
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.media_db_path = os.path.join(data_dir, 'media.db')
        self.faces_db_path = os.path.join(data_dir, 'faces.db')
        
        self.init_databases()

    def init_databases(self):
        """Create all tables if they don't exist."""
        self._init_media_db()
        self._init_faces_db()

    def _init_media_db(self):
        """Initialize media database schema."""
        with self.get_connection('media') as conn:
            cursor = conn.cursor()
            
            # Files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    extension TEXT,
                    file_type TEXT,
                    content_mode TEXT,
                    size_bytes INTEGER,
                    modified_at TEXT,
                    indexed_at TEXT,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    album_artist TEXT,
                    genre TEXT,
                    year INTEGER,
                    duration_seconds REAL,
                    director TEXT,
                    studio TEXT,
                    cast_list TEXT,
                    synopsis TEXT,
                    rating REAL,
                    season INTEGER,
                    episode INTEGER,
                    resolution TEXT,
                    codec TEXT,
                    bitrate TEXT,
                    positions TEXT,
                    acts TEXT,
                    scene_setting TEXT,
                    series_name TEXT,
                    scene_number INTEGER,
                    source_url TEXT,
                    camera TEXT,
                    gps_lat REAL,
                    gps_lon REAL,
                    thumbnail_path TEXT,
                    hash_md5 TEXT,
                    favorite INTEGER DEFAULT 0
                )
            ''')
            
            # FTS5 virtual table for full-text search
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    title, artist, album, filename, synopsis, 
                    content=files, content_rowid=rowid
                )
            ''')
            
            # Performers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performers (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    hair_color TEXT,
                    eye_color TEXT,
                    body_type TEXT,
                    ethnicity TEXT,
                    chest_type TEXT,
                    butt_type TEXT,
                    folder_path TEXT,
                    notes TEXT
                )
            ''')
            
            # File-Performer linking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_performers (
                    file_id TEXT NOT NULL,
                    performer_id TEXT NOT NULL,
                    PRIMARY KEY (file_id, performer_id),
                    FOREIGN KEY (file_id) REFERENCES files(id),
                    FOREIGN KEY (performer_id) REFERENCES performers(id)
                )
            ''')
            
            # Tags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files(id),
                    UNIQUE (file_id, tag)
                )
            ''')
            
            # Folder metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folder_meta (
                    folder_path TEXT PRIMARY KEY,
                    last_scanned TEXT,
                    file_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_artist ON files(artist)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_studio ON files(studio)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_year ON files(year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_rating ON files(rating)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_content_mode ON files(content_mode)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_performers ON file_performers(performer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_file_id ON tags(file_id)')
            
            # Create trigger for FTS5 synchronization
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                    INSERT INTO files_fts(rowid, title, artist, album, filename, synopsis)
                    VALUES (new.rowid, new.title, new.artist, new.album, new.filename, new.synopsis);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                    DELETE FROM files_fts WHERE rowid = old.rowid;
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                    DELETE FROM files_fts WHERE rowid = old.rowid;
                    INSERT INTO files_fts(rowid, title, artist, album, filename, synopsis)
                    VALUES (new.rowid, new.title, new.artist, new.album, new.filename, new.synopsis);
                END
            ''')
            
            conn.commit()

    def _init_faces_db(self):
        """Initialize faces database schema."""
        with self.get_connection('faces') as conn:
            cursor = conn.cursor()
            
            # People table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS people (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    folder_path TEXT
                )
            ''')
            
            # Face encodings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_encodings (
                    id TEXT PRIMARY KEY,
                    person_id TEXT NOT NULL,
                    encoding BLOB NOT NULL,
                    source_file TEXT,
                    confidence REAL DEFAULT 0.0,
                    FOREIGN KEY (person_id) REFERENCES people(id)
                )
            ''')
            
            # Face encounters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_encounters (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    person_id TEXT,
                    matched INTEGER DEFAULT 0,
                    distance REAL,
                    FOREIGN KEY (person_id) REFERENCES people(id)
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_encodings_person ON face_encodings(person_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_encounters_file ON face_encounters(file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_encounters_person ON face_encounters(person_id)')
            
            conn.commit()

    @contextmanager
    def get_connection(self, db: str = 'media'):
        """Get database connection as context manager."""
        if db == 'media':
            path = self.media_db_path
        elif db == 'faces':
            path = self.faces_db_path
        else:
            raise ValueError(f"Unknown database: {db}")
        
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def upsert_file(self, record: FileRecord) -> bool:
        """Insert or update a file record."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                
                # Convert lists to JSON strings
                import json
                cast_list = json.dumps(record.cast_list) if record.cast_list else '[]'
                positions = json.dumps(record.positions) if record.positions else '[]'
                acts = json.dumps(record.acts) if record.acts else '[]'
                
                cursor.execute('''
                    INSERT OR REPLACE INTO files (
                        id, path, filename, extension, file_type, content_mode,
                        size_bytes, modified_at, indexed_at, title, artist, album,
                        album_artist, genre, year, duration_seconds, director, studio,
                        cast_list, synopsis, rating, season, episode, resolution, codec,
                        bitrate, positions, acts, scene_setting, series_name, scene_number,
                        source_url, camera, gps_lat, gps_lon, thumbnail_path, hash_md5, favorite
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.id, record.path, record.filename, record.extension,
                    record.file_type, record.content_mode, record.size_bytes,
                    record.modified_at, record.indexed_at, record.title, record.artist,
                    record.album, record.album_artist, record.genre, record.year,
                    record.duration_seconds, record.director, record.studio, cast_list,
                    record.synopsis, record.rating, record.season, record.episode,
                    record.resolution, record.codec, record.bitrate, positions, acts,
                    record.scene_setting, record.series_name, record.scene_number,
                    record.source_url, record.camera, record.gps_lat, record.gps_lon,
                    record.thumbnail_path, record.hash_md5, int(record.favorite)
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error upserting file: {e}")
            return False

    def get_file(self, path: str) -> Optional[FileRecord]:
        """Get a file record by path."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM files WHERE path = ?', (path,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_file_record(row)
        except Exception as e:
            print(f"Error getting file: {e}")
        return None

    def search_files(self, query: str = "", filters: Dict = None, limit: int = 50, offset: int = 0) -> Tuple[List[FileRecord], int]:
        """Search files with FTS5 and SQL filters."""
        if filters is None:
            filters = {}
        
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                
                # Build WHERE clause from filters
                where_parts = []
                params = []
                
                if 'file_type' in filters:
                    where_parts.append('file_type = ?')
                    params.append(filters['file_type'])
                
                if 'extension' in filters:
                    where_parts.append('extension = ?')
                    params.append(filters['extension'])
                
                if 'studio' in filters:
                    where_parts.append('studio = ?')
                    params.append(filters['studio'])
                
                if 'artist' in filters:
                    where_parts.append('artist = ?')
                    params.append(filters['artist'])
                
                if 'year' in filters:
                    where_parts.append('year = ?')
                    params.append(filters['year'])
                
                if 'rating_min' in filters and 'rating_max' in filters:
                    where_parts.append('rating >= ? AND rating <= ?')
                    params.extend([filters['rating_min'], filters['rating_max']])
                
                if 'content_mode' in filters:
                    where_parts.append('content_mode = ?')
                    params.append(filters['content_mode'])
                
                # Use FTS5 if query provided
                if query:
                    fts_where = ' AND '.join(where_parts) if where_parts else '1=1'
                    sql = f'''
                        SELECT f.* FROM files f
                        JOIN files_fts fts ON f.rowid = fts.rowid
                        WHERE fts.files_fts MATCH ? AND {fts_where}
                        LIMIT ? OFFSET ?
                    '''
                    cursor.execute(sql, [query] + params + [limit, offset])
                else:
                    where = ' AND '.join(where_parts) if where_parts else '1=1'
                    sql = f'SELECT * FROM files WHERE {where} LIMIT ? OFFSET ?'
                    cursor.execute(sql, params + [limit, offset])
                
                rows = cursor.fetchall()
                results = [self._row_to_file_record(row) for row in rows]
                
                # Get total count
                if query:
                    count_sql = f'''
                        SELECT COUNT(*) as cnt FROM files f
                        JOIN files_fts fts ON f.rowid = fts.rowid
                        WHERE fts.files_fts MATCH ? AND {fts_where}
                    '''
                    cursor.execute(count_sql, [query] + params)
                else:
                    count_sql = f'SELECT COUNT(*) as cnt FROM files WHERE {where}'
                    cursor.execute(count_sql, params)
                
                total = cursor.fetchone()['cnt']
                return results, total
        except Exception as e:
            print(f"Error searching files: {e}")
            return [], 0

    def get_performer(self, name: str) -> Optional[PerformerRecord]:
        """Get a performer by name."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM performers WHERE name = ?', (name,))
                row = cursor.fetchone()
                if row:
                    return PerformerRecord(
                        id=row['id'],
                        name=row['name'],
                        hair_color=row['hair_color'] or "",
                        eye_color=row['eye_color'] or "",
                        body_type=row['body_type'] or "",
                        ethnicity=row['ethnicity'] or "",
                        chest_type=row['chest_type'] or "",
                        butt_type=row['butt_type'] or "",
                        folder_path=row['folder_path'] or "",
                        notes=row['notes'] or ""
                    )
        except Exception as e:
            print(f"Error getting performer: {e}")
        return None

    def upsert_performer(self, record: PerformerRecord) -> bool:
        """Insert or update a performer record."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO performers (
                        id, name, hair_color, eye_color, body_type, ethnicity,
                        chest_type, butt_type, folder_path, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.id, record.name, record.hair_color, record.eye_color,
                    record.body_type, record.ethnicity, record.chest_type,
                    record.butt_type, record.folder_path, record.notes
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error upserting performer: {e}")
            return False

    def link_file_performer(self, file_id: str, performer_id: str) -> bool:
        """Link a file to a performer."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO file_performers (file_id, performer_id)
                    VALUES (?, ?)
                ''', (file_id, performer_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error linking file and performer: {e}")
            return False

    def upsert_person(self, name: str, folder_path: str = "") -> str:
        """Insert or update a person (for faces)."""
        import uuid
        person_id = str(uuid.uuid4())
        
        try:
            with self.get_connection('faces') as conn:
                cursor = conn.cursor()
                # Check if exists
                cursor.execute('SELECT id FROM people WHERE name = ?', (name,))
                existing = cursor.fetchone()
                
                if existing:
                    person_id = existing['id']
                    cursor.execute('''
                        UPDATE people SET folder_path = ? WHERE id = ?
                    ''', (folder_path, person_id))
                else:
                    cursor.execute('''
                        INSERT INTO people (id, name, folder_path) VALUES (?, ?, ?)
                    ''', (person_id, name, folder_path))
                
                conn.commit()
                return person_id
        except Exception as e:
            print(f"Error upserting person: {e}")
            return person_id

    def get_all_encodings(self) -> Tuple[List[bytes], List[str]]:
        """Get all face encodings and their person IDs."""
        encodings = []
        person_ids = []
        
        try:
            with self.get_connection('faces') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT person_id, encoding FROM face_encodings')
                rows = cursor.fetchall()
                
                for row in rows:
                    encodings.append(row['encoding'])
                    person_ids.append(row['person_id'])
        except Exception as e:
            print(f"Error getting encodings: {e}")
        
        return encodings, person_ids

    def add_encoding(self, person_id: str, encoding_bytes: bytes, source_file: str) -> bool:
        """Add a face encoding for a person."""
        import uuid
        encoding_id = str(uuid.uuid4())
        
        try:
            with self.get_connection('faces') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO face_encodings (id, person_id, encoding, source_file)
                    VALUES (?, ?, ?, ?)
                ''', (encoding_id, person_id, encoding_bytes, source_file))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding encoding: {e}")
            return False

    def add_encounter(self, file_path: str, person_id: str, encoding_bytes: bytes, distance: float) -> bool:
        """Add a face encounter."""
        import uuid
        encounter_id = str(uuid.uuid4())
        
        try:
            with self.get_connection('faces') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO face_encounters (id, file_path, person_id, matched, distance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (encounter_id, file_path, person_id, 1, distance))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding encounter: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                
                # File stats
                cursor.execute('SELECT COUNT(*) as cnt FROM files')
                file_count = cursor.fetchone()['cnt']
                
                cursor.execute('SELECT SUM(size_bytes) as total FROM files')
                total_size = cursor.fetchone()['total'] or 0
                
                cursor.execute('SELECT COUNT(*) as cnt FROM performers')
                performer_count = cursor.fetchone()['cnt']
                
                # File type breakdown
                cursor.execute('SELECT file_type, COUNT(*) as cnt FROM files GROUP BY file_type')
                types = {row['file_type']: row['cnt'] for row in cursor.fetchall()}
            
            with self.get_connection('faces') as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) as cnt FROM people')
                people_count = cursor.fetchone()['cnt']
                
                cursor.execute('SELECT COUNT(*) as cnt FROM face_encodings')
                encodings_count = cursor.fetchone()['cnt']
            
            # Get DB file sizes
            media_size = os.path.getsize(self.media_db_path) / (1024 * 1024)  # MB
            faces_size = os.path.getsize(self.faces_db_path) / (1024 * 1024)
            
            return {
                'total_files': file_count,
                'total_size_mb': total_size / (1024 * 1024),
                'total_performers': performer_count,
                'total_people': people_count,
                'total_encodings': encodings_count,
                'file_types': types,
                'media_db_size_mb': media_size,
                'faces_db_size_mb': faces_size,
                'total_db_size_mb': media_size + faces_size
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}

    def delete_file(self, path: str) -> bool:
        """Delete a file record and related data."""
        try:
            with self.get_connection('media') as conn:
                cursor = conn.cursor()
                
                # Get file ID
                cursor.execute('SELECT id FROM files WHERE path = ?', (path,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                file_id = row['id']
                
                # Delete related records
                cursor.execute('DELETE FROM file_performers WHERE file_id = ?', (file_id,))
                cursor.execute('DELETE FROM tags WHERE file_id = ?', (file_id,))
                cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def _row_to_file_record(self, row) -> FileRecord:
        """Convert a database row to FileRecord."""
        import json
        
        cast_list = json.loads(row['cast_list']) if row['cast_list'] else []
        positions = json.loads(row['positions']) if row['positions'] else []
        acts = json.loads(row['acts']) if row['acts'] else []
        
        return FileRecord(
            id=row['id'],
            path=row['path'],
            filename=row['filename'],
            extension=row['extension'] or "",
            file_type=row['file_type'] or "",
            content_mode=row['content_mode'] or "",
            size_bytes=row['size_bytes'] or 0,
            modified_at=row['modified_at'] or "",
            indexed_at=row['indexed_at'] or "",
            title=row['title'] or "",
            artist=row['artist'] or "",
            album=row['album'] or "",
            album_artist=row['album_artist'] or "",
            genre=row['genre'] or "",
            year=row['year'] or 0,
            duration_seconds=row['duration_seconds'] or 0.0,
            director=row['director'] or "",
            studio=row['studio'] or "",
            cast_list=cast_list,
            synopsis=row['synopsis'] or "",
            rating=row['rating'] or 0.0,
            season=row['season'] or 0,
            episode=row['episode'] or 0,
            resolution=row['resolution'] or "",
            codec=row['codec'] or "",
            bitrate=row['bitrate'] or "",
            positions=positions,
            acts=acts,
            scene_setting=row['scene_setting'] or "",
            series_name=row['series_name'] or "",
            scene_number=row['scene_number'] or 0,
            source_url=row['source_url'] or "",
            camera=row['camera'] or "",
            gps_lat=row['gps_lat'] or 0.0,
            gps_lon=row['gps_lon'] or 0.0,
            thumbnail_path=row['thumbnail_path'] or "",
            hash_md5=row['hash_md5'] or "",
            favorite=bool(row['favorite'])
        )
