"""
Comprehensive VDHF Test - Tests all document topics with success and failure cases.

Covers all 12 sample documents:
- Python, World War I, Artificial Intelligence, Solar System, Human Body
- Ancient Egypt, Climate Change, World War II, Economics, Renaissance
- Quantum Physics, Music History, Internet Technology
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from demo import (
    VDHFPipeline, extract_claims, verify_claim, apply_firewall, 
    compute_similarity
)

# Create output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Output file paths
PASSED_FILE = os.path.join(OUTPUT_DIR, "passed_results.txt")
FAILED_FILE = os.path.join(OUTPUT_DIR, "failed_results.txt")
REFINED_FILE = os.path.join(OUTPUT_DIR, "refined_prompts.txt")
COMBINED_FILE = os.path.join(OUTPUT_DIR, "combined_report.txt")


class ComprehensiveLogger:
    """Logs comprehensive test results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.refined = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def add_passed(self, topic, query, claim, score, evidence):
        self.passed.append({
            'topic': topic, 'query': query, 'claim': claim, 
            'score': score, 'evidence': evidence[:150]
        })
    
    def add_failed(self, topic, query, claim, score, reason):
        self.failed.append({
            'topic': topic, 'query': query, 'claim': claim,
            'score': score, 'reason': reason
        })
    
    def add_refined(self, topic, query, original, refined, orig_ratio, new_ratio, removed):
        self.refined.append({
            'topic': topic, 'query': query, 'original': original,
            'refined': refined, 'orig_ratio': orig_ratio,
            'new_ratio': new_ratio, 'removed': removed
        })
    
    def save_all(self):
        # Save passed results
        with open(PASSED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PASSED VERIFICATION RESULTS\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Passed Claims: {len(self.passed)}\n")
            f.write("-" * 80 + "\n\n")
            
            current_topic = None
            for i, r in enumerate(self.passed, 1):
                if r['topic'] != current_topic:
                    current_topic = r['topic']
                    f.write(f"\n### {current_topic.upper()} ###\n\n")
                f.write(f"[{i}] PASSED\n")
                f.write(f"    Query: {r['query']}\n")
                f.write(f"    Claim: {r['claim']}\n")
                f.write(f"    Score: {r['score']:.3f}\n")
                f.write(f"    Evidence: {r['evidence']}...\n\n")
        
        # Save failed results
        with open(FAILED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("FAILED VERIFICATION RESULTS (HALLUCINATIONS)\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Failed Claims: {len(self.failed)}\n")
            f.write("-" * 80 + "\n\n")
            
            current_topic = None
            for i, r in enumerate(self.failed, 1):
                if r['topic'] != current_topic:
                    current_topic = r['topic']
                    f.write(f"\n### {current_topic.upper()} ###\n\n")
                f.write(f"[{i}] FAILED - HALLUCINATION\n")
                f.write(f"    Query: {r['query']}\n")
                f.write(f"    Claim: {r['claim']}\n")
                f.write(f"    Score: {r['score']:.3f}\n")
                f.write(f"    Reason: {r['reason']}\n\n")
        
        # Save refined prompts
        with open(REFINED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REFINED PROMPTS (REGENERATED RESPONSES)\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Refinements: {len(self.refined)}\n")
            f.write("-" * 80 + "\n\n")
            
            for i, r in enumerate(self.refined, 1):
                f.write(f"[{i}] REFINED - {r['topic'].upper()}\n")
                f.write(f"    Query: {r['query']}\n")
                f.write(f"    Support Ratio: {r['orig_ratio']:.1%} -> {r['new_ratio']:.1%}\n\n")
                f.write(f"    ORIGINAL:\n    {r['original'][:200]}...\n\n")
                f.write(f"    REFINED:\n    {r['refined']}\n\n")
                f.write(f"    REMOVED CLAIMS:\n")
                for c in r['removed']:
                    f.write(f"      - {c}\n")
                f.write("\n" + "-" * 80 + "\n\n")
        
        # Save combined report
        with open(COMBINED_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("VDHF COMPREHENSIVE VERIFICATION REPORT\n")
            f.write(f"Generated: {self.timestamp}\n")
            f.write("=" * 80 + "\n\n")
            
            total = len(self.passed) + len(self.failed)
            pass_rate = len(self.passed) / total * 100 if total > 0 else 0
            
            f.write("SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"  Total Claims Tested:  {total}\n")
            f.write(f"  Passed Claims:        {len(self.passed)}\n")
            f.write(f"  Failed Claims:        {len(self.failed)}\n")
            f.write(f"  Refined Prompts:      {len(self.refined)}\n")
            f.write(f"  Overall Pass Rate:    {pass_rate:.1f}%\n\n")
            
            # Topics breakdown
            topics = set([r['topic'] for r in self.passed + self.failed])
            f.write("BY TOPIC:\n")
            for topic in sorted(topics):
                passed = len([r for r in self.passed if r['topic'] == topic])
                failed = len([r for r in self.failed if r['topic'] == topic])
                total_t = passed + failed
                rate = passed / total_t * 100 if total_t > 0 else 0
                f.write(f"  {topic:30} | Pass: {passed:2} | Fail: {failed:2} | Rate: {rate:5.1f}%\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("SECTION 1: PASSED CLAIMS (Summary)\n")
            f.write("=" * 80 + "\n\n")
            for r in self.passed[:20]:  # Show first 20
                f.write(f"  [{r['topic']}] {r['claim'][:50]}... (Score: {r['score']:.3f})\n")
            if len(self.passed) > 20:
                f.write(f"  ... and {len(self.passed) - 20} more\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("SECTION 2: FAILED CLAIMS (Summary)\n")
            f.write("=" * 80 + "\n\n")
            for r in self.failed[:20]:
                f.write(f"  [{r['topic']}] {r['claim'][:50]}... (Score: {r['score']:.3f})\n")
            if len(self.failed) > 20:
                f.write(f"  ... and {len(self.failed) - 20} more\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("SECTION 3: REFINED PROMPTS (Summary)\n")
            f.write("=" * 80 + "\n\n")
            for r in self.refined:
                f.write(f"  [{r['topic']}] {r['query'][:40]}... ({r['orig_ratio']:.0%} -> {r['new_ratio']:.0%})\n")


# Define comprehensive test cases for all topics
TEST_CASES = [
    # =========================================================================
    # PYTHON
    # =========================================================================
    {
        'topic': 'Python',
        'query': 'When was Python released and who created it?',
        'true_claims': [
            "Python was first released in 1991.",
            "Guido van Rossum created Python.",
            "Python was conceived in the late 1980s.",
        ],
        'false_claims': [
            "Python was created by Microsoft in 2000.",
            "Python 4.0 was released in 2020.",
            "Python is a compiled language like Java.",
        ]
    },
    
    # =========================================================================
    # WORLD WAR I
    # =========================================================================
    {
        'topic': 'World War I',
        'query': 'What caused World War I and when did it happen?',
        'true_claims': [
            "World War I lasted from 1914 to 1918.",
            "The assassination of Archduke Franz Ferdinand triggered WWI.",
            "Militarism and alliances contributed to WWI.",
        ],
        'false_claims': [
            "World War I started in 1920.",
            "WWI was fought between USA and Japan.",
            "WWI lasted for 10 years.",
        ]
    },
    
    # =========================================================================
    # ARTIFICIAL INTELLIGENCE
    # =========================================================================
    {
        'topic': 'Artificial Intelligence',
        'query': 'Tell me about the history of AI.',
        'true_claims': [
            "The term AI was coined by John McCarthy in 1956.",
            "Deep Blue defeated Garry Kasparov in 1997.",
            "ChatGPT was released by OpenAI in 2022.",
        ],
        'false_claims': [
            "AI was invented by Steve Jobs in 1990.",
            "The first AI was created in 2010.",
            "Machine learning and AI are completely different fields.",
        ]
    },
    
    # =========================================================================
    # SOLAR SYSTEM
    # =========================================================================
    {
        'topic': 'Solar System',
        'query': 'Tell me about the planets in our solar system.',
        'true_claims': [
            "Jupiter is the largest planet in our solar system.",
            "The Solar System formed 4.6 billion years ago.",
            "Pluto was reclassified as a dwarf planet in 2006.",
        ],
        'false_claims': [
            "The Sun is a planet.",
            "Mars has 10 moons.",
            "Saturn is the largest planet.",
        ]
    },
    
    # =========================================================================
    # HUMAN BODY
    # =========================================================================
    {
        'topic': 'Human Body',
        'query': 'How does the human body work?',
        'true_claims': [
            "The human body has approximately 206 bones.",
            "The brain contains approximately 86 billion neurons.",
            "The heart pumps about 2000 gallons of blood daily.",
        ],
        'false_claims': [
            "Humans have 300 bones as adults.",
            "The liver is located in the head.",
            "Blood is blue inside the body.",
        ]
    },
    
    # =========================================================================
    # ANCIENT EGYPT
    # =========================================================================
    {
        'topic': 'Ancient Egypt',
        'query': 'Tell me about Ancient Egypt and the pyramids.',
        'true_claims': [
            "The Great Pyramid was built for Pharaoh Khufu.",
            "Egyptian civilization began around 3100 BCE.",
            "Tutankhamun's tomb was discovered in 1922.",
        ],
        'false_claims': [
            "The pyramids were built by aliens.",
            "Cleopatra lived in 500 AD.",
            "The Sphinx was built in medieval times.",
        ]
    },
    
    # =========================================================================
    # CLIMATE CHANGE
    # =========================================================================
    {
        'topic': 'Climate Change',
        'query': 'What is causing climate change?',
        'true_claims': [
            "CO2 is a major greenhouse gas.",
            "The Paris Agreement was adopted in 2015.",
            "Global temperature has risen by about 1.1°C.",
        ],
        'false_claims': [
            "Climate change is caused only by volcanoes.",
            "The Paris Agreement was signed in 2000.",
            "CO2 levels have decreased since 1900.",
        ]
    },
    
    # =========================================================================
    # WORLD WAR II
    # =========================================================================
    {
        'topic': 'World War II',
        'query': 'When did World War II happen and what were key events?',
        'true_claims': [
            "World War II lasted from 1939 to 1945.",
            "D-Day occurred on June 6, 1944.",
            "The atomic bomb was dropped on Hiroshima in August 1945.",
        ],
        'false_claims': [
            "WWII started in 1950.",
            "Germany won World War II.",
            "The United Nations was created before WWII.",
        ]
    },
    
    # =========================================================================
    # ECONOMICS
    # =========================================================================
    {
        'topic': 'Economics',
        'query': 'Explain basic economic concepts.',
        'true_claims': [
            "GDP measures the total value of goods and services.",
            "The Federal Reserve was established in 1913.",
            "The Great Depression began in 1929.",
        ],
        'false_claims': [
            "Inflation means prices are going down.",
            "The Federal Reserve was created in 1800.",
            "GDP stands for Gross Domestic Profit.",
        ]
    },
    
    # =========================================================================
    # RENAISSANCE
    # =========================================================================
    {
        'topic': 'Renaissance',
        'query': 'Tell me about the Renaissance period.',
        'true_claims': [
            "Leonardo da Vinci created the Mona Lisa.",
            "The Renaissance began in Florence, Italy.",
            "Gutenberg invented the printing press around 1440.",
        ],
        'false_claims': [
            "The Renaissance occurred in the 1900s.",
            "Michelangelo was a French painter.",
            "The printing press was invented in China in 1800.",
        ]
    },
    
    # =========================================================================
    # QUANTUM PHYSICS
    # =========================================================================
    {
        'topic': 'Quantum Physics',
        'query': 'Explain quantum physics concepts.',
        'true_claims': [
            "Heisenberg proposed the Uncertainty Principle in 1927.",
            "Max Planck is considered the father of quantum theory.",
            "Quantum entanglement allows instant effects at distance.",
        ],
        'false_claims': [
            "Quantum physics was invented by Einstein alone.",
            "Schrödinger's cat is a real experiment with cats.",
            "Quantum computers use regular bits.",
        ]
    },
    
    # =========================================================================
    # MUSIC HISTORY
    # =========================================================================
    {
        'topic': 'Music History',
        'query': 'Tell me about the history of Western music.',
        'true_claims': [
            "Bach lived from 1685 to 1750.",
            "The Beatles formed in Liverpool in 1960.",
            "Beethoven bridged Classical and Romantic periods.",
        ],
        'false_claims': [
            "Mozart was born in France.",
            "The Beatles were from New York.",
            "Jazz originated in Europe in 1800.",
        ]
    },
    
    # =========================================================================
    # INTERNET
    # =========================================================================
    {
        'topic': 'Internet Technology',
        'query': 'How did the internet develop?',
        'true_claims': [
            "Tim Berners-Lee invented the World Wide Web in 1989.",
            "The first ARPANET message was sent in 1969.",
            "Google was founded in 1998.",
        ],
        'false_claims': [
            "The internet was invented by Bill Gates.",
            "Facebook was created in 1990.",
            "The World Wide Web and Internet are the same thing.",
        ]
    },
]


def run_comprehensive_test():
    """Run comprehensive tests across all topics."""
    
    print("=" * 80)
    print("COMPREHENSIVE VDHF VERIFICATION TEST")
    print("=" * 80)
    
    # Initialize
    logger = ComprehensiveLogger()
    pipeline = VDHFPipeline()
    
    # Load all documents
    print("\n[*] Loading sample documents...")
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_docs")
    doc_count = 0
    for filename in os.listdir(sample_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(sample_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            pipeline.ingest(content, filename)
            doc_count += 1
    
    print(f"[*] Loaded {doc_count} documents, {len(pipeline.store.chunks)} chunks")
    
    # Run tests for each topic
    print("\n" + "=" * 80)
    print("RUNNING TESTS")
    print("=" * 80)
    
    for test_case in TEST_CASES:
        topic = test_case['topic']
        query = test_case['query']
        true_claims = test_case['true_claims']
        false_claims = test_case['false_claims']
        
        print(f"\n[{topic}]")
        print(f"  Query: {query[:50]}...")
        
        # Get evidence
        chunks = pipeline.store.search(query, top_k=7)
        
        # Test TRUE claims
        for claim in true_claims:
            best_score = 0
            best_evidence = ""
            for chunk, _ in chunks:
                score = compute_similarity(claim, chunk.content)
                if score > best_score:
                    best_score = score
                    best_evidence = chunk.content
            
            if best_score >= 0.5:
                logger.add_passed(topic, query, claim, best_score, best_evidence)
                print(f"    [PASS] {claim[:40]}... ({best_score:.3f})")
            else:
                logger.add_failed(topic, query, claim, best_score, "Score below threshold")
                print(f"    [FAIL] {claim[:40]}... ({best_score:.3f})")
        
        # Test FALSE claims
        for claim in false_claims:
            best_score = 0
            best_evidence = ""
            for chunk, _ in chunks:
                score = compute_similarity(claim, chunk.content)
                if score > best_score:
                    best_score = score
                    best_evidence = chunk.content
            
            if best_score >= 0.5:
                # False positive - claim passed but shouldn't have
                logger.add_passed(topic, query, claim, best_score, best_evidence)
                print(f"    [PASS*] {claim[:40]}... ({best_score:.3f}) - FALSE POSITIVE!")
            else:
                # Correctly identified as hallucination
                logger.add_failed(topic, query, claim, best_score, "Hallucination detected")
                print(f"    [FAIL] {claim[:40]}... ({best_score:.3f}) - Correctly rejected")
        
        # Simulate mixed response for refinement
        mixed_response = " ".join(true_claims[:1] + false_claims[:2])
        claims = extract_claims(mixed_response)
        
        verified = []
        failed_list = []
        for claim in claims:
            result = verify_claim(claim, chunks)
            if result.is_supported:
                verified.append(claim.text)
            else:
                failed_list.append(claim.text)
        
        total = len(verified) + len(failed_list)
        orig_ratio = len(verified) / total if total > 0 else 0
        
        if failed_list and orig_ratio < 0.8:
            logger.add_refined(
                topic=topic,
                query=query,
                original=mixed_response,
                refined=" ".join(verified) if verified else "[No verified claims]",
                orig_ratio=orig_ratio,
                new_ratio=1.0 if verified else 0.0,
                removed=failed_list
            )
    
    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    logger.save_all()
    
    # Print summary
    total = len(logger.passed) + len(logger.failed)
    pass_rate = len(logger.passed) / total * 100 if total > 0 else 0
    
    print(f"\n[*] Results saved to {OUTPUT_DIR}/")
    print(f"\nFINAL SUMMARY:")
    print(f"  Topics Tested:    {len(TEST_CASES)}")
    print(f"  Total Claims:     {total}")
    print(f"  Passed:           {len(logger.passed)}")
    print(f"  Failed:           {len(logger.failed)}")
    print(f"  Refined Prompts:  {len(logger.refined)}")
    print(f"  Pass Rate:        {pass_rate:.1f}%")
    
    print(f"\nOutput files:")
    print(f"  - {PASSED_FILE}")
    print(f"  - {FAILED_FILE}")
    print(f"  - {REFINED_FILE}")
    print(f"  - {COMBINED_FILE}")


if __name__ == "__main__":
    run_comprehensive_test()
