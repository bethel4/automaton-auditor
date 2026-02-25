# src/tools/doc_tools.py

from typing import List
from pypdf import PdfReader


def ingest_pdf(path: str) -> List[str]:
    """Chunk PDF into small text segments."""
    reader = PdfReader(path)

    chunks = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            # naive chunking
            chunks.extend(
                [text[i:i+1000] for i in range(0, len(text), 1000)]
            )

    return chunks


def query_pdf(chunks: List[str], keyword: str) -> List[str]:
    """Simple keyword search."""
    return [chunk for chunk in chunks if keyword.lower() in chunk.lower()]