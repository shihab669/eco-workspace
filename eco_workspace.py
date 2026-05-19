#!/usr/bin/python3
# eco_workspace.py - Native Linux terminal workspace manager.

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Gdk, GdkPixbuf, Vte, GLib, Pango, Gio
import sys
import os

class TerminalPane:
    """Wraps a Vte.Terminal widget with a custom action header bar."""
    def __init__(self, workspace, app):
        self.workspace = workspace
        self.app = app
        self.is_busy = False # Track if the terminal has already executed a command
        
        # Main layout box for this pane
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.widget.get_style_context().add_class("term-box")
        
        # Header bar
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.header.get_style_context().add_class("term-header")
        
        # Spacer to push action buttons to the right
        spacer = Gtk.Box()
        self.header.pack_start(spacer, True, True, 0)
        
        # Split Horizontal button (glyph: ⎯)
        self.split_h_btn = Gtk.Button(label="⎯")
        self.split_h_btn.get_style_context().add_class("term-btn")
        self.split_h_btn.set_tooltip_text("Split Horizontally (Ctrl+Shift+H)")
        self.split_h_btn.connect("clicked", lambda w: self.app.split_terminal(self, Gtk.Orientation.HORIZONTAL))
        self.header.pack_start(self.split_h_btn, False, False, 0)
        
        # Split Vertical button (glyph: ❘)
        self.split_v_btn = Gtk.Button(label="❘")
        self.split_v_btn.get_style_context().add_class("term-btn")
        self.split_v_btn.set_tooltip_text("Split Vertically (Ctrl+Shift+V)")
        self.split_v_btn.connect("clicked", lambda w: self.app.split_terminal(self, Gtk.Orientation.VERTICAL))
        self.header.pack_start(self.split_v_btn, False, False, 0)
        
        # Close button (glyph: ✕)
        self.close_btn = Gtk.Button(label="✕")
        self.close_btn.get_style_context().add_class("term-btn")
        self.close_btn.get_style_context().add_class("close")
        self.close_btn.set_tooltip_text("Close Terminal (Ctrl+Shift+Q)")
        self.close_btn.connect("clicked", lambda w: self.app.close_terminal(self))
        self.header.pack_start(self.close_btn, False, False, 0)
        
        self.widget.pack_start(self.header, False, False, 0)
        
        # Vte Terminal Widget
        self.terminal = Vte.Terminal()
        self.terminal.set_scrollback_lines(10000)
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        self.terminal.set_cursor_shape(Vte.CursorShape.BLOCK)
        self.terminal.set_mouse_autohide(True)
        
        # Load premium theme colors
        self.setup_terminal_colors()
        
        # Setup font
        font_desc = Pango.FontDescription("Ubuntu Mono 11")
        self.terminal.set_font(font_desc)
        
        # Event bindings
        self.terminal.connect("child-exited", self.on_child_exited)
        self.terminal.connect("window-title-changed", self.on_title_changed)
        self.terminal.connect("commit", self.on_commit)
        
        # Focus events to track active terminal highlighting
        self.terminal.connect("focus-in-event", self.on_focus_in)
        
        self.widget.pack_start(self.terminal, True, True, 0)
        
        # Start Shell Session inside active workspace directory
        self.child_pid = self.spawn_shell()
        
    def setup_terminal_colors(self):
        # Pure Black Theme
        bg = Gdk.RGBA()
        bg.parse("#000000") # Dark black background
        fg = Gdk.RGBA()
        fg.parse("#e4e4e7") # Zinc 200 text
        
        palette_hex = [
            "#27272a", "#f43f5e", "#22c55e", "#eab308",
            "#3b82f6", "#d946ef", "#06b6d4", "#d4d4d8",
            "#52525b", "#f43f5e", "#22c55e", "#eab308",
            "#3b82f6", "#d946ef", "#06b6d4", "#fafafa"
        ]
        palette = []
        for hex_val in palette_hex:
            rgba = Gdk.RGBA()
            rgba.parse(hex_val)
            palette.append(rgba)
            
        self.terminal.set_colors(fg, bg, palette)
        
    def spawn_shell(self):
        shell = os.environ.get("SHELL", "/bin/bash")
        cwd = self.app.workspace_dir if self.app.workspace_dir else None
        
        success, pid = self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            cwd, # Start shell directly in selected folder path
            [shell],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            None
        )
        if not success:
            print(f"Failed to spawn shell in {cwd}: {shell}")
        return pid
        
    def on_child_exited(self, terminal, status):
        self.app.close_terminal(self)
        
    def on_title_changed(self, terminal):
        self.app.refresh_sidebar()

    def on_commit(self, terminal, text, size):
        self.is_busy = True # Set busy if user types text manually in terminal
        
    def on_focus_in(self, widget, event):
        self.app.set_active_terminal(self)
        return False
        
    def set_focused_style(self, focused):
        ctx = self.widget.get_style_context()
        if focused:
            ctx.add_class("focused")
            self.terminal.grab_focus()
        else:
            ctx.remove_class("focused")


class Workspace:
    """Manages a single workspace containing multiple terminal splits."""
    def __init__(self, name, app):
        self.name = name
        self.app = app
        self.panes = []
        self.active_pane = None
        
        # Workspace Page Container
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Initialize with a single terminal pane
        init_pane = TerminalPane(self, self.app)
        self.panes.append(init_pane)
        self.active_pane = init_pane
        self.root_box.pack_start(init_pane.widget, True, True, 0)
        
        # Store root widget pointer for building layout splits
        self.root_widget = init_pane.widget


class EcoWorkspaceApp(Gtk.Window):
    """Main application window container and controller."""
    def __init__(self):
        super().__init__(title="echoWorkspace")
        self.set_default_size(1100, 750)
        
        # Set Application Icon using logo.png
        icon_path = "/home/shihab/Desktop/EchoWorkspace/assets/logo.png"
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)
            
        self.get_style_context().add_class("main-window")
        self.connect("destroy", self.on_destroy)
        self.fullscreen()
        
        # Load CSS Styling
        self.load_styles()
        
        # Parse or Pick Workspace Directory
        self.workspace_dir = None
        self.init_workspace_directory()
        
        # Setup workspaces data structure
        self.workspaces = []
        self.active_workspace = None
        
        # Initialize UI Grid
        self.build_ui()
        
        # Add initial workspace inside selected folder
        self.add_workspace("Workspace 1")
        
    def load_styles(self):
        style_provider = Gtk.CssProvider()
        css_path = "/home/shihab/Desktop/EchoWorkspace/style.css"
        if os.path.exists(css_path):
            style_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                style_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
    def init_workspace_directory(self):
        # 1. Check if folder was passed as command line argument (drag-and-drop / terminal launcher)
        if len(sys.argv) > 1:
            arg_path = sys.argv[1]
            if os.path.isdir(arg_path):
                self.workspace_dir = os.path.abspath(arg_path)
                return
                
        # 2. Show native GTK folder selection dialog
        self.workspace_dir = self.show_folder_picker_dialog()
        
        # 3. Default to user home directory if dialog was canceled
        if not self.workspace_dir:
            self.workspace_dir = os.path.expanduser("~")
            
    def show_folder_picker_dialog(self):
        dialog = Gtk.FileChooserDialog(
            title="Open Folder - echoWorkspace",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Open", Gtk.ResponseType.OK
        )
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        folder = None
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            
        dialog.destroy()
        return folder

    def build_ui(self):
        # Main vertical container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)
        
        # 1. Top Navigation Bar
        self.top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.top_bar.get_style_context().add_class("top-bar")
        
        # Logo + text box
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        logo_path = "/home/shihab/Desktop/EchoWorkspace/assets/logo.png"
        if os.path.exists(logo_path):
            try:
                logo_pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 28, 28, True)
                logo_img = Gtk.Image.new_from_pixbuf(logo_pb)
                title_box.pack_start(logo_img, False, False, 0)
            except Exception as e:
                print("Failed to load logo in top nav bar:", e)
                
        self.title_label = Gtk.Label(label="echoWorkspace")
        self.title_label.get_style_context().add_class("title-label")
        title_box.pack_start(self.title_label, False, False, 0)
        
        self.top_bar.pack_start(title_box, False, False, 4)
        
        # Spacer
        spacer = Gtk.Box()
        self.top_bar.pack_start(spacer, True, True, 0)
        
        # Navbar tool execution buttons (text-only with enter icon)
        tools = ["opencode", "codex", "claude", "openclaude", "codebuff", "echoxcode"]
        for tool in tools:
            btn = Gtk.Button(label=f"{tool} ↵")
            btn.get_style_context().add_class("tool-btn")
            btn.connect("clicked", self.on_tool_btn_clicked, tool)
            self.top_bar.pack_start(btn, False, False, 4)
            
        self.main_box.pack_start(self.top_bar, False, False, 0)
        
        # 2. Main content area (Horizontal split between Sidebar and Workspace Notebook)
        self.content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_paned.set_position(180) # Narrow sidebar
        self.main_box.pack_start(self.content_paned, True, True, 0)
        
        # 2a. Sidebar Panel
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.sidebar_box.get_style_context().add_class("sidebar")
        self.sidebar_box.set_size_request(150, -1)
        self.content_paned.pack1(self.sidebar_box, resize=False, shrink=False)
        
        # Sidebar "WORKSPACES" Section Header
        workspaces_header = Gtk.Label(label="Workspaces")
        workspaces_header.get_style_context().add_class("sidebar-section-title")
        workspaces_header.set_alignment(0.0, 0.5)
        self.sidebar_box.pack_start(workspaces_header, False, False, 4)
        
        # List of Workspaces
        self.workspace_listbox = Gtk.ListBox()
        self.workspace_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.workspace_listbox.connect("row-selected", self.on_workspace_selected)
        self.sidebar_box.pack_start(self.workspace_listbox, True, True, 0)
        
        # Add Workspace Button
        self.add_ws_btn = Gtk.Button(label="+ New Workspace")
        self.add_ws_btn.get_style_context().add_class("add-workspace-btn")
        self.add_ws_btn.connect("clicked", lambda w: self.add_workspace(f"Workspace {len(self.workspaces) + 1}"))
        self.sidebar_box.pack_start(self.add_ws_btn, False, False, 4)
        
        # 2b. Right Workspace Notebook
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(False) # Hide tabs to switch ONLY via Sidebar list
        self.notebook.set_show_border(False)
        self.content_paned.pack2(self.notebook, resize=True, shrink=False)
        
        # Connect Keyboard Shortcuts
        self.connect("key-press-event", self.on_key_pressed)
        
    def on_tool_btn_clicked(self, button, tool_command):
        if self.active_workspace and self.active_workspace.active_pane:
            pane = self.active_workspace.active_pane
            
            # If the current terminal is already executing a tool or has user input, automatically split it
            if pane.is_busy:
                pane = self.split_terminal(pane, Gtk.Orientation.HORIZONTAL)
                
            # Feed the command and append a newline to auto-execute it inside active shell/tool
            cmd = f"{tool_command}\n"
            pane.terminal.feed_child(cmd.encode('utf-8'))
            pane.is_busy = True
            
    def add_workspace(self, name):
        ws = Workspace(name, self)
        self.workspaces.append(ws)
        
        # Add page to Notebook
        page_index = self.notebook.append_page(ws.root_box, None)
        ws.page_index = page_index
        
        # Add listbox row to sidebar
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row_label = Gtk.Label(label=name)
        row_label.set_alignment(0.0, 0.5)
        row_box.pack_start(row_label, True, True, 0)
        
        # Small close button for the workspace (only show if not the last workspace)
        ws_close_btn = Gtk.Button(label="✕")
        ws_close_btn.get_style_context().add_class("term-btn")
        ws_close_btn.set_tooltip_text("Delete Workspace")
        ws_close_btn.connect("clicked", lambda w: self.remove_workspace(ws))
        row_box.pack_start(ws_close_btn, False, False, 0)
        
        row = Gtk.ListBoxRow()
        row.get_style_context().add_class("workspace-row")
        row.add(row_box)
        row.ws = ws
        
        self.workspace_listbox.add(row)
        self.show_all()
        
        # Select newly created workspace
        self.workspace_listbox.select_row(row)
        ws.active_pane.terminal.grab_focus()
        
    def remove_workspace(self, ws):
        if len(self.workspaces) <= 1:
            return
            
        # Find index in list
        ws_idx = self.workspaces.index(ws)
        
        # Find listbox row and remove
        for row in self.workspace_listbox.get_children():
            if row.ws == ws:
                self.workspace_listbox.remove(row)
                break
                
        # Remove notebook page
        self.notebook.remove_page(ws.page_index)
        self.workspaces.remove(ws)
        
        # Update remaining workspaces' page indexes
        for i, remaining_ws in enumerate(self.workspaces):
            remaining_ws.page_index = i
            
        # Switch selection
        new_selection_idx = max(0, ws_idx - 1)
        row_to_select = self.workspace_listbox.get_children()[new_selection_idx]
        self.workspace_listbox.select_row(row_to_select)
        
    def on_workspace_selected(self, listbox, row):
        if row is None:
            return
        ws = row.ws
        self.active_workspace = ws
        self.notebook.set_current_page(ws.page_index)
        
        # Highlight active row in sidebar CSS
        for child in listbox.get_children():
            child.get_style_context().remove_class("active")
        row.get_style_context().add_class("active")
        
        # Set active terminal focus styling
        self.update_terminal_focus_borders()
        
        if ws.active_pane:
            ws.active_pane.terminal.grab_focus()
            
    def set_active_terminal(self, pane):
        if self.active_workspace:
            self.active_workspace.active_pane = pane
            self.update_terminal_focus_borders()
            
    def update_terminal_focus_borders(self):
        if not self.active_workspace:
            return
        for pane in self.active_workspace.panes:
            pane.set_focused_style(pane == self.active_workspace.active_pane)
            
    def split_terminal(self, current_pane, orientation):
        ws = current_pane.workspace
        new_pane = TerminalPane(ws, self)
        ws.panes.append(new_pane)
        
        current_widget = current_pane.widget
        parent = current_widget.get_parent()
        
        new_paned = Gtk.Paned(orientation=orientation)
        new_paned.show()
        
        # Determine current layout location and construct splits
        if isinstance(parent, Gtk.Paned):
            is_child1 = (parent.get_child1() == current_widget)
            parent.remove(current_widget)
            if is_child1:
                parent.pack1(new_paned, resize=True, shrink=False)
            else:
                parent.pack2(new_paned, resize=True, shrink=False)
        else: # Parent is the root page box container
            parent.remove(current_widget)
            parent.pack_start(new_paned, True, True, 0)
            ws.root_widget = new_paned
            
        # Dock terminals into splits
        new_paned.pack1(current_widget, resize=True, shrink=False)
        new_paned.pack2(new_pane.widget, resize=True, shrink=False)
        
        self.show_all()
        
        # Set focus to the new pane
        ws.active_pane = new_pane
        self.update_terminal_focus_borders()
        new_pane.terminal.grab_focus()
        self.refresh_sidebar()
        
        return new_pane
        
    def close_terminal(self, pane):
        ws = pane.workspace
        if len(ws.panes) <= 1:
            return
            
        current_widget = pane.widget
        parent_paned = current_widget.get_parent()
        
        if not isinstance(parent_paned, Gtk.Paned):
            return
            
        # Determine sibling pane which will expand
        if parent_paned.get_child1() == current_widget:
            sibling = parent_paned.get_child2()
        else:
            sibling = parent_paned.get_child1()
            
        grandparent = parent_paned.get_parent()
        
        parent_paned.remove(current_widget)
        parent_paned.remove(sibling)
        grandparent.remove(parent_paned)
        
        # Replace the parent container with the promoted sibling pane
        if isinstance(grandparent, Gtk.Paned):
            if grandparent.get_child1() is None:
                grandparent.pack1(sibling, resize=True, shrink=False)
            else:
                grandparent.pack2(sibling, resize=True, shrink=False)
        else: # Grandparent is root box container
            grandparent.pack_start(sibling, True, True, 0)
            ws.root_widget = sibling
            
        # Remove from workspace tracking
        ws.panes.remove(pane)
        
        # If active terminal was deleted, select sibling
        if ws.active_pane == pane:
            sibling_pane = None
            for p in ws.panes:
                if p.widget == sibling or sibling.is_ancestor(p.widget):
                    sibling_pane = p
                    break
            ws.active_pane = sibling_pane or ws.panes[0]
            
        self.show_all()
        self.update_terminal_focus_borders()
        ws.active_pane.terminal.grab_focus()
        self.refresh_sidebar()
        
    def refresh_sidebar(self):
        pass
        
    def on_key_pressed(self, widget, event):
        # Check Ctrl+Shift shortcuts
        state = event.state & Gdk.ModifierType.CONTROL_MASK and event.state & Gdk.ModifierType.SHIFT_MASK
        if state:
            keyval = event.keyval
            key_name = Gdk.keyval_name(keyval)
            
            if key_name in ['T', 't']:
                # Ctrl+Shift+T - New workspace
                self.add_workspace(f"Workspace {len(self.workspaces) + 1}")
                return True
            elif key_name in ['H', 'h']:
                # Ctrl+Shift+H - Split Horizontally
                if self.active_workspace and self.active_workspace.active_pane:
                    self.split_terminal(self.active_workspace.active_pane, Gtk.Orientation.HORIZONTAL)
                return True
            elif key_name in ['V', 'v']:
                # Ctrl+Shift+V - Split Vertically
                if self.active_workspace and self.active_workspace.active_pane:
                    self.split_terminal(self.active_workspace.active_pane, Gtk.Orientation.VERTICAL)
                return True
            elif key_name in ['Q', 'q']:
                # Ctrl+Shift+Q - Close terminal pane
                if self.active_workspace and self.active_workspace.active_pane:
                    self.close_terminal(self.active_workspace.active_pane)
                return True
                
        # F11 - Toggle Fullscreen
        if Gdk.keyval_name(event.keyval) == 'F11':
            state = self.get_window().get_state()
            if state & Gdk.WindowState.FULLSCREEN:
                self.unfullscreen()
            else:
                self.fullscreen()
            return True
            
        return False
        
    def on_destroy(self, widget):
        Gtk.main_quit()

if __name__ == "__main__":
    app = EcoWorkspaceApp()
    Gtk.main()
