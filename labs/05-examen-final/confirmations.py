"""Confirmaciones de escritura ligadas a usuario, chat, tool y argumentos."""
from __future__ import annotations

import asyncio
import json
import secrets
import time
from dataclasses import dataclass


class ConfirmationError(PermissionError):
    """La confirmación no corresponde a una solicitud pendiente y válida."""


@dataclass
class PendingConfirmation:
    token: str
    telegram_user_id: int
    chat_id: int
    tool_name: str
    arguments_json: str
    future: asyncio.Future[bool]
    expires_at: float


class ConfirmationRegistry:
    """Mantiene a lo sumo una confirmación de escritura por usuario.

    Las decisiones se aceptan una sola vez y sólo desde el mismo usuario y chat
    que originaron exactamente la llamada de herramienta pendiente.
    """

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._pending: dict[int, PendingConfirmation] = {}

    @staticmethod
    def canonical_arguments(arguments: dict) -> str:
        return json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def create(
        self,
        telegram_user_id: int,
        chat_id: int,
        tool_name: str,
        arguments: dict,
        future: asyncio.Future[bool],
        timeout_seconds: float = 45,
    ) -> PendingConfirmation:
        user_id = int(telegram_user_id)
        previous = self._pending.get(user_id)
        if previous and self.clock() < previous.expires_at and not previous.future.done():
            raise ConfirmationError("Ya existe una confirmación pendiente")
        request = PendingConfirmation(
            token=secrets.token_urlsafe(18),
            telegram_user_id=user_id,
            chat_id=int(chat_id),
            tool_name=tool_name,
            arguments_json=self.canonical_arguments(arguments),
            future=future,
            expires_at=self.clock() + timeout_seconds,
        )
        self._pending[user_id] = request
        return request

    def resolve(
        self,
        telegram_user_id: int,
        chat_id: int,
        token: str,
        decision: bool,
    ) -> bool:
        request = self._pending.get(int(telegram_user_id))
        if (
            request is None
            or request.future.done()
            or self.clock() > request.expires_at
            or request.token != token
            or request.chat_id != int(chat_id)
        ):
            return False
        self._pending.pop(request.telegram_user_id, None)
        request.future.set_result(bool(decision))
        return True

    def cancel(self, telegram_user_id: int, token: str) -> None:
        request = self._pending.get(int(telegram_user_id))
        if request and request.token == token:
            self._pending.pop(request.telegram_user_id, None)
