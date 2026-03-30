---
title: Hallucination Firewall
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Verification-Driven Hallucination Firewall (VDHF)

A modular Python system that verifies RAG (Retrieval-Augmented Generation) outputs before delivering them to users, preventing AI hallucinations.

Upload documents (TXT, PDF, DOCX, Excel, CSV), ask questions, and get verified answers with every claim checked against your content.

## How It Works

1. **Upload Documents** - Upload any document to the system
2. **Ask Questions** - Query your uploaded content
3. **Claim Extraction** - Every factual claim in the response is identified
4. **Verification** - Each claim is checked against your uploaded data
5. **Firewall Decision** - Response is marked as Verified, Partially Verified, or Hallucinated
6. **Regeneration** - If needed, a safer response is generated

## Features

- Excel/CSV direct data analysis (no ML models needed)
- Student comparison and filter queries
- Claim verification against uploaded data
- Hallucination detection for non-existent records
- Groq LLM-powered analysis for complex questions
- Beautiful React frontend with tabular response rendering

## Tech Stack

- **Backend**: FastAPI + Python
- **Frontend**: React + Vite + Tailwind CSS
- **ML**: Sentence-BERT, DeBERTa NLI
- **Vector DB**: ChromaDB
- **LLM**: Groq API
