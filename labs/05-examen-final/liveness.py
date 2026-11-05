import cv2
import numpy as np

from pathlib import Path
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class LivenessError(Exception):
    """Error durante la comprobación de vida."""


class LivenessDetector:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = (
                Path(__file__).resolve().parent
                / "models"
                / "face_landmarker.task"
            )

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"No se encontró el modelo: {self.model_path}"
            )

        base_options = python.BaseOptions(
            model_asset_path=str(self.model_path)
        )

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1
        )

        self.landmarker = vision.FaceLandmarker.create_from_options(
            options
        )

    @staticmethod
    def _distance(point_a, point_b):
        return np.linalg.norm(
            np.array([point_a.x, point_a.y])
            - np.array([point_b.x, point_b.y])
        )

    def _eye_aspect_ratio(self, landmarks, indices):
        p1, p2, p3, p4, p5, p6 = [
            landmarks[index] for index in indices
        ]

        vertical_1 = self._distance(p2, p6)
        vertical_2 = self._distance(p3, p5)
        horizontal = self._distance(p1, p4)

        if horizontal == 0:
            return 0.0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def _head_position(self, landmarks):
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        nose = landmarks[1]

        eye_distance = self._distance(left_eye, right_eye)

        if eye_distance == 0:
            return None

        center_x = (left_eye.x + right_eye.x) / 2
        center_y = (left_eye.y + right_eye.y) / 2

        return (
            (nose.x - center_x) / eye_distance,
            (nose.y - center_y) / eye_distance
        )

    def analyze_video(self, video_path):
        video_path = str(video_path)

        if not Path(video_path).exists():
            raise FileNotFoundError(
                f"No se encontró el vídeo: {video_path}"
            )

        capture = cv2.VideoCapture(video_path)

        if not capture.isOpened():
            raise LivenessError("No se pudo abrir el vídeo.")

        fps = capture.get(cv2.CAP_PROP_FPS)

        if not np.isfinite(fps) or fps <= 0:
            fps = 30.0

        frame_count = 0
        face_frames = 0
        blink_count = 0

        eye_was_closed = False
        head_positions = []

        left_eye_indices = [33, 160, 158, 133, 153, 144]
        right_eye_indices = [362, 385, 387, 263, 373, 380]

        try:
            while True:
                success, frame = capture.read()

                if not success:
                    break

                frame_count += 1

                rgb_frame = cv2.cvtColor(
                    frame, cv2.COLOR_BGR2RGB
                )

                mp_image = vision.Image(
                    image_format=vision.ImageFormat.SRGB,
                    data=rgb_frame
                )

                timestamp_ms = int((frame_count - 1) * 1000 / fps)

                result = self.landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms
                )

                if not result.face_landmarks:
                    continue

                if len(result.face_landmarks) > 1:
                    continue

                landmarks = result.face_landmarks[0]
                face_frames += 1

                left_ear = self._eye_aspect_ratio(
                    landmarks, left_eye_indices
                )

                right_ear = self._eye_aspect_ratio(
                    landmarks, right_eye_indices
                )

                eye_ratio = (left_ear + right_ear) / 2.0

                # Detectar cierre y reapertura de los ojos.
                if eye_ratio < 0.20:
                    eye_was_closed = True

                elif eye_ratio > 0.23 and eye_was_closed:
                    blink_count += 1
                    eye_was_closed = False

                # Registrar cambios en la orientación facial.
                position = self._head_position(landmarks)

                if position is not None:
                    head_positions.append(position)

        finally:
            capture.release()

        if frame_count == 0:
            raise LivenessError("El vídeo no contiene fotogramas.")

        if face_frames < 5:
            raise LivenessError(
                "No se detectó un rostro durante suficientes fotogramas."
            )

        if len(head_positions) < 5:
            raise LivenessError(
                "No hay suficientes datos para analizar el movimiento."
            )

        positions = np.array(head_positions)

        movement_x = float(
            np.max(positions[:, 0]) - np.min(positions[:, 0])
        )

        movement_y = float(
            np.max(positions[:, 1]) - np.min(positions[:, 1])
        )

        head_movement = max(movement_x, movement_y) >= 0.12

        blink_detected = blink_count >= 1

        return {
            "live": blink_detected and head_movement,
            "blink_detected": blink_detected,
            "blink_count": blink_count,
            "head_movement_detected": head_movement,
            "movement_x": movement_x,
            "movement_y": movement_y,
            "face_frames": face_frames,
            "total_frames": frame_count
        }

    def close(self):
        self.landmarker.close()
