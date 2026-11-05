
"""Vector store en memoria: guarda fragmentos con sus vectores y busca los más parecidos."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from documents import Chunk

VECTORS_FILE = "vectors.npy"
CHUNKS_FILE = "chunks.json"


@dataclass
class SearchResult:
    chunk: Chunk
    score: float


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Divide cada vector por su norma para calcular similitud coseno."""
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.maximum(norms, 1e-12)


class VectorStore:
    def __init__(self, embedding_model: str):
        self.embedding_model = embedding_model
        self.chunks: list[Chunk] = []
        self._vectors: np.ndarray | None = None

    def __len__(self) -> int:
        return len(self.chunks)

    def add(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Debe haber exactamente un vector por fragmento.")

        vectors = normalize(np.asarray(vectors, dtype=np.float32))
        self._vectors = (
            vectors
            if self._vectors is None
            else np.vstack([self._vectors, vectors])
        )
        self.chunks.extend(chunks)

    def search(
        self,
        query_vector: np.ndarray,
        k: int,
        allowed_access_levels: set[str] | None = None,
    ) -> list[SearchResult]:
        """Busca los fragmentos más similares entre los niveles permitidos."""

        if self._vectors is None:
            return []

        if allowed_access_levels is None:
            candidate_indices = list(range(len(self.chunks)))
        else:
            candidate_indices = [
                i
                for i, chunk in enumerate(self.chunks)
                if chunk.access_level in allowed_access_levels
            ]

        if not candidate_indices:
            return []

        candidate_vectors = self._vectors[candidate_indices]
        scores = candidate_vectors @ normalize(
            np.asarray(query_vector, dtype=np.float32)
        )

        top_positions = np.argsort(scores)[::-1][:k]

        return [
            SearchResult(
                chunk=self.chunks[candidate_indices[position]],
                score=float(scores[position]),
            )
            for position in top_positions
        ]

    def save(self, index_dir: Path) -> None:
        """Guarda los vectores y los fragmentos en disco."""

        index_dir.mkdir(parents=True, exist_ok=True)

        if self._vectors is None:
            raise ValueError("No hay vectores para guardar.")

        np.save(index_dir / VECTORS_FILE, self._vectors)

        data = {
            "embedding_model": self.embedding_model,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }

        (index_dir / CHUNKS_FILE).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, index_dir: Path) -> "VectorStore":
        """Carga desde disco los fragmentos y sus vectores."""

        chunks_path = index_dir / CHUNKS_FILE
        vectors_path = index_dir / VECTORS_FILE

        if not chunks_path.exists() or not vectors_path.exists():
            raise FileNotFoundError(
                f"No existe el índice completo en {index_dir}. "
                "Ejecuta primero ingest.py."
            )

        data = json.loads(chunks_path.read_text(encoding="utf-8"))

        store = cls(data["embedding_model"])

        store.chunks = [
            Chunk(
                id=chunk["id"],
                source=chunk["source"],
                text=chunk["text"],
                access_level=chunk.get("access_level", "publico"),
            )
            for chunk in data["chunks"]
        ]

        store._vectors = np.load(vectors_path)

        if len(store.chunks) != len(store._vectors):
            raise ValueError(
                "El número de fragmentos no coincide con los vectores."
            )

        return store
