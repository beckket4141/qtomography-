"""GUI configuration repository for persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from qtomography.gui.domain.gui_config import GUIConfig

__all__ = ["GUIConfigRepository"]


class GUIConfigRepository:
    """Repository for GUI configuration persistence."""

    def __init__(self, config_file_path: Optional[Path] = None) -> None:
        """Initialize repository.

        Args:
            config_file_path: Path to configuration file. If None, uses default location.
        """
        if config_file_path is None:
            # Default: user's home directory / .qtomography / gui_config.json
            import os

            config_dir = Path.home() / ".qtomography"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file_path = config_dir / "gui_config.json"

        self.config_file_path = Path(config_file_path)

    def save_config(self, config: GUIConfig) -> bool:
        """Save configuration to file.

        Args:
            config: GUIConfig value object to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Ensure directory exists
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and save
            config_data = config.to_dict()
            with self.config_file_path.open("w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            return True
        except (IOError, OSError, json.JSONEncodeError) as exc:
            # Log error but don't raise (silent failure for config save)
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Failed to save GUI config: %s", exc)
            return False

    def load_config(self) -> GUIConfig:
        """Load configuration from file.

        Returns:
            GUIConfig value object. Returns default config if file doesn't exist or is invalid.
        """
        if not self.config_file_path.exists():
            return GUIConfig.create_default()

        try:
            with self.config_file_path.open("r", encoding="utf-8") as f:
                config_data = json.load(f)

            return GUIConfig.from_dict(config_data)
        except (IOError, OSError, json.JSONDecodeError, ValueError) as exc:
            # If file is corrupted or invalid, return default
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("Failed to load GUI config, using default: %s", exc)
            return GUIConfig.create_default()

    def get_current_config(self) -> GUIConfig:
        """Get current configuration (loads from file or returns default).

        Returns:
            Current GUIConfig value object.
        """
        return self.load_config()

    def save_config_to_file(self, filepath: Path) -> bool:
        """Save current configuration to a specific file.

        Args:
            filepath: Target file path.

        Returns:
            True if successful, False otherwise.
        """
        config = self.get_current_config()
        temp_repo = GUIConfigRepository(filepath)
        return temp_repo.save_config(config)

    def load_config_from_file(self, filepath: Path) -> bool:
        """Load configuration from a specific file and save as default.

        Args:
            filepath: Source file path.

        Returns:
            True if successful, False otherwise.
        """
        if not filepath.exists():
            return False

        try:
            temp_repo = GUIConfigRepository(filepath)
            config = temp_repo.load_config()
            return self.save_config(config)
        except Exception:
            return False

