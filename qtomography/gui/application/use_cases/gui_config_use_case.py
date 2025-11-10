"""GUI configuration management use case."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from qtomography.gui.domain.gui_config import GUIConfig
from qtomography.gui.infrastructure.repositories import GUIConfigRepository

__all__ = ["GUIConfigUseCase"]


class GUIConfigUseCase:
    """Use case for GUI configuration management."""

    def __init__(self, repository: Optional[GUIConfigRepository] = None) -> None:
        """Initialize use case.

        Args:
            repository: Configuration repository. If None, creates default repository.
        """
        self.repository = repository or GUIConfigRepository()

    def get_current_config(self) -> GUIConfig:
        """Get current configuration.

        Returns:
            Current GUIConfig value object.
        """
        return self.repository.get_current_config()

    def update_config(
        self,
        config_updates: Union[Mapping[str, Any], GUIConfig],
        validate: bool = True,
    ) -> bool:
        """Update configuration with partial or full updates.

        Args:
            config_updates: Dictionary of updates (supports nested keys like "spectral.dimension_hint")
                          or a complete GUIConfig object.
            validate: Whether to validate the updated configuration.

        Returns:
            True if successful, False otherwise.
        """
        # Get current config
        current_config = self.repository.get_current_config()

        # Handle full config object
        if isinstance(config_updates, GUIConfig):
            updated_config = config_updates
        else:
            # Handle partial updates (flatten nested keys)
            updates_dict: Dict[str, Any] = {}
            nested_updates: Dict[str, Dict[str, Any]] = {}

            for key, value in dict(config_updates).items():
                if "." in key:
                    # Handle nested keys like "spectral.dimension_hint"
                    parts = key.split(".", 1)
                    section = parts[0]
                    field = parts[1]
                    if section not in nested_updates:
                        nested_updates[section] = {}
                    nested_updates[section][field] = value
                else:
                    updates_dict[key] = value

            # Merge nested updates
            for section, fields in nested_updates.items():
                if section not in updates_dict:
                    updates_dict[section] = {}
                if isinstance(updates_dict[section], dict):
                    updates_dict[section].update(fields)
                else:
                    updates_dict[section] = fields

            # Create updated config
            updated_config = current_config.with_updates(**updates_dict)

        # Validate if requested
        if validate:
            try:
                # Validation happens in __post_init__ of value objects
                _ = updated_config.to_dict()
            except ValueError as exc:
                import logging

                logger = logging.getLogger(__name__)
                logger.error("Configuration validation failed: %s", exc)
                return False

        # Save to repository
        return self.repository.save_config(updated_config)

    def save_config_to_file(self, filepath: Path) -> bool:
        """Save current configuration to a specific file.

        Args:
            filepath: Target file path.

        Returns:
            True if successful, False otherwise.
        """
        return self.repository.save_config_to_file(filepath)

    def load_config_from_file(self, filepath: Path) -> bool:
        """Load configuration from a specific file and save as default.

        Args:
            filepath: Source file path.

        Returns:
            True if successful, False otherwise.
        """
        return self.repository.load_config_from_file(filepath)

    def reset_to_default(self) -> bool:
        """Reset configuration to default values.

        Returns:
            True if successful, False otherwise.
        """
        default_config = GUIConfig.create_default()
        return self.repository.save_config(default_config)

