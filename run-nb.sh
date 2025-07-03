#!/bin/bash

# Hyland Hockey Jersey Order Management System Launcher
# Enhanced shell script launcher with error handling and dependency checking

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

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "Virtual environment 'venv' not found!"
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created successfully"
    fi
}

# Function to check if requirements are installed
check_dependencies() {
    if [ ! -f "venv/bin/pip" ]; then
        print_error "pip not found in virtual environment!"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Check if main dependencies are installed
    if ! venv/bin/python -c "import ttkbootstrap, google.auth, pandas" 2>/dev/null; then
        print_warning "Some dependencies may not be installed"
        print_status "Installing dependencies from requirements.txt..."
        venv/bin/pip install -r requirements.txt
        print_success "Dependencies installed successfully"
    fi
}

# Function to check if main.py exists
check_main_file() {
    if [ ! -f "main.py" ]; then
        print_error "main.py not found in current directory!"
        exit 1
    fi
}

# Main execution
main() {
    print_status "Starting Hyland Hockey Jersey Order Management System..."
    
    # Check prerequisites
    check_main_file
    check_venv
    check_dependencies
    
    # Activate virtual environment and run the application
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Launching GUI application..."
    python3 main.py
}

# Handle script interruption
trap 'print_warning "Application interrupted by user"; exit 0' INT TERM

# Run main function
main