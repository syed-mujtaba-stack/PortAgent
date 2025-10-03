# Contributing to PortAgent

Thank you for your interest in contributing to PortAgent! We welcome all contributions, whether they're bug reports, feature requests, documentation improvements, or code contributions.

## How to Contribute

### Reporting Issues
- Before creating a new issue, please check if a similar issue already exists
- Provide a clear title and description
- Include steps to reproduce the issue
- Specify the expected and actual behavior
- Include any relevant error messages or screenshots

### Feature Requests
- Describe the feature you'd like to see added
- Explain why this feature would be valuable
- If possible, provide examples of how it might work

### Code Contributions
1. Fork the repository
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/description-of-fix
   ```
3. Make your changes
4. Write tests for your changes (if applicable)
5. Run the test suite:
   ```bash
   pytest
   ```
6. Ensure your code follows the project's style guidelines
7. Commit your changes with a descriptive commit message
8. Push to your fork and submit a pull request

## Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use type hints for function signatures
- Include docstrings for all public functions and classes
- Keep lines under 88 characters (Black's default line length)

## Development Setup

1. Fork and clone the repository
2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Testing

Run the test suite with:
```bash
pytest
```

## Pull Request Process

1. Ensure all tests pass
2. Update the README.md with details of changes if needed
3. Add your name to the CONTRIBUTORS.md file
4. The project maintainers will review your pull request and provide feedback
5. Once approved, your changes will be merged into the main branch

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
