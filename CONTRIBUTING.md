# Contributing to Codebase Gardener

Thank you for your interest in contributing to the Codebase Gardener MVP! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Git
- Ollama (for AI functionality)
- Basic understanding of Python, AI/ML concepts, and software development

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/codebase-gardener-mvp.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment: `source venv/bin/activate` (macOS/Linux)
5. Install development dependencies: `pip install -e .[dev]`
6. Initialize the application: `codebase-gardener init`

## Development Workflow

### Branch Naming
- Feature branches: `feat/feature-name`
- Bug fixes: `fix/bug-description`
- Documentation: `docs/documentation-update`
- Refactoring: `refactor/component-name`

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public functions and classes
- Maintain test coverage above 80%

### Testing
- Run all tests: `pytest`
- Run specific test categories: `pytest -m unit` or `pytest -m integration`
- Check code coverage: `pytest --cov=src/codebase_gardener`
- Validate code quality: `black src/ tests/ && isort src/ tests/ && mypy src/`

### Documentation
- Update documentation for any new features or changes
- Test all code examples in documentation
- Follow the documentation templates in `.kiro/docs/templates/`
- Update the documentation index when adding new documentation

## Contribution Guidelines

### Pull Request Process
1. Create a feature branch from `main`
2. Make your changes with appropriate tests
3. Update documentation as needed
4. Ensure all tests pass and code quality checks pass
5. Submit a pull request with a clear description of changes

### Code Review
- All contributions require code review
- Address feedback promptly and professionally
- Ensure CI/CD checks pass before requesting review
- Be open to suggestions and improvements

### Issue Reporting
- Use the issue templates when available
- Provide clear reproduction steps for bugs
- Include system information (OS, Python version, etc.)
- Search existing issues before creating new ones

## Architecture Guidelines

### Core Principles
- **Local-First Processing**: All AI processing happens locally
- **Project-Specific Intelligence**: Each codebase gets specialized AI models
- **Mac Mini M4 Optimization**: Efficient resource usage for Apple Silicon
- **Quality Over Speed**: Accurate analysis over fast responses

### Component Design
- Follow the established architectural patterns
- Maintain clear separation of concerns
- Use dependency injection for testability
- Implement comprehensive error handling

### AI/ML Components
- Use LoRA adapters for project-specific models
- Implement efficient memory management
- Support dynamic model loading/unloading
- Maintain compatibility with Ollama ecosystem

## Documentation Standards

### Code Documentation
- Write clear, comprehensive docstrings
- Include usage examples in docstrings
- Document all parameters, return values, and exceptions
- Use Google-style docstring format

### User Documentation
- Write for different skill levels
- Include working code examples
- Provide troubleshooting information
- Keep documentation up-to-date with code changes

### Developer Documentation
- Document architectural decisions
- Explain complex algorithms and data structures
- Provide setup and development instructions
- Include testing and deployment information

## Quality Assurance

### Testing Requirements
- Unit tests for all new functionality
- Integration tests for component interactions
- End-to-end tests for user workflows
- Performance tests for resource-intensive operations

### Code Quality
- Follow established coding standards
- Use static analysis tools (pylint, mypy, bandit)
- Maintain high test coverage
- Write clean, readable code

### Security
- Follow secure coding practices
- Validate all user inputs
- Handle sensitive data appropriately
- Regular security audits and updates

## Community Guidelines

### Communication
- Be respectful and professional
- Provide constructive feedback
- Help other contributors
- Follow the code of conduct

### Collaboration
- Share knowledge and expertise
- Participate in discussions
- Review others' contributions
- Contribute to project planning

## Getting Help

### Resources
- **Documentation**: Check `.kiro/docs/` for comprehensive guides
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Examples**: Review existing code for patterns and examples

### Support Channels
- GitHub Issues for bug reports and feature requests
- GitHub Discussions for questions and general discussion
- Code review comments for specific implementation feedback

## Recognition

Contributors are recognized in the following ways:
- Listed in the project contributors
- Mentioned in release notes for significant contributions
- Invited to participate in project planning and decision-making

Thank you for contributing to Codebase Gardener! Your contributions help make AI-powered code analysis more accessible and effective for developers everywhere.