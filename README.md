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

Generated files are written to `examples/figures/` as both PDF and PNG.

## Plot Types

- `grouped_bar`: grouped normalized throughput bars
- `stacked_bar`: stacked normalized latency breakdown bars
- `line_series`: normalized latency curves with a `y = 1.0` reference line
