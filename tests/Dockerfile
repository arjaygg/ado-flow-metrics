# Dockerfile for running E2E UI tests with Playwright
FROM mcr.microsoft.com/playwright/python:v1.53.0-focal

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional test dependencies
RUN pip install --no-cache-dir \
    pytest-playwright \
    pytest-html \
    pytest-xdist \
    pytest-cov \
    selenium \
    playwright

# Install playwright browsers
RUN python -m playwright install --with-deps

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Create test results directory
RUN mkdir -p /app/test-results

# Default command runs E2E tests
CMD ["python", "-m", "pytest", "tests/e2e/", "-v", "--html=test-results/report.html", "--self-contained-html"]
