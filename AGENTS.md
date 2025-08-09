# Codebase Gardener Development Guide

## Setup

run: pip install -e ".[dev]" && pip install -r requirements.txt

## Tests

run: python -m pytest --cov=src/codebase_gardener --cov-report=term-missing

## Style

run: black src tests && isort src tests && ruff check src tests

## Guidelines

• Use 4-space indentation, double quotes for strings, snake_case naming
• Write unit tests for individual functions, integration tests for workflows
• Follow dataclass patterns for structured data, use type hints throughout
• Implement error handling with custom exceptions and structured logging
• Maintain local-first processing principles, optimize for Mac Mini M4
