"""Tests for custom exception hierarchy."""

import pytest

from src.exceptions import (
    ADOFlowException,
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    DataValidationError,
    ExportError,
    MetricsCalculationError,
    NetworkError,
    WorkItemError,
)


class TestADOFlowException:
    """Test base ADO Flow exception."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        error = ADOFlowException("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == "ADOFlowException"

    def test_base_exception_with_code(self):
        """Test creating base exception with custom error code."""
        error = ADOFlowException("Test error", "CUSTOM_CODE")
        assert error.error_code == "CUSTOM_CODE"

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from ADOFlowException."""
        exceptions = [
            ConfigurationError,
            AuthenticationError,
            AuthorizationError,
            NetworkError,
            APIError,
            DataValidationError,
            WorkItemError,
            DatabaseError,
            MetricsCalculationError,
            ExportError,
        ]

        for exc_class in exceptions:
            error = exc_class("Test message")
            assert isinstance(error, ADOFlowException)
            assert isinstance(error, Exception)


class TestAPIError:
    """Test API-specific error handling."""

    def test_api_error_basic(self):
        """Test basic API error creation."""
        error = APIError("API failed")
        assert str(error) == "API failed"
        assert error.status_code is None
        assert error.response_text is None

    def test_api_error_with_details(self):
        """Test API error with status code and response."""
        error = APIError("API failed", status_code=404, response_text="Not found")
        assert error.status_code == 404
        assert error.response_text == "Not found"

    def test_api_error_attributes(self):
        """Test API error attributes are accessible."""
        error = APIError("Test", 500, "Internal server error")
        assert hasattr(error, 'status_code')
        assert hasattr(error, 'response_text')
        assert hasattr(error, 'message')
        assert hasattr(error, 'error_code')


class TestSpecificExceptions:
    """Test specific exception types."""

    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Invalid config"

    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Auth failed"

    def test_authorization_error(self):
        """Test authorization error."""
        error = AuthorizationError("Access denied")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Access denied"

    def test_network_error(self):
        """Test network error."""
        error = NetworkError("Connection failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Connection failed"

    def test_data_validation_error(self):
        """Test data validation error."""
        error = DataValidationError("Invalid data")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Invalid data"

    def test_work_item_error(self):
        """Test work item error."""
        error = WorkItemError("Work item processing failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Work item processing failed"

    def test_database_error(self):
        """Test database error."""
        error = DatabaseError("DB connection failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "DB connection failed"

    def test_metrics_calculation_error(self):
        """Test metrics calculation error."""
        error = MetricsCalculationError("Calculation failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Calculation failed"

    def test_export_error(self):
        """Test export error."""
        error = ExportError("Export failed")
        assert isinstance(error, ADOFlowException)
        assert str(error) == "Export failed"


class TestExceptionRaising:
    """Test that exceptions can be properly raised and caught."""

    def test_raise_and_catch_ado_flow_exception(self):
        """Test raising and catching ADO Flow exception."""
        with pytest.raises(ADOFlowException) as exc_info:
            raise ADOFlowException("Test error")
        
        assert str(exc_info.value) == "Test error"

    def test_catch_specific_as_base(self):
        """Test that specific exceptions can be caught as base exception."""
        with pytest.raises(ADOFlowException):
            raise ConfigurationError("Config error")

    def test_catch_specific_exception(self):
        """Test catching specific exception type."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config error")
        
        assert isinstance(exc_info.value, ADOFlowException)
        assert str(exc_info.value) == "Config error"

    def test_exception_chaining(self):
        """Test exception chaining works properly."""
        original_error = ValueError("Original error")
        
        with pytest.raises(DatabaseError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise DatabaseError("Database error") from e
        
        assert exc_info.value.__cause__ is original_error