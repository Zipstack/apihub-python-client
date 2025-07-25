# Release Workflow Documentation

This document explains how to use the automated release workflow for the `apihub-python-client` package.

## Overview

The project has two GitHub Actions workflows for publishing:

1. **`publish.yml`** - Automated release creation and publishing (recommended)
2. **`publish-on-release.yml`** - Publish when a release is manually created

## Automated Release Workflow (Recommended)

The main workflow (`publish.yml`) automates the entire release process:

### Features

- ✅ Automatic version bumping
- ✅ Git tag creation
- ✅ GitHub release creation with auto-generated notes
- ✅ Code quality checks (linting, type checking)
- ✅ Test execution
- ✅ PyPI publishing
- ✅ Support for pre-releases
- ✅ Custom release notes

### How to Use

1. **Navigate to Actions tab** in the GitHub repository
2. **Select "Release Tag and Publish Package"** workflow
3. **Click "Run workflow"**
4. **Configure the release:**
   - **Version bump type**: Choose `patch`, `minor`, or `major`
   - **Pre-release**: Check if this is a pre-release version
   - **Release notes**: Optional custom notes (auto-generated notes will also be included)
5. **Click "Run workflow"** button

### Version Bumping

The workflow follows semantic versioning:

- **Patch** (e.g., 1.2.3 → 1.2.4): Bug fixes, small improvements
- **Minor** (e.g., 1.2.3 → 1.3.0): New features, backwards compatible
- **Major** (e.g., 1.2.3 → 2.0.0): Breaking changes

### What Happens During Release

1. **Version Update**: Updates `__version__` in `src/apihub_client/__init__.py`
2. **Git Operations**:
   - Commits version change to main branch
   - Creates and pushes git tag (e.g., `v1.2.3`)
3. **Quality Checks**:
   - Runs linting with `ruff`
   - Executes full test suite with `tox`
4. **GitHub Release**: Creates release with auto-generated changelog
5. **PyPI Publishing**: Builds and publishes package to PyPI

### Requirements

The workflow requires these repository secrets:

- `PUSH_TO_MAIN_APP_ID`: GitHub App ID for pushing to main
- `PUSH_TO_MAIN_APP_PRIVATE_KEY`: GitHub App private key

And these repository variables:

- `PUSH_TO_MAIN_APP_ID`: GitHub App ID (can be same as secret)

**PyPI Setup**: This workflow uses PyPI Trusted Publishers with `uv publish` for secure publishing. You need to:

1. Configure the GitHub repository as a trusted publisher on PyPI
2. Set up the trusted publisher for the `apihub-python-client` package
3. No API tokens required - `uv publish` automatically handles OIDC authentication

## Manual Release Workflow

The `publish-on-release.yml` workflow runs when you manually create a release through GitHub's interface.

### When to Use

- When you need more control over the release process
- For hotfixes or special releases
- When the automated workflow is not available

### How to Use

1. **Create a release manually** through GitHub's release interface
2. **Use semantic version tag** (e.g., `v1.2.3`)
3. **Publish the release** - this triggers the workflow automatically

## Best Practices

### Before Releasing

1. **Ensure all tests pass** on the main branch
2. **Review recent changes** and prepare release notes if needed
3. **Check dependencies** are up to date
4. **Verify documentation** is current

### Version Strategy

- Use **patch** for bug fixes and small improvements
- Use **minor** for new features that don't break existing code
- Use **major** for breaking changes
- Use **pre-release** for beta/alpha versions

### Release Notes

- Let GitHub auto-generate notes for most releases
- Add custom notes for major releases or important changes
- Include migration guides for breaking changes

## Troubleshooting

### Common Issues

**Workflow fails at version bump:**

- Check that the current version in `__init__.py` follows semantic versioning
- Ensure the main branch is up to date

**Tests fail during release:**

- Check the latest test results on main branch
- Fix failing tests before attempting release

**PyPI publish fails:**

- Verify PyPI Trusted Publisher is configured correctly
- Check if version already exists on PyPI
- Ensure package builds successfully locally with `uv build`
- Verify the repository and workflow file match the trusted publisher configuration
- Check that `uv publish` has proper OIDC token access (requires `id-token: write` permission)

**Permission errors:**

- Verify GitHub App has necessary permissions
- Check that secrets and variables are properly configured

### Getting Help

1. Check the [Actions tab](../../actions) for detailed logs
2. Review failed workflow runs for specific error messages
3. Create an issue if you encounter persistent problems

## Local Testing

Before releasing, you can test the package locally:

```bash
# Install dependencies
uv sync --dev

# Run linting
tox -e lint

# Run tests
tox -e py312

# Build package
uv build

# Test installation
pip install dist/*.whl
```

## Security Notes

- Never commit API tokens or secrets to the repository
- The workflow uses `uv publish` with PyPI Trusted Publishers for secure, tokenless publishing
- GitHub App tokens are used for secure repository access
- All secrets should be stored in GitHub repository settings
- Trusted Publishers with `uv publish` eliminate the need for long-lived PyPI API tokens
- `uv publish` natively supports OIDC authentication without additional GitHub Actions

## PyPI Trusted Publishers Setup

To configure PyPI Trusted Publishers:

1. **Go to PyPI** → Your project → Manage → Publishing
2. **Add a new trusted publisher** with these details:
   - **Owner**: `Unstract` (your GitHub organization/username)
   - **Repository name**: `apihub-python-client`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: Leave empty (unless using GitHub environments)
3. **Save the configuration**

For more details, see:

- https://docs.pypi.org/trusted-publishers/
- https://docs.astral.sh/uv/guides/publish/#trusted-publishing
