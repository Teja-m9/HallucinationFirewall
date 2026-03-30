"""
Embedding and Vector Store Module for VDHF

Handles embedding generation and vector database operations using ChromaDB.
"""

import os
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import chromadb
except ImportError:
    chromadb = None

from config.settings import (
    EMBEDDING_MODEL,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR
)
from ingestion.loader import DocumentChunk


class EmbeddingModel:
    """
    Embedding Model Wrapper

    Uses Sentence-BERT for generating embeddings.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is required. Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            NumPy array of embeddings (shape: [n_texts, embedding_dim])
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings

    def embed_single(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            NumPy array of embedding (shape: [embedding_dim])
        """
        return self.embed([text])[0]


class VectorStore:
    """
    Vector Store using ChromaDB

    Responsibilities:
    - Store embeddings in ChromaDB
    - Perform similarity-based retrieval
    - Manage document collections
    """

    def __init__(
        self,
        collection_name: str = CHROMA_COLLECTION_NAME,
        persist_directory: str = CHROMA_PERSIST_DIR,
        embedding_model: Optional[EmbeddingModel] = None
    ):
        if chromadb is None:
            raise ImportError(
                "chromadb is required. Install with: pip install chromadb"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize embedding model
        self.embedding_model = embedding_model or EmbeddingModel()

        # Initialize ChromaDB client (in-memory for simplicity)
        self.client = chromadb.Client()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects
        """
        if not chunks:
            return

        # Extract texts and generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents.

        Args:
            query: Query text
            top_k: Number of results to return

        Returns:
            List of tuples (document_text, similarity_score, metadata)
        """
        # Generate query embedding
        query_embedding = self.embedding_model.embed_single(query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        # Format results
        formatted_results = []

        if results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            distances = results["distances"][0] if results["distances"] else [0] * len(documents)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)

            for doc, dist, meta in zip(documents, distances, metadatas):
                # Convert distance to similarity (ChromaDB uses distance, lower is better)
                similarity = 1 - dist
                formatted_results.append((doc, similarity, meta))

        return formatted_results

    def search_with_embeddings(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search using a pre-computed embedding.

        Args:
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return

        Returns:
            List of tuples (document_text, similarity_score, metadata)
        """
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        formatted_results = []

        if results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            distances = results["distances"][0] if results["distances"] else [0] * len(documents)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)

            for doc, dist, meta in zip(documents, distances, metadatas):
                similarity = 1 - dist
                formatted_results.append((doc, similarity, meta))

        return formatted_results

    def get_all_documents(self) -> List[str]:
        """Get all documents in the collection."""
        results = self.collection.get(include=["documents"])
        return results["documents"] if results["documents"] else []

    def clear(self) -> None:
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()


def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))
