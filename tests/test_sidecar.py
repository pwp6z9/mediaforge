"""Comprehensive test suite for MediaForge Python sidecar."""
import sys
import os
import json
import tempfile
import shutil
import subprocess
import time
import uuid
from pathlib import Path

# Set PYTHONPATH to include sidecar directory
sidecar_path = '/sessions/sweet-affectionate-ramanujan/mediaforge/sidecar'
sys.path.insert(0, sidecar_path)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, test_name, message=""):
        """Record a passing test."""
        self.passed += 1
        self.tests.append({
            'name': test_name,
            'status': 'PASS',
            'message': message
        })
        print(f"{GREEN}✓ PASS{RESET}: {test_name}")
        if message:
            print(f"  {message}")
    
    def add_fail(self, test_name, error=""):
        """Record a failing test."""
        self.failed += 1
        self.tests.append({
            'name': test_name,
            'status': 'FAIL',
            'error': error
        })
        print(f"{RED}✗ FAIL{RESET}: {test_name}")
        if error:
            print(f"  {RED}Error: {error}{RESET}")
    
    def summary(self):
        """Print summary."""
        total = self.passed + self.failed
        print(f"\n{BOLD}{'='*70}")
        print(f"Test Summary: {self.passed}/{total} passed")
        print(f"{'='*70}{RESET}")
        if self.failed > 0:
            print(f"{RED}{self.failed} tests failed{RESET}")
        else:
            print(f"{GREEN}All tests passed!{RESET}")
        return self.failed == 0


results = TestResults()


def test_module_imports():
    """Test 1: Module imports."""
    print(f"\n{BOLD}TEST 1: Module Imports{RESET}")
    
    modules_to_test = [
        ('core.db', 'DatabaseManager'),
        ('core.config', 'ConfigManager'),
        ('core.models', ['PerformerRecord', 'PersonRecord', 'FileRecord']),
        ('core.file_classifier', 'FileClassifier'),
        ('core.rules', 'RuleEngine'),
        ('core.indexer', 'LibraryIndexer'),
    ]
    
    for module_name, classes in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[''])
            if isinstance(classes, str):
                classes = [classes]
            
            for cls_name in classes:
                if not hasattr(module, cls_name):
                    results.add_fail(
                        f"Import {module_name}.{cls_name}",
                        f"Class {cls_name} not found in module {module_name}"
                    )
                else:
                    results.add_pass(f"Import {module_name}.{cls_name}")
        except Exception as e:
            results.add_fail(f"Import {module_name}", str(e))


def test_database_operations():
    """Test 2: Database operations."""
    print(f"\n{BOLD}TEST 2: Database Operations{RESET}")
    
    from core.db import DatabaseManager
    from core.models import FileRecord, PerformerRecord
    
    # Create temp directory for databases
    temp_dir = tempfile.mkdtemp(prefix='mediaforge_test_')
    
    try:
        # Initialize database manager with temp path
        db = DatabaseManager(temp_dir)
        results.add_pass("Create DatabaseManager with temp path", temp_dir)
        
        # Check media.db exists
        media_db = os.path.join(temp_dir, 'media.db')
        if os.path.exists(media_db):
            results.add_pass("media.db created", media_db)
        else:
            results.add_fail("media.db exists", f"File not found at {media_db}")
        
        # Check faces.db exists
        faces_db = os.path.join(temp_dir, 'faces.db')
        if os.path.exists(faces_db):
            results.add_pass("faces.db created", faces_db)
        else:
            results.add_fail("faces.db exists", f"File not found at {faces_db}")
        
        # Test inserting a file record
        file_id = str(uuid.uuid4())
        file_record = FileRecord(
            id=file_id,
            path='/test/video.mkv',
            filename='video.mkv',
            extension='mkv',
            file_type='video',
            size_bytes=1024000,
            modified_at='2026-02-21T12:00:00',
            indexed_at='2026-02-21T12:00:01',
            title='Test Video',
            artist='Test Artist',
            hash_md5='abc123def456'
        )
        
        try:
            success = db.upsert_file(file_record)
            if success:
                results.add_pass("Insert file record", f"ID: {file_id}")
            else:
                results.add_fail("Insert file record", "upsert_file returned False")
        except Exception as e:
            results.add_fail("Insert file record", str(e))
        
        # Test inserting a performer record
        perf_id = str(uuid.uuid4())
        performer_record = PerformerRecord(
            id=perf_id,
            name='Test Performer',
            hair_color='brown',
            eye_color='blue',
            body_type='athletic',
            ethnicity='caucasian'
        )
        
        try:
            db.upsert_performer(performer_record)
            results.add_pass("Insert performer record", f"ID: {perf_id}")
        except Exception as e:
            results.add_fail("Insert performer record", str(e))
        
        # Test linking file and performer
        try:
            db.link_file_performer(file_id, perf_id)
            results.add_pass("Link file to performer")
        except Exception as e:
            results.add_fail("Link file to performer", str(e))
        
        # Test FTS5 search
        try:
            results_found, total = db.search_files('video', {}, 10, 0)
            if len(results_found) > 0:
                results.add_pass("FTS5 search", f"Found {total} results")
            else:
                results.add_fail("FTS5 search", "No results found for 'video' query")
        except Exception as e:
            results.add_fail("FTS5 search", str(e))
        
        # Test querying back file
        try:
            queried_file = db.get_file('/test/video.mkv')
            if queried_file and queried_file.title == 'Test Video':
                results.add_pass("Query file record", f"Title: {queried_file.title}")
            else:
                results.add_fail("Query file record", "File not found or data mismatch")
        except Exception as e:
            results.add_fail("Query file record", str(e))
        
        # Test querying performer
        try:
            queried_perf = db.get_performer('Test Performer')
            if queried_perf and queried_perf.name == 'Test Performer':
                results.add_pass("Query performer record", f"Name: {queried_perf.name}")
            else:
                results.add_fail("Query performer record", "Performer not found")
        except Exception as e:
            results.add_fail("Query performer record", str(e))
        
        # Test get_stats
        try:
            stats = db.get_stats()
            if isinstance(stats, dict):
                results.add_pass("Get database stats", f"Stats: {stats}")
            else:
                results.add_fail("Get database stats", "Stats not a dict")
        except Exception as e:
            results.add_fail("Get database stats", str(e))
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_file_classifier():
    """Test 3: FileClassifier with real temp files."""
    print(f"\n{BOLD}TEST 3: FileClassifier{RESET}")
    
    from core.file_classifier import FileClassifier
    
    temp_dir = tempfile.mkdtemp(prefix='mediaforge_files_')
    classifier = FileClassifier()
    
    try:
        # Test files with extension and minimal content
        test_files = [
            ('test.mkv', b'\x1a\x45\xdf\xa3' + b'x' * 100, 'video'),  # MKV magic bytes
            ('test.mp4', b'ftypisom' + b'x' * 100, 'video'),           # MP4 magic bytes
            ('test.mp3', b'ID3' + b'x' * 100, 'audio'),                # MP3 magic bytes
            ('test.flac', b'fLaC' + b'x' * 100, 'audio'),              # FLAC magic bytes
            ('test.jpg', b'\xff\xd8\xff' + b'x' * 100, 'image'),       # JPG magic bytes
            ('test.png', b'\x89PNG\r\n\x1a\n' + b'x' * 100, 'image'),  # PNG magic bytes
        ]
        
        for filename, content, expected_type in test_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(content)
            
            try:
                result = classifier.classify(file_path)
                
                # Check if file_type was determined
                if result.get('file_type') == expected_type:
                    results.add_pass(
                        f"Classify {filename}",
                        f"Type: {result['file_type']}"
                    )
                else:
                    results.add_fail(
                        f"Classify {filename}",
                        f"Expected {expected_type}, got {result.get('file_type')}"
                    )
                
                # Check extension
                if result.get('extension') == filename.split('.')[-1]:
                    results.add_pass(
                        f"Extension detected for {filename}",
                        f"Extension: {result['extension']}"
                    )
                else:
                    results.add_fail(
                        f"Extension for {filename}",
                        f"Got {result.get('extension')}"
                    )
            except Exception as e:
                results.add_fail(f"Classify {filename}", str(e))
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_config_loading():
    """Test 4: Config loading."""
    print(f"\n{BOLD}TEST 4: Config Loading{RESET}")
    
    from core.config import ConfigManager
    import yaml
    
    temp_dir = tempfile.mkdtemp(prefix='mediaforge_config_')
    
    try:
        # Create a temp config file
        config_path = os.path.join(temp_dir, 'config.yaml')
        test_config = {
            'nsfw_mode': True,
            'library_folders': ['/test/library'],
            'watch_folders': ['/test/watch'],
            'theme': 'dark-pink',
            'api_enabled': {
                'stashdb': True,
                'tmdb': False
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        results.add_pass("Create temp config file", config_path)
        
        # Load config
        try:
            config = ConfigManager(config_path)
            results.add_pass("Load ConfigManager", config_path)
            
            # Verify values
            if config.get('nsfw_mode') == True:
                results.add_pass("Config nsfw_mode", "True")
            else:
                results.add_fail("Config nsfw_mode", f"Got {config.get('nsfw_mode')}")
            
            if config.get('theme') == 'dark-pink':
                results.add_pass("Config theme", "dark-pink")
            else:
                results.add_fail("Config theme", f"Got {config.get('theme')}")
            
            # Test getting all config
            all_config = config.get_all()
            if isinstance(all_config, dict):
                results.add_pass("Get all config", f"Keys: {len(all_config)}")
            else:
                results.add_fail("Get all config", "Not a dict")
        
        except Exception as e:
            results.add_fail("Load ConfigManager", str(e))
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_json_rpc_integration():
    """Test 5: JSON-RPC integration with sidecar subprocess."""
    print(f"\n{BOLD}TEST 5: JSON-RPC Integration{RESET}")
    
    main_py = '/sessions/sweet-affectionate-ramanujan/mediaforge/sidecar/main.py'
    
    try:
        # Start sidecar process
        env = os.environ.copy()
        env['PYTHONPATH'] = sidecar_path
        
        proc = subprocess.Popen(
            [sys.executable, main_py],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1
        )
        
        results.add_pass("Start sidecar process", f"PID: {proc.pid}")
        
        # Give it time to initialize
        time.sleep(0.5)
        
        # Test 1: ping
        try:
            request = {
                'id': '1',
                'method': 'ping',
                'params': {}
            }
            proc.stdin.write(json.dumps(request) + '\n')
            proc.stdin.flush()
            
            # Read response with timeout
            response_line = proc.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                if response.get('result', {}).get('pong') == True:
                    results.add_pass("JSON-RPC ping", f"pong=True, version={response['result'].get('version')}")
                else:
                    results.add_fail("JSON-RPC ping", f"No pong in response: {response}")
            else:
                results.add_fail("JSON-RPC ping", "No response received")
        except Exception as e:
            results.add_fail("JSON-RPC ping", str(e))
        
        # Test 2: get_config
        try:
            request = {
                'id': '2',
                'method': 'get_config',
                'params': {}
            }
            proc.stdin.write(json.dumps(request) + '\n')
            proc.stdin.flush()
            
            response_line = proc.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                if response.get('result'):
                    results.add_pass("JSON-RPC get_config", f"Config keys: {len(response['result'])}")
                else:
                    results.add_fail("JSON-RPC get_config", f"No result: {response}")
            else:
                results.add_fail("JSON-RPC get_config", "No response received")
        except Exception as e:
            results.add_fail("JSON-RPC get_config", str(e))
        
        # Test 3: get_stats
        try:
            request = {
                'id': '3',
                'method': 'get_stats',
                'params': {}
            }
            proc.stdin.write(json.dumps(request) + '\n')
            proc.stdin.flush()
            
            response_line = proc.stdout.readline()
            if response_line:
                response = json.loads(response_line)
                if response.get('result'):
                    result = response['result']
                    results.add_pass(
                        "JSON-RPC get_stats",
                        f"Total files: {result.get('total_files', 0)}, performers: {result.get('total_performers', 0)}"
                    )
                else:
                    results.add_fail("JSON-RPC get_stats", f"No result: {response}")
            else:
                results.add_fail("JSON-RPC get_stats", "No response received")
        except Exception as e:
            results.add_fail("JSON-RPC get_stats", str(e))
        
        # Terminate process
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        
        results.add_pass("Terminate sidecar process", "Clean shutdown")
        
    except Exception as e:
        results.add_fail("JSON-RPC Integration", str(e))


def main():
    """Run all tests."""
    print(f"\n{BOLD}{'='*70}")
    print(f"MediaForge Python Sidecar - Comprehensive Test Suite")
    print(f"{'='*70}{RESET}\n")
    
    try:
        test_module_imports()
        test_database_operations()
        test_file_classifier()
        test_config_loading()
        test_json_rpc_integration()
    except Exception as e:
        print(f"\n{RED}Fatal error during testing: {e}{RESET}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    success = results.summary()
    
    # Print detailed results
    print(f"\n{BOLD}Detailed Test Results:{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    for test in results.tests:
        status_color = GREEN if test['status'] == 'PASS' else RED
        print(f"{status_color}[{test['status']}]{RESET} {test['name']}")
        if 'message' in test and test['message']:
            print(f"       {test['message']}")
        if 'error' in test and test['error']:
            print(f"       Error: {test['error']}")
    
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"Total: {results.passed} passed, {results.failed} failed")
    print(f"{'='*70}\n")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
