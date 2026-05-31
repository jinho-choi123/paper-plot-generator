from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from paper_plot.config import PlotConfig


NUMERIC_COLUMNS = {
    "grouped_bar": ("value",),
    "stacked_bar": ("value",),
    "line_series": ("x", "y"),
}


class DataError(ValueError):
    """Raised when CSV data cannot be normalized for plotting."""


def load_plot_data(config: PlotConfig) -> pd.DataFrame:
    try:
        source = pd.read_csv(config.data_path)
    except FileNotFoundError as exc:
        raise DataError(f"CSV file not found: {config.data_path}") from exc

    rename_map: dict[str, str] = {}
    for internal_name, external_name in config.columns.items():
        if external_name not in source.columns:
            raise DataError(
                "CSV column not found for mapping "
                f"data.columns.{internal_name}: {external_name}"
            )
        rename_map[external_name] = internal_name

    frame = source.rename(columns=rename_map)
    selected_columns = list(config.columns.keys())
    frame = frame[selected_columns].copy()

    for column in NUMERIC_COLUMNS[config.plot_type]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            raise DataError(f"Column {column} must be numeric")

    return frame


def ordered_unique(
    values: Iterable[Any], explicit_order: Iterable[Any] | None = None
) -> list[Any]:
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)

    if explicit_order is None:
        return seen

    ordered = [value for value in explicit_order if value in seen]
    ordered.extend(value for value in seen if value not in ordered)
    return ordered
