from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

import matplotlib.pyplot as plt

from paper_plot.config import ConfigError, load_config
from paper_plot.data import DataError, load_plot_data
from paper_plot.export import export_figure
from paper_plot.templates import render_plot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-plot",
        description="Generate paper-ready benchmark plots from CSV and YAML.",
    )
    parser.add_argument("config", help="Path to the YAML plot configuration")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        frame = load_plot_data(config)
        fig = render_plot(frame, config)
        written = export_figure(fig, config.output_path)
    except (ConfigError, DataError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        plt.close("all")

    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
