"""
Configuration Module for Verification-Driven Hallucination Firewall (VDHF)

Central configuration for thresholds, model settings, and parameters.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# API CONFIGURATION
# =============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# =============================================================================
# VERIFICATION THRESHOLDS
# =============================================================================

# Semantic similarity threshold (theta_sim)
# Claims with similarity below this are considered unsupported
SIMILARITY_THRESHOLD = 0.6

# Firewall threshold (tau)
# Responses with SupportRatio below this trigger regeneration
FIREWALL_THRESHOLD = 0.6

# =============================================================================
# DOCUMENT INGESTION PARAMETERS
# =============================================================================

# Chunk size in characters (approximately 300-500 tokens)
CHUNK_SIZE = 1000

# Overlap between chunks in characters
CHUNK_OVERLAP = 200

# =============================================================================
# RETRIEVAL PARAMETERS
# =============================================================================

# Number of top-K chunks to retrieve
TOP_K_RETRIEVAL = 7

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Embedding model (Sentence-BERT)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# NLI model for entailment checking
NLI_MODEL = "microsoft/deberta-base-mnli"

# LLM model for generation (Groq)
LLM_MODEL = "llama-3.3-70b-versatile"

# =============================================================================
# VECTOR DATABASE CONFIGURATION
# =============================================================================

# ChromaDB collection name
CHROMA_COLLECTION_NAME = "vdhf_documents"

# Persist directory for ChromaDB
CHROMA_PERSIST_DIR = "./chroma_db"

# =============================================================================
# GENERATION PARAMETERS
# =============================================================================

# Maximum tokens for generation
MAX_TOKENS = 1024

# Temperature for generation (lower = more deterministic)
TEMPERATURE = 0.3

# Maximum regeneration attempts
MAX_REGENERATION_ATTEMPTS = 2

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

INITIAL_GENERATION_PROMPT = """Answer the question using the following context. Use the information faithfully and accurately. Do not add information not present in the context. Do not include source references, file paths, or [Source: ...] tags in your answer — just provide a clean, natural response.

Context:
{context}

Question:
{question}

Answer:"""

REFINED_GENERATION_PROMPT = """Rewrite the answer using only the verified evidence below.
Exclude any unsupported claims.
If evidence is insufficient, clearly state the limitation.
Do not introduce external information not present in the evidence.
Do not include source references, file paths, or [Source: ...] tags in your answer — just provide a clean, natural response.

Question:
{question}

Verified Evidence:
{evidence}

Answer:"""

CLAIM_EXTRACTION_PROMPT = """Extract all factual claims from the following text. Each claim should be an atomic, independently verifiable statement.

Rules:
1. Split compound sentences into separate claims
2. Only include factual statements, not opinions or vague statements
3. Each claim should be self-contained
4. Return one claim per line

Text:
{text}

Claims:"""
