"""
Test script to verify hallucination detection and prompt refinement.
This script creates scenarios that should trigger the firewall and test regeneration.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from demo import VDHFPipeline, extract_claims, verify_claim, apply_firewall, compute_similarity

def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def test_hallucination_detection():
    """Test with responses containing unsupported claims (hallucinations)."""
    
    print_header("HALLUCINATION DETECTION & REFINEMENT TEST")
    
    # Initialize pipeline
    pipeline = VDHFPipeline()
    
    # Load our sample documents
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_docs")
    
    print("\n[*] Loading sample documents...")
    for filename in os.listdir(sample_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(sample_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            pipeline.ingest(content, filename)
            print(f"    - Loaded: {filename}")
    
    print(f"\n[*] Total chunks in store: {len(pipeline.store.chunks)}")
    
    # =========================================================================
    # TEST 1: Query with potential for hallucination
    # =========================================================================
    print_header("TEST 1: Query about Python with potential hallucination")
    
    # This query might generate hallucinated details not in our documents
    query1 = "Tell me about Python's license and its commercial use policy."
    print(f"\nQuery: {query1}")
    print("-" * 70)
    
    result1 = pipeline.query(query1)
    
    # =========================================================================
    # TEST 2: Query mixing topics (could cause hallucinations)
    # =========================================================================
    print_header("TEST 2: Query mixing topics - potential for confusion")
    
    query2 = "Who invented Python and what years was World War I fought?"
    print(f"\nQuery: {query2}")
    print("-" * 70)
    
    result2 = pipeline.query(query2)
    
    # =========================================================================
    # TEST 3: Manually test claim verification with hallucinated claims
    # =========================================================================
    print_header("TEST 3: Manual Hallucination Detection")
    
    # Create a mix of true and false claims
    test_claims = [
        "Python was created by Guido van Rossum.",  # TRUE - in documents
        "Python was first released in 1991.",        # TRUE - in documents
        "Python 4.0 was released in 2020.",           # FALSE - hallucinated
        "Python is used for web development.",        # TRUE - in documents
        "Python was named after a snake.",            # FALSE - actual: Monty Python
        "Java is faster than Python.",                # FALSE - not in documents
    ]
    
    print("\nTesting individual claims against document store:")
    print("-" * 70)
    
    # Search for evidence
    chunks = pipeline.store.search("Python programming language features history", top_k=5)
    
    for claim_text in test_claims:
        # Compute similarity against all evidence
        best_score = 0
        best_evidence = ""
        
        for chunk, _ in chunks:
            score = compute_similarity(claim_text, chunk.content)
            if score > best_score:
                best_score = score
                best_evidence = chunk.content[:80] + "..."
        
        is_supported = best_score >= 0.5
        status = "[SUPPORTED]" if is_supported else "[UNSUPPORTED - HALLUCINATION]"
        
        print(f"\n  Claim: \"{claim_text}\"")
        print(f"  Score: {best_score:.3f}")
        print(f"  Status: {status}")
        if not is_supported:
            print(f"  -> This claim would trigger firewall warning!")
    
    # =========================================================================
    # TEST 4: Simulate regeneration scenario
    # =========================================================================
    print_header("TEST 4: Simulating Regeneration Flow")
    
    # Create a response with mixed claims
    hallucinated_response = """
    Python was created by Guido van Rossum in the late 1980s. 
    Python 1.0 was released in 1994. 
    The language was named after Monty Python's Flying Circus.
    Python 5.0 introduced major performance improvements in 2023.
    """
    
    print(f"\nOriginal Response (with hallucinations):")
    print(f'"{hallucinated_response.strip()}"')
    print("-" * 70)
    
    # Extract and verify claims
    claims = extract_claims(hallucinated_response)
    print(f"\nExtracted {len(claims)} claims:")
    
    results = []
    for claim in claims:
        result = verify_claim(claim, chunks)
        results.append(result)
        status = "[OK]" if result.is_supported else "[FAIL]"
        print(f"  {status} (score: {result.similarity_score:.3f}) - {claim.text[:60]}...")
    
    # Apply firewall
    firewall_result = apply_firewall(results)
    decision = firewall_result['decision']
    ratio = firewall_result['support_ratio']
    supported = firewall_result['supported']
    total = firewall_result['total_claims']
    
    print(f"\n[FIREWALL DECISION]")
    print(f"  Support Ratio: {ratio:.1%}")
    print(f"  Supported Claims: {supported}/{total}")
    print(f"  Decision: {decision}")
    
    if decision != "PASS":
        print(f"\n[REGENERATION TRIGGERED]")
        print(f"  Reason: Support ratio {ratio:.1%} is below threshold (80%)")
        print(f"  Action: System would regenerate response using only verified evidence")
        print(f"  Unsupported claims would be excluded from the refined response")
        
        # Show what a refined response would look like
        print(f"\n[REFINED RESPONSE - Using only verified claims]:")
        verified_claims = [r.claim.text for r in results if r.is_supported]
        print("  " + " ".join(verified_claims[:3]))  # Show first 3 verified claims
    
    # =========================================================================
    # TEST 5: Topic with no relevant documents
    # =========================================================================
    print_header("TEST 5: Query with no relevant documents (out of scope)")
    
    query5 = "What is the capital of France and what is the population?"
    print(f"\nQuery: {query5}")
    print("-" * 70)
    
    result5 = pipeline.query(query5)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("TEST SUMMARY")
    print("""
The hallucination firewall validates claims by:

1. CLAIM EXTRACTION: Breaking response into atomic factual statements
2. EVIDENCE RETRIEVAL: Finding relevant document chunks
3. SIMILARITY SCORING: Computing semantic similarity between claims and evidence
4. THRESHOLD CHECK: Claims below 0.5 similarity are marked as unsupported
5. FIREWALL DECISION: If support ratio < 80%, regeneration is triggered
6. PROMPT REFINEMENT: System regenerates using only verified evidence

Key behaviors demonstrated:
- TRUE claims (found in documents) -> SUPPORTED -> pass through
- FALSE claims (hallucinated) -> UNSUPPORTED -> filtered out
- Mixed responses -> Partial support -> May trigger regeneration
- Out-of-scope queries -> Low evidence -> Limited/no response
    """)

def interactive_session():
    """Run an interactive session after tests."""
    print("\n" + "=" * 70)
    print("INTERACTIVE MODE")
    print("=" * 70)
    
    response = input("Do you want to run custom queries? (y/n): ").strip().lower()
    if response != 'y':
        return

    # Use the pipeline from demo but we need to re-init properly or pass it. 
    # For simplicity, let's just use the demo's interactive runner or simple loop
    from demo import run_demo
    # We can just call run_demo() which re-initializes or we can build a simple loop here
    # to avoid reloading docs if passed. But demo logic is self-contained.
    
    # Let's import our new clean runner
    try:
        from user_query import run_interactive_session
        run_interactive_session()
    except ImportError:
        print("Could not import user_query.py, falling back to simple loop")
        # Fallback simple loop if needed
        pass

if __name__ == "__main__":
    test_hallucination_detection()
    interactive_session()
