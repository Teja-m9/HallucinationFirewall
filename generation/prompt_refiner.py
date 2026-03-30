"""
Prompt Refinement Module for VDHF

Improves response safety by refining prompts when verification fails.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from config.settings import REFINED_GENERATION_PROMPT
from core.claim_extractor import Claim
from core.firewall import FirewallResult


@dataclass
class RefinementResult:
    """Result of prompt refinement."""
    refined_prompt: str
    excluded_claims: List[str]
    included_evidence: List[str]
    original_query: str

    def __str__(self) -> str:
        return (
            f"Refinement Result:\n"
            f"  Excluded Claims: {len(self.excluded_claims)}\n"
            f"  Included Evidence: {len(self.included_evidence)}\n"
            f"  Prompt Length: {len(self.refined_prompt)} chars"
        )


class PromptRefiner:
    """
    Prompt Refinement Module

    Purpose:
    Improve response safety without rejecting the user.

    Refinement Strategy:
    1. Remove unsupported claims from consideration
    2. Constrain generation strictly to verified evidence
    3. Explicitly instruct the LLM to avoid speculation
    4. Allow partial but accurate answers
    """

    def __init__(
        self,
        prompt_template: str = REFINED_GENERATION_PROMPT,
        max_evidence_length: int = 3000
    ):
        self.prompt_template = prompt_template
        self.max_evidence_length = max_evidence_length

    def refine_prompt(
        self,
        query: str,
        firewall_result: FirewallResult,
        evidence_list: List = None
    ) -> RefinementResult:
        """
        Generate a refined prompt based on verification results.

        Args:
            query: Original user query
            firewall_result: Result from firewall evaluation
            evidence_list: Original retrieved evidence (optional)

        Returns:
            RefinementResult with refined prompt
        """
        # Get unsupported claims to exclude
        excluded_claims = self._get_excluded_claims(firewall_result)

        # Get verified evidence
        verified_evidence = self._get_verified_evidence(firewall_result)

        # Build refined evidence string
        evidence_string = self._format_evidence(verified_evidence)

        # Generate refined prompt
        refined_prompt = self.prompt_template.format(
            question=query,
            evidence=evidence_string
        )

        return RefinementResult(
            refined_prompt=refined_prompt,
            excluded_claims=[c.text for c in excluded_claims],
            included_evidence=verified_evidence,
            original_query=query
        )

    def _get_excluded_claims(
        self,
        firewall_result: FirewallResult
    ) -> List[Claim]:
        """Get claims to exclude from refinement."""
        excluded = []
        for result in firewall_result.verification_results:
            if not result.is_supported:
                excluded.append(result.claim)
        return excluded

    def _get_verified_evidence(
        self,
        firewall_result: FirewallResult
    ) -> List[str]:
        """Get evidence that supports verified claims."""
        evidence = []
        seen = set()

        for result in firewall_result.verification_results:
            if result.is_supported and result.best_evidence:
                if result.best_evidence not in seen:
                    evidence.append(result.best_evidence)
                    seen.add(result.best_evidence)

        return evidence

    def _format_evidence(self, evidence_list: List[str]) -> str:
        """Format evidence for the refined prompt."""
        if not evidence_list:
            return "No verified evidence available. Please indicate that the answer cannot be determined from the available information."

        formatted_parts = []
        total_length = 0

        for i, evidence in enumerate(evidence_list, 1):
            formatted = f"[Evidence {i}]\n{evidence}"

            # Check length limit
            if total_length + len(formatted) > self.max_evidence_length:
                break

            formatted_parts.append(formatted)
            total_length += len(formatted)

        return "\n\n".join(formatted_parts)

    def create_strict_prompt(
        self,
        query: str,
        evidence_list: List[str]
    ) -> str:
        """
        Create a strict prompt that forces the LLM to only use provided evidence.

        Args:
            query: User query
            evidence_list: List of evidence strings

        Returns:
            Strict generation prompt
        """
        evidence_string = self._format_evidence(evidence_list)

        strict_template = """You must answer the following question using ONLY the evidence provided below.

STRICT RULES:
1. Only use information explicitly stated in the evidence
2. Do not add any external knowledge or assumptions
3. If the evidence does not contain enough information, say "Based on the available evidence, I cannot fully answer this question"
4. Quote or closely paraphrase the evidence when possible
5. Do not speculate or infer beyond what is directly stated

Question:
{question}

Evidence:
{evidence}

Answer (using only the evidence above):"""

        return strict_template.format(
            question=query,
            evidence=evidence_string
        )

    def create_acknowledgment_prompt(
        self,
        query: str,
        supported_info: List[str],
        unsupported_topics: List[str]
    ) -> str:
        """
        Create a prompt that acknowledges limitations.

        Args:
            query: User query
            supported_info: Information that is verified
            unsupported_topics: Topics that cannot be verified

        Returns:
            Acknowledgment prompt
        """
        supported_str = "\n".join(f"- {info}" for info in supported_info)
        unsupported_str = "\n".join(f"- {topic}" for topic in unsupported_topics)

        template = """Answer the following question. Use ONLY the verified information provided.

Question: {question}

VERIFIED INFORMATION (you may use this):
{supported}

UNVERIFIED TOPICS (do NOT make claims about these):
{unsupported}

Instructions:
- Provide an accurate answer using only the verified information
- If asked about unverified topics, acknowledge that you cannot verify that information
- Be helpful while maintaining accuracy

Answer:"""

        return template.format(
            question=query,
            supported=supported_str if supported_str else "No verified information available.",
            unsupported=unsupported_str if unsupported_str else "None specified."
        )


class RegenerationManager:
    """
    Manages the regeneration process when firewall blocks a response.
    """

    def __init__(
        self,
        prompt_refiner: Optional[PromptRefiner] = None,
        max_attempts: int = 2
    ):
        self.prompt_refiner = prompt_refiner or PromptRefiner()
        self.max_attempts = max_attempts

    def should_regenerate(
        self,
        firewall_result: FirewallResult,
        attempt_number: int
    ) -> bool:
        """
        Determine if regeneration should be attempted.

        Args:
            firewall_result: Current firewall result
            attempt_number: Current attempt number

        Returns:
            True if regeneration should be attempted
        """
        if firewall_result.is_safe:
            return False

        if attempt_number >= self.max_attempts:
            return False

        # Don't regenerate if no verified evidence exists
        if firewall_result.supported_claims == 0:
            return False

        return True

    def prepare_regeneration(
        self,
        query: str,
        firewall_result: FirewallResult,
        use_strict_mode: bool = True
    ) -> str:
        """
        Prepare the regeneration prompt.

        Args:
            query: Original query
            firewall_result: Firewall result from previous attempt
            use_strict_mode: Whether to use strict prompt mode

        Returns:
            Regeneration prompt string
        """
        refinement = self.prompt_refiner.refine_prompt(
            query=query,
            firewall_result=firewall_result
        )

        if use_strict_mode and refinement.included_evidence:
            return self.prompt_refiner.create_strict_prompt(
                query=query,
                evidence_list=refinement.included_evidence
            )

        return refinement.refined_prompt
