"""RAG: recuperar fragmentos relevantes respetando los permisos del usuario."""

from dataclasses import dataclass

from embeddings import Embedder
from llm_client import LLMClient, LLMResponse, Message
from prompts import build_rag_messages
from vector_store import SearchResult, VectorStore

NO_CONTEXT = "(No se encontraron fragmentos relevantes en los documentos del curso.)"

# Política determinista de acceso.
# El rol debe proceder de una sesión autenticada, nunca del LLM.
ROLE_ACCESS = {
    "publico": {"publico"},
    "estudiante": {"publico", "estudiante"},
    "docente": {"publico", "estudiante", "docente"},
}


@dataclass
class RAGAnswer:
    text: str
    sources: list[SearchResult]
    messages: list[Message]
    response: LLMResponse


def format_context(results: list[SearchResult]) -> str:
    """Prepara los fragmentos recuperados para el contexto del LLM."""
    if not results:
        return NO_CONTEXT

    return "\n\n".join(
        f"[{i}] ({result.chunk.source}) {result.chunk.text}"
        for i, result in enumerate(results, 1)
    )


class CourseRAG:
    def __init__(
        self,
        llm: LLMClient,
        embedder: Embedder,
        store: VectorStore,
        top_k: int,
        min_score: float,
    ):
        self.llm = llm
        self.embedder = embedder
        self.store = store
        self.top_k = top_k
        self.min_score = min_score

    def retrieve(
        self,
        question: str,
        role: str = "publico",
    ) -> list[SearchResult]:
        """Recupera únicamente documentos permitidos para el rol."""

        if role not in ROLE_ACCESS:
            raise PermissionError("Rol no autorizado para consultar el RAG.")

        query_vector = self.embedder.embed_query(question)

        # El filtro se aplica antes de seleccionar los fragmentos más similares.
        results = self.store.search(
            query_vector,
            self.top_k,
            allowed_access_levels=ROLE_ACCESS[role],
        )

        return [
            result
            for result in results
            if result.score >= self.min_score
        ]

    def answer(
        self,
        question: str,
        history: list[Message] | None = None,
        role: str = "publico",
    ) -> RAGAnswer:
        """Genera una respuesta usando solo fuentes permitidas para el rol."""

        sources = self.retrieve(question, role=role)

        messages = build_rag_messages(
            history or [],
            question,
            format_context(sources),
        )

        response = self.llm.chat(messages)

        return RAGAnswer(
            text=response.text,
            sources=sources,
            messages=messages,
            response=response,
        )
