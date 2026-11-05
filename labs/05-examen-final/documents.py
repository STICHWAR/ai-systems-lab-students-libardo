
"""Carga de documentos, clasificación de acceso y chunking."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    source: str
    text: str
    access_level: str = "publico"


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    text: str
    access_level: str = "publico"


def load_documents(data_dir: Path) -> list[Document]:
    """Carga documentos Markdown y asigna su nivel de acceso según su carpeta."""

    paths = sorted(data_dir.rglob("*.md"))
    documents = []

    for path in paths:
        relative_path = path.relative_to(data_dir)
        parts = relative_path.parts

        if parts[0] == "publico":
            access_level = "publico"

        elif len(parts) >= 2 and parts[0] == "restringido":
            if parts[1] not in ("estudiante", "docente"):
                raise ValueError(
                    f"Nivel de acceso desconocido en: {relative_path}"
                )
            access_level = parts[1]

        else:
            raise ValueError(
                f"Documento sin clasificación de acceso: {relative_path}"
            )

        documents.append(
            Document(
                source=relative_path.as_posix(),
                text=path.read_text(encoding="utf-8"),
                access_level=access_level,
            )
        )

    return documents


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Divide el texto en fragmentos de palabras con solapamiento."""

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero.")

    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap debe ser menor que chunk_size.")

    words = text.split()
    step = chunk_size - overlap
    chunks = []

    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + chunk_size]))

        if start + chunk_size >= len(words):
            break

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int,
    overlap: int
) -> list[Chunk]:
    """Genera fragmentos conservando la clasificación de acceso."""

    return [
        Chunk(
            id=f"{doc.source}#{i}",
            source=doc.source,
            text=text,
            access_level=doc.access_level,
        )
        for doc in documents
        for i, text in enumerate(
            chunk_text(doc.text, chunk_size, overlap)
        )
    ]


if __name__ == "__main__":
    sample = "uno dos tres cuatro cinco seis siete ocho nueve diez"

    for chunk in chunk_text(sample, chunk_size=4, overlap=1):
        print(chunk)
