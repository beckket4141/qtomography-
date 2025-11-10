"""GUI configuration value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "SpectralConfig",
    "DataConfig",
    "ExecuteConfig",
    "ConfigConfig",
    "WindowConfig",
    "GUIConfig",
]


@dataclass(frozen=True)
class SpectralConfig:
    """Spectral decomposition panel configuration."""

    folder_path: str = ""
    output_dir: str = ""
    dimension_hint: str = "自动推断"
    theory_mode: str = "4D_custom"
    figure_format: str = "png"
    save_plots: bool = True
    save_reports: bool = True
    save_json: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.dimension_hint not in {"自动推断", "4", "16"}:
            raise ValueError(f"Invalid dimension_hint: {self.dimension_hint}")
        if self.theory_mode not in {"4D_custom", "16D_custom", "custom"}:
            raise ValueError(f"Invalid theory_mode: {self.theory_mode}")
        if self.figure_format not in {"png", "pdf", "svg"}:
            raise ValueError(f"Invalid figure_format: {self.figure_format}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpectralConfig:
        """Create from dictionary."""
        return cls(
            folder_path=str(data.get("folder_path", "")),
            output_dir=str(data.get("output_dir", "")),
            dimension_hint=str(data.get("dimension_hint", "自动推断")),
            theory_mode=str(data.get("theory_mode", "4D_custom")),
            figure_format=str(data.get("figure_format", "png")),
            save_plots=bool(data.get("save_plots", True)),
            save_reports=bool(data.get("save_reports", True)),
            save_json=bool(data.get("save_json", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "folder_path": self.folder_path,
            "output_dir": self.output_dir,
            "dimension_hint": self.dimension_hint,
            "theory_mode": self.theory_mode,
            "figure_format": self.figure_format,
            "save_plots": self.save_plots,
            "save_reports": self.save_reports,
            "save_json": self.save_json,
        }

    def with_updates(self, **kwargs) -> SpectralConfig:
        """Create updated copy."""
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


@dataclass(frozen=True)
class DataConfig:
    """Data panel configuration."""

    last_file: str = ""
    selection_mode: str = "all"
    column_from: int = 1
    column_to: int = 1

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.last_file and not Path(self.last_file).exists():
            # Don't raise error, just warn - file might have been moved
            pass
        if self.selection_mode not in {"all", "range"}:
            raise ValueError(f"Invalid selection_mode: {self.selection_mode}")
        if self.column_from < 1 or self.column_to < 1:
            raise ValueError("column_from/column_to must be >= 1")
        if self.column_to < self.column_from:
            raise ValueError("column_to must be >= column_from")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DataConfig:
        """Create from dictionary."""
        return cls(
            last_file=str(data.get("last_file", "")),
            selection_mode=str(data.get("selection_mode", "all")),
            column_from=int(data.get("column_from", 1) or 1),
            column_to=int(data.get("column_to", 1) or 1),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "last_file": self.last_file,
            "selection_mode": self.selection_mode,
            "column_from": self.column_from,
            "column_to": self.column_to,
        }

    def with_updates(self, **kwargs) -> DataConfig:
        """Create updated copy."""
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


@dataclass(frozen=True)
class ExecuteConfig:
    """Execute panel configuration."""

    output_dir: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecuteConfig:
        """Create from dictionary."""
        return cls(output_dir=str(data.get("output_dir", "")))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"output_dir": self.output_dir}

    def with_updates(self, **kwargs) -> ExecuteConfig:
        """Create updated copy."""
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


@dataclass(frozen=True)
class ConfigConfig:
    """Configuration panel (algorithm parameters) configuration."""

    # Method checkboxes
    linear_enabled: bool = True
    wls_enabled: bool = True
    rhor_enabled: bool = False

    # Measurement design
    design: str = "mub"  # "mub", "sic", "nopovm"

    # Dimension
    auto_dimension: bool = True
    dimension: int = 4  # Only used when auto_dimension=False

    # Sheet (optional)
    sheet: str = ""

    # Regularization
    linear_regularization: Optional[float] = None
    wls_regularization: Optional[float] = None

    # Advanced parameters
    wls_max_iterations: int = 2000
    tolerance: float = 1e-9

    # Options
    cache_projectors: bool = True
    analyze_bell: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.design not in {"mub", "sic", "nopovm"}:
            raise ValueError(f"Invalid design: {self.design}")
        if self.dimension < 2 or self.dimension > 128:
            raise ValueError(f"Invalid dimension: {self.dimension}")
        if self.wls_max_iterations < 100 or self.wls_max_iterations > 10000:
            raise ValueError(f"Invalid wls_max_iterations: {self.wls_max_iterations}")
        if self.tolerance < 1e-12 or self.tolerance > 1e-3:
            raise ValueError(f"Invalid tolerance: {self.tolerance}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConfigConfig:
        """Create from dictionary."""
        linear_reg = data.get("linear_regularization")
        wls_reg = data.get("wls_regularization")
        return cls(
            linear_enabled=bool(data.get("linear_enabled", True)),
            wls_enabled=bool(data.get("wls_enabled", True)),
            rhor_enabled=bool(data.get("rhor_enabled", False)),
            design=str(data.get("design", "mub")),
            auto_dimension=bool(data.get("auto_dimension", True)),
            dimension=int(data.get("dimension", 4)),
            sheet=str(data.get("sheet", "")),
            linear_regularization=float(linear_reg) if linear_reg is not None else None,
            wls_regularization=float(wls_reg) if wls_reg is not None else None,
            wls_max_iterations=int(data.get("wls_max_iterations", 2000)),
            tolerance=float(data.get("tolerance", 1e-9)),
            cache_projectors=bool(data.get("cache_projectors", True)),
            analyze_bell=bool(data.get("analyze_bell", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "linear_enabled": self.linear_enabled,
            "wls_enabled": self.wls_enabled,
            "rhor_enabled": self.rhor_enabled,
            "design": self.design,
            "auto_dimension": self.auto_dimension,
            "dimension": self.dimension,
            "sheet": self.sheet,
            "linear_regularization": self.linear_regularization,
            "wls_regularization": self.wls_regularization,
            "wls_max_iterations": self.wls_max_iterations,
            "tolerance": self.tolerance,
            "cache_projectors": self.cache_projectors,
            "analyze_bell": self.analyze_bell,
        }

    def with_updates(self, **kwargs) -> ConfigConfig:
        """Create updated copy."""
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


@dataclass(frozen=True)
class WindowConfig:
    """Window geometry and state configuration."""

    geometry: str = ""
    state: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WindowConfig:
        """Create from dictionary."""
        return cls(
            geometry=str(data.get("geometry", "")),
            state=str(data.get("state", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "geometry": self.geometry,
            "state": self.state,
        }

    def with_updates(self, **kwargs) -> WindowConfig:
        """Create updated copy."""
        data = self.to_dict()
        data.update(kwargs)
        return self.from_dict(data)


@dataclass(frozen=True)
class GUIConfig:
    """Complete GUI configuration value object."""

    spectral: SpectralConfig = field(default_factory=SpectralConfig)
    data: DataConfig = field(default_factory=DataConfig)
    execute: ExecuteConfig = field(default_factory=ExecuteConfig)
    config: ConfigConfig = field(default_factory=ConfigConfig)
    window: WindowConfig = field(default_factory=WindowConfig)

    def __post_init__(self) -> None:
        """Validate configuration."""
        # All validation is done in sub-configs
        pass

    @classmethod
    def create_default(cls) -> GUIConfig:
        """Create default configuration."""
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GUIConfig:
        """Create from dictionary."""
        return cls(
            spectral=SpectralConfig.from_dict(data.get("spectral", {})),
            data=DataConfig.from_dict(data.get("data", {})),
            execute=ExecuteConfig.from_dict(data.get("execute", {})),
            config=ConfigConfig.from_dict(data.get("config", {})),
            window=WindowConfig.from_dict(data.get("window", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "spectral": self.spectral.to_dict(),
            "data": self.data.to_dict(),
            "execute": self.execute.to_dict(),
            "config": self.config.to_dict(),
            "window": self.window.to_dict(),
        }

    def with_updates(self, **kwargs) -> GUIConfig:
        """Create updated copy."""
        data = self.to_dict()

        # Handle nested updates
        for key, value in kwargs.items():
            if key in {"spectral", "data", "execute", "config", "window"}:
                if isinstance(value, dict):
                    # Merge nested dict
                    if key in data:
                        data[key].update(value)
                    else:
                        data[key] = value
                else:
                    data[key] = value
            else:
                data[key] = value

        return self.from_dict(data)

