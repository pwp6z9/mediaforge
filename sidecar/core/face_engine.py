"""Face detection and recognition engine."""
import os
import sys
from typing import List, Tuple, Optional, Dict
import numpy as np


class FaceEngine:
    """Handles face detection and recognition."""

    def __init__(self, db_manager, threshold: float = 0.6):
        """Initialize face engine."""
        self.db = db_manager
        self.threshold = threshold
        self.known_encodings = np.array([])
        self.known_ids = []
        self.face_recognition_available = self._check_face_recognition()
        self.cv2_available = self._check_cv2()

    def _check_face_recognition(self) -> bool:
        """Check if face_recognition is available."""
        try:
            import face_recognition
            return True
        except ImportError:
            print("Warning: face_recognition not installed", file=sys.stderr)
            return False

    def _check_cv2(self) -> bool:
        """Check if OpenCV is available."""
        try:
            import cv2
            return True
        except ImportError:
            print("Warning: opencv-python not installed", file=sys.stderr)
            return False

    def load_encodings(self) -> int:
        """Load all face encodings from database."""
        try:
            encodings, person_ids = self.db.get_all_encodings()

            if encodings:
                self.known_encodings = np.array(encodings, dtype=object)
                self.known_ids = person_ids
                return len(encodings)
            else:
                self.known_encodings = np.array([])
                self.known_ids = []
                return 0

        except Exception as e:
            print(f"Error loading encodings: {e}", file=sys.stderr)
            return 0

    def extract_faces_from_image(self, path: str) -> List[Tuple[np.ndarray, Dict]]:
        """Extract faces from an image."""
        if not self.face_recognition_available:
            return []

        try:
            import face_recognition

            image = face_recognition.load_image_file(path)
            face_locations = face_recognition.face_locations(image, model='hog')
            face_encodings = face_recognition.face_encodings(image, face_locations)

            results = []
            for encoding, location in zip(face_encodings, face_locations):
                results.append((encoding, {
                    'top': location[0],
                    'right': location[1],
                    'bottom': location[2],
                    'left': location[3]
                }))

            return results

        except Exception as e:
            print(f"Error extracting faces from image: {e}", file=sys.stderr)
            return []

    def extract_faces_from_video(self, path: str, sample_fps: int = 1, max_duration: int = 30) -> List[np.ndarray]:
        """Extract faces from a video."""
        if not self.cv2_available or not self.face_recognition_available:
            return []

        try:
            import cv2
            import face_recognition

            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return []

            fps = cap.get(cv2.CAP_PROP_FPS) or 24
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_interval = max(1, int(fps / sample_fps))

            encodings = []
            frame_count = 0
            max_frames = int(max_duration * fps)

            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Resize for faster processing
                    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

                    # Detect and encode faces
                    face_locations = face_recognition.face_locations(small_frame, model='hog')
                    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

                    encodings.extend(face_encodings)

                frame_count += 1

            cap.release()

            # Deduplicate by distance
            if encodings:
                encodings = self._dedup_encodings(encodings)

            return encodings

        except Exception as e:
            print(f"Error extracting faces from video: {e}", file=sys.stderr)
            return []

    def _dedup_encodings(self, encodings: List[np.ndarray], distance_threshold: float = 0.4) -> List[np.ndarray]:
        """Deduplicate encodings by distance."""
        if not encodings:
            return []

        unique = [encodings[0]]

        for enc in encodings[1:]:
            # Check distance to all unique encodings
            distances = [np.linalg.norm(enc - unique_enc) for unique_enc in unique]
            if min(distances) > distance_threshold:
                unique.append(enc)

        return unique

    def match_face(self, encoding: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Match a face encoding to known faces."""
        if len(self.known_encodings) == 0:
            return None, None

        try:
            import face_recognition

            # Compare with all known encodings
            distances = face_recognition.face_distance(self.known_encodings, encoding)

            if len(distances) == 0:
                return None, None

            min_distance = np.min(distances)
            min_index = np.argmin(distances)

            if min_distance <= self.threshold:
                return self.known_ids[min_index], float(min_distance)

            return None, None

        except Exception as e:
            print(f"Error matching face: {e}", file=sys.stderr)
            return None, None

    def process_file(self, path: str) -> List[Tuple[str, float]]:
        """Full pipeline to extract and match faces in a file."""
        if not os.path.exists(path):
            return []

        ext = os.path.splitext(path)[1].lower().lstrip('.')
        results = []

        try:
            if ext in {'jpg', 'jpeg', 'png', 'tiff', 'tif', 'webp', 'bmp', 'gif'}:
                faces = self.extract_faces_from_image(path)
                for encoding, location in faces:
                    person_id, distance = self.match_face(encoding)
                    if person_id:
                        results.append((person_id, distance))
                        # Log encounter
                        self.db.add_encounter(path, person_id, encoding.tobytes(), distance)

            elif ext in {'mkv', 'mp4', 'avi', 'mov', 'webm', 'wmv', 'm4v', 'mpg', 'mpeg', 'flv'}:
                encodings = self.extract_faces_from_video(path)
                for encoding in encodings:
                    person_id, distance = self.match_face(encoding)
                    if person_id:
                        results.append((person_id, distance))
                        self.db.add_encounter(path, person_id, encoding.tobytes(), distance)

        except Exception as e:
            print(f"Error processing file {path}: {e}", file=sys.stderr)

        return results

    def add_person(self, name: str, folder_path: str, sample_images: List[str]) -> str:
        """Create a new person and extract encodings from sample images."""
        person_id = self.db.upsert_person(name, folder_path)

        try:
            for img_path in sample_images:
                if os.path.exists(img_path):
                    faces = self.extract_faces_from_image(img_path)
                    for encoding, _ in faces:
                        self.db.add_encoding(person_id, encoding.tobytes(), img_path)

            # Reload encodings
            self.load_encodings()

        except Exception as e:
            print(f"Error adding person {name}: {e}", file=sys.stderr)

        return person_id
