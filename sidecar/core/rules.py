"""Watch rule engine."""
import os
import shutil
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from .models import WatchRule


class RuleEngine:
    """Evaluates and executes watch rules."""

    def __init__(self, config):
        """Initialize rule engine."""
        self.config = config
        self.rules = []
        self.load_rules()

    def load_rules(self) -> None:
        """Load rules from config."""
        rules_data = self.config.get('rules', [])
        self.rules = []

        for rule_data in rules_data:
            rule = WatchRule(
                name=rule_data.get('name', ''),
                match=rule_data.get('match', {}),
                actions=rule_data.get('actions', [])
            )
            self.rules.append(rule)

    def evaluate(self, file_info: Dict[str, Any], metadata: Dict[str, Any]) -> List[WatchRule]:
        """Evaluate all rules against a file."""
        matched_rules = []

        for rule in self.rules:
            if self._match_rule(rule, file_info, metadata):
                matched_rules.append(rule)

        return matched_rules

    def _match_rule(self, rule: WatchRule, file_info: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Check if a rule matches a file."""
        match_conditions = rule.match

        # Check file type
        if 'file_type' in match_conditions:
            if file_info.get('file_type') != match_conditions['file_type']:
                return False

        # Check extension
        if 'extension' in match_conditions:
            if file_info.get('extension') != match_conditions['extension']:
                return False

        # Check duration threshold
        if 'duration_gt' in match_conditions:
            duration = metadata.get('duration_seconds', 0)
            if duration <= match_conditions['duration_gt']:
                return False

        if 'duration_lt' in match_conditions:
            duration = metadata.get('duration_seconds', 0)
            if duration >= match_conditions['duration_lt']:
                return False

        # Check studio
        if 'studio' in match_conditions:
            if metadata.get('studio') != match_conditions['studio']:
                return False

        # Check title pattern
        if 'title_pattern' in match_conditions:
            title = metadata.get('title', '')
            pattern = match_conditions['title_pattern']
            if not re.search(pattern, title, re.IGNORECASE):
                return False

        # Check content mode
        if 'content_mode' in match_conditions:
            if file_info.get('content_mode') != match_conditions['content_mode']:
                return False

        return True

    def execute_action(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action."""
        action_type = action.get('type')

        if action_type == 'copy_to':
            return self._action_copy_to(action, file_path, context)

        elif action_type == 'move_to':
            return self._action_move_to(action, file_path, context)

        elif action_type == 'notify':
            return self._action_notify(action, file_path, context)

        elif action_type == 'generate_thumbnail':
            return self._action_generate_thumbnail(action, file_path, context)

        elif action_type == 'detect_faces':
            return self._action_detect_faces(action, file_path, context)

        return {'success': False, 'error': f'Unknown action type: {action_type}'}

    def _interpolate_path(self, template: str, context: Dict[str, Any]) -> str:
        """Interpolate path variables."""
        result = template

        # Replace context variables
        for key, value in context.items():
            result = result.replace(f'{{{key}}}', str(value))

        # Replace date/time
        now = datetime.now()
        result = result.replace('{year}', str(now.year))
        result = result.replace('{month}', f'{now.month:02d}')
        result = result.replace('{day}', f'{now.day:02d}')

        return result

    def _resolve_conflict(self, dest_path: str, conflict_resolution: str) -> str:
        """Resolve file name conflicts."""
        if not os.path.exists(dest_path):
            return dest_path

        strategy = conflict_resolution or self.config.get('conflict_resolution', 'rename_increment')

        if strategy == 'skip':
            return None

        elif strategy == 'overwrite':
            return dest_path

        elif strategy == 'rename_increment':
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(f'{base}_{counter:03d}{ext}'):
                counter += 1
            return f'{base}_{counter:03d}{ext}'

        return dest_path

    def _action_copy_to(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Copy file to destination."""
        try:
            dest_template = action.get('destination', '')
            dest_path = self._interpolate_path(dest_template, context)

            # Resolve conflicts
            conflict_resolution = action.get('conflict_resolution', self.config.get('conflict_resolution'))
            dest_path = self._resolve_conflict(dest_path, conflict_resolution)

            if dest_path is None:
                return {'success': False, 'error': 'Destination already exists (skip)', 'destination': None}

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy file
            shutil.copy2(file_path, dest_path)

            return {'success': True, 'destination': dest_path}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_move_to(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Move file to destination."""
        try:
            dest_template = action.get('destination', '')
            dest_path = self._interpolate_path(dest_template, context)

            # Resolve conflicts
            conflict_resolution = action.get('conflict_resolution', self.config.get('conflict_resolution'))
            dest_path = self._resolve_conflict(dest_path, conflict_resolution)

            if dest_path is None:
                return {'success': False, 'error': 'Destination already exists (skip)', 'destination': None}

            # Create destination directory
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Move file
            shutil.move(file_path, dest_path)

            return {'success': True, 'destination': dest_path}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_notify(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return notification."""
        title = action.get('title', 'MediaForge')
        message_template = action.get('message', '')
        message = self._interpolate_path(message_template, context)

        return {
            'success': True,
            'notification': {
                'title': title,
                'message': message,
                'level': action.get('level', 'info')
            }
        }

    def _action_generate_thumbnail(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate thumbnail."""
        try:
            from .metadata_engine import MetadataEngine

            output_template = action.get('output', '{filename}.jpg')
            output_path = self._interpolate_path(output_template, context)

            # Create output directory
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            engine = MetadataEngine()
            size = action.get('size', 256)
            success = engine.extract_thumbnail(file_path, output_path, size)

            if success:
                return {'success': True, 'thumbnail_path': output_path}
            else:
                return {'success': False, 'error': 'Thumbnail extraction failed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _action_detect_faces(self, action: Dict[str, Any], file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect faces in file."""
        try:
            from .face_engine import FaceEngine

            # This requires db_manager, which is passed via context
            face_engine = context.get('face_engine')
            if not face_engine:
                return {'success': False, 'error': 'Face engine not available'}

            results = face_engine.process_file(file_path)
            return {'success': True, 'faces_detected': len(results), 'matches': results}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_rule(self, rule: WatchRule, file_path: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute all actions in a rule."""
        results = []

        for action in rule.actions:
            result = self.execute_action(action, file_path, context)
            result['action_type'] = action.get('type')
            results.append(result)

        return results
