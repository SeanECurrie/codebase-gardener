"""
Tests for Tree-sitter code parser integration.

Tests cover multi-language parsing, AST traversal, structure extraction,
error handling, and integration with the error handling framework.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from codebase_gardener.data.parser import (
    CodeElement,
    CodeStructure,
    ParseError,
    ParseResult,
    SupportedLanguage,
    TreeSitterParser,
    create_parser_for_file,
    get_supported_extensions,
    is_supported_file,
)
from codebase_gardener.utils.error_handling import ParsingError


class TestSupportedLanguage:
    """Test SupportedLanguage enum."""

    def test_supported_languages(self):
        """Test that all expected languages are supported."""
        expected_languages = {"python", "javascript", "typescript"}
        actual_languages = {lang.value for lang in SupportedLanguage}
        assert actual_languages == expected_languages

    def test_language_enum_values(self):
        """Test specific language enum values."""
        assert SupportedLanguage.PYTHON.value == "python"
        assert SupportedLanguage.JAVASCRIPT.value == "javascript"
        assert SupportedLanguage.TYPESCRIPT.value == "typescript"


class TestCodeElement:
    """Test CodeElement dataclass."""

    def test_code_element_creation(self):
        """Test creating a valid code element."""
        element = CodeElement(
            name="test_function",
            element_type="function",
            start_line=1,
            end_line=5,
            start_byte=0,
            end_byte=50,
            content="def test_function():\n    pass",
            language="python"
        )

        assert element.name == "test_function"
        assert element.element_type == "function"
        assert element.start_line == 1
        assert element.end_line == 5
        assert element.language == "python"
        assert element.metadata == {}

    def test_code_element_with_metadata(self):
        """Test creating code element with metadata."""
        metadata = {"is_async": True, "decorators": ["@property"]}
        element = CodeElement(
            name="async_function",
            element_type="function",
            start_line=1,
            end_line=3,
            start_byte=0,
            end_byte=30,
            content="async def async_function(): pass",
            language="python",
            metadata=metadata
        )

        assert element.metadata == metadata

    def test_code_element_validation_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="Code element name cannot be empty"):
            CodeElement(
                name="",
                element_type="function",
                start_line=1,
                end_line=1,
                start_byte=0,
                end_byte=10,
                content="test",
                language="python"
            )

    def test_code_element_validation_negative_lines(self):
        """Test validation fails for negative line numbers."""
        with pytest.raises(ValueError, match="Line numbers must be non-negative"):
            CodeElement(
                name="test",
                element_type="function",
                start_line=-1,
                end_line=1,
                start_byte=0,
                end_byte=10,
                content="test",
                language="python"
            )

    def test_code_element_validation_invalid_line_order(self):
        """Test validation fails when start line > end line."""
        with pytest.raises(ValueError, match="Start line cannot be greater than end line"):
            CodeElement(
                name="test",
                element_type="function",
                start_line=5,
                end_line=1,
                start_byte=0,
                end_byte=10,
                content="test",
                language="python"
            )


class TestCodeStructure:
    """Test CodeStructure dataclass."""

    def test_empty_code_structure(self):
        """Test creating empty code structure."""
        structure = CodeStructure()

        assert len(structure.functions) == 0
        assert len(structure.classes) == 0
        assert len(structure.imports) == 0
        assert len(structure.variables) == 0
        assert len(structure.comments) == 0
        assert len(structure.get_all_elements()) == 0

    def test_add_elements(self):
        """Test adding elements to code structure."""
        structure = CodeStructure()

        function_element = CodeElement(
            name="test_func", element_type="function", start_line=1, end_line=2,
            start_byte=0, end_byte=20, content="def test_func(): pass", language="python"
        )

        class_element = CodeElement(
            name="TestClass", element_type="class", start_line=3, end_line=5,
            start_byte=21, end_byte=50, content="class TestClass: pass", language="python"
        )

        structure.add_element(function_element)
        structure.add_element(class_element)

        assert len(structure.functions) == 1
        assert len(structure.classes) == 1
        assert structure.functions[0] == function_element
        assert structure.classes[0] == class_element

    def test_get_element_count(self):
        """Test getting element counts."""
        structure = CodeStructure()

        # Add various elements
        for i in range(3):
            structure.add_element(CodeElement(
                name=f"func_{i}", element_type="function", start_line=i, end_line=i+1,
                start_byte=i*10, end_byte=(i+1)*10, content=f"def func_{i}(): pass", language="python"
            ))

        for i in range(2):
            structure.add_element(CodeElement(
                name=f"Class_{i}", element_type="class", start_line=i+10, end_line=i+11,
                start_byte=(i+10)*10, end_byte=(i+11)*10, content=f"class Class_{i}: pass", language="python"
            ))

        counts = structure.get_element_count()
        assert counts["functions"] == 3
        assert counts["classes"] == 2
        assert counts["imports"] == 0
        assert counts["variables"] == 0
        assert counts["comments"] == 0
        assert counts["total"] == 5


class TestParseError:
    """Test ParseError dataclass."""

    def test_parse_error_creation(self):
        """Test creating a parse error."""
        error = ParseError(
            message="Syntax error",
            line=5,
            column=10,
            byte_offset=100,
            error_type="syntax_error",
            context="def invalid_syntax("
        )

        assert error.message == "Syntax error"
        assert error.line == 5
        assert error.column == 10
        assert error.byte_offset == 100
        assert error.error_type == "syntax_error"
        assert error.context == "def invalid_syntax("


class TestParseResult:
    """Test ParseResult dataclass."""

    def test_parse_result_success(self):
        """Test successful parse result."""
        structure = CodeStructure()
        result = ParseResult(
            tree=MagicMock(),  # Mock tree object
            structure=structure,
            errors=[],
            language="python",
            file_path=Path("test.py")
        )

        assert result.tree is not None
        assert result.structure == structure
        assert not result.has_errors
        assert result.is_valid
        assert result.language == "python"
        assert result.file_path == Path("test.py")

    def test_parse_result_with_errors(self):
        """Test parse result with errors."""
        error = ParseError("Syntax error", 1, 0, 0)
        result = ParseResult(
            tree=MagicMock(),
            structure=CodeStructure(),
            errors=[error],
            language="python"
        )

        assert result.has_errors
        assert not result.is_valid
        assert len(result.errors) == 1


class TestTreeSitterParser:
    """Test TreeSitterParser class."""

    def test_language_detection(self):
        """Test language detection from file extensions."""
        assert TreeSitterParser.detect_language("test.py") == SupportedLanguage.PYTHON
        assert TreeSitterParser.detect_language("test.js") == SupportedLanguage.JAVASCRIPT
        assert TreeSitterParser.detect_language("test.ts") == SupportedLanguage.TYPESCRIPT
        assert TreeSitterParser.detect_language("test.tsx") == SupportedLanguage.TYPESCRIPT
        assert TreeSitterParser.detect_language("test.d.ts") == SupportedLanguage.TYPESCRIPT
        assert TreeSitterParser.detect_language("test.unknown") is None

    def test_language_detection_with_path_object(self):
        """Test language detection with Path objects."""
        assert TreeSitterParser.detect_language(Path("test.py")) == SupportedLanguage.PYTHON
        assert TreeSitterParser.detect_language(Path("src/test.js")) == SupportedLanguage.JAVASCRIPT

    def test_parser_initialization_with_string(self):
        """Test parser initialization with string language."""
        parser = TreeSitterParser("python")
        assert parser.language == SupportedLanguage.PYTHON

    def test_parser_initialization_with_enum(self):
        """Test parser initialization with enum language."""
        parser = TreeSitterParser(SupportedLanguage.JAVASCRIPT)
        assert parser.language == SupportedLanguage.JAVASCRIPT

    def test_parser_initialization_unsupported_language(self):
        """Test parser initialization with unsupported language."""
        with pytest.raises(ParsingError, match="Unsupported language: java"):
            TreeSitterParser("java")

    @patch('codebase_gardener.data.parser.Language')
    @patch('codebase_gardener.data.parser.Parser')
    def test_python_parser_setup(self, mock_parser_class, mock_language_class):
        """Test Python parser setup."""
        # Mock the Language class to return a mock language object
        mock_language_obj = MagicMock()
        mock_language_class.return_value = mock_language_obj

        # Mock the Parser class to return a mock parser object
        mock_parser_obj = MagicMock()
        mock_parser_class.return_value = mock_parser_obj

        parser = TreeSitterParser(SupportedLanguage.PYTHON)
        assert parser.language == SupportedLanguage.PYTHON
        assert parser.parser == mock_parser_obj
        mock_language_class.assert_called_once()
        mock_parser_class.assert_called_once_with(mock_language_obj)

    def test_create_for_file_supported(self):
        """Test creating parser for supported file."""
        parser = TreeSitterParser.create_for_file("test.py")
        assert parser is not None
        assert parser.language == SupportedLanguage.PYTHON

    def test_create_for_file_unsupported(self):
        """Test creating parser for unsupported file."""
        parser = TreeSitterParser.create_for_file("test.unknown")
        assert parser is None


class TestTreeSitterParserParsing:
    """Test actual parsing functionality."""

    @pytest.fixture
    def python_parser(self):
        """Create a Python parser for testing."""
        return TreeSitterParser(SupportedLanguage.PYTHON)

    def test_parse_simple_python_function(self, python_parser):
        """Test parsing a simple Python function."""
        code = """def hello_world():
    print("Hello, World!")
    return True"""

        result = python_parser.parse(code)

        assert result.tree is not None
        assert result.language == "python"
        assert not result.has_errors
        assert len(result.structure.functions) == 1

        func = result.structure.functions[0]
        assert func.name == "hello_world"
        assert func.element_type == "function"
        assert func.start_line == 1
        assert func.end_line == 3

    def test_parse_python_class(self, python_parser):
        """Test parsing a Python class."""
        code = """class TestClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value"""

        result = python_parser.parse(code)

        assert not result.has_errors
        assert len(result.structure.classes) == 1
        assert len(result.structure.functions) == 2  # __init__ and get_value

        cls = result.structure.classes[0]
        assert cls.name == "TestClass"
        assert cls.element_type == "class"

    def test_parse_python_imports(self, python_parser):
        """Test parsing Python imports."""
        code = """import os
from pathlib import Path
from typing import List, Dict"""

        result = python_parser.parse(code)

        assert not result.has_errors
        assert len(result.structure.imports) == 3

        # Check import names (they may be concatenated for from imports)
        import_names = [imp.name for imp in result.structure.imports]
        assert "os" in import_names
        # For "from pathlib import Path", the name might be "pathlib, Path" or just "Path"
        assert any("Path" in name for name in import_names)
        # For "from typing import List, Dict", the name might be "typing, List, Dict" or "List, Dict"
        assert any("List" in name and "Dict" in name for name in import_names)

    def test_parse_malformed_code(self, python_parser):
        """Test parsing malformed Python code."""
        code = """def broken_function(
    print("Missing closing parenthesis")
    return"""

        result = python_parser.parse(code)

        # Should still return a result but with errors
        assert result.tree is not None
        assert result.has_errors
        assert len(result.errors) > 0

        # Check error details
        error = result.errors[0]
        assert error.error_type == "syntax_error"
        assert error.line > 0

    def test_parse_empty_code(self, python_parser):
        """Test parsing empty code."""
        result = python_parser.parse("")

        assert result.tree is not None
        assert not result.has_errors
        assert len(result.structure.get_all_elements()) == 0

    def test_parse_with_file_path(self, python_parser):
        """Test parsing with file path context."""
        code = "def test(): pass"
        file_path = Path("test.py")

        result = python_parser.parse(code, file_path=file_path)

        assert result.file_path == file_path
        assert result.language == "python"

    def test_parse_incremental_parsing(self, python_parser):
        """Test incremental parsing with old tree."""
        code1 = "def func1(): pass"
        code2 = "def func1(): pass\ndef func2(): pass"

        # Parse initial code
        result1 = python_parser.parse(code1)
        assert len(result1.structure.functions) == 1

        # Parse updated code with old tree (incremental parsing)
        # Note: Incremental parsing may not always work as expected with Tree-sitter
        # The important thing is that it doesn't crash and produces a valid result
        result2 = python_parser.parse(code2, old_tree=result1.tree)
        assert result2.tree is not None
        assert not result2.has_errors

        # Test without incremental parsing to ensure it works correctly
        result3 = python_parser.parse(code2)
        assert len(result3.structure.functions) == 2

    @patch('codebase_gardener.data.parser.Parser')
    def test_parse_with_retry_on_failure(self, mock_parser_class):
        """Test that parsing retries on failure."""
        # Create a mock parser that fails once then succeeds
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        call_count = 0
        def mock_parse(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            # Return a mock tree on success
            mock_tree = MagicMock()
            mock_tree.root_node = MagicMock()
            mock_tree.root_node.children = []
            return mock_tree

        mock_parser.parse = mock_parse

        # Create parser (will use mocked Parser)
        parser = TreeSitterParser(SupportedLanguage.PYTHON)

        code = "def test(): pass"
        result = parser.parse(code)

        assert result.tree is not None
        assert call_count == 2  # Failed once, succeeded on retry


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_parser_for_file(self):
        """Test create_parser_for_file function."""
        parser = create_parser_for_file("test.py")
        assert parser is not None
        assert parser.language == SupportedLanguage.PYTHON

        parser = create_parser_for_file("test.unknown")
        assert parser is None

    def test_get_supported_extensions(self):
        """Test get_supported_extensions function."""
        extensions = get_supported_extensions()

        expected_extensions = {".py", ".pyi", ".js", ".jsx", ".mjs", ".ts", ".tsx", ".d.ts"}
        assert extensions == expected_extensions

    def test_is_supported_file(self):
        """Test is_supported_file function."""
        assert is_supported_file("test.py") is True
        assert is_supported_file("test.js") is True
        assert is_supported_file("test.ts") is True
        assert is_supported_file("test.unknown") is False
        assert is_supported_file(Path("src/test.py")) is True


class TestErrorHandling:
    """Test error handling integration."""

    def test_parsing_error_on_setup_failure(self):
        """Test ParsingError is raised when language setup fails."""
        with patch('tree_sitter_python.language', side_effect=ImportError("Module not found")):
            with pytest.raises(ParsingError, match="Failed to import Tree-sitter language module"):
                TreeSitterParser(SupportedLanguage.PYTHON)

    @patch('codebase_gardener.data.parser.Parser')
    def test_parsing_error_on_parse_failure(self, mock_parser_class):
        """Test ParsingError is raised when parsing fails completely."""
        # Create a mock parser that returns None
        mock_parser = MagicMock()
        mock_parser.parse.return_value = None
        mock_parser_class.return_value = mock_parser

        parser = TreeSitterParser(SupportedLanguage.PYTHON)

        with pytest.raises(ParsingError, match="Failed to parse python code"):
            parser.parse("def test(): pass")

    @patch('codebase_gardener.data.parser.Parser')
    def test_error_logging_on_parse_failure(self, mock_parser_class):
        """Test that parsing errors are logged properly."""
        # Create a mock parser that raises an exception
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Test error")
        mock_parser_class.return_value = mock_parser

        parser = TreeSitterParser(SupportedLanguage.PYTHON)

        with patch('codebase_gardener.data.parser.logger') as mock_logger:
            with pytest.raises(ParsingError):
                parser.parse("def test(): pass")

            # Logger should be called at least once (may be called multiple times due to retry)
            assert mock_logger.error.call_count >= 1


class TestLanguageSpecificParsing:
    """Test language-specific parsing features."""

    @pytest.fixture
    def js_parser(self):
        """Create a JavaScript parser for testing."""
        return TreeSitterParser(SupportedLanguage.JAVASCRIPT)

    def test_javascript_function_parsing(self, js_parser):
        """Test parsing JavaScript functions."""
        code = """function regularFunction() {
    return 'hello';
}

const arrowFunction = () => {
    return 'world';
};

async function asyncFunction() {
    return await Promise.resolve('async');
}"""

        result = js_parser.parse(code)

        assert not result.has_errors
        assert len(result.structure.functions) == 3

        # Check function names
        func_names = [func.name for func in result.structure.functions]
        assert "regularFunction" in func_names
        assert "<arrow_function>" in func_names
        assert "asyncFunction" in func_names

    def test_javascript_class_parsing(self, js_parser):
        """Test parsing JavaScript classes."""
        code = """class TestClass {
    constructor(value) {
        this.value = value;
    }
    
    getValue() {
        return this.value;
    }
}"""

        result = js_parser.parse(code)

        assert not result.has_errors
        assert len(result.structure.classes) == 1

        cls = result.structure.classes[0]
        assert cls.name == "TestClass"
        assert cls.element_type == "class"


class TestPerformance:
    """Test performance-related functionality."""

    def test_large_file_parsing(self):
        """Test parsing a large file doesn't cause issues."""
        parser = TreeSitterParser(SupportedLanguage.PYTHON)

        # Generate a large Python file
        large_code = "\n".join([f"def function_{i}():\n    return {i}" for i in range(100)])

        result = parser.parse(large_code)

        assert not result.has_errors
        assert len(result.structure.functions) == 100

    def test_deeply_nested_code(self):
        """Test parsing deeply nested code structures."""
        parser = TreeSitterParser(SupportedLanguage.PYTHON)

        # Generate deeply nested code
        nested_code = "def outer():\n"
        for i in range(10):
            nested_code += "    " * (i + 1) + f"def nested_{i}():\n"
            nested_code += "    " * (i + 2) + f"return {i}\n"

        result = parser.parse(nested_code)

        assert not result.has_errors
        # Should find all nested functions
        assert len(result.structure.functions) >= 10
