"""Metadata reading and writing engine."""
import subprocess
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import sys


class MetadataEngine:
    """Handles metadata extraction and writing for media files."""

    def __init__(self):
        """Initialize metadata engine."""
        self.mutagen_available = self._check_mutagen()
        self.ffprobe_available = self._check_ffprobe()
        self.ffmpeg_available = self._check_ffmpeg()
        self.pil_available = self._check_pil()

    def _check_mutagen(self) -> bool:
        """Check if mutagen is available."""
        try:
            import mutagen
            return True
        except ImportError:
            return False

    def _check_ffprobe(self) -> bool:
        """Check if ffprobe is available."""
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=2)
            return True
        except Exception:
            return False

    def _check_pil(self) -> bool:
        """Check if Pillow is available."""
        try:
            from PIL import Image
            return True
        except ImportError:
            return False

    def read_metadata(self, path: str) -> Dict[str, Any]:
        """Read metadata from a file."""
        if not os.path.exists(path):
            return {}

        ext = os.path.splitext(path)[1].lower().lstrip('.')

        # Try audio first
        if ext in {'mp3', 'flac', 'm4a', 'ogg', 'wav', 'aiff', 'opus', 'wma'}:
            return self._read_audio(path)

        # Try video
        elif ext in {'mkv', 'mp4', 'avi', 'mov', 'webm', 'wmv', 'm4v', 'mpg', 'mpeg', 'flv'}:
            return self._read_video(path)

        # Try image
        elif ext in {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif'}:
            return self._read_image(path)

        return {}

    def _read_audio(self, path: str) -> Dict[str, Any]:
        """Read audio metadata using mutagen."""
        if not self.mutagen_available:
            return {}

        try:
            from mutagen.mp3 import MP3
            from mutagen.flac import FLAC
            from mutagen.oggvorbis import OggVorbis
            from mutagen.oggopus import OggOpus
            from mutagen.m4a import M4A
            from mutagen.wave import WAVE
            from mutagen.aiff import AIFF

            ext = os.path.splitext(path)[1].lower().lstrip('.')

            metadata = {}

            if ext == 'mp3':
                audio = MP3(path)
                metadata['duration_seconds'] = audio.info.length
                tags = audio.tags or {}
                metadata['title'] = str(tags.get('TIT2', ''))
                metadata['artist'] = str(tags.get('TPE1', ''))
                metadata['album'] = str(tags.get('TALB', ''))
                metadata['genre'] = str(tags.get('TCON', ''))
                try:
                    metadata['year'] = int(str(tags.get('TDRC', '')))
                except (ValueError, TypeError):
                    metadata['year'] = 0

            elif ext == 'flac':
                audio = FLAC(path)
                metadata['duration_seconds'] = audio.info.length
                metadata['title'] = audio.get('title', [''])[0]
                metadata['artist'] = audio.get('artist', [''])[0]
                metadata['album'] = audio.get('album', [''])[0]
                metadata['genre'] = audio.get('genre', [''])[0]
                try:
                    metadata['year'] = int(audio.get('date', ['0'])[0])
                except (ValueError, TypeError):
                    metadata['year'] = 0

            elif ext == 'm4a':
                audio = M4A(path)
                metadata['duration_seconds'] = audio.info.length
                metadata['title'] = audio.get('\xa9nam', [''])[0] if '\xa9nam' in audio else ''
                metadata['artist'] = audio.get('\xa9ART', [''])[0] if '\xa9ART' in audio else ''
                metadata['album'] = audio.get('\xa9alb', [''])[0] if '\xa9alb' in audio else ''
                metadata['genre'] = audio.get('\xa9gen', [''])[0] if '\xa9gen' in audio else ''

            elif ext in {'ogg', 'opus'}:
                try:
                    audio = OggOpus(path)
                except:
                    audio = OggVorbis(path)
                metadata['duration_seconds'] = audio.info.length
                metadata['title'] = audio.get('title', [''])[0]
                metadata['artist'] = audio.get('artist', [''])[0]
                metadata['album'] = audio.get('album', [''])[0]
                metadata['genre'] = audio.get('genre', [''])[0]

            elif ext == 'wav':
                audio = WAVE(path)
                metadata['duration_seconds'] = audio.info.length

            elif ext == 'aiff':
                audio = AIFF(path)
                metadata['duration_seconds'] = audio.info.length

            return metadata

        except Exception as e:
            print(f"Error reading audio metadata: {e}", file=sys.stderr)
            return {}

    def _read_video(self, path: str) -> Dict[str, Any]:
        """Read video metadata using ffprobe."""
        if not self.ffprobe_available:
            return {}

        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {}

            data = json.loads(result.stdout)
            metadata = {}

            # Format info
            fmt = data.get('format', {})
            metadata['duration_seconds'] = float(fmt.get('duration', 0))

            tags = fmt.get('tags', {})
            metadata['title'] = tags.get('title', '')
            metadata['director'] = tags.get('director', '')
            metadata['artist'] = tags.get('artist', '')

            # Stream info
            streams = data.get('streams', [])
            for stream in streams:
                if stream['codec_type'] == 'video':
                    metadata['resolution'] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                    metadata['codec'] = stream.get('codec_name', '')

            return metadata

        except Exception as e:
            print(f"Error reading video metadata: {e}", file=sys.stderr)
            return {}

    def _read_image(self, path: str) -> Dict[str, Any]:
        """Read image metadata."""
        metadata = {}

        if self.pil_available:
            try:
                from PIL import Image
                from PIL.ExifTags import TAGS

                img = Image.open(path)
                metadata['resolution'] = f"{img.width}x{img.height}"

                # Try to read EXIF
                try:
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == 'GPSInfo':
                                metadata['gps_info'] = str(value)
                except Exception:
                    pass

            except Exception as e:
                print(f"Error reading image metadata: {e}", file=sys.stderr)

        return metadata

    def write_metadata(self, path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Write metadata to a file."""
        if not os.path.exists(path):
            return {'success': False, 'error': 'File not found'}

        ext = os.path.splitext(path)[1].lower().lstrip('.')

        if ext in {'mp3', 'flac', 'm4a', 'ogg', 'wav', 'aiff', 'opus', 'wma'}:
            return self._write_audio_mutagen(path, metadata)

        elif ext in {'mkv', 'mp4', 'avi', 'mov', 'webm', 'wmv', 'm4v', 'mpg', 'mpeg', 'flv'}:
            return self._write_video_ffmpeg(path, metadata)

        elif ext in {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif'}:
            return self._write_image_pil(path, metadata)

        return {'success': False, 'error': 'Unsupported file type'}

    def _write_audio_mutagen(self, path: str, meta: Dict) -> Dict[str, Any]:
        """Write audio metadata using mutagen."""
        if not self.mutagen_available:
            return {'success': False, 'error': 'Mutagen not available'}

        try:
            from mutagen.mp3 import MP3
            from mutagen.flac import FLAC
            from mutagen.m4a import M4A

            ext = os.path.splitext(path)[1].lower().lstrip('.')

            if ext == 'mp3':
                audio = MP3(path)
                if audio.tags is None:
                    from mutagen.id3 import ID3
                    audio.add_tags()

                if 'title' in meta:
                    from mutagen.id3 import TIT2
                    audio.tags['TIT2'] = TIT2(text=[meta['title']])
                if 'artist' in meta:
                    from mutagen.id3 import TPE1
                    audio.tags['TPE1'] = TPE1(text=[meta['artist']])
                if 'album' in meta:
                    from mutagen.id3 import TALB
                    audio.tags['TALB'] = TALB(text=[meta['album']])
                if 'genre' in meta:
                    from mutagen.id3 import TCON
                    audio.tags['TCON'] = TCON(text=[meta['genre']])

            elif ext == 'flac':
                audio = FLAC(path)
                if 'title' in meta:
                    audio['title'] = meta['title']
                if 'artist' in meta:
                    audio['artist'] = meta['artist']
                if 'album' in meta:
                    audio['album'] = meta['album']
                if 'genre' in meta:
                    audio['genre'] = meta['genre']

            elif ext == 'm4a':
                audio = M4A(path)
                if 'title' in meta:
                    audio['\xa9nam'] = meta['title']
                if 'artist' in meta:
                    audio['\xa9ART'] = meta['artist']
                if 'album' in meta:
                    audio['\xa9alb'] = meta['album']
                if 'genre' in meta:
                    audio['\xa9gen'] = meta['genre']

            audio.save()
            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _write_video_ffmpeg(self, path: str, meta: Dict) -> Dict[str, Any]:
        """Write video metadata using ffmpeg."""
        if not self.ffmpeg_available:
            return {'success': False, 'error': 'FFmpeg not available'}

        try:
            import tempfile
            import shutil

            # Build metadata args
            metadata_args = []
            for key, value in meta.items():
                if value:
                    metadata_args.extend(['-metadata', f'{key}={value}'])

            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(path)[1], delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # Run ffmpeg
                cmd = ['ffmpeg', '-i', path, '-c', 'copy'] + metadata_args + ['-y', tmp_path]
                result = subprocess.run(cmd, capture_output=True, timeout=30)

                if result.returncode == 0:
                    # Atomic swap
                    shutil.move(tmp_path, path)
                    return {'success': True}
                else:
                    return {'success': False, 'error': 'FFmpeg failed'}

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _write_image_pil(self, path: str, meta: Dict) -> Dict[str, Any]:
        """Write image metadata using Pillow."""
        if not self.pil_available:
            return {'success': False, 'error': 'Pillow not available'}

        try:
            from PIL import Image
            from PIL.PngImagePlugin import PngInfo

            img = Image.open(path)

            # Save metadata based on format
            if path.lower().endswith('.png'):
                pnginfo = PngInfo()
                for key, value in meta.items():
                    if value:
                        pnginfo.add_text(key, str(value))
                img.save(path, pnginfo=pnginfo)
            else:
                img.save(path)

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def extract_thumbnail(self, path: str, output_path: str, size: int = 256) -> bool:
        """Extract thumbnail from a file."""
        ext = os.path.splitext(path)[1].lower().lstrip('.')

        if ext in {'mkv', 'mp4', 'avi', 'mov', 'webm', 'wmv', 'm4v', 'mpg', 'mpeg', 'flv'}:
            return self._extract_video_thumbnail(path, output_path, size)

        elif ext in {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif'}:
            return self._extract_image_thumbnail(path, output_path, size)

        return False

    def _extract_video_thumbnail(self, path: str, output_path: str, size: int) -> bool:
        """Extract thumbnail from video."""
        if not self.ffmpeg_available:
            return False

        try:
            cmd = [
                'ffmpeg', '-ss', '00:00:10', '-i', path,
                '-vframes', '1', '-vf', f'scale={size}:{size}',
                '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _extract_image_thumbnail(self, path: str, output_path: str, size: int) -> bool:
        """Extract thumbnail from image using PIL."""
        if not self.pil_available:
            return False

        try:
            from PIL import Image
            img = Image.open(path)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            img.save(output_path, 'JPEG')
            return True
        except Exception:
            return False
