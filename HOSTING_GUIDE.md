# Hosting IEDB Library Online

This guide will walk you through the process of publishing your IEDB library to PyPI (Python Package Index) so that others can install it using pip or uv.

## Prerequisites

1. A PyPI account - Register at https://pypi.org/account/register/
2. A package that's ready to be published
3. `twine` - A utility for publishing Python packages

## Step 1: Prepare Your Package

You already have the necessary files:
- `pyproject.toml` - Package metadata and build configuration
- `src/` directory - Package source code
- `LICENSE` - GPL v3.0 license file
- `README.md` - Package documentation

## Step 2: Create a PyPI API Token

1. Log in to your PyPI account at https://pypi.org/
2. Go to Account Settings > API tokens
3. Create an API token with the scope "Upload to this project" for the "iedb" project
4. Save the token securely - you won't be able to see it again

## Step 3: Configure PyPI Credentials

Create a `~/.pypirc` file with your PyPI credentials:

```
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = <your-pypi-token>

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = <your-testpypi-token>
```

Make this file readable only by you:

```bash
chmod 600 ~/.pypirc
```

## Step 4: Test on TestPyPI First (Recommended)

It's a good practice to test your package on TestPyPI before publishing to the main PyPI:

1. Register an account at https://test.pypi.org/account/register/
2. Create an API token for TestPyPI
3. Upload to TestPyPI:

```bash
# Using twine
uv run python -m twine upload --repository testpypi dist/*

# Or using the provided script with TestPyPI flag
./publish_package.sh --test
```

4. Install from TestPyPI to verify:

```bash
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ iedb
```

## Step 5: Publish to PyPI

Once you've confirmed everything works on TestPyPI, you can publish to the main PyPI:

```bash
# Using twine
uv run python -m twine upload dist/*

# Or using the provided script
./publish_package.sh
```

## Step 6: Verify Installation

After publishing, verify that your package can be installed:

```bash
# Clean install to verify
uv pip install --no-cache iedb

# Check the installed version
uv run python -c "import iedb; print(iedb.__version__)"
```

## Automating the Process

The included `publish_package.sh` script automates the build and publish process:

```bash
# Build and publish to TestPyPI
./publish_package.sh --test

# Build and publish to PyPI
./publish_package.sh
```

## Updating Your Package

To update your package:

1. Update the version number in `pyproject.toml`
2. Make your changes to the codebase
3. Build the new package: `./build_package.sh`
4. Publish the new version: `./publish_package.sh`

## Getting Help

If you encounter any issues with publishing:

- PyPI documentation: https://packaging.python.org/en/latest/tutorials/packaging-projects/
- TestPyPI documentation: https://test.pypi.org/help/
- Twine documentation: https://twine.readthedocs.io/