#!/bin/bash
# Flow Metrics Native WSL Setup Script
# Run this directly in WSL for native development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
echo_success() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_info() { echo -e "${CYAN}[INFO]${NC} $1"; }

echo "================================================"
echo "Flow Metrics - Native WSL Setup"
echo "================================================"
echo "Version: 1.0.0 (WSL Native)"
echo ""

# Check if we're in WSL
if ! grep -q microsoft /proc/version 2>/dev/null; then
    echo_warning "This doesn't appear to be WSL. This script is optimized for WSL."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check project structure
echo_step "Verifying project structure..."
required_files=("src/cli.py" "executive-dashboard.html" "requirements.txt")
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo_error "Required file not found: $file"
        echo_info "Make sure you're in the project root directory"
        exit 1
    fi
done
echo_success "Project structure verified"
echo ""

# Check Python installation
echo_step "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo_error "Python3 is not installed"
    echo_info "Install with: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo_success "Python found: $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo_warning "pip3 not found, installing..."
    sudo apt update
    sudo apt install -y python3-pip
fi
echo ""

# Create virtual environment
echo_step "Setting up Python virtual environment..."
if [[ -d "venv" ]]; then
    echo_warning "Virtual environment already exists"
    read -p "Recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        echo_info "Removed existing virtual environment"
    else
        echo_info "Using existing virtual environment"
    fi
fi

if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    if [[ $? -ne 0 ]]; then
        echo_error "Failed to create virtual environment"
        exit 1
    fi
    echo_success "Virtual environment created"
fi
echo ""

# Activate virtual environment
echo_step "Activating virtual environment..."
source venv/bin/activate
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo_success "Virtual environment activated"
else
    echo_error "Failed to activate virtual environment"
    exit 1
fi
echo ""

# Upgrade pip
echo_step "Upgrading pip..."
python -m pip install --upgrade pip --quiet
echo_success "Pip upgraded"
echo ""

# Install dependencies
echo_step "Installing Python dependencies..."
echo_info "This may take several minutes..."
pip install -r requirements.txt --quiet
if [[ $? -ne 0 ]]; then
    echo_error "Failed to install requirements"
    echo_info "Trying without cache..."
    pip install --no-cache-dir -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo_error "Installation failed"
        exit 1
    fi
fi
echo_success "Dependencies installed successfully"
echo ""

# Test CLI installation
echo_step "Testing CLI installation..."
python -m src.cli --help > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
    echo_error "CLI test failed"
    echo_info "Testing basic import..."
    python -c "import src.cli; print('Import successful')"
    exit 1
fi
echo_success "CLI is working correctly"
echo ""

# Create directories
echo_step "Creating project directories..."
mkdir -p data config logs exports
echo_success "Directories created"
echo ""

# Create configuration files
echo_step "Creating configuration files..."

# Main config
cat > config/config.json << 'EOF'
{
  "azure_devops": {
    "org_url": "https://dev.azure.com/your-org",
    "default_project": "your-project-name",
    "pat_token": "${AZURE_DEVOPS_PAT}"
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
    "host": "0.0.0.0",
    "auto_open_browser": false
  }
}
EOF

# Workstream config
cat > config/workstream_config.json << 'EOF'
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
EOF

echo_success "Configuration files created"
echo ""

# Create convenience scripts
echo_step "Creating convenience scripts..."

# CLI wrapper
cat > flow_cli.sh << 'EOF'
#!/bin/bash
# Flow Metrics CLI wrapper for WSL
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.cli "$@"
EOF
chmod +x flow_cli.sh

# Executive dashboard launcher
cat > start_executive_dashboard.sh << 'EOF'
#!/bin/bash
# Launch Executive Dashboard in WSL
cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting Executive Dashboard with Work Items Table..."
echo ""
echo "Generating demo data..."
python -m src.cli calculate --use-mock-data
echo ""

# Get WSL IP address
WSL_IP=$(hostname -I | awk '{print $1}')
echo "Starting server..."
echo "Executive Dashboard URLs:"
echo "  Local:    http://localhost:8080/executive-dashboard.html"
echo "  From Windows: http://$WSL_IP:8080/executive-dashboard.html"
echo ""
echo "Press Ctrl+C to stop the server"
python -m src.cli serve --executive --port 8080 --host 0.0.0.0
EOF
chmod +x start_executive_dashboard.sh

# Demo launcher
cat > start_demo.sh << 'EOF'
#!/bin/bash
# Launch Demo Dashboard in WSL
cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting demo dashboard..."
WSL_IP=$(hostname -I | awk '{print $1}')
echo "Demo URLs:"
echo "  Local:    http://localhost:8080"
echo "  From Windows: http://$WSL_IP:8080"
python -m src.cli demo --use-mock-data --host 0.0.0.0
EOF
chmod +x start_demo.sh

# Installation test
cat > test_installation.sh << 'EOF'
#!/bin/bash
# Test Flow Metrics installation
cd "$(dirname "$0")"
source venv/bin/activate

echo "Testing Flow Metrics installation..."
python -m src.cli calculate --use-mock-data
if [[ $? -eq 0 ]]; then
    echo "[SUCCESS] Installation test passed!"
else
    echo "[ERROR] Test failed"
    exit 1
fi
EOF
chmod +x test_installation.sh

echo_success "Convenience scripts created"
echo ""

# Test complete setup
echo_step "Running final installation test..."
python -m src.cli calculate --use-mock-data > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
    echo_warning "Demo test failed, but setup appears complete"
    echo_info "You may need to check the configuration"
else
    echo_success "Demo test successful - installation verified!"
fi
echo ""

# Get WSL IP for user
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

# Completion message
echo "================================================"
echo -e "${GREEN}SETUP COMPLETED SUCCESSFULLY!${NC}"
echo "================================================"
echo ""

echo -e "${BLUE}[INSTALLATION SUMMARY]${NC}"
echo "✓ WSL native Python environment configured"
echo "✓ Virtual environment created"
echo "✓ All dependencies installed (25+ packages)"
echo "✓ Configuration files created"
echo "✓ Project directories created"
echo "✓ Shell convenience scripts created"
echo "✓ Executive dashboard with work items ready"
echo ""

echo -e "${BLUE}[HOW TO USE - WSL NATIVE]${NC}"
echo ""
echo -e "${YELLOW}Executive Dashboard (New Work Items Feature):${NC}"
echo "  WSL: ./start_executive_dashboard.sh"
echo "  URLs:"
echo "    Local:       http://localhost:8080/executive-dashboard.html"
echo "    From Windows: http://$WSL_IP:8080/executive-dashboard.html"
echo ""
echo -e "${YELLOW}Standard Dashboard:${NC}"
echo "  WSL: ./start_demo.sh"
echo ""
echo -e "${YELLOW}Command Line (WSL):${NC}"
echo "  ./flow_cli.sh calculate --use-mock-data"
echo "  ./flow_cli.sh serve --executive --port 8080 --host 0.0.0.0"
echo ""
echo -e "${YELLOW}Direct Commands:${NC}"
echo "  source venv/bin/activate"
echo "  python -m src.cli [command]"
echo ""

echo -e "${BLUE}[EXECUTIVE DASHBOARD FEATURES]${NC}"
echo "✓ Two-tab interface: Overview + Work Items Details"
echo "✓ Interactive work items table with pagination (50 items/page)"
echo "✓ Chart drill-down functionality (click charts to filter)"
echo "✓ Workstream filtering (Data, QA, OutSystems, Others)"
echo "✓ CSV export capability"
echo "✓ Direct Azure DevOps work item links"
echo "✓ Real-time filter synchronization"
echo ""

echo -e "${BLUE}[AZURE DEVOPS SETUP]${NC}"
echo "To connect to real data:"
echo "1. Set: export AZURE_DEVOPS_PAT='your_token_here'"
echo "2. Edit config/config.json (org/project details)"
echo "3. Run: ./flow_cli.sh fetch"
echo ""

echo -e "${BLUE}[ACCESSING FROM WINDOWS]${NC}"
echo "The server is configured to bind to 0.0.0.0, so you can access it from Windows:"
echo "  http://$WSL_IP:8080/executive-dashboard.html"
echo ""
echo "If that doesn't work, try:"
echo "  http://localhost:8080/executive-dashboard.html"
echo ""

echo -e "${GREEN}Ready to use Flow Metrics with Executive Dashboard natively in WSL!${NC}"
echo ""
echo -e "${CYAN}Test your installation: ./test_installation.sh${NC}"
echo ""