#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Eco Workspace ==="
echo "Installing from: $SCRIPT_DIR"

echo "Making eco_workspace.py executable..."
chmod +x "$SCRIPT_DIR/eco_workspace.py"

echo "Creating application, icon, and binary directories..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/512x512/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/128x128/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/48x48/apps"
mkdir -p "$HOME/.local/share/icons"
mkdir -p "$HOME/.local/bin"

echo "Installing desktop launcher..."
cat > "$HOME/.local/share/applications/eco_workspace.desktop" <<DESKTOP
[Desktop Entry]
Name=Eco Workspace
Comment=Native Linux terminal manager with custom splits
Exec=/usr/bin/python3 ${SCRIPT_DIR}/eco_workspace.py %f
Icon=eco-workspace
StartupWMClass=EcoWorkspace
Terminal=false
Type=Application
Categories=System;TerminalEmulator;
Keywords=terminal;pty;split;workspace;record;eco;
StartupNotify=true
DESKTOP
chmod +x "$HOME/.local/share/applications/eco_workspace.desktop"

echo "Installing icon..."
cp "$SCRIPT_DIR/logo.png" "$HOME/.local/share/icons/hicolor/512x512/apps/eco-workspace.png"
cp "$SCRIPT_DIR/logo.png" "$HOME/.local/share/icons/hicolor/128x128/apps/eco-workspace.png"
cp "$SCRIPT_DIR/logo.png" "$HOME/.local/share/icons/hicolor/48x48/apps/eco-workspace.png"
cp "$SCRIPT_DIR/logo.png" "$HOME/.local/share/icons/eco-workspace.png"

echo "Installing echowork CLI command..."
rm -f "$HOME/.local/bin/echowork"
cat > "$HOME/.local/bin/echowork" <<ECHOWORK
#!/usr/bin/env bash
exec /usr/bin/python3 ${SCRIPT_DIR}/eco_workspace.py "\$@"
ECHOWORK
chmod +x "$HOME/.local/bin/echowork"

echo "Updating desktop application database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications/"
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
fi

echo "=== Eco Workspace Installed Successfully! ==="
echo "You can now launch the manager using:"
echo "  - The desktop launcher shortcut 'Eco Workspace'"
echo "  - Running the command 'echowork' from the terminal"
echo "  - Running direct script: $SCRIPT_DIR/eco_workspace.py"
