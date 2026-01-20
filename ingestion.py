"""
Document Ingestion Module for VDHF

Handles loading and preprocessing of documents for retrieval.
Supports PDF, TXT, and DOCX files.
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    
    def __str__(self) -> str:
        return f"Chunk[{self.chunk_id}]: {self.content[:100]}..."


class DocumentIngestion:
    """
    Document Ingestion Module
    
    Responsibilities:
    - Load PDFs, text files, or DOCX content
    - Clean text (remove noise, headers, footers)
    - Split text into chunks
    - Attach metadata such as source and position
    """
    
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_document(self, file_path: str) -> str:
        """
        Load a document from file path.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Raw text content of the document
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".txt":
            return self._load_txt(file_path)
        elif ext == ".pdf":
            return self._load_pdf(file_path)
        elif ext == ".docx":
            return self._load_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _load_txt(self, file_path: str) -> str:
        """Load a text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    
    def _load_pdf(self, file_path: str) -> str:
        """Load a PDF file."""
        if PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")
        
        reader = PdfReader(file_path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n\n".join(text_parts)
    
    def _load_docx(self, file_path: str) -> str:
        """Load a DOCX file."""
        if DocxDocument is None:
            raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")
        
        doc = DocxDocument(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing noise.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'Page \d+ of \d+', '', text)
        
        # Remove headers/footers markers
        text = re.sub(r'^\s*[-_=]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def split_into_chunks(
        self,
        text: str,
        source: str = "unknown"
    ) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Cleaned text content
            source: Source identifier for metadata
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending within last 100 chars
                search_start = max(end - 100, start)
                last_period = text.rfind('. ', search_start, end)
                if last_period > start:
                    end = last_period + 1
            
            # Extract chunk content
            content = text[start:end].strip()
            
            if content:
                chunk = DocumentChunk(
                    content=content,
                    metadata={
                        "source": source,
                        "chunk_index": chunk_index,
                        "start_char": start,
                        "end_char": end
                    },
                    chunk_id=f"{os.path.basename(source)}_{chunk_index}"
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start <= chunks[-1].metadata["start_char"] if chunks else 0:
                start = end  # Prevent infinite loop
        
        return chunks
    
    def ingest_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Full ingestion pipeline for a single file.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of processed DocumentChunk objects
        """
        # Load document
        raw_text = self.load_document(file_path)
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Split into chunks
        chunks = self.split_into_chunks(cleaned_text, source=file_path)
        
        return chunks
    
    def ingest_directory(
        self,
        directory_path: str,
        extensions: Optional[List[str]] = None
    ) -> List[DocumentChunk]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory_path: Path to the directory
            extensions: List of file extensions to process (default: ['.txt', '.pdf', '.docx'])
            
        Returns:
            List of all DocumentChunk objects from all files
        """
        if extensions is None:
            extensions = ['.txt', '.pdf', '.docx']
        
        all_chunks = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    try:
                        chunks = self.ingest_file(file_path)
                        all_chunks.extend(chunks)
                        print(f"Ingested {file}: {len(chunks)} chunks")
                    except Exception as e:
                        print(f"Error ingesting {file}: {e}")
        
        return all_chunks
    
    def ingest_text(self, text: str, source: str = "direct_input") -> List[DocumentChunk]:
        """
        Ingest raw text directly.
        
        Args:
            text: Raw text content
            source: Source identifier
            
        Returns:
            List of DocumentChunk objects
        """
        cleaned_text = self.clean_text(text)
        return self.split_into_chunks(cleaned_text, source=source)


# Convenience function
def ingest_documents(path: str) -> List[DocumentChunk]:
    """
    Convenience function to ingest documents from a file or directory.
    
    Args:
        path: Path to file or directory
        
    Returns:
        List of DocumentChunk objects
    """
    ingestion = DocumentIngestion()
    
    if os.path.isfile(path):
        return ingestion.ingest_file(path)
    elif os.path.isdir(path):
        return ingestion.ingest_directory(path)
    else:
        raise ValueError(f"Invalid path: {path}")


if __name__ == "__main__":
    # Test ingestion
    print("Document Ingestion Module - Test")
    print("-" * 40)
    
    # Create sample text
    sample_text = """
    Python is a high-level programming language created by Guido van Rossum.
    It was first released in 1991. Python emphasizes code readability and 
    supports multiple programming paradigms including procedural, object-oriented,
    and functional programming.
    
    Python's design philosophy emphasizes code readability with the use of 
    significant indentation. Its language constructs and object-oriented approach
    aim to help programmers write clear, logical code for small and large-scale projects.
    """
    
    ingestion = DocumentIngestion(chunk_size=200, chunk_overlap=50)
    chunks = ingestion.ingest_text(sample_text, source="sample")
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\n{chunk.chunk_id}:")
        print(f"  Content: {chunk.content[:80]}...")
        print(f"  Metadata: {chunk.metadata}")
