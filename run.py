"""
VDHF - Verification-Driven Hallucination Firewall
==================================================
Single entry point to run the complete project.

Usage:
    python run.py              # Run full demo and tests
    python run.py --demo       # Interactive demo only
    python run.py --test       # Run comprehensive tests only
    python run.py --quick      # Quick verification test
"""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_docs")


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title):
    """Print a section header."""
    print("\n" + "-" * 60)
    print(f" {title}")
    print("-" * 60)


def check_requirements():
    """Check if required packages are installed."""
    print_section("Checking Requirements")

    required = ['sentence_transformers', 'chromadb', 'torch', 'transformers', 'numpy']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [X] {package} - NOT FOUND")
            missing.append(package)

    if missing:
        print(f"\n  [!] Missing packages: {', '.join(missing)}")
        print("  [!] Run: pip install -r requirements.txt")
        return False

    print("\n  [OK] All requirements satisfied!")
    return True


def load_documents(pipeline):
    """Load all sample documents."""
    print_section("Loading Documents")

    if not os.path.exists(DATA_DIR):
        print(f"  [!] Sample docs directory not found: {DATA_DIR}")
        return 0

    doc_count = 0
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.txt'):
            filepath = os.path.join(DATA_DIR, filename)
            pipeline.ingest_file(filepath)
            doc_count += 1
            print(f"  [OK] Loaded: {filename}")

    print(f"\n  [OK] Loaded {doc_count} documents, {pipeline.document_count} chunks")
    return doc_count


def run_demo_mode(pipeline):
    """Run interactive demo mode."""
    from core.pipeline import interactive_mode
    interactive_mode(pipeline)


def run_quick_test(pipeline):
    """Run a quick verification test."""
    print_section("Running Quick Test")

    test_queries = [
        "When was Python released and who created it?",
        "What are the key features of Python?",
        "When did Python 3.0 come out?"
    ]

    for query in test_queries:
        print(f"\n  Query: {query}")
        result = pipeline.query(query, verbose=False)
        status = "VERIFIED" if result.is_verified else "NEEDS REVIEW"
        print(f"  Status: {status} | Support: {result.support_ratio:.1%} | Claims: {result.supported_claims}/{result.total_claims}")
        print(f"  Response: {result.final_response[:100]}...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='VDHF - Hallucination Firewall')
    parser.add_argument('--demo', action='store_true', help='Run interactive demo only')
    parser.add_argument('--test', action='store_true', help='Run comprehensive tests only')
    parser.add_argument('--quick', action='store_true', help='Run quick verification test')
    args = parser.parse_args()

    print_header("VERIFICATION-DRIVEN HALLUCINATION FIREWALL (VDHF)")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check requirements
    if not check_requirements():
        return

    # Import pipeline (after requirements check)
    from core.pipeline import VDHFPipeline

    # Initialize pipeline
    print_section("Initializing Pipeline")
    pipeline = VDHFPipeline()

    # Load documents
    doc_count = load_documents(pipeline)
    if doc_count == 0:
        print("  [!] No documents loaded. Please check data/sample_docs folder.")
        return

    # Run based on mode
    if args.demo:
        run_demo_mode(pipeline)
    elif args.test or args.quick:
        run_quick_test(pipeline)
    else:
        # Full run - both test and demo
        print("\n  [1/2] Running Quick Tests...")
        run_quick_test(pipeline)

        print("\n  [2/2] Starting Interactive Demo...")
        print("  (Type '/quit' to exit)\n")
        run_demo_mode(pipeline)

    print_header("VDHF COMPLETED")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
