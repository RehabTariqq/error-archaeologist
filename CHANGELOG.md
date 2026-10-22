# Changelog

## 1.1.0

- Add `search --clip` to search the error on the clipboard
- Add `pyproject.toml`; install with `pip install .` to get the `ea` command
- Add `python -m error_archaeologist`
- Store data in a per-user folder when installed with pip
- Add shell integration guide

## 1.0.0

- Rewrite as a package with atomic storage and corrupt-file backup
- IDF-weighted search with fuzzy matching and error normalisation
- `run`, `edit`, `delete`, `stats`, `export` and `import` commands
- Unit tests and GitHub Actions CI
