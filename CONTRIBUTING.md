# Contributing to Flow Metrics

## Development Workflow

### Prerequisites
- Python 3.11+
- Git
- Poetry (recommended) or pip

### Setup Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd ado-flow-metrics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg

# Run tests to verify setup
python -m pytest tests/ -v
```

## Git Workflow

### Branch Strategy
We follow **Git Flow** with feature branches:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development branches
- `hotfix/*` - Critical production fixes
- `release/*` - Release preparation branches

### Branch Naming Convention
```
feature/ADO-123-add-new-metric
feature/dashboard-enhancement
hotfix/ADO-456-fix-critical-bug
release/v1.2.0
```

### Workflow Steps

1. **Create Feature Branch**
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

2. **Development**
```bash
# Make your changes
# Pre-commit hooks will run automatically
git add .
git commit -m "feat(scope): add new feature"
```

3. **Push and Create PR**
```bash
git push origin feature/your-feature-name
# Create Pull Request via GitHub/GitLab
```

## Commit Message Convention

We use **Conventional Commits** specification:

```
<type>(scope): <description>

[optional body]

[optional footer]
```

### Types
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Adding or updating tests
- `build` - Build system changes
- `ci` - CI/CD changes
- `chore` - Other changes

### Examples
```bash
git commit -m "feat(calculator): add flow efficiency calculation"
git commit -m "fix(api): resolve Azure DevOps authentication issue"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(calculator): add edge case tests for empty data"
```

## Code Quality Standards

### Pre-commit Hooks
Our pre-commit hooks enforce:
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **bandit** - Security scanning
- **Conventional commits** - Commit message format

### Code Style
- **Line length**: 88 characters (Black default)
- **Import organization**: isort with Black profile
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for public functions

### Testing Requirements
- **Coverage**: Minimum 85% test coverage
- **Test types**: Unit, integration, and end-to-end tests
- **TDD**: Write tests before implementation when possible
- **Test naming**: Descriptive test names explaining what is tested

## Pull Request Process

### PR Checklist
- [ ] Feature branch created from `main`
- [ ] All tests passing (`python -m pytest tests/ -v`)
- [ ] Code coverage maintained (>85%)
- [ ] Pre-commit hooks passing
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG updated (for user-facing changes)

### PR Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated
```

### Review Requirements
- **Code review**: At least 1 approval required
- **Quality gates**: All CI checks must pass
- **Security**: Bandit security scan must pass
- **Performance**: No significant performance degradation

## Development Best Practices

### Security
- Never commit secrets, tokens, or credentials
- Use environment variables for sensitive configuration
- Run security scans before committing (`bandit -r src/`)

### Performance
- Profile performance-critical code
- Use appropriate data structures and algorithms
- Monitor database query performance

### Documentation
- Update README for user-facing changes
- Add docstrings for public APIs
- Include examples in documentation
- Keep CHANGELOG updated

### Error Handling
- Use specific exception types
- Include meaningful error messages
- Log errors appropriately
- Implement graceful degradation

## Release Process

### Version Numbering
We follow **Semantic Versioning** (SemVer):
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps
1. Create release branch: `release/v1.2.0`
2. Update version in `setup.py` and `__init__.py`
3. Update CHANGELOG.md
4. Run full test suite
5. Create release PR to `main`
6. Tag release: `git tag v1.2.0`
7. Deploy to production

## Troubleshooting

### Pre-commit Issues
```bash
# Skip hooks for emergency commits (use sparingly)
git commit --no-verify -m "hotfix: emergency fix"

# Update pre-commit hooks
pre-commit autoupdate

# Run hooks manually
pre-commit run --all-files
```

### Test Issues
```bash
# Run specific test
python -m pytest tests/test_calculator.py::TestFlowMetricsCalculator::test_calculate_lead_time -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Debug test failures
python -m pytest tests/ -vv --tb=long
```

## Getting Help

- Check existing issues and PRs
- Review documentation and README
- Ask questions in team channels
- Tag maintainers in issues

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow project conventions
