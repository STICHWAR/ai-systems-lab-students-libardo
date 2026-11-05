"""RAG: recuperar fragmentos relevantes respetando los permisos del usuario."""

from dataclasses import dataclass
import re

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

# Un término concreto como "simulacro" diferencia una intención específica de
# otra semánticamente cercana como "segundo parcial". El boost no altera los
# permisos ni añade documentos: solo reordena candidatos ya autorizados.
SPECIFIC_TERM_BOOST = 0.15


def specific_terms(question: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\wáéíóúüñ]+", question.casefold())
        if len(token) >= 8
    }


def rerank_specific_terms(question: str, results: list[SearchResult]) -> list[SearchResult]:
    terms = specific_terms(question)
    if not terms:
        return results

    def adjusted_score(result: SearchResult) -> float:
        text = result.chunk.text.casefold()
        matches = sum(re.search(rf"\b{re.escape(term)}\b", text) is not None for term in terms)
        return result.score + SPECIFIC_TERM_BOOST * matches

    return sorted(results, key=adjusted_score, reverse=True)


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
        # Se recuperan más candidatos autorizados antes del reranking léxico.
        # El filtro de acceso sigue ocurriendo dentro de VectorStore.search.
        results = self.store.search(
            query_vector,
            max(self.top_k * 3, self.top_k),
            allowed_access_levels=ROLE_ACCESS[role],
        )

        filtered = [
            result
            for result in results
            if result.score >= self.min_score
        ]
        return rerank_specific_terms(question, filtered)[:self.top_k]

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
