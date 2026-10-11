"""
chunking.py — Document & Text Chunking Service (Phase 3)
─────────────────────────────────────────────────────────
Chunks confirmed text by page and heading/paragraph boundaries.
Preserves page numbers, source metadata, and chunk IDs for precise citations.
"""
import re
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DocumentChunk(BaseModel):
    chunk_id: str
    input_id: str
    page: int
    chunk_index: int
    heading: str
    content: str
    snippet: str


def chunk_pages(
    input_id: str,
    pages: List[Dict[str, Any]],
    target_chunk_size: int = 500,
    overlap: int = 60,
) -> List[DocumentChunk]:
    """
    Chunk page-structured text (e.g. from PDF, Multi-page notes).
    Splits along headings and double-newlines while respecting page boundaries.
    """
    chunks: List[DocumentChunk] = []
    global_index = 0

    for page_dict in pages:
        page_num = int(page_dict.get("page", 1))
        page_text = (page_dict.get("text") or "").strip()
        if not page_text:
            continue

        page_chunks = _split_text_by_headings_and_size(
            input_id=input_id,
            text=page_text,
            page_num=page_num,
            start_index=global_index,
            target_chunk_size=target_chunk_size,
            overlap=overlap,
        )
        for c in page_chunks:
            chunks.append(c)
            global_index += 1

    return chunks


def chunk_plain_text(
    input_id: str,
    text: str,
    target_chunk_size: int = 500,
    overlap: int = 60,
) -> List[DocumentChunk]:
    """
    Chunk plain text notes. Looks for '[Page X]' tags if present,
    otherwise treats as Page 1.
    """
    # Check if text has [Page X] tags
    page_splits = re.split(r"\[Page\s+(\d+)\]", text)
    if len(page_splits) > 1:
        pages = []
        # page_splits: ["preamble", "1", "page 1 text", "2", "page 2 text", ...]
        i = 1
        while i < len(page_splits):
            p_num = int(page_splits[i])
            p_text = page_splits[i + 1] if i + 1 < len(page_splits) else ""
            pages.append({"page": p_num, "text": p_text})
            i += 2
        return chunk_pages(input_id, pages, target_chunk_size, overlap)

    return _split_text_by_headings_and_size(
        input_id=input_id,
        text=text,
        page_num=1,
        start_index=0,
        target_chunk_size=target_chunk_size,
        overlap=overlap,
    )


def _split_text_by_headings_and_size(
    input_id: str,
    text: str,
    page_num: int,
    start_index: int,
    target_chunk_size: int = 500,
    overlap: int = 60,
) -> List[DocumentChunk]:
    """
    Splits text along markdown headings (##, ###) and paragraph breaks.
    """
    chunks: List[DocumentChunk] = []
    # Identify heading sections or paragraphs
    paragraphs = re.split(r"\n\s*\n", text)
    current_heading = "General"
    buffer = ""
    chunk_idx = start_index

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        # Check if paragraph begins with a heading
        heading_match = re.match(r"^(#{1,4}\s+[^\n]+)", para_clean)
        if heading_match:
            current_heading = heading_match.group(1).lstrip("#").strip()

        if len(buffer) + len(para_clean) <= target_chunk_size:
            buffer = f"{buffer}\n\n{para_clean}".strip() if buffer else para_clean
        else:
            if buffer:
                c_id = str(uuid.uuid4())
                snippet = buffer[:160].replace("\n", " ").strip() + ("..." if len(buffer) > 160 else "")
                chunks.append(DocumentChunk(
                    chunk_id=c_id,
                    input_id=input_id,
                    page=page_num,
                    chunk_index=chunk_idx,
                    heading=current_heading,
                    content=buffer,
                    snippet=snippet,
                ))
                chunk_idx += 1
                # Keep tail for overlap if meaningful
                tail = buffer[-overlap:] if len(buffer) > overlap else ""
                buffer = f"{tail}\n\n{para_clean}".strip() if tail else para_clean
            else:
                # Very long single paragraph, slice it
                while len(para_clean) > target_chunk_size:
                    slice_content = para_clean[:target_chunk_size]
                    c_id = str(uuid.uuid4())
                    snippet = slice_content[:160].replace("\n", " ").strip() + "..."
                    chunks.append(DocumentChunk(
                        chunk_id=c_id,
                        input_id=input_id,
                        page=page_num,
                        chunk_index=chunk_idx,
                        heading=current_heading,
                        content=slice_content,
                        snippet=snippet,
                    ))
                    chunk_idx += 1
                    para_clean = para_clean[target_chunk_size - overlap:]
                buffer = para_clean

    if buffer:
        c_id = str(uuid.uuid4())
        snippet = buffer[:160].replace("\n", " ").strip() + ("..." if len(buffer) > 160 else "")
        chunks.append(DocumentChunk(
            chunk_id=c_id,
            input_id=input_id,
            page=page_num,
            chunk_index=chunk_idx,
            heading=current_heading,
            content=buffer,
            snippet=snippet,
        ))

    return chunks
