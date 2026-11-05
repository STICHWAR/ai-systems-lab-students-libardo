"""Carga local de fotos de enrolamiento sin guardar copias ni biometría."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps


MAX_ENROLLMENT_SIDE = 1920


def load_enrollment_bgr(path: str | Path, max_side: int = MAX_ENROLLMENT_SIDE) -> np.ndarray:
    """Aplica orientación EXIF, convierte RGB a BGR y reduce proporcionalmente si hace falta."""
    if max_side <= 0:
        raise ValueError("max_side debe ser positivo")

    with Image.open(path) as source:
        rgb = np.asarray(ImageOps.exif_transpose(source).convert("RGB"))

    height, width = rgb.shape[:2]
    scale = min(1.0, max_side / max(height, width))
    if scale < 1.0:
        rgb = cv2.resize(
            rgb,
            (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
