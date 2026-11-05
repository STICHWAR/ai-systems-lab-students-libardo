import cv2
import numpy as np
from pathlib import Path


class FaceAuthenticationError(Exception):
    """Error durante el reconocimiento facial."""


class FaceAuthenticator:
    def __init__(self, models_dir=None, threshold=0.363):
        if models_dir is None:
            models_dir = Path(__file__).resolve().parent / "models"

        models_dir = Path(models_dir)

        detector_path = models_dir / "face_detection_yunet_2023mar.onnx"
        recognizer_path = models_dir / "face_recognition_sface_2021dec.onnx"

        if not detector_path.exists() or not recognizer_path.exists():
            raise FileNotFoundError("No se encontraron los modelos faciales.")

        self.detector = cv2.FaceDetectorYN_create(
            str(detector_path), "", (320, 320)
        )

        self.recognizer = cv2.FaceRecognizerSF_create(
            str(recognizer_path), ""
        )

        self.threshold = threshold

    def extract_embedding(self, image):
        """Detecta un rostro y obtiene su representación facial."""
        if image is None or not isinstance(image, np.ndarray):
            raise FaceAuthenticationError("Imagen inválida.")

        height, width = image.shape[:2]
        self.detector.setInputSize((width, height))

        _, faces = self.detector.detect(image)

        if faces is None or len(faces) == 0:
            raise FaceAuthenticationError("No se detectó ningún rostro.")

        if len(faces) > 1:
            raise FaceAuthenticationError(
                "Se detectaron varios rostros. Debe aparecer una sola persona."
            )

        aligned_face = self.recognizer.alignCrop(image, faces[0])
        embedding = self.recognizer.feature(aligned_face)

        return embedding

    def compare_embeddings(self, reference, candidate):
        """Compara dos representaciones faciales."""
        if reference is None or candidate is None:
            raise FaceAuthenticationError("Representación facial inválida.")

        similarity = self.recognizer.match(
            reference,
            candidate,
            cv2.FaceRecognizerSF_FR_COSINE
        )

        return {
            "similarity": float(similarity),
            "matched": similarity >= self.threshold
        }

    def compare_images(self, reference_image, candidate_image):
        """Compara dos imágenes que contienen un único rostro."""
        reference = self.extract_embedding(reference_image)
        candidate = self.extract_embedding(candidate_image)

        return self.compare_embeddings(reference, candidate)
