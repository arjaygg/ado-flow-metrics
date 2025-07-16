# Configuration Fix Guide

## Problem: Project Not Found Error

### Issue Description
The `data fresh` command fails with "Project Not Found Error" because the organization name is set to placeholder values like "your-org" instead of actual Azure DevOps organization names.

### Root Cause
Several files contained hardcoded placeholder values:
- `config/config.sample.json` has `"org_url": "https://dev.azure.com/your-organization"`
- Demo scripts default to `"https://dev.azure.com/your-org"` when environment variables aren't set
- Configuration manager doesn't validate against placeholder values

### Files Fixed
1. **demo_live_integration.py** - Enhanced error handling and validation
2. **test_ado_integration.py** - Updated example URLs  
3. **src/config_manager.py** - Added placeholder validation
4. **fix_config.py** - New diagnostic and repair tool

## Solution

### Quick Fix (Recommended)
Run the configuration doctor to diagnose and fix issues:
```bash
python3 fix_config.py
```

The tool will:
- ✅ Check current configuration for placeholder values
- ✅ Identify environment variable issues  
- ✅ Provide interactive fix or manual instructions
- ✅ Create proper config.json with actual values

### Manual Fix Options

#### Option 1: Environment Variables
```bash
export AZURE_DEVOPS_PAT='your-personal-access-token'
export AZURE_DEVOPS_ORG='https://dev.azure.com/YOUR_ACTUAL_ORG_NAME'
export AZURE_DEVOPS_PROJECT='YourActualProjectName'
```

#### Option 2: Configuration File
1. Copy `config/config.sample.json` to `config/config.json`
2. Replace placeholder values:
   ```json
   {
     "azure_devops": {
       "org_url": "https://dev.azure.com/YOUR_ACTUAL_ORG_NAME",
       "default_project": "YourActualProjectName",
       "api_version": "7.0"
     }
   }
   ```

### Validation

#### Test with Mock Data
```bash
python3 -m src.cli data fresh --use-mock
```

#### Test with Real Azure DevOps (requires PAT token)
```bash
python3 -m src.cli data fresh --days-back 7
```

### Error Prevention

The updated configuration manager now:
- ✅ Validates against placeholder values like "your-org"
- ✅ Provides clear error messages with fix instructions
- ✅ Checks both environment variables and config files
- ✅ Fails fast with helpful guidance instead of cryptic errors

### Common Issues and Solutions

#### Issue: "Configuration contains placeholder values"
**Solution:** Run `python3 fix_config.py` and choose option 1 (Interactive fix)

#### Issue: "No configuration file found"  
**Solution:** Copy `config.sample.json` to `config.json` and update values

#### Issue: Still getting Project Not Found after fix
**Possible causes:**
- PAT token doesn't have correct permissions
- Organization or project name is misspelled  
- Network connectivity issues
- Project access restrictions

**Debugging:**
```bash
# Test API access directly
curl -u ":$AZURE_DEVOPS_PAT" \
  "https://dev.azure.com/YOUR_ORG/YOUR_PROJECT/_apis/wit/workitems?ids=1&api-version=7.0"
```

## Implementation Details

### Configuration Manager Changes
- Added validation in `load()` method to detect placeholder values
- Enhanced error messages with specific fix instructions
- Better fallback logic for missing configuration

### Demo Script Improvements  
- Smart detection of placeholder URLs
- Graceful fallback to mock data when misconfigured
- Clear user guidance for proper setup

### New Diagnostic Tool
- `fix_config.py` provides interactive configuration repair
- Detects common configuration issues automatically
- Supports both environment variable and config file approaches

## Usage Examples

### Working Configuration (Environment Variables)
```bash
export AZURE_DEVOPS_PAT='ghp_xxxxxxxxxxxxxxxxxxxx'
export AZURE_DEVOPS_ORG='https://dev.azure.com/contoso'  
export AZURE_DEVOPS_PROJECT='MyProject'

python3 -m src.cli data fresh --days-back 30
```

### Working Configuration (Config File)
```json
{
  "azure_devops": {
    "org_url": "https://dev.azure.com/contoso",
    "default_project": "MyProject", 
    "api_version": "7.0"
  }
}
```

```bash
python3 -m src.cli data fresh --days-back 30
```

This fix ensures users get clear, actionable error messages instead of confusing "Project Not Found" errors when using placeholder organization names.