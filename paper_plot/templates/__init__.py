from __future__ import annotations

import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.templates.grouped_bar import render_grouped_bar
from paper_plot.templates.line_series import render_line_series


def render_plot(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    if config.plot_type == "grouped_bar":
        return render_grouped_bar(frame, config)
    if config.plot_type == "line_series":
        return render_line_series(frame, config)
    raise ValueError(f"Unsupported plot type: {config.plot_type}")
