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
