set -e

echo "=== Installing Eco Workspace ==="
echo "Making eco_workspace.py executable..."
chmod +x /home/shihab/Desktop/EchoWorkspace/eco_workspace.py
echo "Creating application, icon, and binary directories..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/512x512/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/128x128/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/48x48/apps"
mkdir -p "$HOME/.local/share/icons"
mkdir -p "$HOME/.local/bin"
echo "Installing desktop launcher..."
cp /home/shihab/Desktop/EchoWorkspace/eco_workspace.desktop "$HOME/.local/share/applications/eco_workspace.desktop"
chmod +x "$HOME/.local/share/applications/eco_workspace.desktop"
echo "Installing icon..."
cp /home/shihab/Desktop/EchoWorkspace/logo.png "$HOME/.local/share/icons/hicolor/512x512/apps/eco-workspace.png"
cp /home/shihab/Desktop/EchoWorkspace/logo.png "$HOME/.local/share/icons/hicolor/128x128/apps/eco-workspace.png"
cp /home/shihab/Desktop/EchoWorkspace/logo.png "$HOME/.local/share/icons/hicolor/48x48/apps/eco-workspace.png"
cp /home/shihab/Desktop/EchoWorkspace/logo.png "$HOME/.local/share/icons/eco-workspace.png"
echo "Installing echowork CLI command..."
rm -f "$HOME/.local/bin/echowork"
cat > "$HOME/.local/bin/echowork" <<'EOF'
#!/usr/bin/env bash
exec /usr/bin/python3 /home/shihab/Desktop/EchoWorkspace/eco_workspace.py "$@"
EOF
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
echo "  - Running direct script: /home/shihab/Desktop/EchoWorkspace/eco_workspace.py"
