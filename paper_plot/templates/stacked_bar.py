from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from paper_plot.config import PlotConfig
from paper_plot.data import ordered_unique
from paper_plot.templates.style import STACK_COLORS, apply_paper_axes, style_legend


def render_stacked_bar(frame: pd.DataFrame, config: PlotConfig) -> Figure:
    fig, ax = plt.subplots(figsize=(10.5, 2.8))

    model_order = ordered_unique(frame["model"], config.order.get("model"))
    batch_order = ordered_unique(frame["batch"], config.order.get("batch"))
    series_order = ordered_unique(frame["series"], config.order.get("series"))
    stack_order = ordered_unique(frame["stack"], config.order.get("stack"))

    x_cursor = 0.0
    x_positions: list[float] = []
    series_labels: list[str] = []
    batch_centers: list[tuple[float, str]] = []
    model_centers: list[tuple[float, str]] = []
    seen_labels: set[str] = set()

    for model in model_order:
        model_start = x_cursor
        for batch in batch_order:
            batch_start = x_cursor
            for series in series_order:
                subset = frame[
                    (frame["model"] == model)
                    & (frame["batch"] == batch)
                    & (frame["series"] == series)
                ]
                if subset.empty:
                    continue
                bottom = 0.0
                for index, stack in enumerate(stack_order):
                    row = subset[subset["stack"] == stack]
                    if row.empty:
                        continue
                    value = float(row["value"].sum())
                    stack_label = str(stack)
                    label = stack_label if stack_label not in seen_labels else None
                    seen_labels.add(stack_label)
                    ax.bar(
                        x_cursor,
                        value,
                        bottom=bottom,
                        width=0.72,
                        label=label,
                        color=STACK_COLORS.get(str(stack), f"C{index}"),
                        edgecolor="black",
                        linewidth=0.8,
                    )
                    bottom += value
                x_positions.append(x_cursor)
                series_labels.append(str(series))
                x_cursor += 1.0
            if x_cursor > batch_start:
                batch_centers.append(((batch_start + x_cursor - 1.0) / 2, str(batch)))
                x_cursor += 0.35
        if x_cursor > model_start:
            model_centers.append(((model_start + x_cursor - 1.35) / 2, str(model)))
            x_cursor += 0.55

    ax.set_xticks(x_positions)
    ax.set_xticklabels(series_labels, rotation=90)
    for center, label in batch_centers:
        ax.text(
            center,
            -0.26,
            label,
            ha="center",
            va="top",
            transform=ax.get_xaxis_transform(),
        )
    for center, label in model_centers:
        ax.text(
            center,
            -0.46,
            label,
            ha="center",
            va="top",
            transform=ax.get_xaxis_transform(),
        )

    ax.set_ylabel("Normalized Latency")
    apply_paper_axes(ax)
    style_legend(ax, ncol=len(stack_order))
    fig.subplots_adjust(bottom=0.42, top=0.76)
    return fig
