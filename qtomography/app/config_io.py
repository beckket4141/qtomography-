
"""
Configuration persistence helpers for :class:`ReconstructionConfig`.

The helpers keep JSON as the on-disk representation to avoid bringing in
additional dependencies. Relative paths inside the JSON file are resolved
against the configuration file location so that configs remain portable.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .controller import ReconstructionConfig

__all__ = [
    "CONFIG_FILE_VERSION",
    "load_config_file",
    "dump_config_file",
    "config_to_payload",
]

# Bump when the schema changes in a backwards-incompatible way.
CONFIG_FILE_VERSION = "1.0"


def config_to_payload(config: ReconstructionConfig) -> Dict[str, Any]:
    """
    Serialise a :class:`ReconstructionConfig` into a JSON-friendly dict.

    Paths are converted to strings. Sequence fields remain JSON arrays and
    Optional values are omitted when ``None`` to keep the file concise.
    """

    data = asdict(config)
    payload: Dict[str, Any] = {
        "version": CONFIG_FILE_VERSION,
        "input_path": str(config.input_path),
        "output_dir": str(config.output_dir),
    }

    def _store(name: str, value: Any) -> None:
        if value is None:
            return
        payload[name] = value

    _store("methods", list(config.methods))
    _store("design", data.get("design"))
    _store("dimension", data.get("dimension"))
    _store("sheet", data.get("sheet"))
    column_range = data.get("column_range")
    if column_range is not None:
        _store("column_range", list(column_range))
    _store("linear_regularization", data.get("linear_regularization"))
    _store("wls_regularization", data.get("wls_regularization"))
    _store("wls_max_iterations", data.get("wls_max_iterations"))
    _store("wls_min_expected_clip", data.get("wls_min_expected_clip"))
    _store("wls_optimizer_ftol", data.get("wls_optimizer_ftol"))
    _store("tolerance", data.get("tolerance"))
    _store("cache_projectors", data.get("cache_projectors"))
    _store("analyze_bell", data.get("analyze_bell"))

    return payload


def dump_config_file(config: ReconstructionConfig, path: Path) -> None:
    """
    Write *config* to *path* as JSON.

    The parent directory is created automatically if necessary.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = config_to_payload(config)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _normalise_methods(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ("linear", "mle")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        raise ValueError("methods must be a string or list of strings")
    methods = []
    for item in raw:
        if not isinstance(item, str):
            raise ValueError("methods items must be strings")
        item_lower = item.lower()
        if item_lower == "both":
            methods.extend(["linear", "mle"])
        else:
            methods.append(item_lower)
    return tuple(methods)


def load_config_file(path: Path) -> ReconstructionConfig:
    """
    Load a JSON configuration file and return a :class:`ReconstructionConfig`.

    Paths inside the JSON are resolved relative to the file's directory when
    they are provided as relative strings.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("configuration file must contain a JSON object")

    version = payload.get("version")
    if version not in (None, CONFIG_FILE_VERSION):
        raise ValueError(
            f"Unsupported configuration version '{version}'. Expected {CONFIG_FILE_VERSION}."
        )

    base_dir = path.parent

    def _resolve_path(value: Any, *, required: bool, field: str) -> Path:
        if value is None:
            if required:
                raise ValueError(f"Missing required field '{field}' in configuration file.")
            raise ValueError(f"Field '{field}' cannot be null.")
        if not isinstance(value, str):
            raise ValueError(f"Field '{field}' must be a string path.")
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        return candidate.resolve()

    input_path = _resolve_path(payload.get("input_path"), required=True, field="input_path")
    output_dir = _resolve_path(payload.get("output_dir"), required=True, field="output_dir")

    dimension = payload.get("dimension")
    if dimension is not None and not isinstance(dimension, int):
        raise ValueError("dimension must be an integer")

    sheet = payload.get("sheet")
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    elif sheet is not None and not isinstance(sheet, (str, int)):
        raise ValueError("sheet must be a string or integer")

    column_range = payload.get("column_range")
    if column_range is not None:
        if isinstance(column_range, dict):
            # Accept {"start": x, "end": y} style for forward compatibility
            column_range = [column_range.get("start"), column_range.get("end")]
        if not isinstance(column_range, (list, tuple)):
            raise ValueError("column_range must be a list/tuple of two integers")
        if len(column_range) != 2:
            raise ValueError("column_range must contain exactly two integers")
        start, end = column_range
        try:
            start_int = int(start)
            end_int = int(end)
        except (TypeError, ValueError) as exc:
            raise ValueError("column_range values must be integers") from exc
        if start_int < 1 or end_int < 1:
            raise ValueError("column_range values must be >= 1")
        if end_int < start_int:
            raise ValueError("column_range end must be >= start")
        column_range = (start_int, end_int)

    linear_regularization = payload.get("linear_regularization")
    if linear_regularization is not None and not isinstance(linear_regularization, (int, float)):
        raise ValueError("linear_regularization must be numeric")

    wls_regularization = payload.get("wls_regularization")
    if wls_regularization is not None and not isinstance(wls_regularization, (int, float)):
        raise ValueError("wls_regularization must be numeric")

    wls_max_iterations = payload.get("wls_max_iterations")
    if wls_max_iterations is None:
        wls_max_iterations = 2000
    elif not isinstance(wls_max_iterations, int) or wls_max_iterations <= 0:
        raise ValueError("wls_max_iterations must be a positive integer")

    wls_min_expected_clip = payload.get("wls_min_expected_clip")
    if wls_min_expected_clip is None:
        wls_min_expected_clip = 1e-12
    elif not isinstance(wls_min_expected_clip, (int, float)):
        raise ValueError("wls_min_expected_clip must be numeric")
    elif wls_min_expected_clip <= 0:
        raise ValueError("wls_min_expected_clip must be positive")

    wls_optimizer_ftol = payload.get("wls_optimizer_ftol")
    if wls_optimizer_ftol is None:
        wls_optimizer_ftol = 1e-9
    elif not isinstance(wls_optimizer_ftol, (int, float)):
        raise ValueError("wls_optimizer_ftol must be numeric")
    elif wls_optimizer_ftol <= 0:
        raise ValueError("wls_optimizer_ftol must be positive")

    tolerance = payload.get("tolerance")
    if tolerance is None:
        tolerance = 1e-9
    elif not isinstance(tolerance, (int, float)):
        raise ValueError("tolerance must be numeric")
    elif tolerance <= 0:
        raise ValueError("tolerance must be positive")

    cache_projectors = payload.get("cache_projectors")
    if cache_projectors is None:
        cache_projectors = True
    elif not isinstance(cache_projectors, bool):
        raise ValueError("cache_projectors must be a boolean")

    analyze_bell = payload.get("analyze_bell")
    if analyze_bell is None:
        analyze_bell = False
    elif not isinstance(analyze_bell, bool):
        raise ValueError("analyze_bell must be a boolean")

    design = payload.get("design")
    if design is None:
        design = "mub"
    elif not isinstance(design, str) or design.lower() not in ("mub", "sic", "nopovm"):
        raise ValueError("design must be one of: 'mub', 'sic', 'nopovm'")
    design = design.lower()

    return ReconstructionConfig(
        input_path=input_path,
        output_dir=output_dir,
        methods=_normalise_methods(payload.get("methods")),
        design=design,
        dimension=dimension,
        sheet=sheet,
        column_range=column_range,
        linear_regularization=linear_regularization,
        wls_regularization=wls_regularization,
        wls_max_iterations=wls_max_iterations,
        wls_min_expected_clip=wls_min_expected_clip,
        wls_optimizer_ftol=wls_optimizer_ftol,
        tolerance=tolerance,
        cache_projectors=cache_projectors,
        analyze_bell=analyze_bell,
    )
