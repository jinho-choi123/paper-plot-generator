from __future__ import annotations

from matplotlib.axes import Axes


SERIES_COLORS = {
    "GPU": "#5AA89D",
    "GPU+Q": "#F6E8A6",
    "GPU+PIM": "#E3C960",
    "Pimba": "#D46F4D",
}

LINE_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
LINE_MARKERS = ["o", "s", "v", "^", "D"]

STACK_COLORS = {
    "State Update": "#2F5D57",
    "Attention": "#5AA89D",
    "Discretization": "#7FA37B",
    "Causal Conv": "#A8B878",
    "GEMM": "#E3C960",
    "Communication": "#D46F4D",
    "Others": "#984A45",
}


def apply_paper_axes(ax: Axes) -> None:
    for spine in ax.spines.values():
        spine.set_color("black")
        spine.set_linewidth(1.3)
    ax.grid(axis="y", linestyle="--", linewidth=0.8, color="#B7B7B7", alpha=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", width=1.2, labelsize=10)


def style_legend(
    ax: Axes,
    *,
    ncol: int | None = None,
    bbox_to_anchor: tuple[float, float] = (0.5, 1.18),
) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=bbox_to_anchor,
        ncol=ncol or len(handles),
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="black",
    )
    legend.get_frame().set_linewidth(1.2)
