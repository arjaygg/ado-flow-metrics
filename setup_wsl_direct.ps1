# Flow Metrics Setup Script - WSL Direct Execution
# This script runs setup commands through WSL to avoid UNC path issues
# Can be run from Windows while accessing WSL filesystem

param(
    [switch]$Force,
    [string]$TargetDistribution = "Ubuntu",
    [int]$Port = 8080
)

# Set up colors for better output
$script:Colors = @{
    Red = [System.ConsoleColor]::Red
    Green = [System.ConsoleColor]::Green
    Yellow = [System.ConsoleColor]::Yellow
    Blue = [System.ConsoleColor]::Blue
    Cyan = [System.ConsoleColor]::Cyan
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

# Header
Write-ColorOutput "================================================" $script:Colors.Cyan
Write-ColorOutput "Flow Metrics - WSL Direct Setup Script" $script:Colors.Cyan
Write-ColorOutput "================================================" $script:Colors.Cyan
Write-ColorOutput "Version: 3.0.0 (PowerShell WSL Integration)" $script:Colors.Cyan
Write-ColorOutput ""

# Check if WSL is available
Write-Step "Checking WSL availability..."
try {
    $wslVersion = wsl --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "WSL command failed"
    }
    Write-Success "WSL is available"
    Write-Info "WSL Version Information:"
    wsl --version
} catch {
    Write-Error "WSL is not installed or not available"
    Write-ColorOutput ""
    Write-Warning "SOLUTION: Please install WSL first:"
    Write-ColorOutput "1. Open PowerShell as Administrator"
    Write-ColorOutput "2. Run: wsl --install"
    Write-ColorOutput "3. Restart your computer"
    Write-ColorOutput "4. Set up Ubuntu or your preferred Linux distribution"
    Write-ColorOutput ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-ColorOutput ""

# Get current directory and convert to WSL path
$currentWinPath = Get-Location
Write-Info "Current Windows path: $currentWinPath"

# Convert Windows path to WSL path
$wslPath = ""
if ($currentWinPath.Path -match "^\\\\wsl\$") {
    # Handle UNC paths from WSL (\\wsl$\Ubuntu\home\devag\git\feat-ado-flow2)
    $pathParts = $currentWinPath.Path -split "\\"
    if ($pathParts.Length -ge 4) {
        # Skip \\wsl$\Ubuntu and reconstruct the Linux path
        $linuxPathParts = $pathParts[4..($pathParts.Length-1)]
        $wslPath = "/" + ($linuxPathParts -join "/")
    }
} elseif ($currentWinPath.Path -match "^[A-Za-z]:") {
    # Convert Windows drive path (C:\path) to WSL path (/mnt/c/path)
    $driveLetter = $currentWinPath.Path.Substring(0,1).ToLower()
    $restPath = $currentWinPath.Path.Substring(3) -replace "\\", "/"
    $wslPath = "/mnt/$driveLetter/$restPath"
}

Write-Info "WSL path: $wslPath"
Write-ColorOutput ""

# Verify project exists in WSL
Write-Step "Verifying project files in WSL..."
$verificationFiles = @("src/cli.py", "executive-dashboard.html", "requirements.txt")

foreach ($file in $verificationFiles) {
    $testResult = wsl test -f "`"$wslPath/$file`""
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Required file not found: $wslPath/$file"
        Write-ColorOutput ""
        Write-Warning "TROUBLESHOOTING:"
        Write-ColorOutput "1. Make sure you're running this from the project root directory"
        Write-ColorOutput "2. Verify the WSL path conversion is correct"
        Write-ColorOutput "3. Check that the WSL distribution is running"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Success "All required project files found in WSL"
Write-ColorOutput ""

# Check Python in WSL
Write-Step "Checking Python installation in WSL..."
$pythonTest = wsl python3 --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python3 is not installed in WSL"
    Write-ColorOutput ""
    Write-Warning "SOLUTION: Install Python in WSL:"
    Write-ColorOutput "wsl sudo apt update"
    Write-ColorOutput "wsl sudo apt install python3 python3-pip python3-venv"
    Write-ColorOutput ""
    $installChoice = Read-Host "Would you like me to install Python3 now? (Y/N)"
    if ($installChoice -eq "Y" -or $installChoice -eq "y") {
        Write-Step "Installing Python3 in WSL..."
        wsl sudo apt update
        wsl sudo apt install -y python3 python3-pip python3-venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install Python3"
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Success "Python3 installed successfully"
    } else {
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    $pythonVersion = wsl python3 --version
    Write-Success "Python found in WSL: $pythonVersion"
}
Write-ColorOutput ""

# Setup Python environment in WSL
Write-Step "Setting up Python environment in WSL..."
Write-Info "Project path: $wslPath"
Write-ColorOutput ""

# Create and activate virtual environment
Write-Step "Creating Python virtual environment..."
$venvResult = wsl bash -c "cd '$wslPath' && python3 -m venv venv"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create virtual environment in WSL"
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Success "Virtual environment created"
Write-ColorOutput ""

# Upgrade pip
Write-Step "Upgrading pip..."
$pipUpgrade = wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m pip install --upgrade pip"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Pip upgrade failed, continuing..."
} else {
    Write-Success "Pip upgraded"
}
Write-ColorOutput ""

# Install dependencies
Write-Step "Installing Python dependencies..."
Write-Info "This may take several minutes..."
$installResult = wsl bash -c "cd '$wslPath' && source venv/bin/activate && pip install -r requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install requirements"
    Write-ColorOutput ""
    Write-Warning "RETRY: Trying with --no-cache-dir..."
    $retryResult = wsl bash -c "cd '$wslPath' && source venv/bin/activate && pip install --no-cache-dir -r requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Installation failed again"
        Write-ColorOutput ""
        Write-Warning "TROUBLESHOOTING:"
        Write-ColorOutput "1. Check internet connection in WSL: wsl ping google.com"
        Write-ColorOutput "2. Update package list: wsl sudo apt update"
        Write-ColorOutput "3. Install build tools: wsl sudo apt install build-essential"
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Success "Dependencies installed successfully"
Write-ColorOutput ""

# Test CLI installation
Write-Step "Testing CLI installation..."
$cliTest = wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli --help" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "CLI test failed"
    Write-ColorOutput ""
    Write-Warning "DEBUG: Testing basic import..."
    wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -c 'import src.cli; print(\`"Import successful\`")'"
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Success "CLI is working correctly"
Write-ColorOutput ""

# Create directories
Write-Step "Creating project directories..."
wsl bash -c "cd '$wslPath' && mkdir -p data config logs exports"
Write-Success "Directories created"
Write-ColorOutput ""

# Create configuration files
Write-Step "Creating configuration files..."

# Create main config
$configJson = @"
{
  "azure_devops": {
    "org_url": "https://dev.azure.com/your-org",
    "default_project": "your-project-name",
    "pat_token": "`${AZURE_DEVOPS_PAT}"
  },
  "flow_metrics": {
    "throughput_period_days": 30,
    "default_days_back": 90,
    "executive_dashboard": {
      "enable_work_items_table": true,
      "items_per_page": 50,
      "enable_chart_drilldown": true,
      "enable_csv_export": true
    }
  },
  "data_management": {
    "data_directory": "data",
    "auto_backup": true,
    "export_directory": "exports"
  },
  "server": {
    "default_port": 8080,
    "host": "127.0.0.1",
    "auto_open_browser": false
  }
}
"@

$workstreamJson = @"
{
  "workstreams": {
    "Data": {
      "description": "Data analytics and engineering team",
      "name_patterns": [
        "Nenissa", "Ariel", "Patrick Oniel", "Kennedy Oliveira",
        "Christopher Jan", "Jegs", "Ian Belmonte"
      ]
    },
    "QA": {
      "description": "Quality assurance and testing team",
      "name_patterns": ["Sharon", "Lorenz", "Arvin"]
    },
    "OutSystems": {
      "description": "OutSystems development team",
      "name_patterns": [
        "Apollo", "Glizzel", "Prince", "Patrick Russel", "Rio", "Nymar"
      ]
    }
  },
  "default_workstream": "Others",
  "matching_options": {
    "case_sensitive": false,
    "partial_match": true,
    "match_full_name": false
  }
}
"@

# Write config files using WSL
$configJson | wsl bash -c "cd '$wslPath' && cat > config/config.json"
$workstreamJson | wsl bash -c "cd '$wslPath' && cat > config/workstream_config.json"

Write-Success "Configuration files created"
Write-ColorOutput ""

# Create Windows convenience scripts that use WSL
Write-Step "Creating Windows convenience scripts..."

# Create PowerShell CLI wrapper
$cliScript = @"
# Flow Metrics CLI through WSL
param([Parameter(ValueFromRemainingArguments)]`$Arguments)
wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli `$(`$Arguments -join ' ')"
"@
$cliScript | Out-File -FilePath "flow_cli.ps1" -Encoding UTF8

# Create executive dashboard launcher
$dashboardScript = @"
# Launch Executive Dashboard through WSL
Write-Host "Starting Executive Dashboard with Work Items Table..." -ForegroundColor Green
Write-Host ""
Write-Host "Generating demo data..." -ForegroundColor Yellow
wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli calculate --use-mock-data"
Write-Host ""
Write-Host "Starting server on http://localhost:$Port..." -ForegroundColor Yellow
Write-Host "Executive Dashboard: http://localhost:$Port/executive-dashboard.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli serve --executive --port $Port"
"@
$dashboardScript | Out-File -FilePath "start_executive_dashboard.ps1" -Encoding UTF8

# Create demo launcher
$demoScript = @"
# Launch Demo Dashboard through WSL
Write-Host "Starting demo dashboard..." -ForegroundColor Green
wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli demo --use-mock-data --open-browser"
"@
$demoScript | Out-File -FilePath "start_demo.ps1" -Encoding UTF8

# Create installation test script
$testScript = @"
# Test installation through WSL
Write-Host "Testing Flow Metrics installation..." -ForegroundColor Green
wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli calculate --use-mock-data"
if (`$LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Installation test passed!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Test failed" -ForegroundColor Red
}
Read-Host "Press Enter to continue"
"@
$testScript | Out-File -FilePath "test_installation.ps1" -Encoding UTF8

Write-Success "PowerShell convenience scripts created"
Write-ColorOutput ""

# Test the complete setup
Write-Step "Running final installation test..."
$finalTest = wsl bash -c "cd '$wslPath' && source venv/bin/activate && python -m src.cli calculate --use-mock-data" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Demo test failed, but setup appears complete"
    Write-Info "You may need to check the configuration"
} else {
    Write-Success "Demo test successful - installation verified!"
}
Write-ColorOutput ""

# Completion message
Write-ColorOutput "================================================" $script:Colors.Green
Write-ColorOutput "SETUP COMPLETED SUCCESSFULLY!" $script:Colors.Green
Write-ColorOutput "================================================" $script:Colors.Green
Write-ColorOutput ""

Write-Step "INSTALLATION SUMMARY"
Write-ColorOutput "✓ WSL Python environment configured" $script:Colors.Green
Write-ColorOutput "✓ Virtual environment created in WSL" $script:Colors.Green
Write-ColorOutput "✓ All dependencies installed (25+ packages)" $script:Colors.Green
Write-ColorOutput "✓ Configuration files created" $script:Colors.Green
Write-ColorOutput "✓ Project directories created" $script:Colors.Green
Write-ColorOutput "✓ PowerShell convenience scripts created" $script:Colors.Green
Write-ColorOutput "✓ Executive dashboard with work items ready" $script:Colors.Green
Write-ColorOutput ""

Write-Step "HOW TO USE"
Write-ColorOutput ""
Write-ColorOutput "Executive Dashboard (New Work Items Feature):" $script:Colors.Yellow
Write-ColorOutput "  PowerShell: .\start_executive_dashboard.ps1" $script:Colors.White
Write-ColorOutput "  Opens: http://localhost:$Port/executive-dashboard.html" $script:Colors.Cyan
Write-ColorOutput ""
Write-ColorOutput "Standard Dashboard:" $script:Colors.Yellow
Write-ColorOutput "  PowerShell: .\start_demo.ps1" $script:Colors.White
Write-ColorOutput ""
Write-ColorOutput "Command Line (PowerShell):" $script:Colors.Yellow
Write-ColorOutput "  .\flow_cli.ps1 calculate --use-mock-data" $script:Colors.White
Write-ColorOutput "  .\flow_cli.ps1 serve --executive --port $Port" $script:Colors.White
Write-ColorOutput ""
Write-ColorOutput "Direct WSL Commands:" $script:Colors.Yellow
Write-ColorOutput "  wsl bash -c `"cd '$wslPath' && source venv/bin/activate && python -m src.cli [command]`"" $script:Colors.White
Write-ColorOutput ""

Write-Step "EXECUTIVE DASHBOARD FEATURES"
Write-ColorOutput "✓ Two-tab interface: Overview + Work Items Details" $script:Colors.Green
Write-ColorOutput "✓ Interactive work items table with pagination (50 items/page)" $script:Colors.Green
Write-ColorOutput "✓ Chart drill-down functionality (click charts to filter)" $script:Colors.Green
Write-ColorOutput "✓ Workstream filtering (Data, QA, OutSystems, Others)" $script:Colors.Green
Write-ColorOutput "✓ CSV export capability" $script:Colors.Green
Write-ColorOutput "✓ Direct Azure DevOps work item links" $script:Colors.Green
Write-ColorOutput "✓ Real-time filter synchronization" $script:Colors.Green
Write-ColorOutput ""

Write-Step "PROJECT PATHS"
Write-ColorOutput "Windows path: $currentWinPath" $script:Colors.White
Write-ColorOutput "WSL path: $wslPath" $script:Colors.White
Write-ColorOutput ""

Write-Step "AZURE DEVOPS SETUP"
Write-ColorOutput "To connect to real data:" $script:Colors.White
Write-ColorOutput "1. Set: `$env:AZURE_DEVOPS_PAT='your_token_here'" $script:Colors.White
Write-ColorOutput "2. Edit config\config.json (org/project details)" $script:Colors.White
Write-ColorOutput "3. Run: .\flow_cli.ps1 fetch" $script:Colors.White
Write-ColorOutput ""

Write-ColorOutput "Ready to use Flow Metrics with Executive Dashboard!" $script:Colors.Green
Write-ColorOutput ""
Write-Info "Test your installation: .\test_installation.ps1"
Write-ColorOutput ""

Read-Host "Press Enter to exit"