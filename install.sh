#!/bin/bash
# install.sh - Installer for Eco Workspace

set -e

echo "=== Installing Eco Workspace ==="

# 1. Make the main script executable
echo "Making eco_workspace.py executable..."
chmod +x /home/shihab/Desktop/EchoWorkspace/eco_workspace.py

# 2. Create local share directories if they do not exist
echo "Creating application, icon, and binary directories..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons"
mkdir -p "$HOME/.local/bin"

# 3. Copy the desktop integration launcher
echo "Installing desktop launcher..."
cp /home/shihab/Desktop/EchoWorkspace/eco_workspace.desktop "$HOME/.local/share/applications/eco_workspace.desktop"
chmod +x "$HOME/.local/share/applications/eco_workspace.desktop"

# 4. Copy the icon
echo "Installing icon..."
cp /home/shihab/Desktop/EchoWorkspace/assets/logo.png "$HOME/.local/share/icons/eco_workspace.png"

# 5. Install the CLI command 'echowork'
echo "Installing echowork CLI command..."
ln -sf /home/shihab/Desktop/EchoWorkspace/eco_workspace.py "$HOME/.local/bin/echowork"

# 6. Update desktop database
echo "Updating desktop application database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications/"
fi

echo "=== Eco Workspace Installed Successfully! ==="
echo "You can now launch the manager using:"
echo "  - The desktop launcher shortcut 'Eco Workspace'"
echo "  - Running the command 'echowork' from the terminal"
echo "  - Running direct script: /home/shihab/Desktop/EchoWorkspace/eco_workspace.py"
