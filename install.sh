#!/bin/bash
# install.sh - Installer for Eco Workspace

set -e

echo "=== Installing Eco Workspace ==="

# 1. Make the main script executable
echo "Making eco_workspace.py executable..."
chmod +x /home/shihab/Desktop/EchoWorkspace/eco_workspace.py

# 2. Create local share directories if they do not exist
echo "Creating application and icon directories..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons"

# 3. Copy the desktop integration launcher
echo "Installing desktop launcher..."
cp /home/shihab/Desktop/EchoWorkspace/eco_workspace.desktop "$HOME/.local/share/applications/eco_workspace.desktop"
# Make the desktop entry trusted/executable for older desktop managers if needed
chmod +x "$HOME/.local/share/applications/eco_workspace.desktop"

# 4. Copy the icon
echo "Installing icon..."
cp /home/shihab/Desktop/EchoWorkspace/assets/icon.png "$HOME/.local/share/icons/eco_workspace.png"

# 5. Update desktop database
echo "Updating desktop application database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications/"
fi

echo "=== Eco Workspace Installed Successfully! ==="
echo "You can now find 'Eco Workspace' in your Application menu or launch it from the terminal using:"
echo "  /home/shihab/Desktop/EchoWorkspace/eco_workspace.py"
