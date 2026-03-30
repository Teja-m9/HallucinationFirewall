"""
VDHF Results Logger - Stores verification results in categorized output files.

Output files:
- output/passed_results.txt      - Claims that passed verification
- output/failed_results.txt      - Claims that failed (hallucinations)
- output/refined_prompts.txt     - Prompts that were refined/regenerated
- output/combined_report.txt     - Complete combined report
"""

import os
from datetime import datetime

# Output directory (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
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
