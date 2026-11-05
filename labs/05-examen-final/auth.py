import hashlib
import json
import secrets
import time
from pathlib import Path


class AuthenticationError(Exception):
    """Error relacionado con la autenticación o las sesiones."""


class SessionManager:
    def __init__(self, users_file=None, session_ttl=3600):
        if users_file is None:
            users_file = (
                Path(__file__).resolve().parent
                / "data"
                / "usuarios.json"
            )

        self.users_file = Path(users_file)
        self.session_ttl = session_ttl
        self.sessions = {}
        self.users = self._load_users()

    def _load_users(self):
        """Carga los usuarios autorizados desde el archivo JSON."""
        if not self.users_file.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de usuarios: {self.users_file}"
            )

        with self.users_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        users = data.get("usuarios", [])

        if not isinstance(users, list):
            raise AuthenticationError(
                "El formato de usuarios.json no es válido."
            )

        return users

    def find_user_by_telegram_id(self, telegram_user_id):
        """Busca un usuario por su identificador de Telegram registrado."""
        if telegram_user_id is None:
            return None

        telegram_id = str(telegram_user_id)

        for user in self.users:
            registered_id = user.get("telegram_user_id")

            if (
                registered_id is not None
                and str(registered_id) == telegram_id
            ):
                return user.copy()

        return None

    def _create_session_for_user(self, user):
        """
        Crea una sesión para un usuario previamente identificado.

        Este método es interno. No debe exponerse directamente
        como una operación disponible para los usuarios de Telegram.
        """
        if not isinstance(user, dict) or not user.get("id"):
            raise AuthenticationError("El usuario no es válido.")

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        expires_at = time.time() + self.session_ttl

        self.sessions[token_hash] = {
            "user_id": user["id"],
            "expires_at": expires_at
        }

        return {
            "token": token,
            "expires_at": expires_at,
            "user": {
                "id": user["id"],
                "nombre": user["nombre"],
                "rol": user["rol"],
                "codigo_estudiante": user.get("codigo_estudiante")
            }
        }

    def validate_session(self, token):
        """Valida un token y recupera la identidad desde el registro."""
        if not token:
            raise AuthenticationError(
                "No se proporcionó un token de sesión."
            )

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        session = self.sessions.get(token_hash)

        if session is None:
            raise AuthenticationError(
                "La sesión no existe o no es válida."
            )

        if time.time() >= session["expires_at"]:
            del self.sessions[token_hash]
            raise AuthenticationError("La sesión ha expirado.")

        user_id = session["user_id"]

        user = next(
            (
                item
                for item in self.users
                if item.get("id") == user_id
            ),
            None
        )

        if user is None:
            del self.sessions[token_hash]
            raise AuthenticationError(
                "El usuario ya no está registrado."
            )

        return {
            "id": user["id"],
            "nombre": user["nombre"],
            "rol": user["rol"],
            "codigo_estudiante": user.get("codigo_estudiante")
        }

    def revoke_session(self, token):
        """Cierra una sesión e invalida su token."""
        if not token:
            return False

        token_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        if token_hash in self.sessions:
            del self.sessions[token_hash]
            return True

        return False
