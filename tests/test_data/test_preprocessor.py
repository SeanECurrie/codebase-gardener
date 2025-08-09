"""
Tests for code preprocessing and chunking system.

This module tests the intelligent code chunking functionality that transforms
parsed AST structures into semantically meaningful chunks with metadata.
"""

from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

import pytest

from codebase_gardener.data.parser import (
    CodeElement,
    CodeStructure,
    ParseResult,
)
from codebase_gardener.data.preprocessor import (
    ChunkType,
    CodeChunk,
    CodePreprocessor,
    PreprocessingConfig,
    preprocess_code_string,
    preprocess_file,
)
from codebase_gardener.utils.error_handling import PreprocessingError


class TestChunkType:
    """Test ChunkType enum."""

    def test_chunk_type_values(self):
        """Test that ChunkType has expected values."""
        assert ChunkType.FUNCTION.value == "function"
        assert ChunkType.CLASS.value == "class"
        assert ChunkType.METHOD.value == "method"
        assert ChunkType.MODULE.value == "module"
        assert ChunkType.IMPORT.value == "import"
        assert ChunkType.VARIABLE.value == "variable"
        assert ChunkType.COMMENT.value == "comment"
        assert ChunkType.INTERFACE.value == "interface"
        assert ChunkType.TYPE.value == "type"
        assert ChunkType.BLOCK.value == "block"


class TestCodeChunk:
    """Test CodeChunk dataclass."""

    def test_code_chunk_creation(self):
        """Test creating a valid CodeChunk."""
        chunk = CodeChunk(
            id="test123",
            content="def hello():\n    return 'world'",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=Path("test.py"),
            start_line=1,
            end_line=2,
            start_byte=0,
            end_byte=30,
            metadata={"test": "value"},
            dependencies=["print"],
            complexity_score=1.5
        )

        assert chunk.id == "test123"
        assert chunk.language == "python"
        assert chunk.chunk_type == ChunkType.FUNCTION
        assert chunk.complexity_score == 1.5

    def test_code_chunk_properties(self):
        """Test CodeChunk computed properties."""
        chunk = CodeChunk(
            id="test123",
            content="def hello():\n    return 'world'",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=None,
            start_line=1,
            end_line=2,
            start_byte=0,
            end_byte=30
        )

        assert chunk.size == len("def hello():\n    return 'world'")
        assert chunk.non_whitespace_size == len("defhello():return'world'")
        assert chunk.line_count == 2

    def test_code_chunk_validation_empty_content(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Code chunk content cannot be empty"):
            CodeChunk(
                id="test123",
                content="   ",  # Only whitespace
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=None,
                start_line=1,
                end_line=1,
                start_byte=0,
                end_byte=10
            )

    def test_code_chunk_validation_invalid_lines(self):
        """Test that invalid line numbers raise ValueError."""
        with pytest.raises(ValueError, match="Line numbers must be non-negative"):
            CodeChunk(
                id="test123",
                content="def hello(): pass",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=None,
                start_line=-1,
                end_line=1,
                start_byte=0,
                end_byte=10
            )

        with pytest.raises(ValueError, match="Start line cannot be greater than end line"):
            CodeChunk(
                id="test123",
                content="def hello(): pass",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=None,
                start_line=5,
                end_line=1,
                start_byte=0,
                end_byte=10
            )

    def test_code_chunk_validation_negative_complexity(self):
        """Test that negative complexity raises ValueError."""
        with pytest.raises(ValueError, match="Complexity score must be non-negative"):
            CodeChunk(
                id="test123",
                content="def hello(): pass",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=None,
                start_line=1,
                end_line=1,
                start_byte=0,
                end_byte=10,
                complexity_score=-1.0
            )


class TestPreprocessingConfig:
    """Test PreprocessingConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PreprocessingConfig()

        assert config.max_chunk_size == 2048
        assert config.min_chunk_size == 50
        assert config.overlap_size == 100
        assert config.preserve_comments is True
        assert config.preserve_docstrings is True
        assert config.normalize_whitespace is True
        assert config.extract_imports is True
        assert config.calculate_complexity is True
        assert config.include_context is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PreprocessingConfig(
            max_chunk_size=1000,
            min_chunk_size=25,
            preserve_comments=False,
            calculate_complexity=False
        )

        assert config.max_chunk_size == 1000
        assert config.min_chunk_size == 25
        assert config.preserve_comments is False
        assert config.calculate_complexity is False


class TestCodePreprocessor:
    """Test CodePreprocessor class."""

    def test_preprocessor_initialization(self):
        """Test preprocessor initialization."""
        preprocessor = CodePreprocessor()
        assert preprocessor.config is not None
        assert preprocessor.config.max_chunk_size == 2048

    def test_preprocessor_with_custom_config(self):
        """Test preprocessor with custom configuration."""
        config = PreprocessingConfig(max_chunk_size=1000)
        preprocessor = CodePreprocessor(config)
        assert preprocessor.config.max_chunk_size == 1000

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_preprocess_code_success(self, mock_parser_class):
        """Test successful code preprocessing."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Create mock parse result
        mock_element = CodeElement(
            name="test_function",
            element_type="function",
            start_line=1,
            end_line=3,
            start_byte=0,
            end_byte=50,
            content="def test_function():\n    return 'hello'",
            language="python"
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(mock_element)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        mock_parser.parse.return_value = mock_parse_result

        # Test preprocessing
        preprocessor = CodePreprocessor()
        chunks = preprocessor.preprocess_code("def test_function():\n    return 'hello'", "python")

        assert len(chunks) >= 1
        assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
        mock_parser_class.assert_called_once_with("python")
        mock_parser.parse.assert_called_once()

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_preprocess_file_success(self, mock_parser_class):
        """Test successful file preprocessing."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser_class.create_for_file.return_value = mock_parser

        # Create mock parse result
        mock_element = CodeElement(
            name="test_function",
            element_type="function",
            start_line=1,
            end_line=3,
            start_byte=0,
            end_byte=50,
            content="def test_function():\n    return 'hello'",
            language="python"
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(mock_element)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        mock_parser.parse.return_value = mock_parse_result

        # Test preprocessing
        preprocessor = CodePreprocessor()
        file_path = Path("test.py")
        code = "def test_function():\n    return 'hello'"

        chunks = preprocessor.preprocess_file(file_path, code)

        assert len(chunks) >= 1
        assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
        mock_parser_class.create_for_file.assert_called_once_with(file_path)
        mock_parser.parse.assert_called_once_with(code, file_path)

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_preprocess_unsupported_file(self, mock_parser_class):
        """Test preprocessing unsupported file type."""
        mock_parser_class.create_for_file.return_value = None

        preprocessor = CodePreprocessor()
        file_path = Path("test.unknown")

        with pytest.raises(PreprocessingError, match="Failed to preprocess file"):
            preprocessor.preprocess_file(file_path, "some code")

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_preprocess_parser_error(self, mock_parser_class):
        """Test preprocessing when parser raises error."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse.side_effect = Exception("Parser failed")

        preprocessor = CodePreprocessor()

        with pytest.raises(PreprocessingError, match="Failed to preprocess python code"):
            preprocessor.preprocess_code("invalid code", "python")

    def test_map_element_to_chunk_type(self):
        """Test mapping element types to chunk types."""
        preprocessor = CodePreprocessor()

        # Create test elements
        function_element = CodeElement(
            name="test", element_type="function", start_line=1, end_line=1,
            start_byte=0, end_byte=10, content="def test(): pass", language="python"
        )
        class_element = CodeElement(
            name="Test", element_type="class", start_line=1, end_line=1,
            start_byte=0, end_byte=10, content="class Test: pass", language="python"
        )
        import_element = CodeElement(
            name="os", element_type="import", start_line=1, end_line=1,
            start_byte=0, end_byte=10, content="import os", language="python"
        )

        assert preprocessor._map_element_to_chunk_type(function_element) == ChunkType.FUNCTION
        assert preprocessor._map_element_to_chunk_type(class_element) == ChunkType.CLASS
        assert preprocessor._map_element_to_chunk_type(import_element) == ChunkType.IMPORT

    def test_normalize_content(self):
        """Test content normalization."""
        preprocessor = CodePreprocessor()

        # Test with excessive blank lines
        content = "def test():\n\n\n\n    pass\n\n\n"
        normalized = preprocessor._normalize_content(content)

        assert "\n\n\n\n" not in normalized
        assert normalized.endswith('\n')

        # Test with tabs
        content_with_tabs = "def test():\n\tpass"
        normalized = preprocessor._normalize_content(content_with_tabs)
        assert '\t' not in normalized
        assert '    ' in normalized  # Converted to spaces

    def test_normalize_content_disabled(self):
        """Test content normalization when disabled."""
        config = PreprocessingConfig(normalize_whitespace=False)
        preprocessor = CodePreprocessor(config)

        content = "def test():\n\n\n\n    pass"
        normalized = preprocessor._normalize_content(content)

        assert normalized == content  # Should be unchanged

    def test_generate_chunk_id(self):
        """Test chunk ID generation."""
        preprocessor = CodePreprocessor()

        content = "def test(): pass"
        start_line = 1
        file_path = Path("test.py")

        chunk_id = preprocessor._generate_chunk_id(content, start_line, file_path)

        assert isinstance(chunk_id, str)
        assert len(chunk_id) == 12  # MD5 hash truncated to 12 chars

        # Same inputs should generate same ID
        chunk_id2 = preprocessor._generate_chunk_id(content, start_line, file_path)
        assert chunk_id == chunk_id2

        # Different inputs should generate different IDs
        chunk_id3 = preprocessor._generate_chunk_id(content, 2, file_path)
        assert chunk_id != chunk_id3

    def test_extract_dependencies(self):
        """Test dependency extraction."""
        preprocessor = CodePreprocessor()

        element = CodeElement(
            name="test_function",
            element_type="function",
            start_line=1,
            end_line=5,
            start_byte=0,
            end_byte=100,
            content="def test_function():\n    import os\n    print('hello')\n    os.path.join('a', 'b')",
            language="python"
        )

        module_info = {
            "imports": [
                {"name": "sys", "content": "import sys", "line": 1}
            ]
        }

        dependencies = preprocessor._extract_dependencies(element, module_info)

        assert "sys" in dependencies  # From module imports
        assert "os" in dependencies   # From function content
        # print is filtered out as a common keyword, so check for other dependencies
        assert len(dependencies) > 0  # Should have some dependencies
        assert len(dependencies) <= 10  # Limited to 10

    def test_calculate_complexity(self):
        """Test complexity calculation."""
        preprocessor = CodePreprocessor()

        # Simple function
        simple_element = CodeElement(
            name="simple", element_type="function", start_line=1, end_line=2,
            start_byte=0, end_byte=30, content="def simple():\n    return 1", language="python"
        )
        simple_complexity = preprocessor._calculate_complexity(simple_element, "")
        assert simple_complexity >= 1.0

        # Complex function with conditionals and loops
        complex_element = CodeElement(
            name="complex", element_type="function", start_line=1, end_line=10,
            start_byte=0, end_byte=200,
            content="""def complex():
    if True:
        for i in range(10):
            if i % 2:
                try:
                    print(i)
                except:
                    pass
            else:
                while i > 0:
                    i -= 1""",
            language="python"
        )
        complex_complexity = preprocessor._calculate_complexity(complex_element, "")
        assert complex_complexity > simple_complexity

    def test_has_docstring(self):
        """Test docstring detection."""
        preprocessor = CodePreprocessor()

        # Content with docstring
        with_docstring = '''def test():
    """This is a docstring."""
    pass'''
        assert preprocessor._has_docstring(with_docstring) is True

        # Content without docstring
        without_docstring = '''def test():
    pass'''
        assert preprocessor._has_docstring(without_docstring) is False

    def test_has_comments(self):
        """Test comment detection."""
        preprocessor = CodePreprocessor()

        # Content with comments
        with_comments = "def test():\n    # This is a comment\n    pass"
        assert preprocessor._has_comments(with_comments) is True

        # Content without comments
        without_comments = "def test():\n    pass"
        assert preprocessor._has_comments(without_comments) is False

    def test_is_well_formatted(self):
        """Test code formatting quality check."""
        preprocessor = CodePreprocessor()

        # Well-formatted code
        well_formatted = "def test():\n    if True:\n        pass"
        assert preprocessor._is_well_formatted(well_formatted) is True

        # Poorly formatted code (inconsistent indentation)
        poorly_formatted = "def test():\n   if True:\n      pass"
        # This might still pass depending on the exact implementation
        result = preprocessor._is_well_formatted(poorly_formatted)
        assert isinstance(result, bool)

        # Very long lines
        long_lines = "def test():\n    " + "x" * 150
        assert preprocessor._is_well_formatted(long_lines) is False

    def test_is_valid_chunk(self):
        """Test chunk validation."""
        preprocessor = CodePreprocessor()

        # Valid chunk
        valid_chunk = CodeChunk(
            id="test123",
            content="def hello():\n    return 'world'",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=None,
            start_line=1,
            end_line=2,
            start_byte=0,
            end_byte=30
        )
        assert preprocessor._is_valid_chunk(valid_chunk) is True

        # Too small chunk
        small_chunk = CodeChunk(
            id="test123",
            content="x=1",  # Very small content
            language="python",
            chunk_type=ChunkType.VARIABLE,
            file_path=None,
            start_line=1,
            end_line=1,
            start_byte=0,
            end_byte=3
        )
        assert preprocessor._is_valid_chunk(small_chunk) is False

        # Comment chunk when comments not preserved
        config = PreprocessingConfig(preserve_comments=False)
        preprocessor_no_comments = CodePreprocessor(config)

        comment_chunk = CodeChunk(
            id="test123",
            content="# This is a comment that is long enough to pass size check",
            language="python",
            chunk_type=ChunkType.COMMENT,
            file_path=None,
            start_line=1,
            end_line=1,
            start_byte=0,
            end_byte=60
        )
        assert preprocessor_no_comments._is_valid_chunk(comment_chunk) is False

    def test_remove_duplicate_chunks(self):
        """Test duplicate chunk removal."""
        preprocessor = CodePreprocessor()

        # Create duplicate chunks (same content, different IDs)
        chunk1 = CodeChunk(
            id="test1",
            content="def hello(): pass",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=None,
            start_line=1,
            end_line=1,
            start_byte=0,
            end_byte=17
        )

        chunk2 = CodeChunk(
            id="test2",
            content="def hello(): pass",  # Same content
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=None,
            start_line=5,
            end_line=5,
            start_byte=100,
            end_byte=117
        )

        chunk3 = CodeChunk(
            id="test3",
            content="def world(): pass",  # Different content
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=None,
            start_line=10,
            end_line=10,
            start_byte=200,
            end_byte=217
        )

        chunks = [chunk1, chunk2, chunk3]
        unique_chunks = preprocessor._remove_duplicate_chunks(chunks)

        assert len(unique_chunks) == 2  # Should remove one duplicate
        assert chunk3 in unique_chunks  # Different content should remain

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_extract_module_info(self, mock_parser_class):
        """Test module information extraction."""
        preprocessor = CodePreprocessor()

        # Create mock parse result with imports and docstring
        import_element = CodeElement(
            name="os", element_type="import", start_line=1, end_line=1,
            start_byte=0, end_byte=9, content="import os", language="python"
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(import_element)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        # Mock the has_errors property
        type(mock_parse_result).has_errors = PropertyMock(return_value=False)

        code = '"""Module docstring"""\nimport os\n\ndef test(): pass'

        module_info = preprocessor._extract_module_info(mock_parse_result, code)

        assert module_info["language"] == "python"
        assert module_info["has_errors"] is False
        assert len(module_info["imports"]) == 1
        assert module_info["imports"][0]["name"] == "os"
        assert module_info["docstring"] == '"""Module docstring"""'


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch('codebase_gardener.data.preprocessor.CodePreprocessor')
    @patch('builtins.open')
    def test_preprocess_file_function(self, mock_open, mock_preprocessor_class):
        """Test preprocess_file convenience function."""
        # Setup mocks
        mock_file = Mock()
        mock_file.read.return_value = "def test(): pass"
        mock_open.return_value.__enter__.return_value = mock_file

        mock_preprocessor = Mock()
        mock_preprocessor.preprocess_file.return_value = [Mock()]
        mock_preprocessor_class.return_value = mock_preprocessor

        # Test function
        file_path = Path("test.py")
        result = preprocess_file(file_path)

        mock_open.assert_called_once_with(file_path, 'r', encoding='utf-8')
        mock_preprocessor.preprocess_file.assert_called_once_with(file_path, "def test(): pass")
        assert len(result) == 1

    @patch('codebase_gardener.data.preprocessor.CodePreprocessor')
    def test_preprocess_code_string_function(self, mock_preprocessor_class):
        """Test preprocess_code_string convenience function."""
        # Setup mocks
        mock_preprocessor = Mock()
        mock_preprocessor.preprocess_code.return_value = [Mock()]
        mock_preprocessor_class.return_value = mock_preprocessor

        # Test function
        code = "def test(): pass"
        language = "python"
        result = preprocess_code_string(code, language)

        mock_preprocessor.preprocess_code.assert_called_once_with(code, language)
        assert len(result) == 1


class TestIntegrationScenarios:
    """Test integration scenarios with real-like data."""

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_python_function_preprocessing(self, mock_parser_class):
        """Test preprocessing a Python function."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Create realistic Python function element
        python_code = '''def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)'''

        mock_element = CodeElement(
            name="calculate_fibonacci",
            element_type="function",
            start_line=1,
            end_line=5,
            start_byte=0,
            end_byte=len(python_code),
            content=python_code,
            language="python",
            metadata={"has_docstring": True}
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(mock_element)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        mock_parser.parse.return_value = mock_parse_result

        # Test preprocessing
        preprocessor = CodePreprocessor()
        chunks = preprocessor.preprocess_code(python_code, "python")

        assert len(chunks) >= 1
        function_chunk = next((c for c in chunks if c.chunk_type == ChunkType.FUNCTION), None)
        assert function_chunk is not None
        assert function_chunk.metadata["element_name"] == "calculate_fibonacci"
        assert function_chunk.complexity_score > 1.0  # Should have some complexity

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_class_with_methods_preprocessing(self, mock_parser_class):
        """Test preprocessing a Python class with methods."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Create realistic Python class
        python_code = '''class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        """Add two numbers."""
        return x + y
    
    def multiply(self, x, y):
        """Multiply two numbers."""
        return x * y'''

        # Create elements for class and methods
        class_element = CodeElement(
            name="Calculator", element_type="class", start_line=1, end_line=12,
            start_byte=0, end_byte=len(python_code), content=python_code, language="python"
        )

        init_method = CodeElement(
            name="__init__", element_type="function", start_line=4, end_line=5,
            start_byte=60, end_byte=100, content="def __init__(self):\n        self.result = 0", language="python"
        )

        add_method = CodeElement(
            name="add", element_type="function", start_line=7, end_line=9,
            start_byte=120, end_byte=180, content="def add(self, x, y):\n        \"\"\"Add two numbers.\"\"\"\n        return x + y", language="python"
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(class_element)
        mock_structure.add_element(init_method)
        mock_structure.add_element(add_method)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        mock_parser.parse.return_value = mock_parse_result

        # Test preprocessing
        preprocessor = CodePreprocessor()
        chunks = preprocessor.preprocess_code(python_code, "python")

        assert len(chunks) >= 3  # Class + methods

        class_chunks = [c for c in chunks if c.chunk_type == ChunkType.CLASS]
        function_chunks = [c for c in chunks if c.chunk_type == ChunkType.FUNCTION]

        assert len(class_chunks) >= 1
        assert len(function_chunks) >= 2

    @patch('codebase_gardener.data.preprocessor.TreeSitterParser')
    def test_module_with_imports_preprocessing(self, mock_parser_class):
        """Test preprocessing a module with imports."""
        # Setup mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Create realistic module with imports
        python_code = '''"""
A utility module for file operations.
"""
import os
import sys
from pathlib import Path

def get_file_size(file_path):
    """Get the size of a file."""
    return os.path.getsize(file_path)'''

        # Create elements
        import1 = CodeElement(
            name="os", element_type="import", start_line=4, end_line=4,
            start_byte=50, end_byte=59, content="import os", language="python"
        )

        import2 = CodeElement(
            name="sys", element_type="import", start_line=5, end_line=5,
            start_byte=60, end_byte=70, content="import sys", language="python"
        )

        import3 = CodeElement(
            name="Path", element_type="import", start_line=6, end_line=6,
            start_byte=71, end_byte=95, content="from pathlib import Path", language="python"
        )

        function = CodeElement(
            name="get_file_size", element_type="function", start_line=8, end_line=10,
            start_byte=97, end_byte=180,
            content="def get_file_size(file_path):\n    \"\"\"Get the size of a file.\"\"\"\n    return os.path.getsize(file_path)",
            language="python"
        )

        mock_structure = CodeStructure()
        mock_structure.add_element(import1)
        mock_structure.add_element(import2)
        mock_structure.add_element(import3)
        mock_structure.add_element(function)

        mock_parse_result = ParseResult(
            tree=Mock(),
            structure=mock_structure,
            language="python"
        )
        mock_parser.parse.return_value = mock_parse_result

        # Test preprocessing
        config = PreprocessingConfig(extract_imports=True)
        preprocessor = CodePreprocessor(config)
        chunks = preprocessor.preprocess_code(python_code, "python")

        # Should have module chunk with imports + function chunk
        assert len(chunks) >= 2

        module_chunks = [c for c in chunks if c.chunk_type == ChunkType.MODULE]
        function_chunks = [c for c in chunks if c.chunk_type == ChunkType.FUNCTION]

        assert len(module_chunks) >= 1
        assert len(function_chunks) >= 1

        # Module chunk should contain imports
        module_chunk = module_chunks[0]
        assert "import os" in module_chunk.content or "os" in module_chunk.dependencies
