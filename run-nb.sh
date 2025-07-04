#!/bin/bash

# Hyland Hockey Jersey Order Management System
# Run script with mode selection

echo "Hyland Hockey Jersey Order Management System"
echo "============================================="
echo ""
echo "Usage options:"
echo "  ./run-nb.sh --test        # Run in TEST mode (default)"
echo "  ./run-nb.sh --production  # Run in PRODUCTION mode"
echo "  ./run-nb.sh               # Run in TEST mode (default for safety)"
echo ""
echo "Mode differences:"
echo "  TEST MODE:     Uses credentials_test.json and token_test.pickle"
echo "  PRODUCTION:    Uses credentials.json and token.pickle"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
echo "Installing/upgrading requirements..."
pip install -r requirements.txt 2>&1 | grep -v "Requirement already satisfied:"

# Run the application with provided arguments
echo "Starting application..."
python main.py "$@"