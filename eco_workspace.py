#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Gdk, GdkPixbuf, Vte, GLib, Pango, Gio
import sys
import os

class TerminalPane:
    def __init__(self, workspace, app):
        self.workspace = workspace
        self.app = app
        self.is_busy = False
        
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.widget.get_style_context().add_class("term-box")
        
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.header.get_style_context().add_class("term-header")
        
        spacer = Gtk.Box()
        self.header.pack_start(spacer, True, True, 0)
        
        self.split_h_btn = Gtk.Button(label="⎯")
        self.split_h_btn.get_style_context().add_class("term-btn")
        self.split_h_btn.set_tooltip_text("Split Horizontally (Ctrl+Shift+H)")
        self.split_h_btn.connect("clicked", lambda w: self.app.split_terminal(self, Gtk.Orientation.HORIZONTAL))
        self.header.pack_start(self.split_h_btn, False, False, 0)
        
        self.split_v_btn = Gtk.Button(label="❘")
        self.split_v_btn.get_style_context().add_class("term-btn")
        self.split_v_btn.set_tooltip_text("Split Vertically (Ctrl+Shift+V)")
        self.split_v_btn.connect("clicked", lambda w: self.app.split_terminal(self, Gtk.Orientation.VERTICAL))
        self.header.pack_start(self.split_v_btn, False, False, 0)
        
        self.close_btn = Gtk.Button(label="✕")
        self.close_btn.get_style_context().add_class("term-btn")
        self.close_btn.get_style_context().add_class("close")
        self.close_btn.set_tooltip_text("Close Terminal (Ctrl+Shift+Q)")
        self.close_btn.connect("clicked", lambda w: self.app.close_terminal(self))
        self.header.pack_start(self.close_btn, False, False, 0)
        
        self.widget.pack_start(self.header, False, False, 0)
        
        self.terminal = Vte.Terminal()
        self.terminal.set_scrollback_lines(10000)
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        self.terminal.set_cursor_shape(Vte.CursorShape.BLOCK)
        self.terminal.set_mouse_autohide(True)
        
        self.setup_terminal_colors()
        
        font_desc = Pango.FontDescription("Ubuntu Mono 11")
        self.terminal.set_font(font_desc)
        
        self.terminal.connect("child-exited", self.on_child_exited)
        self.terminal.connect("window-title-changed", self.on_title_changed)
        self.terminal.connect("commit", self.on_commit)
        self.terminal.connect("focus-in-event", self.on_focus_in)
        
        self.widget.pack_start(self.terminal, True, True, 0)
        
        self.child_pid = self.spawn_shell()
        
    def setup_terminal_colors(self):
        bg = Gdk.RGBA()
        bg.parse("#000000")
        fg = Gdk.RGBA()
        fg.parse("#e4e4e7")
        
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
            cwd,
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
        self.is_busy = True
        
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
    def __init__(self, name, app):
        self.name = name
        self.app = app
        self.panes = []
        self.active_pane = None
        
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        init_pane = TerminalPane(self, self.app)
        self.panes.append(init_pane)
        self.active_pane = init_pane
        self.root_box.pack_start(init_pane.widget, True, True, 0)
        
        self.root_widget = init_pane.widget


class EcoWorkspaceApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="echoWorkspace")
        self.set_default_size(1100, 750)
        
        icon_path = "/home/shihab/Desktop/EchoWorkspace/assets/logo.png"
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)
            
        self.get_style_context().add_class("main-window")
        self.connect("destroy", self.on_destroy)
        self.maximize()
        
        self.load_styles()
        
        self.workspace_dir = None
        self.init_workspace_directory()
        
        self.workspaces = []
        self.active_workspace = None
        
        self.build_ui()
        
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
        if len(sys.argv) > 1:
            arg_path = sys.argv[1]
            if os.path.isdir(arg_path):
                self.workspace_dir = os.path.abspath(arg_path)
                return
                
        self.workspace_dir = self.show_folder_picker_dialog()
        
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
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)
        
        self.top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.top_bar.get_style_context().add_class("top-bar")
        
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
        
        spacer = Gtk.Box()
        self.top_bar.pack_start(spacer, True, True, 0)
        
        tools = ["opencode", "codex", "claude", "openclaude", "codebuff", "echoxcode"]
        for tool in tools:
            btn = Gtk.Button(label=f"{tool} ↵")
            btn.get_style_context().add_class("tool-btn")
            btn.connect("clicked", self.on_tool_btn_clicked, tool)
            self.top_bar.pack_start(btn, False, False, 4)
            
        self.main_box.pack_start(self.top_bar, False, False, 0)
        
        self.content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.content_paned.set_position(240)
        self.main_box.pack_start(self.content_paned, True, True, 0)
        
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.sidebar_box.get_style_context().add_class("sidebar")
        self.sidebar_box.set_size_request(220, -1)
        self.content_paned.pack1(self.sidebar_box, resize=False, shrink=False)
        
        workspaces_header = Gtk.Label(label="Workspaces")
        workspaces_header.get_style_context().add_class("sidebar-section-title")
        workspaces_header.set_alignment(0.0, 0.5)
        self.sidebar_box.pack_start(workspaces_header, False, False, 4)
        
        self.workspace_listbox = Gtk.ListBox()
        self.workspace_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.workspace_listbox.connect("row-selected", self.on_workspace_selected)
        self.sidebar_box.pack_start(self.workspace_listbox, True, True, 0)
        
        self.add_ws_btn = Gtk.Button(label="+ New Workspace")
        self.add_ws_btn.get_style_context().add_class("add-workspace-btn")
        self.add_ws_btn.connect("clicked", lambda w: self.add_workspace(f"Workspace {len(self.workspaces) + 1}"))
        self.sidebar_box.pack_start(self.add_ws_btn, False, False, 4)
        
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.notebook.set_show_border(False)
        self.content_paned.pack2(self.notebook, resize=True, shrink=False)
        
        self.connect("key-press-event", self.on_key_pressed)
        
    def on_tool_btn_clicked(self, button, tool_command):
        if self.active_workspace and self.active_workspace.active_pane:
            pane = self.active_workspace.active_pane
            
            if pane.is_busy:
                pane = self.split_terminal(pane, Gtk.Orientation.HORIZONTAL)
                
            cmd = f"{tool_command}\n"
            pane.terminal.feed_child(cmd.encode('utf-8'))
            pane.is_busy = True
            
    def add_workspace(self, name):
        ws = Workspace(name, self)
        self.workspaces.append(ws)
        
        page_index = self.notebook.append_page(ws.root_box, None)
        ws.page_index = page_index
        
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row_label = Gtk.Label(label=name)
        row_label.set_alignment(0.0, 0.5)
        row_box.pack_start(row_label, True, True, 0)
        
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
        
        self.workspace_listbox.select_row(row)
        ws.active_pane.terminal.grab_focus()
        
    def remove_workspace(self, ws):
        if len(self.workspaces) <= 1:
            return
            
        ws_idx = self.workspaces.index(ws)
        
        for row in self.workspace_listbox.get_children():
            if row.ws == ws:
                self.workspace_listbox.remove(row)
                break
                
        self.notebook.remove_page(ws.page_index)
        self.workspaces.remove(ws)
        
        for i, remaining_ws in enumerate(self.workspaces):
            remaining_ws.page_index = i
            
        new_selection_idx = max(0, ws_idx - 1)
        row_to_select = self.workspace_listbox.get_children()[new_selection_idx]
        self.workspace_listbox.select_row(row_to_select)
        
    def on_workspace_selected(self, listbox, row):
        if row is None:
            return
        ws = row.ws
        self.active_workspace = ws
        self.notebook.set_current_page(ws.page_index)
        
        for child in listbox.get_children():
            child.get_style_context().remove_class("active")
        row.get_style_context().add_class("active")
        
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
        
        if isinstance(parent, Gtk.Paned):
            is_child1 = (parent.get_child1() == current_widget)
            parent.remove(current_widget)
            if is_child1:
                parent.pack1(new_paned, resize=True, shrink=False)
            else:
                parent.pack2(new_paned, resize=True, shrink=False)
        else:
            parent.remove(current_widget)
            parent.pack_start(new_paned, True, True, 0)
            ws.root_widget = new_paned
            
        new_paned.pack1(current_widget, resize=True, shrink=False)
        new_paned.pack2(new_pane.widget, resize=True, shrink=False)
        
        self.show_all()
        
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
            
        if parent_paned.get_child1() == current_widget:
            sibling = parent_paned.get_child2()
        else:
            sibling = parent_paned.get_child1()
            
        grandparent = parent_paned.get_parent()
        
        parent_paned.remove(current_widget)
        parent_paned.remove(sibling)
        grandparent.remove(parent_paned)
        
        if isinstance(grandparent, Gtk.Paned):
            if grandparent.get_child1() is None:
                grandparent.pack1(sibling, resize=True, shrink=False)
            else:
                grandparent.pack2(sibling, resize=True, shrink=False)
        else:
            grandparent.pack_start(sibling, True, True, 0)
            ws.root_widget = sibling
            
        ws.panes.remove(pane)
        
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
        state = event.state & Gdk.ModifierType.CONTROL_MASK and event.state & Gdk.ModifierType.SHIFT_MASK
        if state:
            keyval = event.keyval
            key_name = Gdk.keyval_name(keyval)
            
            if key_name in ['T', 't']:
                self.add_workspace(f"Workspace {len(self.workspaces) + 1}")
                return True
            elif key_name in ['H', 'h']:
                if self.active_workspace and self.active_workspace.active_pane:
                    self.split_terminal(self.active_workspace.active_pane, Gtk.Orientation.HORIZONTAL)
                return True
            elif key_name in ['V', 'v']:
                if self.active_workspace and self.active_workspace.active_pane:
                    self.split_terminal(self.active_workspace.active_pane, Gtk.Orientation.VERTICAL)
                return True
            elif key_name in ['Q', 'q']:
                if self.active_workspace and self.active_workspace.active_pane:
                    self.close_terminal(self.active_workspace.active_pane)
                return True
                
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
