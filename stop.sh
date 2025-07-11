#!/bin/bash

# Finance Knowledge Graph - Stop Application Script
# This script provides a convenient way to stop all running services

set -e

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

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if psutil is available
if ! python3 -c "import psutil" 2>/dev/null; then
    print_warning "psutil not found. Installing..."
    pip3 install psutil
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

print_status "Stopping Finance Knowledge Graph application..."

# Run the Python stop script with all arguments passed to this script
python3 stop_app.py "$@"

# Check the exit code
if [ $? -eq 0 ]; then
    print_success "Application stopped successfully!"
else
    print_error "Failed to stop application"
    exit 1
fi 