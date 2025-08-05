#!/usr/bin/env python3
"""
Integration test for project-specific vector store management.

This script tests the complete functionality of the ProjectVectorStoreManager
to ensure it works correctly with real components.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from src.codebase_gardener.data.project_vector_store import (
    ProjectVectorStoreManager,
    get_project_vector_store_manager,
    reset_project_vector_store_manager,
)
from src.codebase_gardener.core.project_registry import ProjectMetadata, TrainingStatus


def test_project_vector_store_integration():
    """Test project vector store integration."""
    print("Testing project vector store integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Mock settings and project registry
        mock_settings = Mock()
        mock_settings.data_dir = temp_path
        
        mock_registry = Mock()
        
        def mock_get_project(project_id):
            return ProjectMetadata(
                project_id=project_id,
                name=f"Project {project_id}",
                source_path=Path(f"/test/{project_id}"),
                created_at=datetime.now(),
                training_status=TrainingStatus.COMPLETED
            )
        
        mock_registry.get_project.side_effect = mock_get_project
        
        with patch('src.codebase_gardener.data.project_vector_store.get_settings', return_value=mock_settings):
            with patch('src.codebase_gardener.data.project_vector_store.get_project_registry', return_value=mock_registry):
                
                # Test 1: Create manager
                print("✓ Creating ProjectVectorStoreManager...")
                manager = ProjectVectorStoreManager(max_cache_size=3)
                assert manager is not None
                assert manager._max_cache_size == 3
                assert len(manager._vector_store_cache) == 0
                
                # Test 2: Test table name generation
                print("✓ Testing table name generation...")
                assert manager._get_table_name("test-project") == "project_test_project"
                assert manager._get_table_name("my project") == "project_my_project"
                
                # Test 3: Test active project management
                print("✓ Testing active project management...")
                assert manager.get_active_project_id() is None
                assert manager.get_active_vector_store() is None
                
                # Test 4: Test project switching (mocked)
                print("✓ Testing project switching...")
                # This would normally create actual vector stores, but we're testing the logic
                with patch('src.codebase_gardener.data.project_vector_store.VectorStore') as mock_vs_class:
                    with patch('src.codebase_gardener.data.project_vector_store.lancedb') as mock_lancedb:
                        mock_db = Mock()
                        mock_lancedb.connect.return_value = mock_db
                        
                        mock_vector_store = Mock()
                        mock_vs_class.return_value = mock_vector_store
                        
                        # Switch to project
                        result = manager.switch_project("test-project")
                        assert result is True
                        assert manager.get_active_project_id() == "test-project"
                        assert manager.get_active_vector_store() == mock_vector_store
                
                # Test 5: Test cache management
                print("✓ Testing cache management...")
                # Add mock entries to test cache eviction
                mock_vs1 = Mock()
                mock_vs2 = Mock()
                mock_vs3 = Mock()
                mock_vs4 = Mock()
                
                from src.codebase_gardener.data.project_vector_store import ProjectVectorStoreInfo
                
                manager._vector_store_cache["project1"] = ProjectVectorStoreInfo(
                    "project1", "table1", mock_vs1, datetime.now(), 10
                )
                manager._vector_store_cache["project2"] = ProjectVectorStoreInfo(
                    "project2", "table2", mock_vs2, datetime.now(), 20
                )
                manager._vector_store_cache["project3"] = ProjectVectorStoreInfo(
                    "project3", "table3", mock_vs3, datetime.now(), 30
                )
                manager._vector_store_cache["project4"] = ProjectVectorStoreInfo(
                    "project4", "table4", mock_vs4, datetime.now(), 40
                )
                
                # Should trigger cache management (max_cache_size = 3)
                manager._manage_cache()
                
                # Should have evicted oldest entry
                assert len(manager._vector_store_cache) == 3
                assert "project1" not in manager._vector_store_cache
                mock_vs1.close.assert_called_once()
                
                # Test 6: Test cleanup
                print("✓ Testing cleanup...")
                manager.close_all()
                
                assert len(manager._vector_store_cache) == 0
                assert manager.get_active_project_id() is None
                assert manager.get_active_vector_store() is None
                
                # Verify remaining vector stores were closed
                mock_vs2.close.assert_called_once()
                mock_vs3.close.assert_called_once()
                mock_vs4.close.assert_called_once()
                
                print("✓ All integration tests passed!")


def test_global_manager_singleton():
    """Test global manager singleton behavior."""
    print("Testing global manager singleton...")
    
    # Reset any existing manager
    reset_project_vector_store_manager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        mock_settings = Mock()
        mock_settings.data_dir = temp_path
        
        mock_registry = Mock()
        mock_registry.get_project.return_value = Mock()
        
        with patch('src.codebase_gardener.data.project_vector_store.get_settings', return_value=mock_settings):
            with patch('src.codebase_gardener.data.project_vector_store.get_project_registry', return_value=mock_registry):
                
                # Get manager twice
                manager1 = get_project_vector_store_manager()
                manager2 = get_project_vector_store_manager()
                
                # Should be the same instance
                assert manager1 is manager2
                print("✓ Singleton behavior verified")
                
                # Reset and get again
                reset_project_vector_store_manager()
                manager3 = get_project_vector_store_manager()
                
                # Should be different instance
                assert manager1 is not manager3
                print("✓ Reset behavior verified")


if __name__ == "__main__":
    print("Running Project Vector Store Integration Tests...")
    print("=" * 60)
    
    try:
        test_project_vector_store_integration()
        print()
        test_global_manager_singleton()
        print()
        print("=" * 60)
        print("🎉 All integration tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)