# Paper Plot Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `paper-plot` CLI that reads one YAML config and one CSV file, renders one of three reference-style Matplotlib plots, and exports both PDF and PNG.

**Architecture:** Keep `paper_plot/cli.py` as orchestration only. Put YAML validation in `paper_plot/config.py`, CSV normalization in `paper_plot/data.py`, export in `paper_plot/export.py`, and one focused renderer per template under `paper_plot/templates/`. Tests drive each layer before the CLI ties them together.

**Tech Stack:** Python 3.10+, pandas, PyYAML, Matplotlib, pytest, uv, Hatchling.

---

## File Structure

- Create `paper_plot/__init__.py`: package marker and version-friendly exports if needed.
- Create `paper_plot/config.py`: config dataclass, YAML loader, plot-type validation, required column mapping validation.
- Create `paper_plot/data.py`: CSV loading, column mapping, numeric validation, appearance-order and explicit-order helpers.
- Create `paper_plot/export.py`: output stem normalization and dual PDF/PNG saving.
- Create `paper_plot/templates/__init__.py`: template dispatch registry.
- Create `paper_plot/templates/style.py`: shared Matplotlib style helpers, palettes, spine/grid setup.
- Create `paper_plot/templates/grouped_bar.py`: `grouped_bar` renderer.
- Create `paper_plot/templates/stacked_bar.py`: `stacked_bar` renderer.
- Create `paper_plot/templates/line_series.py`: `line_series` renderer.
- Create `paper_plot/cli.py`: CLI parser and pipeline orchestration.
- Modify `main.py`: delegate to `paper_plot.cli.main`.
- Modify `pyproject.toml`: add the `paper-plot` console script.
- Create tests under `tests/` for each layer and the CLI smoke path.
- Optionally update `README.md` after implementation with one minimal YAML example.

---

### Task 1: Package Skeleton And Config Loader

**Files:**
- Create: `paper_plot/__init__.py`
- Create: `paper_plot/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from paper_plot.config import ConfigError, PlotConfig, load_config


def write_yaml(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_grouped_bar_config(tmp_path):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        """
plot:
  type: grouped_bar
data:
  path: data/throughput.csv
  columns:
    group: Scale
    model: Model
    batch: Batch
    series: System
    value: Throughput
output:
  path: figures/throughput
order:
  batch: [32, 64, 128]
""",
    )

    config = load_config(config_path)

    assert isinstance(config, PlotConfig)
    assert config.plot_type == "grouped_bar"
    assert config.data_path == Path("data/throughput.csv")
    assert config.columns["value"] == "Throughput"
    assert config.output_path == Path("figures/throughput")
    assert config.order["batch"] == [32, 64, 128]


def test_rejects_unknown_plot_type(tmp_path):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        """
plot:
  type: pie_chart
data:
  path: data.csv
  columns: {}
output:
  path: figures/out
""",
    )

    with pytest.raises(ConfigError, match="Unsupported plot type: pie_chart"):
        load_config(config_path)


def test_rejects_missing_required_column_mapping(tmp_path):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        """
plot:
  type: line_series
data:
  path: data.csv
  columns:
    series: System
    x: X
output:
  path: figures/out
""",
    )

    with pytest.raises(
        ConfigError,
        match="Missing required column mapping for line_series: y",
    ):
        load_config(config_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'paper_plot'` or import errors for `paper_plot.config`.

- [ ] **Step 3: Add package marker**

Create `paper_plot/__init__.py`:

```python
"""Paper-ready benchmark plot generator."""
```

- [ ] **Step 4: Implement minimal config loader**

Create `paper_plot/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_PLOT_TYPES = {"grouped_bar", "stacked_bar", "line_series"}

REQUIRED_COLUMNS = {
    "grouped_bar": ("group", "model", "batch", "series", "value"),
    "stacked_bar": ("model", "batch", "series", "stack", "value"),
    "line_series": ("series", "x", "y"),
}


class ConfigError(ValueError):
    """Raised when a plot YAML config is invalid."""


@dataclass(frozen=True)
class PlotConfig:
    plot_type: str
    data_path: Path
    columns: dict[str, str]
    output_path: Path
    order: dict[str, list[Any]]


def load_config(path: str | Path) -> PlotConfig:
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML config: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping")

    plot_type = _required_nested(raw, ("plot", "type"))
    if plot_type not in SUPPORTED_PLOT_TYPES:
        raise ConfigError(f"Unsupported plot type: {plot_type}")

    data_path = Path(_required_nested(raw, ("data", "path")))
    output_path = Path(_required_nested(raw, ("output", "path")))
    columns = _required_nested(raw, ("data", "columns"))
    if not isinstance(columns, dict):
        raise ConfigError("data.columns must be a mapping")

    normalized_columns = {str(key): str(value) for key, value in columns.items()}
    _validate_required_columns(plot_type, normalized_columns)

    order = raw.get("order", {})
    if order is None:
        order = {}
    if not isinstance(order, dict):
        raise ConfigError("order must be a mapping")

    return PlotConfig(
        plot_type=str(plot_type),
        data_path=data_path,
        columns=normalized_columns,
        output_path=output_path,
        order={str(key): list(value) for key, value in order.items()},
    )


def _required_nested(raw: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = raw
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            dotted = ".".join(keys)
            raise ConfigError(f"Missing required config field: {dotted}")
        current = current[key]
    return current


def _validate_required_columns(plot_type: str, columns: dict[str, str]) -> None:
    missing = [name for name in REQUIRED_COLUMNS[plot_type] if name not in columns]
    if missing:
        raise ConfigError(
            f"Missing required column mapping for {plot_type}: {', '.join(missing)}"
        )
```

- [ ] **Step 5: Run config tests to verify they pass**

Run:

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add paper_plot/__init__.py paper_plot/config.py tests/test_config.py
git commit -m "feat: add plot config loader"
```

---

### Task 2: CSV Loading, Column Mapping, And Ordering

**Files:**
- Create: `paper_plot/data.py`
- Test: `tests/test_data.py`

- [ ] **Step 1: Write failing data tests**

Create `tests/test_data.py`:

```python
from pathlib import Path

import pandas as pd
import pytest

from paper_plot.config import PlotConfig
from paper_plot.data import DataError, load_plot_data, ordered_unique


def write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_plot_data_renames_columns_and_converts_value(tmp_path):
    csv_path = write_csv(
        tmp_path / "throughput.csv",
        "Scale,Model,Batch,System,Throughput\nSmall,RetNet,32,GPU,1.0\n",
    )
    config = PlotConfig(
        plot_type="grouped_bar",
        data_path=csv_path,
        columns={
            "group": "Scale",
            "model": "Model",
            "batch": "Batch",
            "series": "System",
            "value": "Throughput",
        },
        output_path=Path("figures/throughput"),
        order={},
    )

    frame = load_plot_data(config)

    assert list(frame.columns) == ["group", "model", "batch", "series", "value"]
    assert frame.loc[0, "value"] == 1.0
    assert pd.api.types.is_numeric_dtype(frame["value"])


def test_load_plot_data_reports_missing_csv_column(tmp_path):
    csv_path = write_csv(tmp_path / "bad.csv", "System,X\nGPU,1\n")
    config = PlotConfig(
        plot_type="line_series",
        data_path=csv_path,
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={},
    )

    with pytest.raises(
        DataError,
        match="CSV column not found for mapping data.columns.y: Latency",
    ):
        load_plot_data(config)


def test_load_plot_data_reports_non_numeric_value(tmp_path):
    csv_path = write_csv(tmp_path / "bad.csv", "System,X,Latency\nGPU,1,fast\n")
    config = PlotConfig(
        plot_type="line_series",
        data_path=csv_path,
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={},
    )

    with pytest.raises(DataError, match="Column y must be numeric"):
        load_plot_data(config)


def test_ordered_unique_uses_explicit_order_then_remaining_values():
    values = ["GPU+PIM", "GPU", "Pimba", "GPU"]

    assert ordered_unique(values, ["GPU", "GPU+PIM"]) == ["GPU", "GPU+PIM", "Pimba"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_data.py -v
```

Expected: FAIL with `ModuleNotFoundError` or import errors for `paper_plot.data`.

- [ ] **Step 3: Implement data loading**

Create `paper_plot/data.py`:

```python
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from paper_plot.config import PlotConfig


NUMERIC_COLUMNS = {
    "grouped_bar": ("value",),
    "stacked_bar": ("value",),
    "line_series": ("x", "y"),
}


class DataError(ValueError):
    """Raised when CSV data cannot be normalized for plotting."""


def load_plot_data(config: PlotConfig) -> pd.DataFrame:
    try:
        source = pd.read_csv(config.data_path)
    except FileNotFoundError as exc:
        raise DataError(f"CSV file not found: {config.data_path}") from exc

    rename_map: dict[str, str] = {}
    for internal_name, external_name in config.columns.items():
        if external_name not in source.columns:
            raise DataError(
                "CSV column not found for mapping "
                f"data.columns.{internal_name}: {external_name}"
            )
        rename_map[external_name] = internal_name

    frame = source.rename(columns=rename_map)
    selected_columns = list(config.columns.keys())
    frame = frame[selected_columns].copy()

    for column in NUMERIC_COLUMNS[config.plot_type]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            raise DataError(f"Column {column} must be numeric")

    return frame


def ordered_unique(values: Iterable[Any], explicit_order: Iterable[Any] | None = None) -> list[Any]:
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)

    if explicit_order is None:
        return seen

    ordered = [value for value in explicit_order if value in seen]
    ordered.extend(value for value in seen if value not in ordered)
    return ordered
```

- [ ] **Step 4: Run data tests to verify they pass**

Run:

```bash
uv run pytest tests/test_data.py -v
```

Expected: PASS.

- [ ] **Step 5: Run config and data tests together**

Run:

```bash
uv run pytest tests/test_config.py tests/test_data.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add paper_plot/data.py tests/test_data.py
git commit -m "feat: normalize csv plot data"
```

---

### Task 3: Export PDF And PNG

**Files:**
- Create: `paper_plot/export.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write failing export tests**

Create `tests/test_export.py`:

```python
from pathlib import Path

import matplotlib.pyplot as plt

from paper_plot.export import export_figure, output_stem


def test_output_stem_removes_known_extension():
    assert output_stem(Path("figures/result.pdf")) == Path("figures/result")
    assert output_stem(Path("figures/result.png")) == Path("figures/result")
    assert output_stem(Path("figures/result")) == Path("figures/result")


def test_export_figure_writes_pdf_and_png(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])

    written = export_figure(fig, tmp_path / "nested" / "plot.pdf")

    assert written == [
        tmp_path / "nested" / "plot.pdf",
        tmp_path / "nested" / "plot.png",
    ]
    assert written[0].exists()
    assert written[1].exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_export.py -v
```

Expected: FAIL with import errors for `paper_plot.export`.

- [ ] **Step 3: Implement export helper**

Create `paper_plot/export.py`:

```python
from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure


KNOWN_OUTPUT_SUFFIXES = {".pdf", ".png", ".svg"}


def output_stem(path: str | Path) -> Path:
    output_path = Path(path)
    if output_path.suffix.lower() in KNOWN_OUTPUT_SUFFIXES:
        return output_path.with_suffix("")
    return output_path


def export_figure(fig: Figure, path: str | Path) -> list[Path]:
    stem = output_stem(path)
    stem.parent.mkdir(parents=True, exist_ok=True)

    outputs = [stem.with_suffix(".pdf"), stem.with_suffix(".png")]
    fig.savefig(outputs[0], bbox_inches="tight")
    fig.savefig(outputs[1], bbox_inches="tight", dpi=300)
    return outputs
```

- [ ] **Step 4: Run export tests to verify they pass**

Run:

```bash
uv run pytest tests/test_export.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add paper_plot/export.py tests/test_export.py
git commit -m "feat: export plots as pdf and png"
```

---

### Task 4: Shared Template Dispatch And Line Series Renderer

**Files:**
- Create: `paper_plot/templates/__init__.py`
- Create: `paper_plot/templates/style.py`
- Create: `paper_plot/templates/line_series.py`
- Test: `tests/test_line_series_template.py`

- [ ] **Step 1: Write failing line-series template tests**

Create `tests/test_line_series_template.py`:

```python
from pathlib import Path

import pandas as pd

from paper_plot.config import PlotConfig
from paper_plot.templates import render_plot
from paper_plot.templates.line_series import render_line_series


def test_render_line_series_returns_figure_with_one_line_per_series():
    frame = pd.DataFrame(
        {
            "series": ["GPU", "GPU", "Pimba", "Pimba"],
            "x": [1, 2, 1, 2],
            "y": [0.1, 0.2, 0.08, 0.12],
        }
    )
    config = PlotConfig(
        plot_type="line_series",
        data_path=Path("data.csv"),
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={"series": ["GPU", "Pimba"]},
    )

    fig = render_line_series(frame, config)
    ax = fig.axes[0]

    data_lines = [line for line in ax.lines if line.get_label() != "_y=1.0"]
    assert len(data_lines) == 2
    assert ax.get_ylabel() == "ShareGPT\nNorm. Latency (s/token)"
    assert ax.get_legend() is not None


def test_render_plot_dispatches_line_series():
    frame = pd.DataFrame({"series": ["GPU"], "x": [1], "y": [0.1]})
    config = PlotConfig(
        plot_type="line_series",
        data_path=Path("data.csv"),
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={},
    )

    fig = render_plot(frame, config)

    assert len(fig.axes) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_line_series_template.py -v
```

Expected: FAIL with import errors for `paper_plot.templates`.

- [ ] **Step 3: Implement shared style helpers**

Create `paper_plot/templates/style.py`:

```python
from __future__ import annotations

from matplotlib.axes import Axes


SERIES_COLORS = {
    "GPU": "#5AA89D",
    "GPU+Q": "#F6E8A6",
    "GPU+PIM": "#E3C960",
    "Pimba": "#D46F4D",
}

LINE_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
LINE_MARKERS = ["o", "s", "v", "^", "D"]


def apply_paper_axes(ax: Axes) -> None:
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.3)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, color="#B7B7B7", alpha=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", width=1.2, labelsize=10)


def style_legend(ax: Axes, *, ncol: int | None = None) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=ncol or len(handles),
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="black",
    )
    legend.get_frame().set_linewidth(1.2)
```

- [ ] **Step 4: Implement line-series renderer**

Create `paper_plot/templates/line_series.py`:

```python
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import LINE_COLORS, LINE_MARKERS, apply_paper_axes, style_legend


def render_line_series(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(4.8, 2.2))
    series_order = ordered_unique(frame["series"], config.order.get("series"))

    for index, series in enumerate(series_order):
        subset = frame[frame["series"] == series].sort_values("x")
        ax.plot(
            subset["x"],
            subset["y"],
            label=str(series),
            color=LINE_COLORS[index % len(LINE_COLORS)],
            marker=LINE_MARKERS[index % len(LINE_MARKERS)],
            linewidth=1.8,
            markersize=5,
        )

    ax.axhline(1.0, color="#808080", linestyle="--", linewidth=1.2, label="_y=1.0")
    ax.set_ylabel("ShareGPT\nNorm. Latency (s/token)")
    ax.set_xlabel("")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(series_order))
    fig.tight_layout()
    return fig
```

- [ ] **Step 5: Implement template dispatch**

Create `paper_plot/templates/__init__.py`:

```python
from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.templates.line_series import render_line_series


def render_plot(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    if config.plot_type == "line_series":
        return render_line_series(frame, config)
    raise ValueError(f"Unsupported plot type: {config.plot_type}")
```

- [ ] **Step 6: Run line-series template tests to verify they pass**

Run:

```bash
uv run pytest tests/test_line_series_template.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add paper_plot/templates tests/test_line_series_template.py
git commit -m "feat: add line series template"
```

---

### Task 5: Grouped Bar Renderer

**Files:**
- Create: `paper_plot/templates/grouped_bar.py`
- Modify: `paper_plot/templates/__init__.py`
- Test: `tests/test_grouped_bar_template.py`

- [ ] **Step 1: Write failing grouped-bar tests**

Create `tests/test_grouped_bar_template.py`:

```python
from pathlib import Path

import pandas as pd

from paper_plot.config import PlotConfig
from paper_plot.templates import render_plot
from paper_plot.templates.grouped_bar import render_grouped_bar


def sample_config() -> PlotConfig:
    return PlotConfig(
        plot_type="grouped_bar",
        data_path=Path("data.csv"),
        columns={
            "group": "Scale",
            "model": "Model",
            "batch": "Batch",
            "series": "System",
            "value": "Throughput",
        },
        output_path=Path("figures/grouped"),
        order={
            "group": ["Small Scale", "Large Scale"],
            "model": ["RetNet", "GLA"],
            "batch": [32, 64],
            "series": ["GPU", "GPU+Q", "Pimba"],
        },
    )


def test_render_grouped_bar_draws_one_patch_per_row():
    frame = pd.DataFrame(
        {
            "group": ["Small Scale", "Small Scale", "Small Scale"],
            "model": ["RetNet", "RetNet", "RetNet"],
            "batch": [32, 32, 32],
            "series": ["GPU", "GPU+Q", "Pimba"],
            "value": [1.0, 1.2, 1.6],
        }
    )

    fig = render_grouped_bar(frame, sample_config())
    ax = fig.axes[0]

    assert len(ax.patches) == 3
    assert ax.get_ylabel() == "Normalized Throughput"
    assert ax.get_legend() is not None


def test_render_plot_dispatches_grouped_bar():
    frame = pd.DataFrame(
        {
            "group": ["Small Scale"],
            "model": ["RetNet"],
            "batch": [32],
            "series": ["GPU"],
            "value": [1.0],
        }
    )

    fig = render_plot(frame, sample_config())

    assert len(fig.axes[0].patches) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_grouped_bar_template.py -v
```

Expected: FAIL with import errors for `paper_plot.templates.grouped_bar`.

- [ ] **Step 3: Implement grouped-bar renderer**

Create `paper_plot/templates/grouped_bar.py`:

```python
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import SERIES_COLORS, apply_paper_axes, style_legend


def render_grouped_bar(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(10.5, 2.6))

    group_order = ordered_unique(frame["group"], config.order.get("group"))
    model_order = ordered_unique(frame["model"], config.order.get("model"))
    batch_order = ordered_unique(frame["batch"], config.order.get("batch"))
    series_order = ordered_unique(frame["series"], config.order.get("series"))

    bar_width = 0.16
    cluster_gap = 0.35
    x_cursor = 0.0
    centers: list[float] = []
    batch_labels: list[str] = []
    boundary_positions: list[float] = []

    for group in group_order:
        group_start = x_cursor
        for model in model_order:
            model_frame = frame[(frame["group"] == group) & (frame["model"] == model)]
            if model_frame.empty:
                continue
            model_start = x_cursor
            for batch in batch_order:
                subset = model_frame[model_frame["batch"] == batch]
                if subset.empty:
                    continue
                center = x_cursor
                centers.append(center)
                batch_labels.append(str(batch))
                for index, series in enumerate(series_order):
                    row = subset[subset["series"] == series]
                    if row.empty:
                        continue
                    offset = (index - (len(series_order) - 1) / 2) * bar_width
                    ax.bar(
                        center + offset,
                        float(row.iloc[0]["value"]),
                        width=bar_width,
                        label=str(series) if not ax.containers or str(series) not in ax.get_legend_handles_labels()[1] else None,
                        color=SERIES_COLORS.get(str(series), f"C{index}"),
                        edgecolor="black",
                        linewidth=1.0,
                    )
                x_cursor += 1.0
            model_center = (model_start + x_cursor - 1.0) / 2
            ax.text(model_center, -0.18, str(model), ha="center", va="top", transform=ax.get_xaxis_transform())
            boundary_positions.append(x_cursor - 0.5)
            x_cursor += cluster_gap
        group_center = (group_start + x_cursor - cluster_gap - 1.0) / 2
        ax.text(group_center, -0.38, str(group), ha="center", va="top", transform=ax.get_xaxis_transform())

    for boundary in boundary_positions[:-1]:
        ax.axvline(boundary, color="black", linewidth=1.0, ymin=-0.28, ymax=0.0, clip_on=False)

    ax.set_xticks(centers)
    ax.set_xticklabels(batch_labels)
    ax.set_ylabel("Normalized Throughput")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(series_order))
    fig.subplots_adjust(bottom=0.34, top=0.78)
    return fig
```

- [ ] **Step 4: Update template dispatch**

Modify `paper_plot/templates/__init__.py`:

```python
from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.templates.grouped_bar import render_grouped_bar
from paper_plot.templates.line_series import render_line_series


def render_plot(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    if config.plot_type == "grouped_bar":
        return render_grouped_bar(frame, config)
    if config.plot_type == "line_series":
        return render_line_series(frame, config)
    raise ValueError(f"Unsupported plot type: {config.plot_type}")
```

- [ ] **Step 5: Run grouped-bar tests to verify they pass**

Run:

```bash
uv run pytest tests/test_grouped_bar_template.py -v
```

Expected: PASS.

- [ ] **Step 6: Run all current template tests**

Run:

```bash
uv run pytest tests/test_line_series_template.py tests/test_grouped_bar_template.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add paper_plot/templates tests/test_grouped_bar_template.py
git commit -m "feat: add grouped bar template"
```

---

### Task 6: Stacked Bar Renderer

**Files:**
- Create: `paper_plot/templates/stacked_bar.py`
- Modify: `paper_plot/templates/__init__.py`
- Test: `tests/test_stacked_bar_template.py`

- [ ] **Step 1: Write failing stacked-bar tests**

Create `tests/test_stacked_bar_template.py`:

```python
from pathlib import Path

import pandas as pd

from paper_plot.config import PlotConfig
from paper_plot.templates import render_plot
from paper_plot.templates.stacked_bar import render_stacked_bar


def sample_config() -> PlotConfig:
    return PlotConfig(
        plot_type="stacked_bar",
        data_path=Path("data.csv"),
        columns={
            "model": "Model",
            "batch": "Batch",
            "series": "System",
            "stack": "Component",
            "value": "Latency",
        },
        output_path=Path("figures/stacked"),
        order={
            "model": ["RetNet"],
            "batch": [32],
            "series": ["GPU", "Pimba"],
            "stack": ["State Update", "GEMM"],
        },
    )


def test_render_stacked_bar_draws_one_patch_per_stack_segment():
    frame = pd.DataFrame(
        {
            "model": ["RetNet", "RetNet", "RetNet", "RetNet"],
            "batch": [32, 32, 32, 32],
            "series": ["GPU", "GPU", "Pimba", "Pimba"],
            "stack": ["State Update", "GEMM", "State Update", "GEMM"],
            "value": [0.5, 0.3, 0.2, 0.1],
        }
    )

    fig = render_stacked_bar(frame, sample_config())
    ax = fig.axes[0]

    assert len(ax.patches) == 4
    assert ax.get_ylabel() == "Normalized Latency"
    assert ax.get_legend() is not None


def test_render_plot_dispatches_stacked_bar():
    frame = pd.DataFrame(
        {
            "model": ["RetNet"],
            "batch": [32],
            "series": ["GPU"],
            "stack": ["GEMM"],
            "value": [0.3],
        }
    )

    fig = render_plot(frame, sample_config())

    assert len(fig.axes[0].patches) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_stacked_bar_template.py -v
```

Expected: FAIL with import errors for `paper_plot.templates.stacked_bar`.

- [ ] **Step 3: Add stack palette to shared style**

Modify `paper_plot/templates/style.py` to include:

```python
STACK_COLORS = {
    "State Update": "#2F5D57",
    "Attention": "#5AA89D",
    "Discretization": "#7FA37B",
    "Causal Conv": "#A8B878",
    "GEMM": "#E3C960",
    "Communication": "#D46F4D",
    "Others": "#984A45",
}
```

- [ ] **Step 4: Implement stacked-bar renderer**

Create `paper_plot/templates/stacked_bar.py`:

```python
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import STACK_COLORS, apply_paper_axes, style_legend


def render_stacked_bar(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(10.5, 2.8))

    model_order = ordered_unique(frame["model"], config.order.get("model"))
    batch_order = ordered_unique(frame["batch"], config.order.get("batch"))
    series_order = ordered_unique(frame["series"], config.order.get("series"))
    stack_order = ordered_unique(frame["stack"], config.order.get("stack"))

    x_cursor = 0.0
    x_positions: list[float] = []
    series_labels: list[str] = []
    batch_centers: list[tuple[float, str]] = []
    model_centers: list[tuple[float, str]] = []

    for model in model_order:
        model_start = x_cursor
        for batch in batch_order:
            batch_start = x_cursor
            for series in series_order:
                subset = frame[
                    (frame["model"] == model)
                    & (frame["batch"] == batch)
                    & (frame["series"] == series)
                ]
                if subset.empty:
                    continue
                bottom = 0.0
                for index, stack in enumerate(stack_order):
                    row = subset[subset["stack"] == stack]
                    if row.empty:
                        continue
                    value = float(row.iloc[0]["value"])
                    ax.bar(
                        x_cursor,
                        value,
                        bottom=bottom,
                        width=0.72,
                        label=str(stack) if str(stack) not in ax.get_legend_handles_labels()[1] else None,
                        color=STACK_COLORS.get(str(stack), f"C{index}"),
                        edgecolor="black",
                        linewidth=0.8,
                    )
                    bottom += value
                x_positions.append(x_cursor)
                series_labels.append(str(series))
                x_cursor += 1.0
            if x_cursor > batch_start:
                batch_centers.append(((batch_start + x_cursor - 1.0) / 2, str(batch)))
                x_cursor += 0.35
        if x_cursor > model_start:
            model_centers.append(((model_start + x_cursor - 1.35) / 2, str(model)))
            x_cursor += 0.55

    ax.set_xticks(x_positions)
    ax.set_xticklabels(series_labels, rotation=90)
    for center, label in batch_centers:
        ax.text(center, -0.26, label, ha="center", va="top", transform=ax.get_xaxis_transform())
    for center, label in model_centers:
        ax.text(center, -0.46, label, ha="center", va="top", transform=ax.get_xaxis_transform())

    ax.set_ylabel("Normalized Latency")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(stack_order))
    fig.subplots_adjust(bottom=0.42, top=0.76)
    return fig
```

- [ ] **Step 5: Update template dispatch**

Modify `paper_plot/templates/__init__.py`:

```python
from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.templates.grouped_bar import render_grouped_bar
from paper_plot.templates.line_series import render_line_series
from paper_plot.templates.stacked_bar import render_stacked_bar


def render_plot(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    if config.plot_type == "grouped_bar":
        return render_grouped_bar(frame, config)
    if config.plot_type == "stacked_bar":
        return render_stacked_bar(frame, config)
    if config.plot_type == "line_series":
        return render_line_series(frame, config)
    raise ValueError(f"Unsupported plot type: {config.plot_type}")
```

- [ ] **Step 6: Run stacked-bar tests to verify they pass**

Run:

```bash
uv run pytest tests/test_stacked_bar_template.py -v
```

Expected: PASS.

- [ ] **Step 7: Run all template tests**

Run:

```bash
uv run pytest tests/test_line_series_template.py tests/test_grouped_bar_template.py tests/test_stacked_bar_template.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add paper_plot/templates tests/test_stacked_bar_template.py
git commit -m "feat: add stacked bar template"
```

---

### Task 7: CLI Entry Point And End-To-End Smoke Test

**Files:**
- Create: `paper_plot/cli.py`
- Modify: `main.py`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI smoke test**

Create `tests/test_cli.py`:

```python
from pathlib import Path

from paper_plot.cli import main


def test_cli_generates_pdf_and_png_for_line_series(tmp_path):
    csv_path = tmp_path / "line.csv"
    csv_path.write_text(
        "System,X,Latency\nGPU,1,0.1\nGPU,2,0.2\nPimba,1,0.08\nPimba,2,0.12\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "figures" / "line"
    config_path = tmp_path / "line.yaml"
    config_path.write_text(
        f"""
plot:
  type: line_series
data:
  path: {csv_path}
  columns:
    series: System
    x: X
    y: Latency
output:
  path: {output_path}
order:
  series: [GPU, Pimba]
""",
        encoding="utf-8",
    )

    exit_code = main([str(config_path)])

    assert exit_code == 0
    assert output_path.with_suffix(".pdf").exists()
    assert output_path.with_suffix(".png").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_cli.py -v
```

Expected: FAIL with import errors for `paper_plot.cli`.

- [ ] **Step 3: Implement CLI**

Create `paper_plot/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import matplotlib.pyplot as plt

from paper_plot.config import ConfigError, load_config
from paper_plot.data import DataError, load_plot_data
from paper_plot.export import export_figure
from paper_plot.templates import render_plot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-plot",
        description="Generate paper-ready benchmark plots from CSV and YAML.",
    )
    parser.add_argument("config", help="Path to the YAML plot configuration")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        frame = load_plot_data(config)
        fig = render_plot(frame, config)
        written = export_figure(fig, config.output_path)
    except (ConfigError, DataError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        plt.close("all")

    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Delegate `main.py` to CLI**

Replace `main.py` with:

```python
from paper_plot.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Add console script to `pyproject.toml`**

Add this section after `[project.optional-dependencies]`:

```toml
[project.scripts]
paper-plot = "paper_plot.cli:main"
```

- [ ] **Step 6: Run CLI test to verify it passes**

Run:

```bash
uv run pytest tests/test_cli.py -v
```

Expected: PASS.

- [ ] **Step 7: Run the full test suite**

Run:

```bash
uv run pytest
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add paper_plot/cli.py main.py pyproject.toml tests/test_cli.py
git commit -m "feat: add paper plot cli"
```

---

### Task 8: README Usage Example And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with minimal usage**

Modify `README.md`:

```markdown
# paper-plot-program

Template gallery for paper-ready benchmark figures.

## Usage

Install dependencies:

```bash
uv sync --extra dev
```

Create a YAML config:

```yaml
plot:
  type: line_series
data:
  path: data/line.csv
  columns:
    series: System
    x: X
    y: Latency
output:
  path: figures/line
order:
  series: [GPU, Pimba]
```

Generate the figure:

```bash
uv run paper-plot config.yaml
```

The command writes both `figures/line.pdf` and `figures/line.png`.

## Plot Types

- `grouped_bar`: grouped normalized throughput bars
- `stacked_bar`: stacked normalized latency breakdown bars
- `line_series`: normalized latency curves with a `y = 1.0` reference line
```

- [ ] **Step 2: Run full tests**

Run:

```bash
uv run pytest
```

Expected: PASS.

- [ ] **Step 3: Build package**

Run:

```bash
uv build
```

Expected: command completes and creates distribution artifacts under `dist/`.

- [ ] **Step 4: Check working tree**

Run:

```bash
git status --short
```

Expected: only intended README changes and any generated `dist/` files. Do not commit `dist/` unless the user explicitly asks.

- [ ] **Step 5: Commit README update**

```bash
git add README.md
git commit -m "docs: document paper plot cli usage"
```

---

## Implementation Notes

- Keep production changes test-driven. For each task, run the task-specific test and verify the expected failure before adding implementation code.
- Do not add YAML style overrides in this version. The approved design keeps YAML simple and puts reference-like styling in template presets.
- Preserve existing user changes in the working tree. At the time this plan was written, there were unrelated changes in `AGENTS.md`, deleted older docs, and untracked `docs/reference/` images.
- Matplotlib visual fidelity should be validated structurally in tests first. Pixel-perfect tests are out of scope for this first implementation.

## Self-Review

- Spec coverage: config loading, CSV mapping, ordering, three plot templates, dual export, CLI, error messages, and tests are covered by Tasks 1-8.
- Placeholder scan: no placeholder tokens or open-ended implementation steps remain.
- Type consistency: `PlotConfig`, `load_config`, `load_plot_data`, `render_plot`, `export_figure`, and `main` signatures are introduced before later tasks use them.
