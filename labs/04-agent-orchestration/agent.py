
"""Agente: un ciclo en el que el LLM decide el siguiente paso.

El modelo puede solicitar herramientas, pero la ejecución está controlada
por el código. Las herramientas con efectos requieren autorización.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from llm_client import LLMClient, LLMResponse, Message, ToolCall
from prompts import build_agent_messages
from tools import Tool

MAX_STEPS = 5

ConfirmFn = Callable[[Tool, dict[str, Any]], Awaitable[bool]]

LIMIT_MESSAGE = (
    "[Aviso del sistema] Se alcanzó el límite de pasos: ya no puedes usar "
    "herramientas. Responde ahora al estudiante con la información que ya "
    "tienes y di qué quedó pendiente."
)

REJECTED = "El usuario NO autorizó esta acción, así que no se ejecutó."


@dataclass
class ToolRun:
    call: ToolCall
    status: Literal["ok", "error", "rechazada"]
    result: str


@dataclass
class AgentStep:
    response: LLMResponse
    tool_runs: list[ToolRun] = field(default_factory=list)


@dataclass
class AgentAnswer:
    text: str
    steps: list[AgentStep]
    messages: list[Message]
    stopped_by_limit: bool


class Agent:
    def __init__(
        self,
        llm: LLMClient,
        tools: list[Tool],
        confirm: ConfirmFn,
        max_steps: int = MAX_STEPS,
    ):
        if max_steps < 1:
            raise ValueError("max_steps debe ser mayor que cero.")

        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}

        if len(self.tools) != len(tools):
            raise ValueError("Hay dos tools con el mismo nombre.")

        self.confirm = confirm
        self.max_steps = max_steps

    async def run(
        self,
        question: str,
        history: list[Message] | None = None,
    ) -> AgentAnswer:

        if not isinstance(question, str) or not question.strip():
            raise ValueError("La pregunta no puede estar vacía.")

        messages = build_agent_messages(history or [], question)
        definitions = [
            tool.definition()
            for tool in self.tools.values()
        ]

        steps: list[AgentStep] = []

        for _ in range(self.max_steps):

            response = self.llm.chat(
                messages,
                tools=definitions,
            )

            if not response.tool_calls:
                steps.append(AgentStep(response))

                return AgentAnswer(
                    text=response.text,
                    steps=steps,
                    messages=messages,
                    stopped_by_limit=False,
                )

            messages.append(response.as_message())

            step = AgentStep(response)

            for call in response.tool_calls:
                tool_run = await self.execute(call)
                step.tool_runs.append(tool_run)

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": tool_run.result,
                })

            steps.append(step)

        messages.append({
            "role": "user",
            "content": LIMIT_MESSAGE,
        })

        final = self.llm.chat(
            messages,
            tools=definitions,
            allow_tools=False,
        )

        steps.append(AgentStep(final))

        return AgentAnswer(
            text=final.text,
            steps=steps,
            messages=messages,
            stopped_by_limit=True,
        )

    async def execute(self, call: ToolCall) -> ToolRun:
        """Ejecuta una herramienta solicitada por el modelo."""

        tool = self.tools.get(call.name)

        if tool is None:
            return ToolRun(
                call,
                "error",
                f"Error: no existe la herramienta {call.name!r}.",
            )

        try:
            arguments = call.arguments()

            if not isinstance(arguments, dict):
                raise ValueError("Los argumentos deben ser un objeto JSON.")

        except (ValueError, TypeError) as exc:
            return ToolRun(
                call,
                "error",
                f"Error en los argumentos: {exc}",
            )

        # Las herramientas que modifican información necesitan autorización.
        if not tool.read_only:
            try:
                authorized = await self.confirm(tool, arguments)
            except Exception:
                return ToolRun(
                    call,
                    "error",
                    "No fue posible verificar la autorización. Acción cancelada.",
                )

            if not authorized:
                return ToolRun(
                    call,
                    "rechazada",
                    REJECTED,
                )

        try:
            result = await tool.run(arguments)

            return ToolRun(
                call,
                "ok",
                str(result),
            )

        except Exception:
            # No se exponen detalles internos al LLM.
            return ToolRun(
                call,
                "error",
                "La herramienta no pudo completar la operación. "
                "Verifica los argumentos o el servicio correspondiente.",
            )
