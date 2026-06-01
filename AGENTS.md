# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python project for generating paper-ready benchmark figures. The package name is `paper-plot-program`; the wheel configuration expects source modules under `paper_plot/`. Keep reusable plotting, data-loading, and template-gallery code there as the project grows. `main.py` is currently a minimal entry point and should stay thin. Tests live in `tests/`, with shared pytest setup in `tests/conftest.py`; it configures Matplotlib to use the non-interactive `Agg` backend. Design notes and implementation plans belong under `docs/superpowers/`.

## Build, Test, and Development Commands

Use `uv` for dependency and environment management.

```bash
uv sync --extra dev
```

Install runtime and development dependencies from `pyproject.toml` and `uv.lock`.

```bash
uv run python main.py
```

Run the current CLI entry point.

```bash
uv run pytest
```

Run the test suite defined by `tool.pytest.ini_options`, which points pytest at `tests/`.

```bash
uv build
```

Build the package with Hatchling.

## Coding Style & Naming Conventions

Target Python 3.10 or newer. Use 4-space indentation, descriptive snake_case names for functions and modules, PascalCase for classes, and UPPER_SNAKE_CASE for constants. Keep plotting functions deterministic where possible: accept data/config inputs and return Matplotlib figure or axes objects instead of relying on global state. Prefer small modules grouped by responsibility, such as `paper_plot/templates.py`, `paper_plot/data.py`, and `paper_plot/export.py`.

## Testing Guidelines

Use pytest. Name test files `test_*.py` and test functions `test_*`. Place tests near the behavior they validate conceptually, but keep all test files under `tests/`. For plotting code, assert figure structure, labels, scales, exported files, or data transformations rather than relying on visual inspection. Add regression tests when changing template behavior or parsing logic.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style prefixes such as `chore:` and `docs:`. Continue with short, imperative messages like `feat: add line chart template` or `test: cover yaml config loading`.

Pull requests should include a concise description, test results such as `uv run pytest`, and links to related issues or design docs when applicable. Include screenshots or generated sample figures for user-visible plotting changes.

## Security & Configuration Tips

Do not commit generated datasets, private benchmark results, or local environment files. Keep dependency changes in both `pyproject.toml` and `uv.lock`, and document any new required input formats in `README.md` or `docs/`.
