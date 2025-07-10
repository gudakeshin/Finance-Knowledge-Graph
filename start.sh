#!/bin/bash

# Finance Knowledge Graph Application Startup Script
# This is a simple wrapper around the Python startup script

set -e  # Exit on any error

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

# Function to show usage
show_usage() {
    echo "Finance Knowledge Graph Application Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help                    Show this help message"
    echo "  --skip-deps              Skip starting dependencies (Neo4j, Redis)"
    echo "  --port-backend PORT      Backend port (default: 8000)"
    echo "  --port-frontend PORT     Frontend port (default: 5173)"
    echo "  --dev                    Development mode (skip deps, use default ports)"
    echo "  --prod                   Production mode (start all deps)"
    echo ""
    echo "Examples:"
    echo "  $0                       # Start all services with default settings"
    echo "  $0 --dev                 # Development mode (skip deps)"
    echo "  $0 --skip-deps           # Skip dependencies"
    echo "  $0 --port-backend 9000   # Use custom backend port"
    echo ""
}

# Parse command line arguments
SKIP_DEPS=false
BACKEND_PORT=8000
FRONTEND_PORT=5173
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_usage
            exit 0
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --port-backend)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --port-frontend)
            FRONTEND_PORT="$2"
            shift 2
            ;;
        --dev)
            DEV_MODE=true
            SKIP_DEPS=true
            shift
            ;;
        --prod)
            DEV_MODE=false
            SKIP_DEPS=false
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    print_error "Please install Python 3 and try again"
    exit 1
fi

# Check if Node.js is available (for frontend)
if ! command -v node &> /dev/null; then
    print_warning "Node.js is not installed or not in PATH"
    print_warning "Frontend may not start properly"
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_warning "npm is not installed or not in PATH"
    print_warning "Frontend may not start properly"
fi

# Check if the startup script exists
if [ ! -f "start_app.py" ]; then
    print_error "start_app.py not found in current directory"
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Make the Python script executable
chmod +x start_app.py

# Build the command
CMD="python3 start_app.py --port-backend $BACKEND_PORT --port-frontend $FRONTEND_PORT"

if [ "$SKIP_DEPS" = true ]; then
    CMD="$CMD --skip-deps"
fi

# Show startup information
print_status "Starting Finance Knowledge Graph Application..."
print_status "Backend port: $BACKEND_PORT"
print_status "Frontend port: $FRONTEND_PORT"

if [ "$SKIP_DEPS" = true ]; then
    print_warning "Dependencies (Neo4j, Redis) will be skipped"
    print_warning "Make sure they are running manually if needed"
else
    print_status "Dependencies will be started automatically"
fi

echo ""

# Execute the startup script
exec $CMD 