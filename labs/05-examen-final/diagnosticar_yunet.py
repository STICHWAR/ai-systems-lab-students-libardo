"""Diagnóstico local YuNet: no persiste imágenes, embeddings ni landmarks."""
import argparse
from pathlib import Path

import cv2
import numpy as np

from face_auth import FaceAuthenticator
from image_normalization import load_enrollment_bgr


def usable_landmarks(face: np.ndarray, width: int, height: int) -> bool:
    """Comprueba geometría mínima sin exponer coordenadas faciales."""
    x, y, box_width, box_height = face[:4]
    landmarks = face[4:14].reshape(5, 2)
    return bool(
        np.isfinite(face).all()
        and box_width > 0
        and box_height > 0
        and 0 <= x < width
        and 0 <= y < height
        and x + box_width <= width
        and y + box_height <= height
        and (landmarks[:, 0] >= 0).all()
        and (landmarks[:, 0] < width).all()
        and (landmarks[:, 1] >= 0).all()
        and (landmarks[:, 1] < height).all()
    )


def detect(image: np.ndarray, threshold: float) -> tuple[list[float], bool]:
    auth = FaceAuthenticator(detection_threshold=threshold)
    height, width = image.shape[:2]
    auth.detector.setInputSize((width, height))
    _, faces = auth.detector.detect(image)
    if faces is None:
        return [], True
    return [float(score) for score in faces[:, 14]], all(
        usable_landmarks(face, width, height) for face in faces
    )


def report(name: str, image: np.ndarray, thresholds: list[float]) -> None:
    height, width = image.shape[:2]
    for threshold in thresholds:
        scores, valid = detect(image, threshold)
        rendered_scores = ",".join(f"{score:.3f}" for score in scores) or "—"
        print(
            f"{name} | {width}×{height} | umbral={threshold:.2f} | "
            f"rostros={len(scores)} | puntuaciones={rendered_scores} | "
            f"landmarks_utilizables={valid}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fotos", nargs="+")
    parser.add_argument("--umbrales", type=float, nargs="+", default=[0.80, 0.85, 0.90])
    parser.add_argument("--regresion", action="store_true")
    args = parser.parse_args()

    images = [(Path(path).name, load_enrollment_bgr(path)) for path in args.fotos]
    print("Archivo | Dimensiones | Umbral | Rostros | Puntuaciones | Landmarks utilizables")
    for name, image in images:
        report(name, image, args.umbrales)

    if args.regresion:
        blank = np.zeros_like(images[0][1])
        # Dos copias en memoria del mismo rostro autorizado prueban que el
        # control sigue rechazando más de un rostro. No se escribe archivo.
        composite = np.hstack([images[-1][1], images[-1][1]])
        report("regresion_sin_rostro_en_memoria", blank, [min(args.umbrales)])
        report("regresion_dos_rostros_en_memoria", composite, [min(args.umbrales)])


if __name__ == "__main__":
    main()
