"""
Firewall Decision Engine for VDHF

Controls output delivery based on verification score and threshold.
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from config import FIREWALL_THRESHOLD
from verifier import VerificationResult, ClaimVerifier
from claim_extractor import Claim


class FirewallDecision(Enum):
    """Possible firewall decisions."""
    PASS = "PASS"  # Response is safe to deliver
    REGENERATE = "REGENERATE"  # Trigger prompt refinement


@dataclass
class FirewallResult:
    """Result of firewall evaluation."""
    decision: FirewallDecision
    support_ratio: float
    threshold: float
    total_claims: int
    supported_claims: int
    unsupported_claims: int
    verification_results: List[VerificationResult]
    
    @property
    def is_safe(self) -> bool:
        return self.decision == FirewallDecision.PASS
    
    def __str__(self) -> str:
        status = "✓ PASSED" if self.is_safe else "✗ BLOCKED"
        return (
            f"Firewall Decision: {status}\n"
            f"  Support Ratio: {self.support_ratio:.2%} (threshold: {self.threshold:.2%})\n"
            f"  Claims: {self.supported_claims}/{self.total_claims} supported"
        )


class FirewallScoringModule:
    """
    Firewall Scoring Module
    
    Computes global verification score for the response.
    
    Metric:
    SupportRatio = (Number of SUPPORTED claims) / (Total number of claims)
    """
    
    def __init__(self, threshold: float = FIREWALL_THRESHOLD):
        self.threshold = threshold
    
    def compute_support_ratio(
        self,
        verification_results: List[VerificationResult]
    ) -> float:
        """
        Compute the support ratio for verification results.
        
        Args:
            verification_results: List of VerificationResult objects
            
        Returns:
            Support ratio (0.0 to 1.0)
        """
        if not verification_results:
            return 1.0  # No claims = safe
        
        supported = sum(1 for r in verification_results if r.is_supported)
        total = len(verification_results)
        
        return supported / total
    
    def get_detailed_scores(
        self,
        verification_results: List[VerificationResult]
    ) -> Dict[str, Any]:
        """
        Get detailed scoring breakdown.
        
        Args:
            verification_results: List of VerificationResult objects
            
        Returns:
            Dictionary with detailed scores
        """
        total = len(verification_results)
        supported = sum(1 for r in verification_results if r.is_supported)
        
        similarity_scores = [r.similarity_score for r in verification_results]
        entailment_scores = [r.entailment_score for r in verification_results]
        
        return {
            'support_ratio': supported / total if total > 0 else 1.0,
            'total_claims': total,
            'supported_claims': supported,
            'unsupported_claims': total - supported,
            'average_similarity': sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0,
            'average_entailment': sum(entailment_scores) / len(entailment_scores) if entailment_scores else 0.0,
            'min_similarity': min(similarity_scores) if similarity_scores else 0.0,
            'max_similarity': max(similarity_scores) if similarity_scores else 0.0,
        }


class FirewallDecisionEngine:
    """
    Firewall Decision Engine
    
    Purpose:
    Control output delivery based on verification score.
    
    Decision Logic:
    If SupportRatio >= tau:
        Allow the response to pass to the user
    Else:
        Trigger prompt refinement and regeneration
    """
    
    def __init__(self, threshold: float = FIREWALL_THRESHOLD):
        self.threshold = threshold
        self.scoring_module = FirewallScoringModule(threshold)
    
    def evaluate(
        self,
        verification_results: List[VerificationResult]
    ) -> FirewallResult:
        """
        Evaluate whether response should pass the firewall.
        
        Args:
            verification_results: List of VerificationResult objects
            
        Returns:
            FirewallResult object with decision
        """
        # Compute support ratio
        support_ratio = self.scoring_module.compute_support_ratio(verification_results)
        
        # Make decision
        if support_ratio >= self.threshold:
            decision = FirewallDecision.PASS
        else:
            decision = FirewallDecision.REGENERATE
        
        # Count claims
        total = len(verification_results)
        supported = sum(1 for r in verification_results if r.is_supported)
        
        return FirewallResult(
            decision=decision,
            support_ratio=support_ratio,
            threshold=self.threshold,
            total_claims=total,
            supported_claims=supported,
            unsupported_claims=total - supported,
            verification_results=verification_results
        )
    
    def get_unsupported_claims(
        self,
        firewall_result: FirewallResult
    ) -> List[Claim]:
        """
        Get list of unsupported claims for prompt refinement.
        
        Args:
            firewall_result: FirewallResult object
            
        Returns:
            List of unsupported Claim objects
        """
        unsupported = []
        for result in firewall_result.verification_results:
            if not result.is_supported:
                unsupported.append(result.claim)
        return unsupported
    
    def get_supported_claims(
        self,
        firewall_result: FirewallResult
    ) -> List[Claim]:
        """
        Get list of supported claims.
        
        Args:
            firewall_result: FirewallResult object
            
        Returns:
            List of supported Claim objects
        """
        supported = []
        for result in firewall_result.verification_results:
            if result.is_supported:
                supported.append(result.claim)
        return supported
    
    def get_verified_evidence(
        self,
        firewall_result: FirewallResult
    ) -> List[str]:
        """
        Get evidence that supports verified claims.
        
        Args:
            firewall_result: FirewallResult object
            
        Returns:
            List of evidence strings
        """
        evidence = set()
        for result in firewall_result.verification_results:
            if result.is_supported and result.best_evidence:
                evidence.add(result.best_evidence)
        return list(evidence)


class HallucinationFirewall:
    """
    Complete Hallucination Firewall
    
    Combines verification and decision-making into a single interface.
    """
    
    def __init__(
        self,
        similarity_threshold: float = None,
        firewall_threshold: float = FIREWALL_THRESHOLD
    ):
        from config import SIMILARITY_THRESHOLD
        self.similarity_threshold = similarity_threshold or SIMILARITY_THRESHOLD
        self.firewall_threshold = firewall_threshold
        
        self.verifier = ClaimVerifier(self.similarity_threshold)
        self.decision_engine = FirewallDecisionEngine(firewall_threshold)
    
    def check_response(
        self,
        claims: List[Claim],
        evidence_list: List
    ) -> FirewallResult:
        """
        Check a response through the firewall.
        
        Args:
            claims: Extracted claims from response
            evidence_list: Retrieved evidence
            
        Returns:
            FirewallResult with decision
        """
        # Verify all claims
        verification_results = self.verifier.verify_all_claims(claims, evidence_list)
        
        # Evaluate through firewall
        result = self.decision_engine.evaluate(verification_results)
        
        return result
    
    def get_refinement_info(
        self,
        firewall_result: FirewallResult
    ) -> Dict[str, Any]:
        """
        Get information needed for prompt refinement.
        
        Args:
            firewall_result: FirewallResult from check_response
            
        Returns:
            Dictionary with refinement information
        """
        return {
            'unsupported_claims': self.decision_engine.get_unsupported_claims(firewall_result),
            'supported_claims': self.decision_engine.get_supported_claims(firewall_result),
            'verified_evidence': self.decision_engine.get_verified_evidence(firewall_result),
            'support_ratio': firewall_result.support_ratio,
            'needs_regeneration': not firewall_result.is_safe
        }


if __name__ == "__main__":
    # Test firewall
    print("Firewall Module - Test")
    print("-" * 40)
    
    from claim_extractor import Claim
    from verifier import VerificationResult
    
    # Create mock verification results
    results = [
        VerificationResult(
            claim=Claim(text="Python was released in 1991", claim_id=0),
            is_supported=True,
            similarity_score=0.85,
            entailment_label='ENTAILED',
            entailment_score=0.9,
            best_evidence="Python was first released in 1991.",
            evidence_source="wiki"
        ),
        VerificationResult(
            claim=Claim(text="Python was created by Guido", claim_id=1),
            is_supported=True,
            similarity_score=0.82,
            entailment_label='ENTAILED',
            entailment_score=0.88,
            best_evidence="Guido van Rossum created Python.",
            evidence_source="wiki"
        ),
        VerificationResult(
            claim=Claim(text="Python is written in Java", claim_id=2),
            is_supported=False,
            similarity_score=0.45,
            entailment_label='NEUTRAL',
            entailment_score=0.6,
            best_evidence="Python is implemented in C.",
            evidence_source="wiki"
        ),
    ]
    
    # Test firewall with different thresholds
    print("\n--- Threshold 0.8 ---")
    firewall = HallucinationFirewall(firewall_threshold=0.8)
    engine = FirewallDecisionEngine(threshold=0.8)
    result = engine.evaluate(results)
    print(result)
    
    print("\n--- Threshold 0.6 ---")
    engine2 = FirewallDecisionEngine(threshold=0.6)
    result2 = engine2.evaluate(results)
    print(result2)
    
    # Get unsupported claims
    unsupported = engine.get_unsupported_claims(result)
    print(f"\nUnsupported claims: {[c.text for c in unsupported]}")
