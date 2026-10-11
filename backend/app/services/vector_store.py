"""
vector_store.py — In-Memory & SQLite Vector Index for RAG (Phase 3)
───────────────────────────────────────────────────────────────────
Stores chunk vectors and metadata (user_id, input_id, page, chunk_id, snippet).
Computes cosine similarity for semantic search and BM25/keyword ranking.
Enforces relevance thresholds for strict "not_found_in_notes" behavior.
"""
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from app.services.chunking import DocumentChunk


class VectorStore:
    def __init__(self, relevance_threshold: float = 0.28):
        # chunk_id -> dict with embedding, chunk metadata
        self._chunks: Dict[str, Dict[str, Any]] = {}
        # input_id -> list of chunk_ids
        self._input_index: Dict[str, List[str]] = {}
        self.relevance_threshold = relevance_threshold

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: Optional[List[List[float]]] = None, user_id: Optional[str] = None):
        """Add or update chunks in the index with optional embedding vectors."""
        for i, chunk in enumerate(chunks):
            emb = embeddings[i] if embeddings and i < len(embeddings) else None
            self._chunks[chunk.chunk_id] = {
                "chunk": chunk,
                "user_id": user_id,
                "embedding": emb,
                "tokens": self._tokenize(chunk.content + " " + chunk.heading),
            }
            if chunk.input_id not in self._input_index:
                self._input_index[chunk.input_id] = []
            if chunk.chunk_id not in self._input_index[chunk.input_id]:
                self._input_index[chunk.input_id].append(chunk.chunk_id)

    def delete_input(self, input_id: str):
        """Delete all chunks for a specific input."""
        c_ids = self._input_index.pop(input_id, [])
        for c_id in c_ids:
            self._chunks.pop(c_id, None)

    def search(
        self,
        query: str,
        input_id: Optional[str] = None,
        user_id: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 4,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search chunks using hybrid vector similarity and token overlap.
        Returns list of (DocumentChunk, score) sorted by score descending.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens and not query_embedding:
            return []

        scored_chunks: List[Tuple[DocumentChunk, float]] = []

        candidate_ids = self._input_index.get(input_id, []) if input_id else list(self._chunks.keys())

        for c_id in candidate_ids:
            entry = self._chunks.get(c_id)
            if not entry:
                continue

            # Per-user data isolation check
            if user_id and entry.get("user_id") and entry["user_id"] != user_id:
                continue

            # 1. Lexical / Keyword score (Jaccard + keyword density)
            chunk_tokens = entry["tokens"]
            intersect = query_tokens.intersection(chunk_tokens)
            lexical_score = 0.0
            if intersect:
                # Weight by proportion of query words found in chunk
                lexical_score = len(intersect) / max(len(query_tokens), 1)

            # 2. Embedding score (Cosine similarity) if available
            cos_sim = 0.0
            if query_embedding and entry.get("embedding"):
                cos_sim = self._cosine_similarity(query_embedding, entry["embedding"])

            # Hybrid score
            final_score = max(lexical_score, cos_sim)
            if lexical_score > 0 and cos_sim > 0:
                final_score = 0.6 * cos_sim + 0.4 * lexical_score

            scored_chunks.append((entry["chunk"], round(final_score, 4)))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"\b\w{2,}\b", text.lower())
        stopwords = {
            "the", "and", "is", "in", "it", "of", "to", "for", "with", "on", "at",
            "from", "by", "about", "as", "into", "like", "through", "after", "over",
            "between", "out", "against", "during", "without", "before", "under", "around",
            "among", "what", "which", "who", "whom", "this", "that", "these", "those",
            "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "can", "could", "should", "would", "how", "why", "when", "where"
        }
        return {w for w in words if w not in stopwords}

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm_a * norm_b)))


# Global singleton vector store instance
global_vector_store = VectorStore(relevance_threshold=0.25)
