#!/bin/bash

# Test Automation Runner Script for ADO Flow Metrics
# This script runs comprehensive tests in the proper environment

set -e  # Exit on any error

echo "🚀 Starting ADO Flow Metrics Test Automation"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    print_error "Not in the correct directory. Please run from the project root."
    exit 1
fi

# Set up environment variables
export PYTHONPATH="$(pwd)/src"
export ADO_FLOW_METRICS_ENV="test"
export AZURE_DEVOPS_ORG="test-org"
export AZURE_DEVOPS_PROJECT="test-project"
export AZURE_DEVOPS_PAT="test-token"
export AZURE_DEVOPS_BASE_URL="http://localhost:8080"

print_status "Environment variables set for testing"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.8+"
    exit 1
fi

print_status "Using Python: $PYTHON_CMD"

# Check if we're in a virtual environment (recommended)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Running in virtual environment: $VIRTUAL_ENV"
else
    print_warning "Not running in a virtual environment. Consider using 'python -m venv venv && source venv/bin/activate'"
fi

# Install test dependencies if needed
print_status "Checking test dependencies..."
$PYTHON_CMD -c "import pytest" 2>/dev/null || {
    print_status "Installing pytest..."
    $PYTHON_CMD -m pip install pytest pytest-cov pytest-mock pytest-asyncio
}

# Function to run tests with error handling
run_test_suite() {
    local test_name="$1"
    local test_path="$2"
    local test_args="${3:-}"
    
    print_status "Running $test_name..."
    
    if $PYTHON_CMD -m pytest "$test_path" $test_args; then
        print_success "$test_name passed!"
        return 0
    else
        print_error "$test_name failed!"
        return 1
    fi
}

# Create test results directory
mkdir -p test-results

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# 1. Run unit tests for Azure DevOps client
if run_test_suite "Azure DevOps Client Tests" "tests/test_azure_devops_client.py" "-v --tb=short"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 2. Run WIQL parser tests
if run_test_suite "WIQL Parser Tests" "tests/test_wiql_parser.py" "-v --tb=short"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 3. Run calculator tests if the file exists
if [ -f "tests/test_calculator.py" ]; then
    if run_test_suite "Flow Metrics Calculator Tests" "tests/test_calculator.py" "-v --tb=short"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
fi

# 4. Run comprehensive calculator tests
if [ -f "tests/test_metrics_calculator_comprehensive.py" ]; then
    if run_test_suite "Comprehensive Calculator Tests" "tests/test_metrics_calculator_comprehensive.py" "-v --tb=short"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
fi

# 5. Run integration tests if they exist
if [ -d "tests/integration" ]; then
    if run_test_suite "Integration Tests" "tests/integration/" "-v --tb=short"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
fi

# 6. Run all unit tests with coverage
print_status "Running comprehensive test suite with coverage..."
if $PYTHON_CMD -m pytest tests/ \
    -m "not (e2e or performance)" \
    --cov=src \
    --cov-report=html:test-results/coverage_html \
    --cov-report=xml:test-results/coverage.xml \
    --cov-report=term \
    --junit-xml=test-results/test-results.xml \
    -v; then
    print_success "Comprehensive test suite passed!"
    ((TESTS_PASSED++))
else
    print_error "Comprehensive test suite failed!"
    ((TESTS_FAILED++))
fi

# Test Docker environment if Docker is available
if command -v docker &> /dev/null; then
    print_status "Testing Docker environment..."
    
    # Build the test image
    if docker build -f tests/Dockerfile -t ado-flow-test . >/dev/null 2>&1; then
        print_success "Docker test image built successfully"
        
        # Run a simple test in Docker
        if docker run --rm -e PYTHONPATH=/app/src ado-flow-test python -c "import src.azure_devops_client; print('Import test successful')"; then
            print_success "Docker environment test passed"
            ((TESTS_PASSED++))
        else
            print_error "Docker environment test failed"
            ((TESTS_FAILED++))
        fi
    else
        print_warning "Docker test image build failed - skipping Docker tests"
    fi
else
    print_warning "Docker not available - skipping Docker tests"
fi

# Check if mock server dependencies are available
if command -v npm &> /dev/null && [ -f "tests/mock-server/package.json" ]; then
    print_status "Testing mock server setup..."
    
    cd tests/mock-server
    if npm install >/dev/null 2>&1; then
        print_success "Mock server dependencies installed"
        
        # Start mock server in background for testing
        npm start &
        MOCK_SERVER_PID=$!
        sleep 3
        
        # Test if mock server is responding
        if curl -f http://localhost:8080/health >/dev/null 2>&1; then
            print_success "Mock server is running correctly"
            ((TESTS_PASSED++))
        else
            print_error "Mock server failed to start"
            ((TESTS_FAILED++))
        fi
        
        # Clean up mock server
        kill $MOCK_SERVER_PID 2>/dev/null || true
    else
        print_warning "Failed to install mock server dependencies"
    fi
    
    cd - >/dev/null
else
    print_warning "npm not available or mock server not configured - skipping mock server tests"
fi

# Print summary
echo ""
echo "=============================================="
echo "🎯 Test Automation Summary"
echo "=============================================="
print_success "Tests Passed: $TESTS_PASSED"
if [ $TESTS_FAILED -gt 0 ]; then
    print_error "Tests Failed: $TESTS_FAILED"
else
    print_success "Tests Failed: $TESTS_FAILED"
fi

echo ""
print_status "Test Results Location:"
echo "  - Coverage HTML Report: test-results/coverage_html/index.html"
echo "  - Coverage XML Report: test-results/coverage.xml"
echo "  - JUnit XML Report: test-results/test-results.xml"

echo ""
if [ $TESTS_FAILED -eq 0 ]; then
    print_success "🎉 All tests passed! Ready for deployment."
    echo ""
    echo "Next Steps:"
    echo "  1. Review coverage report: open test-results/coverage_html/index.html"
    echo "  2. Commit changes: git add . && git commit -m 'Add comprehensive test automation'"
    echo "  3. Push to trigger CI/CD: git push origin fix/ado-flow"
    exit 0
else
    print_error "❌ Some tests failed. Please review and fix issues before proceeding."
    echo ""
    echo "Debugging Steps:"
    echo "  1. Check individual test outputs above"
    echo "  2. Review test-results/test-results.xml for detailed failure info"
    echo "  3. Run specific failing tests with: python -m pytest <test_file> -v -s"
    exit 1
fi