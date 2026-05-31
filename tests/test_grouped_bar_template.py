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


def test_render_grouped_bar_draws_duplicate_series_rows():
    frame = pd.DataFrame(
        {
            "group": ["Small Scale", "Small Scale"],
            "model": ["RetNet", "RetNet"],
            "batch": [32, 32],
            "series": ["GPU", "GPU"],
            "value": [1.0, 1.1],
        }
    )

    fig = render_grouped_bar(frame, sample_config())
    duplicate_patches = sorted(fig.axes[0].patches, key=lambda patch: patch.get_x())

    assert len(duplicate_patches) == len(frame)
    assert duplicate_patches[0].get_x() + duplicate_patches[0].get_width() <= (
        duplicate_patches[1].get_x()
    )


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
