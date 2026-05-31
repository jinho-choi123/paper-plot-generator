from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import (
    LINE_COLORS,
    LINE_MARKERS,
    apply_paper_axes,
    style_legend,
)


def render_line_series(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(4.8, 2.2))
    series_order = ordered_unique(frame["series"], config.order.get("series"))

    for index, series in enumerate(series_order):
        subset = frame[frame["series"] == series].sort_values("x")
        ax.plot(
            subset["x"],
            subset["y"],
            label=str(series),
            color=LINE_COLORS[index % len(LINE_COLORS)],
            marker=LINE_MARKERS[index % len(LINE_MARKERS)],
            linewidth=1.8,
            markersize=5,
        )

    ax.axhline(1.0, color="#808080", linestyle="--", linewidth=1.2, label="_y=1.0")
    ax.set_ylabel("ShareGPT\nNorm. Latency (s/token)")
    ax.set_xlabel("")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(series_order))
    fig.tight_layout()
    return fig
