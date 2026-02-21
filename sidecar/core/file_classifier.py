"""File type detection and classification."""
import os
import hashlib
import time
from typing import Dict, Tuple


class FileClassifier:
    """Detects and classifies media files."""

    AUDIO_EXTS = {'mp3', 'flac', 'm4a', 'ogg', 'wav', 'aiff', 'opus', 'wma'}
    VIDEO_EXTS = {'mkv', 'mp4', 'avi', 'mov', 'webm', 'wmv', 'm4v', 'mpg', 'mpeg', 'flv'}
    IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif'}

    MAGIC_BYTES = {
        b'\xff\xfb': ('mp3', 'audio'),
        b'\xff\xfa': ('mp3', 'audio'),
        b'\x1a\x45\xdf\xa3': ('mkv', 'video'),
        b'\xff\xd8\xff': ('jpg', 'image'),
        b'\x89PNG\r\n\x1a\n': ('png', 'image'),
        b'ID3': ('mp3', 'audio'),
        b'fLaC': ('flac', 'audio'),
    }

    def classify(self, path: str) -> Dict:
        """Classify a file and return metadata."""
        if not os.path.exists(path):
            return {
                'file_type': 'unknown',
                'extension': '',
                'mime_type': 'unknown',
                'size_bytes': 0,
                'modified_at': ''
            }

        try:
            # Get file stats
            stat = os.stat(path)
            size_bytes = stat.st_size
            modified_at = str(stat.st_mtime)

            # Get extension
            _, ext = os.path.splitext(path)
            ext = ext.lstrip('.').lower()

            # Classify by extension first
            file_type = 'unknown'
            mime_type = 'application/octet-stream'

            if ext in self.AUDIO_EXTS:
                file_type = 'audio'
                mime_type = f'audio/{ext}'
            elif ext in self.VIDEO_EXTS:
                file_type = 'video'
                mime_type = f'video/{ext}'
            elif ext in self.IMAGE_EXTS:
                file_type = 'image'
                mime_type = f'image/{ext}'

            # Fallback to magic bytes if unknown
            if file_type == 'unknown':
                file_type, mime_type = self._detect_by_magic_bytes(path)

            return {
                'file_type': file_type,
                'extension': ext,
                'mime_type': mime_type,
                'size_bytes': size_bytes,
                'modified_at': modified_at
            }
        except Exception as e:
            print(f"Error classifying file {path}: {e}")
            return {
                'file_type': 'unknown',
                'extension': '',
                'mime_type': 'unknown',
                'size_bytes': 0,
                'modified_at': ''
            }

    def _detect_by_magic_bytes(self, path: str) -> Tuple[str, str]:
        """Detect file type by magic bytes."""
        try:
            with open(path, 'rb') as f:
                header = f.read(16)

            # Check MP4 signature (ftyp at offset 4)
            if len(header) >= 8 and header[4:8] == b'ftyp':
                return 'video', 'video/mp4'

            # Check other signatures
            for magic, (ext, ftype) in self.MAGIC_BYTES.items():
                if header.startswith(magic):
                    return ftype, f'{ftype}/{ext}'

            return 'unknown', 'application/octet-stream'
        except Exception:
            return 'unknown', 'application/octet-stream'

    def is_stable(self, path: str, check_interval: float = 0.5) -> bool:
        """Check if file size is stable (not being written to)."""
        try:
            if not os.path.exists(path):
                return False

            size1 = os.path.getsize(path)
            time.sleep(check_interval)
            size2 = os.path.getsize(path)

            return size1 == size2
        except Exception:
            return False

    def compute_md5(self, path: str) -> str:
        """Compute MD5 hash of file."""
        try:
            md5_hash = hashlib.md5()
            with open(path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"Error computing MD5 for {path}: {e}")
            return ""
