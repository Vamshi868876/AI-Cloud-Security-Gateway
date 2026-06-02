# Contributing to AI Cloud Security Gateway

## Welcome! 👋

We're excited you want to contribute to our ML-powered Cloud Security Gateway!

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis 7.0+
- Node.js 18+ (for frontend)

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/AI-Cloud-Security-Gateway.git
cd AI-Cloud-Security-Gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run: `pytest tests/ -v && black . && flake8 .`
4. Commit: `git commit -m "feat: add feature description"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

## Code Style

- PEP 8 compliance (Black for formatting)
- Type hints on all functions
- Docstrings for all modules/classes/functions
- Maximum line length: 100 characters

## Testing

```bash
# Run all tests
pytest tests/ -v --cov

# Run specific test file
pytest tests/test_security.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

## Before Submitting PR

- [ ] Tests written and passing
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings
- [ ] CHANGELOG.md updated

## Questions?

- 📖 [Documentation](docs/)
- 🐛 [Open an Issue](https://github.com/Vamshi868876/AI-Cloud-Security-Gateway/issues)
- 💬 [Discussions](https://github.com/Vamshi868876/AI-Cloud-Security-Gateway/discussions)
- 📧 Email: vamshi@example.com

Thank you for contributing! 🙏
