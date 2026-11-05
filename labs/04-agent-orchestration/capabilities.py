
"""Capacidades del asistente expresadas como tools.

El RAG se convierte en una herramienta del agente (buscar_documentos).
Realiza la recuperación de información y devuelve fragmentos numerados
con su fuente, respetando los permisos del rol autenticado.

Uso:
    uv run python labs/04-agent-orchestration/capabilities.py
"""

import asyncio
import sys
from typing import Any

from rag import CourseRAG, format_context
from tools import Tool


# Roles reconocidos por el sistema.
VALID_ROLES = {"publico", "estudiante", "docente"}


def rag_tool(
    rag: CourseRAG,
    authenticated_role: str = "publico",
) -> Tool:
    """Convierte la recuperación documental en una herramienta con permisos."""

    # Validar el rol antes de crear la herramienta.
    if authenticated_role not in VALID_ROLES:
        raise PermissionError(
            f"El rol '{authenticated_role}' no está autorizado."
        )

    description = (
        "Busca información en los documentos del curso, incluyendo programa, "
        "horarios, evaluación, fechas de parciales, políticas, anuncios y "
        "preguntas frecuentes. Devuelve fragmentos numerados con sus fuentes."
    )

    # El modelo únicamente puede proporcionar la consulta.
    # No puede elegir ni modificar el rol de acceso.
    parameters = {
        "type": "object",
        "properties": {
            "consulta": {
                "type": "string",
                "description": (
                    "Pregunta autocontenida sobre el curso. "
                    "Por ejemplo: fecha del primer parcial."
                ),
            }
        },
        "required": ["consulta"],
    }

    async def run(arguments: dict[str, Any]) -> str:
        consulta = arguments.get("consulta")

        if not isinstance(consulta, str) or not consulta.strip():
            return "Error: debes proporcionar una consulta válida."

        # El rol procede del contexto confiable de la aplicación,
        # no de los argumentos enviados por el LLM.
        resultados = rag.retrieve(
            consulta,
            role=authenticated_role,
        )

        return format_context(resultados)

    return Tool(
        name="buscar_documentos",
        description=description,
        parameters=parameters,
        run=run,
        read_only=True,
        origin="rag",
    )


async def _demo(question: str) -> None:
    """Prueba la recuperación documental sin utilizar un LLM."""

    from config import load_rag_settings
    from embeddings import Embedder
    from vector_store import VectorStore

    settings = load_rag_settings()
    store = VectorStore.load(settings.index_dir)

    # La demostración funciona como usuario público.
    # La aplicación principal deberá proporcionar el rol autenticado.
    authenticated_role = "publico"

    rag = CourseRAG(
        None,
        Embedder(store.embedding_model),
        store,
        settings.top_k,
        settings.min_score,
    )

    tool = rag_tool(
        rag,
        authenticated_role=authenticated_role,
    )

    print(f"Rol de demostración: {authenticated_role}")
    print(f"{tool.name}({{'consulta': {question!r}}}) →\n")

    resultado = await tool.run({"consulta": question})
    print(resultado)


if __name__ == "__main__":
    asyncio.run(
        _demo(
            " ".join(sys.argv[1:])
            or "¿Cuándo es el primer parcial?"
        )
    )
