"""
Response Generation Module for VDHF

Handles LLM-based response generation using retrieved context.
"""

import os
from typing import List, Optional

from config.settings import (
    GROQ_API_KEY,
    LLM_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    INITIAL_GENERATION_PROMPT
)
from retrieval.retriever import RetrievedEvidence


class ResponseGenerator:
    """
    Response Generation Module

    Purpose:
    - Generate initial response using retrieved context
    - Support Groq Cloud API
    - Provide fallback for testing without API
    """

    def __init__(
        self,
        model: str = LLM_MODEL,
        api_key: Optional[str] = None,
        max_tokens: int = MAX_TOKENS,
        temperature: float = TEMPERATURE
    ):
        self.model = model
        self.api_key = api_key or GROQ_API_KEY
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

        # Initialize Groq client if API key is available
        if self.api_key:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                print("Warning: groq package not installed. Using mock generation.")

    def generate(
        self,
        query: str,
        context: str,
        prompt_template: Optional[str] = None
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            query: User query
            context: Retrieved context/evidence
            prompt_template: Custom prompt template (uses default if not provided)

        Returns:
            Generated response string
        """
        template = prompt_template or INITIAL_GENERATION_PROMPT

        # Format prompt
        prompt = template.format(
            context=context,
            question=query
        )

        # Use Groq if available, otherwise mock
        if self._client:
            return self._generate_groq(prompt)
        else:
            return self._generate_mock(query, context)

    def _generate_groq(self, prompt: str) -> str:
        """Generate using Groq API."""
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate, factual answers based on the given context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._generate_mock_from_prompt(prompt)

    def _generate_mock(self, query: str, context: str) -> str:
        """Generate a mock response for testing without API."""
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'what', 'how', 'who', 'which', 'where', 'when', 'why', 'do',
                      'does', 'did', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
                      'by', 'from', 'and', 'or', 'but', 'if', 'it', 'this', 'that'}

        query_words = set(query.lower().split()) - stop_words

        # Split into sentences and score by meaningful word overlap
        sentences = [s.strip() for s in context.split('.') if len(s.strip()) > 20]
        scored = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split()) - stop_words
            overlap = query_words & sentence_words
            if overlap:
                scored.append((len(overlap), sentence))

        # Sort by relevance (most overlapping words first)
        scored.sort(key=lambda x: x[0], reverse=True)

        if scored:
            best = [s for _, s in scored[:4]]
            response = ". ".join(best)
            if not response.endswith('.'):
                response += '.'
            return response
        elif context:
            return context[:500].rsplit('.', 1)[0] + '.'
        else:
            return "No relevant information found in the uploaded documents."

    def _generate_mock_from_prompt(self, prompt: str) -> str:
        """Extract a simple response from the prompt context."""
        # Find context section
        if "Context:" in prompt:
            start = prompt.find("Context:") + len("Context:")
            end = prompt.find("Question:")
            if end > start:
                context = prompt[start:end].strip()
                return self._generate_mock("", context)
        return "Unable to generate response from the provided context."

    def generate_with_evidence(
        self,
        query: str,
        evidence_list: List[RetrievedEvidence],
        prompt_template: Optional[str] = None
    ) -> str:
        """
        Generate a response using evidence list.

        Args:
            query: User query
            evidence_list: List of RetrievedEvidence objects
            prompt_template: Custom prompt template

        Returns:
            Generated response string
        """
        # Build context string from evidence
        context_parts = []
        for ev in evidence_list:
            context_parts.append(ev.content)

        context = "\n\n---\n\n".join(context_parts)

        return self.generate(query, context, prompt_template)

    def regenerate_with_refinement(
        self,
        query: str,
        verified_evidence: str,
        prompt_template: str
    ) -> str:
        """
        Regenerate response using refined prompt.

        Args:
            query: Original user query
            verified_evidence: Only verified evidence
            prompt_template: Refined prompt template

        Returns:
            Regenerated response
        """
        prompt = prompt_template.format(
            question=query,
            evidence=verified_evidence
        )

        if self._client:
            return self._generate_groq(prompt)
        else:
            return self._generate_mock(query, verified_evidence)


class GenerationResult:
    """Container for generation results with metadata."""

    def __init__(
        self,
        response: str,
        query: str,
        context: str,
        is_regenerated: bool = False,
        attempt_number: int = 1
    ):
        self.response = response
        self.query = query
        self.context = context
        self.is_regenerated = is_regenerated
        self.attempt_number = attempt_number

    def __str__(self) -> str:
        status = "Regenerated" if self.is_regenerated else "Initial"
        return f"[{status} Response - Attempt {self.attempt_number}]\n{self.response}"
