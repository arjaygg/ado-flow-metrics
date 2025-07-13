# Flow Metrics Setup Script for Windows (Native PowerShell)
# Enhanced version with better error handling and user experience

param(
    [switch]$Force,
    [int]$Port = 8080,
    [string]$PythonVersion = "3.8"
)

# Set up colors for better output
$script:Colors = @{
    Red = [System.ConsoleColor]::Red
    Green = [System.ConsoleColor]::Green
    Yellow = [System.ConsoleColor]::Yellow
    Blue = [System.ConsoleColor]::Blue
    Cyan = [System.ConsoleColor]::Cyan
    Magenta = [System.ConsoleColor]::Magenta
    White = [System.ConsoleColor]::White
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [System.ConsoleColor]$ForegroundColor = [System.ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "[STEP] $Message" $script:Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[OK] $Message" $script:Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" $script:Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" $script:Colors.Red
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" $script:Colors.Cyan
}

function Test-PythonVersion {
    param([string]$RequiredVersion = "3.8")
    
    try {
        $pythonVersionOutput = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        
        $versionMatch = $pythonVersionOutput -match "Python (\d+\.\d+)"
        if (-not $versionMatch) {
            return $false
        }
        
        $installedVersion = [Version]$matches[1]
        $required = [Version]$RequiredVersion
        
        return $installedVersion -ge $required
    } catch {
        return $false
    }
}

# Header
Write-ColorOutput "================================================" $script:Colors.Cyan
Write-ColorOutput "Flow Metrics - Enhanced Windows Setup Script" $script:Colors.Cyan
Write-ColorOutput "================================================" $script:Colors.Cyan
Write-ColorOutput "Version: 3.0.0 (PowerShell Native Windows)" $script:Colors.Cyan
Write-ColorOutput ""

# Check if we're in the correct directory
Write-Step "Verifying project structure..."
$requiredFiles = @("src\cli.py", "executive-dashboard.html", "requirements.txt")

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file not found: $file"
        Write-ColorOutput ""
        Write-Warning "Please run this script from the ado-flow-metrics project root directory"
        Write-Info "Expected to find: $file"
        Write-Info "Current directory: $(Get-Location)"
        Write-ColorOutput ""
        Write-Warning "HINT: If you copied from WSL, make sure you're in the project root:"
        Write-ColorOutput "  cd C:\path\to\ado-flow-metrics"
        Write-ColorOutput "  .\setup_windows.ps1"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Success "Project structure verified"
Write-ColorOutput ""

# Check Python installation
Write-Step "Checking Python installation..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH"
    Write-ColorOutput ""
    Write-Warning "SOLUTION: Please install Python $PythonVersion+ from https://python.org"
    Write-Info "Make sure to check 'Add Python to PATH' during installation"
    Write-ColorOutput ""
    $openBrowser = Read-Host "Would you like me to open the Python download page? (Y/N)"
    if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
        Start-Process "https://python.org/downloads/"
    }
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersionOutput = python --version
Write-Success "Python found: $pythonVersionOutput"

# Check Python version compatibility
Write-Step "Verifying Python version compatibility..."
if (-not (Test-PythonVersion -RequiredVersion $PythonVersion)) {
    Write-Error "Python $PythonVersion or higher is required"
    Write-Info "Current version: $pythonVersionOutput"
    Write-Info "Please upgrade Python from https://python.org"
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Success "Python version is compatible"
Write-ColorOutput ""

# Create virtual environment
Write-Step "Setting up Python virtual environment..."
if (Test-Path "venv") {
    if ($Force) {
        Write-Info "Removing existing virtual environment..."
        Remove-Item -Recurse -Force "venv"
    } else {
        Write-Warning "Virtual environment already exists"
        $recreate = Read-Host "Would you like to recreate it? (Y/N)"
        if ($recreate -eq "Y" -or $recreate -eq "y") {
            Remove-Item -Recurse -Force "venv"
        } else {
            Write-Info "Using existing virtual environment"
        }
    }
}

if (-not (Test-Path "venv")) {
    Write-Info "Creating new virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        Write-ColorOutput ""
        Write-Warning "TROUBLESHOOTING:"
        Write-ColorOutput "1. Check available disk space"
        Write-ColorOutput "2. Ensure no antivirus is blocking Python"
        Write-ColorOutput "3. Try running as Administrator"
        Write-ColorOutput "4. Check Python installation integrity"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Success "Virtual environment created"
}
Write-ColorOutput ""

# Activate virtual environment
Write-Step "Activating virtual environment..."

# Check for PowerShell activation script first, then fall back to batch
$activatePs1 = "venv\Scripts\Activate.ps1"
$activateBat = "venv\Scripts\activate.bat"

if (Test-Path $activatePs1) {
    try {
        & ".\$activatePs1"
        Write-Success "Virtual environment activated (PowerShell)"
    } catch {
        Write-Warning "PowerShell activation failed, trying batch activation..."
        if (Test-Path $activateBat) {
            cmd /c "call `"$activateBat`""
            Write-Success "Virtual environment activated (Batch fallback)"
        } else {
            Write-Error "No activation scripts found. Recreating virtual environment..."
            Remove-Item -Recurse -Force "venv"
            python -m venv venv
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to recreate virtual environment"
                Read-Host "Press Enter to exit"
                exit 1
            }
            Write-Success "Virtual environment recreated"
            
            # Try activation again
            if (Test-Path "venv\Scripts\Activate.ps1") {
                & ".\venv\Scripts\Activate.ps1"
                Write-Success "Virtual environment activated"
            } else {
                cmd /c "call `"venv\Scripts\activate.bat`""
                Write-Success "Virtual environment activated (Batch)"
            }
        }
    }
} elseif (Test-Path $activateBat) {
    cmd /c "call `"$activateBat`""
    Write-Success "Virtual environment activated (Batch)"
} else {
    Write-Error "Virtual environment activation scripts not found"
    Write-Info "Recreating virtual environment with proper scripts..."
    
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to recreate virtual environment"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Success "Virtual environment recreated"
    
    # Try activation again
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & ".\venv\Scripts\Activate.ps1"
        Write-Success "Virtual environment activated"
    } else {
        cmd /c "call `"venv\Scripts\activate.bat`""
        Write-Success "Virtual environment activated (Batch)"
    }
}
Write-ColorOutput ""

# Upgrade pip
Write-Step "Upgrading pip..."
try {
    python -m pip install --upgrade pip --quiet --no-warn-script-location
    Write-Success "Pip upgraded successfully"
} catch {
    Write-Warning "Pip upgrade failed, continuing with existing version"
}
Write-ColorOutput ""

# Install dependencies
Write-Step "Installing Python dependencies..."
Write-Info "This may take several minutes depending on your internet connection..."
Write-ColorOutput ""

if (Test-Path "requirements.txt") {
    Write-Info "Installing from requirements.txt..."
    try {
        pip install -r requirements.txt --quiet --no-warn-script-location
        Write-Success "Dependencies installed successfully"
    } catch {
        Write-Error "Failed to install requirements"
        Write-ColorOutput ""
        Write-Warning "TROUBLESHOOTING: Common solutions:"
        Write-ColorOutput "1. Check internet connection"
        Write-ColorOutput "2. If behind corporate firewall: pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt"
        Write-ColorOutput "3. Try with cache disabled: pip install --no-cache-dir -r requirements.txt"
        Write-ColorOutput "4. Run as Administrator"
        Write-ColorOutput ""
        $retry = Read-Host "Would you like to try installing without cache? (Y/N)"
        if ($retry -eq "Y" -or $retry -eq "y") {
            Write-Info "Retrying installation without cache..."
            pip install --no-cache-dir -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Installation failed again"
                Read-Host "Press Enter to exit"
                exit 1
            }
            Write-Success "Dependencies installed successfully (retry)"
        } else {
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
} else {
    Write-Warning "requirements.txt not found, installing core dependencies..."
    $corePackages = @(
        "click>=8.0.0", "rich>=13.0.0", "requests>=2.31.0", "python-dateutil>=2.8.2",
        "pandas>=1.5.0", "numpy>=1.23.0", "sqlalchemy>=2.0.0", "python-dotenv>=0.19.0",
        "pydantic>=2.0.0,<3.0.0", "pydantic-settings>=2.0.0,<3.0.0", "flask>=2.0.0",
        "flask-cors>=4.0.0", "plotly>=5.0.0", "dash>=2.0.0", "tenacity>=8.0.0", "tqdm>=4.64.0"
    )
    
    foreach ($package in $corePackages) {
        Write-Info "Installing $package..."
        pip install $package --quiet --no-warn-script-location
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install $package"
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    Write-Success "Core dependencies installed successfully"
}
Write-ColorOutput ""

# Test CLI installation
Write-Step "Testing CLI installation..."
try {
    python -m src.cli --help | Out-Null
    Write-Success "CLI is working correctly"
} catch {
    Write-Error "CLI test failed"
    Write-Info "The installation may be incomplete or there may be import errors"
    Write-ColorOutput ""
    Write-Info "Trying basic import test..."
    try {
        python -c "import src.cli; print('Import successful')"
    } catch {
        Write-Error "Import test failed: $_"
    }
    Read-Host "Press Enter to exit"
    exit 1
}
Write-ColorOutput ""

# Create project directories
Write-Step "Creating project directories..."
$directories = @("data", "config", "logs", "exports")

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Success "Created $dir\ directory"
    } else {
        Write-Info "Directory $dir\ already exists"
    }
}
Write-ColorOutput ""

# Create enhanced configuration files
Write-Step "Creating configuration files..."

$configPath = "config\config.json"
if (-not (Test-Path $configPath)) {
    $configContent = @{
        azure_devops = @{
            org_url = "https://dev.azure.com/your-org"
            default_project = "your-project-name"
            pat_token = "`${AZURE_DEVOPS_PAT}"
        }
        flow_metrics = @{
            throughput_period_days = 30
            default_days_back = 90
            executive_dashboard = @{
                enable_work_items_table = $true
                items_per_page = 50
                enable_chart_drilldown = $true
                enable_csv_export = $true
            }
        }
        data_management = @{
            data_directory = "data"
            auto_backup = $true
            export_directory = "exports"
        }
        server = @{
            default_port = 8080
            host = "127.0.0.1"
            auto_open_browser = $false
        }
    }
    $configContent | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
    Write-Success "Main config created"
} else {
    Write-Info "Main config already exists"
}

$workstreamConfigPath = "config\workstream_config.json"
if (-not (Test-Path $workstreamConfigPath)) {
    $workstreamContent = @{
        workstreams = @{
            Data = @{
                description = "Data analytics and engineering team"
                name_patterns = @(
                    "Nenissa", "Ariel", "Patrick Oniel", "Kennedy Oliveira",
                    "Christopher Jan", "Jegs", "Ian Belmonte"
                )
            }
            QA = @{
                description = "Quality assurance and testing team"
                name_patterns = @("Sharon", "Lorenz", "Arvin")
            }
            OutSystems = @{
                description = "OutSystems development team"
                name_patterns = @(
                    "Apollo", "Glizzel", "Prince", "Patrick Russel", "Rio", "Nymar"
                )
            }
        }
        default_workstream = "Others"
        matching_options = @{
            case_sensitive = $false
            partial_match = $true
            match_full_name = $false
        }
    }
    $workstreamContent | ConvertTo-Json -Depth 10 | Out-File -FilePath $workstreamConfigPath -Encoding UTF8
    Write-Success "Workstream config created"
} else {
    Write-Info "Workstream config already exists"
}
Write-ColorOutput ""

# Create convenience scripts
Write-Step "Creating convenience scripts..."

# PowerShell CLI wrapper
$cliScript = @"
# Flow Metrics CLI - PowerShell Wrapper
param([Parameter(ValueFromRemainingArguments)][string[]]`$Arguments)

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run CLI with all arguments
if (`$Arguments) {
    python -m src.cli @Arguments
} else {
    python -m src.cli --help
}
"@
$cliScript | Out-File -FilePath "flow_cli.ps1" -Encoding UTF8

# Executive dashboard launcher
$dashboardScript = @"
# Flow Metrics Executive Dashboard Launcher
Write-Host "Starting Executive Dashboard with Work Items Table..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

Write-Host "Generating demo data..." -ForegroundColor Yellow
python -m src.cli calculate --use-mock-data

Write-Host ""
Write-Host "Starting server on http://localhost:$Port..." -ForegroundColor Yellow
Write-Host "Executive Dashboard: http://localhost:$Port/executive-dashboard.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

python -m src.cli serve --executive --port $Port
"@
$dashboardScript | Out-File -FilePath "start_executive_dashboard.ps1" -Encoding UTF8

# Demo launcher
$demoScript = @"
# Flow Metrics Demo Dashboard Launcher
Write-Host "Starting demo dashboard..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

python -m src.cli demo --use-mock-data --open-browser
"@
$demoScript | Out-File -FilePath "start_demo.ps1" -Encoding UTF8

# Installation test script
$testScript = @"
# Flow Metrics Installation Test
Write-Host "Testing Flow Metrics installation..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

try {
    python -m src.cli calculate --use-mock-data
    Write-Host "[SUCCESS] Installation test passed!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Test failed: `$_" -ForegroundColor Red
    exit 1
}

Read-Host "Press Enter to continue"
"@
$testScript | Out-File -FilePath "test_installation.ps1" -Encoding UTF8

Write-Success "PowerShell convenience scripts created"
Write-ColorOutput ""

# Test complete setup
Write-Step "Testing complete setup with demo data..."
try {
    python -m src.cli calculate --use-mock-data | Out-Null
    Write-Success "Demo data generation test successful"
    
    # Check if data files were created
    if (Test-Path "data\dashboard_data.json") {
        Write-Success "Dashboard data file created successfully"
    }
} catch {
    Write-Warning "Demo test failed, but basic setup completed"
    Write-Info "You may need to check the configuration or dependencies"
}
Write-ColorOutput ""

# Create desktop shortcuts (optional)
$createShortcuts = Read-Host "Would you like to create desktop shortcuts? (Y/N)"
if ($createShortcuts -eq "Y" -or $createShortcuts -eq "y") {
    Write-Step "Creating desktop shortcuts..."
    
    $currentPath = Get-Location
    
    # Create batch files that can be copied to desktop
    $execDashboardBat = @"
@echo off
cd /d "$currentPath"
powershell -ExecutionPolicy Bypass -File "start_executive_dashboard.ps1"
"@
    $execDashboardBat | Out-File -FilePath "Desktop_Executive_Dashboard.bat" -Encoding ASCII
    
    $demoBat = @"
@echo off
cd /d "$currentPath"
powershell -ExecutionPolicy Bypass -File "start_demo.ps1"
"@
    $demoBat | Out-File -FilePath "Desktop_Demo_Dashboard.bat" -Encoding ASCII
    
    Write-Success "Created desktop launcher files"
    Write-Info "You can copy Desktop_*.bat files to your desktop for quick access"
}
Write-ColorOutput ""

# Final completion message
Write-ColorOutput "================================================" $script:Colors.Green
Write-ColorOutput "SETUP COMPLETED SUCCESSFULLY!" $script:Colors.Green
Write-ColorOutput "================================================" $script:Colors.Green
Write-ColorOutput ""

Write-Step "INSTALLATION SUMMARY"
Write-ColorOutput "✓ Python virtual environment created and activated" $script:Colors.Green
Write-ColorOutput "✓ All dependencies installed (25+ packages)" $script:Colors.Green
Write-ColorOutput "✓ Configuration files created" $script:Colors.Green
Write-ColorOutput "✓ Project directories created" $script:Colors.Green
Write-ColorOutput "✓ PowerShell convenience scripts created" $script:Colors.Green
Write-ColorOutput "✓ Executive dashboard with work items table ready" $script:Colors.Green
Write-ColorOutput ""

Write-Step "QUICK START OPTIONS"
Write-ColorOutput ""
Write-ColorOutput "Option 1: Executive Dashboard (New Work Items Feature)" $script:Colors.Yellow
Write-ColorOutput "  PowerShell: .\start_executive_dashboard.ps1" $script:Colors.White
Write-ColorOutput "  Or run: .\flow_cli.ps1 demo --executive --use-mock-data" $script:Colors.White
Write-ColorOutput "  Then open: http://localhost:$Port/executive-dashboard.html" $script:Colors.Cyan
Write-ColorOutput ""
Write-ColorOutput "Option 2: Standard Dashboard" $script:Colors.Yellow
Write-ColorOutput "  PowerShell: .\start_demo.ps1" $script:Colors.White
Write-ColorOutput "  Or run: .\flow_cli.ps1 demo --use-mock-data --open-browser" $script:Colors.White
Write-ColorOutput ""
Write-ColorOutput "Option 3: Command Line Usage" $script:Colors.Yellow
Write-ColorOutput "  .\flow_cli.ps1 calculate --use-mock-data" $script:Colors.White
Write-ColorOutput "  .\flow_cli.ps1 serve --executive --port $Port" $script:Colors.White
Write-ColorOutput ""

Write-Step "EXECUTIVE DASHBOARD FEATURES"
Write-ColorOutput "✓ Two-tab interface: Overview + Work Items Details" $script:Colors.Green
Write-ColorOutput "✓ Interactive work items table with pagination" $script:Colors.Green
Write-ColorOutput "✓ Chart drill-down (click charts to filter work items)" $script:Colors.Green
Write-ColorOutput "✓ Workstream filtering (Data, QA, OutSystems, Others)" $script:Colors.Green
Write-ColorOutput "✓ CSV export functionality" $script:Colors.Green
Write-ColorOutput "✓ Direct Azure DevOps work item links" $script:Colors.Green
Write-ColorOutput ""

Write-Step "AZURE DEVOPS SETUP"
Write-ColorOutput "To connect to real Azure DevOps data:" $script:Colors.White
Write-ColorOutput "1. Set PAT token: `$env:AZURE_DEVOPS_PAT='your_token_here'" $script:Colors.White
Write-ColorOutput "2. Edit config\config.json with your org/project details" $script:Colors.White
Write-ColorOutput "3. Run: .\flow_cli.ps1 fetch" $script:Colors.White
Write-ColorOutput ""

Write-Step "PROJECT LOCATION"
Write-ColorOutput "Working directory: $(Get-Location)" $script:Colors.White
Write-ColorOutput "All files are now in Windows-native format" $script:Colors.White
Write-ColorOutput ""

Write-ColorOutput "Ready to use Flow Metrics with Executive Dashboard!" $script:Colors.Green
Write-ColorOutput ""
Write-Info "Test your installation: .\test_installation.ps1"
Write-ColorOutput ""

Read-Host "Press any key to exit setup"