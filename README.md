# Verification-Driven Hallucination Firewall (VDHF)

A modular Python system that verifies RAG (Retrieval-Augmented Generation) outputs before delivering them to users, preventing AI hallucinations.

---

## 📋 Prerequisites

### Required
1. **Python 3.9+** - Download from https://www.python.org/downloads/
   - ⚠️ During installation, check **"Add Python to PATH"**

### Optional (for full LLM features)
2. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
   - Without this, the system uses mock generation for testing

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```powershell
cd "c:\Users\HP\Desktop\Hallucination Firewall"
pip install -r requirements.txt
```

### Step 2: (Optional) Configure API Key
```powershell
copy .env.example .env
# Edit .env and add your OpenAI API key
```

### Step 3: Run the System
```powershell
python main.py
```

---

## 📂 Project Structure

```
Hallucination Firewall/
│
├── config.py              # Configuration (thresholds, models)
├── ingestion.py           # Document loading (PDF, TXT, DOCX)
├── embeddings.py          # Sentence-BERT embeddings + ChromaDB
├── retriever.py           # Semantic search for evidence
├── generator.py           # LLM response generation
├── claim_extractor.py     # Extract factual claims from text
├── verifier.py            # Verify claims using similarity + NLI
├── firewall.py            # Decision engine (pass/block)
├── prompt_refiner.py      # Regenerate safer responses
├── main.py                # Main pipeline + interactive CLI
│
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
│
├── sample_docs/
│   └── sample.txt         # Sample test documents
│
└── tests/
    └── test_pipeline.py   # Unit tests
```

---

## 🔧 How It Works

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ User Query  │───▶│   Retrieve   │───▶│ Generate Answer │
└─────────────┘    │   Evidence   │    └────────┬────────┘
                   └──────────────┘             │
                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Output    │◀───│   Firewall   │◀───│ Extract Claims  │
│  (Verified) │    │   Decision   │    │   & Verify      │
└─────────────┘    └──────────────┘    └─────────────────┘
                          │
                          │ If fails threshold
                          ▼
                   ┌──────────────┐
                   │   Refine &   │
                   │  Regenerate  │
                   └──────────────┘
```

### Pipeline Steps:
1. **Ingest Documents** → Load PDFs/TXT files into vector database
2. **Retrieve Evidence** → Find relevant chunks for user query
3. **Generate Response** → LLM creates initial answer
4. **Extract Claims** → Break response into atomic factual statements
5. **Verify Claims** → Check each claim against evidence
6. **Firewall Decision** → Pass if ≥80% claims verified
7. **Regenerate** → If failed, refine prompt and try again

---

## 💻 Interactive Commands

When running `main.py`, use these commands:

| Command | Description |
|---------|-------------|
| `/ingest <path>` | Load documents from file or folder |
| `/clear` | Clear all documents from memory |
| `/count` | Show number of document chunks |
| `/quit` | Exit the program |

**Example session:**
```
You: /ingest sample_docs
Ingested sample_docs: 5 chunks total

You: When was Python released?
[Processing...]
✓ VERIFIED - Support Ratio: 100%
Response: Python was first released in 1991 by Guido van Rossum.
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `SIMILARITY_THRESHOLD` | 0.75 | Minimum similarity for claim-evidence match |
| `FIREWALL_THRESHOLD` | 0.8 | Minimum % of claims that must be verified |
| `TOP_K_RETRIEVAL` | 7 | Number of evidence chunks to retrieve |
| `CHUNK_SIZE` | 1000 | Characters per document chunk |
| `LLM_MODEL` | gpt-3.5-turbo | OpenAI model to use |

---

### Step 4: Run Interactive Querying
To interactively query the system and see verification results:
```powershell
python run.py --demo
```

---

## 🧪 Running Tests


```powershell
python -m pytest tests/test_pipeline.py -v
```

---

## 📝 Example Output

```
============================================================
VDHF Pipeline Result
============================================================
Status: ✓ VERIFIED
Support Ratio: 100.00%
Claims: 2/2 supported
Regeneration Attempts: 0
============================================================
Response:
Python was released in 1991. It was created by Guido van Rossum.
============================================================
```

---

## 🔑 What You Need to Provide

| Item | Required? | How to Get |
|------|-----------|------------|
| Python 3.9+ | ✅ Yes | https://python.org/downloads |
| Documents to verify against | ✅ Yes | Your PDFs, TXT files |
| OpenAI API Key | ❌ Optional | https://platform.openai.com/api-keys |

---

## 📚 Module Details

### claim_extractor.py
Extracts atomic factual claims from LLM responses:
- Filters out opinions ("I think...")
- Splits compound sentences ("X and Y" → "X", "Y")
- Identifies verifiable statements

### verifier.py
Two-step verification:
1. **Semantic Similarity**: Cosine similarity ≥ 0.75
2. **NLI Entailment**: Evidence must logically support claim

### firewall.py
Decision logic:
- Calculate `SupportRatio = supported_claims / total_claims`
- If ratio ≥ 0.8: **PASS** (deliver to user)
- If ratio < 0.8: **REGENERATE** (refine and retry)
