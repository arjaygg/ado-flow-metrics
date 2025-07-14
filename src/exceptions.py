"""Custom exception hierarchy for ADO Flow Hive."""


class ADOFlowException(Exception):
    """Base exception class for ADO Flow Hive."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__


class ConfigurationError(ADOFlowException):
    """Raised when there are configuration-related errors."""
    pass


class AuthenticationError(ADOFlowException):
    """Raised when authentication to Azure DevOps fails."""
    pass


class AuthorizationError(ADOFlowException):
    """Raised when user lacks permissions for requested operation."""
    pass


class NetworkError(ADOFlowException):
    """Raised when network-related errors occur."""
    pass


class APIError(ADOFlowException):
    """Raised when Azure DevOps API returns errors."""
    
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class DataValidationError(ADOFlowException):
    """Raised when data validation fails."""
    pass


class WorkItemError(ADOFlowException):
    """Raised when work item operations fail."""
    pass


class DatabaseError(ADOFlowException):
    """Raised when database operations fail."""
    pass


class MetricsCalculationError(ADOFlowException):
    """Raised when metrics calculation fails."""
    pass


class ExportError(ADOFlowException):
    """Raised when data export operations fail."""
    pass