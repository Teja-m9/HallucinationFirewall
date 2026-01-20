"""
Retriever Module for VDHF

Handles RAG retrieval - finding relevant evidence for user queries.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from config import TOP_K_RETRIEVAL
from embeddings import VectorStore, EmbeddingModel
from ingestion import DocumentChunk, DocumentIngestion


@dataclass
class RetrievedEvidence:
    """Represents a piece of retrieved evidence."""
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    rank: int
    
    def __str__(self) -> str:
        return f"[{self.rank}] (score: {self.similarity_score:.3f}) {self.content[:100]}..."


class Retriever:
    """
    RAG Retriever Module
    
    Purpose:
    - Embed user query
    - Retrieve top-K relevant chunks from vector store
    - Return ranked evidence set
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        top_k: int = TOP_K_RETRIEVAL
    ):
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[RetrievedEvidence]:
        """
        Retrieve evidence relevant to a query.
        
        Args:
            query: User query
            top_k: Number of results (uses default if not specified)
            
        Returns:
            List of RetrievedEvidence objects, ranked by similarity
        """
        k = top_k or self.top_k
        
        # Search vector store
        results = self.vector_store.search(query, top_k=k)
        
        # Convert to RetrievedEvidence objects
        evidence_list = []
        for rank, (content, score, metadata) in enumerate(results, 1):
            evidence = RetrievedEvidence(
                content=content,
                similarity_score=score,
                metadata=metadata,
                rank=rank
            )
            evidence_list.append(evidence)
        
        return evidence_list
    
    def retrieve_for_claim(
        self,
        claim: str,
        top_k: int = 3
    ) -> List[RetrievedEvidence]:
        """
        Retrieve evidence specifically for claim verification.
        
        Args:
            claim: Claim to find evidence for
            top_k: Number of evidence pieces to retrieve
            
        Returns:
            List of RetrievedEvidence objects
        """
        return self.retrieve(claim, top_k=top_k)
    
    def get_context_string(
        self,
        evidence_list: List[RetrievedEvidence],
        separator: str = "\n\n---\n\n"
    ) -> str:
        """
        Convert evidence list to a context string for LLM prompts.
        
        Args:
            evidence_list: List of RetrievedEvidence
            separator: String to separate evidence pieces
            
        Returns:
            Concatenated context string
        """
        if not evidence_list:
            return ""
        
        context_parts = []
        for evidence in evidence_list:
            source = evidence.metadata.get("source", "Unknown")
            context_parts.append(f"[Source: {source}]\n{evidence.content}")
        
        return separator.join(context_parts)
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the retriever's vector store.
        
        Args:
            chunks: List of DocumentChunk objects
        """
        self.vector_store.add_chunks(chunks)
    
    def ingest_and_add(self, path: str) -> int:
        """
        Ingest documents from path and add to vector store.
        
        Args:
            path: Path to file or directory
            
        Returns:
            Number of chunks added
        """
        ingestion = DocumentIngestion()
        
        import os
        if os.path.isfile(path):
            chunks = ingestion.ingest_file(path)
        elif os.path.isdir(path):
            chunks = ingestion.ingest_directory(path)
        else:
            raise ValueError(f"Invalid path: {path}")
        
        self.add_documents(chunks)
        return len(chunks)
    
    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.vector_store.clear()
    
    @property
    def document_count(self) -> int:
        """Get number of documents in the store."""
        return self.vector_store.count()


class RAGPipeline:
    """
    Complete RAG Pipeline
    
    Combines ingestion, embedding, and retrieval.
    """
    
    def __init__(
        self,
        collection_name: str = "vdhf_pipeline",
        top_k: int = TOP_K_RETRIEVAL
    ):
        # Initialize components
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(
            collection_name=collection_name,
            embedding_model=self.embedding_model
        )
        self.retriever = Retriever(
            vector_store=self.vector_store,
            top_k=top_k
        )
        self.ingestion = DocumentIngestion()
    
    def ingest(self, path: str) -> int:
        """
        Ingest documents from a path.
        
        Args:
            path: Path to file or directory
            
        Returns:
            Number of chunks ingested
        """
        return self.retriever.ingest_and_add(path)
    
    def ingest_text(self, text: str, source: str = "direct_input") -> int:
        """
        Ingest raw text directly.
        
        Args:
            text: Text content
            source: Source identifier
            
        Returns:
            Number of chunks created
        """
        chunks = self.ingestion.ingest_text(text, source=source)
        self.retriever.add_documents(chunks)
        return len(chunks)
    
    def query(self, query: str, top_k: Optional[int] = None) -> List[RetrievedEvidence]:
        """
        Query the pipeline for relevant evidence.
        
        Args:
            query: User query
            top_k: Number of results
            
        Returns:
            List of RetrievedEvidence objects
        """
        return self.retriever.retrieve(query, top_k=top_k)
    
    def get_context(self, query: str, top_k: Optional[int] = None) -> str:
        """
        Get context string for a query.
        
        Args:
            query: User query
            top_k: Number of evidence pieces
            
        Returns:
            Context string for LLM prompt
        """
        evidence = self.query(query, top_k=top_k)
        return self.retriever.get_context_string(evidence)


if __name__ == "__main__":
    # Test retriever
    print("Retriever Module - Test")
    print("-" * 40)
    
    # Create pipeline
    pipeline = RAGPipeline(collection_name="test_retriever")
    
    # Add sample documents
    sample_docs = [
        "Python is a high-level programming language created by Guido van Rossum in 1991.",
        "Python emphasizes code readability and supports multiple programming paradigms.",
        "JavaScript is a scripting language primarily used for web development.",
        "Machine learning is a subset of artificial intelligence that enables systems to learn.",
        "The Python Package Index (PyPI) hosts thousands of third-party Python packages."
    ]
    
    for doc in sample_docs:
        pipeline.ingest_text(doc)
    
    print(f"Ingested {pipeline.retriever.document_count} chunks")
    
    # Test queries
    test_queries = [
        "Who created Python?",
        "What is machine learning?",
        "What is Python used for?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 30)
        evidence = pipeline.query(query, top_k=3)
        for ev in evidence:
            print(f"  [{ev.rank}] Score: {ev.similarity_score:.3f}")
            print(f"      {ev.content[:80]}...")
