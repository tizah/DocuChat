import logging
from dataclasses import dataclass

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

# Using a single collection with document_id filtering rather than one collection per document.
# Reasons:
# 1. Cross-document search is simpler — a single query can span multiple documents.
# 2. Avoids collection proliferation and management overhead.
# 3. ChromaDB where-filtering on metadata is efficient for this use case.

COLLECTION_NAME = "docuchat_chunks"


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    chunk_index: int
    page_number: int
    content: str
    score: float


class VectorStore:
    def __init__(self, persist_dir: str | None = None) -> None:
        path = persist_dir or settings.chroma_persist_dir
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Added %d chunks to vector store", len(ids))

    def search(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int = 5,
    ) -> list[SearchResult]:
        where_filter: dict | None = None
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity score: 1 - (distance / 2)
                similarity = 1 - (distance / 2)
                search_results.append(SearchResult(
                    chunk_id=chunk_id,
                    document_id=metadata.get("document_id", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    page_number=metadata.get("page_number", 0),
                    content=results["documents"][0][i] if results["documents"] else "",
                    score=similarity,
                ))

        return search_results

    def delete_by_document(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info("Deleted chunks for document %s from vector store", document_id)
        except Exception:
            logger.warning(
                "No chunks found for document %s in vector store", document_id
            )
