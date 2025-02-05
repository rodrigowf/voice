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

# Check if script is run with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script with sudo"
    exit 1
fi

# Store the real user who ran sudo
REAL_USER=${SUDO_USER:-$(whoami)}
USER_HOME=$(eval echo ~$REAL_USER)

print_info "Starting installation..."

# Update package list
print_info "Updating package list..."
apt-get update || {
    print_error "Failed to update package list"
    exit 1
}

# Install system dependencies
print_info "Installing system dependencies..."
apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    portaudio19-dev \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    pulseaudio \
    alsa-utils \
    gcc \
    pkg-config || {
    print_error "Failed to install system dependencies"
    exit 1
}

# Switch to the real user for Python operations
su - $REAL_USER << 'EOF'
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv || {
        print_error "Failed to create virtual environment"
        exit 1
    }
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip || {
    print_error "Failed to upgrade pip"
    exit 1
}

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt || {
    print_error "Failed to install Python dependencies"
    exit 1
}

# Patch pystray
print_info "Patching pystray..."
python3 pystray_patch.py || {
    print_error "Failed to patch pystray"
    exit 1
}

# Create icon
print_info "Creating application icon..."
python3 create_icon.py || {
    print_error "Failed to create icon"
    exit 1
}

# Make the virtual environment use system libraries for audio
if [ ! -f "venv/lib/python3.*/site-packages/usesystemlibs.pth" ]; then
    print_info "Configuring virtual environment to use system libraries..."
    echo "/usr/lib/python3/dist-packages" > venv/lib/python3.*/site-packages/usesystemlibs.pth
fi

# Deactivate virtual environment
deactivate
EOF

# Create ALSA config if it doesn't exist
if [ ! -f "$USER_HOME/.asoundrc" ]; then
    print_info "Creating ALSA config..."
    cat > "$USER_HOME/.asoundrc" << EOL
pcm.!default {
    type pulse
    fallback "sysdefault"
    hint {
        show on
        description "Default ALSA Output (currently PulseAudio Sound Server)"
    }
}

ctl.!default {
    type pulse
    fallback "sysdefault"
}
EOL
    chown $REAL_USER:$REAL_USER "$USER_HOME/.asoundrc"
fi

# Install desktop entry
print_info "Installing desktop entry..."
DESKTOP_FILE="/usr/share/applications/voice-to-text.desktop"
cp voice-to-text.desktop "$DESKTOP_FILE" || {
    print_error "Failed to install desktop entry"
    exit 1
}
chmod +x "$DESKTOP_FILE"

# Restart audio services
print_info "Restarting audio services..."
systemctl --user restart pulseaudio.service || true
pulseaudio -k || true
pulseaudio --start || {
    print_error "Failed to restart audio services"
    exit 1
}

print_success "Installation completed successfully!"
print_info "You can now run the application from the applications menu or by running ./run.sh"

