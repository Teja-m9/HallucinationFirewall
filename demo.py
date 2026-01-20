"""
VDHF Demo - Simplified Standalone Version
No external dependencies required.

This demonstrates the Verification-Driven Hallucination Firewall concept
using built-in Python features only.
"""

import re
import math
from collections import Counter
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


# =============================================================================
# CONFIGURATION
# =============================================================================

SIMILARITY_THRESHOLD = 0.5  # Lower for basic word matching
FIREWALL_THRESHOLD = 0.8


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DocumentChunk:
    content: str
    source: str
    chunk_id: int


@dataclass
class Claim:
    text: str
    claim_id: int
    is_verified: bool = False
    similarity_score: float = 0.0
    supporting_evidence: str = ""


@dataclass
class VerificationResult:
    claim: Claim
    is_supported: bool
    similarity_score: float
    best_evidence: str


# =============================================================================
# SIMPLE TEXT SIMILARITY (TF-IDF inspired)
# =============================================================================

def tokenize(text: str) -> List[str]:
    """Simple tokenization."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'can', 'to',
                  'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                  'and', 'or', 'but', 'if', 'then', 'that', 'this', 'it'}
    return [w for w in words if w not in stop_words and len(w) > 1]


def compute_similarity(text1: str, text2: str) -> float:
    """Compute word-overlap based similarity."""
    words1 = set(tokenize(text1))
    words2 = set(tokenize(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    # Jaccard similarity
    jaccard = intersection / union if union > 0 else 0.0
    
    # Also consider coverage of claim words in evidence
    coverage = intersection / len(words1) if words1 else 0.0
    
    # Combined score
    return (jaccard + coverage) / 2


# =============================================================================
# DOCUMENT INGESTION
# =============================================================================

class DocumentStore:
    """Simple in-memory document store."""
    
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.chunk_counter = 0
    
    def add_text(self, text: str, source: str = "input") -> int:
        """Add text as document chunks."""
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        added = 0
        for para in paragraphs:
            if len(para) > 50:
                chunk = DocumentChunk(
                    content=para,
                    source=source,
                    chunk_id=self.chunk_counter
                )
                self.chunks.append(chunk)
                self.chunk_counter += 1
                added += 1
        
        return added
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for relevant chunks."""
        results = []
        
        for chunk in self.chunks:
            score = compute_similarity(query, chunk.content)
            results.append((chunk, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]


# =============================================================================
# CLAIM EXTRACTION
# =============================================================================

def extract_claims(response: str) -> List[Claim]:
    """Extract factual claims from response."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', response)
    
    claims = []
    claim_id = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        if len(sentence) < 20:
            continue
        
        # Skip questions
        if sentence.endswith('?'):
            continue
        
        # Skip opinions
        opinion_patterns = ['i think', 'i believe', 'probably', 'maybe', 'perhaps']
        if any(p in sentence.lower() for p in opinion_patterns):
            continue
        
        # Split on "and" for compound claims
        if ' and ' in sentence and len(sentence) > 80:
            parts = sentence.split(' and ')
            for part in parts:
                part = part.strip()
                if len(part) > 15:
                    claims.append(Claim(text=part, claim_id=claim_id))
                    claim_id += 1
        else:
            claims.append(Claim(text=sentence, claim_id=claim_id))
            claim_id += 1
    
    return claims


# =============================================================================
# CLAIM VERIFICATION
# =============================================================================

def verify_claim(claim: Claim, chunks: List[Tuple[DocumentChunk, float]]) -> VerificationResult:
    """Verify a single claim against evidence."""
    best_score = 0.0
    best_evidence = ""
    
    for chunk, _ in chunks:
        score = compute_similarity(claim.text, chunk.content)
        if score > best_score:
            best_score = score
            best_evidence = chunk.content
    
    is_supported = best_score >= SIMILARITY_THRESHOLD
    
    claim.is_verified = is_supported
    claim.similarity_score = best_score
    claim.supporting_evidence = best_evidence
    
    return VerificationResult(
        claim=claim,
        is_supported=is_supported,
        similarity_score=best_score,
        best_evidence=best_evidence[:200] + "..." if len(best_evidence) > 200 else best_evidence
    )


# =============================================================================
# FIREWALL
# =============================================================================

def apply_firewall(results: List[VerificationResult]) -> Dict[str, Any]:
    """Apply firewall decision logic."""
    if not results:
        return {
            'decision': 'PASS',
            'support_ratio': 1.0,
            'total_claims': 0,
            'supported': 0,
            'unsupported': 0
        }
    
    supported = sum(1 for r in results if r.is_supported)
    total = len(results)
    ratio = supported / total
    
    decision = 'PASS' if ratio >= FIREWALL_THRESHOLD else 'REGENERATE'
    
    return {
        'decision': decision,
        'support_ratio': ratio,
        'total_claims': total,
        'supported': supported,
        'unsupported': total - supported
    }


# =============================================================================
# MOCK LLM GENERATION
# =============================================================================

def generate_response(query: str, context: str) -> str:
    """Generate response from context (mock LLM)."""
    # Find relevant sentences from context
    sentences = re.split(r'(?<=[.!?])\s+', context)
    query_words = set(tokenize(query))
    
    relevant = []
    for sentence in sentences:
        sentence_words = set(tokenize(sentence))
        overlap = len(query_words & sentence_words)
        if overlap >= 1:
            relevant.append((overlap, sentence.strip()))
    
    # Sort by relevance
    relevant.sort(key=lambda x: x[0], reverse=True)
    
    # Build response from top relevant sentences
    response_parts = []
    for _, sentence in relevant[:3]:
        if sentence not in response_parts:
            response_parts.append(sentence)
    
    if response_parts:
        return ' '.join(response_parts)
    else:
        return "Based on the available information, I cannot find a specific answer to your question."


# =============================================================================
# MAIN PIPELINE
# =============================================================================

class VDHFPipeline:
    """Verification-Driven Hallucination Firewall Pipeline."""
    
    def __init__(self):
        self.store = DocumentStore()
        print("=" * 60)
        print("VDHF Demo - Verification-Driven Hallucination Firewall")
        print("=" * 60)
    
    def ingest(self, text: str, source: str = "document") -> int:
        """Ingest text into the document store."""
        count = self.store.add_text(text, source)
        print(f"[OK] Ingested {count} chunks from '{source}'")
        return count
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """Process a query through the VDHF pipeline."""
        print("\n" + "=" * 60)
        print(f"QUERY: {user_query}")
        print("=" * 60)
        
        # Step 1: Retrieve evidence
        print("\n[1] RETRIEVING EVIDENCE...")
        evidence = self.store.search(user_query, top_k=5)
        if not evidence:
            print("    [X] No documents found. Please ingest documents first.")
            return {'error': 'No documents'}
        
        # Check relevance
        best_score = evidence[0][1]
        print(f"    Best Match Score: {best_score:.3f}")
        
        if best_score < 0.25:
             print(f"    [X] Irrelevant query (Score {best_score:.3f} < 0.25)")
             response = "I cannot answer this question as it is not supported by the knowledge base."
             return {
                'response': response,
                'decision': 'FAIL',
                'support_ratio': 0.0,
                'claims': [],
                'results': []
            }
        
        for i, (chunk, score) in enumerate(evidence[:3], 1):
            print(f"    [{i}] Score: {score:.3f} - {chunk.content[:60]}...")
        
        # Step 2: Generate response
        print("\n[2] GENERATING RESPONSE...")
        context = '\n'.join([c.content for c, _ in evidence])
        response = generate_response(user_query, context)
        print(f"    Response: {response[:100]}...")
        
        # Step 3: Extract claims
        print("\n[3] EXTRACTING CLAIMS...")
        claims = extract_claims(response)
        print(f"    Found {len(claims)} claims")
        for claim in claims:
            print(f"      - {claim.text[:60]}...")
        
        # Step 4: Verify claims
        print("\n[4] VERIFYING CLAIMS...")
        results = [verify_claim(claim, evidence) for claim in claims]
        for result in results:
            status = "[OK] SUPPORTED" if result.is_supported else "[X] UNSUPPORTED"
            print(f"    {status} (score: {result.similarity_score:.3f})")
            print(f"      Claim: {result.claim.text[:50]}...")
        
        # Step 5: Apply firewall
        print("\n[5] APPLYING FIREWALL...")
        firewall_result = apply_firewall(results)
        decision = firewall_result['decision']
        ratio = firewall_result['support_ratio']
        
        if decision == 'PASS':
            print(f"    [PASS] PASSED - Support Ratio: {ratio:.1%})")
        else:
            print(f"    [WARN] BLOCKED - Support Ratio: {ratio:.1%} (threshold: {FIREWALL_THRESHOLD:.1%})")
        
        # Final output
        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(f"Decision: {'[OK] VERIFIED' if decision == 'PASS' else '[WARN] NEEDS REGENERATION'}")
        print(f"Support Ratio: {ratio:.1%}")
        print(f"Claims: {firewall_result['supported']}/{firewall_result['total_claims']} supported")
        print(f"\nResponse:\n{response}")
        print("=" * 60)
        
        return {
            'response': response,
            'decision': decision,
            'support_ratio': ratio,
            'claims': claims,
            'results': results
        }


# =============================================================================
# SAMPLE DOCUMENTS
# =============================================================================

SAMPLE_DOCUMENTS = """
Python Programming Language

Python is a high-level, general-purpose programming language. Its design philosophy 
emphasizes code readability with the use of significant indentation.

Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & 
Informatica (CWI) in the Netherlands. Python was first released in 1991.

Guido van Rossum began working on Python in the late 1980s as a successor to the 
ABC programming language. He chose the name Python because he was a fan of the 
British comedy series "Monty Python's Flying Circus."

Python consistently ranks as one of the most popular programming languages. 
It is used for web development, data science, artificial intelligence, 
scientific computing, and automation.

Key features of Python include dynamic typing and binding, built-in data structures 
like lists, tuples, and dictionaries, support for modules and packages, an extensive 
standard library, and support for multiple programming paradigms.

Python 2.0 was released on October 16, 2000. Python 3.0 was released on 
December 3, 2008. Python 2.7 reached end of life on January 1, 2020.

The Python Software Foundation (PSF) is a non-profit organization that holds 
the intellectual property rights behind Python and organizes PyCon.

World War I

World War I, often abbreviated as WWI, was a global conflict that lasted from 
1914 to 1918. It was one of the deadliest conflicts in human history.

The war was triggered by the assassination of Archduke Franz Ferdinand of 
Austria-Hungary on June 28, 1914, in Sarajevo by Gavrilo Princip.

Several factors contributed to the outbreak of World War I including militarism, 
alliances between nations, imperialism, and nationalism.

The major Allied Powers included France, the United Kingdom, Russia, Italy, 
and later the United States. The Central Powers included Germany, Austria-Hungary, 
the Ottoman Empire, and Bulgaria.

The war ended on November 11, 1918, when an armistice was signed. The Treaty 
of Versailles was signed on June 28, 1919, officially ending the war.

An estimated 9 million soldiers and 7 million civilians died as a result of 
the war, making it one of the deadliest conflicts in history.
"""


# =============================================================================
# INTERACTIVE DEMO
# =============================================================================

def run_demo():
    """Run the interactive demo."""
    pipeline = VDHFPipeline()
    
    # Ingest sample documents
    print("\nLoading sample documents...")
    pipeline.ingest(SAMPLE_DOCUMENTS, "sample_docs")
    
    # Test queries
    test_queries = [
        "When was Python released and who created it?",
        "What caused World War I?",
        "What are the key features of Python?"
    ]
    
    print("\n" + "=" * 60)
    print("RUNNING TEST QUERIES")
    print("=" * 60)
    
    for query in test_queries:
        pipeline.query(query)
        print("\n")
    
    # Interactive mode
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("Type your questions (or 'quit' to exit)")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            pipeline.query(user_input)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            break


if __name__ == "__main__":
    run_demo()
