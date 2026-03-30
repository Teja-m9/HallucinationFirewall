"""
VDHF FastAPI Backend
Serves the Hallucination Firewall pipeline as REST API endpoints.
"""

import os
import re
import sys
import time
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="VDHF API", version="1.0.0")

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global pipeline instance ─────────────────────────────────────────────────
from config.settings import SIMILARITY_THRESHOLD, FIREWALL_THRESHOLD
pipeline = None
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_docs")

# Structured data analyzer for Excel/CSV queries
from utils.data_analyzer import StructuredDataStore
data_store = StructuredDataStore()


def get_pipeline(force_clean: bool = False):
    global pipeline
    if pipeline is None or force_clean:
        from core.pipeline import VDHFPipeline
        pipeline = VDHFPipeline()
        # Clear the vector store to ensure a fresh start
        pipeline.clear_documents()
        # Auto-load any previously uploaded files
        _reload_uploads()
    return pipeline


def _reload_uploads():
    """Re-ingest files left in the uploads folder from a prior session."""
    global uploaded_files
    if not os.path.exists(UPLOAD_DIR):
        return
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        try:
            pipeline.ingest_file(fpath)
            if ext in (".xlsx", ".xls"):
                data_store.load_excel(fpath)
            elif ext == ".csv":
                data_store.load_csv(fpath)
            if fname not in uploaded_files:
                uploaded_files.append(fname)
        except Exception as e:
            print(f"Warning: could not reload {fname}: {e}")


# ── Request / Response Models ────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    similarity_threshold: float = 0.75
    firewall_threshold: float = 0.80
    top_k: int = 7


class ClaimResult(BaseModel):
    text: str
    is_supported: bool
    similarity_score: float
    entailment_label: str
    best_evidence: str
    evidence_source: str


class EvidenceResult(BaseModel):
    content: str
    similarity_score: float
    source: str
    rank: int


class QueryResponse(BaseModel):
    query: str
    response: str
    is_verified: bool
    support_ratio: float
    total_claims: int
    supported_claims: int
    regeneration_attempts: int
    claims: List[ClaimResult]
    evidence: List[EvidenceResult]
    elapsed_seconds: float


class VerifyRequest(BaseModel):
    claims: List[str]
    top_k: int = 7


class VerifyClaimResult(BaseModel):
    text: str
    is_supported: bool
    similarity_score: float
    entailment_label: str
    best_evidence: str


class VerifyResponse(BaseModel):
    results: List[VerifyClaimResult]
    supported: int
    total: int
    ratio: float


class StatusResponse(BaseModel):
    document_chunks: int
    documents_loaded: List[str]
    uploaded_files: List[str]
    similarity_threshold: float
    firewall_threshold: float


# Track uploaded file names
uploaded_files: List[str] = []

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".xlsx", ".xls", ".csv"}
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/status", response_model=StatusResponse)
def status():
    return StatusResponse(
        document_chunks=pipeline.document_count if pipeline else 0,
        documents_loaded=[],
        uploaded_files=uploaded_files,
        similarity_threshold=SIMILARITY_THRESHOLD,
        firewall_threshold=FIREWALL_THRESHOLD,
    )


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    p = get_pipeline()
    start = time.time()

    # ── Try structured data analysis first (Excel/CSV queries) ───────────
    computed_answer = data_store.answer_query(req.query) if data_store.has_data else None

    if computed_answer:
        elapsed = time.time() - start
        is_partial = "PARTIAL VERIFICATION" in computed_answer
        is_hallucination = "HALLUCINATION DETECTED" in computed_answer

        if is_partial:
            # One entity found, one not — partially verified
            claims = [
                ClaimResult(
                    text="One student/ID was found in the data.",
                    is_supported=True,
                    similarity_score=1.0,
                    entailment_label="DATA_VERIFIED",
                    best_evidence="Found in uploaded data.",
                    evidence_source="Structured Data Analysis",
                ),
                ClaimResult(
                    text="The other student/ID does not exist in the uploaded data.",
                    is_supported=False,
                    similarity_score=0.0,
                    entailment_label="NOT_FOUND",
                    best_evidence="No matching record exists in the uploaded data.",
                    evidence_source="Structured Data Analysis",
                ),
            ]
            return QueryResponse(
                query=req.query,
                response=computed_answer,
                is_verified=False,
                support_ratio=0.5,
                total_claims=2,
                supported_claims=1,
                regeneration_attempts=0,
                claims=claims,
                evidence=[],
                elapsed_seconds=round(elapsed, 3),
            )

        if is_hallucination:
            # The query references an ID/name not found in the data
            claims = [
                ClaimResult(
                    text=computed_answer,
                    is_supported=False,
                    similarity_score=0.0,
                    entailment_label="NOT_FOUND",
                    best_evidence="No matching record exists in the uploaded data.",
                    evidence_source="Structured Data Analysis",
                )
            ]
            return QueryResponse(
                query=req.query,
                response=computed_answer,
                is_verified=False,
                support_ratio=0.0,
                total_claims=1,
                supported_claims=0,
                regeneration_attempts=0,
                claims=claims,
                evidence=[],
                elapsed_seconds=round(elapsed, 3),
            )

        # Answer was computed directly from the raw spreadsheet data,
        # so it is correct by definition — no LLM hallucination possible.
        from core.claim_extractor import ClaimExtractor
        extractor = ClaimExtractor()
        claim_objs = extractor.extract_claims(computed_answer)

        claims = [
            ClaimResult(
                text=c.text,
                is_supported=True,
                similarity_score=1.0,
                entailment_label="DATA_VERIFIED",
                best_evidence="Computed directly from uploaded spreadsheet data.",
                evidence_source="Structured Data Analysis",
            )
            for c in claim_objs
        ]

        total = len(claims) if claims else 1

        return QueryResponse(
            query=req.query,
            response=computed_answer,
            is_verified=True,
            support_ratio=1.0,
            total_claims=total,
            supported_claims=total,
            regeneration_attempts=0,
            claims=claims,
            evidence=[],
            elapsed_seconds=round(elapsed, 3),
        )

    # ── Normal RAG pipeline ──────────────────────────────────────────────
    p.similarity_threshold = req.similarity_threshold
    p.firewall_threshold = req.firewall_threshold
    p.top_k = req.top_k
    p.verifier.similarity_threshold = req.similarity_threshold
    p.firewall.similarity_threshold = req.similarity_threshold
    p.firewall.decision_engine.threshold = req.firewall_threshold
    p.firewall.decision_engine.scoring_module.threshold = req.firewall_threshold

    result = p.query(req.query, verbose=False)
    elapsed = time.time() - start

    # ── Check if query is relevant to the uploaded documents ────────────
    RELEVANCE_THRESHOLD = 0.3
    best_score = max((ev.similarity_score for ev in result.retrieved_evidence), default=0)

    if best_score < RELEVANCE_THRESHOLD:
        # Query is completely unrelated to uploaded documents
        doc_names = ", ".join(uploaded_files) if uploaded_files else "the uploaded documents"
        no_match_response = (
            f"This query is not related to {doc_names}. "
            f"The uploaded documents do not contain any information about \"{req.query}\". "
            f"Please ask questions relevant to the content you have uploaded."
        )
        claims = [
            ClaimResult(
                text=f"The query \"{req.query}\" has no matching content in the uploaded documents.",
                is_supported=False,
                similarity_score=round(best_score, 4),
                entailment_label="NO_RELEVANT_DATA",
                best_evidence="No relevant information found in the uploaded documents.",
                evidence_source="Relevance Check",
            )
        ]
        return QueryResponse(
            query=req.query,
            response=no_match_response,
            is_verified=False,
            support_ratio=0.0,
            total_claims=1,
            supported_claims=0,
            regeneration_attempts=0,
            claims=claims,
            evidence=[],
            elapsed_seconds=round(elapsed, 3),
        )

    claims = []
    for vr in result.verification_results:
        claims.append(ClaimResult(
            text=vr.claim.text,
            is_supported=vr.is_supported,
            similarity_score=round(vr.similarity_score, 4),
            entailment_label=vr.entailment_label,
            best_evidence=vr.best_evidence[:500] if vr.best_evidence else "",
            evidence_source=vr.evidence_source,
        ))

    evidence = []
    for ev in result.retrieved_evidence:
        evidence.append(EvidenceResult(
            content=ev.content[:400],
            similarity_score=round(ev.similarity_score, 4),
            source=os.path.basename(ev.metadata.get("source", "Unknown")),
            rank=ev.rank,
        ))

    # Strip any [Source: ...] tags that leaked into the response
    clean_response = re.sub(r'\[Source:\s*[^\]]*\]\s*', '', result.final_response).strip()

    # ── Build explanation based on verification outcome ──────────────────
    if result.supported_claims == 0 and result.total_claims > 0:
        clean_response = (
            f"Hallucination detected: The generated response could not be verified against the uploaded documents. "
            f"None of the {result.total_claims} claim(s) in the response were supported by the available evidence. "
            f"The information requested may not exist in the uploaded data."
        )
    elif result.supported_claims < result.total_claims:
        unsupported = result.total_claims - result.supported_claims
        clean_response = (
            f"{clean_response}\n\n"
            f"Note: {unsupported} out of {result.total_claims} claim(s) could not be verified against the uploaded documents."
        )

    return QueryResponse(
        query=req.query,
        response=clean_response,
        is_verified=result.is_verified,
        support_ratio=round(result.support_ratio, 4),
        total_claims=result.total_claims,
        supported_claims=result.supported_claims,
        regeneration_attempts=result.regeneration_attempts,
        claims=claims,
        evidence=evidence,
        elapsed_seconds=round(elapsed, 3),
    )


@app.post("/api/verify", response_model=VerifyResponse)
def verify_claims(req: VerifyRequest):
    from core.claim_extractor import Claim

    p = get_pipeline()
    combined = " ".join(req.claims)
    evidence_list = p.retriever.retrieve(combined, top_k=req.top_k)

    claim_objs = [Claim(text=t, claim_id=i) for i, t in enumerate(req.claims)]
    vr_list = p.verifier.verify_all_claims(claim_objs, evidence_list)

    results = []
    for vr in vr_list:
        results.append(VerifyClaimResult(
            text=vr.claim.text,
            is_supported=vr.is_supported,
            similarity_score=round(vr.similarity_score, 4),
            entailment_label=vr.entailment_label,
            best_evidence=vr.best_evidence[:500] if vr.best_evidence else "",
        ))

    supported = sum(1 for r in results if r.is_supported)
    total = len(results)
    return VerifyResponse(
        results=results,
        supported=supported,
        total=total,
        ratio=round(supported / total, 4) if total > 0 else 0,
    )


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document (TXT, PDF, DOCX, Excel, CSV)."""
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Save file
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        chunks_added = 0

        # For Excel/CSV: load into structured data store (fast, no ML models needed)
        if ext in (".xlsx", ".xls"):
            rows = data_store.load_excel(save_path)
            chunks_added = rows
        elif ext == ".csv":
            rows = data_store.load_csv(save_path)
            chunks_added = rows

        # For text documents: need the full pipeline with ML models
        if ext in (".txt", ".pdf", ".docx"):
            p = get_pipeline()
            chunks_added = p.ingest_file(save_path)

        # Also ingest into vector store for RAG queries (if pipeline already loaded)
        if pipeline is not None and ext in (".xlsx", ".xls", ".csv"):
            chunks_added = pipeline.ingest_file(save_path)

        uploaded_files.append(file.filename)

        return {
            "filename": file.filename,
            "file_type": ext,
            "chunks_added": chunks_added,
            "total_chunks": pipeline.document_count if pipeline else chunks_added,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to process {file.filename}: {str(e)}")


@app.post("/api/clear-uploads")
def clear_uploads():
    """Clear all uploaded documents and reset the pipeline."""
    global pipeline, uploaded_files
    pipeline = None
    uploaded_files = []
    data_store.clear()
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            os.remove(os.path.join(UPLOAD_DIR, f))
    p = get_pipeline(force_clean=True)
    return {"status": "cleared", "total_chunks": p.document_count}


class DeleteRequest(BaseModel):
    filename: str


@app.post("/api/delete-file")
def delete_file(req: DeleteRequest):
    """Delete a single uploaded file and rebuild the pipeline."""
    global pipeline, uploaded_files

    fpath = os.path.join(UPLOAD_DIR, req.filename)
    if not os.path.exists(fpath):
        raise HTTPException(404, f"File not found: {req.filename}")

    # Remove the file
    os.remove(fpath)

    # Remove from tracked list
    uploaded_files = [f for f in uploaded_files if f != req.filename]

    # Rebuild pipeline + data store from remaining files
    pipeline = None
    data_store.clear()
    p = get_pipeline(force_clean=True)

    return {
        "deleted": req.filename,
        "remaining_files": uploaded_files,
        "total_chunks": p.document_count,
    }


# ── Serve React build ────────────────────────────────────────────────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse

    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
