# Paper Figure Template Gallery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python template gallery that turns CSV/Excel data plus YAML presentation configs into paper-ready PDF/SVG/PNG figures for grouped throughput bars, stacked latency breakdowns, and multi-panel latency curves.

**Architecture:** Keep figure scripts editable and concrete, with shared helpers for loading data/configs, validating schemas, applying matplotlib paper style, computing repeated bar positions, and exporting formats. Values are plotted exactly as provided in CSV/Excel; v1 does not compute normalized values.

**Tech Stack:** Python 3.10+, pandas, matplotlib, PyYAML, openpyxl, pytest.

---

## File Structure

Create or modify these files:

- Modify: `pyproject.toml` for package metadata, runtime deps, dev deps, pytest config, and hatch build config.
- Create: `paper_plot/__init__.py` to expose common helper APIs.
- Create: `paper_plot/config.py` to load YAML and resolve common config sections.
- Create: `paper_plot/data.py` to load CSV/Excel input.
- Create: `paper_plot/validation.py` to enforce required columns and style/data consistency warnings.
- Create: `paper_plot/export.py` to write PDF/SVG/PNG outputs.
- Create: `paper_plot/style.py` to apply consistent paper-style matplotlib rcParams and resolve palettes.
- Create: `paper_plot/layout.py` to compute grouped bar x positions and separator locations.
- Create: `templates/grouped_bar_throughput.py` for Image #1-style normalized throughput bars.
- Create: `templates/stacked_latency_breakdown.py` for Image #1-style latency breakdown bars.
- Create: `templates/multi_panel_latency.py` for Image #2-style serving latency panels.
- Create: `examples/data/*.csv` and `examples/configs/*.yaml` for runnable sample inputs.
- Create: `tests/conftest.py`, `tests/test_data.py`, `tests/test_validation.py`, `tests/test_export.py`, `tests/test_layout.py`, and `tests/test_templates.py`.
- Modify: `README.md` for installation and usage.
- Create: `examples/README.md` for input schemas and sample commands.
- Create: `notebooks/*.ipynb` as thin examples that call the scripts/helpers without duplicating plotting logic.

## Task 1: Project Metadata And Test Harness

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/conftest.py`

- [ ] **Step 1: Update package metadata and dependencies**

Replace `pyproject.toml` with:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "paper-plot-program"
version = "0.1.0"
description = "Template gallery for paper-ready benchmark figures"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "matplotlib>=3.8",
    "openpyxl>=3.1",
    "pandas>=2.1",
    "PyYAML>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.hatch.build.targets.wheel]
packages = ["paper_plot"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Add matplotlib test backend setup**

Create `tests/conftest.py`:

```python
import matplotlib

matplotlib.use("Agg")
```

- [ ] **Step 3: Install the package in editable mode**

Run:

```bash
python -m pip install -e ".[dev]"
```

Expected: dependencies install successfully and the package imports from the workspace.

- [ ] **Step 4: Run the empty test suite**

Run:

```bash
python -m pytest -q
```

Expected: pytest exits successfully with no tests collected, or with only collection output if local pytest behavior differs.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/conftest.py
git commit -m "chore: configure paper plot package"
```

## Task 2: Data, Config, Validation, And Export Helpers

**Files:**
- Create: `paper_plot/__init__.py`
- Create: `paper_plot/config.py`
- Create: `paper_plot/data.py`
- Create: `paper_plot/validation.py`
- Create: `paper_plot/export.py`
- Test: `tests/test_data.py`
- Test: `tests/test_validation.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write failing tests for data/config loading**

Create `tests/test_data.py`:

```python
from pathlib import Path

import pandas as pd

from paper_plot.config import load_config
from paper_plot.data import load_table


def test_load_table_reads_csv(tmp_path: Path):
    path = tmp_path / "data.csv"
    path.write_text("model,value\nRetNet,1.0\n", encoding="utf-8")

    df = load_table(path)

    assert list(df.columns) == ["model", "value"]
    assert df.loc[0, "model"] == "RetNet"


def test_load_table_reads_excel(tmp_path: Path):
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"model": ["RetNet"], "value": [1.0]}).to_excel(path, index=False)

    df = load_table(path)

    assert list(df.columns) == ["model", "value"]
    assert df.loc[0, "value"] == 1.0


def test_load_config_reads_yaml(tmp_path: Path):
    path = tmp_path / "config.yaml"
    path.write_text("figure:\n  output_name: figure12\n", encoding="utf-8")

    config = load_config(path)

    assert config["figure"]["output_name"] == "figure12"
```

- [ ] **Step 2: Write failing tests for validation**

Create `tests/test_validation.py`:

```python
import warnings

import pandas as pd
import pytest

from paper_plot.validation import SchemaError, require_columns, warn_for_style_mismatches


def test_require_columns_accepts_complete_schema():
    df = pd.DataFrame({"model": ["RetNet"], "value": [1.0]})

    require_columns(df, ["model", "value"], source="throughput")


def test_require_columns_reports_missing_columns():
    df = pd.DataFrame({"model": ["RetNet"]})

    with pytest.raises(SchemaError, match="throughput is missing required columns: value"):
        require_columns(df, ["model", "value"], source="throughput")


def test_warn_for_style_mismatches_reports_absent_and_unstyled_values():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_for_style_mismatches(
            data_values={"GPU", "Pimba"},
            configured_values={"GPU", "GPU+Q"},
            style_values={"GPU"},
            label="system",
        )

    messages = [str(item.message) for item in caught]
    assert "Configured system values not present in data: GPU+Q" in messages
    assert "Data system values without explicit style: Pimba" in messages
```

- [ ] **Step 3: Write failing tests for export**

Create `tests/test_export.py`:

```python
from pathlib import Path

import matplotlib.pyplot as plt

from paper_plot.export import export_figure


def test_export_figure_writes_requested_formats(tmp_path: Path):
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])

    paths = export_figure(
        fig,
        output_dir=tmp_path,
        output_name="figure_test",
        formats=["pdf", "svg", "png"],
        dpi=120,
    )

    assert [path.suffix for path in paths] == [".pdf", ".svg", ".png"]
    assert all(path.exists() for path in paths)
    assert all(path.stat().st_size > 0 for path in paths)
```

- [ ] **Step 4: Run helper tests and confirm they fail**

Run:

```bash
python -m pytest tests/test_data.py tests/test_validation.py tests/test_export.py -q
```

Expected: FAIL because `paper_plot` helper modules do not exist yet.

- [ ] **Step 5: Implement helper modules**

Create `paper_plot/config.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


Config = dict[str, Any]


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config must be a YAML mapping: {config_path}")
    return loaded


def section(config: Config, name: str) -> Config:
    value = config.get(name, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{name}' must be a mapping")
    return value


def nested(config: Config, *keys: str, default: Any = None) -> Any:
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
```

Create `paper_plot/data.py`:

```python
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_table(path: str | Path) -> pd.DataFrame:
    data_path = Path(path)
    suffix = data_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(data_path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(data_path)
    raise ValueError(f"Unsupported data file type '{suffix}' for {data_path}")
```

Create `paper_plot/validation.py`:

```python
from __future__ import annotations

import warnings
from collections.abc import Iterable

import pandas as pd


class SchemaError(ValueError):
    """Raised when input data does not match a template schema."""


def require_columns(df: pd.DataFrame, required: Iterable[str], source: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        joined = ", ".join(missing)
        raise SchemaError(f"{source} is missing required columns: {joined}")


def ordered_unique(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = str(value)
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def warn_for_style_mismatches(
    data_values: set[str],
    configured_values: set[str],
    style_values: set[str],
    label: str,
) -> None:
    absent = sorted(configured_values - data_values)
    if absent:
        warnings.warn(
            f"Configured {label} values not present in data: {', '.join(absent)}",
            stacklevel=2,
        )

    unstyled = sorted(data_values - style_values)
    if unstyled:
        warnings.warn(
            f"Data {label} values without explicit style: {', '.join(unstyled)}",
            stacklevel=2,
        )
```

Create `paper_plot/export.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from matplotlib.figure import Figure


def export_figure(
    fig: Figure,
    output_dir: str | Path,
    output_name: str,
    formats: Iterable[str],
    dpi: int = 300,
) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for fmt in formats:
        clean_fmt = str(fmt).lower().lstrip(".")
        path = directory / f"{output_name}.{clean_fmt}"
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        paths.append(path)
    return paths
```

Create `paper_plot/__init__.py`:

```python
from paper_plot.config import load_config
from paper_plot.data import load_table
from paper_plot.export import export_figure
from paper_plot.validation import SchemaError, require_columns

__all__ = [
    "SchemaError",
    "export_figure",
    "load_config",
    "load_table",
    "require_columns",
]
```

- [ ] **Step 6: Run helper tests and confirm they pass**

Run:

```bash
python -m pytest tests/test_data.py tests/test_validation.py tests/test_export.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add paper_plot tests/test_data.py tests/test_validation.py tests/test_export.py
git commit -m "feat: add data validation and export helpers"
```

## Task 3: Style And Bar Layout Helpers

**Files:**
- Create: `paper_plot/style.py`
- Create: `paper_plot/layout.py`
- Test: `tests/test_layout.py`

- [ ] **Step 1: Write failing tests for bar layout**

Create `tests/test_layout.py`:

```python
import pandas as pd

from paper_plot.layout import build_grouped_bar_layout


def test_build_grouped_bar_layout_assigns_positions_by_group_and_series():
    df = pd.DataFrame(
        {
            "model": ["RetNet", "RetNet", "RetNet", "RetNet"],
            "batch": [32, 32, 64, 64],
            "system": ["GPU", "Pimba", "GPU", "Pimba"],
        }
    )

    layout = build_grouped_bar_layout(
        df,
        group_columns=["model", "batch"],
        series_column="system",
        series_order=["GPU", "Pimba"],
    )

    assert len(layout.groups) == 2
    assert layout.groups[0].key == ("RetNet", "32")
    assert layout.groups[0].positions["GPU"] < layout.groups[0].positions["Pimba"]
    assert layout.groups[0].center < layout.groups[1].center
    assert layout.tick_positions == [layout.groups[0].center, layout.groups[1].center]
    assert layout.tick_labels == ["32", "64"]
```

- [ ] **Step 2: Run layout test and confirm it fails**

Run:

```bash
python -m pytest tests/test_layout.py -q
```

Expected: FAIL because `paper_plot.layout` does not exist yet.

- [ ] **Step 3: Implement paper style helper**

Create `paper_plot/style.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import matplotlib.pyplot as plt

from paper_plot.config import nested, section


DEFAULT_PALETTE = [
    "#4db6ac",
    "#fff3cd",
    "#e9c95d",
    "#e76f51",
    "#1f77b4",
    "#2ca02c",
    "#9467bd",
    "#d62728",
]


def apply_paper_style(config: Mapping[str, Any]) -> None:
    figure = section(dict(config), "figure")
    font_family = figure.get("font_family", "DejaVu Serif")
    plt.rcParams.update(
        {
            "font.family": font_family,
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 8,
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "lines.linewidth": 1.2,
            "patch.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def palette_for(config: Mapping[str, Any], names: list[str]) -> dict[str, str]:
    configured = nested(dict(config), "style", "palette", default={}) or {}
    palette: dict[str, str] = {}
    for index, name in enumerate(names):
        palette[name] = configured.get(name, DEFAULT_PALETTE[index % len(DEFAULT_PALETTE)])
    return palette


def line_style_for(config: Mapping[str, Any], name: str) -> dict[str, Any]:
    configured = nested(dict(config), "style", "line_styles", name, default={}) or {}
    return dict(configured)
```

- [ ] **Step 4: Implement grouped bar layout helper**

Create `paper_plot/layout.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd


@dataclass(frozen=True)
class BarGroup:
    key: tuple[str, ...]
    center: float
    positions: dict[str, float]


@dataclass(frozen=True)
class BarLayout:
    groups: list[BarGroup]
    tick_positions: list[float]
    tick_labels: list[str]
    separators: list[float]


def _row_key(row: pd.Series, columns: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(row[column]) for column in columns)


def unique_group_keys(df: pd.DataFrame, columns: Sequence[str]) -> list[tuple[str, ...]]:
    keys: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for _, row in df.iterrows():
        key = _row_key(row, columns)
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def build_grouped_bar_layout(
    df: pd.DataFrame,
    group_columns: Sequence[str],
    series_column: str,
    series_order: Sequence[str],
    bar_width: float = 0.18,
    group_gap: float = 0.18,
    major_gap: float = 0.45,
) -> BarLayout:
    keys = unique_group_keys(df, group_columns)
    groups: list[BarGroup] = []
    separators: list[float] = []
    cursor = 0.0
    previous_major: str | None = None

    for key in keys:
        current_major = key[0] if key else None
        if previous_major is not None and current_major != previous_major:
            separators.append(cursor - group_gap / 2)
            cursor += major_gap

        positions = {
            str(series): cursor + index * bar_width
            for index, series in enumerate(series_order)
        }
        center = sum(positions.values()) / len(positions)
        groups.append(BarGroup(key=key, center=center, positions=positions))
        cursor += len(series_order) * bar_width + group_gap
        previous_major = current_major

    return BarLayout(
        groups=groups,
        tick_positions=[group.center for group in groups],
        tick_labels=[group.key[-1] for group in groups],
        separators=separators,
    )
```

- [ ] **Step 5: Run layout tests**

Run:

```bash
python -m pytest tests/test_layout.py -q
```

Expected: PASS.

- [ ] **Step 6: Run all helper tests**

Run:

```bash
python -m pytest tests/test_data.py tests/test_validation.py tests/test_export.py tests/test_layout.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add paper_plot/style.py paper_plot/layout.py tests/test_layout.py
git commit -m "feat: add paper style and bar layout helpers"
```

## Task 4: Example Data And YAML Configs

**Files:**
- Create: `examples/data/grouped_bar_throughput.csv`
- Create: `examples/data/stacked_latency_breakdown.csv`
- Create: `examples/data/multi_panel_latency.csv`
- Create: `examples/configs/grouped_bar_throughput.yaml`
- Create: `examples/configs/stacked_latency_breakdown.yaml`
- Create: `examples/configs/multi_panel_latency.yaml`

- [ ] **Step 1: Add grouped bar example data**

Create `examples/data/grouped_bar_throughput.csv`:

```csv
scale,model,batch,system,normalized_throughput
small,RetNet,32,GPU,1.00
small,RetNet,32,GPU+Q,1.24
small,RetNet,32,GPU+PIM,1.33
small,RetNet,32,Pimba,1.62
small,RetNet,64,GPU,1.00
small,RetNet,64,GPU+Q,1.38
small,RetNet,64,GPU+PIM,1.32
small,RetNet,64,Pimba,2.16
small,GLA,32,GPU,1.00
small,GLA,32,GPU+Q,1.09
small,GLA,32,GPU+PIM,1.13
small,GLA,32,Pimba,1.21
large,RetNet,32,GPU,1.00
large,RetNet,32,GPU+Q,1.48
large,RetNet,32,GPU+PIM,1.82
large,RetNet,32,Pimba,2.78
large,OPT,128,GPU,1.00
large,OPT,128,GPU+Q,1.56
large,OPT,128,GPU+PIM,1.90
large,OPT,128,Pimba,2.63
```

- [ ] **Step 2: Add stacked latency example data**

Create `examples/data/stacked_latency_breakdown.csv`:

```csv
model,batch,system,component,latency_share
RetNet,32,GPU,State Update,0.52
RetNet,32,GPU,GEMM,0.30
RetNet,32,GPU,Communication,0.10
RetNet,32,GPU,Others,0.06
RetNet,32,GPU+Q,State Update,0.24
RetNet,32,GPU+Q,GEMM,0.42
RetNet,32,GPU+Q,Communication,0.14
RetNet,32,GPU+Q,Others,0.08
RetNet,32,Pimba,State Update,0.06
RetNet,32,Pimba,GEMM,0.24
RetNet,32,Pimba,Communication,0.16
RetNet,32,Pimba,Others,0.02
GLA,64,GPU,State Update,0.52
GLA,64,GPU,GEMM,0.27
GLA,64,GPU,Communication,0.13
GLA,64,GPU,Others,0.06
GLA,64,Pimba,State Update,0.04
GLA,64,Pimba,GEMM,0.31
GLA,64,Pimba,Communication,0.12
GLA,64,Pimba,Others,0.04
```

- [ ] **Step 3: Add multi-panel line example data**

Create `examples/data/multi_panel_latency.csv`:

```csv
workload,metric,system,request_rate,normalized_latency
ShareGPT,avg_per_token,LoongServe,0.05,0.04
ShareGPT,avg_per_token,LoongServe,0.20,0.08
ShareGPT,avg_per_token,LoongServe,0.40,0.18
ShareGPT,avg_per_token,vLLM,0.05,0.08
ShareGPT,avg_per_token,vLLM,0.20,0.16
ShareGPT,avg_per_token,vLLM,0.45,1.10
ShareGPT,avg_input_token,LoongServe,0.05,0.03
ShareGPT,avg_input_token,LoongServe,0.20,0.09
ShareGPT,avg_input_token,LoongServe,0.40,0.20
ShareGPT,avg_input_token,LightLLM w/ SplitFuse,0.05,0.07
ShareGPT,avg_input_token,LightLLM w/ SplitFuse,0.20,0.18
ShareGPT,avg_input_token,LightLLM w/ SplitFuse,0.45,0.42
ShareGPT,avg_output_token,LoongServe,0.05,0.06
ShareGPT,avg_output_token,LoongServe,0.20,0.10
ShareGPT,avg_output_token,LoongServe,0.40,0.16
Leval,avg_per_token,LoongServe,0.05,0.05
Leval,avg_per_token,LoongServe,0.50,0.08
Leval,avg_per_token,LoongServe,1.50,0.16
Leval,avg_per_token,LightLLM w/ SplitFuse,0.05,0.06
Leval,avg_per_token,LightLLM w/ SplitFuse,0.50,0.20
Leval,avg_per_token,LightLLM w/ SplitFuse,1.20,0.88
```

- [ ] **Step 4: Add grouped bar YAML**

Create `examples/configs/grouped_bar_throughput.yaml`:

```yaml
figure:
  width: 7.2
  height: 2.8
  dpi: 300
  font_family: DejaVu Serif
  output_name: grouped_bar_throughput

data:
  scale_order: ["small", "large"]
  model_order: ["RetNet", "GLA", "OPT"]
  batch_order: [32, 64, 128]
  system_order: ["GPU", "GPU+Q", "GPU+PIM", "Pimba"]

style:
  palette:
    GPU: "#4db6ac"
    GPU+Q: "#fff3cd"
    GPU+PIM: "#e9c95d"
    Pimba: "#e76f51"

axes:
  y_label: "Normalized Throughput"
  y_limit: [0, 3.0]
  grid: true

legend:
  location: "upper center"
  columns: 4

export:
  directory: "outputs"
  formats: ["pdf", "svg", "png"]
```

- [ ] **Step 5: Add stacked latency YAML**

Create `examples/configs/stacked_latency_breakdown.yaml`:

```yaml
figure:
  width: 7.2
  height: 3.0
  dpi: 300
  font_family: DejaVu Serif
  output_name: stacked_latency_breakdown

data:
  model_order: ["RetNet", "GLA"]
  batch_order: [32, 64]
  system_order: ["GPU", "GPU+Q", "Pimba"]
  component_order: ["State Update", "GEMM", "Communication", "Others"]

style:
  palette:
    State Update: "#2f6f73"
    GEMM: "#e9c95d"
    Communication: "#e76f51"
    Others: "#913f3f"

axes:
  y_label: "Normalized Latency"
  y_limit: [0, 1.05]
  grid: true

legend:
  location: "upper center"
  columns: 4

export:
  directory: "outputs"
  formats: ["pdf", "svg", "png"]
```

- [ ] **Step 6: Add multi-panel latency YAML**

Create `examples/configs/multi_panel_latency.yaml`:

```yaml
figure:
  width: 7.2
  height: 5.8
  dpi: 300
  font_family: DejaVu Serif
  output_name: multi_panel_latency

data:
  workload_order: ["ShareGPT", "Leval"]
  metric_order: ["avg_per_token", "avg_input_token", "avg_output_token"]
  system_order: ["LoongServe", "vLLM", "LightLLM w/ SplitFuse"]

style:
  line_styles:
    LoongServe:
      color: "#1f77b4"
      marker: "o"
    vLLM:
      color: "#ff7f0e"
      marker: "s"
    LightLLM w/ SplitFuse:
      color: "#d62728"
      marker: "D"

axes:
  x_label: "Request Rate (req/s)"
  y_label: "Norm. Latency (s/token)"
  y_limit: [0, 1.2]
  reference_y: 1.0
  grid: false

legend:
  location: "upper center"
  columns: 3

export:
  directory: "outputs"
  formats: ["pdf", "svg", "png"]
```

- [ ] **Step 7: Commit**

```bash
git add examples/data examples/configs
git commit -m "docs: add runnable figure examples"
```

## Task 5: Grouped Bar Throughput Template

**Files:**
- Create: `templates/grouped_bar_throughput.py`
- Test: `tests/test_templates.py`

- [ ] **Step 1: Write failing grouped-bar smoke test**

Create `tests/test_templates.py`:

```python
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run_template(script: str, data: str, config: str, out_dir: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "templates" / script),
            "--data",
            str(ROOT / "examples" / "data" / data),
            "--config",
            str(ROOT / "examples" / "configs" / config),
            "--out-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def assert_exports(out_dir: Path, output_name: str) -> None:
    for suffix in ("pdf", "svg", "png"):
        path = out_dir / f"{output_name}.{suffix}"
        assert path.exists()
        assert path.stat().st_size > 0


def test_grouped_bar_template_exports_all_formats(tmp_path: Path):
    run_template(
        "grouped_bar_throughput.py",
        "grouped_bar_throughput.csv",
        "grouped_bar_throughput.yaml",
        tmp_path,
    )

    assert_exports(tmp_path, "grouped_bar_throughput")
```

- [ ] **Step 2: Run grouped-bar smoke test and confirm it fails**

Run:

```bash
python -m pytest tests/test_templates.py::test_grouped_bar_template_exports_all_formats -q
```

Expected: FAIL because `templates/grouped_bar_throughput.py` does not exist yet.

- [ ] **Step 3: Implement grouped bar template**

Create `templates/grouped_bar_throughput.py`:

```python
"""Generate grouped normalized-throughput bar charts.

Required CSV columns:
    scale, model, batch, system, normalized_throughput

Example:
    python templates/grouped_bar_throughput.py \
        --data examples/data/grouped_bar_throughput.csv \
        --config examples/configs/grouped_bar_throughput.yaml \
        --out-dir outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from paper_plot.config import load_config, nested, section
from paper_plot.data import load_table
from paper_plot.export import export_figure
from paper_plot.layout import build_grouped_bar_layout
from paper_plot.style import apply_paper_style, palette_for
from paper_plot.validation import require_columns, warn_for_style_mismatches


REQUIRED_COLUMNS = ["scale", "model", "batch", "system", "normalized_throughput"]


def _ordered(config: dict, key: str, fallback: list[str]) -> list[str]:
    values = nested(config, "data", key, default=fallback)
    return [str(value) for value in values]


def _prepare(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    require_columns(df, REQUIRED_COLUMNS, source="grouped throughput data")
    prepared = df.copy()
    prepared["scale"] = prepared["scale"].astype(str)
    prepared["model"] = prepared["model"].astype(str)
    prepared["batch"] = prepared["batch"].astype(str)
    prepared["system"] = prepared["system"].astype(str)

    scale_order = _ordered(config, "scale_order", list(prepared["scale"].drop_duplicates()))
    model_order = _ordered(config, "model_order", list(prepared["model"].drop_duplicates()))
    batch_order = _ordered(config, "batch_order", list(prepared["batch"].drop_duplicates()))
    system_order = _ordered(config, "system_order", list(prepared["system"].drop_duplicates()))

    prepared["scale"] = pd.Categorical(prepared["scale"], categories=scale_order, ordered=True)
    prepared["model"] = pd.Categorical(prepared["model"], categories=model_order, ordered=True)
    prepared["batch"] = pd.Categorical(prepared["batch"], categories=batch_order, ordered=True)
    prepared["system"] = pd.Categorical(prepared["system"], categories=system_order, ordered=True)
    return prepared.sort_values(["scale", "model", "batch", "system"])


def build_figure(data_path: str | Path, config_path: str | Path) -> plt.Figure:
    config = load_config(config_path)
    apply_paper_style(config)
    df = _prepare(load_table(data_path), config)

    system_order = _ordered(config, "system_order", list(df["system"].astype(str).drop_duplicates()))
    style_values = set((nested(config, "style", "palette", default={}) or {}).keys())
    warn_for_style_mismatches(
        data_values=set(df["system"].astype(str)),
        configured_values=set(system_order),
        style_values=style_values,
        label="system",
    )

    layout = build_grouped_bar_layout(
        df,
        group_columns=["scale", "model", "batch"],
        series_column="system",
        series_order=system_order,
    )
    palette = palette_for(config, system_order)

    figure_cfg = section(config, "figure")
    fig, ax = plt.subplots(
        figsize=(float(figure_cfg.get("width", 7.2)), float(figure_cfg.get("height", 2.8)))
    )

    for group in layout.groups:
        scale, model, batch = group.key
        rows = df[
            (df["scale"].astype(str) == scale)
            & (df["model"].astype(str) == model)
            & (df["batch"].astype(str) == batch)
        ]
        for system in system_order:
            value_rows = rows[rows["system"].astype(str) == system]
            if value_rows.empty:
                continue
            ax.bar(
                group.positions[system],
                float(value_rows.iloc[0]["normalized_throughput"]),
                width=0.16,
                label=system,
                color=palette[system],
                edgecolor="black",
            )

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    legend_cfg = section(config, "legend")
    ax.legend(
        unique.values(),
        unique.keys(),
        loc=legend_cfg.get("location", "upper center"),
        ncol=int(legend_cfg.get("columns", len(system_order))),
        bbox_to_anchor=(0.5, 1.22),
        frameon=True,
    )

    axes_cfg = section(config, "axes")
    ax.set_ylabel(str(axes_cfg.get("y_label", "Normalized Throughput")))
    if "y_limit" in axes_cfg:
        ax.set_ylim(*axes_cfg["y_limit"])
    if axes_cfg.get("grid", False):
        ax.yaxis.grid(True, linestyle="--", alpha=0.45)
        ax.set_axisbelow(True)

    for separator in layout.separators:
        ax.axvline(separator, color="black", linewidth=0.8)

    ax.set_xticks(layout.tick_positions)
    ax.set_xticklabels(layout.tick_labels)
    ax.tick_params(axis="x", length=0)
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to CSV or Excel data")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--out-dir", default=None, help="Override export directory")
    args = parser.parse_args()

    config = load_config(args.config)
    fig = build_figure(args.data, args.config)
    figure_cfg = section(config, "figure")
    export_cfg = section(config, "export")
    output_dir = args.out_dir or export_cfg.get("directory", "outputs")
    output_name = figure_cfg.get("output_name", "grouped_bar_throughput")
    formats = export_cfg.get("formats", ["pdf", "svg", "png"])
    dpi = int(figure_cfg.get("dpi", 300))
    export_figure(fig, output_dir, output_name, formats, dpi)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run grouped-bar smoke test**

Run:

```bash
python -m pytest tests/test_templates.py::test_grouped_bar_template_exports_all_formats -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/grouped_bar_throughput.py tests/test_templates.py
git commit -m "feat: add grouped throughput template"
```

## Task 6: Stacked Latency Breakdown Template

**Files:**
- Create: `templates/stacked_latency_breakdown.py`
- Modify: `tests/test_templates.py`

- [ ] **Step 1: Add failing stacked-bar smoke test**

Append this test to `tests/test_templates.py`:

```python

def test_stacked_latency_template_exports_all_formats(tmp_path: Path):
    run_template(
        "stacked_latency_breakdown.py",
        "stacked_latency_breakdown.csv",
        "stacked_latency_breakdown.yaml",
        tmp_path,
    )

    assert_exports(tmp_path, "stacked_latency_breakdown")
```

- [ ] **Step 2: Run stacked-bar test and confirm it fails**

Run:

```bash
python -m pytest tests/test_templates.py::test_stacked_latency_template_exports_all_formats -q
```

Expected: FAIL because `templates/stacked_latency_breakdown.py` does not exist yet.

- [ ] **Step 3: Implement stacked latency template**

Create `templates/stacked_latency_breakdown.py`:

```python
"""Generate stacked latency-breakdown bar charts.

Required CSV columns:
    model, batch, system, component, latency_share

Example:
    python templates/stacked_latency_breakdown.py \
        --data examples/data/stacked_latency_breakdown.csv \
        --config examples/configs/stacked_latency_breakdown.yaml \
        --out-dir outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from paper_plot.config import load_config, nested, section
from paper_plot.data import load_table
from paper_plot.export import export_figure
from paper_plot.layout import build_grouped_bar_layout
from paper_plot.style import apply_paper_style, palette_for
from paper_plot.validation import require_columns, warn_for_style_mismatches


REQUIRED_COLUMNS = ["model", "batch", "system", "component", "latency_share"]


def _ordered(config: dict, key: str, fallback: list[str]) -> list[str]:
    values = nested(config, "data", key, default=fallback)
    return [str(value) for value in values]


def _prepare(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    require_columns(df, REQUIRED_COLUMNS, source="stacked latency data")
    prepared = df.copy()
    for column in ["model", "batch", "system", "component"]:
        prepared[column] = prepared[column].astype(str)

    model_order = _ordered(config, "model_order", list(prepared["model"].drop_duplicates()))
    batch_order = _ordered(config, "batch_order", list(prepared["batch"].drop_duplicates()))
    system_order = _ordered(config, "system_order", list(prepared["system"].drop_duplicates()))
    component_order = _ordered(config, "component_order", list(prepared["component"].drop_duplicates()))

    prepared["model"] = pd.Categorical(prepared["model"], categories=model_order, ordered=True)
    prepared["batch"] = pd.Categorical(prepared["batch"], categories=batch_order, ordered=True)
    prepared["system"] = pd.Categorical(prepared["system"], categories=system_order, ordered=True)
    prepared["component"] = pd.Categorical(prepared["component"], categories=component_order, ordered=True)
    return prepared.sort_values(["model", "batch", "system", "component"])


def build_figure(data_path: str | Path, config_path: str | Path) -> plt.Figure:
    config = load_config(config_path)
    apply_paper_style(config)
    df = _prepare(load_table(data_path), config)

    system_order = _ordered(config, "system_order", list(df["system"].astype(str).drop_duplicates()))
    component_order = _ordered(config, "component_order", list(df["component"].astype(str).drop_duplicates()))
    style_values = set((nested(config, "style", "palette", default={}) or {}).keys())
    warn_for_style_mismatches(
        data_values=set(df["component"].astype(str)),
        configured_values=set(component_order),
        style_values=style_values,
        label="component",
    )

    layout = build_grouped_bar_layout(
        df.drop_duplicates(["model", "batch", "system"]),
        group_columns=["model", "batch"],
        series_column="system",
        series_order=system_order,
    )
    palette = palette_for(config, component_order)

    figure_cfg = section(config, "figure")
    fig, ax = plt.subplots(
        figsize=(float(figure_cfg.get("width", 7.2)), float(figure_cfg.get("height", 3.0)))
    )

    for group in layout.groups:
        model, batch = group.key
        for system in system_order:
            rows = df[
                (df["model"].astype(str) == model)
                & (df["batch"].astype(str) == batch)
                & (df["system"].astype(str) == system)
            ]
            bottom = 0.0
            for component in component_order:
                value_rows = rows[rows["component"].astype(str) == component]
                value = float(value_rows.iloc[0]["latency_share"]) if not value_rows.empty else 0.0
                ax.bar(
                    group.positions[system],
                    value,
                    bottom=bottom,
                    width=0.16,
                    color=palette[component],
                    edgecolor="black",
                    label=component,
                )
                bottom += value

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    legend_cfg = section(config, "legend")
    ax.legend(
        unique.values(),
        unique.keys(),
        loc=legend_cfg.get("location", "upper center"),
        ncol=int(legend_cfg.get("columns", len(component_order))),
        bbox_to_anchor=(0.5, 1.22),
        frameon=True,
    )

    axes_cfg = section(config, "axes")
    ax.set_ylabel(str(axes_cfg.get("y_label", "Normalized Latency")))
    if "y_limit" in axes_cfg:
        ax.set_ylim(*axes_cfg["y_limit"])
    if axes_cfg.get("grid", False):
        ax.yaxis.grid(True, linestyle="--", alpha=0.45)
        ax.set_axisbelow(True)

    for separator in layout.separators:
        ax.axvline(separator, color="black", linewidth=0.8)

    ax.set_xticks(layout.tick_positions)
    ax.set_xticklabels(layout.tick_labels)
    ax.tick_params(axis="x", length=0)
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to CSV or Excel data")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--out-dir", default=None, help="Override export directory")
    args = parser.parse_args()

    config = load_config(args.config)
    fig = build_figure(args.data, args.config)
    figure_cfg = section(config, "figure")
    export_cfg = section(config, "export")
    output_dir = args.out_dir or export_cfg.get("directory", "outputs")
    output_name = figure_cfg.get("output_name", "stacked_latency_breakdown")
    formats = export_cfg.get("formats", ["pdf", "svg", "png"])
    dpi = int(figure_cfg.get("dpi", 300))
    export_figure(fig, output_dir, output_name, formats, dpi)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run stacked-bar smoke test**

Run:

```bash
python -m pytest tests/test_templates.py::test_stacked_latency_template_exports_all_formats -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/stacked_latency_breakdown.py tests/test_templates.py
git commit -m "feat: add stacked latency template"
```

## Task 7: Multi-Panel Latency Template

**Files:**
- Create: `templates/multi_panel_latency.py`
- Modify: `tests/test_templates.py`

- [ ] **Step 1: Add failing multi-panel smoke test**

Append this test to `tests/test_templates.py`:

```python

def test_multi_panel_latency_template_exports_all_formats(tmp_path: Path):
    run_template(
        "multi_panel_latency.py",
        "multi_panel_latency.csv",
        "multi_panel_latency.yaml",
        tmp_path,
    )

    assert_exports(tmp_path, "multi_panel_latency")
```

- [ ] **Step 2: Run multi-panel test and confirm it fails**

Run:

```bash
python -m pytest tests/test_templates.py::test_multi_panel_latency_template_exports_all_formats -q
```

Expected: FAIL because `templates/multi_panel_latency.py` does not exist yet.

- [ ] **Step 3: Implement multi-panel latency template**

Create `templates/multi_panel_latency.py`:

```python
"""Generate multi-panel normalized-latency line charts.

Required CSV columns:
    workload, metric, system, request_rate, normalized_latency

Example:
    python templates/multi_panel_latency.py \
        --data examples/data/multi_panel_latency.csv \
        --config examples/configs/multi_panel_latency.yaml \
        --out-dir outputs
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from paper_plot.config import load_config, nested, section
from paper_plot.data import load_table
from paper_plot.export import export_figure
from paper_plot.style import apply_paper_style, line_style_for
from paper_plot.validation import require_columns, warn_for_style_mismatches


REQUIRED_COLUMNS = ["workload", "metric", "system", "request_rate", "normalized_latency"]


def _ordered(config: dict, key: str, fallback: list[str]) -> list[str]:
    values = nested(config, "data", key, default=fallback)
    return [str(value) for value in values]


def _prepare(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    require_columns(df, REQUIRED_COLUMNS, source="multi-panel latency data")
    prepared = df.copy()
    for column in ["workload", "metric", "system"]:
        prepared[column] = prepared[column].astype(str)

    workload_order = _ordered(config, "workload_order", list(prepared["workload"].drop_duplicates()))
    metric_order = _ordered(config, "metric_order", list(prepared["metric"].drop_duplicates()))
    system_order = _ordered(config, "system_order", list(prepared["system"].drop_duplicates()))

    prepared["workload"] = pd.Categorical(prepared["workload"], categories=workload_order, ordered=True)
    prepared["metric"] = pd.Categorical(prepared["metric"], categories=metric_order, ordered=True)
    prepared["system"] = pd.Categorical(prepared["system"], categories=system_order, ordered=True)
    return prepared.sort_values(["workload", "metric", "system", "request_rate"])


def build_figure(data_path: str | Path, config_path: str | Path) -> plt.Figure:
    config = load_config(config_path)
    apply_paper_style(config)
    df = _prepare(load_table(data_path), config)

    workload_order = _ordered(config, "workload_order", list(df["workload"].astype(str).drop_duplicates()))
    metric_order = _ordered(config, "metric_order", list(df["metric"].astype(str).drop_duplicates()))
    system_order = _ordered(config, "system_order", list(df["system"].astype(str).drop_duplicates()))
    style_values = set((nested(config, "style", "line_styles", default={}) or {}).keys())
    warn_for_style_mismatches(
        data_values=set(df["system"].astype(str)),
        configured_values=set(system_order),
        style_values=style_values,
        label="system",
    )

    figure_cfg = section(config, "figure")
    fig, axes = plt.subplots(
        nrows=len(workload_order),
        ncols=len(metric_order),
        figsize=(float(figure_cfg.get("width", 7.2)), float(figure_cfg.get("height", 5.8))),
        squeeze=False,
        sharey=True,
    )

    axes_cfg = section(config, "axes")
    for row_index, workload in enumerate(workload_order):
        for col_index, metric in enumerate(metric_order):
            ax = axes[row_index][col_index]
            panel = df[
                (df["workload"].astype(str) == workload)
                & (df["metric"].astype(str) == metric)
            ]
            for system in system_order:
                series = panel[panel["system"].astype(str) == system]
                if series.empty:
                    continue
                style = line_style_for(config, system)
                ax.plot(
                    series["request_rate"],
                    series["normalized_latency"],
                    label=system,
                    marker=style.get("marker", "o"),
                    color=style.get("color"),
                    linestyle=style.get("linestyle", "-"),
                )

            if "reference_y" in axes_cfg:
                ax.axhline(float(axes_cfg["reference_y"]), color="0.45", linestyle="--", linewidth=0.8)
            if "y_limit" in axes_cfg:
                ax.set_ylim(*axes_cfg["y_limit"])
            if row_index == len(workload_order) - 1:
                ax.set_xlabel(str(axes_cfg.get("x_label", "Request Rate (req/s)")))
            if col_index == 0:
                ax.set_ylabel(str(axes_cfg.get("y_label", "Norm. Latency (s/token)")))
                ax.text(
                    -0.22,
                    0.5,
                    workload,
                    transform=ax.transAxes,
                    rotation=90,
                    ha="center",
                    va="center",
                    fontsize=9,
                )
            if row_index == 0:
                ax.set_title(metric.replace("_", " "))
            if axes_cfg.get("grid", False):
                ax.grid(True, linestyle="--", alpha=0.35)

    handles, labels = axes[0][0].get_legend_handles_labels()
    legend_cfg = section(config, "legend")
    fig.legend(
        handles,
        labels,
        loc=legend_cfg.get("location", "upper center"),
        ncol=int(legend_cfg.get("columns", len(system_order))),
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to CSV or Excel data")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--out-dir", default=None, help="Override export directory")
    args = parser.parse_args()

    config = load_config(args.config)
    fig = build_figure(args.data, args.config)
    figure_cfg = section(config, "figure")
    export_cfg = section(config, "export")
    output_dir = args.out_dir or export_cfg.get("directory", "outputs")
    output_name = figure_cfg.get("output_name", "multi_panel_latency")
    formats = export_cfg.get("formats", ["pdf", "svg", "png"])
    dpi = int(figure_cfg.get("dpi", 300))
    export_figure(fig, output_dir, output_name, formats, dpi)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all template smoke tests**

Run:

```bash
python -m pytest tests/test_templates.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/multi_panel_latency.py tests/test_templates.py
git commit -m "feat: add multi-panel latency template"
```

## Task 8: Documentation And Notebook Examples

**Files:**
- Modify: `README.md`
- Create: `examples/README.md`
- Create: `notebooks/grouped_bar_throughput.ipynb`
- Create: `notebooks/stacked_latency_breakdown.ipynb`
- Create: `notebooks/multi_panel_latency.ipynb`

- [ ] **Step 1: Write README**

Replace `README.md` with:

````markdown
# Paper Plot Program

Template gallery for generating paper-ready benchmark figures from CSV/Excel data and YAML presentation configs.

The project intentionally does not compute normalized values. If a plot shows normalized throughput or normalized latency, the CSV/Excel input must already contain the normalized value.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Run Templates

Grouped throughput bars:

```bash
python templates/grouped_bar_throughput.py \
  --data examples/data/grouped_bar_throughput.csv \
  --config examples/configs/grouped_bar_throughput.yaml \
  --out-dir outputs
```

Stacked latency breakdown:

```bash
python templates/stacked_latency_breakdown.py \
  --data examples/data/stacked_latency_breakdown.csv \
  --config examples/configs/stacked_latency_breakdown.yaml \
  --out-dir outputs
```

Multi-panel latency curves:

```bash
python templates/multi_panel_latency.py \
  --data examples/data/multi_panel_latency.csv \
  --config examples/configs/multi_panel_latency.yaml \
  --out-dir outputs
```

Each command writes PDF, SVG, and PNG by default.

## Data And Config Split

- CSV/Excel contains measured values.
- YAML contains presentation settings such as figure size, colors, labels, legend order, axis limits, and export formats.
- Plotting scripts render the provided values directly.

## Tests

```bash
python -m pytest -q
```
````

- [ ] **Step 2: Write examples README**

Create `examples/README.md`:

```markdown
# Examples

## Grouped Bar Throughput

Data: `examples/data/grouped_bar_throughput.csv`

Required columns:

- `scale`
- `model`
- `batch`
- `system`
- `normalized_throughput`

The `normalized_throughput` value is plotted exactly as provided.

## Stacked Latency Breakdown

Data: `examples/data/stacked_latency_breakdown.csv`

Required columns:

- `model`
- `batch`
- `system`
- `component`
- `latency_share`

Each `(model, batch, system)` bar stacks `latency_share` by `component`.

## Multi-Panel Latency

Data: `examples/data/multi_panel_latency.csv`

Required columns:

- `workload`
- `metric`
- `system`
- `request_rate`
- `normalized_latency`

Each `(workload, metric)` pair becomes a panel, and each `system` becomes a line.
```

- [ ] **Step 3: Create thin notebook examples**

Create each notebook as a minimal JSON notebook that imports the corresponding template and saves outputs. Use the same pattern below with the template-specific file names.

Create `notebooks/grouped_bar_throughput.ipynb`:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": ["# Grouped Bar Throughput\\n", "Render the grouped throughput example."]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from pathlib import Path\\n",
        "from paper_plot.config import load_config, section\\n",
        "from paper_plot.export import export_figure\\n",
        "from templates.grouped_bar_throughput import build_figure\\n",
        "\\n",
        "config_path = Path('../examples/configs/grouped_bar_throughput.yaml')\\n",
        "data_path = Path('../examples/data/grouped_bar_throughput.csv')\\n",
        "config = load_config(config_path)\\n",
        "fig = build_figure(data_path, config_path)\\n",
        "export_figure(fig, '../outputs', section(config, 'figure').get('output_name', 'grouped_bar_throughput'), section(config, 'export').get('formats', ['pdf', 'svg', 'png']))\\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

Create `notebooks/stacked_latency_breakdown.ipynb`:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": ["# Stacked Latency Breakdown\\n", "Render the stacked latency breakdown example."]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from pathlib import Path\\n",
        "from paper_plot.config import load_config, section\\n",
        "from paper_plot.export import export_figure\\n",
        "from templates.stacked_latency_breakdown import build_figure\\n",
        "\\n",
        "config_path = Path('../examples/configs/stacked_latency_breakdown.yaml')\\n",
        "data_path = Path('../examples/data/stacked_latency_breakdown.csv')\\n",
        "config = load_config(config_path)\\n",
        "fig = build_figure(data_path, config_path)\\n",
        "export_figure(fig, '../outputs', section(config, 'figure').get('output_name', 'stacked_latency_breakdown'), section(config, 'export').get('formats', ['pdf', 'svg', 'png']))\\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

Create `notebooks/multi_panel_latency.ipynb`:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": ["# Multi-Panel Latency\\n", "Render the multi-panel latency example."]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {},
      "outputs": [],
      "source": [
        "from pathlib import Path\\n",
        "from paper_plot.config import load_config, section\\n",
        "from paper_plot.export import export_figure\\n",
        "from templates.multi_panel_latency import build_figure\\n",
        "\\n",
        "config_path = Path('../examples/configs/multi_panel_latency.yaml')\\n",
        "data_path = Path('../examples/data/multi_panel_latency.csv')\\n",
        "config = load_config(config_path)\\n",
        "fig = build_figure(data_path, config_path)\\n",
        "export_figure(fig, '../outputs', section(config, 'figure').get('output_name', 'multi_panel_latency'), section(config, 'export').get('formats', ['pdf', 'svg', 'png']))\\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

- [ ] **Step 4: Run documentation-adjacent checks**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md examples/README.md notebooks
git commit -m "docs: document figure template usage"
```

## Task 9: Final Verification And Visual Smoke Check

**Files:**
- No new files expected unless fixes are needed.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 2: Generate all sample figures**

Run:

```bash
python templates/grouped_bar_throughput.py --data examples/data/grouped_bar_throughput.csv --config examples/configs/grouped_bar_throughput.yaml --out-dir outputs
python templates/stacked_latency_breakdown.py --data examples/data/stacked_latency_breakdown.csv --config examples/configs/stacked_latency_breakdown.yaml --out-dir outputs
python templates/multi_panel_latency.py --data examples/data/multi_panel_latency.csv --config examples/configs/multi_panel_latency.yaml --out-dir outputs
```

Expected:

```text
outputs/grouped_bar_throughput.pdf
outputs/grouped_bar_throughput.svg
outputs/grouped_bar_throughput.png
outputs/stacked_latency_breakdown.pdf
outputs/stacked_latency_breakdown.svg
outputs/stacked_latency_breakdown.png
outputs/multi_panel_latency.pdf
outputs/multi_panel_latency.svg
outputs/multi_panel_latency.png
```

- [ ] **Step 3: Confirm generated files are non-empty**

Run:

```bash
python - <<'PY'
from pathlib import Path

expected = [
    "grouped_bar_throughput.pdf",
    "grouped_bar_throughput.svg",
    "grouped_bar_throughput.png",
    "stacked_latency_breakdown.pdf",
    "stacked_latency_breakdown.svg",
    "stacked_latency_breakdown.png",
    "multi_panel_latency.pdf",
    "multi_panel_latency.svg",
    "multi_panel_latency.png",
]

for name in expected:
    path = Path("outputs") / name
    assert path.exists(), f"missing {path}"
    assert path.stat().st_size > 0, f"empty {path}"
print("all sample exports exist and are non-empty")
PY
```

Expected:

```text
all sample exports exist and are non-empty
```

- [ ] **Step 4: Manually inspect PNG previews**

Open the generated PNG files and check:

- grouped bars have separate system colors and visible y-axis/grid;
- stacked bars show component stacks and a shared legend;
- multi-panel figure shows workload rows, metric columns, system lines, and dashed y=1.0 reference line.

If a plot is visually broken, fix only the relevant template/style/layout code and rerun the targeted test plus the generation command.

- [ ] **Step 5: Commit any verification fixes**

If fixes were needed:

```bash
git add paper_plot templates tests examples README.md
git commit -m "fix: polish sample figure rendering"
```

If no fixes were needed, do not create an empty commit.

## Self-Review Checklist

- Spec coverage: The plan covers CSV/Excel loading, YAML config, three template scripts, PDF/SVG/PNG export, explicit normalized values, examples, docs, notebooks, and tests.
- Placeholder scan: No unresolved placeholder language remains. Each code step names exact files and provides concrete content.
- Type consistency: Helper names are consistent across tasks: `load_config`, `load_table`, `require_columns`, `export_figure`, `build_grouped_bar_layout`, and each template's `build_figure`.
- Scope check: The plan intentionally excludes GUI, automatic normalization, arbitrary chart grammar, visual regression tests, and pixel-perfect cloning.
