import logging
import logging.config
from pathlib import Path

from config_manager import get_settings


def setup_logging():
    """
    Configures the application's logging based on settings from the config file.
    """
    try:
        settings = get_settings()
        log_config = settings.logging

        if not log_config or not log_config.file:
            print("Warning: Logging to file is not configured.")
            return

        log_file_path = Path(log_config.file)
        # Ensure the parent directory exists
        log_file_path.parent.mkdir(exist_ok=True, parents=True)

        # Base configuration
        config_dict = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": log_config.format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": log_config.level.upper(),
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": log_file_path,
                    "maxBytes": log_config.max_size_mb * 1024 * 1024,
                    "backupCount": log_config.backup_count,
                    "level": log_config.level.upper(),
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": log_config.level.upper(),
            },
        }

        logging.config.dictConfig(config_dict)
        logging.info("Logging configured successfully.")

    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(level=logging.INFO)
        logging.exception(f"Error configuring logging from settings: {e}")
