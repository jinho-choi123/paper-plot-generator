from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure


KNOWN_OUTPUT_SUFFIXES = {".pdf", ".png", ".svg"}


def output_stem(path: str | Path) -> Path:
    output_path = Path(path)
    if output_path.suffix.lower() in KNOWN_OUTPUT_SUFFIXES:
        return output_path.with_suffix("")
    return output_path


def export_figure(fig: Figure, path: str | Path) -> list[Path]:
    stem = output_stem(path)
    stem.parent.mkdir(parents=True, exist_ok=True)

    outputs = [stem.with_suffix(".pdf"), stem.with_suffix(".png")]
    fig.savefig(outputs[0], bbox_inches="tight")
    fig.savefig(outputs[1], bbox_inches="tight", dpi=300)
    return outputs
