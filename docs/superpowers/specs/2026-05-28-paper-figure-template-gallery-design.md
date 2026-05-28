# Paper Figure Template Gallery Design

Date: 2026-05-28

## Goal

Build a lightweight Python template gallery for generating paper-ready figures like the provided throughput, latency-breakdown, and multi-panel latency plots from user-provided CSV or Excel data.

The first version is not a general chart grammar and not a GUI. It is a practical set of editable scripts and notebooks with shared helpers for publication-style plotting.

## Approved Direction

Use the notebook/script template gallery approach.

The project should provide concrete templates that a researcher can copy, edit, and rerun while writing a paper. Repeated low-level work such as data loading, validation, matplotlib styling, output directory creation, and multi-format export should live in shared Python helpers.

## Project Shape

The intended structure is:

```text
paper_plot/
  __init__.py
  data.py
  style.py
  export.py
  validation.py
templates/
  grouped_bar_throughput.py
  stacked_latency_breakdown.py
  multi_panel_latency.py
notebooks/
  grouped_bar_throughput.ipynb
  stacked_latency_breakdown.ipynb
  multi_panel_latency.ipynb
examples/
  README.md
  data/
    grouped_bar_throughput.csv
    stacked_latency_breakdown.csv
    multi_panel_latency.csv
  configs/
    grouped_bar_throughput.yaml
    stacked_latency_breakdown.yaml
    multi_panel_latency.yaml
tests/
  test_data.py
  test_export.py
  test_validation.py
  test_templates.py
```

## Data And Config Format

Measurement values belong in CSV or Excel files. Presentation choices belong in YAML config files.

CSV files should use long-form data so pandas can group and filter rows consistently. YAML config should control figure size, output name, labels, colors, legend order, axis limits, and export formats.

The renderer must not infer or compute normalized values in version 1. If a figure needs normalized throughput or normalized latency, the CSV must contain the final normalized value.

Grouped bar input requires a value column such as:

```csv
scale,model,batch,system,normalized_throughput
small,RetNet,32,GPU,1.00
small,RetNet,32,GPU+Q,1.25
small,RetNet,32,GPU+PIM,1.32
small,RetNet,32,Pimba,1.60
```

Stacked latency input uses component shares:

```csv
model,batch,system,component,latency_share
RetNet,32,GPU,State Update,0.52
RetNet,32,GPU,GEMM,0.30
RetNet,32,GPU,Communication,0.10
```

Multi-panel latency input uses workload, metric, system, x, and y columns:

```csv
workload,metric,system,request_rate,normalized_latency
ShareGPT,avg_per_token,LoongServe,0.1,0.07
ShareGPT,avg_input_token,vLLM,0.5,0.30
```

Example YAML:

```yaml
figure:
  width: 7.2
  height: 3.2
  dpi: 300
  font_family: DejaVu Serif
  output_name: figure12

style:
  palette:
    GPU: "#4db6ac"
    GPU+Q: "#fff3cd"
    GPU+PIM: "#e9c95d"
    Pimba: "#e76f51"

axes:
  y_label: "Normalized Throughput"
  y_limit: [0, 4.2]
  grid: true

export:
  formats: ["pdf", "svg", "png"]
```

## Template Behavior

### `grouped_bar_throughput.py`

Generate grouped bar charts like the throughput figure.

The template should:

- read CSV or Excel input;
- require explicit `normalized_throughput` values;
- plot the provided values directly;
- group the x-axis by scale, model, batch, and system;
- support model and scale separator lines;
- support lower group labels;
- export PDF, SVG, and PNG by default.

It must not compute GPU baselines, ratios, or normalized values.

### `stacked_latency_breakdown.py`

Generate stacked bar charts like the latency breakdown figure.

The template should:

- read component-level latency shares;
- stack bars by component in YAML-defined order;
- group bars by model, batch, and system;
- support rotated system labels;
- support component legend ordering;
- support separator lines between model groups;
- export PDF, SVG, and PNG by default.

### `multi_panel_latency.py`

Generate multi-panel line plots like the serving latency figure.

The template should:

- build a subplot grid from workload rows and metric columns;
- draw one line per system in each panel;
- support marker, color, and line-style settings per system;
- draw a dashed y=1.0 reference line when configured;
- support shared legend placement;
- support panel-specific x/y limit overrides;
- export PDF, SVG, and PNG by default.

## Visual Fidelity

The goal is to reproduce the information structure and publication style of the reference figures, not to make pixel-identical copies.

The default style should use matplotlib settings suitable for papers:

- consistent font sizes;
- visible tick and axis line widths;
- compact legends;
- vector-friendly hatch and marker choices;
- gridlines only when helpful;
- no decorative web-style styling.

## Error Handling

Validation should be explicit and small.

The program should:

- stop with a clear error when required CSV columns are missing;
- warn when YAML lists a system or component that is absent from the data;
- warn when data contains a system or component without a YAML style entry, then use a default matplotlib style;
- create export directories when they do not exist;
- avoid automatic normalization, unit conversion, and data inference.

## Testing

Testing should focus on reproducible execution and helper correctness.

Required tests:

- each template runs on sample CSV and YAML;
- each template creates PDF, SVG, and PNG outputs;
- missing required columns produce a clear validation error;
- shared helpers load CSV and Excel data;
- shared helpers create output paths;
- export helper loops over requested formats.

Visual regression testing is out of scope for version 1. Smoke tests are enough as long as the generated files exist and are non-empty.

## Documentation

Documentation should be usage-first.

`README.md` should explain:

- installation;
- how to run each template;
- why values must already be normalized in CSV;
- how CSV data and YAML presentation config are separated;
- how to export PDF, SVG, and PNG.

`examples/README.md` should document the schema for each template and point to runnable sample commands.

Each template script should include a top-level docstring with:

- expected input columns;
- config path argument;
- example command;
- output files.

## Explicit Non-Goals

Version 1 will not include:

- GUI;
- automatic normalization;
- arbitrary chart grammar;
- interactive plotting;
- paper-specific automatic layout inference;
- pixel-perfect cloning of the supplied figures.

## Success Criteria

The design is successful when a user can:

1. edit an example CSV with measured values;
2. adjust a YAML config for labels, colors, and output names;
3. run one of the template scripts;
4. receive PDF, SVG, and PNG files suitable for paper drafting;
5. understand from the docs that all normalized values must be prepared before plotting.
