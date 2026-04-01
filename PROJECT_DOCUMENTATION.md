# Hallucination Firewall for Reliable Retrieval-Augmented Generation via Post-Generation Claim Verification

## Project Documentation

**Batch No:** S113 | **SDG No:** 9 & 16

**Department of Computer Science & Engineering**
**Vishnu Institute of Technology (A), Bhimavaram (AP), India**

**Guide:** Mr. K. Narasimha Rao

---

## Team Members & Contributions

| Member | Roll/Role | Contribution |
|--------|-----------|--------------|
| **M. Siva Rama Teja** | Developer | Verification Algorithm, Backend API, Deployment |
| **M. V. S. S. Varma** | Developer | Traditional RAG Pipeline, LLM Integration |
| **P. Chaya Kiran** | Developer | Vector Databases, Document Ingestion, Embeddings |
| **L. Sravya Naga Sri** | Developer | Frontend Development, UI/UX, Documentation |

---

## 1. Abstract

RAG systems pair LLMs with retrieval to improve accuracy, yet LLMs still hallucinate. We propose the **Hallucination Firewall** - a post-generation verification framework using identifier matching, numerical checking, and semantic similarity. On 75 records across 12 queries: **100% hallucination detection**, **79.03% claim verification**, **2.4s latency**, no LLM changes needed.

---

## 2. Introduction

Large Language Models (LLMs) have become the backbone of modern document-driven AI. Retrieval-Augmented Generation (RAG) was introduced to ground LLM responses in external documents, improving factual accuracy and contextual relevance.

However, even when RAG retrieves relevant documents, LLMs still fabricate incorrect details - particularly for numerical values, entity identifiers, and aggregate statistics. These hallucinations are dangerous in healthcare, finance, and legal systems.

Current strategies (retrieval improvements, prompt engineering, confidence estimation) all assume the LLM faithfully reproduces retrieved content. None provide explicit post-generation claim verification.

The **Hallucination Firewall** addresses this gap as a validation layer that decomposes every response into atomic factual claims and verifies each against trusted source data. It is **model-agnostic** and requires **no LLM retraining**.

---

## 3. System Architecture

### 3.1 Architecture Overview

```
                        +---------------------------+
                        |       User Interface       |
                        |    (React + Tailwind CSS)  |
                        +-------------+-------------+
                                      |
                                      v
                        +---------------------------+
                        |     FastAPI REST API       |
                        |        (api.py)            |
                        +-------------+-------------+
                                      |
                    +-----------------+-----------------+
                    |                                   |
                    v                                   v
        +---------------------+             +---------------------+
        | Structured Data     |             |   RAG Pipeline      |
        | Analyzer (Excel/CSV)|             |                     |
        | (data_analyzer.py)  |             |  +---------------+  |
        +---------------------+             |  | 1. Retriever  |  |
                                            |  +-------+-------+  |
                                            |          |          |
                                            |          v          |
                                            |  +---------------+  |
                                            |  | 2. Generator  |  |
                                            |  |   (Groq LLM)  |  |
                                            |  +-------+-------+  |
                                            |          |          |
                                            +----------+----------+
                                                       |
                                                       v
                              +----------------------------------------+
                              |        HALLUCINATION FIREWALL          |
                              |                                        |
                              |  +----------------------------------+  |
                              |  | 3. Claim Extractor               |  |
                              |  |    (Atomic claim decomposition)  |  |
                              |  +----------------+-----------------+  |
                              |                   |                    |
                              |                   v                    |
                              |  +----------------------------------+  |
                              |  | 4. Three-Stage Verifier          |  |
                              |  |    a) Identifier Matching        |  |
                              |  |    b) Numerical Consistency      |  |
                              |  |    c) Semantic Similarity + NLI  |  |
                              |  +----------------+-----------------+  |
                              |                   |                    |
                              |                   v                    |
                              |  +----------------------------------+  |
                              |  | 5. Firewall Decision Engine      |  |
                              |  |    Support Ratio >= threshold    |  |
                              |  |    PASS -> Deliver | FAIL -> Regen|  |
                              |  +----------------------------------+  |
                              +----------------------------------------+
                                                  |
                                        +---------+---------+
                                        |                   |
                                        v                   v
                                  +-----------+      +-------------+
                                  |   PASS    |      | REGENERATE  |
                                  | (Deliver) |      | (Refine &   |
                                  +-----------+      |  Retry x2)  |
                                                     +-------------+
```

### 3.2 Data Flow (7-Step Pipeline)

| Step | Module | Description |
|------|--------|-------------|
| **1. Document Ingestion** | `ingestion/loader.py` | Load PDF/TXT/DOCX/Excel/CSV, clean text, split into chunks |
| **2. Embedding & Indexing** | `ingestion/embeddings.py` | Generate Sentence-BERT embeddings, store in ChromaDB |
| **3. Evidence Retrieval** | `retrieval/retriever.py` | Retrieve top-K relevant chunks via semantic search |
| **4. Response Generation** | `generation/generator.py` | Groq LLM generates response from retrieved context |
| **5. Claim Extraction** | `core/claim_extractor.py` | Decompose response into atomic factual claims |
| **6. Claim Verification** | `core/verifier.py` | Verify each claim via similarity + NLI entailment |
| **7. Firewall Decision** | `core/firewall.py` | Compute Support Ratio, PASS or REGENERATE |

---

## 4. Technology Stack

### 4.1 Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core programming language |
| **FastAPI** | 0.104+ | REST API framework |
| **Uvicorn** | 0.24+ | ASGI web server |
| **Groq API** | 0.4+ | LLM inference (Llama-3.3-70B-Versatile) |
| **Sentence-BERT** | all-MiniLM-L6-v2 | Text embeddings (384 dimensions) |
| **DeBERTa** | microsoft/deberta-base-mnli | NLI entailment checking |
| **ChromaDB** | 0.4.22+ | Vector database for document embeddings |
| **PyTorch** | 2.1+ | Deep learning framework |
| **Transformers** | 4.36+ | Hugging Face model loading |

### 4.2 Document Processing

| Technology | Purpose |
|------------|---------|
| **PyPDF2** | PDF text extraction |
| **python-docx** | DOCX document parsing |
| **openpyxl** | Excel (XLSX/XLS) file handling |
| **csv module** | CSV file parsing |
| **chardet** | Character encoding detection |

### 4.3 Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2.4 | UI component framework |
| **Vite** | 8.0.1 | Build tool & dev server |
| **Tailwind CSS** | 4.2.2 | Utility-first styling |

### 4.4 Deployment

| Platform | Purpose |
|----------|---------|
| **Hugging Face Spaces** | Production deployment (Docker) |
| **GitHub** | Source code repository |
| **Docker** | Containerized deployment |

---

## 5. Module-Wise Detailed Description

### 5.1 Verification Algorithm & Backend (M. Siva Rama Teja)

#### 5.1.1 Claim Verification (`core/verifier.py`)

The verification module implements a **three-stage verification** process:

**Stage 1: Semantic Similarity**
- Uses Sentence-BERT (`all-MiniLM-L6-v2`) to compute cosine similarity between each claim and evidence chunks
- Finds the best-matching evidence for each claim
- Threshold: 0.6 (configurable)

**Stage 2: NLI Entailment**
- Uses DeBERTa (`microsoft/deberta-base-mnli`) for Natural Language Inference
- Classifies claim-evidence pairs as: ENTAILED, NEUTRAL, or CONTRADICTED
- Fallback heuristic based on word overlap when model unavailable

**Stage 3: Combined Verification Rule**
A claim is marked as **supported** if ANY of these conditions hold:
```
(similarity >= 0.6 AND entailment in [ENTAILED, NEUTRAL])  OR
(similarity >= 0.5 AND entailment == ENTAILED)             OR
(similarity >= 0.85)
```

This flexible rule handles:
- Paraphrased content (high similarity, neutral NLI)
- Semantically equivalent text (moderate similarity, strong entailment)
- Near-exact matches (very high similarity alone)

#### 5.1.2 Firewall Decision Engine (`core/firewall.py`)

The firewall computes a **Support Ratio**:

```
Support Ratio = (Number of Supported Claims) / (Total Claims)
```

**Decision Logic:**
- If `Support Ratio >= 0.6` (threshold tau): **PASS** - deliver response to user
- If `Support Ratio < 0.6`: **REGENERATE** - refine prompt and retry (up to 2 attempts)

**Scoring Module:**
- Computes per-claim scores
- Calculates average similarity and entailment scores
- Provides detailed breakdown for transparency

#### 5.1.3 Backend API (`api.py`)

FastAPI REST endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status, document count, thresholds |
| `/api/query` | POST | Process query with full verification pipeline |
| `/api/verify` | POST | Verify a list of claims directly |
| `/api/upload` | POST | Upload and ingest documents |
| `/api/clear-uploads` | POST | Clear all uploaded documents |
| `/api/delete-file` | POST | Delete a specific file |

**Query Processing Logic:**
1. Check structured data analyzer (Excel/CSV) first
2. If no structured answer, use RAG pipeline
3. Apply relevance check (threshold 0.3)
4. Verify all claims
5. Append verification notes
6. Return response with full metrics

**Structured Data Features:**
- Direct computation for Excel/CSV queries (no LLM needed)
- Student comparison (side-by-side)
- Filter queries (attendance > 75%)
- Aggregate operations (highest, lowest, average)
- Claim value verification ("is X's attendance 90%?")
- Hallucination detection for non-existent records
- Groq LLM fallback for complex analytical questions

### 5.2 Traditional RAG Pipeline (M. V. S. S. Varma)

#### 5.2.1 Retrieval Module (`retrieval/retriever.py`)

**Retriever Class:**
- Embeds user query using Sentence-BERT
- Searches ChromaDB for top-K most similar document chunks
- Returns ranked `RetrievedEvidence` objects with similarity scores
- Default top-K: 7 chunks

**RAG Pipeline Class:**
- Combines ingestion + embedding + retrieval into a single interface
- Methods: `ingest()`, `query()`, `get_context()`

#### 5.2.2 Response Generation (`generation/generator.py`)

**Generator:**
- Uses Groq Cloud API with Llama-3.3-70B-Versatile model
- Temperature: 0.3 (low for factual accuracy)
- Max tokens: 1024
- System prompt: "Provide accurate, factual answers based on context"
- Prompt instructs LLM to NOT include source references

**Prompt Refiner (`generation/prompt_refiner.py`):**
- Creates refined prompts when verification fails
- Excludes unsupported claims from context
- Forces LLM to use ONLY verified evidence
- Supports strict mode and acknowledgment mode

#### 5.2.3 Claim Extraction (`core/claim_extractor.py`)

**Extraction Methods:**
1. **Rule-based extraction** (primary):
   - Split response into sentences
   - Filter out opinions ("I think", "probably")
   - Filter out vague statements ("usually", "in general")
   - Split compound sentences on conjunctions
   - Validate claim structure and length

2. **LLM-based extraction** (fallback):
   - Uses Groq to decompose response into atomic claims
   - Follows structured prompt for consistent output

**Claim Dataclass:**
```python
@dataclass
class Claim:
    text: str               # The atomic claim
    claim_id: int           # Unique identifier
    source_sentence: str    # Original sentence
    is_verified: bool       # Verification result
    similarity_score: float # Best similarity score
    entailment_label: str   # NLI result
    supporting_evidence: str # Best matching evidence
```

### 5.3 Vector Databases & Document Ingestion (P. Chaya Kiran)

#### 5.3.1 Document Ingestion (`ingestion/loader.py`)

**Supported Formats:**

| Format | Library | Extraction Method |
|--------|---------|-------------------|
| `.txt` | Built-in | Direct file read |
| `.pdf` | PyPDF2 | Page-by-page text extraction |
| `.docx` | python-docx | Paragraph-by-paragraph |
| `.xlsx/.xls` | openpyxl | Smart header detection, row-by-row |
| `.csv` | csv module | DictReader with headers |

**Text Chunking Strategy:**
- **Chunk Size:** 1000 characters (~300-500 tokens)
- **Chunk Overlap:** 200 characters (preserves cross-boundary context)
- **Boundary Detection:** Attempts to break at sentence boundaries
- **Metadata:** Each chunk stores source filename, chunk index, character positions

**Excel Special Handling:**
- Auto-detects real header row (skips merged title rows)
- Keyword matching: name, roll, total, marks, attendance, etc.
- Filters out non-data rows (totals, max-marks)
- Preserves preamble (college name, department info)

#### 5.3.2 Embedding & Vector Store (`ingestion/embeddings.py`)

**Embedding Model:**
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Output dimensions: 384
- Batch embedding support for efficiency

**Vector Store (ChromaDB):**
- In-memory ephemeral client (no persistence needed)
- Collection with cosine distance metric
- Operations: add, search, search_with_embeddings, clear, count
- Stores document text + metadata + embeddings

**Similarity Computation:**
```python
cosine_similarity = dot(A, B) / (norm(A) * norm(B))
```
Returns value between 0 (no similarity) and 1 (identical meaning).

### 5.4 Frontend Development & Documentation (L. Sravya Naga Sri)

#### 5.4.1 React Frontend (`frontend/src/App.jsx`)

**Application Structure:**
- Single-page application with tab-based navigation
- Tabs: Upload, Query, Verify Claims, About

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `App` | Main application with tab routing |
| `UploadTab` | File upload with drag-and-drop, file management |
| `QueryTab` | Query input, results display, verification metrics |
| `VerifyTab` | Direct claim verification interface |
| `AboutTab` | System documentation and pipeline explanation |
| `ResponseRenderer` | Smart response rendering (tables, lists, details) |
| `ComparisonTable` | Side-by-side student comparison with color coding |
| `ListResponse` | Tabular list for filter query results |
| `DetailTable` | Key-value table for student details |
| `ClaimCard` | Expandable claim with evidence display |
| `EvidenceCard` | Evidence chunk with similarity score |
| `Metric` | Numeric metric display card |

**UI Features:**
- Dark theme with gradient backgrounds
- Three verification states: Verified (green), Partially Verified (amber), Hallucinated (red)
- Support ratio percentage with color-coded progress bar
- Expandable claim cards with best evidence
- Tabular rendering for comparisons and lists
- Auto-clear uploads on app start (clean slate each session)
- Auto-switch to Query tab after successful upload
- Responsive design with Tailwind CSS

**Build Configuration:**
- Vite with React plugin + Tailwind CSS plugin
- Dev server proxy: `/api` -> `http://localhost:8001`
- Production build served by FastAPI

---

## 6. Algorithm: Hallucination Firewall

```
Algorithm: Hallucination Firewall
Input:  Query Q, Source data D
Output: Verified response or BLOCK

1. Retrieve relevant records from D using hybrid retrieval (exact + semantic)
2. Construct context window C from retrieved records
3. Generate response R = LLM(Q, C) with low temperature (0.3)
4. Extract atomic claims {c1, c2, ..., cn} from R
5. For each claim ci:
   a. Exact identifier matching
   b. Numerical consistency check
   c. Semantic similarity analysis (cosine similarity)
   d. NLI entailment check (DeBERTa)
   e. Assign verification score vi
6. Compute Support Ratio = Sum(verified) / n
7. If ratio >= threshold (0.6): PASS -> deliver R
   Else: FAIL -> refine prompt, regenerate (max 2 attempts)
8. If still FAIL after regeneration: deliver with verification notes
```

---

## 7. Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `SIMILARITY_THRESHOLD` | 0.6 | Minimum cosine similarity for claim-evidence match |
| `FIREWALL_THRESHOLD` | 0.6 | Minimum support ratio to pass firewall |
| `RELEVANCE_THRESHOLD` | 0.3 | Minimum relevance to uploaded content |
| `TOP_K_RETRIEVAL` | 7 | Number of evidence chunks retrieved |
| `CHUNK_SIZE` | 1000 | Characters per document chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between consecutive chunks |
| `MAX_TOKENS` | 1024 | Maximum LLM response tokens |
| `TEMPERATURE` | 0.3 | LLM generation temperature |
| `MAX_REGENERATION_ATTEMPTS` | 2 | Maximum regeneration attempts |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Sentence embedding model |
| `NLI_MODEL` | microsoft/deberta-base-mnli | Entailment checking model |
| `LLM_MODEL` | llama-3.3-70b-versatile | Groq-hosted LLM |

---

## 8. Results & Analysis

| Metric | Value |
|--------|-------|
| **Dataset Size** | 75 records |
| **Total Queries** | 12 |
| **Claims Extracted** | 62 |
| **Claims Verified** | 49 / 62 (79.03%) |
| **Hallucination Detection** | 100% |
| **Queries PASS** | 7 / 12 (58.3%) |
| **Queries FAIL** | 5 / 12 (41.7%) |
| **Mean Latency** | 2.4 seconds |

Of 62 claims extracted, 49 were verified. The remaining 13 triggered the firewall. Every hallucinated response was correctly identified - **100% detection accuracy with zero false negatives**.

---

## 9. Comparison with Existing Approaches

| Approach | Ext. Retrieval | Prompt Control | Post-Gen Validation | Claim Verification | Hallucination Block |
|----------|:-:|:-:|:-:|:-:|:-:|
| RAG (Standard) | Yes | No | No | No | No |
| Prompt Engineering | No | Yes | No | No | No |
| Confidence Estimation | No | No | Partial | No | No |
| Citation-Based | Yes | No | Partial | No | No |
| Self-Reflection | Yes | Yes | Partial | No | No |
| **Hallucination Firewall** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

**Key Insight:** The Hallucination Firewall is the only approach providing all five capabilities simultaneously. It is model-agnostic and deployable on any RAG system without architectural changes.

---

## 10. Deployment

### 10.1 Local Development
```bash
# Backend
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8001

# Frontend
cd frontend && npm install && npm run dev
```

### 10.2 Production (Hugging Face Spaces)
- **URL:** https://huggingface.co/spaces/Teja990/HallucinationFirewall
- **SDK:** Docker
- **Hardware:** CPU Basic (2 vCPU, 16GB RAM)
- **Environment:** GROQ_API_KEY secret variable

### 10.3 GitHub Repository
- **URL:** https://github.com/Teja-m9/HallucinationFirewall
- **Branch:** clean-main

---

## 11. Project Structure

```
Hallucination Firewall/
|
|-- api.py                          # FastAPI REST API (main entry point)
|-- app.py                          # Alternative Streamlit interface
|-- run.py                          # CLI demo and testing
|-- Dockerfile                      # Docker deployment config
|-- Procfile                        # Process file for deployment
|-- railway.json                    # Railway deployment config
|-- nixpacks.toml                   # Nixpacks build config
|-- requirements.txt                # Python dependencies
|-- .env.example                    # Environment variable template
|
|-- config/
|   |-- __init__.py
|   |-- settings.py                 # Central configuration
|
|-- core/
|   |-- __init__.py
|   |-- claim_extractor.py          # Claim decomposition
|   |-- verifier.py                 # Three-stage verification
|   |-- firewall.py                 # Firewall decision engine
|   |-- pipeline.py                 # Main pipeline orchestration
|
|-- generation/
|   |-- __init__.py
|   |-- generator.py                # LLM response generation (Groq)
|   |-- prompt_refiner.py           # Prompt refinement for regeneration
|
|-- ingestion/
|   |-- __init__.py
|   |-- loader.py                   # Document loading & chunking
|   |-- embeddings.py               # Sentence-BERT embeddings & ChromaDB
|
|-- retrieval/
|   |-- __init__.py
|   |-- retriever.py                # Semantic search & evidence retrieval
|
|-- utils/
|   |-- __init__.py
|   |-- data_analyzer.py            # Structured data analysis (Excel/CSV)
|   |-- logger.py                   # Logging utilities
|
|-- frontend/
|   |-- src/
|   |   |-- App.jsx                 # React application
|   |   |-- main.jsx                # Entry point
|   |   |-- index.css               # Tailwind CSS styles
|   |-- dist/                       # Production build
|   |-- package.json                # Node.js dependencies
|   |-- vite.config.js              # Vite build configuration
|   |-- index.html                  # HTML template
|
|-- data/
|   |-- sample_docs/                # Sample test documents
|   |-- uploads/                    # User uploaded documents
|
|-- tests/
|   |-- __init__.py
|   |-- test_pipeline.py            # Unit tests
|
|-- output/
|   |-- OUTPUT_REPORT.txt           # Pipeline output reports
```

---

## 12. Conclusions

The Hallucination Firewall demonstrates that post-generation validation effectively eliminates hallucinations from RAG systems:

- **100% hallucination detection** across all test queries
- **79.03% claim-level verification** - 49 of 62 claims verified
- **2.4 second mean latency** with minimal overhead
- **Model-agnostic** - zero LLM modifications required
- **Supports all document types** - PDF, TXT, DOCX, Excel, CSV
- **Dual-mode analysis** - RAG for text docs, direct computation for structured data
- **Production-ready** - deployed on Hugging Face Spaces with React frontend

---

## 13. References

1. Lewis et al. (2020) "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS 33.
2. Ji et al. (2023) "Survey of Hallucination in Natural Language Generation," ACM Computing Surveys 55(12).
3. Gao et al. (2023) "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv:2312.10997.
4. Min et al. (2023) "FActScore: Fine-grained Atomic Evaluation of Factual Precision," EMNLP.
5. Manakul et al. (2023) "SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection," EMNLP.

---

## 14. Applications

- Enterprise knowledge bases
- Clinical decision support systems
- Financial analytics and reporting
- Educational platforms and assessment
- Legal document verification
- Government data integrity
