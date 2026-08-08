Release checklist

- Bump version in `pyproject.toml` and `CHANGELOG.md`.
- Ensure tests pass: `python -m unittest discover -v`.
- Create tag and push:

```
git tag -a v0.1.0 -m "release v0.1.0"
git push origin v0.1.0
```

- Build distribution:

```
python -m build
```

- Upload to PyPI or internal index as needed.
