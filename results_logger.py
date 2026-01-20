"""
VDHF Results Logger - Stores verification results in categorized output files.

Output files:
- output/passed_results.txt      - Claims that passed verification
- output/failed_results.txt      - Claims that failed (hallucinations)  
- output/refined_prompts.txt     - Prompts that were refined/regenerated
- output/combined_report.txt     - Complete combined report
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from demo import (
    VDHFPipeline, extract_claims, verify_claim, apply_firewall, 
    compute_similarity, DocumentChunk
)

# Create output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Output file paths
PASSED_FILE = os.path.join(OUTPUT_DIR, "passed_results.txt")
FAILED_FILE = os.path.join(OUTPUT_DIR, "failed_results.txt")
REFINED_FILE = os.path.join(OUTPUT_DIR, "refined_prompts.txt")
COMBINED_FILE = os.path.join(OUTPUT_DIR, "combined_report.txt")


class ResultsLogger:
    """Logs verification results to categorized files."""
    
    def __init__(self):
        self.passed_results = []
        self.failed_results = []
        self.refined_prompts = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def log_passed(self, query, claim, score, evidence):
        """Log a passed (supported) claim."""
        self.passed_results.append({
            'query': query,
            'claim': claim,
            'score': score,
            'evidence': evidence
        })
    
    def log_failed(self, query, claim, score, reason="Insufficient evidence"):
        """Log a failed (unsupported/hallucinated) claim."""
        self.failed_results.append({
            'query': query,
            'claim': claim,
            'score': score,
            'reason': reason
        })
    
    def log_refined(self, query, original_response, refined_response, 
                    original_ratio, new_ratio, removed_claims):
        """Log a refined/regenerated prompt."""
        self.refined_prompts.append({
            'query': query,
            'original_response': original_response,
            'refined_response': refined_response,
            'original_ratio': original_ratio,
            'new_ratio': new_ratio,
            'removed_claims': removed_claims
        })
    
    def save_all(self):
        """Save all results to their respective files."""
        self._save_passed()
        self._save_failed()
        self._save_refined()
        self._save_combined()
        print(f"\n[*] Results saved to {OUTPUT_DIR}/")
        
    def _save_passed(self):
        """Save passed results to file."""
        with open(PASSED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PASSED VERIFICATION RESULTS\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 70 + "\n\n")
            
            if not self.passed_results:
                f.write("No passed results recorded.\n")
            else:
                f.write(f"Total Passed Claims: {len(self.passed_results)}\n")
                f.write("-" * 70 + "\n\n")
                
                for i, result in enumerate(self.passed_results, 1):
                    f.write(f"[{i}] PASSED CLAIM\n")
                    f.write(f"    Query: {result['query']}\n")
                    f.write(f"    Claim: {result['claim']}\n")
                    f.write(f"    Score: {result['score']:.3f}\n")
                    f.write(f"    Evidence: {result['evidence'][:100]}...\n")
                    f.write("\n")
    
    def _save_failed(self):
        """Save failed results to file."""
        with open(FAILED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("FAILED VERIFICATION RESULTS (HALLUCINATIONS)\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 70 + "\n\n")
            
            if not self.failed_results:
                f.write("No failed results recorded.\n")
            else:
                f.write(f"Total Failed Claims: {len(self.failed_results)}\n")
                f.write("-" * 70 + "\n\n")
                
                for i, result in enumerate(self.failed_results, 1):
                    f.write(f"[{i}] FAILED CLAIM (HALLUCINATION)\n")
                    f.write(f"    Query: {result['query']}\n")
                    f.write(f"    Claim: {result['claim']}\n")
                    f.write(f"    Score: {result['score']:.3f}\n")
                    f.write(f"    Reason: {result['reason']}\n")
                    f.write("\n")
    
    def _save_refined(self):
        """Save refined prompts to file."""
        with open(REFINED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("REFINED PROMPTS (REGENERATED RESPONSES)\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 70 + "\n\n")
            
            if not self.refined_prompts:
                f.write("No refined prompts recorded.\n")
            else:
                f.write(f"Total Refinements: {len(self.refined_prompts)}\n")
                f.write("-" * 70 + "\n\n")
                
                for i, result in enumerate(self.refined_prompts, 1):
                    f.write(f"[{i}] REFINED PROMPT\n")
                    f.write(f"    Query: {result['query']}\n")
                    f.write(f"    Original Support Ratio: {result['original_ratio']:.1%}\n")
                    f.write(f"    New Support Ratio: {result['new_ratio']:.1%}\n")
                    f.write(f"\n    ORIGINAL RESPONSE:\n")
                    f.write(f"    {result['original_response'][:200]}...\n")
                    f.write(f"\n    REFINED RESPONSE:\n")
                    f.write(f"    {result['refined_response']}\n")
                    f.write(f"\n    REMOVED CLAIMS:\n")
                    for claim in result['removed_claims']:
                        f.write(f"      - {claim}\n")
                    f.write("\n")
    
    def _save_combined(self):
        """Save combined report to file."""
        with open(COMBINED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("VDHF COMBINED VERIFICATION REPORT\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 70 + "\n\n")
            
            # Summary
            f.write("SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"  Passed Claims:     {len(self.passed_results)}\n")
            f.write(f"  Failed Claims:     {len(self.failed_results)}\n")
            f.write(f"  Refined Prompts:   {len(self.refined_prompts)}\n")
            total = len(self.passed_results) + len(self.failed_results)
            if total > 0:
                pass_rate = len(self.passed_results) / total * 100
                f.write(f"  Overall Pass Rate: {pass_rate:.1f}%\n")
            f.write("\n")
            
            # Passed section
            f.write("=" * 70 + "\n")
            f.write("SECTION 1: PASSED CLAIMS\n")
            f.write("=" * 70 + "\n\n")
            if not self.passed_results:
                f.write("No passed claims.\n\n")
            else:
                for i, result in enumerate(self.passed_results, 1):
                    f.write(f"  [{i}] {result['claim'][:60]}...\n")
                    f.write(f"      Score: {result['score']:.3f} | Query: {result['query'][:40]}...\n\n")
            
            # Failed section
            f.write("=" * 70 + "\n")
            f.write("SECTION 2: FAILED CLAIMS (HALLUCINATIONS)\n")
            f.write("=" * 70 + "\n\n")
            if not self.failed_results:
                f.write("No failed claims.\n\n")
            else:
                for i, result in enumerate(self.failed_results, 1):
                    f.write(f"  [{i}] {result['claim'][:60]}...\n")
                    f.write(f"      Score: {result['score']:.3f} | Reason: {result['reason']}\n\n")
            
            # Refined section
            f.write("=" * 70 + "\n")
            f.write("SECTION 3: REFINED PROMPTS\n")
            f.write("=" * 70 + "\n\n")
            if not self.refined_prompts:
                f.write("No refined prompts.\n\n")
            else:
                for i, result in enumerate(self.refined_prompts, 1):
                    f.write(f"  [{i}] Query: {result['query']}\n")
                    f.write(f"      Ratio: {result['original_ratio']:.1%} -> {result['new_ratio']:.1%}\n")
                    f.write(f"      Removed {len(result['removed_claims'])} unsupported claims\n\n")


def run_verification_tests():
    """Run verification tests and log results."""
    
    print("=" * 70)
    print("VDHF Results Logging Test")
    print("=" * 70)
    
    # Initialize
    logger = ResultsLogger()
    pipeline = VDHFPipeline()
    
    # Load documents
    print("\n[*] Loading sample documents...")
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_docs")
    for filename in os.listdir(sample_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(sample_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            pipeline.ingest(content, filename)
    
    print(f"[*] Loaded {len(pipeline.store.chunks)} chunks")
    
    # =========================================================================
    # Test 1: Query with supported claims
    # =========================================================================
    print("\n[TEST 1] Testing supported claims...")
    
    query1 = "When was Python first released?"
    chunks = pipeline.store.search(query1, top_k=5)
    
    supported_claims = [
        "Python was first released in 1991.",
        "Python was conceived in the late 1980s.",
        "Guido van Rossum created Python.",
    ]
    
    for claim in supported_claims:
        best_score = 0
        best_evidence = ""
        for chunk, _ in chunks:
            score = compute_similarity(claim, chunk.content)
            if score > best_score:
                best_score = score
                best_evidence = chunk.content
        
        if best_score >= 0.5:
            logger.log_passed(query1, claim, best_score, best_evidence)
            print(f"  [PASS] {claim[:50]}... (score: {best_score:.3f})")
        else:
            logger.log_failed(query1, claim, best_score, "Score below threshold")
            print(f"  [FAIL] {claim[:50]}... (score: {best_score:.3f})")
    
    # =========================================================================
    # Test 2: Query with hallucinated claims
    # =========================================================================
    print("\n[TEST 2] Testing hallucinated claims...")
    
    query2 = "Tell me about Python versions."
    chunks = pipeline.store.search(query2, top_k=5)
    
    hallucinated_claims = [
        "Python 4.0 was released in 2020.",
        "Python was written in Java.",
        "Python is a compiled language.",
        "Python was created by Microsoft.",
    ]
    
    for claim in hallucinated_claims:
        best_score = 0
        best_evidence = ""
        for chunk, _ in chunks:
            score = compute_similarity(claim, chunk.content)
            if score > best_score:
                best_score = score
                best_evidence = chunk.content
        
        if best_score >= 0.5:
            logger.log_passed(query2, claim, best_score, best_evidence)
            print(f"  [PASS] {claim[:50]}... (score: {best_score:.3f})")
        else:
            logger.log_failed(query2, claim, best_score, "Hallucination - no supporting evidence")
            print(f"  [FAIL] {claim[:50]}... (score: {best_score:.3f})")
    
    # =========================================================================
    # Test 3: Prompt refinement scenario
    # =========================================================================
    print("\n[TEST 3] Testing prompt refinement...")
    
    query3 = "When was Python released and by whom?"
    
    # Simulate a response with mixed claims
    original_response = """
    Python was first released in 1991 by Guido van Rossum.
    Python 1.0 was released in 1994.
    Python 5.0 was released in 2023 with major improvements.
    Python is named after Monty Python's Flying Circus.
    """
    
    claims = extract_claims(original_response)
    chunks = pipeline.store.search(query3, top_k=5)
    
    verified_claims = []
    failed_claims = []
    
    for claim in claims:
        result = verify_claim(claim, chunks)
        if result.is_supported:
            verified_claims.append(claim.text)
            logger.log_passed(query3, claim.text, result.similarity_score, result.best_evidence)
            print(f"  [PASS] {claim.text[:50]}... (score: {result.similarity_score:.3f})")
        else:
            failed_claims.append(claim.text)
            logger.log_failed(query3, claim.text, result.similarity_score, "Unsupported claim")
            print(f"  [FAIL] {claim.text[:50]}... (score: {result.similarity_score:.3f})")
    
    # Calculate ratios
    total = len(verified_claims) + len(failed_claims)
    original_ratio = len(verified_claims) / total if total > 0 else 0
    
    # Simulate refinement
    refined_response = " ".join(verified_claims)
    new_ratio = 1.0  # After refinement, only verified claims remain
    
    if failed_claims:
        logger.log_refined(
            query=query3,
            original_response=original_response,
            refined_response=refined_response,
            original_ratio=original_ratio,
            new_ratio=new_ratio,
            removed_claims=failed_claims
        )
        print(f"\n  [REFINED] Removed {len(failed_claims)} unsupported claims")
        print(f"            Ratio: {original_ratio:.1%} -> {new_ratio:.1%}")
    
    # =========================================================================
    # Test 4: More refinement scenarios
    # =========================================================================
    print("\n[TEST 4] Additional refinement tests...")
    
    test_scenarios = [
        {
            'query': "What caused World War I?",
            'response': """
                WWI started in 1914 and ended in 1918.
                WWI was caused by the assassination of Archduke Franz Ferdinand.
                WWI was primarily fought in North America.
                Over 50 million soldiers died in WWI.
            """
        },
        {
            'query': "Tell me about artificial intelligence.",
            'response': """
                AI was invented by Alan Turing in 1950.
                The term AI was coined by John McCarthy in 1956.
                ChatGPT was released in 2025.
                Deep Blue defeated Garry Kasparov in chess in 1997.
            """
        }
    ]
    
    for scenario in test_scenarios:
        query = scenario['query']
        response = scenario['response']
        
        claims = extract_claims(response)
        chunks = pipeline.store.search(query, top_k=5)
        
        verified = []
        failed = []
        
        for claim in claims:
            result = verify_claim(claim, chunks)
            if result.is_supported:
                verified.append(claim.text)
                logger.log_passed(query, claim.text, result.similarity_score, result.best_evidence)
            else:
                failed.append(claim.text)
                logger.log_failed(query, claim.text, result.similarity_score, "Unsupported")
        
        total = len(verified) + len(failed)
        orig_ratio = len(verified) / total if total > 0 else 0
        
        if failed and orig_ratio < 0.8:
            logger.log_refined(
                query=query,
                original_response=response,
                refined_response=" ".join(verified),
                original_ratio=orig_ratio,
                new_ratio=1.0,
                removed_claims=failed
            )
            print(f"  [{query[:30]}...] Refined: {orig_ratio:.1%} -> 100%")
    
    # =========================================================================
    # Save all results
    # =========================================================================
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)
    
    logger.save_all()
    
    print(f"\nOutput files created:")
    print(f"  - {PASSED_FILE}")
    print(f"  - {FAILED_FILE}")
    print(f"  - {REFINED_FILE}")
    print(f"  - {COMBINED_FILE}")
    
    # Print summary
    print(f"\nSUMMARY:")
    print(f"  Passed Claims:   {len(logger.passed_results)}")
    print(f"  Failed Claims:   {len(logger.failed_results)}")
    print(f"  Refined Prompts: {len(logger.refined_prompts)}")


if __name__ == "__main__":
    run_verification_tests()
