"""
Test Suite for VDHF Pipeline

Tests for claim extraction, verification, and firewall logic.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from claim_extractor import ClaimExtractor, Claim
from verifier import ClaimVerifier, VerificationResult, SemanticSimilarityChecker
from firewall import FirewallDecisionEngine, FirewallDecision, HallucinationFirewall
from retriever import RetrievedEvidence
from ingestion import DocumentIngestion


class TestClaimExtractor:
    """Tests for claim extraction module."""
    
    def test_extract_simple_claims(self):
        """Test extraction of simple factual claims."""
        extractor = ClaimExtractor()
        
        response = "Python was released in 1991. It was created by Guido van Rossum."
        claims = extractor.extract_claims(response)
        
        assert len(claims) >= 2
        claim_texts = [c.text for c in claims]
        assert any("1991" in text for text in claim_texts)
        assert any("Guido" in text for text in claim_texts)
    
    def test_filter_opinions(self):
        """Test that opinions are filtered out."""
        extractor = ClaimExtractor()
        
        response = "I think Python is great. Python was released in 1991."
        claims = extractor.extract_claims(response)
        
        claim_texts = [c.text.lower() for c in claims]
        # Opinion should be filtered
        assert not any("i think" in text for text in claim_texts)
    
    def test_split_compound_sentences(self):
        """Test splitting of compound sentences."""
        extractor = ClaimExtractor()
        
        response = "Python was released in 1991 and created by Guido van Rossum."
        claims = extractor.extract_claims(response)
        
        # Should split into two claims
        assert len(claims) >= 2
    
    def test_empty_response(self):
        """Test handling of empty response."""
        extractor = ClaimExtractor()
        
        claims = extractor.extract_claims("")
        assert len(claims) == 0
    
    def test_question_filtering(self):
        """Test that questions are filtered out."""
        extractor = ClaimExtractor()
        
        response = "What is Python? Python was released in 1991."
        claims = extractor.extract_claims(response)
        
        claim_texts = [c.text for c in claims]
        assert not any("?" in text for text in claim_texts)


class TestSemanticSimilarity:
    """Tests for semantic similarity checking."""
    
    @pytest.fixture
    def similarity_checker(self):
        return SemanticSimilarityChecker()
    
    def test_high_similarity(self, similarity_checker):
        """Test high similarity for semantically similar texts."""
        claim = "Python was created by Guido van Rossum"
        evidence = "Guido van Rossum created Python programming language"
        
        score = similarity_checker.compute_similarity(claim, evidence)
        assert score > 0.5  # Should have reasonable similarity
    
    def test_low_similarity(self, similarity_checker):
        """Test low similarity for unrelated texts."""
        claim = "Python was released in 1991"
        evidence = "The weather is sunny today"
        
        score = similarity_checker.compute_similarity(claim, evidence)
        assert score < 0.5  # Should have low similarity


class TestFirewallDecisionEngine:
    """Tests for firewall decision logic."""
    
    def create_mock_result(self, is_supported: bool) -> VerificationResult:
        """Create a mock verification result."""
        claim = Claim(text="Test claim", claim_id=0)
        return VerificationResult(
            claim=claim,
            is_supported=is_supported,
            similarity_score=0.8 if is_supported else 0.4,
            entailment_label='ENTAILED' if is_supported else 'NEUTRAL',
            entailment_score=0.9 if is_supported else 0.5,
            best_evidence="Test evidence",
            evidence_source="test"
        )
    
    def test_pass_decision(self):
        """Test that high support ratio passes."""
        engine = FirewallDecisionEngine(threshold=0.8)
        
        # All supported
        results = [self.create_mock_result(True) for _ in range(5)]
        
        decision = engine.evaluate(results)
        
        assert decision.decision == FirewallDecision.PASS
        assert decision.support_ratio == 1.0
    
    def test_regenerate_decision(self):
        """Test that low support ratio triggers regeneration."""
        engine = FirewallDecisionEngine(threshold=0.8)
        
        # Only 50% supported
        results = [
            self.create_mock_result(True),
            self.create_mock_result(False)
        ]
        
        decision = engine.evaluate(results)
        
        assert decision.decision == FirewallDecision.REGENERATE
        assert decision.support_ratio == 0.5
    
    def test_threshold_boundary(self):
        """Test behavior at threshold boundary."""
        engine = FirewallDecisionEngine(threshold=0.8)
        
        # Exactly 80% supported (4 out of 5)
        results = [self.create_mock_result(True) for _ in range(4)]
        results.append(self.create_mock_result(False))
        
        decision = engine.evaluate(results)
        
        assert decision.decision == FirewallDecision.PASS
        assert decision.support_ratio == 0.8
    
    def test_empty_results(self):
        """Test handling of empty results."""
        engine = FirewallDecisionEngine(threshold=0.8)
        
        decision = engine.evaluate([])
        
        # Empty should pass (no claims = safe)
        assert decision.decision == FirewallDecision.PASS
        assert decision.support_ratio == 1.0


class TestDocumentIngestion:
    """Tests for document ingestion module."""
    
    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        ingestion = DocumentIngestion()
        
        dirty_text = "Hello   World\n\n\n\nTest"
        clean = ingestion.clean_text(dirty_text)
        
        assert "   " not in clean  # Multiple spaces removed
        assert "\n\n\n\n" not in clean  # Multiple newlines reduced
    
    def test_chunk_splitting(self):
        """Test chunk splitting."""
        ingestion = DocumentIngestion(chunk_size=100, chunk_overlap=20)
        
        text = "This is a test. " * 20
        chunks = ingestion.split_into_chunks(text, source="test")
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 150  # Allow some flexibility
    
    def test_ingest_text(self):
        """Test direct text ingestion."""
        ingestion = DocumentIngestion()
        
        text = "Python is a programming language. It was created in 1991."
        chunks = ingestion.ingest_text(text, source="test")
        
        assert len(chunks) >= 1
        assert all(isinstance(c.content, str) for c in chunks)


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_claim_to_verification_flow(self):
        """Test the flow from claim extraction to verification."""
        # Create test response
        response = "Python was released in 1991. Guido van Rossum created Python."
        
        # Extract claims
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(response)
        
        assert len(claims) >= 2
        
        # Create mock evidence
        evidence = [
            RetrievedEvidence(
                content="Python is a programming language first released in 1991 by Guido van Rossum.",
                similarity_score=0.9,
                metadata={"source": "wiki"},
                rank=1
            )
        ]
        
        # Verify claims
        verifier = ClaimVerifier()
        results = verifier.verify_all_claims(claims, evidence)
        
        assert len(results) == len(claims)
        
        # Check firewall
        engine = FirewallDecisionEngine(threshold=0.5)  # Lower threshold for test
        decision = engine.evaluate(results)
        
        assert decision.total_claims == len(claims)


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
