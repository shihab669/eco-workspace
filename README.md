# Eco Workspace

Eco Workspace is a lightweight Linux desktop application for managing terminal workspaces in one place. It is built with Python, GTK 3, and VTE, and it is designed to feel like a native tool rather than a browser app wrapped in a shell.

The app opens a workspace chooser, detects frontend and backend project folders when it can, and gives you a focused terminal dashboard with split panes, workspace switching, and quick launch buttons for common development commands.

## What it does

- Runs as a native Linux GUI app.
- Opens one or more workspace sessions inside the same window.
- Splits terminals horizontally or vertically.
- Detects likely frontend and backend project roots inside the selected folder.
- Adds quick buttons for starting frontend and backend processes.
- Lets you install a desktop launcher and a terminal command for easy access.

## Built For Linux

This project is intended for Linux desktops only. It depends on GTK 3, VTE, and a working shell environment, so it fits naturally into a GNOME-style or other GTK-based desktop setup.

## Requirements

- Linux
- Python 3
- GTK 3 bindings for Python (`gi` / PyGObject)
- VTE 2.91 bindings
- A shell such as `bash`

If you want the desktop integration, you also need a writable user installation path under `~/.local/`.

## Installation

Use the included installer from the project root:

```bash
chmod +x install.sh
./install.sh
```

The installer will:

- Make `eco_workspace.py` executable.
- Install the desktop launcher.
- Copy the app icon into your local icon directory.
- Create an `echowork` command in `~/.local/bin`.
- Refresh the desktop application database when available.

## Running the app

You can launch Eco Workspace in any of these ways:

```bash
./eco_workspace.py
```

```bash
echowork
```

```bash
./eco_workspace.py /path/to/your/project
```

When you pass a project folder, the app uses that directory directly instead of prompting you to choose one.

## How to use it

1. Open the app and choose a workspace folder.
2. Use the left sidebar to manage workspaces.
3. Click the split buttons in a terminal pane to create more terminal views.
4. Use the top bar buttons to start common commands like frontend and backend servers.
5. Press `F11` to toggle fullscreen.

Keyboard shortcuts:

- `Ctrl + Shift + T` adds a workspace.
- `Ctrl + Shift + H` splits the active terminal horizontally.
- `Ctrl + Shift + V` splits the active terminal vertically.
- `Ctrl + Shift + Q` closes the active terminal pane.

## Project structure

- `eco_workspace.py` - main GTK application and terminal workspace logic.
- `style.css` - custom GTK styling for the window, sidebar, and terminal panes.
- `install.sh` - Linux installer for desktop integration.
- `eco_workspace.desktop` - desktop launcher definition.
- `assets/` - app assets such as the logo.

## Design notes

The interface uses a dark, compact layout with a strong focus on the terminal surface. Workspace names update based on active tool/process activity, so you can glance at the sidebar and see what each workspace is doing without opening it.

## Development notes

The app scans the selected workspace for common project markers such as `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, and `build.gradle`. It uses that to guess likely frontend and backend roots and surface launch buttons automatically.

## License

No license file is currently included in the repository.