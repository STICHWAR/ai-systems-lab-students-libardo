"""Descarga y verifica modelos oficiales de OpenCV Zoo para uso local."""
import hashlib
from pathlib import Path
from urllib.request import urlretrieve

# Las URLs github.com/raw siguen correctamente los archivos Git LFS del Zoo.
BASE = "https://github.com/opencv/opencv_zoo/raw/main/models"
MODELS = {
    "face_detection_yunet/face_detection_yunet_2023mar.onnx": {
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "min_size": 100_000,
    },
    "face_recognition_sface/face_recognition_sface_2021dec.onnx": {
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "min_size": 1_000_000,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model:
        for block in iter(lambda: model.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, expected: dict[str, object]) -> None:
    if path.stat().st_size < expected["min_size"]:
        raise RuntimeError(f"Descarga inválida o puntero Git LFS: {path.name}")
    actual = sha256(path)
    if actual != expected["sha256"]:
        raise RuntimeError(f"Checksum SHA-256 inválido para {path.name}: {actual}")


if __name__ == "__main__":
    target = Path(__file__).parent / "models"
    target.mkdir(exist_ok=True)
    for src, expected in MODELS.items():
        filename = src.split("/")[-1]
        path = target / filename
        if path.exists():
            try:
                verify(path, expected)
                print("Existe y fue verificado:", path)
                continue
            except RuntimeError:
                path.unlink()
        print("Descargando:", filename)
        try:
            urlretrieve(f"{BASE}/{src}", path)
            verify(path, expected)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        print("Descargado y verificado:", path)
