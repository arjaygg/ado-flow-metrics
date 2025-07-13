# Flow Metrics Setup Guide

Quick setup guide for the Flow Metrics project with Executive Dashboard and Work Items features.

## 🚀 Quick Start

### Option 1: Simple Setup Launcher (Recommended)
```cmd
run_setup.bat
```
- Choose option 1 for WSL users
- Choose option 2 for Windows native setup

### Option 2: Direct PowerShell Setup

#### For WSL Users (accessing from `\\wsl$\...` paths)
```powershell
.\setup_wsl_direct.ps1
```

#### For Windows Native Setup
```powershell
.\setup_windows.ps1
```

## 📋 What Gets Installed

✅ **Python virtual environment**  
✅ **All dependencies** (25+ packages)  
✅ **Configuration files** with work items support  
✅ **Project directories** (data, config, logs, exports)  
✅ **PowerShell convenience scripts**  
✅ **Executive dashboard** with work items table  

## 🎯 After Setup

### Launch Executive Dashboard
```powershell
.\start_executive_dashboard.ps1
```
Then open: http://localhost:8080/executive-dashboard.html

### Launch Standard Dashboard
```powershell
.\start_demo.ps1
```

### Command Line Usage
```powershell
.\flow_cli.ps1 calculate --use-mock-data
.\flow_cli.ps1 serve --executive --port 8080
```

## 🔧 Azure DevOps Configuration

To connect to real data:
1. Set token: `$env:AZURE_DEVOPS_PAT='your_token_here'`
2. Edit `config\config.json` with your org/project details
3. Run: `.\flow_cli.ps1 fetch`

## ✨ Executive Dashboard Features

- **Two-tab interface**: Overview + Work Items Details
- **Interactive work items table** with pagination (50 items/page)
- **Chart drill-down** (click charts to filter work items)
- **Workstream filtering** (Data, QA, OutSystems, Others)
- **CSV export** capability
- **Direct Azure DevOps links** for work items
- **Real-time filter synchronization**

## 🛠️ Troubleshooting

### PowerShell Execution Policy Issues
If you get execution policy errors, run:
```cmd
powershell -ExecutionPolicy Bypass -File "setup_windows.ps1"
```

### WSL Issues
Make sure WSL is installed and working:
```cmd
wsl --version
```

### Test Installation
```powershell
.\test_installation.ps1
```

## 📁 File Structure After Setup

```
├── config/
│   ├── config.json              # Main configuration
│   └── workstream_config.json   # Team/workstream definitions
├── data/                        # Generated data files
├── logs/                        # Application logs
├── exports/                     # CSV export files
├── venv/                        # Python virtual environment
├── flow_cli.ps1                 # PowerShell CLI wrapper
├── start_executive_dashboard.ps1 # Executive dashboard launcher
├── start_demo.ps1               # Demo dashboard launcher
└── test_installation.ps1        # Installation test script
```

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run the test script: `.\test_installation.ps1`
3. Verify all required files are present
4. Check PowerShell execution policy settings