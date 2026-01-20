"""
Claim Extraction Module for VDHF

Decomposes generated responses into verifiable atomic claims.
"""

import re
from typing import List, Optional
from dataclasses import dataclass, field

from config import CLAIM_EXTRACTION_PROMPT


@dataclass
class Claim:
    """Represents an atomic factual claim."""
    text: str
    claim_id: int
    source_sentence: str = ""
    is_factual: bool = True
    
    # Verification results (populated by verifier)
    is_verified: bool = False
    similarity_score: float = 0.0
    entailment_label: str = ""
    supporting_evidence: str = ""
    
    def __str__(self) -> str:
        status = "✓" if self.is_verified else "✗"
        return f"[{status}] Claim {self.claim_id}: {self.text}"


class ClaimExtractor:
    """
    Claim Extraction Module
    
    Purpose:
    - Decompose response into sentences
    - Identify factual claims
    - Split compound sentences into atomic claims
    """
    
    # Patterns for non-factual content
    OPINION_PATTERNS = [
        r'\b(I think|I believe|In my opinion|probably|maybe|perhaps|might|could be)\b',
        r'\b(it seems|appears to|likely|unlikely|possibly)\b',
        r'\b(should|would|ought to|must be)\b',  # Modal suggestions
    ]
    
    # Patterns for vague statements
    VAGUE_PATTERNS = [
        r'^(Yes|No|Sure|Okay|Of course)[,.]',
        r'^(In general|Generally|Usually|Often|Sometimes)',
        r'\b(and so on|etc\.|et cetera)\b',
    ]
    
    # Conjunctions to split on
    CONJUNCTIONS = [
        ' and ',
        ' but ',
        ' while ',
        ' whereas ',
        ', and ',
        '; ',
    ]
    
    def __init__(self, use_llm: bool = False, generator=None):
        """
        Initialize the claim extractor.
        
        Args:
            use_llm: Whether to use LLM for claim extraction
            generator: Generator instance for LLM-based extraction
        """
        self.use_llm = use_llm
        self.generator = generator
    
    def extract_claims(self, response: str) -> List[Claim]:
        """
        Extract all factual claims from a response.
        
        Args:
            response: Generated response text
            
        Returns:
            List of Claim objects
        """
        if self.use_llm and self.generator:
            return self._extract_with_llm(response)
        else:
            return self._extract_rule_based(response)
    
    def _extract_rule_based(self, response: str) -> List[Claim]:
        """
        Extract claims using rule-based approach.
        
        Args:
            response: Generated response text
            
        Returns:
            List of Claim objects
        """
        claims = []
        claim_id = 0
        
        # Split into sentences
        sentences = self._split_into_sentences(response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            if not sentence or len(sentence) < 10:
                continue
            
            # Check if sentence is factual
            if not self._is_factual(sentence):
                continue
            
            # Split compound sentences into atomic claims
            atomic_claims = self._split_compound_sentence(sentence)
            
            for claim_text in atomic_claims:
                claim_text = claim_text.strip()
                
                if self._is_valid_claim(claim_text):
                    claim = Claim(
                        text=claim_text,
                        claim_id=claim_id,
                        source_sentence=sentence,
                        is_factual=True
                    )
                    claims.append(claim)
                    claim_id += 1
        
        return claims
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr)\.\s', r'\1<PERIOD> ', text)
        text = re.sub(r'\b(Inc|Ltd|Corp|Co)\.\s', r'\1<PERIOD> ', text)
        text = re.sub(r'\b(e\.g|i\.e|etc)\.\s', r'\1<PERIOD> ', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore periods
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]
        
        return sentences
    
    def _is_factual(self, sentence: str) -> bool:
        """
        Check if a sentence contains factual content.
        
        Args:
            sentence: Sentence to check
            
        Returns:
            True if sentence appears factual
        """
        sentence_lower = sentence.lower()
        
        # Check for opinion patterns
        for pattern in self.OPINION_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                return False
        
        # Check for vague patterns
        for pattern in self.VAGUE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                return False
        
        # Check for questions
        if sentence.strip().endswith('?'):
            return False
        
        return True
    
    def _split_compound_sentence(self, sentence: str) -> List[str]:
        """
        Split a compound sentence into atomic claims.
        
        Args:
            sentence: Sentence to split
            
        Returns:
            List of atomic claim strings
        """
        claims = [sentence]
        
        for conj in self.CONJUNCTIONS:
            new_claims = []
            for claim in claims:
                if conj in claim:
                    parts = claim.split(conj)
                    for part in parts:
                        part = part.strip()
                        if part:
                            # Ensure proper capitalization
                            if part[0].islower():
                                part = part[0].upper() + part[1:]
                            new_claims.append(part)
                else:
                    new_claims.append(claim)
            claims = new_claims
        
        return claims
    
    def _is_valid_claim(self, claim_text: str) -> bool:
        """
        Check if extracted claim is valid.
        
        Args:
            claim_text: Claim text to validate
            
        Returns:
            True if claim is valid
        """
        # Minimum length check
        if len(claim_text) < 15:
            return False
        
        # Must contain at least one noun-like word (basic check)
        words = claim_text.split()
        if len(words) < 3:
            return False
        
        # Should not be just a fragment
        if claim_text.lower().startswith(('the', 'a ', 'an ')) and len(words) < 5:
            return False
        
        return True
    
    def _extract_with_llm(self, response: str) -> List[Claim]:
        """
        Extract claims using LLM.
        
        Args:
            response: Generated response text
            
        Returns:
            List of Claim objects
        """
        if not self.generator:
            return self._extract_rule_based(response)
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=response)
        
        try:
            result = self.generator.generate(
                query="Extract claims",
                context=prompt
            )
            
            # Parse LLM output
            claims = []
            claim_id = 0
            
            for line in result.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove numbering if present
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    line = re.sub(r'^[-•]\s*', '', line)
                    
                    if self._is_valid_claim(line):
                        claim = Claim(
                            text=line,
                            claim_id=claim_id,
                            source_sentence=response,
                            is_factual=True
                        )
                        claims.append(claim)
                        claim_id += 1
            
            return claims if claims else self._extract_rule_based(response)
            
        except Exception as e:
            print(f"LLM extraction failed: {e}")
            return self._extract_rule_based(response)
    
    def get_claim_texts(self, claims: List[Claim]) -> List[str]:
        """
        Get just the text of claims.
        
        Args:
            claims: List of Claim objects
            
        Returns:
            List of claim text strings
        """
        return [claim.text for claim in claims]


def extract_claims(response: str) -> List[Claim]:
    """
    Convenience function to extract claims from a response.
    
    Args:
        response: Generated response text
        
    Returns:
        List of Claim objects
    """
    extractor = ClaimExtractor()
    return extractor.extract_claims(response)


if __name__ == "__main__":
    # Test claim extraction
    print("Claim Extractor Module - Test")
    print("-" * 40)
    
    test_responses = [
        """Python was released in 1991 and created by Guido van Rossum. 
        It is a high-level programming language that emphasizes code readability.
        Python supports multiple programming paradigms including procedural, 
        object-oriented, and functional programming.""",
        
        """I think Python is great. It was definitely released in 1991.
        The language was created by Guido van Rossum in the Netherlands.
        Maybe it's the best language for beginners?""",
        
        """World War I was caused by several factors. Militarism contributed 
        to the war, and nationalism played a significant role. The assassination 
        of Archduke Franz Ferdinand triggered the conflict in 1914."""
    ]
    
    extractor = ClaimExtractor()
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n--- Test {i} ---")
        print(f"Response: {response[:100]}...")
        print("\nExtracted Claims:")
        
        claims = extractor.extract_claims(response)
        for claim in claims:
            print(f"  {claim}")
