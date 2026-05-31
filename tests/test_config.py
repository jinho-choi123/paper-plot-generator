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
