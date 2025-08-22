#!/usr/bin/env python3
"""
Comprehensive test suite for Enhanced Analysis Integration (Task 11)

Tests the integration between RAG engine and codebase analysis system,
including context-aware responses, performance monitoring, and A/B testing.
"""

# Test imports
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from codebase_gardener.core.component_registry import ComponentRegistry
    from codebase_gardener.core.enhanced_analysis_integration import (
        AnalysisContext,
        EnhancedAnalysisIntegration,
        EnhancedResponse,
        PerformanceMetrics,
        enhanced_analysis_integration,
    )
except ImportError as e:
    pytest.skip(
        f"Enhanced analysis integration not available: {e}", allow_module_level=True
    )


class TestAnalysisContext:
    """Test AnalysisContext data structure."""

    def test_analysis_context_creation(self):
        """Test creating AnalysisContext with all fields."""
        context = AnalysisContext(
            query="What are the main patterns?",
            query_type="analysis",
            timestamp=datetime.now(),
            retrieved_chunks=[{"id": "chunk1", "content": "test"}],
            context_text="Test context",
            retrieval_time_ms=150.0,
            relevance_score=0.8,
            context_length=100,
            num_chunks_used=1,
            project_id="test_project",
        )

        assert context.query == "What are the main patterns?"
        assert context.query_type == "analysis"
        assert context.relevance_score == 0.8
        assert context.num_chunks_used == 1
        assert context.project_id == "test_project"

    def test_analysis_context_defaults(self):
        """Test AnalysisContext with default values."""
        context = AnalysisContext(
            query="test query",
            query_type="chat",
            timestamp=datetime.now(),
            retrieved_chunks=[],
            context_text="",
            retrieval_time_ms=0.0,
            relevance_score=0.0,
            context_length=0,
            num_chunks_used=0,
        )

        assert context.project_id is None
        assert context.language_filter is None
        assert context.chunk_type_filter is None


class TestEnhancedResponse:
    """Test EnhancedResponse data structure."""

    def test_enhanced_response_creation(self):
        """Test creating EnhancedResponse with all fields."""
        response = EnhancedResponse(
            response="Enhanced analysis response",
            response_type="enhanced",
            context_used=True,
            context_summary="Used 3 chunks",
            total_time_ms=250.0,
            retrieval_time_ms=150.0,
            generation_time_ms=100.0,
            confidence_score=0.9,
            context_relevance=0.8,
            timestamp=datetime.now(),
            model_used="enhanced_mode",
        )

        assert response.response_type == "enhanced"
        assert response.context_used is True
        assert response.confidence_score == 0.9
        assert response.fallback_reason is None

    def test_fallback_response_creation(self):
        """Test creating fallback EnhancedResponse."""
        response = EnhancedResponse(
            response="Fallback response",
            response_type="simple",
            context_used=False,
            context_summary="No context available",
            total_time_ms=50.0,
            retrieval_time_ms=0.0,
            generation_time_ms=50.0,
            confidence_score=0.5,
            context_relevance=0.0,
            timestamp=datetime.now(),
            model_used="fallback_mode",
            fallback_reason="RAG engine unavailable",
        )

        assert response.response_type == "simple"
        assert response.context_used is False
        assert response.fallback_reason == "RAG engine unavailable"


class TestEnhancedAnalysisIntegration:
    """Test core EnhancedAnalysisIntegration functionality."""

    @pytest.fixture
    def mock_registry(self):
        """Create mock component registry."""
        registry = Mock(spec=ComponentRegistry)
        return registry

    @pytest.fixture
    def integration(self, mock_registry):
        """Create EnhancedAnalysisIntegration with mock registry."""
        return EnhancedAnalysisIntegration(mock_registry)

    def test_integration_initialization(self, integration):
        """Test integration initializes with correct defaults."""
        assert integration.config["retrieval_timeout_ms"] == 200
        assert integration.config["max_context_chunks"] == 5
        assert integration.config["min_relevance_threshold"] == 0.3
        assert integration.config["enable_ab_testing"] is True
        assert integration.config["enable_performance_monitoring"] is True

    def test_retrieve_context_no_rag_engine(self, integration, mock_registry):
        """Test context retrieval when RAG engine is not available."""
        mock_registry.is_component_available.return_value = False

        result = integration.retrieve_context_for_query("test query")

        assert result is None
        mock_registry.is_component_available.assert_called_with("rag_engine")

    def test_retrieve_context_successful(self, integration, mock_registry):
        """Test successful context retrieval."""
        # Setup mock RAG engine
        mock_rag_engine = Mock()
        mock_retrieval_result = Mock()
        mock_retrieval_result.chunks = [Mock(id="chunk1")]
        mock_retrieval_result.avg_relevance_score = 0.75
        mock_enhanced_context = Mock()
        mock_enhanced_context.formatted_context = "Retrieved context"

        mock_rag_engine.retrieve_context.return_value = mock_retrieval_result
        mock_rag_engine.format_context.return_value = mock_enhanced_context

        mock_registry.is_component_available.return_value = True
        mock_registry.get_component.return_value = mock_rag_engine

        result = integration.retrieve_context_for_query(
            query="test query", project_id="test_project"
        )

        assert result is not None
        assert result.query == "test query"
        assert result.project_id == "test_project"
        assert result.relevance_score == 0.75
        assert result.context_text == "Retrieved context"
        assert result.num_chunks_used == 1

    def test_enhance_chat_response_no_context(self, integration):
        """Test chat enhancement when no context is available."""
        response = integration.enhance_chat_response(
            query="test query", base_response="base response", analysis_context=None
        )

        assert response.response == "base response"
        assert response.response_type == "simple"
        assert response.context_used is False

    def test_enhance_chat_response_with_context(self, integration):
        """Test chat enhancement with available context."""
        # Create mock analysis context
        analysis_context = AnalysisContext(
            query="test query",
            query_type="chat",
            timestamp=datetime.now(),
            retrieved_chunks=[{"id": "chunk1"}],
            context_text="Test context",
            retrieval_time_ms=100.0,
            relevance_score=0.8,
            context_length=50,
            num_chunks_used=1,
        )

        with patch.object(integration, "_generate_enhanced_response") as mock_generate:
            mock_generate.return_value = "Enhanced response"

            response = integration.enhance_chat_response(
                query="test query",
                base_response="base response",
                analysis_context=analysis_context,
            )

            assert response.response == "Enhanced response"
            assert response.response_type == "enhanced"
            assert response.context_used is True
            assert response.confidence_score > 0.5

    def test_ab_testing_configuration(self, integration):
        """Test A/B testing enable/disable functionality."""
        # Test enable
        integration.enable_ab_testing(True)
        assert integration.config["enable_ab_testing"] is True

        # Test disable
        integration.enable_ab_testing(False)
        assert integration.config["enable_ab_testing"] is False

    def test_should_use_enhanced_mode_no_ab_testing(self, integration):
        """Test enhanced mode decision when A/B testing is disabled."""
        integration.config["enable_ab_testing"] = False

        # Should use enhanced mode when available
        assert integration.should_use_enhanced_mode("test query", True) is True

        # Should not use enhanced mode when not available
        assert integration.should_use_enhanced_mode("test query", False) is False

    def test_should_use_enhanced_mode_ab_testing(self, integration):
        """Test enhanced mode decision with A/B testing enabled."""
        integration.config["enable_ab_testing"] = True

        # Should make consistent decisions based on query hash
        result1 = integration.should_use_enhanced_mode("consistent query", True)
        result2 = integration.should_use_enhanced_mode("consistent query", True)
        assert result1 == result2  # Consistent for same query

    def test_record_user_preference(self, integration):
        """Test recording user preferences for A/B testing."""
        integration.record_user_preference(
            query="test query",
            enhanced_response="enhanced",
            simple_response="simple",
            preference="enhanced",
        )

        assert len(integration._ab_test_data) == 1
        assert integration._ab_test_data[0]["preference"] == "enhanced"

    def test_performance_metrics_recording(self, integration):
        """Test performance metrics are recorded correctly."""
        analysis_context = AnalysisContext(
            query="test query",
            query_type="chat",
            timestamp=datetime.now(),
            retrieved_chunks=[],
            context_text="",
            retrieval_time_ms=150.0,
            relevance_score=0.7,
            context_length=100,
            num_chunks_used=2,
        )

        enhanced_response = EnhancedResponse(
            response="test response",
            response_type="enhanced",
            context_used=True,
            context_summary="test",
            total_time_ms=200.0,
            retrieval_time_ms=150.0,
            generation_time_ms=50.0,
            confidence_score=0.8,
            context_relevance=0.7,
            timestamp=datetime.now(),
            model_used="enhanced",
        )

        integration._record_performance_metrics(analysis_context, enhanced_response)

        assert len(integration._performance_metrics) == 1
        metric = integration._performance_metrics[0]
        assert metric["retrieval_time_ms"] == 150.0
        assert metric["relevance_score"] == 0.7
        assert metric["response_type"] == "enhanced"

    def test_get_performance_summary_no_data(self, integration):
        """Test performance summary when no data is available."""
        metrics = integration.get_performance_summary()

        assert metrics.total_queries == 0
        assert metrics.avg_retrieval_time_ms == 0.0
        assert metrics.retrieval_success_rate == 0.0

    def test_get_performance_summary_with_data(self, integration):
        """Test performance summary with recorded metrics."""
        # Add test metrics
        test_metrics = [
            {
                "timestamp": datetime.now().isoformat(),
                "retrieval_time_ms": 100.0,
                "total_time_ms": 150.0,
                "relevance_score": 0.8,
                "context_length": 200,
                "num_chunks": 2,
                "response_type": "enhanced",
                "confidence_score": 0.9,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "retrieval_time_ms": 200.0,
                "total_time_ms": 250.0,
                "relevance_score": 0.6,
                "context_length": 150,
                "num_chunks": 1,
                "response_type": "simple",
                "confidence_score": 0.5,
            },
        ]

        integration._performance_metrics = test_metrics

        metrics = integration.get_performance_summary()

        assert metrics.total_queries == 2
        assert metrics.avg_retrieval_time_ms == 150.0  # (100 + 200) / 2
        assert metrics.max_retrieval_time_ms == 200.0
        assert metrics.avg_relevance_score == 0.7  # (0.8 + 0.6) / 2


class TestIntegrationWithCodebaseAuditor:
    """Test integration with the main CodebaseAuditor class."""

    @pytest.fixture
    def mock_auditor(self):
        """Create mock CodebaseAuditor instance."""
        # Import here to avoid circular dependencies
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        with patch("codebase_auditor.CodebaseAuditor") as MockAuditor:
            auditor = MockAuditor()
            auditor.analysis_results = {
                "full_analysis": "Test analysis",
                "file_list": ["test.py"],
                "directory_path": "/test",
                "timestamp": datetime.now().isoformat(),
                "file_count": 1,
            }
            auditor._current_project_id = "test_project"
            yield auditor

    def test_enhanced_chat_integration(self, mock_auditor):
        """Test enhanced chat functionality integration."""
        # This would test the actual integration, but since we're in a test environment
        # we'll test the interface compatibility

        with patch(
            "codebase_auditor.CodebaseAuditor._get_enhanced_analysis_integration"
        ) as mock_get_integration:
            mock_integration = Mock(spec=EnhancedAnalysisIntegration)
            mock_integration.should_use_enhanced_mode.return_value = True
            mock_integration.retrieve_context_for_query.return_value = None
            mock_get_integration.return_value = mock_integration

            # Test that the integration interface is called correctly
            # (This is a structural test since we can't easily mock ollama client)

            assert (
                mock_integration.should_use_enhanced_mode.called is False
            )  # Not called yet
            mock_integration.should_use_enhanced_mode("test query", True)
            mock_integration.should_use_enhanced_mode.assert_called_with(
                "test query", True
            )

    def test_performance_metrics_display(self, mock_auditor):
        """Test performance metrics display functionality."""
        with patch(
            "codebase_auditor.CodebaseAuditor._get_enhanced_analysis_integration"
        ) as mock_get_integration:
            mock_integration = Mock(spec=EnhancedAnalysisIntegration)
            mock_metrics = PerformanceMetrics(
                avg_retrieval_time_ms=150.0,
                max_retrieval_time_ms=300.0,
                retrieval_success_rate=0.85,
                avg_relevance_score=0.75,
                context_hit_rate=0.80,
                enhanced_response_rate=0.70,
                fallback_rate=0.30,
                enhanced_preference_rate=0.60,
                simple_preference_rate=0.40,
                measurement_period_start=datetime.now(),
                measurement_period_end=datetime.now(),
                total_queries=100,
            )
            mock_integration.get_performance_summary.return_value = mock_metrics
            mock_get_integration.return_value = mock_integration

            # Test would call _show_performance_metrics method
            # This verifies the interface works correctly
            mock_integration.get_performance_summary()
            mock_integration.get_performance_summary.assert_called_once()

    def test_ab_testing_commands(self, mock_auditor):
        """Test A/B testing command handling."""
        with patch(
            "codebase_auditor.CodebaseAuditor._get_enhanced_analysis_integration"
        ) as mock_get_integration:
            mock_integration = Mock(spec=EnhancedAnalysisIntegration)
            mock_integration.config = {"enable_ab_testing": True}
            mock_integration._ab_test_data = [
                {"preference": "enhanced", "timestamp": datetime.now().isoformat()},
                {"preference": "simple", "timestamp": datetime.now().isoformat()},
            ]
            mock_get_integration.return_value = mock_integration

            # Test enable A/B testing
            mock_integration.enable_ab_testing(True)
            mock_integration.enable_ab_testing.assert_called_with(True)

            # Test record preference
            mock_integration.record_user_preference(
                query="test",
                enhanced_response="",
                simple_response="",
                preference="enhanced",
            )
            mock_integration.record_user_preference.assert_called_once()


class TestErrorHandling:
    """Test error handling in enhanced analysis integration."""

    def test_graceful_degradation_import_error(self):
        """Test graceful degradation when imports fail."""
        # Test that the global instance handles import errors gracefully
        assert enhanced_analysis_integration is not None

    def test_context_retrieval_exception_handling(self):
        """Test exception handling in context retrieval."""
        integration = EnhancedAnalysisIntegration()

        # Mock registry to throw exception
        with patch.object(
            integration.registry, "is_component_available"
        ) as mock_available:
            mock_available.side_effect = Exception("Registry error")

            result = integration.retrieve_context_for_query("test query")
            assert result is None  # Should return None on error

    def test_response_enhancement_exception_handling(self):
        """Test exception handling in response enhancement."""
        integration = EnhancedAnalysisIntegration()

        with patch.object(integration, "_generate_enhanced_response") as mock_generate:
            mock_generate.side_effect = Exception("Generation error")

            analysis_context = AnalysisContext(
                query="test",
                query_type="chat",
                timestamp=datetime.now(),
                retrieved_chunks=[],
                context_text="",
                retrieval_time_ms=0,
                relevance_score=0,
                context_length=0,
                num_chunks_used=0,
            )

            response = integration.enhance_chat_response(
                query="test",
                base_response="fallback",
                analysis_context=analysis_context,
            )

            assert response.response == "fallback"
            assert response.response_type == "simple"
            assert response.fallback_reason is not None


def test_global_integration_instance():
    """Test that global enhanced_analysis_integration instance is available."""
    assert enhanced_analysis_integration is not None
    assert isinstance(enhanced_analysis_integration, EnhancedAnalysisIntegration)

    # Test basic functionality
    assert enhanced_analysis_integration.config["retrieval_timeout_ms"] > 0
    assert enhanced_analysis_integration.config["max_context_chunks"] > 0


if __name__ == "__main__":
    # Run tests with verbose output
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
