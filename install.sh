set -e

echo "=== Installing Eco Workspace ==="
echo "Making eco_workspace.py executable..."
chmod +x /home/shihab/Desktop/EchoWorkspace/eco_workspace.py
echo "Creating application, icon, and binary directories..."
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons"
mkdir -p "$HOME/.local/bin"
echo "Installing desktop launcher..."
cp /home/shihab/Desktop/EchoWorkspace/eco_workspace.desktop "$HOME/.local/share/applications/eco_workspace.desktop"
chmod +x "$HOME/.local/share/applications/eco_workspace.desktop"
echo "Installing icon..."
cp /home/shihab/Desktop/EchoWorkspace/assets/logo.png "$HOME/.local/share/icons/eco_workspace.png"
echo "Installing echowork CLI command..."
cat > "$HOME/.local/bin/echowork" <<'EOF'
#!/usr/bin/env bash
exec /home/shihab/Desktop/EchoWorkspace/eco_workspace.py "$@"
EOF
chmod +x "$HOME/.local/bin/echowork"
echo "Updating desktop application database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications/"
fi

echo "=== Eco Workspace Installed Successfully! ==="
echo "You can now launch the manager using:"
echo "  - The desktop launcher shortcut 'Eco Workspace'"
echo "  - Running the command 'echowork' from the terminal"
echo "  - Running direct script: /home/shihab/Desktop/EchoWorkspace/eco_workspace.py"
