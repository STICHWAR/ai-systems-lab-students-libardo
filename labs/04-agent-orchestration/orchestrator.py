
"""Orquestador: compone LLM, RAG, tools locales y MCP en un solo asistente.

Dos estrategias para decidir qué capacidad usar:

  modo "router":
      pregunta → router → directa | documentos | acciones

  modo "agente":
      pregunta → agente con todas las capacidades como tools

El rol se recibe desde el contexto autenticado de la aplicación.
Nunca se obtiene de los argumentos enviados por el LLM.
"""

from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Literal

from agent import MAX_STEPS, Agent, AgentAnswer, AgentStep, ConfirmFn
from capabilities import rag_tool
from config import load_rag_settings, load_settings
from embeddings import Embedder
from llm_client import LLMClient, LLMResponse, Message
from mcp_client import load_mcp_tools, open_client
from prompts import build_direct_messages
from rag import CourseRAG, ROLE_ACCESS
from router import RouterResult, route
from tools import LOCAL_TOOLS, Tool
from vector_store import VectorStore


Mode = Literal["router", "agente"]


@dataclass
class OrchestratorAnswer:
    text: str
    mode: Mode
    routing: RouterResult | None = None
    steps: list[AgentStep] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    responses: list[LLMResponse] = field(default_factory=list)
    stopped_by_limit: bool = False

    def tools_used(self) -> list[str]:
        return [
            run.call.name
            for step in self.steps
            for run in step.tool_runs
        ]


class Orchestrator:

    def __init__(
        self,
        llm: LLMClient,
        rag: CourseRAG,
        action_tools: list[Tool],
        confirm: ConfirmFn,
        max_steps: int = MAX_STEPS,
    ):
        self.llm = llm
        self.rag = rag
        self.action_tools = action_tools
        self.confirm = confirm
        self.max_steps = max_steps

        # Agente exclusivo para ejecutar acciones.
        # No incluye la herramienta RAG.
        self.actions_agent = Agent(
            llm,
            action_tools,
            confirm,
            max_steps,
        )

    async def answer(
        self,
        question: str,
        history: list[Message] | None = None,
        mode: Mode = "agente",
        authenticated_role: str = "publico",
    ) -> OrchestratorAnswer:
        """Procesa una pregunta respetando el rol de la sesión autenticada.

        authenticated_role debe proceder de la autenticación de la aplicación.
        No debe establecerse usando texto del usuario ni argumentos del LLM.
        """

        if authenticated_role not in ROLE_ACCESS:
            raise PermissionError(
                "No existe un rol válido para esta sesión."
            )

        history = history or []

        # Crear el agente para esta consulta con una herramienta RAG
        # limitada al rol autenticado.
        current_agent = Agent(
            self.llm,
            [
                rag_tool(
                    self.rag,
                    authenticated_role=authenticated_role,
                ),
                *self.action_tools,
            ],
            self.confirm,
            self.max_steps,
        )

        # Modo agente: el modelo decide qué herramientas utilizar.
        if mode == "agente":
            result = await current_agent.run(question, history)
            return self._from_agent(result, mode)

        # Modo router: el software clasifica la pregunta.
        if mode == "router":
            routing = route(self.llm, question)
            ruta = routing.decision.ruta

            # Ruta 1: respuesta directa del LLM.
            if ruta == "directa":
                response = self.llm.chat(
                    build_direct_messages(history, question)
                )

                answer = OrchestratorAnswer(
                    text=response.text,
                    mode=mode,
                    responses=[response],
                )

            # Ruta 2: consulta documental con permisos.
            elif ruta == "documentos":
                rag_answer = self.rag.answer(
                    question,
                    history,
                    role=authenticated_role,
                )

                sources = sorted({
                    result.chunk.source
                    for result in rag_answer.sources
                })

                answer = OrchestratorAnswer(
                    text=rag_answer.text,
                    mode=mode,
                    sources=sources,
                    responses=[rag_answer.response],
                )

            # Ruta 3: ejecución de herramientas y servicios MCP.
            elif ruta == "acciones":
                result = await self.actions_agent.run(
                    question,
                    history,
                )

                answer = self._from_agent(result, mode)

            else:
                raise ValueError(
                    f"Ruta no reconocida: {ruta}"
                )

            answer.routing = routing
            answer.responses.insert(0, routing.response)

            return answer

        raise ValueError(f"Modo no reconocido: {mode}")

    @staticmethod
    def _from_agent(
        result: AgentAnswer,
        mode: Mode,
    ) -> OrchestratorAnswer:

        sources = sorted({
            run.result
            for step in result.steps
            for run in step.tool_runs
            if run.call.name == "buscar_documentos"
        })

        return OrchestratorAnswer(
            text=result.text,
            mode=mode,
            steps=result.steps,
            sources=sources,
            responses=[
                step.response
                for step in result.steps
            ],
            stopped_by_limit=result.stopped_by_limit,
        )


async def create_orchestrator(
    stack: AsyncExitStack,
    confirm: ConfirmFn,
) -> Orchestrator:
    """Construye el sistema completo: configuración, LLM, índice,
    RAG, herramientas locales y servidor MCP.
    """

    settings = load_settings()
    rag_settings = load_rag_settings()

    store = VectorStore.load(rag_settings.index_dir)

    llm = LLMClient(settings)

    rag = CourseRAG(
        llm=llm,
        embedder=Embedder(store.embedding_model),
        store=store,
        top_k=rag_settings.top_k,
        min_score=rag_settings.min_score,
    )

    mcp_client = await open_client(stack)

    action_tools = [
        *LOCAL_TOOLS,
        *await load_mcp_tools(mcp_client),
    ]

    return Orchestrator(
        llm=llm,
        rag=rag,
        action_tools=action_tools,
        confirm=confirm,
    )
