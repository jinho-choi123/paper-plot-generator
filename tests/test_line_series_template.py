from pathlib import Path

import pandas as pd

from paper_plot.config import PlotConfig
from paper_plot.templates import render_plot
from paper_plot.templates.line_series import render_line_series


def test_render_line_series_returns_figure_with_one_line_per_series():
    frame = pd.DataFrame(
        {
            "series": ["GPU", "GPU", "Pimba", "Pimba"],
            "x": [1, 2, 1, 2],
            "y": [0.1, 0.2, 0.08, 0.12],
        }
    )
    config = PlotConfig(
        plot_type="line_series",
        data_path=Path("data.csv"),
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={"series": ["GPU", "Pimba"]},
    )

    fig = render_line_series(frame, config)
    ax = fig.axes[0]

    data_lines = [line for line in ax.lines if line.get_label() != "_y=1.0"]
    assert len(data_lines) == 2
    assert ax.get_ylabel() == "ShareGPT\nNorm. Latency (s/token)"
    assert ax.get_legend() is not None


def test_render_plot_dispatches_line_series():
    frame = pd.DataFrame({"series": ["GPU"], "x": [1], "y": [0.1]})
    config = PlotConfig(
        plot_type="line_series",
        data_path=Path("data.csv"),
        columns={"series": "System", "x": "X", "y": "Latency"},
        output_path=Path("figures/line"),
        order={},
    )

    fig = render_plot(frame, config)

    assert len(fig.axes) == 1
