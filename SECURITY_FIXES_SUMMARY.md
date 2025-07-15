# Security Fixes Summary

## Organization and Project Names Removed

For security reasons, all hardcoded organization and project names have been replaced with generic placeholders.

### Files Updated

1. **`config/config.json`**
   - Changed: `"org_url": "https://dev.azure.com/bofaz"` → `"org_url": "https://dev.azure.com/your-org"`
   - Changed: `"default_project": "Axos-Universal-Core"` → `"default_project": "your-project"`

2. **`src/mock_data.py`**
   - Changed default parameters from `org_name="bofaz", project_name="Axos-Universal-Core"`
   - To: `org_name="example-org", project_name="example-project"`

3. **`executive-dashboard.html`**
   - Fallback config changed from `bofaz` → `example-org`
   - Fallback project changed from `Axos-Universal-Core` → `example-project`
   - Comment example changed to generic format

4. **`js/dashboard.js`**
   - Changed hardcoded URL from `"https://dev.azure.com/bofaz"` → `"https://dev.azure.com/your-org"`
   - Changed hardcoded project from `"Axos-Universal-Core"` → `"your-project"`

### Configuration Usage

The system now properly uses configuration variables instead of hardcoded values:

1. **Azure DevOps Client** (`src/azure_devops_client.py`)
   - Uses `self.org_url` and `self.project` from configuration
   - Generates links dynamically: `https://{org_name}.visualstudio.com/{project}/_workitems/edit/{id}`

2. **Mock Data Generation** (`src/mock_data.py`)
   - Accepts org_name and project_name as parameters
   - Uses these parameters to generate URLs dynamically

3. **Executive Dashboard** (`executive-dashboard.html`)
   - Loads configuration from `config/config.json`
   - Falls back to generic values if config fails to load
   - Uses configuration for all link generation

### Setup Instructions

Users should update their `config/config.json` with their actual values:

```json
{
  "azure_devops": {
    "org_url": "https://dev.azure.com/YOUR-ORG-NAME",
    "default_project": "YOUR-PROJECT-NAME",
    "pat_token": "${AZURE_DEVOPS_PAT}"
  }
}
```

### Benefits

- ✅ No sensitive organization/project names in code
- ✅ Configuration-driven approach
- ✅ Easy to deploy to different organizations
- ✅ Secure by default with generic placeholders
- ✅ All URLs generated dynamically from configuration