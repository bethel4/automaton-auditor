# src/tools/doc_tools.py

from typing import List

from docling.document_converter import DocumentConverter
from pypdf import PdfReader


def extract_images_from_pdf(path: str) -> List[bytes]:
    """
    Extract raw image bytes from a PDF.

    Returns a list of image byte blobs. This keeps the
    function focused on extraction; higher-level callers
    can decide how to pass these bytes to a multimodal LLM.
    """
    reader = PdfReader(path)
    images: List[bytes] = []

    for page in reader.pages:
        # `page.images` is provided by pypdf and may be empty
        page_images = getattr(page, "images", [])
        for image in page_images:
            try:
                images.append(image.data)
            except Exception:
                # Skip any images we fail to read
                continue

    return images


def ingest_pdf(path: str, max_chars: int = 20_000, chunk_size: int = 1000) -> List[str]:
    """
    Chunk a PDF into small text segments using Docling.

    - Uses Docling's `DocumentConverter` to extract structured text.
    - Truncates the total extracted text to `max_chars` to keep context small.
    - Returns fixed-size chunks (RAG-lite).
    """
    converter = DocumentConverter()
    doc = converter.convert(path).document
    full_text = doc.export_to_markdown()

    if max_chars is not None:
        full_text = full_text[:max_chars]

    return [full_text[i : i + chunk_size] for i in range(0, len(full_text), chunk_size)]


def query_pdf(chunks: List[str], keyword: str) -> List[str]:
    """Simple keyword search."""
    return [chunk for chunk in chunks if keyword.lower() in chunk.lower()]