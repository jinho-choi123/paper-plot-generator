from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_PLOT_TYPES = {"grouped_bar", "stacked_bar", "line_series"}

REQUIRED_COLUMNS = {
    "grouped_bar": ("group", "model", "batch", "series", "value"),
    "stacked_bar": ("model", "batch", "series", "stack", "value"),
    "line_series": ("series", "x", "y"),
}


class ConfigError(ValueError):
    """Raised when a plot YAML config is invalid."""


@dataclass(frozen=True)
class PlotConfig:
    plot_type: str
    data_path: Path
    columns: dict[str, str]
    output_path: Path
    order: dict[str, list[Any]]


def load_config(path: str | Path) -> PlotConfig:
    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Failed to parse YAML config: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping")

    plot_type = _required_string(raw, ("plot", "type"))
    if plot_type not in SUPPORTED_PLOT_TYPES:
        raise ConfigError(f"Unsupported plot type: {plot_type}")

    data_path = Path(_required_string(raw, ("data", "path")))
    output_path = Path(_required_string(raw, ("output", "path")))
    columns = _required_nested(raw, ("data", "columns"))
    if not isinstance(columns, dict):
        raise ConfigError("data.columns must be a mapping")

    normalized_columns = _normalize_columns(columns)
    _validate_required_columns(plot_type, normalized_columns)

    order = raw.get("order", {})
    if order is None:
        order = {}
    if not isinstance(order, dict):
        raise ConfigError("order must be a mapping")
    normalized_order = _normalize_order(order)

    return PlotConfig(
        plot_type=str(plot_type),
        data_path=data_path,
        columns=normalized_columns,
        output_path=output_path,
        order=normalized_order,
    )


def _required_nested(raw: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = raw
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            dotted = ".".join(keys)
            raise ConfigError(f"Missing required config field: {dotted}")
        current = current[key]
    return current


def _required_string(raw: dict[str, Any], keys: tuple[str, ...]) -> str:
    value = _required_nested(raw, keys)
    if not isinstance(value, str):
        dotted = ".".join(keys)
        raise ConfigError(f"{dotted} must be a string")
    return value


def _normalize_columns(columns: dict[Any, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in columns.items():
        if not isinstance(key, str):
            raise ConfigError("data.columns keys must be strings")
        if not isinstance(value, str):
            raise ConfigError(f"data.columns.{key} must be a string")
        normalized[key] = value
    return normalized


def _normalize_order(order: dict[Any, Any]) -> dict[str, list[Any]]:
    normalized: dict[str, list[Any]] = {}
    for key, value in order.items():
        order_key = str(key)
        if not isinstance(value, list):
            raise ConfigError(f"order.{order_key} must be a list")
        normalized[order_key] = value
    return normalized


def _validate_required_columns(plot_type: str, columns: dict[str, str]) -> None:
    missing = [name for name in REQUIRED_COLUMNS[plot_type] if name not in columns]
    if missing:
        raise ConfigError(
            f"Missing required column mapping for {plot_type}: {', '.join(missing)}"
        )
