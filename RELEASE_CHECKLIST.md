# IEDB Library Release Checklist

Use this checklist to ensure that the IEDB library package is properly prepared and published.

## Pre-Release Tasks

- [ ] Update version number in `src/iedb/__init__.py`
- [ ] Update version number in `pyproject.toml`
- [ ] Update CHANGELOG.md with recent changes
- [ ] Run tests to ensure all functionality works correctly
- [ ] Check that all documentation is up-to-date
- [ ] Verify license and copyright notices are correct
- [ ] Ensure all dependencies are properly specified

## Build and Validation

- [ ] Run the build script: `./build_uv.sh`
- [ ] Validate the built package: `./validate_package.sh`
- [ ] Test installing the package: `./test_install_uv.sh`
- [ ] Test the installed package with `comprehensive_example.py`
- [ ] Check package size and structure
- [ ] Verify package metadata is correct

## Publishing

- [ ] Create a PyPI account if you don't have one
- [ ] Set up your `.pypirc` file with API tokens
- [ ] (Optional) Upload to TestPyPI first: `./upload_pypi.sh`
- [ ] Test the TestPyPI installation
- [ ] Upload to PyPI: `./upload_pypi.sh`
- [ ] Upload to GitHub Packages: `./upload_github.sh`
- [ ] Verify the package is installable from PyPI: `uv install iedb`

## Post-Release Tasks

- [ ] Tag the release in git: `git tag -a v0.1.0 -m "Version 0.1.0 release"`
- [ ] Push the tag to GitHub: `git push origin v0.1.0`
- [ ] Create a GitHub release with release notes
- [ ] Update the project website (if applicable)
- [ ] Announce the release on relevant channels
- [ ] Monitor for any issues reported by early users

## Final Verification

- [ ] Install from PyPI and run the example script
- [ ] Verify documentation links are working
- [ ] Check that import paths and examples are correct
- [ ] Ensure LICENSE file is included in the package

## Notes on UV Compatibility

- UV is more strict about dependencies than pip
- Ensure all dependencies are explicitly listed
- Test installation with both UV and pip
- Include proper Python version classifiers in `pyproject.toml`

## Important URLs

- PyPI project page: https://pypi.org/project/iedb/
- TestPyPI project page: https://test.pypi.org/project/iedb/
- GitHub repository: https://github.com/yourusername/iedb
- Documentation: https://github.com/yourusername/iedb/wiki

## Contact Information

- Maintainer: niranjoyy@gmail.com
- GitHub Issues: https://github.com/yourusername/iedb/issues