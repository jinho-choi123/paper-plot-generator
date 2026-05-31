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


def test_rejects_non_string_plot_type(tmp_path):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        """
plot:
  type: [grouped_bar]
data:
  path: data.csv
  columns: {}
output:
  path: figures/out
""",
    )

    with pytest.raises(ConfigError, match="plot.type must be a string"):
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


@pytest.mark.parametrize(
    ("field_yaml", "expected_message"),
    [
        ("  path: [bad]", "data.path must be a string"),
        ("  path: null", "output.path must be a string"),
    ],
)
def test_rejects_invalid_path_field_types(tmp_path, field_yaml, expected_message):
    if "data.path" in expected_message:
        data_path_yaml = field_yaml
        output_path_yaml = "  path: figures/out"
    else:
        data_path_yaml = "  path: data.csv"
        output_path_yaml = field_yaml

    config_path = write_yaml(
        tmp_path / "plot.yaml",
        f"""
plot:
  type: grouped_bar
data:
{data_path_yaml}
  columns:
    group: Scale
    model: Model
    batch: Batch
    series: System
    value: Throughput
output:
{output_path_yaml}
""",
    )

    with pytest.raises(ConfigError, match=expected_message):
        load_config(config_path)


def test_rejects_invalid_column_mapping_values(tmp_path):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        """
plot:
  type: grouped_bar
data:
  path: data.csv
  columns:
    group: Scale
    model: Model
    batch: Batch
    series: System
    value: null
output:
  path: figures/out
""",
    )

    with pytest.raises(ConfigError, match="data.columns.value must be a string"):
        load_config(config_path)


@pytest.mark.parametrize("order_yaml", ["  batch: 32", "  batch: abc"])
def test_rejects_non_list_order_values(tmp_path, order_yaml):
    config_path = write_yaml(
        tmp_path / "plot.yaml",
        f"""
plot:
  type: grouped_bar
data:
  path: data.csv
  columns:
    group: Scale
    model: Model
    batch: Batch
    series: System
    value: Throughput
output:
  path: figures/out
order:
{order_yaml}
""",
    )

    with pytest.raises(ConfigError, match="order.batch must be a list"):
        load_config(config_path)
