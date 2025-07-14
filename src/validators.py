"""Input validation utilities for security and data integrity."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from .exceptions import DataValidationError


class InputValidator:
    """Comprehensive input validation for security and data integrity."""
    
    # Pattern for Azure DevOps organization URLs
    AZURE_DEVOPS_URL_PATTERN = re.compile(
        r'^https://dev\.azure\.com/[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?/?$'
    )
    
    # Pattern for project names (alphanumeric, hyphens, underscores)
    PROJECT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Pattern for safe file paths (no path traversal)
    SAFE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]+$')
    
    @staticmethod
    def validate_azure_org_url(url: str) -> Tuple[bool, str]:
        """Validate Azure DevOps organization URL."""
        if not url:
            return False, "Organization URL cannot be empty"
        
        if not isinstance(url, str):
            return False, "Organization URL must be a string"
        
        if len(url) > 200:
            return False, "Organization URL is too long"
        
        if not InputValidator.AZURE_DEVOPS_URL_PATTERN.match(url):
            return False, "Invalid Azure DevOps organization URL format"
        
        return True, "Valid organization URL"
    
    @staticmethod
    def validate_project_name(project: str) -> Tuple[bool, str]:
        """Validate Azure DevOps project name."""
        if not project:
            return False, "Project name cannot be empty"
        
        if not isinstance(project, str):
            return False, "Project name must be a string"
        
        if len(project) > 64:
            return False, "Project name is too long (max 64 characters)"
        
        if not InputValidator.PROJECT_NAME_PATTERN.match(project):
            return False, "Project name contains invalid characters (only alphanumeric, hyphens, and underscores allowed)"
        
        return True, "Valid project name"
    
    @staticmethod
    def validate_pat_token(token: str) -> Tuple[bool, str]:
        """Validate Personal Access Token format."""
        if not token:
            return False, "PAT token cannot be empty"
        
        if not isinstance(token, str):
            return False, "PAT token must be a string"
        
        if len(token) < 20:
            return False, "PAT token is too short (minimum 20 characters)"
        
        if len(token) > 100:
            return False, "PAT token is too long (maximum 100 characters)"
        
        # Basic format check (Base64-like characters)
        if not re.match(r'^[a-zA-Z0-9+/=]+$', token):
            return False, "PAT token contains invalid characters"
        
        return True, "Valid PAT token format"
    
    @staticmethod
    def validate_days_back(days: Union[int, str]) -> Tuple[bool, str, int]:
        """Validate days_back parameter."""
        try:
            days_int = int(days)
        except (ValueError, TypeError):
            return False, "Days back must be a valid integer", 0
        
        if days_int < 1:
            return False, "Days back must be at least 1", 0
        
        if days_int > 3650:  # 10 years max
            return False, "Days back cannot exceed 3650 (10 years)", 0
        
        return True, "Valid days back value", days_int
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> Tuple[bool, str, int]:
        """Validate port number."""
        try:
            port_int = int(port)
        except (ValueError, TypeError):
            return False, "Port must be a valid integer", 0
        
        if port_int < 1:
            return False, "Port must be at least 1", 0
        
        if port_int > 65535:
            return False, "Port cannot exceed 65535", 0
        
        if port_int < 1024:
            return False, "Port should be above 1024 for non-privileged access", port_int
        
        return True, "Valid port number", port_int
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> Tuple[bool, str]:
        """Validate file path for security."""
        if not path:
            return False, "File path cannot be empty"
        
        if not isinstance(path, str):
            return False, "File path must be a string"
        
        # Check for path traversal attempts
        if '..' in path:
            return False, "Path traversal detected in file path"
        
        # Check for absolute paths outside project
        try:
            path_obj = Path(path)
            
            # Convert to absolute and resolve
            resolved_path = path_obj.resolve()
            
            # Check if path is within project directory
            project_root = Path(__file__).parent.parent.resolve()
            try:
                resolved_path.relative_to(project_root)
            except ValueError:
                return False, "File path is outside project directory"
            
            if must_exist and not resolved_path.exists():
                return False, "File path does not exist"
            
        except (OSError, ValueError) as e:
            return False, f"Invalid file path: {str(e)}"
        
        return True, "Valid file path"
    
    @staticmethod
    def validate_json_data(data: str) -> Tuple[bool, str, Optional[Any]]:
        """Validate JSON data."""
        if not data:
            return False, "JSON data cannot be empty", None
        
        if not isinstance(data, str):
            return False, "JSON data must be a string", None
        
        if len(data) > 10 * 1024 * 1024:  # 10MB limit
            return False, "JSON data is too large (max 10MB)", None
        
        try:
            import json
            parsed_data = json.loads(data)
            return True, "Valid JSON data", parsed_data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}", None
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_work_item_data(item: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate work item data structure."""
        required_fields = ['id', 'title', 'type', 'current_state', 'created_date']
        
        for field in required_fields:
            if field not in item:
                return False, f"Missing required field: {field}"
            
            if not item[field]:
                return False, f"Field '{field}' cannot be empty"
        
        # Validate ID format
        item_id = item['id']
        if not isinstance(item_id, (str, int)):
            return False, "Work item ID must be string or integer"
        
        # Validate title length
        title = item['title']
        if len(str(title)) > 500:
            return False, "Work item title is too long (max 500 characters)"
        
        # Validate date format
        created_date = item['created_date']
        if isinstance(created_date, str):
            try:
                from datetime import datetime
                datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            except ValueError:
                return False, "Invalid created_date format"
        
        return True, "Valid work item data"
    
    @staticmethod
    def validate_config_data(config: Dict[str, Any]) -> List[str]:
        """Validate configuration data and return list of errors."""
        errors = []
        
        # Validate Azure DevOps configuration
        if 'azure_devops' in config:
            azure_config = config['azure_devops']
            
            if 'org_url' in azure_config:
                is_valid, message = InputValidator.validate_azure_org_url(azure_config['org_url'])
                if not is_valid:
                    errors.append(f"Azure DevOps org_url: {message}")
            
            if 'default_project' in azure_config:
                is_valid, message = InputValidator.validate_project_name(azure_config['default_project'])
                if not is_valid:
                    errors.append(f"Azure DevOps project: {message}")
        
        # Validate data management configuration
        if 'data_management' in config:
            data_config = config['data_management']
            
            if 'data_directory' in data_config:
                is_valid, message = InputValidator.validate_file_path(str(data_config['data_directory']))
                if not is_valid:
                    errors.append(f"Data directory: {message}")
        
        return errors


class SecurityValidator:
    """Security-focused validation utilities."""
    
    @staticmethod
    def check_for_injection_patterns(value: str) -> List[str]:
        """Check for common injection attack patterns."""
        threats = []
        
        if not isinstance(value, str):
            return threats
        
        value_lower = value.lower()
        
        # SQL injection patterns
        sql_patterns = [
            r"'\s*or\s*'",
            r"'\s*and\s*'",
            r"union\s+select",
            r"insert\s+into",
            r"delete\s+from",
            r"drop\s+table",
            r"exec\s*\(",
            r"script\s*>",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value_lower):
                threats.append(f"Potential SQL injection pattern detected: {pattern}")
        
        # Command injection patterns
        cmd_patterns = [
            r";\s*rm\s+",
            r";\s*cat\s+",
            r"\|\s*nc\s+",
            r"&&\s*curl",
            r"`[^`]+`",
            r"\$\([^)]+\)",
        ]
        
        for pattern in cmd_patterns:
            if re.search(pattern, value_lower):
                threats.append(f"Potential command injection pattern detected: {pattern}")
        
        return threats
    
    @staticmethod
    def validate_host_binding(host: str) -> Tuple[bool, str]:
        """Validate host binding for security."""
        if not host:
            return False, "Host cannot be empty"
        
        # Only allow safe host bindings
        safe_hosts = ['127.0.0.1', 'localhost', '0.0.0.0']
        
        if host not in safe_hosts:
            return False, f"Host '{host}' is not in allowed list: {safe_hosts}"
        
        if host == '0.0.0.0':
            return True, "WARNING: Binding to 0.0.0.0 exposes service to all network interfaces"
        
        return True, "Safe host binding"