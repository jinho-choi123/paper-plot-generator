from pathlib import Path

import pandas as pd
import pytest

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
    assert [patch.get_height() for patch in ax.patches] == pytest.approx(
        [0.5, 0.3, 0.2, 0.1]
    )
    assert [patch.get_y() for patch in ax.patches] == pytest.approx(
        [0.0, 0.5, 0.0, 0.2]
    )
    assert ax.get_ylabel() == "Normalized Latency"
    assert ax.get_legend() is not None


def test_render_stacked_bar_sums_duplicate_stack_rows():
    frame = pd.DataFrame(
        {
            "model": ["RetNet", "RetNet", "RetNet"],
            "batch": [32, 32, 32],
            "series": ["GPU", "GPU", "GPU"],
            "stack": ["State Update", "GEMM", "GEMM"],
            "value": [0.5, 0.3, 0.2],
        }
    )

    fig = render_stacked_bar(frame, sample_config())
    ax = fig.axes[0]

    assert len(ax.patches) == 2
    assert [patch.get_height() for patch in ax.patches] == pytest.approx([0.5, 0.5])
    assert [patch.get_y() for patch in ax.patches] == pytest.approx([0.0, 0.5])


def test_render_stacked_bar_places_legend_above_plot_area():
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
    legend = fig.axes[0].get_legend()

    assert legend is not None
    assert legend.get_bbox_to_anchor()._bbox.y0 >= 1.30


def test_render_stacked_bar_uses_tall_figure():
    frame = pd.DataFrame(
        {
            "model": ["RetNet"],
            "batch": [32],
            "series": ["GPU"],
            "stack": ["GEMM"],
            "value": [0.3],
        }
    )

    fig = render_stacked_bar(frame, sample_config())

    assert fig.get_size_inches()[1] == 8.4


def test_render_stacked_bar_omits_batch_and_model_guides():
    frame = pd.DataFrame(
        {
            "model": ["RetNet", "RetNet", "RetNet", "RetNet"],
            "batch": [32, 32, 64, 64],
            "series": ["GPU", "Pimba", "GPU", "Pimba"],
            "stack": ["GEMM", "GEMM", "GEMM", "GEMM"],
            "value": [0.3, 0.2, 0.4, 0.25],
        }
    )
    config = PlotConfig(
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
            "batch": [32, 64],
            "series": ["GPU", "Pimba"],
            "stack": ["GEMM"],
        },
    )

    fig = render_stacked_bar(frame, config)
    ax = fig.axes[0]
    text_labels = [text.get_text() for text in ax.texts]

    assert "32" not in text_labels
    assert "64" not in text_labels
    assert "RetNet" not in text_labels
    assert "Batch >" not in text_labels
    assert "Model >" not in text_labels
    assert len(ax.lines) == 0


def test_render_stacked_bar_uses_tight_bar_spacing():
    frame = pd.DataFrame(
        {
            "model": ["RetNet", "RetNet"],
            "batch": [32, 32],
            "series": ["GPU", "Pimba"],
            "stack": ["GEMM", "GEMM"],
            "value": [0.3, 0.2],
        }
    )

    fig = render_stacked_bar(frame, sample_config())
    bar_centers = sorted(
        patch.get_x() + patch.get_width() / 2 for patch in fig.axes[0].patches
    )

    assert len(bar_centers) == 2
    assert bar_centers[1] - bar_centers[0] == pytest.approx(0.12)


def test_render_stacked_bar_uses_narrow_bars():
    frame = pd.DataFrame(
        {
            "model": ["RetNet"],
            "batch": [32],
            "series": ["GPU"],
            "stack": ["GEMM"],
            "value": [0.3],
        }
    )

    fig = render_stacked_bar(frame, sample_config())

    assert fig.axes[0].patches[0].get_width() == pytest.approx(0.08)


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
