"""Service layer for business logic and complex operations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .azure_devops_client import AzureDevOpsClient
from .config_manager import get_settings
from .exceptions import (
    ADOFlowException,
    AuthenticationError,
    ConfigurationError,
    NetworkError
)


class AzureDevOpsService:
    """Service for Azure DevOps operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
    
    def validate_connection(self) -> Tuple[bool, str]:
        """Validate Azure DevOps connection and return status with message."""
        try:
            pat_token = os.getenv("AZURE_DEVOPS_PAT")
            
            if not pat_token:
                return False, "AZURE_DEVOPS_PAT environment variable not set"
            
            if len(pat_token) < 20:
                return False, f"PAT token seems short (length: {len(pat_token)})"
            
            self.client = AzureDevOpsClient(
                org_url=self.settings.azure_devops.org_url,
                project=self.settings.azure_devops.default_project,
                pat_token=pat_token
            )
            
            if not self.client.verify_connection():
                return False, "Azure DevOps connection verification failed"
            
            return True, "Azure DevOps connection verified successfully"
            
        except AuthenticationError as e:
            return False, f"Authentication failed: {e.message}"
        except ConfigurationError as e:
            return False, f"Configuration error: {e.message}"
        except NetworkError as e:
            return False, f"Network error: {e.message}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def fetch_work_items_with_fallback(
        self, 
        days_back: int, 
        history_limit: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[List[Dict], bool]:
        """
        Fetch work items with intelligent fallback.
        
        Returns:
            Tuple of (work_items, used_real_data)
        """
        # Try to validate connection first
        is_valid, message = self.validate_connection()
        
        if not is_valid:
            return [], False
        
        try:
            # Attempt to fetch real data
            work_items = self.client.get_work_items(
                days_back=days_back,
                history_limit=history_limit,
                progress_callback=progress_callback
            )
            
            if work_items:
                return work_items, True
            else:
                # No data returned - likely permissions issue
                return [], False
                
        except (AuthenticationError, ConfigurationError, NetworkError):
            # Known issues that should fallback to mock
            return [], False
        except Exception:
            # Unexpected errors should also fallback
            return [], False


class DataManagementService:
    """Service for data management operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = self.settings.data_management.data_directory
    
    def validate_work_items_file(self) -> Tuple[bool, str, int]:
        """
        Validate work items file exists and has data.
        
        Returns:
            Tuple of (is_valid, message, item_count)
        """
        work_items_file = self.data_dir / "work_items.json"
        
        if not work_items_file.exists():
            return False, "Work items file not found", 0
        
        try:
            with open(work_items_file) as f:
                work_items_data = json.load(f)
            
            item_count = len(work_items_data) if work_items_data else 0
            
            if item_count == 0:
                return False, "Work items file is empty", 0
            
            return True, f"Found {item_count} work items", item_count
            
        except json.JSONDecodeError:
            return False, "Work items file contains invalid JSON", 0
        except Exception as e:
            return False, f"Error reading work items file: {str(e)}", 0
    
    def reset_data_directory(self, keep_config: bool = True):
        """Reset data directory while optionally preserving config."""
        import shutil
        
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        
        if not keep_config:
            config_file = Path("config/config.json")
            if config_file.exists():
                config_file.unlink()


class ValidationService:
    """Service for various validation operations."""
    
    @staticmethod
    def validate_azure_devops_config() -> List[str]:
        """Validate Azure DevOps configuration and return list of errors."""
        errors = []
        
        try:
            settings = get_settings()
            
            if not hasattr(settings, 'azure_devops'):
                errors.append("Missing 'azure_devops' section in config")
                return errors
            
            if not settings.azure_devops.org_url:
                errors.append("Missing 'org_url' in azure_devops config")
            elif not settings.azure_devops.org_url.startswith('https://dev.azure.com/'):
                errors.append(f"Unusual org_url format: {settings.azure_devops.org_url}")
            
            if not settings.azure_devops.default_project:
                errors.append("Missing 'default_project' in azure_devops config")
                
        except Exception as e:
            errors.append(f"Configuration error: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_pat_token() -> Tuple[bool, str]:
        """Validate PAT token and return status with message."""
        pat_token = os.getenv("AZURE_DEVOPS_PAT")
        
        if not pat_token:
            return False, "AZURE_DEVOPS_PAT environment variable not set"
        
        if len(pat_token) < 20:
            return False, f"PAT token seems short (length: {len(pat_token)})"
        
        return True, f"PAT Token: {'*' * (len(pat_token) - 4)}{pat_token[-4:]} (length: {len(pat_token)})"
    
    @staticmethod
    def validate_data_directory() -> Tuple[bool, str]:
        """Validate data directory exists and is accessible."""
        data_dir = Path("data")
        
        try:
            if not data_dir.exists():
                data_dir.mkdir(parents=True, exist_ok=True)
                return True, "Created data directory"
            else:
                return True, "Data directory exists"
                
        except PermissionError:
            return False, "Permission denied creating data directory"
        except Exception as e:
            return False, f"Error with data directory: {str(e)}"


class ErrorAnalysisService:
    """Service for analyzing and categorizing errors."""
    
    @staticmethod
    def categorize_error(error_msg: str) -> Tuple[str, List[str]]:
        """
        Categorize error and provide recommendations.
        
        Returns:
            Tuple of (category, recommendations)
        """
        error_lower = error_msg.lower()
        
        if "not found" in error_lower and "project" in error_lower:
            return "project_not_found", [
                "Project name is incorrect in config/config.json",
                "You don't have access to this project",
                "The project has been renamed or moved"
            ]
        
        if any(keyword in error_lower for keyword in ['conditional access', 'authentication', 'unauthorized']):
            return "authentication", [
                "Check your PAT token is valid and not expired",
                "Verify you have access to the project",
                "Check for conditional access policies"
            ]
        
        if any(keyword in error_lower for keyword in ['json', 'invalid', 'parse']):
            return "data_format", [
                "API returned unexpected format",
                "May be due to conditional access policy redirects",
                "Try using --use-mock flag for testing"
            ]
        
        if any(keyword in error_lower for keyword in ['network', 'connection', 'timeout']):
            return "network", [
                "Check network connectivity",
                "Verify Azure DevOps service is accessible",
                "Try again later if service is experiencing issues"
            ]
        
        return "unknown", [
            "Check logs for more details",
            "Try using --use-mock flag for testing",
            "Contact support if issue persists"
        ]