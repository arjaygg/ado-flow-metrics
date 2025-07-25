"""Error handler mixin for consistent error handling across components."""

import logging
import sys
from functools import wraps
from typing import Any, Dict, Optional, Type

from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    WIQLError,
    WIQLValidationError,
)

logger = logging.getLogger(__name__)


class ErrorHandlerMixin:
    """Mixin class providing consistent error handling across components."""

    def handle_api_error(self, error: Exception, context: str = "API") -> None:
        """Handle API-related errors with appropriate logging and user messages."""
        error_msg = str(error)

        if isinstance(error, AuthenticationError):
            logger.error(f"{context} authentication failed: {error_msg}")
            self._print_error_if_available(
                "Authentication failed - check your PAT token"
            )
            self._suggest_mock_data()

        elif isinstance(error, AuthorizationError):
            logger.error(f"{context} authorization failed: {error_msg}")
            self._print_error_if_available(
                "Access forbidden - check project permissions or conditional access policies"
            )
            self._suggest_mock_data()

        elif isinstance(error, APIError):
            logger.error(f"{context} API error: {error_msg}")
            self._print_error_if_available(f"API Error: {error_msg}")
            if "405" in error_msg or "Method Not Allowed" in error_msg:
                self._print_warning_if_available(
                    "This usually indicates an API endpoint issue or authentication problem"
                )
            self._suggest_mock_data()

        elif isinstance(error, ConfigurationError):
            logger.error(f"Configuration error: {error_msg}")
            self._print_error_if_available(f"Configuration Error: {error_msg}")

        elif isinstance(error, (WIQLError, WIQLValidationError)):
            logger.error(f"WIQL error: {error_msg}")
            self._print_error_if_available(f"WIQL Error: {error_msg}")

        else:
            # Generic error handling
            logger.error(f"{context} error: {error_msg}")
            self._print_error_if_available(f"Unexpected error: {error_msg}")

    def handle_validation_error(
        self, error: Exception, context: str = "Validation"
    ) -> None:
        """Handle validation errors."""
        error_msg = str(error)
        logger.error(f"{context} validation failed: {error_msg}")
        self._print_error_if_available(f"Validation Error: {error_msg}")

    def handle_file_error(
        self, error: Exception, file_path: str, operation: str = "file operation"
    ) -> None:
        """Handle file-related errors."""
        error_msg = str(error)
        logger.error(f"File {operation} failed for {file_path}: {error_msg}")

        if "Permission denied" in error_msg:
            self._print_error_if_available(f"Permission denied accessing {file_path}")
            self._print_info_if_available(
                "Check file permissions and try running as administrator if needed"
            )
        elif "No such file or directory" in error_msg:
            self._print_error_if_available(f"File not found: {file_path}")
        elif "Is a directory" in error_msg:
            self._print_error_if_available(
                f"Expected file but found directory: {file_path}"
            )
        else:
            self._print_error_if_available(f"File {operation} failed: {error_msg}")

    def handle_network_error(self, error: Exception, context: str = "Network") -> None:
        """Handle network-related errors."""
        error_msg = str(error)
        logger.error(f"{context} error: {error_msg}")

        if "timeout" in error_msg.lower():
            self._print_error_if_available(
                "Network timeout - check your internet connection"
            )
            self._print_info_if_available(
                "Try increasing timeout or checking network connectivity"
            )
        elif "connection" in error_msg.lower():
            self._print_error_if_available(
                "Connection error - unable to reach Azure DevOps"
            )
            self._print_info_if_available(
                "Check your network connection and firewall settings"
            )
        else:
            self._print_error_if_available(f"Network error: {error_msg}")

        self._suggest_mock_data()

    def safe_execute(self, func, *args, error_context: str = "Operation", **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except (AuthenticationError, AuthorizationError, APIError) as e:
            self.handle_api_error(e, error_context)
            return None
        except ConfigurationError as e:
            self.handle_validation_error(e, error_context)
            return None
        except Exception as e:
            logger.error(f"{error_context} failed with unexpected error: {e}")
            self._print_error_if_available(
                f"Unexpected error during {error_context.lower()}: {e}"
            )
            return None

    def with_error_handling(self, error_context: str = "Operation"):
        """Decorator for automatic error handling."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.safe_execute(
                    func, *args, error_context=error_context, **kwargs
                )

            return wrapper

        return decorator

    def log_and_exit(self, message: str, exit_code: int = 1) -> None:
        """Log an error message and exit the application."""
        logger.error(message)
        self._print_error_if_available(message)
        sys.exit(exit_code)

    def _print_error_if_available(self, message: str) -> None:
        """Print error message if formatter is available."""
        if hasattr(self, "formatter") and self.formatter:
            self.formatter.print_error(message)
        else:
            print(f"ERROR: {message}")

    def _print_warning_if_available(self, message: str) -> None:
        """Print warning message if formatter is available."""
        if hasattr(self, "formatter") and self.formatter:
            self.formatter.print_warning(message)
        else:
            print(f"WARNING: {message}")

    def _print_info_if_available(self, message: str) -> None:
        """Print info message if formatter is available."""
        if hasattr(self, "formatter") and self.formatter:
            self.formatter.print_info(message)
        else:
            print(f"INFO: {message}")

    def _suggest_mock_data(self) -> None:
        """Suggest using mock data as fallback."""
        self._print_info_if_available(
            "For immediate testing, use mock data: python -m src.cli data fresh --use-mock"
        )

    def create_error_context(self, **context_data) -> Dict[str, Any]:
        """Create error context for better debugging."""
        return {
            "timestamp": self._get_current_timestamp(),
            "component": self.__class__.__name__,
            **context_data,
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for error context."""
        from datetime import datetime

        return datetime.now().isoformat()


def handle_exceptions(*exception_types: Type[Exception], context: str = "Operation"):
    """Decorator for handling specific exception types."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not isinstance(self, ErrorHandlerMixin):
                # If not using the mixin, just execute normally
                return func(self, *args, **kwargs)

            try:
                return func(self, *args, **kwargs)
            except exception_types as e:
                self.handle_api_error(e, context)
                return None
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                self._print_error_if_available(f"Unexpected error: {e}")
                return None

        return wrapper

    return decorator


def safe_operation(context: str = "Operation"):
    """Decorator for safe operation execution with generic error handling."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if isinstance(self, ErrorHandlerMixin):
                return self.safe_execute(func, *args, error_context=context, **kwargs)
            else:
                # Fallback for classes not using the mixin
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"{context} failed: {e}")
                    return None

        return wrapper

    return decorator
