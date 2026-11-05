import re
import numpy as np
from pathlib import Path


class BiometricStoreError(Exception):
    """Error al almacenar o recuperar datos biométricos."""


class BiometricStore:
    def __init__(self, storage_dir=None):
        if storage_dir is None:
            storage_dir = (
                Path(__file__).resolve().parent / "biometric_data"
            )

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, user_id):
        """Obtiene una ruta segura a partir del ID interno del usuario."""
        if not isinstance(user_id, str):
            raise BiometricStoreError("El ID del usuario no es válido.")

        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", user_id):
            raise BiometricStoreError("El formato del ID no es válido.")

        return self.storage_dir / f"{user_id}.npz"

    def save_embedding(self, user_id, embedding):
        """Guarda el embedding facial de un usuario."""
        if embedding is None:
            raise BiometricStoreError("El embedding está vacío.")

        array = np.asarray(embedding, dtype=np.float32)

        if array.size == 0 or not np.all(np.isfinite(array)):
            raise BiometricStoreError("El embedding no es válido.")

        path = self._get_path(user_id)

        np.savez_compressed(path, embedding=array)

        return path

    def load_embedding(self, user_id):
        """Recupera el embedding facial de un usuario."""
        path = self._get_path(user_id)

        if not path.exists():
            raise BiometricStoreError(
                "El usuario no tiene un registro biométrico."
            )

        try:
            with np.load(path, allow_pickle=False) as data:
                embedding = np.asarray(
                    data["embedding"],
                    dtype=np.float32
                )
        except (OSError, KeyError, ValueError) as error:
            raise BiometricStoreError(
                "No se pudo recuperar el registro biométrico."
            ) from error

        if embedding.size == 0 or not np.all(np.isfinite(embedding)):
            raise BiometricStoreError("El embedding almacenado no es válido.")

        return embedding

    def delete_embedding(self, user_id):
        """Elimina el registro biométrico de un usuario."""
        path = self._get_path(user_id)

        if not path.exists():
            return False

        path.unlink()
        return True
