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

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


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
    
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_docs")
    
    if not os.path.exists(sample_dir):
        print(f"  [!] Sample docs directory not found: {sample_dir}")
        return 0
    
    doc_count = 0
    for filename in os.listdir(sample_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(sample_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            pipeline.ingest(content, filename)
            doc_count += 1
            print(f"  [OK] Loaded: {filename}")
    
    print(f"\n  [OK] Loaded {doc_count} documents, {len(pipeline.store.chunks)} chunks")
    return doc_count


def run_demo_mode(pipeline):
    """Run interactive demo mode."""
    print_section("Interactive Demo Mode")
    print("  Type your questions and press Enter.")
    print("  Type 'quit' or 'exit' to return to menu.\n")
    
    # We will append to these files
    passed_file = os.path.join(OUTPUT_DIR, "passed_results.txt")
    failed_file = os.path.join(OUTPUT_DIR, "failed_results.txt")
    refined_file = os.path.join(OUTPUT_DIR, "refined_prompts.txt")
    
    while True:
        try:
            user_input = input("  You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("  Exiting demo mode...")
                break
            
            # Process query
            result = pipeline.query(user_input)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Determine output file based on decision
            decision = result.get('decision', 'UNKNOWN')
            
            if decision == 'PASS':
                # Log to passed_results.txt
                with open(passed_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[{timestamp}] [INTERACTIVE] {user_input}\n")
                    f.write(f"Score: {result.get('support_ratio', 0):.3f}\n")
                    f.write(f"Response: {result.get('response', '')}\n")
                    f.write("-" * 40 + "\n")
                print(f"  [i] Saved to passed_results.txt")
                
            else:
                # Log to failed_results.txt
                with open(failed_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[{timestamp}] [INTERACTIVE] {user_input}\n")
                    f.write(f"Score: {result.get('support_ratio', 0):.3f} - Decision: {decision}\n")
                    # Log individual claim failures
                    match_results = result.get('results', [])
                    for r in match_results:
                        if not r.is_supported:
                            f.write(f"  [FAIL] {r.claim.text} (Score: {r.similarity_score:.3f})\n")
                    f.write("-" * 40 + "\n")
                print(f"  [i] Saved to failed_results.txt")
                
                # Also log to refined_prompts.txt if failed
                with open(refined_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[{timestamp}] [INTERACTIVE] {user_input}\n")
                print(f"  [i] Saved to refined_prompts.txt")

        except KeyboardInterrupt:
            print("\n  Exiting demo mode...")
            break


def run_comprehensive_test(pipeline, logger):
    """Run comprehensive tests across all topics."""
    from demo import extract_claims, verify_claim, compute_similarity
    
    print_section("Running Comprehensive Tests")
    
    # Test cases for all topics
    test_cases = [
        {
            'topic': 'Python',
            'query': 'When was Python released and who created it?',
            'true_claims': ["Python was first released in 1991.", "Guido van Rossum created Python."],
            'false_claims': ["Python was created by Microsoft.", "Python 4.0 was released in 2020."]
        },
        {
            'topic': 'World War I',
            'query': 'What caused World War I?',
            'true_claims': ["World War I lasted from 1914 to 1918."],
            'false_claims': ["World War I started in 1920.", "WWI lasted for 10 years."]
        },
        {
            'topic': 'Artificial Intelligence',
            'query': 'Tell me about AI history.',
            'true_claims': ["The term AI was coined by John McCarthy in 1956."],
            'false_claims': ["AI was invented by Steve Jobs.", "The first AI was created in 2010."]
        },
        {
            'topic': 'Solar System',
            'query': 'Tell me about planets.',
            'true_claims': ["The Solar System formed 4.6 billion years ago."],
            'false_claims': ["Mars has 10 moons.", "The Sun is a planet."]
        },
        {
            'topic': 'World War II',
            'query': 'When did WWII happen?',
            'true_claims': ["World War II lasted from 1939 to 1945."],
            'false_claims': ["WWII started in 1950.", "Germany won World War II."]
        },
        {
            'topic': 'Economics',
            'query': 'Explain economics.',
            'true_claims': ["The Great Depression began in 1929."],
            'false_claims': ["Inflation means prices are going down."]
        },
        {
            'topic': 'Internet',
            'query': 'How did the internet develop?',
            'true_claims': ["The first ARPANET message was sent in 1969."],
            'false_claims': ["The internet was invented by Bill Gates."]
        },
    ]
    
    passed = []
    failed = []
    refined = []
    
    for test in test_cases:
        topic = test['topic']
        query = test['query']
        
        print(f"\n  [{topic}]")
        
        chunks = pipeline.store.search(query, top_k=5)
        
        # Test true claims
        for claim in test['true_claims']:
            best_score = max([compute_similarity(claim, c.content) for c, _ in chunks], default=0)
            if best_score >= 0.5:
                passed.append({'topic': topic, 'claim': claim, 'score': best_score})
                print(f"    [PASS] {claim[:40]}... ({best_score:.3f})")
            else:
                failed.append({'topic': topic, 'claim': claim, 'score': best_score, 'reason': 'Below threshold'})
                print(f"    [FAIL] {claim[:40]}... ({best_score:.3f})")
        
        # Test false claims
        for claim in test['false_claims']:
            best_score = max([compute_similarity(claim, c.content) for c, _ in chunks], default=0)
            if best_score >= 0.5:
                passed.append({'topic': topic, 'claim': claim, 'score': best_score})
                print(f"    [!] FALSE POSITIVE: {claim[:40]}... ({best_score:.3f})")
            else:
                failed.append({'topic': topic, 'claim': claim, 'score': best_score, 'reason': 'Hallucination'})
                print(f"    [OK] REJECTED: {claim[:40]}... ({best_score:.3f})")
        
        # Simulate refinement
        mixed = test['true_claims'][:1] + test['false_claims'][:1]
        verified_count = sum(1 for c in mixed if max([compute_similarity(c, ch.content) for ch, _ in chunks], default=0) >= 0.5)
        if verified_count < len(mixed):
            refined.append({'topic': topic, 'query': query})
    
    return passed, failed, refined


def save_results(passed, failed, refined, timestamp):
    """Save results to output files."""
    print_section("Saving Results")
    
    # Passed results
    with open(os.path.join(OUTPUT_DIR, "passed_results.txt"), 'w', encoding='utf-8') as f:
        f.write(f"PASSED VERIFICATION RESULTS\nGenerated: {timestamp}\n{'='*60}\n\n")
        f.write(f"Total Passed: {len(passed)}\n\n")
        for i, r in enumerate(passed, 1):
            f.write(f"[{i}] [{r['topic']}] {r['claim']} (Score: {r['score']:.3f})\n")
    
    # Failed results
    with open(os.path.join(OUTPUT_DIR, "failed_results.txt"), 'w', encoding='utf-8') as f:
        f.write(f"FAILED VERIFICATION RESULTS\nGenerated: {timestamp}\n{'='*60}\n\n")
        f.write(f"Total Failed: {len(failed)}\n\n")
        for i, r in enumerate(failed, 1):
            f.write(f"[{i}] [{r['topic']}] {r['claim']} (Score: {r['score']:.3f}) - {r['reason']}\n")
    
    # Refined prompts
    with open(os.path.join(OUTPUT_DIR, "refined_prompts.txt"), 'w', encoding='utf-8') as f:
        f.write(f"REFINED PROMPTS\nGenerated: {timestamp}\n{'='*60}\n\n")
        f.write(f"Total Refined: {len(refined)}\n\n")
        for i, r in enumerate(refined, 1):
            f.write(f"[{i}] [{r['topic']}] {r['query']}\n")
    
    # Combined report
    with open(os.path.join(OUTPUT_DIR, "combined_report.txt"), 'w', encoding='utf-8') as f:
        total = len(passed) + len(failed)
        rate = len(passed) / total * 100 if total > 0 else 0
        
        f.write(f"VDHF COMPREHENSIVE REPORT\nGenerated: {timestamp}\n{'='*60}\n\n")
        f.write(f"SUMMARY\n{'-'*40}\n")
        f.write(f"  Total Claims:    {total}\n")
        f.write(f"  Passed:          {len(passed)}\n")
        f.write(f"  Failed:          {len(failed)}\n")
        f.write(f"  Refined:         {len(refined)}\n")
        f.write(f"  Pass Rate:       {rate:.1f}%\n\n")
        
        f.write(f"PASSED CLAIMS\n{'-'*40}\n")
        for r in passed:
            f.write(f"  [{r['topic']}] {r['claim'][:50]}...\n")
        
        f.write(f"\nFAILED CLAIMS\n{'-'*40}\n")
        for r in failed:
            f.write(f"  [{r['topic']}] {r['claim'][:50]}...\n")
    
    print(f"  [OK] passed_results.txt")
    print(f"  [OK] failed_results.txt")
    print(f"  [OK] refined_prompts.txt")
    print(f"  [OK] combined_report.txt")
    print(f"\n  [OK] All results saved to: {OUTPUT_DIR}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='VDHF - Hallucination Firewall')
    parser.add_argument('--demo', action='store_true', help='Run interactive demo only')
    parser.add_argument('--test', action='store_true', help='Run comprehensive tests only')
    parser.add_argument('--quick', action='store_true', help='Run quick verification test')
    args = parser.parse_args()
    
    print_header("VERIFICATION-DRIVEN HALLUCINATION FIREWALL (VDHF)")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Import demo module
    try:
        from demo import VDHFPipeline
    except ImportError as e:
        print(f"\n  [!] Import error: {e}")
        print("  [!] Make sure demo.py is in the same directory")
        return
    
    # Initialize pipeline
    print_section("Initializing Pipeline")
    pipeline = VDHFPipeline()
    
    # Load documents
    doc_count = load_documents(pipeline)
    if doc_count == 0:
        print("  [!] No documents loaded. Please check sample_docs folder.")
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Run based on mode
    if args.demo:
        run_demo_mode(pipeline)
    elif args.test or args.quick:
        passed, failed, refined = run_comprehensive_test(pipeline, None)
        save_results(passed, failed, refined, timestamp)
        
        # Print summary
        print_section("Test Summary")
        total = len(passed) + len(failed)
        rate = len(passed) / total * 100 if total > 0 else 0
        print(f"  Total Claims:    {total}")
        print(f"  Passed:          {len(passed)}")
        print(f"  Failed:          {len(failed)}")
        print(f"  Refined:         {len(refined)}")
        print(f"  Pass Rate:       {rate:.1f}%")
    else:
        # Full run - both demo and tests
        print("\n  [1/2] Running Tests...")
        passed, failed, refined = run_comprehensive_test(pipeline, None)
        save_results(passed, failed, refined, timestamp)
        
        # Print summary
        print_section("Test Summary")
        total = len(passed) + len(failed)
        rate = len(passed) / total * 100 if total > 0 else 0
        print(f"  Total Claims:    {total}")
        print(f"  Passed:          {len(passed)}")
        print(f"  Failed:          {len(failed)}")
        print(f"  Refined:         {len(refined)}")
        print(f"  Pass Rate:       {rate:.1f}%")
        
        print("\n  [2/2] Starting Interactive Demo...")
        print("  (Type 'quit' to exit)\n")
        run_demo_mode(pipeline)
    
    print_header("VDHF COMPLETED")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
