# src/tools/doc_tools.py (Docling version)

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import Docling
# Import Docling
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

def ingest_pdf(pdf_path: str) -> List[str]:
    """
    Ingest PDF and return chunks of text.
    This is the function detectives.py is trying to import!
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of text chunks
    """
    if not os.path.exists(pdf_path):
        return []
    
    # Extract text first
    text = extract_text_from_pdf(pdf_path)
    
    # If docling is available, use it for better chunking
    if DOCLING_AVAILABLE:
        try:
            doc = DoclingDocument.from_pdf(pdf_path)
            # Get structured chunks with better boundaries
            chunks = []
            for element in doc.elements:
                if hasattr(element, 'text') and element.text:
                    chunks.append(element.text)
            if chunks:
                return chunks
        except:
            pass  # Fall back to basic chunking
    
    # Fallback: basic chunking
    return chunk_text(text, chunk_size=2000, overlap=200)


def query_pdf(chunks: List[str], question: str) -> List[str]:
    """
    Find relevant chunks for a question.
    This is the other function detectives.py is trying to import!
    
    Args:
        chunks: List of text chunks from ingest_pdf
        question: Question to find relevant chunks for
        
    Returns:
        List of relevant chunks
    """
    if not chunks:
        return []
    
    # Simple keyword matching (you could enhance this with embeddings later)
    question_words = set(question.lower().split())
    relevant_chunks = []
    
    for chunk in chunks:
        chunk_lower = chunk.lower()
        # Count how many question words appear in chunk
        matches = sum(1 for word in question_words if word in chunk_lower)
        if matches > 0:
            relevant_chunks.append(chunk)
    
    # Return top 5 most relevant (or all if less)
    return relevant_chunks[:5]


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from PDF using Docling
    
    Returns:
        Extracted text as string
    """
    if not os.path.exists(pdf_path):
        return ""
    
    try:
        # Use Docling DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        # Extract text from the document
        text_content = result.document.export_to_markdown()
        
        return text_content if text_content else ""
        
    except Exception as e:
        return f"Error extracting text with Docling: {str(e)}"


def extract_images_from_pdf(pdf_path: str) -> List[bytes]:
    """
    Extract images from PDF using Docling
    
    Returns:
        List of image bytes
    """
    if not os.path.exists(pdf_path):
        return []
    
    try:
        # Use Docling DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        # Extract images from the document
        image_bytes = []
        for element in result.document.pages[0].elements:
            if hasattr(element, 'image'):
                # Convert image to bytes if available
                try:
                    import io
                    from PIL import Image
                    
                    if hasattr(element, 'image') and element.image:
                        img_bytes = io.BytesIO()
                        element.image.save(img_bytes, format='PNG')
                        image_bytes.append(img_bytes.getvalue())
                except:
                    continue
        
        return image_bytes
        
    except Exception as e:
        print(f"Error extracting images with Docling: {e}")
        return []


# Keep all your other functions the same
def extract_file_paths_from_text(text: str) -> List[str]:
    """Extract file paths mentioned in text using regex"""
    python_pattern = r'src/[a-zA-Z0-9_/]+\.py'
    matches = re.findall(python_pattern, text)
    
    code_block_pattern = r'```[a-zA-Z]*\n(.*?)```'
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
    
    for block in code_blocks:
        code_matches = re.findall(python_pattern, block)
        matches.extend(code_matches)
    
    return list(set(matches))


def extract_concepts(text: str) -> Dict[str, bool]:
    """Check for key concepts in text"""
    concepts = [
        "Dialectical Synthesis", "Fan-In", "Fan-Out", 
        "Metacognition", "State Synchronization", "Parallel Execution",
        "Evidence Aggregator", "Chief Justice", "LangGraph", "StateGraph"
    ]
    
    result = {}
    text_lower = text.lower()
    
    for concept in concepts:
        concept_lower = concept.lower()
        result[concept] = concept_lower in text_lower
    
    return result


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """Split text into chunks for LLM processing"""
    if not text:
        return []
    
    words = text.split()
    chunks = []
    
    if len(words) * 5 < chunk_size:
        return [text]
    
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size//5]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        i += (chunk_size//5) - (overlap//5)
    
    return chunks


def cross_reference_paths(claimed_paths: List[str], actual_files: List[str]) -> Dict[str, List[str]]:
    """Cross-reference claimed file paths with actual files"""
    verified = []
    hallucinated = []
    
    actual_files_normalized = [f.replace('\\', '/') for f in actual_files]
    
    for path in claimed_paths:
        normalized_path = path.replace('\\', '/')
        if normalized_path in actual_files_normalized:
            verified.append(path)
        else:
            hallucinated.append(path)
    
    return {
        "verified": verified,
        "hallucinated": hallucinated
    }


def extract_metadata(text: str) -> Dict[str, Any]:
    """Extract basic metadata from PDF text"""
    if not text:
        return {
            "word_count": 0,
            "estimated_pages": 0,
            "has_code_blocks": False,
            "has_diagrams": False
        }
    
    words = text.split()
    word_count = len(words)
    estimated_pages = max(1, word_count // 250)
    
    return {
        "word_count": word_count,
        "estimated_pages": estimated_pages,
        "has_code_blocks": "```" in text,
        "has_diagrams": any(kw in text.lower() for kw in ["figure", "diagram", "image"]),
        "has_tables": "|" in text and "-" in text
    }


def get_pdf_hash(pdf_path: str) -> str:
    """Get hash of PDF file for caching"""
    if not os.path.exists(pdf_path):
        return ""
    
    with open(pdf_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()