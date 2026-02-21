"""External API clients with rate limiting."""
import urllib.request
import urllib.parse
import json
import time
from threading import Lock
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, capacity: int = None):
        """Initialize rate limiter.

        Args:
            rate: Requests per second
            capacity: Maximum tokens (defaults to rate)
        """
        self.rate = rate
        self.capacity = capacity or rate
        self.tokens = self.capacity
        self.last_update = time.time()
        self.lock = Lock()

    def acquire(self) -> None:
        """Wait until a token is available."""
        while not self.try_acquire():
            time.sleep(0.01)

    def try_acquire(self) -> bool:
        """Try to acquire a token without waiting."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            return False


class ApiClient:
    """Client for external APIs with rate limiting."""

    def __init__(self, config):
        """Initialize API client."""
        self.config = config
        self.rate_limiters = {
            'tmdb': RateLimiter(50),  # 50 req/s
            'omdb': RateLimiter(100 / 60),  # 100 req/min
            'musicbrainz': RateLimiter(1),  # 1 req/s (strict)
            'acoustid': RateLimiter(3),  # 3 req/s
        }

    def search_stashdb(self, query: str, search_type: str = 'scene') -> Dict[str, Any]:
        """Search StashDB via GraphQL."""
        if not self.config.get('api_enabled.stashdb'):
            return {'success': False, 'data': {}, 'error': 'StashDB disabled'}

        api_key = self.config.get('api_keys.stashdb')
        if not api_key:
            return {'success': False, 'data': {}, 'error': 'No StashDB API key'}

        try:
            if search_type == 'scene':
                gql = f'''
                    query {{
                        sceneSearch(input: {{q: "{query}"}}) {{
                            count
                            scenes {{
                                id
                                title
                                details
                                date
                                duration
                                directors {{
                                    name
                                }}
                            }}
                        }}
                    }}
                '''
            else:
                gql = f'''
                    query {{
                        performerSearch(input: {{q: "{query}"}}) {{
                            count
                            performers {{
                                id
                                name
                                disambiguation
                            }}
                        }}
                    }}
                '''

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'MediaForge'
            }

            data = json.dumps({'query': gql}).encode('utf-8')
            req = urllib.request.Request(
                'https://stashdb.org/graphql',
                data=data,
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {'success': True, 'data': result, 'error': None}

        except Exception as e:
            return {'success': False, 'data': {}, 'error': str(e)}

    def search_tmdb(self, title: str, year: Optional[int] = None, media_type: str = 'movie') -> Dict[str, Any]:
        """Search The Movie Database."""
        if not self.config.get('api_enabled.tmdb'):
            return {'success': False, 'data': {}, 'error': 'TMDB disabled'}

        api_key = self.config.get('api_keys.tmdb')
        if not api_key:
            return {'success': False, 'data': {}, 'error': 'No TMDB API key'}

        try:
            self.rate_limiters['tmdb'].acquire()

            params = {
                'api_key': api_key,
                'query': title,
            }
            if year:
                params['year'] = year

            url = f'https://api.themoviedb.org/3/search/{media_type}?{urllib.parse.urlencode(params)}'

            req = urllib.request.Request(url, headers={'User-Agent': 'MediaForge'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {'success': True, 'data': result, 'error': None}

        except Exception as e:
            return {'success': False, 'data': {}, 'error': str(e)}

    def search_omdb(self, title: str, year: Optional[int] = None) -> Dict[str, Any]:
        """Search Open Movie Database."""
        if not self.config.get('api_enabled.omdb'):
            return {'success': False, 'data': {}, 'error': 'OMDB disabled'}

        api_key = self.config.get('api_keys.omdb')
        if not api_key:
            return {'success': False, 'data': {}, 'error': 'No OMDB API key'}

        try:
            self.rate_limiters['omdb'].acquire()

            params = {
                'apikey': api_key,
                't': title,
            }
            if year:
                params['y'] = year

            url = f'http://www.omdbapi.com/?{urllib.parse.urlencode(params)}'

            req = urllib.request.Request(url, headers={'User-Agent': 'MediaForge'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {'success': True, 'data': result, 'error': None}

        except Exception as e:
            return {'success': False, 'data': {}, 'error': str(e)}

    def search_musicbrainz(self, artist: str, title: Optional[str] = None, album: Optional[str] = None) -> Dict[str, Any]:
        """Search MusicBrainz."""
        if not self.config.get('api_enabled.musicbrainz'):
            return {'success': False, 'data': {}, 'error': 'MusicBrainz disabled'}

        try:
            self.rate_limiters['musicbrainz'].acquire()

            query = f'artist:{artist}'
            if title:
                query += f' recording:{title}'
            if album:
                query += f' album:{album}'

            params = {'query': query}
            url = f'https://musicbrainz.org/ws/2/recording?{urllib.parse.urlencode(params)}&fmt=json'

            headers = {'User-Agent': 'MediaForge/1.0 (contact@mediaforge.local)'}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {'success': True, 'data': result, 'error': None}

        except Exception as e:
            return {'success': False, 'data': {}, 'error': str(e)}

    def lookup_acoustid(self, fingerprint: str, duration: float) -> Dict[str, Any]:
        """Lookup AcoustID fingerprint."""
        if not self.config.get('api_enabled.acoustid'):
            return {'success': False, 'data': {}, 'error': 'AcoustID disabled'}

        client_id = self.config.get('api_keys.acoustid_client')
        if not client_id:
            return {'success': False, 'data': {}, 'error': 'No AcoustID client ID'}

        try:
            self.rate_limiters['acoustid'].acquire()

            params = {
                'client': client_id,
                'fingerprint': fingerprint,
                'duration': int(duration),
            }
            url = f'https://api.acoustid.org/v2/lookup?{urllib.parse.urlencode(params)}'

            req = urllib.request.Request(url, headers={'User-Agent': 'MediaForge'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return {'success': True, 'data': result, 'error': None}

        except Exception as e:
            return {'success': False, 'data': {}, 'error': str(e)}
