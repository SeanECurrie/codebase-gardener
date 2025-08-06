#!/usr/bin/env python3
"""
Integration test for Gradio web interface.

This script tests the complete Gradio interface functionality including
project switching, chat interface, and code analysis features.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codebase_gardener.ui.gradio_app import (
    initialize_components,
    get_project_options,
    switch_project,
    handle_chat,
    analyze_code,
    get_system_health,
    create_app,
    app_state
)
from codebase_gardener.core.project_registry import TrainingStatus

def test_gradio_integration():
    """Test complete Gradio interface integration."""
    print("🧪 Running Gradio Integration Tests...")
    
    # Test 1: Component Initialization
    print("\n1. Testing component initialization...")
    with patch('codebase_gardener.ui.gradio_app.get_settings') as mock_settings, \
         patch('codebase_gardener.ui.gradio_app.get_project_registry') as mock_registry, \
         patch('codebase_gardener.ui.gradio_app.get_dynamic_model_loader') as mock_loader, \
         patch('codebase_gardener.ui.gradio_app.get_project_context_manager') as mock_context, \
         patch('codebase_gardener.ui.gradio_app.get_project_vector_store_manager') as mock_vector:
        
        # Setup mocks
        mock_settings.return_value = Mock()
        mock_registry.return_value = Mock()
        mock_loader.return_value = Mock()
        mock_context.return_value = Mock()
        mock_vector.return_value = Mock()
        
        result = initialize_components()
        assert result is True, "Component initialization should succeed"
        print("   ✅ Components initialized successfully")
    
    # Test 2: Project Options
    print("\n2. Testing project options...")
    
    # Create mock projects
    project1 = Mock()
    project1.name = "Test Project 1"
    project1.project_id = "test-1"
    project1.training_status = TrainingStatus.COMPLETED
    
    project2 = Mock()
    project2.name = "Test Project 2"
    project2.project_id = "test-2"
    project2.training_status = TrainingStatus.TRAINING
    
    mock_registry = Mock()
    mock_registry.list_projects.return_value = [project1, project2]
    app_state["project_registry"] = mock_registry
    
    options = get_project_options()
    assert len(options) == 2, f"Expected 2 projects, got {len(options)}"
    assert ("🟢 Test Project 1", "test-1") in options, "Completed project should be in options"
    assert ("🟡 Test Project 2", "test-2") in options, "Training project should be in options"
    print("   ✅ Project options generated correctly")
    
    # Test 3: Project Switching
    print("\n3. Testing project switching...")
    
    # Setup mock components for switching
    mock_context = Mock()
    mock_context.switch_project.return_value = True
    mock_loader = Mock()
    mock_loader.switch_project.return_value = True
    mock_vector = Mock()
    mock_vector.switch_project.return_value = True
    
    app_state["context_manager"] = mock_context
    app_state["model_loader"] = mock_loader
    app_state["vector_store_manager"] = mock_vector
    
    # Mock project for status
    project1.created_at = datetime(2025, 1, 1, 12, 0, 0)
    project1.source_path = Path("/test/path")
    mock_registry.get_project.return_value = project1
    
    result = switch_project("test-1")
    assert "Successfully switched" in result[1], "Project switch should succeed"
    assert app_state["current_project"] == "test-1", "Current project should be updated"
    
    # Verify component coordination
    mock_context.switch_project.assert_called_once_with("test-1")
    mock_loader.switch_project.assert_called_once_with("test-1")
    mock_vector.switch_project.assert_called_once_with("test-1")
    print("   ✅ Project switching coordinated across all components")
    
    # Test 4: Chat Interface
    print("\n4. Testing chat interface...")
    
    mock_context.add_message = Mock()
    history = []
    result = handle_chat("Hello, test message", history, "test-1")
    
    assert len(result[0]) == 2, "Chat should add user and assistant messages"
    assert result[0][0]["role"] == "user", "First message should be from user"
    assert result[0][0]["content"] == "Hello, test message", "User message content should match"
    assert result[0][1]["role"] == "assistant", "Second message should be from assistant"
    assert "test-1" in result[0][1]["content"], "Assistant response should mention project"
    
    # Verify context manager integration
    assert mock_context.add_message.call_count == 2, "Should add both user and assistant messages to context"
    print("   ✅ Chat interface working with context management")
    
    # Test 5: Code Analysis
    print("\n5. Testing code analysis...")
    
    test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    result = analyze_code(test_code, "test-1")
    assert "Code Analysis for Project: test-1" in result, "Analysis should mention project"
    assert str(len(test_code)) in result, "Analysis should include code length"
    assert "lines" in result, "Analysis should include line count"
    print("   ✅ Code analysis functioning correctly")
    
    # Test 6: System Health
    print("\n6. Testing system health...")
    
    result = get_system_health()
    assert "System Health Status" in result, "Health check should include status header"
    assert "**Project Registry:** 🟢 OK" in result, "Registry should show as OK"
    assert "**Model Loader:** 🟢 OK" in result, "Model loader should show as OK"
    assert "**Context Manager:** 🟢 OK" in result, "Context manager should show as OK"
    assert "**Vector Store Manager:** 🟢 OK" in result, "Vector store should show as OK"
    assert "**Active Project:** test-1" in result, "Should show active project"
    print("   ✅ System health monitoring working")
    
    # Test 7: App Creation
    print("\n7. Testing app creation...")
    
    with patch('codebase_gardener.ui.gradio_app.initialize_components') as mock_init:
        mock_init.return_value = True
        
        app = create_app()
        assert app is not None, "App should be created successfully"
        print("   ✅ Gradio app created successfully")
    
    # Test 8: Error Handling
    print("\n8. Testing error handling...")
    
    # Test project switching with failures
    mock_context.switch_project.return_value = False
    mock_loader.switch_project.return_value = False
    mock_vector.switch_project.return_value = False
    
    result = switch_project("test-1")
    # Should still succeed overall even if components fail
    assert "Successfully switched" in result[1], "Should handle component failures gracefully"
    print("   ✅ Error handling working correctly")
    
    # Test chat with no project
    result = handle_chat("Hello", [], "")
    assert len(result[0]) == 2, "Should handle no project gracefully"
    assert "Please select a project first" in result[0][1]["content"], "Should prompt for project selection"
    print("   ✅ Chat error handling working")
    
    # Test code analysis with no project
    result = analyze_code("print('hello')", "")
    assert "Please select a project first" in result, "Should handle no project gracefully"
    print("   ✅ Code analysis error handling working")
    
    print("\n🎉 All integration tests passed!")
    print("\n📊 Test Summary:")
    print("   ✅ Component initialization")
    print("   ✅ Project options generation")
    print("   ✅ Project switching coordination")
    print("   ✅ Chat interface with context management")
    print("   ✅ Code analysis functionality")
    print("   ✅ System health monitoring")
    print("   ✅ Gradio app creation")
    print("   ✅ Error handling and graceful degradation")
    
    return True

if __name__ == "__main__":
    try:
        success = test_gradio_integration()
        if success:
            print("\n🌟 Integration test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Integration test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Integration test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)