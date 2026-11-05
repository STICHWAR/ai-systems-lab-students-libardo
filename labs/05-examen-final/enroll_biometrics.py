import cv2
from pathlib import Path

from auth import SessionManager
from face_auth import FaceAuthenticator, FaceAuthenticationError
from biometric_store import BiometricStore, BiometricStoreError


class BiometricEnrollment:
    """Registra embeddings faciales de usuarios autorizados."""

    def __init__(self):
        self.session_manager = SessionManager()
        self.biometric_store = BiometricStore()
        self.face_authenticator = FaceAuthenticator()

    def enroll(self, user_id, image_path, consent=False):
        """Registra el embedding facial de un usuario."""
        if consent is not True:
            raise ValueError(
                "Se requiere consentimiento explícito para el registro."
            )

        user = next(
            (
                item for item in self.session_manager.users
                if item.get("id") == user_id
            ),
            None
        )

        if user is None:
            raise ValueError("El usuario no está registrado.")

        path = Path(image_path)

        if not path.is_file():
            raise FileNotFoundError("No se encontró la fotografía.")

        image = cv2.imread(str(path))

        if image is None:
            raise ValueError("No se pudo leer la fotografía.")

        try:
            embedding = self.face_authenticator.extract_embedding(image)
            self.biometric_store.save_embedding(user_id, embedding)
        except (FaceAuthenticationError, BiometricStoreError):
            raise
        finally:
            del image

        return {
            "registered": True,
            "user_id": user_id,
            "embedding_saved": True
        }


def main():
    enrollment = BiometricEnrollment()

    try:
        print("=== REGISTRO BIOMÉTRICO ===")
        print("Usuarios registrados:")

        for user in enrollment.session_manager.users:
            print(
                f"- {user.get('id')} ({user.get('rol')})"
            )

        user_id = input("\nID interno del usuario: ").strip()
        image_path = input("Ruta de la fotografía: ").strip()

        consent_answer = input(
            "¿La persona autorizó explícitamente este registro? (si/no): "
        ).strip().lower()

        result = enrollment.enroll(
            user_id=user_id,
            image_path=image_path,
            consent=consent_answer == "si"
        )

        print("\nRegistro completado.")
        print("Usuario:", result["user_id"])
        print("Embedding almacenado correctamente.")

    except Exception as error:
        print("\nNo se pudo completar el registro:", error)


if __name__ == "__main__":
    main()
