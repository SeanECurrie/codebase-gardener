"""
Enhanced Analysis Integration - RAG-powered Context Retrieval

This module provides integration between the RAG engine and the codebase analysis
system, enabling context-aware responses and enhanced analysis generation.
"""

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import structlog

from ..utils import graceful_fallback
from .component_registry import ComponentRegistry

logger = structlog.get_logger(__name__)


@dataclass
class AnalysisContext:
    """Context information for enhanced analysis."""

    # Query information
    query: str
    query_type: str  # 'chat', 'analysis', 'explanation'
    timestamp: datetime

    # Retrieved context
    retrieved_chunks: list[dict[str, Any]]
    context_text: str
    retrieval_time_ms: float

    # Quality metrics
    relevance_score: float
    context_length: int
    num_chunks_used: int

    # Metadata
    project_id: str | None = None
    language_filter: str | None = None
    chunk_type_filter: str | None = None


@dataclass
class EnhancedResponse:
    """Enhanced response with context and performance metrics."""

    # Response content
    response: str
    response_type: str  # 'simple', 'enhanced', 'hybrid'

    # Context used
    context_used: bool
    context_summary: str

    # Performance metrics
    total_time_ms: float
    retrieval_time_ms: float
    generation_time_ms: float

    # Quality indicators
    confidence_score: float
    context_relevance: float

    # Metadata
    timestamp: datetime
    model_used: str
    fallback_reason: str | None = None


@dataclass
class PerformanceMetrics:
    """Performance tracking for enhanced analysis."""

    # Retrieval metrics
    avg_retrieval_time_ms: float
    max_retrieval_time_ms: float
    retrieval_success_rate: float

    # Context quality metrics
    avg_relevance_score: float
    context_hit_rate: float  # % of queries that found relevant context

    # Response metrics
    enhanced_response_rate: float  # % using enhanced mode
    fallback_rate: float  # % falling back to simple mode

    # A/B testing metrics
    enhanced_preference_rate: float
    simple_preference_rate: float

    # Timestamps
    measurement_period_start: datetime
    measurement_period_end: datetime
    total_queries: int


class EnhancedAnalysisIntegration:
    """
    Integration layer for RAG-powered enhanced analysis.

    This class coordinates between the RAG engine, vector store, and
    chat/analysis functionality to provide context-aware responses.
    """

    def __init__(self, component_registry: ComponentRegistry | None = None):
        """Initialize enhanced analysis integration.

        Args:
            component_registry: Component registry for dynamic loading
        """
        self.registry = component_registry or ComponentRegistry()
        self._performance_metrics = []
        self._ab_test_data = []

        # Configuration
        self.config = {
            "retrieval_timeout_ms": 200,
            "max_context_chunks": 5,
            "min_relevance_threshold": 0.3,
            "enable_ab_testing": True,
            "enable_performance_monitoring": True,
            "context_window_chars": 4000,
        }

        logger.info("EnhancedAnalysisIntegration initialized")

    @graceful_fallback("Failed to retrieve RAG context")
    def retrieve_context_for_query(
        self,
        query: str,
        project_id: str | None = None,
        language_filter: str | None = None,
        chunk_type_filter: str | None = None,
    ) -> AnalysisContext | None:
        """
        Retrieve relevant context for a user query using RAG.

        Args:
            query: User's question or request
            project_id: Project to search within
            language_filter: Filter by programming language
            chunk_type_filter: Filter by chunk type (function, class, etc.)

        Returns:
            AnalysisContext with retrieved information, or None if unavailable
        """
        start_time = time.time()

        try:
            # Check if RAG components are available
            if not self.registry.is_component_available("rag_engine"):
                logger.debug("RAG engine not available, skipping context retrieval")
                return None

            # Get RAG engine component
            rag_engine = self.registry.get_component("rag_engine")
            if not rag_engine:
                return None

            # Perform context retrieval
            retrieval_result = rag_engine.retrieve_context(
                query=query,
                project_id=project_id,
                language_filter=language_filter,
                chunk_type_filter=chunk_type_filter,
                max_chunks=self.config["max_context_chunks"],
                min_similarity=self.config["min_relevance_threshold"],
            )

            if not retrieval_result or not retrieval_result.chunks:
                logger.debug("No relevant context found for query", query=query[:50])
                return None

            # Format context
            enhanced_context = rag_engine.format_context(retrieval_result)

            retrieval_time = (time.time() - start_time) * 1000

            # Create analysis context
            analysis_context = AnalysisContext(
                query=query,
                query_type="chat",  # Will be updated by caller if needed
                timestamp=datetime.now(),
                retrieved_chunks=[asdict(chunk) for chunk in retrieval_result.chunks],
                context_text=enhanced_context.formatted_context,
                retrieval_time_ms=retrieval_time,
                relevance_score=retrieval_result.avg_relevance_score,
                context_length=len(enhanced_context.formatted_context),
                num_chunks_used=len(retrieval_result.chunks),
                project_id=project_id,
                language_filter=language_filter,
                chunk_type_filter=chunk_type_filter,
            )

            logger.info(
                "Context retrieved successfully",
                query_length=len(query),
                chunks_found=len(retrieval_result.chunks),
                relevance_score=retrieval_result.avg_relevance_score,
                retrieval_time_ms=retrieval_time,
            )

            return analysis_context

        except Exception as e:
            logger.warning("Context retrieval failed", error=str(e), query=query[:50])
            return None

    def enhance_chat_response(
        self,
        query: str,
        base_response: str,
        analysis_context: AnalysisContext | None = None,
        project_id: str | None = None,
    ) -> EnhancedResponse:
        """
        Enhance a chat response using retrieved context.

        Args:
            query: Original user query
            base_response: Base response from simple mode
            analysis_context: Retrieved context information
            project_id: Current project ID

        Returns:
            EnhancedResponse with improved content and metrics
        """
        start_time = time.time()

        try:
            if not analysis_context:
                # No context available, return simple response
                return EnhancedResponse(
                    response=base_response,
                    response_type="simple",
                    context_used=False,
                    context_summary="No relevant context found",
                    total_time_ms=(time.time() - start_time) * 1000,
                    retrieval_time_ms=0.0,
                    generation_time_ms=0.0,
                    confidence_score=0.5,  # Neutral confidence for simple response
                    context_relevance=0.0,
                    timestamp=datetime.now(),
                    model_used="simple_mode",
                )

            # Build enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(query, analysis_context)

            # Generate enhanced response
            generation_start = time.time()
            enhanced_response_text = self._generate_enhanced_response(enhanced_prompt)
            generation_time = (time.time() - generation_start) * 1000

            total_time = (time.time() - start_time) * 1000

            # Calculate confidence score based on context relevance and length
            confidence_score = min(
                0.9,
                0.5
                + (analysis_context.relevance_score * 0.3)
                + (min(analysis_context.num_chunks_used, 3) * 0.1),
            )

            enhanced_response = EnhancedResponse(
                response=enhanced_response_text,
                response_type="enhanced",
                context_used=True,
                context_summary=f"Used {analysis_context.num_chunks_used} code chunks "
                f"(relevance: {analysis_context.relevance_score:.2f})",
                total_time_ms=total_time,
                retrieval_time_ms=analysis_context.retrieval_time_ms,
                generation_time_ms=generation_time,
                confidence_score=confidence_score,
                context_relevance=analysis_context.relevance_score,
                timestamp=datetime.now(),
                model_used="enhanced_mode",
            )

            # Log performance metrics
            if self.config["enable_performance_monitoring"]:
                self._record_performance_metrics(analysis_context, enhanced_response)

            return enhanced_response

        except Exception as e:
            logger.warning("Enhanced response generation failed", error=str(e))

            # Fallback to simple response with error info
            return EnhancedResponse(
                response=base_response,
                response_type="simple",
                context_used=False,
                context_summary="Enhancement failed, using simple mode",
                total_time_ms=(time.time() - start_time) * 1000,
                retrieval_time_ms=analysis_context.retrieval_time_ms
                if analysis_context
                else 0.0,
                generation_time_ms=0.0,
                confidence_score=0.4,  # Lower confidence due to fallback
                context_relevance=0.0,
                timestamp=datetime.now(),
                model_used="fallback_mode",
                fallback_reason=str(e),
            )

    def _build_enhanced_prompt(self, query: str, context: AnalysisContext) -> str:
        """Build enhanced prompt with retrieved context."""

        context_section = f"""
## Relevant Code Context

Based on your question, here are the most relevant parts of the codebase:

{context.context_text}

## Analysis Guidelines

- Reference specific code examples from the context above when relevant
- Explain how the code context relates to the user's question
- Provide concrete examples using the actual code shown
- If the context doesn't fully answer the question, be clear about limitations
"""

        enhanced_prompt = f"""You are analyzing a codebase and helping a developer understand their code.

{context_section}

## User Question
{query}

## Response Instructions
Provide a helpful, specific answer that:
1. Uses the relevant code context shown above
2. References specific files, functions, or patterns when relevant
3. Explains concepts clearly with concrete examples
4. Acknowledges if additional context would be helpful

Response:"""

        return enhanced_prompt

    @graceful_fallback("Enhanced response generation failed")
    def _generate_enhanced_response(self, enhanced_prompt: str) -> str:
        """Generate response using enhanced prompt."""

        # Try to get the ollama client from the main application
        try:
            # This is a placeholder - in actual implementation, we'd get the client
            # from the main CodebaseAuditor instance or dependency injection
            return "Enhanced response based on retrieved context: [PLACEHOLDER - would generate with ollama client]"

        except Exception as e:
            logger.warning("Enhanced generation failed", error=str(e))
            return "Enhanced analysis temporarily unavailable."

    def _record_performance_metrics(
        self, context: AnalysisContext, response: EnhancedResponse
    ) -> None:
        """Record performance metrics for monitoring."""

        metric_data = {
            "timestamp": datetime.now().isoformat(),
            "retrieval_time_ms": context.retrieval_time_ms,
            "total_time_ms": response.total_time_ms,
            "relevance_score": context.relevance_score,
            "context_length": context.context_length,
            "num_chunks": context.num_chunks_used,
            "response_type": response.response_type,
            "confidence_score": response.confidence_score,
        }

        self._performance_metrics.append(metric_data)

        # Keep only last 1000 metrics to prevent memory bloat
        if len(self._performance_metrics) > 1000:
            self._performance_metrics = self._performance_metrics[-1000:]

    def get_performance_summary(self, hours: int = 24) -> PerformanceMetrics:
        """Get performance metrics summary for the specified time period."""

        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_metrics = [
            m
            for m in self._performance_metrics
            if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff_time
        ]

        if not recent_metrics:
            return PerformanceMetrics(
                avg_retrieval_time_ms=0.0,
                max_retrieval_time_ms=0.0,
                retrieval_success_rate=0.0,
                avg_relevance_score=0.0,
                context_hit_rate=0.0,
                enhanced_response_rate=0.0,
                fallback_rate=0.0,
                enhanced_preference_rate=0.0,
                simple_preference_rate=0.0,
                measurement_period_start=datetime.now(),
                measurement_period_end=datetime.now(),
                total_queries=0,
            )

        # Calculate metrics
        retrieval_times = [m["retrieval_time_ms"] for m in recent_metrics]
        relevance_scores = [m["relevance_score"] for m in recent_metrics]
        enhanced_responses = [
            m for m in recent_metrics if m["response_type"] == "enhanced"
        ]

        return PerformanceMetrics(
            avg_retrieval_time_ms=sum(retrieval_times) / len(retrieval_times),
            max_retrieval_time_ms=max(retrieval_times),
            retrieval_success_rate=len(enhanced_responses) / len(recent_metrics),
            avg_relevance_score=sum(relevance_scores) / len(relevance_scores),
            context_hit_rate=len([m for m in recent_metrics if m["num_chunks"] > 0])
            / len(recent_metrics),
            enhanced_response_rate=len(enhanced_responses) / len(recent_metrics),
            fallback_rate=len(
                [m for m in recent_metrics if m["response_type"] == "simple"]
            )
            / len(recent_metrics),
            enhanced_preference_rate=0.0,  # Would be filled from A/B test data
            simple_preference_rate=0.0,  # Would be filled from A/B test data
            measurement_period_start=datetime.fromisoformat(
                recent_metrics[0]["timestamp"]
            ),
            measurement_period_end=datetime.fromisoformat(
                recent_metrics[-1]["timestamp"]
            ),
            total_queries=len(recent_metrics),
        )

    def enable_ab_testing(self, enable: bool = True) -> None:
        """Enable or disable A/B testing for enhanced vs simple responses."""
        self.config["enable_ab_testing"] = enable
        logger.info("A/B testing configuration updated", enabled=enable)

    def should_use_enhanced_mode(
        self, query: str, context_available: bool = True
    ) -> bool:
        """
        Determine whether to use enhanced mode for a query.

        Uses A/B testing when enabled, otherwise uses availability-based logic.
        """

        if not context_available:
            return False

        if not self.config["enable_ab_testing"]:
            return True

        # Simple A/B test: 50/50 split based on query hash
        import hashlib

        query_hash = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        return query_hash % 2 == 0

    def record_user_preference(
        self, query: str, enhanced_response: str, simple_response: str, preference: str
    ) -> None:
        """
        Record user preference for A/B testing.

        Args:
            query: Original query
            enhanced_response: Enhanced response shown
            simple_response: Simple response shown
            preference: 'enhanced', 'simple', or 'no_preference'
        """

        preference_data = {
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query),
            "enhanced_length": len(enhanced_response),
            "simple_length": len(simple_response),
            "preference": preference,
        }

        self._ab_test_data.append(preference_data)

        # Keep only last 500 preferences
        if len(self._ab_test_data) > 500:
            self._ab_test_data = self._ab_test_data[-500:]

        logger.info("User preference recorded", preference=preference)


# Global instance for application-wide use
enhanced_analysis_integration = EnhancedAnalysisIntegration()
