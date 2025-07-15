"""Centralized error handling utility for Flow Metrics application."""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from flask import jsonify

# Configure logging for error handling
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorType:
    """Standard error types for the application."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATA_SOURCE_ERROR = "DATA_SOURCE_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    FILE_IO_ERROR = "FILE_IO_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class FlowMetricsErrorHandler:
    """Centralized error handler for Flow Metrics application."""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
    
    def handle_error(
        self, 
        error: Exception, 
        error_type: str = ErrorType.INTERNAL_ERROR,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Centralized error handling method.
        
        Args:
            error: The exception that occurred
            error_type: Type of error from ErrorType class
            context: Additional context about the error
            user_message: Custom user-friendly message
            
        Returns:
            Tuple of (error_response_dict, http_status_code)
        """
        # Generate unique error ID
        error_id = self._generate_error_id()
        
        # Extract error details
        error_details = self._extract_error_details(error, error_type, context)
        
        # Log the error
        self._log_error(error_id, error_details, error)
        
        # Track error statistics
        self._track_error(error_type)
        
        # Generate user-friendly response
        response = self._generate_error_response(
            error_id, 
            error_type, 
            error_details,
            user_message
        )
        
        # Determine HTTP status code
        status_code = self._get_http_status_code(error_type, error)
        
        return response, status_code
    
    def handle_data_source_error(self, error: Exception, source: str) -> Tuple[Dict[str, Any], int]:
        """Handle data source specific errors."""
        context = {"data_source": source}
        user_message = f"Failed to load data from {source}. Please check the data source configuration."
        
        return self.handle_error(
            error, 
            ErrorType.DATA_SOURCE_ERROR, 
            context, 
            user_message
        )
    
    def handle_cache_error(self, error: Exception, operation: str) -> Tuple[Dict[str, Any], int]:
        """Handle cache operation errors."""
        context = {"cache_operation": operation}
        user_message = f"Cache {operation} operation failed. Data may not be persisted."
        
        return self.handle_error(
            error, 
            ErrorType.CACHE_ERROR, 
            context, 
            user_message
        )
    
    def handle_api_error(self, error: Exception, api_endpoint: str) -> Tuple[Dict[str, Any], int]:
        """Handle external API errors."""
        context = {"api_endpoint": api_endpoint}
        user_message = f"External API call to {api_endpoint} failed. Please try again later."
        
        return self.handle_error(
            error, 
            ErrorType.EXTERNAL_API_ERROR, 
            context, 
            user_message
        )
    
    def handle_file_io_error(self, error: Exception, file_path: str, operation: str) -> Tuple[Dict[str, Any], int]:
        """Handle file I/O errors."""
        context = {"file_path": file_path, "operation": operation}
        user_message = f"File {operation} operation failed for {file_path}."
        
        return self.handle_error(
            error, 
            ErrorType.FILE_IO_ERROR, 
            context, 
            user_message
        )
    
    def handle_validation_error(self, error: Exception, field: str = None) -> Tuple[Dict[str, Any], int]:
        """Handle validation errors."""
        context = {"field": field} if field else None
        user_message = f"Validation failed{f' for field: {field}' if field else ''}."
        
        return self.handle_error(
            error, 
            ErrorType.VALIDATION_ERROR, 
            context, 
            user_message
        )
    
    def handle_configuration_error(self, error: Exception, config_key: str = None) -> Tuple[Dict[str, Any], int]:
        """Handle configuration errors."""
        context = {"config_key": config_key} if config_key else None
        user_message = f"Configuration error{f' for {config_key}' if config_key else ''}. Please check your settings."
        
        return self.handle_error(
            error, 
            ErrorType.CONFIGURATION_ERROR, 
            context, 
            user_message
        )
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ERR_{timestamp}_{hash(datetime.now()) % 10000:04d}"
    
    def _extract_error_details(self, error: Exception, error_type: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Extract detailed error information."""
        return {
            "error_type": error_type,
            "exception_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
        }
    
    def _log_error(self, error_id: str, error_details: Dict[str, Any], error: Exception):
        """Log error with appropriate level."""
        error_type = error_details["error_type"]
        
        # Determine log level based on error type
        if error_type in [ErrorType.VALIDATION_ERROR, ErrorType.CONFIGURATION_ERROR]:
            log_level = logging.WARNING
        elif error_type in [ErrorType.CACHE_ERROR]:
            log_level = logging.INFO
        else:
            log_level = logging.ERROR
        
        logger.log(
            log_level,
            f"Error {error_id}: {error_type} - {error_details['exception_type']}: {error_details['error_message']}"
        )
        
        # Log context if available
        if error_details["context"]:
            logger.log(log_level, f"Error {error_id} context: {error_details['context']}")
        
        # Log traceback for debug level
        if logger.isEnabledFor(logging.DEBUG) and error_details["traceback"]:
            logger.debug(f"Error {error_id} traceback:\n{error_details['traceback']}")
    
    def _track_error(self, error_type: str):
        """Track error statistics."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = datetime.now().isoformat()
    
    def _generate_error_response(
        self, 
        error_id: str, 
        error_type: str, 
        error_details: Dict[str, Any],
        user_message: Optional[str]
    ) -> Dict[str, Any]:
        """Generate standardized error response."""
        response = {
            "error": True,
            "error_id": error_id,
            "error_type": error_type,
            "message": user_message or "An error occurred while processing your request.",
            "timestamp": error_details["timestamp"]
        }
        
        # Add technical details in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            response["debug"] = {
                "exception_type": error_details["exception_type"],
                "error_message": error_details["error_message"],
                "context": error_details["context"]
            }
        
        return response
    
    def _get_http_status_code(self, error_type: str, error: Exception) -> int:
        """Determine appropriate HTTP status code for error type."""
        status_code_map = {
            ErrorType.VALIDATION_ERROR: 400,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.CONFIGURATION_ERROR: 400,
            ErrorType.DATA_SOURCE_ERROR: 503,
            ErrorType.EXTERNAL_API_ERROR: 502,
            ErrorType.FILE_IO_ERROR: 500,
            ErrorType.CACHE_ERROR: 500,
            ErrorType.INTERNAL_ERROR: 500
        }
        
        # Check for specific exception types
        if isinstance(error, FileNotFoundError):
            return 404
        elif isinstance(error, PermissionError):
            return 403
        elif isinstance(error, ValueError):
            return 400
        
        return status_code_map.get(error_type, 500)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "error_counts": self.error_counts,
            "last_errors": self.last_errors,
            "total_errors": sum(self.error_counts.values())
        }
    
    def create_flask_response(self, error_response: Dict[str, Any], status_code: int):
        """Create Flask JSON response from error response."""
        return jsonify(error_response), status_code


# Global error handler instance
error_handler = FlowMetricsErrorHandler()


def handle_error_with_response(error: Exception, error_type: str = ErrorType.INTERNAL_ERROR, **kwargs):
    """
    Decorator and utility function for handling errors with automatic Flask response creation.
    
    Usage:
        response, status = handle_error_with_response(error, ErrorType.DATA_SOURCE_ERROR, context={"source": "api"})
        return response, status
    """
    error_response, status_code = error_handler.handle_error(error, error_type, **kwargs)
    return error_handler.create_flask_response(error_response, status_code)


def with_error_handling(error_type: str = ErrorType.INTERNAL_ERROR, **error_kwargs):
    """
    Decorator for automatic error handling in Flask routes.
    
    Usage:
        @with_error_handling(ErrorType.DATA_SOURCE_ERROR, context={"source": "api"})
        def my_route():
            # Route logic here
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handle_error_with_response(e, error_type, **error_kwargs)
        return wrapper
    return decorator