"""
Application configuration.

Provides centralized configuration management for the application.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    logs_dir: str = ".logs"
    enable_file_logging: bool = True
    enable_console_logging: bool = True
    log_level: str = "INFO"


@dataclass
class ExecutionConfig:
    """Configuration for execution."""
    default_timeout: int = 300  # 5 minutes
    max_execution_time: int = 3600  # 1 hour
    enable_parallel_execution: bool = False


@dataclass
class UIConfig:
    """Configuration for UI."""
    window_width: int = 1400
    window_height: int = 900
    theme: str = "dark"
    enable_minimap: bool = True


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    logging: LoggingConfig
    execution: ExecutionConfig
    ui: UIConfig
    debug_mode: bool = False

    @classmethod
    def default(cls) -> "ApplicationConfig":
        """
        Create default configuration.

        Returns:
            ApplicationConfig with default values
        """
        return cls(
            logging=LoggingConfig(),
            execution=ExecutionConfig(),
            ui=UIConfig(),
            debug_mode=False
        )

    @classmethod
    def headless(cls) -> "ApplicationConfig":
        """
        Create configuration for headless mode.

        Returns:
            ApplicationConfig optimized for headless execution
        """
        return cls(
            logging=LoggingConfig(
                enable_file_logging=True,
                enable_console_logging=False
            ),
            execution=ExecutionConfig(
                enable_parallel_execution=True
            ),
            ui=UIConfig(),  # UI config ignored in headless mode
            debug_mode=False
        )
