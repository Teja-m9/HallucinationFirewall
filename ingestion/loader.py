"""
Document Ingestion Module for VDHF

Handles loading and preprocessing of documents for retrieval.
Supports PDF, TXT, DOCX, and Excel (XLSX/XLS/CSV) files.
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

try:
    import openpyxl
except ImportError:
    openpyxl = None

import csv
import io

from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


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
        elif ext in (".xlsx", ".xls"):
            return self._load_excel(file_path)
        elif ext == ".csv":
            return self._load_csv(file_path)
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

    def _load_excel(self, file_path: str) -> str:
        """Load an Excel file (.xlsx/.xls) — converts every sheet into readable text.

        Auto-detects the real header row (skips merged title rows) by looking
        for the first row where 3+ cells are filled with short text values.
        Also skips non-student rows like totals or max-marks rows.
        """
        if openpyxl is None:
            raise ImportError("openpyxl is required for Excel support. Install with: pip install openpyxl")

        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        text_parts = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 2:
                continue

            # --- Auto-detect header row ---
            header_idx = self._find_header_row(rows)
            headers = [str(h).strip() if h is not None else f"Col{i}"
                       for i, h in enumerate(rows[header_idx])]

            # Collect any title lines above the header (college name, dept, etc.)
            preamble_lines = []
            for r in rows[:header_idx]:
                vals = [str(v).strip() for v in r if v is not None and str(v).strip()]
                if vals:
                    preamble_lines.append(" ".join(vals))

            sheet_lines = []
            if preamble_lines:
                sheet_lines.append(" | ".join(preamble_lines))

            # --- Process data rows (after header) ---
            for row in rows[header_idx + 1:]:
                cells = list(row)
                # Skip rows that are mostly empty
                filled = [c for c in cells if c is not None and str(c).strip()]
                if len(filled) < 2:
                    continue

                # Skip rows without a text name (likely totals / max-marks)
                has_name = any(
                    isinstance(c, str) and len(c.strip()) > 3 and not c.strip().replace('.', '').isdigit()
                    for c in cells
                )
                if not has_name:
                    continue

                parts = []
                for header, cell in zip(headers, cells):
                    if cell is not None and str(cell).strip():
                        parts.append(f"{header}: {cell}")
                if parts:
                    sheet_lines.append(". ".join(parts) + ".")

            if sheet_lines:
                text_parts.append("\n".join(sheet_lines))

        wb.close()

        if not text_parts:
            raise ValueError(f"No readable data found in {file_path}")

        return "\n\n".join(text_parts)

    @staticmethod
    def _find_header_row(rows) -> int:
        """Find the first row that looks like column headers.

        A header row has 3+ non-empty short-ish text cells and often
        contains keywords like 'name', 'no', 'roll', 'total', 'sl'.
        Falls back to row 0 if nothing better is found.
        """
        header_keywords = {'name', 'no', 'roll', 'sl', 'sno', 'total', 'id',
                           'section', 'subject', 'marks', 'grade', 'percentage',
                           'attendance', 'date', 'class', 'student'}

        best_idx = 0
        best_score = 0

        for i, row in enumerate(rows[:20]):  # only scan first 20 rows
            cells = [str(c).strip().lower() for c in row if c is not None and str(c).strip()]
            if len(cells) < 3:
                continue

            # Score: how many cells match header keywords
            keyword_hits = sum(
                1 for c in cells
                if any(kw in c for kw in header_keywords)
            )
            # Also reward rows where most cells are short text (< 30 chars)
            short_text = sum(1 for c in cells if len(c) < 30)
            score = keyword_hits * 3 + short_text

            if score > best_score:
                best_score = score
                best_idx = i

        return best_idx

    def _load_csv(self, file_path: str) -> str:
        """Load a CSV file — converts rows into readable text."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            raise ValueError(f"CSV file is empty: {file_path}")

        headers = rows[0]
        text_lines = []

        for row in rows[1:]:
            parts = []
            for header, cell in zip(headers, row):
                if cell and cell.strip():
                    parts.append(f"{header}: {cell}")
            if parts:
                text_lines.append(". ".join(parts) + ".")

        return "\n".join(text_lines)

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
        raw_text = self.load_document(file_path)
        cleaned_text = self.clean_text(raw_text)
        chunks = self.split_into_chunks(cleaned_text, source=os.path.basename(file_path))
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
            extensions = ['.txt', '.pdf', '.docx', '.xlsx', '.xls', '.csv']

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
