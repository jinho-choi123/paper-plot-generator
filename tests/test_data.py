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


def test_load_plot_data_supports_reusing_source_column(tmp_path):
    csv_path = write_csv(tmp_path / "line.csv", "System,Value\nGPU,1\n")
    config = PlotConfig(
        plot_type="line_series",
        data_path=csv_path,
        columns={"series": "System", "x": "Value", "y": "Value"},
        output_path=Path("figures/line"),
        order={},
    )

    frame = load_plot_data(config)

    assert list(frame.columns) == ["series", "x", "y"]
    assert frame.loc[0, "x"] == 1
    assert frame.loc[0, "y"] == 1


def test_ordered_unique_uses_explicit_order_then_remaining_values():
    values = ["GPU+PIM", "GPU", "Pimba", "GPU"]

    assert ordered_unique(values, ["GPU", "GPU+PIM"]) == ["GPU", "GPU+PIM", "Pimba"]


def test_ordered_unique_deduplicates_explicit_order():
    assert ordered_unique(["B", "A"], ["A", "A"]) == ["A", "B"]
