"""
Main Pipeline Module for VDHF

Orchestrates the complete Verification-Driven Hallucination Firewall pipeline.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from config.settings import (
    SIMILARITY_THRESHOLD,
    FIREWALL_THRESHOLD,
    MAX_REGENERATION_ATTEMPTS,
    TOP_K_RETRIEVAL
)
from ingestion.loader import DocumentIngestion, DocumentChunk
from ingestion.embeddings import EmbeddingModel, VectorStore
from retrieval.retriever import Retriever, RetrievedEvidence, RAGPipeline
from generation.generator import ResponseGenerator, GenerationResult
from core.claim_extractor import ClaimExtractor, Claim
from core.verifier import ClaimVerifier, VerificationResult
from core.firewall import HallucinationFirewall, FirewallResult, FirewallDecision
from generation.prompt_refiner import PromptRefiner, RegenerationManager


@dataclass
class PipelineResult:
    """Complete result from the VDHF pipeline."""
    query: str
    final_response: str
    is_verified: bool
    support_ratio: float
    total_claims: int
    supported_claims: int
    regeneration_attempts: int
    retrieved_evidence: List[RetrievedEvidence]
    claims: List[Claim]
    verification_results: List[VerificationResult]

    def __str__(self) -> str:
        status = "✓ VERIFIED" if self.is_verified else "⚠ PARTIALLY VERIFIED"
        return (
            f"\n{'='*60}\n"
            f"VDHF Pipeline Result\n"
            f"{'='*60}\n"
            f"Status: {status}\n"
            f"Support Ratio: {self.support_ratio:.2%}\n"
            f"Claims: {self.supported_claims}/{self.total_claims} supported\n"
            f"Regeneration Attempts: {self.regeneration_attempts}\n"
            f"{'='*60}\n"
            f"Response:\n{self.final_response}\n"
            f"{'='*60}"
        )


class VDHFPipeline:
    """
    Verification-Driven Hallucination Firewall Pipeline

    Complete pipeline that:
    1. Ingests documents
    2. Retrieves relevant evidence for queries
    3. Generates initial response
    4. Extracts and verifies claims
    5. Applies firewall decision
    6. Regenerates if necessary
    7. Delivers verified response
    """

    def __init__(
        self,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        firewall_threshold: float = FIREWALL_THRESHOLD,
        max_regeneration_attempts: int = MAX_REGENERATION_ATTEMPTS,
        top_k: int = TOP_K_RETRIEVAL,
        collection_name: str = "vdhf_main"
    ):
        # Store configuration
        self.similarity_threshold = similarity_threshold
        self.firewall_threshold = firewall_threshold
        self.max_regeneration_attempts = max_regeneration_attempts
        self.top_k = top_k

        # Initialize components
        print("Initializing VDHF Pipeline components...")

        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore(
            collection_name=collection_name,
            embedding_model=self.embedding_model
        )
        self.retriever = Retriever(
            vector_store=self.vector_store,
            top_k=top_k
        )
        self.generator = ResponseGenerator()
        self.claim_extractor = ClaimExtractor()
        self.verifier = ClaimVerifier(similarity_threshold=similarity_threshold)
        self.firewall = HallucinationFirewall(
            similarity_threshold=similarity_threshold,
            firewall_threshold=firewall_threshold
        )
        self.prompt_refiner = PromptRefiner()
        self.regeneration_manager = RegenerationManager(
            prompt_refiner=self.prompt_refiner,
            max_attempts=max_regeneration_attempts
        )
        self.ingestion = DocumentIngestion()

        print("VDHF Pipeline initialized successfully!")

    # =========================================================================
    # Document Management
    # =========================================================================

    def ingest_file(self, file_path: str) -> int:
        """
        Ingest a single document file.

        Args:
            file_path: Path to the document

        Returns:
            Number of chunks created
        """
        chunks = self.ingestion.ingest_file(file_path)
        self.vector_store.add_chunks(chunks)
        print(f"Ingested {file_path}: {len(chunks)} chunks")
        return len(chunks)

    def ingest_directory(self, directory_path: str) -> int:
        """
        Ingest all documents from a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            Number of chunks created
        """
        chunks = self.ingestion.ingest_directory(directory_path)
        self.vector_store.add_chunks(chunks)
        print(f"Ingested {directory_path}: {len(chunks)} chunks total")
        return len(chunks)

    def ingest_text(self, text: str, source: str = "direct_input") -> int:
        """
        Ingest text directly.

        Args:
            text: Text content to ingest
            source: Source identifier

        Returns:
            Number of chunks created
        """
        chunks = self.ingestion.ingest_text(text, source=source)
        self.vector_store.add_chunks(chunks)
        print(f"Ingested text from {source}: {len(chunks)} chunks")
        return len(chunks)

    def clear_documents(self) -> None:
        """Clear all documents from the vector store."""
        self.vector_store.clear()
        print("Cleared all documents from vector store")

    @property
    def document_count(self) -> int:
        """Get number of document chunks in the store."""
        return self.vector_store.count()

    # =========================================================================
    # Query Processing
    # =========================================================================

    def query(self, user_query: str, verbose: bool = False) -> PipelineResult:
        """
        Process a user query through the complete VDHF pipeline.

        Args:
            user_query: User's question
            verbose: Whether to print detailed progress

        Returns:
            PipelineResult with verified response
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing Query: {user_query}")
            print(f"{'='*60}")

        # Step 1: Retrieve relevant evidence
        if verbose:
            print("\n[1] Retrieving evidence...")
        evidence_list = self.retriever.retrieve(user_query, top_k=self.top_k)

        if not evidence_list:
            return self._create_no_evidence_result(user_query)

        if verbose:
            print(f"    Retrieved {len(evidence_list)} evidence chunks")

        # Step 2: Generate initial response
        if verbose:
            print("\n[2] Generating initial response...")
        context = self.retriever.get_context_string(evidence_list)
        initial_response = self.generator.generate(user_query, context)

        if verbose:
            print(f"    Generated response: {initial_response[:100]}...")

        # Step 3: Extract claims
        if verbose:
            print("\n[3] Extracting claims...")
        claims = self.claim_extractor.extract_claims(initial_response)

        if verbose:
            print(f"    Extracted {len(claims)} claims")

        # Handle case with no extractable claims
        if not claims:
            return self._create_no_claims_result(
                user_query, initial_response, evidence_list
            )

        # Step 4-6: Verify, firewall check, and potentially regenerate
        current_response = initial_response
        current_claims = claims
        regeneration_count = 0

        for attempt in range(self.max_regeneration_attempts + 1):
            # Step 4: Verify claims
            if verbose:
                print(f"\n[4] Verifying claims (attempt {attempt + 1})...")

            verification_results = self.verifier.verify_all_claims(
                current_claims, evidence_list
            )

            # Step 5: Apply firewall
            if verbose:
                print("\n[5] Applying firewall...")

            firewall_result = self.firewall.decision_engine.evaluate(verification_results)

            if verbose:
                print(f"    Support ratio: {firewall_result.support_ratio:.2%}")
                print(f"    Decision: {firewall_result.decision.value}")

            # Step 6: Check if regeneration needed
            if firewall_result.is_safe:
                if verbose:
                    print("\n[6] Response passed firewall ✓")
                break

            # Attempt regeneration
            if not self.regeneration_manager.should_regenerate(
                firewall_result, attempt + 1
            ):
                if verbose:
                    print("\n[6] Max regeneration attempts reached")
                break

            if verbose:
                print(f"\n[6] Regenerating response (attempt {attempt + 2})...")

            regeneration_count += 1

            # Generate refined prompt
            refined_prompt = self.regeneration_manager.prepare_regeneration(
                query=user_query,
                firewall_result=firewall_result,
                use_strict_mode=True
            )

            # Regenerate response
            current_response = self.generator._generate_mock(
                user_query,
                "\n".join(self.firewall.decision_engine.get_verified_evidence(firewall_result))
            )

            # Re-extract claims
            current_claims = self.claim_extractor.extract_claims(current_response)

            if not current_claims:
                break

        # Create final result
        return PipelineResult(
            query=user_query,
            final_response=current_response,
            is_verified=firewall_result.is_safe,
            support_ratio=firewall_result.support_ratio,
            total_claims=firewall_result.total_claims,
            supported_claims=firewall_result.supported_claims,
            regeneration_attempts=regeneration_count,
            retrieved_evidence=evidence_list,
            claims=current_claims,
            verification_results=verification_results
        )

    def _create_no_evidence_result(self, query: str) -> PipelineResult:
        """Create result when no evidence is found."""
        return PipelineResult(
            query=query,
            final_response="I could not find relevant information to answer your question. Please ensure documents have been ingested into the system.",
            is_verified=True,
            support_ratio=1.0,
            total_claims=0,
            supported_claims=0,
            regeneration_attempts=0,
            retrieved_evidence=[],
            claims=[],
            verification_results=[]
        )

    def _create_no_claims_result(
        self,
        query: str,
        response: str,
        evidence: List[RetrievedEvidence]
    ) -> PipelineResult:
        """Create result when no claims are extractable."""
        return PipelineResult(
            query=query,
            final_response=response,
            is_verified=True,
            support_ratio=1.0,
            total_claims=0,
            supported_claims=0,
            regeneration_attempts=0,
            retrieved_evidence=evidence,
            claims=[],
            verification_results=[]
        )

    # =========================================================================
    # Analysis and Debugging
    # =========================================================================

    def analyze_response(
        self,
        response: str,
        evidence_list: List[RetrievedEvidence]
    ) -> Dict[str, Any]:
        """
        Analyze a response without regeneration.

        Useful for debugging and understanding verification.
        """
        claims = self.claim_extractor.extract_claims(response)
        verification_results = self.verifier.verify_all_claims(claims, evidence_list)
        firewall_result = self.firewall.decision_engine.evaluate(verification_results)

        return {
            'claims': claims,
            'verification_results': verification_results,
            'firewall_result': firewall_result,
            'summary': self.verifier.get_verification_summary(verification_results)
        }


def interactive_mode(pipeline: VDHFPipeline):
    """Run the pipeline in interactive mode."""
    print("\n" + "="*60)
    print("VDHF Interactive Mode")
    print("="*60)
    print("Commands:")
    print("  /ingest <path>  - Ingest document(s) from path")
    print("  /clear          - Clear all documents")
    print("  /count          - Show document count")
    print("  /quit           - Exit")
    print("="*60)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()

                if command == "/quit":
                    print("Goodbye!")
                    break
                elif command == "/clear":
                    pipeline.clear_documents()
                elif command == "/count":
                    print(f"Documents in store: {pipeline.document_count} chunks")
                elif command == "/ingest":
                    if len(parts) > 1:
                        path = parts[1].strip()
                        if os.path.exists(path):
                            if os.path.isfile(path):
                                pipeline.ingest_file(path)
                            else:
                                pipeline.ingest_directory(path)
                        else:
                            print(f"Path not found: {path}")
                    else:
                        print("Usage: /ingest <path>")
                else:
                    print(f"Unknown command: {command}")
                continue

            # Process query
            if pipeline.document_count == 0:
                print("\nNo documents loaded. Use /ingest <path> to add documents.")
                continue

            result = pipeline.query(user_input, verbose=True)
            print(result)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
