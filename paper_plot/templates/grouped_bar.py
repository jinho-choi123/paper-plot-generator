from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import SERIES_COLORS, apply_paper_axes, style_legend


def render_grouped_bar(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(10.5, 2.6))

    group_order = ordered_unique(frame["group"], config.order.get("group"))
    model_order = ordered_unique(frame["model"], config.order.get("model"))
    batch_order = ordered_unique(frame["batch"], config.order.get("batch"))
    series_order = ordered_unique(frame["series"], config.order.get("series"))

    bar_width = 0.16
    cluster_gap = 0.35
    x_cursor = 0.0
    centers: list[float] = []
    batch_labels: list[str] = []
    boundary_positions: list[float] = []

    for group in group_order:
        group_start = x_cursor
        for model in model_order:
            model_frame = frame[(frame["group"] == group) & (frame["model"] == model)]
            if model_frame.empty:
                continue
            model_start = x_cursor
            for batch in batch_order:
                subset = model_frame[model_frame["batch"] == batch]
                if subset.empty:
                    continue
                center = x_cursor
                centers.append(center)
                batch_labels.append(str(batch))
                for index, series in enumerate(series_order):
                    row = subset[subset["series"] == series]
                    if row.empty:
                        continue
                    offset = (index - (len(series_order) - 1) / 2) * bar_width
                    _, labels = ax.get_legend_handles_labels()
                    label = str(series) if str(series) not in labels else None
                    ax.bar(
                        center + offset,
                        float(row.iloc[0]["value"]),
                        width=bar_width,
                        label=label,
                        color=SERIES_COLORS.get(str(series), f"C{index}"),
                        edgecolor="black",
                        linewidth=1.0,
                    )
                x_cursor += 1.0
            model_center = (model_start + x_cursor - 1.0) / 2
            ax.text(
                model_center,
                -0.18,
                str(model),
                ha="center",
                va="top",
                transform=ax.get_xaxis_transform(),
            )
            boundary_positions.append(x_cursor - 0.5)
            x_cursor += cluster_gap
        group_center = (group_start + x_cursor - cluster_gap - 1.0) / 2
        ax.text(
            group_center,
            -0.38,
            str(group),
            ha="center",
            va="top",
            transform=ax.get_xaxis_transform(),
        )

    for boundary in boundary_positions[:-1]:
        ax.axvline(
            boundary,
            color="black",
            linewidth=1.0,
            ymin=-0.28,
            ymax=0.0,
            clip_on=False,
        )

    ax.set_xticks(centers)
    ax.set_xticklabels(batch_labels)
    ax.set_ylabel("Normalized Throughput")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(series_order))
    fig.subplots_adjust(bottom=0.34, top=0.78)
    return fig
