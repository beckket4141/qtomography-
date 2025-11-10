"""Domain ports for persistence.

This module defines abstract, technology-agnostic interfaces (ports) that the
domain and application layers can depend on. Concrete implementations live in
the infrastructure layer and must implement these protocols.

Notes
- Keep this file free of infrastructure dependencies (e.g., pandas, file I/O).
- Use minimal typing contracts to enable testing and easy swapping of adapters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import numpy as np

__all__ = ["SupportsRecord", "IResultRepository"]


@runtime_checkable
class SupportsRecord(Protocol):
    """A serializable reconstruction record contract.

    Concrete implementations (e.g., dataclasses) should provide at least these
    attributes and a ``to_serializable`` method returning a JSON-friendly dict.
    This avoids the domain depending on any specific implementation details.
    """

    method: str
    dimension: int
    probabilities: np.ndarray
    density_matrix: np.ndarray
    metrics: Dict[str, float]
    metadata: Optional[Dict[str, str]]
    timestamp: Optional[str]

    def to_serializable(self) -> Dict[str, Any]:
        ...


@runtime_checkable
class IResultRepository(Protocol):
    """Persistence port for reconstruction records.

    Infrastructure adapters (JSON/CSV/DB) implement this protocol.
    """

    def save(self, record: SupportsRecord) -> Path:
        """Persist a single record and return the output path."""
        ...

    def load_all(self) -> List[SupportsRecord]:
        """Load all records from the repository's storage root."""
        ...

    # Optional helper; return type left open intentionally to avoid pandas
    # dependency in the domain layer. Implementations may return a DataFrame.
    def to_dataframe(self) -> Any:  # pragma: no cover - adapter-specific
        ...

