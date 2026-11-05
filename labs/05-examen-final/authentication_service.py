import cv2
import numpy as np
from pathlib import Path

from auth import SessionManager, AuthenticationError
from face_auth import FaceAuthenticator, FaceAuthenticationError
from liveness import LivenessDetector, LivenessError
from biometric_store import BiometricStore, BiometricStoreError


class AuthenticationService:
    """Coordina la autenticación facial y la creación de sesiones."""

    def __init__(
        self,
        session_manager=None,
        biometric_store=None,
        face_authenticator=None,
        liveness_detector=None
    ):
        self.session_manager = session_manager or SessionManager()
        self.biometric_store = biometric_store or BiometricStore()
        self.face_authenticator = (
            face_authenticator or FaceAuthenticator()
        )
        self.liveness_detector = (
            liveness_detector or LivenessDetector()
        )

    def _extract_video_frame(self, video_path):
        """Extrae un fotograma del punto medio del video."""
        path = Path(video_path)

        if not path.is_file():
            raise AuthenticationError(
                "No se encontró el video de autenticación."
            )

        capture = cv2.VideoCapture(str(path))

        if not capture.isOpened():
            raise AuthenticationError(
                "No se pudo abrir el video de autenticación."
            )

        try:
            frame_count = int(
                capture.get(cv2.CAP_PROP_FRAME_COUNT)
            )

            fps = capture.get(cv2.CAP_PROP_FPS)

            if (
                frame_count <= 0
                or not np.isfinite(fps)
                or fps <= 0
            ):
                raise AuthenticationError(
                    "El video no contiene información válida."
                )

            duration = frame_count / fps

            if duration < 1 or duration > 60:
                raise AuthenticationError(
                    "El video debe durar entre 1 y 60 segundos."
                )

            middle_frame = frame_count // 2

            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                middle_frame
            )

            success, frame = capture.read()

            if not success or frame is None:
                raise AuthenticationError(
                    "No se pudo extraer un fotograma del video."
                )

            return frame

        finally:
            capture.release()

    def authenticate(self, telegram_user_id, video_path):
        """
        Autentica al usuario mediante Telegram, reconocimiento
        facial y prueba de vida.
        """
        user = self.session_manager.find_user_by_telegram_id(
            telegram_user_id
        )

        if user is None:
            raise AuthenticationError(
                "El identificador de Telegram no está autorizado."
            )

        try:
            reference_embedding = (
                self.biometric_store.load_embedding(user["id"])
            )

            liveness_result = (
                self.liveness_detector.analyze_video(video_path)
            )

            if not liveness_result.get("live", False):
                raise AuthenticationError(
                    "La prueba de vida no fue satisfactoria."
                )

            frame = self._extract_video_frame(video_path)

            candidate_embedding = (
                self.face_authenticator.extract_embedding(frame)
            )

            face_result = (
                self.face_authenticator.compare_embeddings(
                    reference_embedding,
                    candidate_embedding
                )
            )

            if not face_result.get("matched", False):
                raise AuthenticationError(
                    "El rostro no coincide con el usuario registrado."
                )

            session = self.session_manager._create_session_for_user(
                user
            )

            return {
                "authenticated": True,
                "session": session,
                "verification": {
                    "face_verified": True,
                    "liveness_verified": True
                }
            }

        except (
            BiometricStoreError,
            FaceAuthenticationError,
            LivenessError,
            FileNotFoundError
        ) as error:
            raise AuthenticationError(
                f"No fue posible completar la autenticación: {error}"
            ) from error

    def close(self):
        """Libera los recursos del detector de prueba de vida."""
        if self.liveness_detector is not None:
            self.liveness_detector.close()
