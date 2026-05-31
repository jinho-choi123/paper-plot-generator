# Paper Plot Generator Design

## Goal

Build a small Python package and CLI that generates paper-ready benchmark figures from CSV data and a simple YAML configuration file. The first version supports the three reference plot styles stored in `docs/reference/`:

- `grouped_bar`: normalized throughput grouped bar plot, based on `type1.png`
- `stacked_bar`: normalized latency breakdown stacked bar plot, based on `type2.png`
- `line_series`: ShareGPT normalized latency line plot, based on `type3.png`

The user should be able to reproduce each figure from one YAML file and one CSV file.

## User Workflow

The primary command is:

```bash
uv run paper-plot config.yaml
```

Each YAML file specifies the plot type, CSV path, CSV column mapping, and output path.

Example:

```yaml
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
```

Running this command generates both:

- `figures/throughput.pdf`
- `figures/throughput.png`

If `output.path` includes an extension, the implementation treats it as a stem and still writes both `.pdf` and `.png`.

## YAML Schema

Common required fields:

```yaml
plot:
  type: grouped_bar | stacked_bar | line_series
data:
  path: path/to/data.csv
  columns:
    ...
output:
  path: figures/name
```

Optional ordering:

```yaml
order:
  model: [RetNet, GLA, HGRN2, Mamba-2, Zamba2, OPT]
  batch: [32, 64, 128]
  series: [GPU, GPU+Q, GPU+PIM, Pimba]
```

If `order` is omitted, CSV appearance order is preserved.

### `grouped_bar`

Required columns:

```yaml
columns:
  group: Scale
  model: Model
  batch: Batch
  series: System
  value: Throughput
```

`grouped_bar` renders a hierarchy of `group > model > batch`, with one bar per `series` inside each batch. The `group` mapping is required so the implementation can match the reference layout directly.

### `stacked_bar`

Required columns:

```yaml
columns:
  model: Model
  batch: Batch
  series: System
  stack: Component
  value: Latency
```

`stacked_bar` renders a hierarchy of `model > batch > series`, with each system bar stacked by `stack` component.

### `line_series`

Required columns:

```yaml
columns:
  series: System
  x: X
  y: Latency
```

`line_series` renders one line per `series` and includes a dashed horizontal reference line at `y = 1.0`.

## Architecture

Implement the project under the configured `paper_plot/` package.

### `paper_plot/config.py`

Loads and validates YAML. It checks:

- required top-level fields
- supported `plot.type`
- required column mappings for the selected plot type
- output path presence

It returns a typed config object suitable for the rest of the pipeline.

### `paper_plot/data.py`

Reads CSV data with pandas and applies YAML column mappings. External CSV column names are renamed to internal standard names such as `model`, `batch`, `series`, `value`, `x`, and `y`.

It also applies optional ordering. If no order is provided for a field, the first appearance order in the CSV is preserved.

### `paper_plot/templates/`

Each template module accepts a normalized DataFrame and config object, then returns a Matplotlib `Figure`.

- `paper_plot/templates/grouped_bar.py`
- `paper_plot/templates/stacked_bar.py`
- `paper_plot/templates/line_series.py`

Templates do not save files directly. This keeps rendering testable and separates plotting from export.

### `paper_plot/export.py`

Saves a Matplotlib `Figure` to both `.pdf` and `.png`. It creates the output directory when needed.

### `paper_plot/cli.py`

Provides the `paper-plot` CLI entry point. It should stay thin:

1. Load config.
2. Load and normalize data.
3. Dispatch to the selected template.
4. Export PDF and PNG.

`main.py` can remain minimal or delegate to the CLI.

## Data Flow

```text
YAML config
  -> validate config
  -> read CSV
  -> rename columns to internal schema
  -> apply ordering
  -> render selected template
  -> save PDF + PNG
```

## Reference Style

The initial implementation prioritizes close reproduction of the reference images while keeping YAML simple. Style is encoded in template presets, not in required YAML fields.

Common style:

- white background
- thick black axis spines
- dashed gray horizontal grid
- compact legend with black border
- readable paper-oriented font sizes
- deterministic color palettes
- layout adjustments that avoid clipped labels

### `grouped_bar` Style

- `group > model > batch` hierarchical x-axis
- batch labels closest to bars
- model labels below batch labels
- group labels centered below model labels
- vertical divider lines at model and group boundaries
- default y-axis label: `Normalized Throughput`
- legend at top center
- GPU/GPU+Q/GPU+PIM/Pimba colors based on the reference palette

### `stacked_bar` Style

- `model > batch > series` hierarchical x-axis
- one stacked bar per system
- default y-axis label: `Normalized Latency`
- legend at top center
- muted component colors based on the reference palette
- y-axis range chosen from the data, with normalized latency plots naturally centered around the 0 to 1 range when applicable

### `line_series` Style

- one line per system
- distinct marker shapes and colors based on the reference
- dashed horizontal reference line at `y = 1.0`
- default y-axis label: `ShareGPT\nNorm. Latency (s/token)`
- x/y limits inferred from data

## Error Handling

The CLI should fail early with direct messages for:

- missing YAML file
- YAML parse errors
- unsupported `plot.type`
- missing required top-level fields
- missing required column mapping for the selected plot type
- mapped CSV column not found
- missing CSV file
- non-numeric values in required numeric columns
- output directory creation or file writing errors

Example messages:

```text
Missing required column mapping for grouped_bar: value
CSV column not found for mapping data.columns.value: Throughput
Unsupported plot type: pie_chart
```

## Testing Strategy

Use pytest and the existing non-interactive Matplotlib `Agg` backend.

Tests should cover:

- config loading for valid YAML
- config errors for unknown plot type and missing required fields
- data loading with column mapping
- data errors for missing CSV columns
- order preservation and explicit ordering
- each template returning a Matplotlib `Figure`
- expected high-level figure structure, such as legend presence, bar count, stack count, or line count
- export creating both `.pdf` and `.png`
- CLI smoke test from small CSV/YAML fixtures through generated outputs

Implementation should follow TDD: write a failing test for each behavior, verify the failure, then add the smallest implementation needed to pass.
