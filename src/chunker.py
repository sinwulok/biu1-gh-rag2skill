"""Chunk files into smaller, meaningful pieces for embedding and retrieval.

The goal is to create chunks that:
- Preserve semantic meaning
- Include sufficient context
- Are small enough to embed efficiently
- Don't break code or markdown structure unnecessarily
"""

import re
from typing import List, Dict

from src.config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_FILE


def chunk_file(path: str, content: str) -> List[Dict[str, any]]:
    """Split a file into overlapping chunks with metadata.

    Args:
        path: Repository-relative file path.
        content: Full file content as a string.

    Returns:
        List of chunk dicts with keys: text, path, chunk_id, metadata.
    """
    if not content or not content.strip():
        return []

    # Choose chunking strategy based on file type
    if path.endswith(('.md', '.rst', '.txt')):
        chunks = _chunk_markdown(content)
    elif path.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.rb', '.cs')):
        chunks = _chunk_code(content)
    else:
        chunks = _chunk_generic(content)

    # Limit chunks per file to avoid massive files dominating
    if len(chunks) > MAX_CHUNKS_PER_FILE:
        chunks = chunks[:MAX_CHUNKS_PER_FILE]

    # Add metadata
    result = []
    for i, text in enumerate(chunks):
        result.append({
            "text": text,
            "path": path,
            "chunk_id": i,
            "metadata": {
                "total_chunks": len(chunks),
                "file_type": _get_file_type(path),
            }
        })

    return result


def _chunk_markdown(content: str) -> List[str]:
    """Chunk markdown by headers and paragraphs."""
    chunks = []

    # Split by headers first
    sections = re.split(r'\n(#{1,6}\s+.+)\n', content)

    current_header = ""
    for i, section in enumerate(sections):
        if section.startswith('#'):
            current_header = section
        elif section.strip():
            # Include header context in each chunk
            text = f"{current_header}\n{section}" if current_header else section

            # Further split long sections
            if len(text) > CHUNK_SIZE:
                subsections = _split_by_paragraphs(text)
                chunks.extend(subsections)
            else:
                chunks.append(text)

    return chunks if chunks else [content[:CHUNK_SIZE]]


def _chunk_code(content: str) -> List[str]:
    """Chunk code by functions/classes/top-level blocks."""
    chunks = []

    # Try to split by function/class definitions
    # This regex captures common patterns across languages
    patterns = [
        r'\n((?:def|class|function|func|fn|public|private|protected)\s+\w+)',  # Python, JS, Go, Rust
        r'\n((?:public|private|protected)\s+(?:static\s+)?(?:class|interface|enum))',  # Java, C#
    ]

    splits = []
    for pattern in patterns:
        matches = list(re.finditer(pattern, content))
        if matches:
            splits = matches
            break

    if splits:
        # Split at function/class boundaries
        last_pos = 0
        for match in splits:
            if match.start() > last_pos:
                chunk = content[last_pos:match.start()].strip()
                if chunk:
                    chunks.extend(_split_with_overlap(chunk, CHUNK_SIZE, CHUNK_OVERLAP))
            last_pos = match.start()

        # Add remaining content
        if last_pos < len(content):
            chunk = content[last_pos:].strip()
            if chunk:
                chunks.extend(_split_with_overlap(chunk, CHUNK_SIZE, CHUNK_OVERLAP))
    else:
        # Fall back to generic chunking
        chunks = _chunk_generic(content)

    return chunks


def _chunk_generic(content: str) -> List[str]:
    """Generic chunking with overlap for any text."""
    return _split_with_overlap(content, CHUNK_SIZE, CHUNK_OVERLAP)


def _split_by_paragraphs(text: str) -> List[str]:
    """Split text by paragraphs, then by size if needed."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []

    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < CHUNK_SIZE:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(para) > CHUNK_SIZE:
                chunks.extend(_split_with_overlap(para, CHUNK_SIZE, CHUNK_OVERLAP))
                current_chunk = ""
            else:
                current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _split_with_overlap(text: str, size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks of specified size."""
    if len(text) <= size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunk = text[start:end]

        # Try to break at sentence/line boundary if possible
        if end < len(text):
            # Look for last sentence end in chunk
            for delim in ['. ', '.\n', '\n\n', '\n']:
                last_delim = chunk.rfind(delim)
                if last_delim > size // 2:  # Only break if we're past halfway
                    chunk = chunk[:last_delim + len(delim)]
                    break

        chunks.append(chunk.strip())
        start += size - overlap

        # Avoid tiny last chunks
        if len(text) - start < overlap:
            break

    return chunks


def _get_file_type(path: str) -> str:
    """Get simple file type category."""
    if path.endswith(('.md', '.rst', '.txt')):
        return 'documentation'
    elif path.endswith(('.py', '.js', '.ts', '.go', '.rs', '.java', '.rb', '.cs')):
        return 'code'
    elif path.endswith(('.json', '.yaml', '.yml', '.toml', '.xml')):
        return 'config'
    else:
        return 'other'
