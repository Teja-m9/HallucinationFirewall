"""
Verification Module for VDHF

Handles claim verification using semantic similarity and NLI entailment.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
except ImportError:
    pipeline = None
    torch = None

from config.settings import (
    SIMILARITY_THRESHOLD,
    NLI_MODEL,
    EMBEDDING_MODEL
)
from core.claim_extractor import Claim
from ingestion.embeddings import EmbeddingModel, compute_cosine_similarity
from retrieval.retriever import RetrievedEvidence


@dataclass
class VerificationResult:
    """Result of claim verification."""
    claim: Claim
    is_supported: bool
    similarity_score: float
    entailment_label: str  # ENTAILED, NEUTRAL, CONTRADICTED
    entailment_score: float
    best_evidence: str
    evidence_source: str

    def __str__(self) -> str:
        status = "SUPPORTED" if self.is_supported else "UNSUPPORTED"
        return (
            f"[{status}] Claim: {self.claim.text[:50]}...\n"
            f"  Similarity: {self.similarity_score:.3f}, "
            f"Entailment: {self.entailment_label} ({self.entailment_score:.3f})"
        )


class SemanticSimilarityChecker:
    """
    Semantic Similarity Module

    Measures semantic closeness between claims and evidence using embeddings.
    """

    def __init__(self, embedding_model: Optional[EmbeddingModel] = None):
        self.embedding_model = embedding_model or EmbeddingModel()

    def compute_similarity(self, claim: str, evidence: str) -> float:
        """
        Compute semantic similarity between claim and evidence.

        Args:
            claim: Claim text
            evidence: Evidence text

        Returns:
            Cosine similarity score (0 to 1)
        """
        claim_embedding = self.embedding_model.embed_single(claim)
        evidence_embedding = self.embedding_model.embed_single(evidence)

        return compute_cosine_similarity(claim_embedding, evidence_embedding)

    def find_best_evidence(
        self,
        claim: str,
        evidence_list: List[RetrievedEvidence]
    ) -> Tuple[RetrievedEvidence, float]:
        """
        Find the most similar evidence for a claim.

        Args:
            claim: Claim text
            evidence_list: List of evidence candidates

        Returns:
            Tuple of (best evidence, similarity score)
        """
        if not evidence_list:
            return None, 0.0

        best_evidence = None
        best_score = 0.0

        claim_embedding = self.embedding_model.embed_single(claim)

        for evidence in evidence_list:
            evidence_embedding = self.embedding_model.embed_single(evidence.content)
            score = compute_cosine_similarity(claim_embedding, evidence_embedding)

            if score > best_score:
                best_score = score
                best_evidence = evidence

        return best_evidence, best_score


class EntailmentChecker:
    """
    NLI Entailment Module

    Checks whether evidence logically entails a claim.
    """

    def __init__(self, model_name: str = NLI_MODEL):
        self.model_name = model_name
        self._pipeline = None

        if pipeline is not None:
            try:
                self._pipeline = pipeline(
                    "text-classification",
                    model=model_name,
                    top_k=None
                )
            except Exception as e:
                print(f"Warning: Could not load NLI model: {e}")

    def check_entailment(
        self,
        premise: str,
        hypothesis: str
    ) -> Tuple[str, float]:
        """
        Check if premise entails hypothesis.

        Args:
            premise: Evidence text (premise)
            hypothesis: Claim text (hypothesis)

        Returns:
            Tuple of (label, score) where label is ENTAILED/NEUTRAL/CONTRADICTED
        """
        if self._pipeline is None:
            # Fallback to simple heuristic
            return self._heuristic_entailment(premise, hypothesis)

        try:
            # Format input for NLI model
            input_text = f"{premise} [SEP] {hypothesis}"

            # Get predictions
            results = self._pipeline(input_text)

            # Parse results
            label_mapping = {
                'ENTAILMENT': 'ENTAILED',
                'CONTRADICTION': 'CONTRADICTED',
                'NEUTRAL': 'NEUTRAL',
                'entailment': 'ENTAILED',
                'contradiction': 'CONTRADICTED',
                'neutral': 'NEUTRAL',
            }

            best_label = 'NEUTRAL'
            best_score = 0.0

            for result in results:
                label = result['label'].upper()
                score = result['score']

                mapped_label = label_mapping.get(label, label)
                if mapped_label in ['ENTAILED', 'NEUTRAL', 'CONTRADICTED']:
                    if score > best_score:
                        best_score = score
                        best_label = mapped_label

            return best_label, best_score

        except Exception as e:
            print(f"NLI error: {e}")
            return self._heuristic_entailment(premise, hypothesis)

    def _heuristic_entailment(
        self,
        premise: str,
        hypothesis: str
    ) -> Tuple[str, float]:
        """
        Simple heuristic for entailment when NLI model unavailable.

        Based on word overlap and key phrase matching.
        """
        premise_words = set(premise.lower().split())
        hypothesis_words = set(hypothesis.lower().split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'can', 'to',
                      'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                      'and', 'or', 'but', 'if', 'then', 'that', 'this', 'it'}

        premise_words = premise_words - stop_words
        hypothesis_words = hypothesis_words - stop_words

        if not hypothesis_words:
            return 'NEUTRAL', 0.5

        overlap = len(premise_words & hypothesis_words)
        overlap_ratio = overlap / len(hypothesis_words)

        if overlap_ratio >= 0.7:
            return 'ENTAILED', overlap_ratio
        elif overlap_ratio >= 0.3:
            return 'NEUTRAL', overlap_ratio
        else:
            return 'NEUTRAL', overlap_ratio


class ClaimVerifier:
    """
    Claim Verification Module

    Combines semantic similarity and NLI entailment to verify claims.

    Verification Rule:
    A claim is SUPPORTED if:
    - Semantic similarity >= threshold (theta_sim)
    - Entailment label == ENTAILED
    """

    def __init__(
        self,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        embedding_model: Optional[EmbeddingModel] = None
    ):
        self.similarity_threshold = similarity_threshold
        self.similarity_checker = SemanticSimilarityChecker(embedding_model)
        self.entailment_checker = EntailmentChecker()

    def verify_claim(
        self,
        claim: Claim,
        evidence_list: List[RetrievedEvidence]
    ) -> VerificationResult:
        """
        Verify a single claim against evidence.

        Args:
            claim: Claim to verify
            evidence_list: Available evidence

        Returns:
            VerificationResult object
        """
        # Find best matching evidence
        best_evidence, similarity_score = self.similarity_checker.find_best_evidence(
            claim.text,
            evidence_list
        )

        if best_evidence is None:
            return VerificationResult(
                claim=claim,
                is_supported=False,
                similarity_score=0.0,
                entailment_label='NEUTRAL',
                entailment_score=0.0,
                best_evidence="",
                evidence_source=""
            )

        # Check entailment
        entailment_label, entailment_score = self.entailment_checker.check_entailment(
            premise=best_evidence.content,
            hypothesis=claim.text
        )

        # Apply verification rule
        is_supported = (
            similarity_score >= self.similarity_threshold and
            entailment_label == 'ENTAILED'
        )

        # Update claim object
        claim.is_verified = is_supported
        claim.similarity_score = similarity_score
        claim.entailment_label = entailment_label
        claim.supporting_evidence = best_evidence.content

        return VerificationResult(
            claim=claim,
            is_supported=is_supported,
            similarity_score=similarity_score,
            entailment_label=entailment_label,
            entailment_score=entailment_score,
            best_evidence=best_evidence.content,
            evidence_source=best_evidence.metadata.get('source', 'Unknown')
        )

    def verify_all_claims(
        self,
        claims: List[Claim],
        evidence_list: List[RetrievedEvidence]
    ) -> List[VerificationResult]:
        """
        Verify all claims against evidence.

        Args:
            claims: List of claims to verify
            evidence_list: Available evidence

        Returns:
            List of VerificationResult objects
        """
        results = []
        for claim in claims:
            result = self.verify_claim(claim, evidence_list)
            results.append(result)
        return results

    def get_verification_summary(
        self,
        results: List[VerificationResult]
    ) -> Dict[str, Any]:
        """
        Get summary statistics of verification results.

        Args:
            results: List of VerificationResult objects

        Returns:
            Summary dictionary
        """
        total = len(results)
        supported = sum(1 for r in results if r.is_supported)
        unsupported = total - supported

        avg_similarity = np.mean([r.similarity_score for r in results]) if results else 0.0

        return {
            'total_claims': total,
            'supported_claims': supported,
            'unsupported_claims': unsupported,
            'support_ratio': supported / total if total > 0 else 0.0,
            'average_similarity': avg_similarity
        }


def verify_response(
    claims: List[Claim],
    evidence_list: List[RetrievedEvidence],
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[List[VerificationResult], Dict[str, Any]]:
    """
    Convenience function to verify all claims in a response.

    Args:
        claims: Extracted claims
        evidence_list: Retrieved evidence
        similarity_threshold: Verification threshold

    Returns:
        Tuple of (verification results, summary)
    """
    verifier = ClaimVerifier(similarity_threshold=similarity_threshold)
    results = verifier.verify_all_claims(claims, evidence_list)
    summary = verifier.get_verification_summary(results)
    return results, summary
