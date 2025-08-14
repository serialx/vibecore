# Release Process

This document describes the release process for vibecore maintainers.

## Prerequisites

Before releasing, ensure you have:

1. **Commit access** to the main repository
2. **PyPI account** with maintainer access to vibecore
3. **TestPyPI account** for testing releases
4. **uv** package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
5. **GitHub CLI** installed (optional, for creating releases manually)

## Pre-Release Checklist

Before creating a release, ensure:

- [ ] All tests pass: `uv run pytest`
- [ ] Type checking passes: `uv run pyright`
- [ ] Code is formatted: `uv run ruff format .`
- [ ] Linting passes: `uv run ruff check .`
- [ ] CHANGELOG.md is updated with release notes
- [ ] Documentation is up to date
- [ ] Dependencies are locked: `uv lock`

## Version Numbering

Vibecore follows [Semantic Versioning](https://semver.org/) with the format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, backwards compatible

Pre-release versions:
- **Alpha**: `X.Y.ZaN` (early testing)
- **Beta**: `X.Y.ZbN` (feature complete, testing)
- **Release Candidate**: `X.Y.ZrcN` (final testing)

## Release Types

### 1. Alpha/Beta Release (TestPyPI)

For testing and early feedback:

```bash
# Bump to alpha version
uv version 0.2.0a1  # Set specific alpha version
# OR
uv version --bump alpha  # Auto-increment alpha number

# Commit changes
git add pyproject.toml uv.lock
git commit -m "release: bump version to 0.2.0a1"
git push

# Create and push tag (triggers GitHub Actions)
git tag v0.2.0a1
git push origin v0.2.0a1
```

The GitHub Actions workflow will automatically:
1. Build the package
2. Run tests
3. Publish to TestPyPI
4. Create a GitHub pre-release

### 2. Production Release (PyPI)

For stable releases:

```bash
# Bump version (choose one)
uv version 0.2.0              # Set specific version
uv version --bump patch        # 0.1.0 -> 0.1.1
uv version --bump minor        # 0.1.0 -> 0.2.0
uv version --bump major        # 0.1.0 -> 1.0.0

# Update CHANGELOG.md
# Document all changes since last release

# Commit changes
git add pyproject.toml uv.lock CHANGELOG.md
git commit -m "release: bump version to 0.2.0"
git push

# Create and push tag (triggers GitHub Actions)
git tag v0.2.0
git push origin v0.2.0
```

The GitHub Actions workflow will automatically:
1. Build the package
2. Run comprehensive tests
3. Publish to PyPI
4. Create a GitHub release with artifacts

## Manual Release Process

If GitHub Actions is unavailable, you can release manually:

### Build Package

```bash
# Clean previous builds
rm -rf dist/

# Build the package
uv build

# Verify the build
ls -la dist/
# Should contain:
# - vibecore-X.Y.Z-py3-none-any.whl
# - vibecore-X.Y.Z.tar.gz
```

### Test Installation

```bash
# Create test environment
uv venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from wheel
uv pip install dist/vibecore-*.whl

# Test it works
vibecore --version
# Should show: vibecore X.Y.Z

# Deactivate test environment
deactivate
rm -rf test-env
```

### Publish to TestPyPI

```bash
uv publish --index testpypi

# Test installation from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ vibecore==X.Y.Z
```

### Publish to PyPI

```bash
# Upload to PyPI (ONLY for stable releases)
uv publish

# Verify installation
uv pip install vibecore==X.Y.Z
```

## Post-Release Tasks

After a successful release:

1. **Create GitHub Release** (if not auto-created):
   ```bash
   gh release create v0.2.0 \
     --title "v0.2.0" \
     --notes "Release notes here" \
     --prerelease  # Only for alpha/beta
   ```

2. **Announce the Release**:
   - Update README.md if needed
   - Post to relevant channels/forums
   - Update documentation site

3. **Prepare for Next Development**:
   ```bash
   # Bump to next development version
   uv version 0.3.0a0  # Next minor version alpha
   
   git add pyproject.toml uv.lock
   git commit -m "chore: bump version for development"
   git push
   ```

## Troubleshooting

### Version Already Exists

If you get "version already exists" error:
1. Check PyPI/TestPyPI for existing version
2. Bump to a new version number
3. Ensure you're not re-using version numbers

### GitHub Actions Failure

Check the Actions tab for detailed logs:
1. Go to https://github.com/yourusername/vibecore/actions
2. Click on the failed workflow run
3. Review logs for each job

Common issues:
- **Test failures**: Fix tests before releasing
- **Token issues**: Verify PyPI tokens in repository secrets
- **Build issues**: Test build locally with `uv build`

### Package Not Installing Correctly

1. Verify package metadata in `pyproject.toml`
2. Check that all required files are included
3. Test local installation: `uv pip install dist/*.whl`
4. Check PyPI page for package details

### Emergency Rollback

If a bad release is published:
1. **Cannot delete from PyPI** - versions are immutable
2. **Yank the release** on PyPI (marks as broken)
3. **Release a patch version** with fixes immediately
4. **Update documentation** to skip the bad version

## API Token Setup

### TestPyPI Token
1. Go to https://test.pypi.org/manage/account/token/
2. Create token named "vibecore-github-actions"
3. Add as `TESTPYPI_API_TOKEN` in GitHub repository secrets

### PyPI Token
1. Go to https://pypi.org/manage/account/token/
2. Create token named "vibecore-github-actions"
3. Add as `PYPI_API_TOKEN` in GitHub repository secrets

## Quick Reference

```bash
# Check current version
uv run vibecore --version

# Run all quality checks
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest

# Bump versions
uv version --bump alpha   # 0.2.0a1 -> 0.2.0a2
uv version --bump beta    # 0.2.0a2 -> 0.2.0b1
uv version --bump rc      # 0.2.0b1 -> 0.2.0rc1
uv version --bump patch   # 0.2.0 -> 0.2.1
uv version --bump minor   # 0.2.0 -> 0.3.0
uv version --bump major   # 0.2.0 -> 1.0.0

# Create and push tag
git tag v$(uv version)
git push origin v$(uv version)
```

## Resources

- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Actions Workflow](.github/workflows/publish.yml)
- [Keep a Changelog](https://keepachangelog.com/)