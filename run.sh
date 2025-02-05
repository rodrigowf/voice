#!/bin/bash

# Function to print error messages
print_error() {
    echo -e "\e[31mError: $1\e[0m"
}

# Function to print success messages
print_success() {
    echo -e "\e[32m$1\e[0m"
}

# Function to print info messages
print_info() {
    echo -e "\e[34m$1\e[0m"
}

# Change to the application directory
cd "$(dirname "$0")" || {
    print_error "Failed to change to application directory"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run install.sh first"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please create it with your OpenAI API key"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY" .env; then
    print_error "OPENAI_API_KEY not found in .env file"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Run the application
print_info "Starting Voice-to-Text application..."
python3 run.py

# Store the exit code
exit_code=$?

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Exit with the application's exit code
exit $exit_code
