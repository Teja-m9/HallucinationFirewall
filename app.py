"""
VDHF - Streamlit Interface
Verification-Driven Hallucination Firewall
"""

import os
import sys
import time
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_docs")


# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VDHF - Hallucination Firewall",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        padding: 0.5rem 0 0.2rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-card h3 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 0; font-size: 0.85rem; opacity: 0.9; }
    .claim-supported {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
    }
    .claim-unsupported {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
    }
    .evidence-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        margin: 0.4rem 0;
        font-size: 0.9rem;
    }
    .status-pass {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 600;
    }
    .status-fail {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ─── Pipeline Init (cached) ─────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_pipeline():
    """Initialize the VDHF pipeline and load documents."""
    from core.pipeline import VDHFPipeline
    pipeline = VDHFPipeline()

    # Load sample documents
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.txt'):
                filepath = os.path.join(DATA_DIR, filename)
                pipeline.ingest_file(filepath)

    return pipeline


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    similarity_threshold = st.slider(
        "Similarity Threshold (θ_sim)",
        min_value=0.0, max_value=1.0, value=0.75, step=0.05,
        help="Minimum semantic similarity for a claim to be considered supported."
    )
    firewall_threshold = st.slider(
        "Firewall Threshold (τ)",
        min_value=0.0, max_value=1.0, value=0.80, step=0.05,
        help="Minimum support ratio to pass the firewall."
    )
    top_k = st.slider(
        "Top-K Evidence Chunks",
        min_value=1, max_value=15, value=7,
        help="Number of evidence chunks to retrieve."
    )

    st.markdown("---")
    st.markdown("## 📚 Knowledge Base")

    # Custom document upload
    uploaded_file = st.file_uploader(
        "Upload a document (.txt)", type=["txt"],
        help="Add your own document to the knowledge base."
    )

    st.markdown("---")
    st.markdown("## ℹ️ How It Works")
    st.markdown("""
    1. **Retrieve** relevant evidence from documents
    2. **Generate** an LLM response using context
    3. **Extract** atomic factual claims
    4. **Verify** each claim against evidence
    5. **Firewall** blocks hallucinated responses
    6. **Regenerate** using only verified evidence
    """)


# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🛡️ Hallucination Firewall</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Verification-Driven Hallucination Firewall for RAG Systems</div>', unsafe_allow_html=True)

# ─── Load Pipeline ───────────────────────────────────────────────────────────
with st.spinner("🔄 Loading models and documents... (first load may take a moment)"):
    pipeline = load_pipeline()

# Handle file upload
if uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    if f"uploaded_{uploaded_file.name}" not in st.session_state:
        pipeline.ingest_text(content, source=uploaded_file.name)
        st.session_state[f"uploaded_{uploaded_file.name}"] = True
        st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")

# Show doc count
st.sidebar.metric("Document Chunks Loaded", pipeline.document_count)

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_query, tab_analyze, tab_about = st.tabs(["🔍 Query", "🧪 Analyze Claims", "📖 About"])

# ═══ TAB 1: Query ════════════════════════════════════════════════════════════
with tab_query:
    query = st.text_input(
        "Ask a question about the knowledge base:",
        placeholder="e.g., When was Python released and who created it?",
    )

    col_btn, col_examples = st.columns([1, 3])
    with col_btn:
        run_query = st.button("🚀 Run Query", type="primary", use_container_width=True)
    with col_examples:
        example = st.selectbox("Or try an example:", [
            "",
            "When was Python released and who created it?",
            "What caused World War I?",
            "Tell me about artificial intelligence history.",
            "How does the human body work?",
            "What is climate change and what causes it?",
            "Tell me about the Renaissance period.",
            "How did the internet develop?",
        ], label_visibility="collapsed")

    if example and not query:
        query = example
        run_query = True

    if run_query and query:
        # Update pipeline thresholds
        pipeline.similarity_threshold = similarity_threshold
        pipeline.firewall_threshold = firewall_threshold
        pipeline.top_k = top_k
        pipeline.verifier.similarity_threshold = similarity_threshold
        pipeline.firewall.similarity_threshold = similarity_threshold
        pipeline.firewall.decision_engine.threshold = firewall_threshold
        pipeline.firewall.decision_engine.scoring_module.threshold = firewall_threshold

        with st.spinner("Processing query through the VDHF pipeline..."):
            start_time = time.time()
            result = pipeline.query(query, verbose=False)
            elapsed = time.time() - start_time

        # ── Status Banner ──
        if result.is_verified:
            st.markdown(
                f'<div class="status-pass">✅ VERIFIED — Support Ratio: {result.support_ratio:.0%} '
                f'({result.supported_claims}/{result.total_claims} claims supported)</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="status-fail">⚠️ PARTIALLY VERIFIED — Support Ratio: {result.support_ratio:.0%} '
                f'({result.supported_claims}/{result.total_claims} claims supported)</div>',
                unsafe_allow_html=True
            )

        st.markdown("")

        # ── Metrics Row ──
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Support Ratio", f"{result.support_ratio:.0%}")
        m2.metric("Total Claims", result.total_claims)
        m3.metric("Supported", result.supported_claims)
        m4.metric("Regenerations", result.regeneration_attempts)

        st.markdown("---")

        # ── Response ──
        st.subheader("📝 Response")
        st.info(result.final_response)
        st.caption(f"⏱️ Processed in {elapsed:.2f}s")

        # ── Claims Breakdown ──
        if result.verification_results:
            st.subheader("🔬 Claims Verification")

            for vr in result.verification_results:
                if vr.is_supported:
                    st.markdown(
                        f'<div class="claim-supported">'
                        f'<strong>✅ SUPPORTED</strong> (similarity: {vr.similarity_score:.3f}, '
                        f'entailment: {vr.entailment_label})<br/>'
                        f'{vr.claim.text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="claim-unsupported">'
                        f'<strong>❌ UNSUPPORTED</strong> (similarity: {vr.similarity_score:.3f}, '
                        f'entailment: {vr.entailment_label})<br/>'
                        f'{vr.claim.text}</div>',
                        unsafe_allow_html=True
                    )

        # ── Retrieved Evidence ──
        if result.retrieved_evidence:
            with st.expander(f"📄 Retrieved Evidence ({len(result.retrieved_evidence)} chunks)", expanded=False):
                for i, ev in enumerate(result.retrieved_evidence, 1):
                    source = os.path.basename(ev.metadata.get("source", "Unknown"))
                    st.markdown(
                        f'<div class="evidence-box">'
                        f'<strong>[{i}]</strong> Score: {ev.similarity_score:.3f} | Source: {source}<br/>'
                        f'{ev.content[:300]}{"..." if len(ev.content) > 300 else ""}</div>',
                        unsafe_allow_html=True
                    )

# ═══ TAB 2: Analyze Claims ═══════════════════════════════════════════════════
with tab_analyze:
    st.subheader("Test Custom Claims Against the Knowledge Base")
    st.markdown("Enter individual claims to verify them against the loaded documents.")

    claims_input = st.text_area(
        "Enter claims (one per line):",
        placeholder="Python was created by Guido van Rossum.\nPython was released in 2005.\nPython is a compiled language.",
        height=150,
    )

    if st.button("🔍 Verify Claims", type="primary"):
        if claims_input.strip():
            from core.claim_extractor import Claim
            from retrieval.retriever import RetrievedEvidence

            lines = [l.strip() for l in claims_input.strip().split("\n") if l.strip()]

            with st.spinner("Verifying claims..."):
                # Retrieve evidence for all claims combined
                combined_query = " ".join(lines)
                evidence_list = pipeline.retriever.retrieve(combined_query, top_k=top_k)

                claims = [Claim(text=line, claim_id=i) for i, line in enumerate(lines)]
                results = pipeline.verifier.verify_all_claims(claims, evidence_list)

            supported = sum(1 for r in results if r.is_supported)
            total = len(results)
            ratio = supported / total if total > 0 else 0

            st.markdown(f"**Results: {supported}/{total} claims supported ({ratio:.0%})**")
            st.progress(ratio)

            for vr in results:
                if vr.is_supported:
                    st.markdown(
                        f'<div class="claim-supported">'
                        f'<strong>✅ SUPPORTED</strong> (score: {vr.similarity_score:.3f})<br/>'
                        f'{vr.claim.text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="claim-unsupported">'
                        f'<strong>❌ UNSUPPORTED</strong> (score: {vr.similarity_score:.3f})<br/>'
                        f'{vr.claim.text}</div>',
                        unsafe_allow_html=True
                    )

                if vr.best_evidence:
                    with st.expander(f"Evidence for: {vr.claim.text[:50]}..."):
                        st.markdown(
                            f'<div class="evidence-box">{vr.best_evidence[:500]}</div>',
                            unsafe_allow_html=True
                        )
        else:
            st.warning("Please enter at least one claim.")

# ═══ TAB 3: About ════════════════════════════════════════════════════════════
with tab_about:
    st.subheader("About VDHF")
    st.markdown("""
    The **Verification-Driven Hallucination Firewall (VDHF)** is a post-generation
    verification system that detects and mitigates hallucinations in LLM-generated responses.

    ### Architecture

    ```
    User Query
        │
        ▼
    ┌─────────────────┐
    │  RAG Retrieval   │  ← Sentence-BERT + ChromaDB
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │  LLM Generation  │  ← Groq API / Mock
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ Claim Extraction │  ← Rule-based decomposition
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │  Verification    │  ← Semantic Similarity + NLI
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │    Firewall      │  ← Support Ratio ≥ τ ?
    └────────┬────────┘
         ┌───┴───┐
         ▼       ▼
       PASS   REGENERATE
    ```

    ### Key Parameters

    | Parameter | Default | Description |
    |-----------|---------|-------------|
    | Similarity Threshold (θ_sim) | 0.75 | Min cosine similarity for support |
    | Firewall Threshold (τ) | 0.80 | Min support ratio to pass |
    | Top-K | 7 | Evidence chunks retrieved |
    | Max Regenerations | 2 | Retry attempts on failure |

    ### Models Used

    - **Embeddings**: `all-MiniLM-L6-v2` (Sentence-BERT)
    - **NLI**: `microsoft/deberta-base-mnli`
    - **LLM**: `llama-3.3-70b-versatile` (via Groq API)

    ### Knowledge Base

    The system comes preloaded with 12 sample documents covering:
    Python, Ancient Egypt, AI, Climate Change, Economics, Human Body,
    Internet Technology, Music History, Quantum Physics, Renaissance,
    Solar System, and World War II.
    """)
