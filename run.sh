#!/bin/bash

# Function to print error messages
print_error() {
    echo -e "\e[31mError: $1\e[0m" >&2
    logger -t "voice-to-text" "ERROR: $1"
}

# Function to print success messages
print_success() {
    echo -e "\e[32m$1\e[0m"
    logger -t "voice-to-text" "INFO: $1"
}

# Function to print info messages
print_info() {
    echo -e "\e[34m$1\e[0m"
    logger -t "voice-to-text" "INFO: $1"
}

# Function to print debug information
print_debug() {
    echo -e "\e[35mDebug: $1\e[0m" >&2
    logger -t "voice-to-text" "DEBUG: $1"
}

# Print debug information about the environment
print_debug "Current user: $(whoami)"
print_debug "Current directory: $(pwd)"
print_debug "Display: $DISPLAY"
print_debug "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
print_debug "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
print_info "Application directory: $SCRIPT_DIR"

# Change to the application directory
cd "$SCRIPT_DIR" || {
    print_error "Failed to change to application directory: $SCRIPT_DIR"
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

# Export environment variables
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

# Print audio device information
print_debug "Audio devices:"
aplay -l || true
print_debug "PulseAudio status:"
pactl info || true
print_debug "ALSA devices:"
amixer -D pulse sget Master || true

# Ensure proper permissions for audio
if ! groups | grep -qE '(audio|pulse|pulse-access)'; then
    print_error "User does not have proper audio group permissions"
    print_info "Please run: sudo usermod -aG audio,pulse-access $USER"
    print_info "Then log out and log back in"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Run the application with proper error handling
print_info "Starting Voice-to-Text application..."

# Create a timestamp for the log file
LOG_FILE="voice_to_text_$(date +%Y%m%d_%H%M%S).log"

# Run with full output capture
{
    print_debug "Python version: $(python3 --version)"
    print_debug "Pip packages:"
    pip list
    
    python3 run.py
} 2>&1 | tee -a "$LOG_FILE"

# Store the exit code
exit_code=$?

# Check for specific error conditions
if [ $exit_code -ne 0 ]; then
    print_error "Application exited with error code: $exit_code"
    print_info "Check $LOG_FILE for details"
fi

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

# Exit with the application's exit code
exit $exit_code
