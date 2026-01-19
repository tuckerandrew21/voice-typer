"""
MurmurTone Settings GUI - V2
Rebuilt to exactly match the HTML mockup (Slack Examples/settings-mockup-v2.html)
"""
import version_check  # noqa: F401 - Must be first, checks Python version

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import webbrowser
import os
import sys
import threading
import subprocess
import ctypes
from PIL import Image

import config
import settings_logic
from theme import make_combobox_clickable
from ai_cleanup import validate_ollama_url

# =============================================================================
# COLORS - Exact match to HTML mockup CSS variables
# =============================================================================
PRIMARY = "#0d9488"        # --primary (teal)
PRIMARY_DARK = "#0f766e"   # --primary-dark
PRIMARY_LIGHT = "#14b8a6"  # --primary-light

SLATE_900 = "#0f172a"      # Window background
SLATE_800 = "#1e293b"      # Sidebar, card backgrounds
SLATE_700 = "#334155"      # Hover states, borders
SLATE_600 = "#475569"      # Borders, disabled
SLATE_500 = "#64748b"      # Help text, version text
SLATE_400 = "#94a3b8"      # Placeholder, close button
SLATE_300 = "#cbd5e1"      # Nav items text
SLATE_200 = "#e2e8f0"      # Primary text
SLATE_100 = "#f1f5f9"      # Titles, bright text

SUCCESS = "#10b981"
WARNING = "#f59e0b"
ERROR = "#ef4444"
ERROR_DARK = "#dc2626"     # Darker red for hover states

# Font family - Roboto Serif for softer, friendlier feel
FONT_FAMILY = "Roboto Serif"

# =============================================================================
# SPACING - Exact match to HTML mockup CSS variables
# =============================================================================
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_2XL = 32

# Window dimensions
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650
SIDEBAR_WIDTH = 220

# =============================================================================
# SAMPLE RATE OPTIONS
# =============================================================================
SAMPLE_RATE_OPTIONS = {
    16000: "16000 Hz (Recommended)",
    44100: "44100 Hz (CD Quality)",
    48000: "48000 Hz (Studio)",
}

# =============================================================================
# RECORDING MODE LABELS - Display labels for recording modes
# =============================================================================
RECORDING_MODE_LABELS = {
    "push_to_talk": "Push-to-Talk",
    "toggle": "Toggle",
    "auto_stop": "Auto-stop",
}
RECORDING_MODE_VALUES = {v: k for k, v in RECORDING_MODE_LABELS.items()}

# =============================================================================
# PASTE MODE LABELS
# =============================================================================
PASTE_MODE_LABELS = {
    "clipboard": "Clipboard",
    "type": "Type",
}
PASTE_MODE_VALUES = {v: k for k, v in PASTE_MODE_LABELS.items()}

# =============================================================================
# PREVIEW POSITION LABELS
# =============================================================================
PREVIEW_POSITION_LABELS = {
    "top_left": "Top Left",
    "top_right": "Top Right",
    "bottom_left": "Bottom Left",
    "bottom_right": "Bottom Right",
    "center": "Center",
}
PREVIEW_POSITION_VALUES = {v: k for k, v in PREVIEW_POSITION_LABELS.items()}

# =============================================================================
# PREVIEW THEME LABELS
# =============================================================================
PREVIEW_THEME_LABELS = {
    "dark": "Dark",
    "light": "Light",
}
PREVIEW_THEME_VALUES = {v: k for k, v in PREVIEW_THEME_LABELS.items()}

# =============================================================================
# ICONS - PNG icons matching mockup SVG line icons
# Icons are loaded from assets/icons/ directory
# =============================================================================
ICON_NAMES = ["general", "audio", "recognition", "text", "advanced", "about"]
ICON_SIZE = (20, 20)  # Matches mockup .nav-icon size

def load_nav_icons():
    """Load navigation icons as CTkImage objects."""
    icons = {}
    icons_dir = resource_path(os.path.join("assets", "icons"))

    for name in ICON_NAMES:
        icon_path = os.path.join(icons_dir, f"icon_{name}.png")
        if os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                icons[name] = ctk.CTkImage(light_image=img, dark_image=img, size=ICON_SIZE)
            except Exception as e:
                print(f"Failed to load icon {name}: {e}")
                icons[name] = None
        else:
            print(f"Icon not found: {icon_path}")
            icons[name] = None

    return icons


def resource_path(relative_path):
    """Get absolute path to resource."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_custom_fonts():
    """Load bundled fonts for the current process (Windows only)."""
    if sys.platform != "win32":
        return
    fonts_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    if os.path.exists(fonts_dir):
        FR_PRIVATE = 0x10  # Font is available only to this process
        for filename in os.listdir(fonts_dir):
            if filename.lower().endswith(".ttf"):
                font_path = os.path.join(fonts_dir, filename)
                ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)


# Load custom fonts before initializing GUI
load_custom_fonts()

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# =============================================================================
# DEBOUNCE MANAGER - For autosave functionality
# =============================================================================

class DebounceManager:
    """Manages debounced saves for text inputs and sliders."""

    def __init__(self, window, save_callback, delay_ms=1500):
        """
        Args:
            window: Tkinter window (for after() scheduling)
            save_callback: Function to call when debounce timer expires
            delay_ms: Delay in milliseconds before saving
        """
        self._window = window
        self._save_callback = save_callback
        self._delay_ms = delay_ms
        self._pending_id = None

    def schedule(self):
        """Schedule a debounced save. Cancels any pending save."""
        if self._pending_id:
            self._window.after_cancel(self._pending_id)
        self._pending_id = self._window.after(self._delay_ms, self._execute)

    def _execute(self):
        """Execute the save callback."""
        self._pending_id = None
        self._save_callback()

    def flush(self):
        """Immediately execute pending save if any."""
        if self._pending_id:
            self._window.after_cancel(self._pending_id)
            self._pending_id = None
            self._save_callback()

    def cancel(self):
        """Cancel any pending save without executing."""
        if self._pending_id:
            self._window.after_cancel(self._pending_id)
            self._pending_id = None


# =============================================================================
# EDITOR DIALOGS
# =============================================================================

class ListEditorDialog:
    """Base class for list editor dialogs (Dictionary, Vocabulary, Shortcuts)."""

    def __init__(self, parent, title, items, columns, on_save):
        """
        Args:
            parent: Parent window
            title: Dialog title
            items: List of items to edit
            columns: List of column names
            on_save: Callback with updated items list
        """
        self.parent = parent
        self.items = [item.copy() if isinstance(item, dict) else item for item in items]
        self.columns = columns
        self.on_save = on_save
        self.selected_index = None

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.configure(fg_color=SLATE_900)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self._create_ui()
        self._refresh_list()

    def _create_ui(self):
        """Create the dialog UI."""
        # Main container
        main = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # List frame
        list_frame = ctk.CTkFrame(main, fg_color=SLATE_800, corner_radius=8)
        list_frame.pack(fill="both", expand=True, pady=(0, SPACE_MD))

        # Calculate column width based on dialog width and number of columns
        # Dialog is 500px, minus padding (16*2) and list frame padding (2*2) and scrollbar (~16)
        available_width = 500 - 32 - 4 - 16
        self.col_width = available_width // len(self.columns)

        # Header row
        header = ctk.CTkFrame(list_frame, fg_color=SLATE_700, corner_radius=0)
        header.pack(fill="x", padx=2, pady=(2, 0))

        for i, col in enumerate(self.columns):
            lbl = ctk.CTkLabel(
                header,
                text=col,
                width=self.col_width,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color=SLATE_300,
                anchor="w",
            )
            lbl.pack(side="left", padx=SPACE_SM, pady=SPACE_XS)

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            scrollbar_button_color=SLATE_600,
        )
        self.list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Button row
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x")

        self.add_btn = ctk.CTkButton(
            btn_row,
            text="Add",
            width=80,
            height=32,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._add_item,
        )
        self.add_btn.pack(side="left", padx=(0, SPACE_SM))

        self.edit_btn = ctk.CTkButton(
            btn_row,
            text="Edit",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._edit_item,
        )
        self.edit_btn.pack(side="left", padx=(0, SPACE_SM))

        self.delete_btn = ctk.CTkButton(
            btn_row,
            text="Delete",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=ERROR,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._delete_item,
        )
        self.delete_btn.pack(side="left")

        # Save/Cancel
        ctk.CTkButton(
            btn_row,
            text="Save",
            width=80,
            height=32,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._save,
        ).pack(side="right", padx=(SPACE_SM, 0))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self.dialog.destroy,
        ).pack(side="right")

    def _refresh_list(self):
        """Refresh the list display."""
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Add items
        for i, item in enumerate(self.items):
            row = ctk.CTkFrame(
                self.list_frame,
                fg_color=SLATE_700 if i == self.selected_index else "transparent",
                corner_radius=4,
            )
            row.pack(fill="x", pady=1)
            row.bind("<Button-1>", lambda e, idx=i: self._select_item(idx))

            values = self._get_display_values(item)
            for val in values:
                lbl = ctk.CTkLabel(
                    row,
                    text=str(val),
                    width=self.col_width,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    text_color=SLATE_200,
                    anchor="w",
                )
                lbl.pack(side="left", padx=SPACE_SM, pady=SPACE_XS)
                lbl.bind("<Button-1>", lambda e, idx=i: self._select_item(idx))

    def _select_item(self, index):
        """Select an item."""
        self.selected_index = index
        self._refresh_list()

    def _get_display_values(self, item):
        """Override in subclass to return display values for an item."""
        raise NotImplementedError

    def _add_item(self):
        """Override in subclass to add a new item."""
        raise NotImplementedError

    def _edit_item(self):
        """Override in subclass to edit selected item."""
        raise NotImplementedError

    def _delete_item(self):
        """Delete selected item."""
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            del self.items[self.selected_index]
            self.selected_index = None
            self._refresh_list()

    def _save(self):
        """Save and close."""
        self.on_save(self.items)
        self.dialog.destroy()


class DictionaryEditor(ListEditorDialog):
    """Editor for custom word replacements."""

    def __init__(self, parent, items, on_save):
        super().__init__(
            parent,
            "Edit Dictionary",
            items,
            ["From", "To"],
            on_save,
        )

    def _get_display_values(self, item):
        if isinstance(item, dict):
            return [item.get("from", ""), item.get("to", "")]
        return [str(item), ""]

    def _add_item(self):
        self._show_entry_dialog(None)

    def _edit_item(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            self._show_entry_dialog(self.selected_index)

    def _show_entry_dialog(self, edit_index):
        """Show dialog to add/edit an entry."""
        is_edit = edit_index is not None
        item = self.items[edit_index] if is_edit else {"from": "", "to": ""}

        dlg = ctk.CTkToplevel(self.dialog)
        dlg.title("Edit Entry" if is_edit else "Add Entry")
        dlg.geometry("350x220")
        dlg.configure(fg_color=SLATE_900)
        dlg.transient(self.dialog)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # From field
        ctk.CTkLabel(frame, text="From:", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                     text_color=SLATE_200).pack(anchor="w")
        from_var = ctk.StringVar(value=item.get("from", ""))
        from_entry = ctk.CTkEntry(frame, textvariable=from_var, width=300,
                                   fg_color=SLATE_800, border_color=SLATE_600)
        from_entry.pack(fill="x", pady=(SPACE_XS, SPACE_MD))

        # To field
        ctk.CTkLabel(frame, text="To:", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                     text_color=SLATE_200).pack(anchor="w")
        to_var = ctk.StringVar(value=item.get("to", ""))
        to_entry = ctk.CTkEntry(frame, textvariable=to_var, width=300,
                                 fg_color=SLATE_800, border_color=SLATE_600)
        to_entry.pack(fill="x", pady=(SPACE_XS, SPACE_MD))

        def save_entry():
            new_item = {"from": from_var.get(), "to": to_var.get(), "case_sensitive": False}
            if from_var.get():  # Only save if "from" is not empty
                if is_edit:
                    self.items[edit_index] = new_item
                else:
                    self.items.append(new_item)
                self._refresh_list()
            dlg.destroy()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="Save", width=80, fg_color=PRIMARY,
                      hover_color=PRIMARY_DARK, command=save_entry).pack(side="right", padx=(SPACE_SM, 0))
        ctk.CTkButton(btn_row, text="Cancel", width=80, fg_color=SLATE_700,
                      hover_color=SLATE_600, command=dlg.destroy).pack(side="right")


class VocabularyEditor(ListEditorDialog):
    """Editor for custom vocabulary words."""

    def __init__(self, parent, items, on_save):
        super().__init__(
            parent,
            "Edit Vocabulary",
            items,
            ["Word/Phrase"],
            on_save,
        )

    def _get_display_values(self, item):
        return [str(item)]

    def _add_item(self):
        self._show_entry_dialog(None)

    def _edit_item(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            self._show_entry_dialog(self.selected_index)

    def _show_entry_dialog(self, edit_index):
        """Show dialog to add/edit a vocabulary word."""
        is_edit = edit_index is not None
        word = self.items[edit_index] if is_edit else ""

        dlg = ctk.CTkToplevel(self.dialog)
        dlg.title("Edit Word" if is_edit else "Add Word")
        dlg.geometry("350x160")
        dlg.configure(fg_color=SLATE_900)
        dlg.transient(self.dialog)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(frame, text="Word/Phrase:", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                     text_color=SLATE_200).pack(anchor="w")
        word_var = ctk.StringVar(value=word)
        word_entry = ctk.CTkEntry(frame, textvariable=word_var, width=300,
                                   fg_color=SLATE_800, border_color=SLATE_600)
        word_entry.pack(fill="x", pady=(SPACE_XS, SPACE_MD))

        def save_entry():
            if word_var.get():
                if is_edit:
                    self.items[edit_index] = word_var.get()
                else:
                    self.items.append(word_var.get())
                self._refresh_list()
            dlg.destroy()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="Save", width=80, fg_color=PRIMARY,
                      hover_color=PRIMARY_DARK, command=save_entry).pack(side="right", padx=(SPACE_SM, 0))
        ctk.CTkButton(btn_row, text="Cancel", width=80, fg_color=SLATE_700,
                      hover_color=SLATE_600, command=dlg.destroy).pack(side="right")


class ShortcutsEditor(ListEditorDialog):
    """Editor for text shortcuts (trigger -> expansion)."""

    def __init__(self, parent, items, on_save):
        super().__init__(
            parent,
            "Edit Shortcuts",
            items,
            ["Trigger", "Replacement"],
            on_save,
        )

    def _get_display_values(self, item):
        if isinstance(item, dict):
            replacement = item.get("replacement", "")
            # Truncate long replacements
            if len(replacement) > 30:
                replacement = replacement[:27] + "..."
            return [item.get("trigger", ""), replacement]
        return [str(item), ""]

    def _add_item(self):
        self._show_entry_dialog(None)

    def _edit_item(self):
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            self._show_entry_dialog(self.selected_index)

    def _show_entry_dialog(self, edit_index):
        """Show dialog to add/edit a shortcut."""
        is_edit = edit_index is not None
        item = self.items[edit_index] if is_edit else {"trigger": "", "replacement": "", "enabled": True}

        dlg = ctk.CTkToplevel(self.dialog)
        dlg.title("Edit Shortcut" if is_edit else "Add Shortcut")
        dlg.geometry("400x290")
        dlg.configure(fg_color=SLATE_900)
        dlg.transient(self.dialog)
        dlg.grab_set()

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # Trigger field
        ctk.CTkLabel(frame, text="Trigger phrase:", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                     text_color=SLATE_200).pack(anchor="w")
        trigger_var = ctk.StringVar(value=item.get("trigger", ""))
        trigger_entry = ctk.CTkEntry(frame, textvariable=trigger_var, width=350,
                                      fg_color=SLATE_800, border_color=SLATE_600)
        trigger_entry.pack(fill="x", pady=(SPACE_XS, SPACE_MD))

        # Replacement field
        ctk.CTkLabel(frame, text="Replacement text:", font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                     text_color=SLATE_200).pack(anchor="w")
        replacement_text = ctk.CTkTextbox(frame, width=350, height=80,
                                           fg_color=SLATE_800, border_color=SLATE_600)
        replacement_text.insert("1.0", item.get("replacement", ""))
        replacement_text.pack(fill="x", pady=(SPACE_XS, SPACE_MD))

        def save_entry():
            new_item = {
                "trigger": trigger_var.get(),
                "replacement": replacement_text.get("1.0", "end-1c"),
                "enabled": True,
            }
            if trigger_var.get():
                if is_edit:
                    self.items[edit_index] = new_item
                else:
                    self.items.append(new_item)
                self._refresh_list()
            dlg.destroy()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(btn_row, text="Save", width=80, fg_color=PRIMARY,
                      hover_color=PRIMARY_DARK, command=save_entry).pack(side="right", padx=(SPACE_SM, 0))
        ctk.CTkButton(btn_row, text="Cancel", width=80, fg_color=SLATE_700,
                      hover_color=SLATE_600, command=dlg.destroy).pack(side="right")


class HistoryViewer:
    """Dialog for viewing transcription history."""

    def __init__(self, parent):
        """
        Args:
            parent: Parent window
        """
        import text_processor

        self.parent = parent
        self.entries = text_processor.TranscriptionHistory.load_from_disk()

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Transcription History")
        self.dialog.geometry("600x450")
        self.dialog.configure(fg_color=SLATE_900)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 450) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self._create_ui()

    def _create_ui(self):
        """Create the dialog UI."""
        # Main container
        main = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # Title
        title = ctk.CTkLabel(
            main,
            text="Recent Transcriptions",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=SLATE_100,
        )
        title.pack(anchor="w", pady=(0, SPACE_MD))

        # List frame
        list_frame = ctk.CTkFrame(main, fg_color=SLATE_800, corner_radius=8)
        list_frame.pack(fill="both", expand=True, pady=(0, SPACE_MD))

        # Header row
        header = ctk.CTkFrame(list_frame, fg_color=SLATE_700, corner_radius=0)
        header.pack(fill="x", padx=2, pady=(2, 0))

        ctk.CTkLabel(
            header,
            text="Time",
            width=120,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=SLATE_300,
            anchor="w",
        ).pack(side="left", padx=SPACE_SM, pady=SPACE_XS)

        ctk.CTkLabel(
            header,
            text="Transcription",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=SLATE_300,
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=SPACE_SM, pady=SPACE_XS)

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            scrollbar_button_color=SLATE_600,
        )
        self.list_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.selected_index = None
        self.row_frames = []
        self._populate_list()

        # Button row
        btn_row = ctk.CTkFrame(main, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="Copy",
            width=80,
            height=32,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._copy_selected,
        ).pack(side="left", padx=(0, SPACE_SM))

        ctk.CTkButton(
            btn_row,
            text="Export",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._export_history,
        ).pack(side="left", padx=(0, SPACE_SM))

        ctk.CTkButton(
            btn_row,
            text="Clear All",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=ERROR,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self._clear_history,
        ).pack(side="left", padx=(0, SPACE_SM))

        ctk.CTkButton(
            btn_row,
            text="Close",
            width=80,
            height=32,
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self.dialog.destroy,
        ).pack(side="right")

    def _populate_list(self):
        """Populate the history list."""
        # Clear existing
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.row_frames = []

        if not self.entries:
            empty_label = ctk.CTkLabel(
                self.list_frame,
                text="No transcriptions yet",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=SLATE_400,
            )
            empty_label.pack(pady=SPACE_LG)
            return

        # Show newest first
        for i, entry in enumerate(reversed(self.entries)):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent", height=36)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            # Time column
            timestamp = entry.get("timestamp", "")[:16]  # YYYY-MM-DD HH:MM
            time_lbl = ctk.CTkLabel(
                row,
                text=timestamp,
                width=120,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=SLATE_400,
                anchor="w",
            )
            time_lbl.pack(side="left", padx=SPACE_SM)

            # Text column (truncated)
            text = entry.get("text", "").strip()
            display_text = text[:60] + "..." if len(text) > 60 else text
            text_lbl = ctk.CTkLabel(
                row,
                text=display_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=SLATE_200,
                anchor="w",
            )
            text_lbl.pack(side="left", fill="x", expand=True, padx=SPACE_SM)

            # Store index in reversed order
            actual_index = len(self.entries) - 1 - i

            # Click handler
            def on_click(event, idx=actual_index, frame=row):
                self._select_row(idx, frame)

            row.bind("<Button-1>", on_click)
            time_lbl.bind("<Button-1>", on_click)
            text_lbl.bind("<Button-1>", on_click)

            self.row_frames.append((row, actual_index))

    def _select_row(self, index, frame):
        """Select a row."""
        # Reset all rows
        for row, _ in self.row_frames:
            row.configure(fg_color="transparent")

        # Highlight selected
        frame.configure(fg_color=SLATE_700)
        self.selected_index = index

    def _copy_selected(self):
        """Copy selected transcription to clipboard."""
        if self.selected_index is None:
            messagebox.showinfo("Copy", "Please select a transcription first.")
            return

        text = self.entries[self.selected_index].get("text", "")
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(text)
        self.dialog.update()
        messagebox.showinfo("Copied", "Transcription copied to clipboard.")

    def _export_history(self):
        """Export history to file."""
        if not self.entries:
            messagebox.showinfo("Export", "No history to export.")
            return

        # Format selection dialog
        format_dlg = ctk.CTkToplevel(self.dialog)
        format_dlg.title("Export Format")
        format_dlg.geometry("300x200")
        format_dlg.configure(fg_color=SLATE_900)
        format_dlg.transient(self.dialog)
        format_dlg.grab_set()

        # Center on dialog
        format_dlg.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() - 300) // 2
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() - 200) // 2
        format_dlg.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(format_dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(
            frame,
            text="Select export format:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=SLATE_100,
        ).pack(anchor="w", pady=(0, SPACE_MD))

        format_var = ctk.StringVar(value="txt")
        ctk.CTkRadioButton(frame, text="Plain Text (.txt)", variable=format_var, value="txt",
                           text_color=SLATE_200).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(frame, text="CSV with timestamps (.csv)", variable=format_var, value="csv",
                           text_color=SLATE_200).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(frame, text="JSON with metadata (.json)", variable=format_var, value="json",
                           text_color=SLATE_200).pack(anchor="w", pady=2)

        result = {"format": None}

        def do_export():
            result["format"] = format_var.get()
            format_dlg.destroy()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(SPACE_MD, 0))

        ctk.CTkButton(btn_row, text="Export", width=80, fg_color=PRIMARY,
                      hover_color=PRIMARY_DARK, command=do_export).pack(side="right", padx=(SPACE_SM, 0))
        ctk.CTkButton(btn_row, text="Cancel", width=80, fg_color=SLATE_700,
                      hover_color=SLATE_600, command=format_dlg.destroy).pack(side="right")

        format_dlg.wait_window()

        if not result["format"]:
            return

        # File save dialog
        from tkinter import filedialog
        ext_map = {"txt": ".txt", "csv": ".csv", "json": ".json"}
        file_types = {
            "txt": [("Text files", "*.txt"), ("All files", "*.*")],
            "csv": [("CSV files", "*.csv"), ("All files", "*.*")],
            "json": [("JSON files", "*.json"), ("All files", "*.*")]
        }

        filename = filedialog.asksaveasfilename(
            defaultextension=ext_map[result["format"]],
            filetypes=file_types[result["format"]],
            title="Export History"
        )

        if not filename:
            return

        try:
            fmt = result["format"]
            if fmt == "txt":
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("Transcription History\n")
                    f.write("=" * 60 + "\n\n")
                    for entry in self.entries:
                        ts = entry.get("timestamp", "")
                        text = entry.get("text", "")
                        f.write(f"[{ts}]\n{text}\n\n")
            elif fmt == "csv":
                import csv
                with open(filename, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Text", "Characters"])
                    for entry in self.entries:
                        ts = entry.get("timestamp", "")
                        text = entry.get("text", "")
                        char_count = entry.get("char_count", len(text))
                        writer.writerow([ts, text, char_count])
            elif fmt == "json":
                import json
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump({"entries": self.entries}, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Export Successful", f"History exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export history:\n{str(e)}")

    def _clear_history(self):
        """Clear all history."""
        if not self.entries:
            messagebox.showinfo("Clear History", "No history to clear.")
            return

        if messagebox.askyesno("Clear History", "Delete all transcription history?\n\nThis cannot be undone."):
            import text_processor
            text_processor.TranscriptionHistory.clear_on_disk()
            self.entries = []
            self._populate_list()
            messagebox.showinfo("Cleared", "Transcription history cleared.")


class SettingsWindow:
    """Settings window matching the HTML mockup exactly."""

    def __init__(self, current_config, on_save_callback=None):
        self.config = current_config or {}
        self.on_save_callback = on_save_callback
        self.window = None
        self.nav_items = {}
        self.nav_icons = {}  # Will hold CTkImage objects for nav icons
        self.sections = {}
        self.current_section = "general"

        # Audio test state
        self.noise_test_running = False
        self.noise_stream = None
        self.meter_gradient_photo = None  # Audio meter gradient image

        # Custom data
        self.custom_dictionary = self.config.get("custom_dictionary", {})
        self.custom_vocabulary = self.config.get("custom_vocabulary", [])
        self.custom_commands = self.config.get("custom_commands", {})

        # Autosave state (debounce managers initialized in show())
        self._text_debounce = None
        self._slider_debounce = None
        self._status_label = None
        self._status_hide_id = None

        # Lazy loading for About section
        self._sys_info_label = None
        self._sys_info_loaded = False

    def show(self):
        """Show the settings window."""
        self.window = ctk.CTk()
        self.window.title("MurmurTone Settings")
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.window.resizable(True, True)
        self.window.minsize(800, 500)
        self.window.configure(fg_color=SLATE_900)

        # Try to set icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except Exception:
            pass

        # Load navigation icons
        self.nav_icons = load_nav_icons()

        # Initialize debounce managers for autosave
        self._text_debounce = DebounceManager(self.window, self._autosave, delay_ms=1500)
        self._slider_debounce = DebounceManager(self.window, self._autosave, delay_ms=300)

        # Build UI
        self._create_sidebar()
        self._create_content_area()

        # Create all sections
        self._create_general_section()
        self._create_audio_section()
        self._create_recognition_section()
        self._create_text_section()
        self._create_advanced_section()
        self._create_about_section()

        # Show initial section
        self._show_section("general")

        # Ensure window is visible and focused
        self.window.update_idletasks()  # Process geometry

        # Center on screen (with fallback position)
        try:
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = max(50, (screen_width - WINDOW_WIDTH) // 2)
            y = max(50, (screen_height - WINDOW_HEIGHT) // 2)
        except Exception:
            x, y = 100, 100  # Fallback position
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # Force window to be visible
        self.window.state('normal')  # Ensure not minimized/maximized
        self.window.deiconify()
        self.window.update()

        # Force to front (Windows-specific)
        self.window.attributes('-topmost', True)
        self.window.lift()
        self.window.focus_force()
        self.window.after(200, lambda: self.window.attributes('-topmost', False))

        # Setup keyboard navigation for accessibility
        self._setup_keyboard_navigation()

        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.mainloop()

    def _create_sidebar(self):
        """Create sidebar - matches mockup exactly."""
        self.sidebar = ctk.CTkFrame(
            self.window,
            width=SIDEBAR_WIDTH,
            fg_color=SLATE_800,
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # "Settings" title - 20px bold, SLATE_100
        title = ctk.CTkLabel(
            self.sidebar,
            text="Settings",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=SLATE_100,
            anchor="w",
        )
        title.pack(fill="x", padx=SPACE_LG, pady=(SPACE_LG, SPACE_XL))

        # Navigation items with PNG icons
        nav_items_data = [
            ("general", "General"),
            ("audio", "Audio"),
            ("recognition", "Recognition"),
            ("text", "Text"),
            ("advanced", "Advanced"),
            ("about", "About"),
        ]

        for section_id, label in nav_items_data:
            icon = self.nav_icons.get(section_id)
            self._add_nav_item(section_id, label, icon)

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Footer separator
        sep = ctk.CTkFrame(self.sidebar, fg_color=SLATE_600, height=1)
        sep.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_MD))

        # Autosave status indicator
        self._status_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SUCCESS,
            anchor="w",
            height=16,
        )
        self._status_label.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_XS))

        # Version text - 11px, SLATE_500
        version = ctk.CTkLabel(
            self.sidebar,
            text=f"MurmurTone v{config.VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
            anchor="w",
        )
        version.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_LG))

    def _add_nav_item(self, section_id, label, icon):
        """Add a navigation item with PNG icon."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=label,
            image=icon,  # CTkImage object
            compound="left",  # Icon on the left of text
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color=SLATE_700,
            text_color=SLATE_300,
            command=lambda: self._show_section(section_id),
        )
        btn.pack(fill="x", padx=SPACE_MD, pady=2)
        self.nav_items[section_id] = btn

    def _create_content_area(self):
        """Create content area - matches mockup exactly."""
        self.content_area = ctk.CTkFrame(
            self.window,
            fg_color=SLATE_900,
            corner_radius=0,
        )
        self.content_area.pack(side="right", fill="both", expand=True)

        # Page header container
        header_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header_container.pack(fill="x", padx=SPACE_XL, pady=(SPACE_XL, 0))

        # Header row: title on left, X button on right
        header_row = ctk.CTkFrame(header_container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, SPACE_MD))

        self.page_title = ctk.CTkLabel(
            header_row,
            text="General",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=SLATE_100,
            anchor="w",
        )
        self.page_title.pack(side="left")

        # Border below header
        border = ctk.CTkFrame(header_container, fg_color=SLATE_600, height=2, corner_radius=0)
        border.pack(fill="x")
        border.pack_propagate(False)
        border.grid_propagate(False)

        # Scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.content_area,
            fg_color="transparent",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACE_XL, pady=SPACE_MD)

        # Note: Save/Cancel buttons removed - using autosave instead

    def _show_section(self, section_id):
        """Show a specific section."""
        # Update nav item states
        for nav_id, btn in self.nav_items.items():
            if nav_id == section_id:
                btn.configure(fg_color=PRIMARY, text_color="white", hover_color=PRIMARY_DARK)
            else:
                btn.configure(fg_color="transparent", text_color=SLATE_300, hover_color=SLATE_700)

        # Hide all sections
        for section in self.sections.values():
            section.pack_forget()

        # Show selected section
        if section_id in self.sections:
            self.sections[section_id].pack(fill="both", expand=True)
            # Reset scroll position to top when switching tabs
            self.scroll_frame._parent_canvas.yview_moveto(0)

        # Update page title
        titles = {
            "general": "General",
            "audio": "Audio",
            "recognition": "Recognition",
            "text": "Text",
            "advanced": "Advanced",
            "about": "About",
        }
        self.page_title.configure(text=titles.get(section_id, section_id.title()))
        self.current_section = section_id

        # Lazy-load system info when About is first shown
        if section_id == "about" and not self._sys_info_loaded:
            self.window.after(10, self._populate_system_info)

    # =========================================================================
    # SECTION BUILDERS
    # =========================================================================

    def _create_section_header(self, parent, title, description=None, show_divider=False):
        """Create a section header matching mockup exactly.

        Returns a frame for adding controls to.
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_MD))

        # Optional divider line above section
        if show_divider:
            divider = ctk.CTkFrame(container, fg_color=SLATE_700, height=2, corner_radius=0)
            divider.pack(fill="x", pady=(SPACE_XS, SPACE_XL))

        # Section header - 14px semibold, SLATE_200
        if title:
            header = ctk.CTkLabel(
                container,
                text=title,
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                text_color=SLATE_200,
                anchor="w",
            )
            header.pack(fill="x")

        # Description - 12px, SLATE_400
        if description:
            desc = ctk.CTkLabel(
                container,
                text=description,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=SLATE_400,
                anchor="w",
            )
            desc.pack(fill="x", pady=(SPACE_XS, 0))

        # Content frame with proper spacing
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(fill="x", pady=(SPACE_SM, SPACE_SM))

        return content

    def _create_toggle_setting(self, parent, label, help_text=None, variable=None, command=None):
        """Create toggle setting matching mockup: [toggle] [label + help on right]."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, SPACE_SM))

        # Wrap command to include autosave
        def on_toggle():
            if command:
                command()
            self._autosave()

        # Toggle switch on left - 40x22
        switch = ctk.CTkSwitch(
            row,
            text="",
            variable=variable,
            command=on_toggle,
            width=40,
            height=22,
            switch_width=40,
            switch_height=22,
            corner_radius=11,
            button_color="white",
            button_hover_color="white",
            fg_color=SLATE_600,
            progress_color=PRIMARY,
        )
        switch.pack(side="left", anchor="n", pady=(2, 0))

        # Text content on right
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", anchor="n", padx=(SPACE_MD, 0), fill="x", expand=True)

        # Label - 13px, SLATE_200, tight height
        lbl = ctk.CTkLabel(
            text_frame,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
            height=16,
        )
        lbl.pack(fill="x")

        # Help text - 11px, SLATE_500, tight height
        if help_text:
            help_lbl = ctk.CTkLabel(
                text_frame,
                text=help_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=SLATE_500,
                anchor="w",
                height=14,
            )
            help_lbl.pack(fill="x")

        return switch

    def _create_labeled_dropdown(self, parent, label, values, variable, help_text=None, width=160, command=None):
        """Create labeled dropdown: label above, dropdown below, help below."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_SM))

        # Label - 13px, SLATE_200
        lbl = ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        lbl.pack(fill="x")

        # Wrap command to include autosave
        def on_dropdown_change(choice):
            if command:
                command(choice)
            self._autosave()

        # Dropdown - matches mockup styling
        dropdown = ctk.CTkComboBox(
            container,
            values=values,
            variable=variable,
            command=on_dropdown_change,
            width=width,
            height=36,
            corner_radius=12,
            border_width=1,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            button_color=SLATE_700,
            button_hover_color=SLATE_600,
            dropdown_fg_color=SLATE_700,
            dropdown_hover_color=SLATE_600,
            dropdown_text_color=SLATE_200,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="readonly",
        )
        dropdown.pack(anchor="w", pady=(SPACE_XS, 0))

        # Add toggle behavior, hand cursor, and make entire combobox clickable
        make_combobox_clickable(dropdown)

        # Help text
        help_lbl = None
        if help_text:
            help_lbl = ctk.CTkLabel(
                container,
                text=help_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=SLATE_500,
                anchor="w",
            )
            help_lbl.pack(fill="x", pady=(SPACE_XS, 0))

        return dropdown, help_lbl

    def _create_labeled_entry(self, parent, label, variable, help_text=None, width=80):
        """Create labeled entry: label above, entry below, help below."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_SM))

        # Label
        lbl = ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        lbl.pack(fill="x")

        # Entry
        entry = ctk.CTkEntry(
            container,
            textvariable=variable,
            width=width,
            height=36,
            corner_radius=8,
            border_width=1,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
        )
        entry.pack(anchor="w", pady=(SPACE_XS, 0))

        # Debounced autosave on text change
        def on_entry_change(*args):
            self._text_debounce.schedule()

        def on_focus_out(event):
            self._text_debounce.flush()

        variable.trace_add("write", on_entry_change)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<Return>", lambda e: self._text_debounce.flush())

        # Help text
        if help_text:
            help_lbl = ctk.CTkLabel(
                container,
                text=help_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=SLATE_500,
                anchor="w",
            )
            help_lbl.pack(fill="x", pady=(SPACE_XS, 0))

        return entry

    def _create_checkbox_setting(self, parent, label, variable, command=None):
        """Create checkbox setting matching mockup."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, SPACE_SM))

        # Wrap command to include autosave
        def on_checkbox():
            if command:
                command()
            self._autosave()

        checkbox = ctk.CTkCheckBox(
            row,
            text=label,
            variable=variable,
            command=on_checkbox,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            border_color=SLATE_500,
            checkmark_color="white",
            corner_radius=6,
            border_width=2,
            width=18,
            height=18,
        )
        checkbox.pack(anchor="w")

        return checkbox

    def _create_hotkey_button(self, parent, initial_hotkey):
        """Create hotkey button matching mockup: [badge] Change."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_SM))

        # Label above
        lbl = ctk.CTkLabel(
            container,
            text="Push-to-Talk Hotkey",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        lbl.pack(fill="x")

        # Button with badge inside
        btn_frame = ctk.CTkFrame(
            container,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            border_width=1,
            corner_radius=8,
        )
        btn_frame.pack(anchor="w", pady=(SPACE_XS, 0))

        inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner.pack(padx=SPACE_LG, pady=SPACE_SM)

        # Hotkey badge
        self.hotkey_badge = ctk.CTkLabel(
            inner,
            text=self._format_hotkey(initial_hotkey),
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=SLATE_300,
            fg_color=SLATE_700,
            corner_radius=8,
            padx=8,
            pady=2,
        )
        self.hotkey_badge.pack(side="left")

        # "Change" text
        change_lbl = ctk.CTkLabel(
            inner,
            text="Change",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
        )
        change_lbl.pack(side="left", padx=(SPACE_SM, 0))

        # Make clickable
        self.hotkey = initial_hotkey
        self.capturing = False
        for widget in [btn_frame, inner, self.hotkey_badge, change_lbl]:
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda e: self._start_hotkey_capture())
            widget.bind("<Enter>", lambda e: btn_frame.configure(fg_color=SLATE_700, border_color=SLATE_500))
            widget.bind("<Leave>", lambda e: btn_frame.configure(fg_color=SLATE_800, border_color=SLATE_600) if not self.capturing else None)

        self.hotkey_btn_frame = btn_frame

        # Help text (updated dynamically based on recording mode)
        self.hotkey_help_label = ctk.CTkLabel(
            container,
            text="Press and hold to record audio",  # Default, updated by _update_hotkey_help_text
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
            anchor="w",
        )
        self.hotkey_help_label.pack(fill="x", pady=(SPACE_XS, 0))

    def _format_hotkey(self, hotkey):
        """Format hotkey for display."""
        if not hotkey:
            return "Not set"
        if isinstance(hotkey, dict):
            return config.hotkey_to_string(hotkey)
        parts = hotkey.split("+")
        formatted = [p.replace("_", " ").title() for p in parts]
        return " + ".join(formatted)

    def _update_hotkey_help_text(self, mode_label=None):
        """Update hotkey help text based on recording mode."""
        if mode_label is None:
            mode_label = self.mode_var.get() if hasattr(self, 'mode_var') else "Push-to-Talk"

        help_texts = {
            "Push-to-Talk": "Press and hold to record audio",
            "Toggle": "Press to start recording, press again to stop",
            "Auto-stop": "Press to start recording, stops after silence",
        }
        text = help_texts.get(mode_label, "Press and hold to record audio")

        if hasattr(self, 'hotkey_help_label'):
            self.hotkey_help_label.configure(text=text)

    def _update_paste_help_text(self, mode_label=None):
        """Update paste method help text based on selected mode."""
        if mode_label is None:
            mode_label = self.paste_mode_var.get() if hasattr(self, 'paste_mode_var') else "Clipboard"

        help_texts = {
            "Clipboard": "Copies text to clipboard and pastes with Ctrl+V",
            "Type": "Simulates typing each character (slower but more compatible)",
        }
        text = help_texts.get(mode_label, "How text is inserted")

        if hasattr(self, 'paste_help_label') and self.paste_help_label:
            self.paste_help_label.configure(text=text)

    def _start_hotkey_capture(self):
        """Start capturing a hotkey."""
        if self.capturing:
            return
        self.capturing = True
        self.hotkey_btn_frame.configure(fg_color=PRIMARY, border_color=PRIMARY)
        self.hotkey_badge.configure(text="Press any key...")

        try:
            from pynput import keyboard

            def on_press(key):
                try:
                    if hasattr(key, "char") and key.char:
                        key_name = key.char.lower()
                    else:
                        key_name = key.name.lower()
                    self.hotkey = key_name
                    self.hotkey_badge.configure(text=self._format_hotkey(key_name))
                except AttributeError:
                    pass
                self._stop_hotkey_capture()
                return False

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
        except ImportError:
            self.hotkey_badge.configure(text="pynput not installed")
            self._stop_hotkey_capture()

    def _stop_hotkey_capture(self):
        """Stop capturing."""
        self.capturing = False
        self.hotkey_btn_frame.configure(fg_color=SLATE_800, border_color=SLATE_600)
        if hasattr(self, 'listener') and self.listener:
            self.listener.stop()
            self.listener = None
        # Autosave after hotkey capture (use after() to ensure main thread)
        if self.window:
            self.window.after(100, self._autosave)

    def _create_button(self, parent, text, command=None, style="secondary", width=None):
        """Create a button matching mockup styles."""
        if style == "primary":
            fg = PRIMARY
            hover = PRIMARY_DARK
            text_color = "white"
            border = PRIMARY
        else:  # secondary
            fg = SLATE_800
            hover = SLATE_700
            text_color = SLATE_200
            border = SLATE_600

        btn = ctk.CTkButton(
            parent,
            text=text,
            width=width or 120,
            height=36,
            corner_radius=8,
            fg_color=fg,
            hover_color=hover,
            border_color=border,
            border_width=1,
            text_color=text_color,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=command,
        )
        return btn

    def _create_status_dot(self, parent, color=SLATE_500):
        """Create a circular status indicator matching mockup spec (10px circle)."""
        dot = ctk.CTkFrame(
            parent,
            width=10,
            height=10,
            corner_radius=5,  # Circle: radius = width/2
            fg_color=color,
        )
        dot.pack_propagate(False)  # Maintain exact size
        dot.pack(side="left", padx=(0, SPACE_XS))  # Add space after dot
        return dot

    def _create_meter_gradient(self, width, height):
        """Create gradient image for audio meter (green → orange → red)."""
        from PIL import Image, ImageDraw, ImageTk

        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Draw gradient: green -> orange -> red (matches mockup line 575)
        for x in range(width):
            if x < width * 0.7:  # 0-70%: green (#10b981) to orange (#f59e0b)
                ratio = x / (width * 0.7)
                r = int(16 + (245 - 16) * ratio)
                g = int(185 + (158 - 185) * ratio)
                b = int(129 + (11 - 129) * ratio)
            else:  # 70-100%: orange to red (#ef4444)
                ratio = (x - width * 0.7) / (width * 0.3)
                r = int(245 + (239 - 245) * ratio)
                g = int(158 + (68 - 158) * ratio)
                b = int(11 + (68 - 11) * ratio)

            draw.line([(x, 0), (x, height)], fill=(r, g, b))

        return ImageTk.PhotoImage(img)

    # =========================================================================
    # GENERAL SECTION
    # =========================================================================

    def _create_general_section(self):
        """Create General settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["general"] = section

        # Recording section (first section - no separator)
        recording = self._create_section_header(section, "Recording", "Configure how voice recording works")

        # Hotkey
        self._create_hotkey_button(recording, self.config.get("hotkey", "scroll_lock"))

        # Recording mode (use display labels)
        mode_value = self.config.get("recording_mode", "push_to_talk")
        self.mode_var = ctk.StringVar(value=RECORDING_MODE_LABELS.get(mode_value, "Push-to-Talk"))
        self._create_labeled_dropdown(
            recording,
            "Recording Mode",
            values=list(RECORDING_MODE_LABELS.values()),
            variable=self.mode_var,
            help_text="How recording starts and stops",
            width=160,
            command=self._update_hotkey_help_text,
        )
        # Set initial hotkey help text based on loaded recording mode
        self._update_hotkey_help_text()

        # Language
        self.lang_var = ctk.StringVar(
            value=settings_logic.language_code_to_label(self.config.get("language", "auto"))
        )
        self._create_labeled_dropdown(
            recording,
            "Language",
            values=settings_logic.get_language_labels(),
            variable=self.lang_var,
            help_text="Primary transcription language",
            width=160,
        )

        # Output section
        output = self._create_section_header(section, "Output", "Control what happens with transcribed text", show_divider=True)

        # Auto-paste toggle
        self.autopaste_var = ctk.BooleanVar(value=self.config.get("auto_paste", True))
        self._create_toggle_setting(
            output,
            "Auto-paste transcribed text",
            help_text="Automatically paste text into the active application",
            variable=self.autopaste_var,
        )

        # Paste method (use display labels)
        paste_value = self.config.get("paste_mode", "clipboard")
        self.paste_mode_var = ctk.StringVar(value=PASTE_MODE_LABELS.get(paste_value, "Clipboard"))
        _, self.paste_help_label = self._create_labeled_dropdown(
            output,
            "Paste Method",
            values=list(PASTE_MODE_LABELS.values()),
            variable=self.paste_mode_var,
            help_text="How text is inserted",
            width=120,
            command=self._update_paste_help_text,
        )
        # Set initial paste help text based on loaded mode
        self._update_paste_help_text()

        # Preview Window section
        preview = self._create_section_header(section, "Preview Window", "Floating overlay showing transcription progress", show_divider=True)

        # Show preview toggle
        self.preview_enabled_var = ctk.BooleanVar(value=self.config.get("preview_enabled", True))
        self._create_toggle_setting(
            preview,
            "Show preview window",
            help_text="Display a small overlay during transcription",
            variable=self.preview_enabled_var,
        )

        # Preview position (use display labels)
        pos_value = self.config.get("preview_position", "bottom_right")
        self.preview_position_var = ctk.StringVar(value=PREVIEW_POSITION_LABELS.get(pos_value, "Bottom Right"))
        self._create_labeled_dropdown(
            preview,
            "Position",
            values=list(PREVIEW_POSITION_LABELS.values()),
            variable=self.preview_position_var,
            width=140,
        )

        # Preview theme (use display labels)
        theme_value = self.config.get("preview_theme", "dark")
        self.preview_theme_var = ctk.StringVar(value=PREVIEW_THEME_LABELS.get(theme_value, "Dark"))
        self._create_labeled_dropdown(
            preview,
            "Theme",
            values=list(PREVIEW_THEME_LABELS.values()),
            variable=self.preview_theme_var,
            width=100,
        )

        # Auto-hide delay
        self.preview_delay_var = ctk.StringVar(value=str(self.config.get("preview_auto_hide_delay", 2.0)))
        self._create_labeled_entry(
            preview,
            "Auto-hide Delay",
            variable=self.preview_delay_var,
            help_text="Seconds before overlay disappears",
            width=80,
        )

        # Preview font size
        self.preview_font_size_var = ctk.IntVar(value=self.config.get("preview_font_size", 11))

        # Startup section
        startup = self._create_section_header(section, "Startup", show_divider=True)

        self.startup_var = ctk.BooleanVar(value=self.config.get("start_with_windows", False))
        self._create_toggle_setting(
            startup,
            "Start with Windows",
            help_text="Launch automatically on login",
            variable=self.startup_var,
        )

    # =========================================================================
    # AUDIO SECTION
    # =========================================================================

    def _create_audio_section(self):
        """Create Audio settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["audio"] = section

        # Input Device section (first section - no separator)
        device = self._create_section_header(section, "Input Device", "Select and configure your microphone")

        # Microphone with refresh button
        mic_container = ctk.CTkFrame(device, fg_color="transparent")
        mic_container.pack(fill="x", pady=(0, SPACE_LG))

        mic_lbl = ctk.CTkLabel(
            mic_container,
            text="Microphone",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        mic_lbl.pack(fill="x")

        mic_row = ctk.CTkFrame(mic_container, fg_color="transparent")
        mic_row.pack(fill="x", pady=(SPACE_SM, 0))

        self.devices_list = settings_logic.get_input_devices()
        display_names = [name for name, _ in self.devices_list]
        current_device = settings_logic.get_device_display_name(
            self.config.get("input_device"),
            self.devices_list,
        )

        self.device_var = ctk.StringVar(value=current_device)
        self.device_combo = ctk.CTkComboBox(
            mic_row,
            values=display_names,
            variable=self.device_var,
            command=lambda choice: self._autosave(),
            width=280,
            height=36,
            corner_radius=12,
            border_width=1,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            button_color=SLATE_700,
            button_hover_color=SLATE_600,
            dropdown_fg_color=SLATE_700,
            dropdown_hover_color=SLATE_600,
            dropdown_text_color=SLATE_200,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="readonly",
        )
        self.device_combo.pack(side="left")

        # Add toggle behavior, hand cursor, and make entire combobox clickable
        make_combobox_clickable(self.device_combo)

        refresh_btn = self._create_button(mic_row, "Refresh", self.refresh_devices, width=80)
        refresh_btn.pack(side="left", padx=(SPACE_SM, 0))

        # Sample rate
        sample_rate = self.config.get("sample_rate", 16000)
        self.rate_var = ctk.StringVar(
            value=SAMPLE_RATE_OPTIONS.get(sample_rate, SAMPLE_RATE_OPTIONS[16000])
        )
        self._create_labeled_dropdown(
            device,
            "Sample Rate",
            values=list(SAMPLE_RATE_OPTIONS.values()),
            variable=self.rate_var,
            width=280,
        )

        # Noise Gate section
        gate = self._create_section_header(section, "Noise Gate", "Filter out background noise below a threshold", show_divider=True)

        self.noise_gate_var = ctk.BooleanVar(value=self.config.get("noise_gate_enabled", False))
        self._create_toggle_setting(
            gate,
            "Enable noise gate",
            help_text="Ignore audio below the threshold level",
            variable=self.noise_gate_var,
        )

        # Threshold meter
        threshold_container = ctk.CTkFrame(gate, fg_color="transparent")
        threshold_container.pack(fill="x", pady=(0, SPACE_LG))

        threshold_lbl = ctk.CTkLabel(
            threshold_container,
            text="Threshold Level",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        threshold_lbl.pack(fill="x")

        self.noise_threshold_var = ctk.IntVar(value=self.config.get("noise_gate_threshold_db", -40))

        meter_row = ctk.CTkFrame(threshold_container, fg_color="transparent")
        meter_row.pack(fill="x", pady=(SPACE_SM, 0))

        self.meter_width = 300
        self.meter_height = 20
        self.noise_level_canvas = tk.Canvas(
            meter_row,
            width=self.meter_width,
            height=self.meter_height,
            bg=SLATE_700,
            highlightthickness=1,
            highlightbackground=SLATE_600,
            cursor="hand2",
        )
        self.noise_level_canvas.pack(side="left")

        # Gradient fill (green → orange → red)
        if not self.meter_gradient_photo:
            self.meter_gradient_photo = self._create_meter_gradient(self.meter_width, self.meter_height)

        self.meter_gradient_item = self.noise_level_canvas.create_image(
            0, 0, anchor="nw", image=self.meter_gradient_photo
        )

        # Level mask - covers the gradient (fully covered when idle, reveals left portion during test)
        self.noise_level_bar = self.noise_level_canvas.create_rectangle(
            0, 0, self.meter_width, self.meter_height,
            fill=SLATE_800, width=0, state="normal"
        )

        # Threshold marker
        thresh_x = self._db_to_x(self.noise_threshold_var.get())
        self.threshold_marker = self.noise_level_canvas.create_line(
            thresh_x, 0, thresh_x, self.meter_height, fill=PRIMARY_LIGHT, width=3
        )

        self.noise_level_canvas.bind("<Button-1>", self._on_threshold_click)
        self.noise_level_canvas.bind("<B1-Motion>", self._on_threshold_drag)

        self.threshold_label = ctk.CTkLabel(
            meter_row,
            text=f"{self.noise_threshold_var.get()} dB",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_300,
            width=60,
        )
        self.threshold_label.pack(side="left", padx=(SPACE_SM, 0))

        threshold_help = ctk.CTkLabel(
            threshold_container,
            text="Click or drag to adjust threshold",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
            anchor="w",
        )
        threshold_help.pack(fill="x", pady=(SPACE_XS, 0))

        # Test button
        self.noise_test_btn = self._create_button(gate, "Test Microphone", self.toggle_noise_test, width=140)
        self.noise_test_btn.pack(anchor="w", pady=(0, SPACE_SM))

        # Audio Feedback section
        feedback = self._create_section_header(section, "Audio Feedback", "Sound notifications for recording events", show_divider=True)

        self.feedback_var = ctk.BooleanVar(value=self.config.get("audio_feedback", True))
        self._create_toggle_setting(
            feedback,
            "Enable sounds",
            help_text="Play audio cues for recording states",
            variable=self.feedback_var,
        )

        # Sound checkboxes
        self.sound_processing_var = ctk.BooleanVar(value=self.config.get("sound_processing", True))
        self._create_checkbox_setting(feedback, "Processing sound", self.sound_processing_var)

        self.sound_success_var = ctk.BooleanVar(value=self.config.get("sound_success", True))
        self._create_checkbox_setting(feedback, "Success sound", self.sound_success_var)

        self.sound_error_var = ctk.BooleanVar(value=self.config.get("sound_error", True))
        self._create_checkbox_setting(feedback, "Error sound", self.sound_error_var)

        self.sound_command_var = ctk.BooleanVar(value=self.config.get("sound_command", True))
        self._create_checkbox_setting(feedback, "Command sound", self.sound_command_var)

        # Volume slider
        volume_container = ctk.CTkFrame(feedback, fg_color="transparent")
        volume_container.pack(fill="x", pady=(SPACE_MD, 0))

        volume_lbl = ctk.CTkLabel(
            volume_container,
            text="Volume",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        volume_lbl.pack(fill="x")

        slider_row = ctk.CTkFrame(volume_container, fg_color="transparent")
        slider_row.pack(fill="x", pady=(SPACE_SM, 0))

        self.volume_var = ctk.IntVar(value=self.config.get("audio_feedback_volume", 100))

        slider = ctk.CTkSlider(
            slider_row,
            from_=0,
            to=100,
            variable=self.volume_var,
            width=150,
            height=6,  # Matches mockup line 492 (thin track)
            fg_color=SLATE_600,
            progress_color=PRIMARY,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
        )
        slider.pack(side="left")

        self.volume_label = ctk.CTkLabel(
            slider_row,
            text=f"{self.volume_var.get()}%",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_300,
            width=50,
        )
        self.volume_label.pack(side="left", padx=(SPACE_MD, 0))

        def update_volume_label(*args):
            self.volume_label.configure(text=f"{self.volume_var.get()}%")
            # Schedule debounced autosave
            self._slider_debounce.schedule()
        self.volume_var.trace_add("write", update_volume_label)

    def _db_to_x(self, db):
        """Convert dB value to x position on meter."""
        # Range: -80 to 0 dB
        normalized = (db + 80) / 80
        return int(normalized * self.meter_width)

    def _x_to_db(self, x):
        """Convert x position to dB value."""
        normalized = x / self.meter_width
        return int(normalized * 80 - 80)

    def _on_threshold_click(self, event):
        """Handle click on threshold meter."""
        db = self._x_to_db(event.x)
        db = max(-80, min(0, db))
        self.noise_threshold_var.set(db)
        self.noise_level_canvas.coords(
            self.threshold_marker,
            event.x, 0, event.x, self.meter_height
        )
        self.threshold_label.configure(text=f"{db} dB")
        # Schedule debounced autosave (for drag operations)
        self._slider_debounce.schedule()

    def _on_threshold_drag(self, event):
        """Handle drag on threshold meter."""
        self._on_threshold_click(event)

    def refresh_devices(self):
        """Refresh the device list."""
        self.devices_list = settings_logic.get_input_devices()
        display_names = [name for name, _ in self.devices_list]
        self.device_combo.configure(values=display_names)
        if display_names:
            self.device_var.set(display_names[0])

    def toggle_noise_test(self):
        """Toggle microphone test."""
        if self.noise_test_running:
            self.stop_noise_test()
        else:
            self.start_noise_test()

    def start_noise_test(self):
        """Start microphone test with real audio monitoring."""
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            messagebox.showerror("Error", "sounddevice or numpy not installed")
            return

        self.noise_test_running = True
        self.noise_test_btn.configure(text="Stop Test", fg_color=ERROR, hover_color=ERROR_DARK)

        # Get selected device
        device_info = self.get_selected_device_info()
        device_index = None
        if device_info:
            device_index = device_info.get("index")

        def audio_callback(indata, frames, time_info, status):
            """Process audio data and update meter."""
            if not self.noise_test_running:
                return
            # Calculate RMS level
            rms = np.sqrt(np.mean(indata**2))
            # Convert to dB (with floor at -80)
            if rms > 0:
                db = 20 * np.log10(rms)
                db = max(-80, min(0, db))
            else:
                db = -80
            # Schedule UI update on main thread
            self.window.after(0, lambda: self._update_noise_meter(db))

        try:
            self.audio_stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=16000,
                blocksize=1024,
                callback=audio_callback,
            )
            self.audio_stream.start()
        except Exception as e:
            self.noise_test_running = False
            self.noise_test_btn.configure(text="Test Microphone", fg_color=SLATE_800, hover_color=SLATE_700)
            messagebox.showerror("Error", f"Could not open audio device: {e}")

    def _update_noise_meter(self, db):
        """Update the noise meter display with current level."""
        if not self.noise_test_running:
            return
        x = self._db_to_x(db)
        # Update mask to cover inactive portion (from current level to right edge)
        self.noise_level_canvas.coords(self.noise_level_bar, x, 0, self.meter_width, self.meter_height)
        self.noise_level_canvas.itemconfigure(self.noise_level_bar, state="normal")

    def stop_noise_test(self):
        """Stop microphone test."""
        self.noise_test_running = False
        self.noise_test_btn.configure(text="Test Microphone", fg_color=SLATE_800, hover_color=SLATE_700)

        # Stop audio stream
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

        # Reset mask to cover entire gradient (hide the meter)
        if hasattr(self, 'noise_level_bar'):
            self.noise_level_canvas.coords(self.noise_level_bar, 0, 0, self.meter_width, self.meter_height)

    # =========================================================================
    # RECOGNITION SECTION
    # =========================================================================

    def _create_recognition_section(self):
        """Create Recognition settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["recognition"] = section

        # Whisper Model section (first section - no separator)
        model = self._create_section_header(section, "Whisper Model", "Recommended for most users")

        # Model var stores internal name (tiny, base, etc.)
        # Dropdown displays friendly names (Quick, Standard, etc.)
        initial_model = self.config.get("model_size", "tiny")
        self.model_var = ctk.StringVar(value=initial_model)

        # Create display names list in same order as MODEL_OPTIONS
        display_names = [config.MODEL_DISPLAY_NAMES.get(m, m) for m in config.MODEL_OPTIONS]
        initial_display = config.MODEL_DISPLAY_NAMES.get(initial_model, initial_model)
        self._model_display_var = ctk.StringVar(value=initial_display)

        def on_model_display_changed(display_name):
            # Convert display name back to internal name
            internal_name = config.MODEL_INTERNAL_NAMES.get(display_name, display_name)
            self.model_var.set(internal_name)
            self._on_model_changed()

        self._create_labeled_dropdown(
            model,
            "Model Size",
            values=display_names,
            variable=self._model_display_var,
            help_text="Larger models are more accurate but slower",
            width=160,
            command=on_model_display_changed,
        )

        # Learn more link (below help text)
        learn_more_link = ctk.CTkLabel(
            model,
            text="Learn more about models",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PRIMARY,
            cursor="hand2",
            anchor="w",
        )
        learn_more_link.pack(fill="x", pady=(0, SPACE_SM))
        learn_more_link.bind("<Button-1>", lambda e: webbrowser.open("https://murmurtone.com/docs/model-guide.html"))

        # Model status row
        self.model_status_frame = ctk.CTkFrame(model, fg_color="transparent")
        self.model_status_frame.pack(fill="x", pady=(0, SPACE_MD))

        model_status_row = ctk.CTkFrame(self.model_status_frame, fg_color="transparent")
        model_status_row.pack(fill="x")

        # Status dot
        self.model_status_dot = self._create_status_dot(model_status_row, SUCCESS)

        self.model_status_text = ctk.CTkLabel(
            model_status_row,
            text="Checking...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_300,
        )
        self.model_status_text.pack(side="left")

        # Download Model button (hidden by default, shown when needed)
        self.download_model_frame = ctk.CTkFrame(model, fg_color="transparent")
        self.download_model_btn = ctk.CTkButton(
            self.download_model_frame,
            text="Download Model",
            command=self._download_selected_model,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            corner_radius=6,
            height=32,
        )
        self.download_model_btn.pack(side="left")

        self.download_model_size_label = ctk.CTkLabel(
            self.download_model_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
        )
        self.download_model_size_label.pack(side="left", padx=(SPACE_SM, 0))

        # Pack frame now, will be hidden/shown by refresh_model_status
        self.download_model_frame.pack(fill="x", pady=(SPACE_SM, 0))

        # Refresh model status on load
        self.window.after(100, self.refresh_model_status)

        self.silence_var = ctk.StringVar(value=str(self.config.get("silence_duration_sec", 2.0)))
        self._create_labeled_entry(
            model,
            "Silence Duration",
            variable=self.silence_var,
            help_text="Seconds of silence before auto-stop",
            width=80,
        )

        # GPU Acceleration section
        gpu = self._create_section_header(section, "GPU Acceleration", "Use NVIDIA graphics card for faster processing", show_divider=True)

        # GPU status
        self.gpu_status_frame = ctk.CTkFrame(gpu, fg_color="transparent")
        self.gpu_status_frame.pack(fill="x", pady=(0, SPACE_MD))

        status_row = ctk.CTkFrame(self.gpu_status_frame, fg_color="transparent")
        status_row.pack(fill="x")

        # Status dot
        self.gpu_status_dot = self._create_status_dot(status_row, SUCCESS)

        self.gpu_status_text = ctk.CTkLabel(
            status_row,
            text="Checking...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_300,
        )
        self.gpu_status_text.pack(side="left")

        refresh_gpu = self._create_button(status_row, "Refresh", self.refresh_gpu_status, width=80)
        refresh_gpu.configure(fg_color="transparent", border_width=0)
        refresh_gpu.pack(side="left", padx=(SPACE_LG, 0))

        # Install GPU Support button (hidden by default, shown when needed)
        self.install_gpu_frame = ctk.CTkFrame(gpu, fg_color="transparent")
        self.install_gpu_btn = ctk.CTkButton(
            self.install_gpu_frame,
            text="Install GPU Support",
            command=self.install_gpu_support,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            corner_radius=6,
            height=32,
        )
        self.install_gpu_btn.pack(side="left")

        install_help = ctk.CTkLabel(
            self.install_gpu_frame,
            text="?",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=SLATE_500,
            cursor="question_arrow",
        )
        install_help.pack(side="left", padx=(SPACE_SM, 0))
        # Pack it now to establish position, will be hidden/shown by refresh_gpu_status
        self.install_gpu_frame.pack(fill="x", pady=(SPACE_SM, 0))

        # Processing mode
        processing_mode = self.config.get("processing_mode", "auto")
        mode_label = config.PROCESSING_MODE_LABELS.get(processing_mode, "Auto")
        self.processing_mode_var = ctk.StringVar(value=mode_label)
        self._create_labeled_dropdown(
            gpu,
            "Processing Mode",
            values=list(config.PROCESSING_MODE_LABELS.values()),
            variable=self.processing_mode_var,
            help_text="Auto uses GPU if available, otherwise CPU",
            width=160,
        )

        # Refresh GPU status on load
        self.window.after(100, self.refresh_gpu_status)

        # Translation section
        trans = self._create_section_header(section, "Translation", "Translate spoken audio to English", show_divider=True)

        self.translation_enabled_var = ctk.BooleanVar(value=self.config.get("translation_enabled", False))
        self._create_toggle_setting(
            trans,
            "Enable translation",
            help_text="Translate speech to English output",
            variable=self.translation_enabled_var,
        )

        self.trans_lang_var = ctk.StringVar(
            value=settings_logic.language_code_to_label(
                self.config.get("translation_source_language", "auto")
            )
        )
        self._create_labeled_dropdown(
            trans,
            "Source Language",
            values=settings_logic.get_language_labels(),
            variable=self.trans_lang_var,
            help_text="Language being spoken",
            width=160,
        )

    # =========================================================================
    # MODEL STATUS AND DOWNLOAD
    # =========================================================================

    def _on_model_changed(self, *args):
        """Callback when model dropdown selection changes."""
        self.refresh_model_status()

    def refresh_model_status(self):
        """Refresh model status display."""
        model_name = self.model_var.get()

        # Check if model is available
        from dependency_check import check_model_available
        is_available, _ = check_model_available(model_name)

        if is_available:
            # Green status - model installed
            self.model_status_dot.configure(fg_color=SUCCESS)
            self.model_status_text.configure(text="Installed")
            # Hide download button
            self.download_model_frame.pack_forget()
        else:
            # Check if this is a downloadable model
            if model_name in config.DOWNLOADABLE_MODELS:
                # Orange status - downloadable
                self.model_status_dot.configure(fg_color=WARNING)
                self.model_status_text.configure(text="Not installed")
                # Show download button with size
                size_mb = config.MODEL_SIZES_MB.get(model_name, 500)
                if size_mb >= 1000:
                    size_text = f"~{size_mb / 1000:.1f} GB"
                else:
                    size_text = f"~{size_mb} MB"
                self.download_model_size_label.configure(text=size_text)
                self.download_model_frame.pack(fill="x", pady=(SPACE_SM, 0), after=self.model_status_frame)
            elif model_name in config.BUNDLED_MODELS:
                # Red status - bundled model missing (installation error)
                self.model_status_dot.configure(fg_color=ERROR)
                self.model_status_text.configure(text="Missing (reinstall required)")
                self.download_model_frame.pack_forget()
            else:
                # Unknown model
                self.model_status_dot.configure(fg_color=SLATE_500)
                self.model_status_text.configure(text="Unknown model")
                self.download_model_frame.pack_forget()

    def _download_selected_model(self):
        """Download the currently selected model."""
        model_name = self.model_var.get()

        # Confirm download
        if not self._show_model_download_confirm(model_name):
            return

        # Download using dependency_check
        from dependency_check import download_model
        success = download_model(model_name)

        if success:
            # Refresh status
            self.refresh_model_status()
            self._show_info_dialog(
                "Download Complete",
                f"The {model_name} model has been downloaded successfully!"
            )

    def _show_info_dialog(self, title, message):
        """Show a branded info dialog."""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(title)
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(fg_color=SLATE_800)

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 350) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        # Set icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                dialog.after(200, lambda: dialog.iconbitmap(icon_path))
        except Exception:
            pass

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            wraplength=310,
            justify="center",
        ).pack(pady=(SPACE_MD, SPACE_LG))

        ctk.CTkButton(
            frame,
            text="OK",
            command=dialog.destroy,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            width=80,
            height=32,
        ).pack()

        dialog.wait_window()

    def _show_model_download_confirm(self, model_name):
        """Show branded confirmation dialog for model download. Returns True if confirmed."""
        size_mb = config.MODEL_SIZES_MB.get(model_name, 500)
        if size_mb >= 1000:
            size_text = f"~{size_mb / 1000:.1f} GB"
        else:
            size_text = f"~{size_mb} MB"

        result = {"confirmed": False}

        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Download Model")
        dialog.geometry("380x180")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(fg_color=SLATE_800)

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 380) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        # Set icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                dialog.after(200, lambda: dialog.iconbitmap(icon_path))
        except Exception:
            pass

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(
            frame,
            text=f"Download {model_name} Model?",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=SLATE_100,
        ).pack(pady=(SPACE_SM, SPACE_SM))

        ctk.CTkLabel(
            frame,
            text=f"Download size: {size_text}\nThis may take a few minutes.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
            justify="center",
        ).pack(pady=(0, SPACE_LG))

        def on_yes():
            result["confirmed"] = True
            dialog.destroy()

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame,
            text="Download",
            command=on_yes,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            width=100,
            height=32,
        ).pack(side="left", padx=SPACE_SM)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            width=100,
            height=32,
        ).pack(side="left", padx=SPACE_SM)

        dialog.wait_window()
        return result["confirmed"]

    # =========================================================================
    # GPU STATUS AND INSTALL
    # =========================================================================

    def refresh_gpu_status(self):
        """Refresh GPU status display."""
        is_available, status_msg, detail = settings_logic.get_cuda_status()
        cuda_libs_installed = status_msg != "GPU libraries not installed"

        if is_available:
            # Green status - GPU working
            self.gpu_status_dot.configure(fg_color=SUCCESS)
            display_text = detail if detail else status_msg
            self.gpu_status_text.configure(text=display_text)
            # Hide install button when CUDA is available
            self.install_gpu_frame.pack_forget()
        else:
            # Gray/red status - GPU not available
            self.gpu_status_dot.configure(fg_color=ERROR if not cuda_libs_installed else SLATE_500)
            self.gpu_status_text.configure(text=status_msg)
            # Show install button only if libraries aren't installed
            if not cuda_libs_installed:
                # Re-pack after status_row to maintain position
                self.install_gpu_frame.pack(fill="x", pady=(SPACE_SM, 0), after=self.gpu_status_frame)
            else:
                self.install_gpu_frame.pack_forget()

    def _show_gpu_confirm_dialog(self):
        """Show custom confirmation dialog for GPU install. Returns True if confirmed."""
        result = {"confirmed": False}

        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Install GPU Support")
        dialog.geometry("420x200")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 420) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        dialog.configure(fg_color=SLATE_800)

        # Set window icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                dialog.after(200, lambda: dialog.iconbitmap(icon_path))
        except Exception:
            pass

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # Title
        ctk.CTkLabel(
            frame,
            text="Install NVIDIA CUDA Libraries?",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=SLATE_100,
        ).pack(pady=(SPACE_MD, SPACE_MD), anchor="center")

        # Info text
        ctk.CTkLabel(
            frame,
            text="Download size: ~2-3 GB\nRequires: NVIDIA GPU with CUDA support",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
            justify="center",
        ).pack(pady=(0, SPACE_LG))

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        def on_yes():
            result["confirmed"] = True
            dialog.destroy()

        def on_no():
            dialog.destroy()

        ctk.CTkButton(
            btn_frame,
            text="Install",
            command=on_yes,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            width=100,
            height=32,
        ).pack(side="left", expand=True, padx=SPACE_SM)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=on_no,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=SLATE_700,
            hover_color=SLATE_600,
            width=100,
            height=32,
        ).pack(side="left", expand=True, padx=SPACE_SM)

        dialog.wait_window()
        return result["confirmed"]

    def install_gpu_support(self):
        """Install GPU dependencies via pip using a modal dialog."""
        app_dir = os.path.dirname(os.path.abspath(__file__))

        # Confirm with user using custom styled dialog
        if not self._show_gpu_confirm_dialog():
            return

        # Create modal dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Installing GPU Support")
        dialog.geometry("420x260")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 420) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        # Prevent closing during install
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        # Configure dialog appearance
        dialog.configure(fg_color=SLATE_800)

        # Set window icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                dialog.after(200, lambda: dialog.iconbitmap(icon_path))
        except Exception:
            pass

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        # Logo
        try:
            logo_path = resource_path(os.path.join("assets", "logo", "murmurtone-icon-transparent.png"))
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(48, 48))
                logo_label = ctk.CTkLabel(frame, image=logo_ctk, text="")
                logo_label.pack(pady=(0, SPACE_SM))
        except Exception:
            pass  # Skip logo if it fails to load

        # Title
        title_label = ctk.CTkLabel(
            frame,
            text="Installing NVIDIA CUDA Libraries",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color=SLATE_100,
        )
        title_label.pack(pady=(0, SPACE_MD))

        # Progress bar
        progress = ctk.CTkProgressBar(frame, width=360, mode="indeterminate")
        progress.pack(pady=SPACE_SM)
        progress.start()

        # Status label
        status_label = ctk.CTkLabel(
            frame,
            text="Downloading... this may take several minutes",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
        )
        status_label.pack(pady=SPACE_SM)

        # Size hint
        size_hint = ctk.CTkLabel(
            frame,
            text="(Download size: ~2-3 GB)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
        )
        size_hint.pack()

        # Store references for the completion handler
        self._install_dialog = dialog
        self._install_progress = progress
        self._install_status = status_label

        def run_install():
            try:
                # Install only GPU-specific packages to avoid dependency conflicts
                # (user already has base deps since the app is running)
                gpu_packages = [
                    "nvidia-cublas-cu12>=12.1.0",
                    "nvidia-cudnn-cu12>=9.1.0",
                ]
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + gpu_packages,
                    capture_output=True,
                    text=True,
                    cwd=app_dir,
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr

                # Schedule UI update on main thread
                self.window.after(0, lambda: self._install_complete(success, output))
            except Exception as e:
                self.window.after(0, lambda: self._install_complete(False, str(e)))

        # Run in background thread
        thread = threading.Thread(target=run_install, daemon=True)
        thread.start()

    def _install_complete(self, success, output):
        """Handle completion of GPU installation."""
        # Stop progress and close dialog
        if hasattr(self, "_install_progress"):
            self._install_progress.stop()
        if hasattr(self, "_install_dialog") and self._install_dialog:
            self._install_dialog.destroy()

        if success:
            messagebox.showinfo(
                "Installation Complete",
                "GPU libraries installed successfully!\n\n"
                "Please restart MurmurTone for changes to take effect.",
                parent=self.window,
            )
        else:
            # Show error with manual install instructions
            error_msg = (
                "Automatic GPU installation failed.\n\n"
                "You can install manually by running:\n"
                "pip install nvidia-cublas-cu12 nvidia-cudnn-cu12\n\n"
                "If you have dependency conflicts, try:\n"
                "pip install --no-deps nvidia-cublas-cu12 nvidia-cudnn-cu12"
            )
            messagebox.showwarning("Installation Failed", error_msg, parent=self.window)

        # Refresh GPU status
        self.refresh_gpu_status()

    # =========================================================================
    # TEXT SECTION
    # =========================================================================

    def _create_text_section(self):
        """Create Text settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["text"] = section

        # Voice Commands section (first section - no separator)
        commands = self._create_section_header(section, "Voice Commands", 'Spoken commands like "new line" or "period"')

        self.voice_commands_var = ctk.BooleanVar(value=self.config.get("voice_commands_enabled", True))
        self._create_toggle_setting(
            commands,
            "Enable voice commands",
            help_text='Execute commands like "new line", "period"',
            variable=self.voice_commands_var,
        )

        self.scratch_that_var = ctk.BooleanVar(value=self.config.get("scratch_that_enabled", True))
        self._create_toggle_setting(
            commands,
            '"Scratch that" command',
            help_text="Delete the last transcription",
            variable=self.scratch_that_var,
        )

        # Filler Word Removal section
        filler = self._create_section_header(section, "Filler Word Removal", "Clean up hesitation sounds from transcriptions", show_divider=True)

        self.filler_var = ctk.BooleanVar(value=self.config.get("filler_removal_enabled", False))
        self._create_toggle_setting(
            filler,
            "Remove filler words",
            help_text='Remove "um", "uh", "like", etc.',
            variable=self.filler_var,
        )

        self.filler_aggressive_var = ctk.BooleanVar(value=self.config.get("filler_removal_aggressive", False))
        self._create_toggle_setting(
            filler,
            "Aggressive mode",
            help_text="Remove more hesitation patterns",
            variable=self.filler_aggressive_var,
        )

        # Custom Dictionary section
        dictionary = self._create_section_header(section, "Custom Dictionary", "Add word replacements and custom vocabulary", show_divider=True)

        dict_row = ctk.CTkFrame(dictionary, fg_color="transparent")
        dict_row.pack(fill="x", pady=(0, SPACE_SM))

        dict_btn = self._create_button(dict_row, "Edit Dictionary", self._edit_dictionary, width=140)
        dict_btn.pack(side="left")

        vocab_btn = self._create_button(dict_row, "Edit Vocabulary", self._edit_vocabulary, width=140)
        vocab_btn.pack(side="left", padx=(SPACE_SM, 0))

        # Text Shortcuts section
        shortcuts = self._create_section_header(section, "Text Shortcuts", "Trigger phrases that expand to text blocks", show_divider=True)

        shortcuts_btn = self._create_button(shortcuts, "Edit Shortcuts", self._edit_shortcuts, width=140)
        shortcuts_btn.pack(anchor="w", pady=(0, SPACE_SM))

    def _edit_dictionary(self):
        """Open dictionary editor."""
        def on_save(items):
            self.custom_dictionary = items
            self._autosave()

        DictionaryEditor(self.window, self.custom_dictionary, on_save)

    def _edit_vocabulary(self):
        """Open vocabulary editor."""
        def on_save(items):
            self.custom_vocabulary = items
            self._autosave()

        VocabularyEditor(self.window, self.custom_vocabulary, on_save)

    def _edit_shortcuts(self):
        """Open shortcuts editor."""
        def on_save(items):
            self.custom_commands = items
            self._autosave()

        ShortcutsEditor(self.window, self.custom_commands, on_save)

    # =========================================================================
    # ADVANCED SECTION
    # =========================================================================

    def _create_advanced_section(self):
        """Create Advanced settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["advanced"] = section

        # AI Text Cleanup section (first section - no separator)
        ai = self._create_section_header(section, "AI Text Cleanup", "Use local LLM to polish transcriptions")

        self.ai_cleanup_var = ctk.BooleanVar(value=self.config.get("ai_cleanup_enabled", False))
        self._create_toggle_setting(
            ai,
            "Enable AI cleanup",
            help_text="Process text through Ollama",
            variable=self.ai_cleanup_var,
        )

        # Ollama status
        status_row = ctk.CTkFrame(ai, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, SPACE_MD))

        self.ollama_status_dot = self._create_status_dot(status_row, SLATE_500)

        self.ollama_status_text = ctk.CTkLabel(
            status_row,
            text="Not checked",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_300,
        )
        self.ollama_status_text.pack(side="left")

        check_btn = self._create_button(status_row, "Check", self._check_ollama, width=60)
        check_btn.configure(fg_color="transparent", border_width=0)
        check_btn.pack(side="left", padx=(SPACE_LG, 0))

        # Cleanup mode
        self.ai_mode_var = ctk.StringVar(value=self.config.get("ai_cleanup_mode", "grammar"))
        self._create_labeled_dropdown(
            ai,
            "Cleanup Mode",
            values=["grammar", "formality", "both"],
            variable=self.ai_mode_var,
            help_text="Grammar fixes or formality adjustment",
            width=140,
        )

        # Formality level
        self.ai_formality_var = ctk.StringVar(value=self.config.get("ai_formality_level", "professional"))
        self._create_labeled_dropdown(
            ai,
            "Formality Level",
            values=["casual", "professional", "formal"],
            variable=self.ai_formality_var,
            width=100,
        )

        # Ollama model
        self.ai_model_var = ctk.StringVar(value=self.config.get("ollama_model", "llama3.2"))
        self._create_labeled_entry(
            ai,
            "Ollama Model",
            variable=self.ai_model_var,
            help_text="Local AI model name",
            width=140,
        )

        # Transcription History section
        history = self._create_section_header(section, "Transcription History", "Recent transcriptions stored for review", show_divider=True)

        history_btn = self._create_button(history, "View History", self._view_history, width=120)
        history_btn.pack(anchor="w", pady=(0, SPACE_SM))

        # Reset Settings section
        reset_section = self._create_section_header(
            section,
            "Reset Settings",
            "Restore all settings to factory defaults",
            show_divider=True
        )

        reset_btn = self._create_button(
            reset_section,
            "Reset to Defaults",
            self.reset_defaults,
            style="secondary",
            width=140
        )
        reset_btn.pack(anchor="w", pady=(0, SPACE_SM))

    def _check_ollama(self):
        """Check Ollama connection."""
        try:
            import requests
            url = self.config.get("ollama_url", "http://localhost:11434")
            # Validate URL before making request (prevents SSRF)
            if not validate_ollama_url(url):
                self.ollama_status_dot.configure(fg_color=ERROR)
                self.ollama_status_text.configure(text="Invalid URL")
                return
            response = requests.get(f"{url}/api/tags", timeout=2)
            if response.status_code == 200:
                self.ollama_status_dot.configure(fg_color=SUCCESS)
                self.ollama_status_text.configure(text="Ollama connected")
            else:
                self.ollama_status_dot.configure(fg_color=ERROR)
                self.ollama_status_text.configure(text="Connection failed")
        except Exception:
            self.ollama_status_dot.configure(fg_color=ERROR)
            self.ollama_status_text.configure(text="Not running")

    def _view_history(self):
        """View transcription history."""
        HistoryViewer(self.window)

    # =========================================================================
    # ABOUT SECTION
    # =========================================================================

    def _create_about_section(self):
        """Create About section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["about"] = section

        # App info (first section - no separator)
        info = self._create_section_header(section, "")

        # App row
        app_row = ctk.CTkFrame(info, fg_color="transparent")
        app_row.pack(fill="x", pady=(0, SPACE_XL))

        # Logo
        logo = ctk.CTkFrame(
            app_row,
            width=64,
            height=64,
            fg_color=PRIMARY,
            corner_radius=16,
        )
        logo.pack(side="left")
        logo.pack_propagate(False)

        logo_icon = ctk.CTkLabel(
            logo,
            text="🎤",
            font=ctk.CTkFont(family=FONT_FAMILY, size=28),
        )
        logo_icon.place(relx=0.5, rely=0.5, anchor="center")

        # App details
        details = ctk.CTkFrame(app_row, fg_color="transparent")
        details.pack(side="left", padx=(SPACE_LG, 0))

        name = ctk.CTkLabel(
            details,
            text="MurmurTone",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=SLATE_100,
            anchor="w",
        )
        name.pack(fill="x")

        version = ctk.CTkLabel(
            details,
            text=f"Version {config.VERSION}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_400,
            anchor="w",
        )
        version.pack(fill="x")

        # Description
        desc = ctk.CTkLabel(
            info,
            text="Local speech-to-text powered by OpenAI Whisper. Your voice stays on your device.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
            anchor="w",
            wraplength=500,
        )
        desc.pack(fill="x", pady=(0, SPACE_XL))

        # Links
        links_data = [
            ("View on GitHub", "https://github.com/tuckerandrew21/MurmurTone"),
            ("Open Logs Folder", None),
            ("Report an Issue", "https://github.com/tuckerandrew21/MurmurTone/issues"),
        ]

        for link_text, url in links_data:
            link = ctk.CTkLabel(
                info,
                text=f"↗ {link_text}",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                text_color=PRIMARY,
                cursor="hand2",
                anchor="w",
            )
            link.pack(fill="x", pady=(0, SPACE_SM))

            # Hover effects (PRIMARY -> PRIMARY_LIGHT)
            link.bind("<Enter>", lambda e, l=link: l.configure(text_color=PRIMARY_LIGHT))
            link.bind("<Leave>", lambda e, l=link: l.configure(text_color=PRIMARY))

            if url:
                link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            elif link_text == "Open Logs Folder":
                link.bind("<Button-1>", lambda e: self._open_logs_folder())

        # System Info section (lazy-loaded for faster startup)
        sys_info = self._create_section_header(section, "System Information", show_divider=True)

        self._sys_info_label = ctk.CTkLabel(
            sys_info,
            text="Loading...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
            anchor="w",
            justify="left",
        )
        self._sys_info_label.pack(fill="x")

    def _open_logs_folder(self):
        """Open logs folder."""
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        os.startfile(logs_dir)

    def _populate_system_info(self):
        """Populate system info label (called lazily when About tab is first shown)."""
        if self._sys_info_loaded or not self._sys_info_label:
            return

        info_text = []
        try:
            import sys
            info_text.append(f"Python: {sys.version.split()[0]}")
        except Exception:
            pass

        try:
            import torch
            info_text.append(f"PyTorch: {torch.__version__}")
            if torch.cuda.is_available():
                info_text.append(f"CUDA: {torch.version.cuda}")
        except ImportError:
            info_text.append("PyTorch: Not installed")

        try:
            import faster_whisper
            info_text.append(f"Whisper: faster-whisper")
        except ImportError:
            pass

        self._sys_info_label.configure(text="\n".join(info_text))
        self._sys_info_loaded = True

    # =========================================================================
    # AUTOSAVE
    # =========================================================================

    def _show_save_status(self, state):
        """Show save status in sidebar: 'saving', 'saved', or 'error'."""
        if not self._status_label:
            return

        # Cancel any pending hide
        if self._status_hide_id:
            self.window.after_cancel(self._status_hide_id)
            self._status_hide_id = None

        if state == "saving":
            self._status_label.configure(text="Saving...", text_color=SLATE_400)
        elif state == "saved":
            self._status_label.configure(text="Saved", text_color=SUCCESS)
            # Auto-hide after 2 seconds
            self._status_hide_id = self.window.after(
                2000, lambda: self._status_label.configure(text="")
            )
        elif state == "error":
            self._status_label.configure(text="Save failed", text_color=ERROR)

    def _build_config_dict(self):
        """Build configuration dictionary from current widget values."""
        # Validate inputs
        rate_str = self.rate_var.get()
        rate_value = rate_str.split()[0]
        sample_rate = settings_logic.validate_sample_rate(rate_value)
        silence_duration = settings_logic.validate_silence_duration(self.silence_var.get())

        # Get device info
        device_info = self.get_selected_device_info()

        # Convert language labels to codes
        lang_code = settings_logic.language_label_to_code(self.lang_var.get())
        trans_lang_code = settings_logic.language_label_to_code(self.trans_lang_var.get())

        # Convert processing mode
        processing_mode = settings_logic.processing_mode_label_to_code(
            self.processing_mode_var.get()
        )

        # Convert display labels back to internal values
        recording_mode = RECORDING_MODE_VALUES.get(self.mode_var.get(), "push_to_talk")
        paste_mode = PASTE_MODE_VALUES.get(self.paste_mode_var.get(), "clipboard")
        preview_position = PREVIEW_POSITION_VALUES.get(self.preview_position_var.get(), "bottom_right")
        preview_theme = PREVIEW_THEME_VALUES.get(self.preview_theme_var.get(), "dark")

        # Convert hotkey string to dict format expected by config
        if isinstance(self.hotkey, str):
            hotkey_dict = {"ctrl": False, "shift": False, "alt": False, "key": self.hotkey}
        else:
            hotkey_dict = self.hotkey

        return {
            "model_size": self.model_var.get(),
            "language": lang_code,
            "translation_enabled": self.translation_enabled_var.get(),
            "translation_source_language": trans_lang_code,
            "sample_rate": sample_rate,
            "hotkey": hotkey_dict,
            "recording_mode": recording_mode,
            "silence_duration_sec": silence_duration,
            "audio_feedback": self.feedback_var.get(),
            "input_device": device_info,
            "auto_paste": self.autopaste_var.get(),
            "paste_mode": paste_mode,
            "start_with_windows": self.startup_var.get(),
            "processing_mode": processing_mode,
            "noise_gate_enabled": self.noise_gate_var.get(),
            "noise_gate_threshold_db": self.noise_threshold_var.get(),
            "audio_feedback_volume": self.volume_var.get(),
            "sound_processing": self.sound_processing_var.get(),
            "sound_success": self.sound_success_var.get(),
            "sound_error": self.sound_error_var.get(),
            "sound_command": self.sound_command_var.get(),
            "voice_commands_enabled": self.voice_commands_var.get(),
            "scratch_that_enabled": self.scratch_that_var.get(),
            "filler_removal_enabled": self.filler_var.get(),
            "filler_removal_aggressive": self.filler_aggressive_var.get(),
            "custom_fillers": self.config.get("custom_fillers", []),
            "custom_dictionary": self.custom_dictionary,
            "custom_vocabulary": self.custom_vocabulary,
            "custom_commands": self.custom_commands,
            "ai_cleanup_enabled": self.ai_cleanup_var.get(),
            "ai_cleanup_mode": self.ai_mode_var.get(),
            "ai_formality_level": self.ai_formality_var.get(),
            "ollama_model": self.ai_model_var.get(),
            "ollama_url": self.config.get("ollama_url", "http://localhost:11434"),
            "preview_enabled": self.preview_enabled_var.get(),
            "preview_position": preview_position,
            "preview_theme": preview_theme,
            "preview_auto_hide_delay": float(self.preview_delay_var.get() or 2.0),
            "preview_font_size": self.preview_font_size_var.get(),
        }

    def _autosave(self):
        """Save current settings immediately (called by widget callbacks)."""
        try:
            new_config = self._build_config_dict()

            # Save to file
            config.save_config(new_config)

            # Update startup registry if needed
            config.set_startup_enabled(self.startup_var.get())

            # Show status
            self._show_save_status("saved")

            # Notify main app (for settings that affect runtime)
            if self.on_save_callback:
                self.on_save_callback(new_config)

        except Exception as e:
            self._show_save_status("error")
            print(f"Autosave error: {e}")

    # =========================================================================
    # SAVE / RESET / CLOSE (Legacy - save() kept for compatibility)
    # =========================================================================

    def save(self):
        """Save settings."""
        # Validate inputs
        rate_str = self.rate_var.get()
        rate_value = rate_str.split()[0]
        sample_rate = settings_logic.validate_sample_rate(rate_value)
        silence_duration = settings_logic.validate_silence_duration(self.silence_var.get())

        # Get device info
        device_info = self.get_selected_device_info()

        # Convert language labels to codes
        lang_code = settings_logic.language_label_to_code(self.lang_var.get())
        trans_lang_code = settings_logic.language_label_to_code(self.trans_lang_var.get())

        # Convert processing mode
        processing_mode = settings_logic.processing_mode_label_to_code(
            self.processing_mode_var.get()
        )

        # Convert display labels back to internal values
        recording_mode = RECORDING_MODE_VALUES.get(self.mode_var.get(), "push_to_talk")
        paste_mode = PASTE_MODE_VALUES.get(self.paste_mode_var.get(), "clipboard")
        preview_position = PREVIEW_POSITION_VALUES.get(self.preview_position_var.get(), "bottom_right")
        preview_theme = PREVIEW_THEME_VALUES.get(self.preview_theme_var.get(), "dark")

        # Convert hotkey string to dict format expected by config
        if isinstance(self.hotkey, str):
            hotkey_dict = {"ctrl": False, "shift": False, "alt": False, "key": self.hotkey}
        else:
            hotkey_dict = self.hotkey

        new_config = {
            "model_size": self.model_var.get(),
            "language": lang_code,
            "translation_enabled": self.translation_enabled_var.get(),
            "translation_source_language": trans_lang_code,
            "sample_rate": sample_rate,
            "hotkey": hotkey_dict,
            "recording_mode": recording_mode,
            "silence_duration_sec": silence_duration,
            "audio_feedback": self.feedback_var.get(),
            "input_device": device_info,
            "auto_paste": self.autopaste_var.get(),
            "paste_mode": paste_mode,
            "start_with_windows": self.startup_var.get(),
            "processing_mode": processing_mode,
            "noise_gate_enabled": self.noise_gate_var.get(),
            "noise_gate_threshold_db": self.noise_threshold_var.get(),
            "audio_feedback_volume": self.volume_var.get(),
            "sound_processing": self.sound_processing_var.get(),
            "sound_success": self.sound_success_var.get(),
            "sound_error": self.sound_error_var.get(),
            "sound_command": self.sound_command_var.get(),
            "voice_commands_enabled": self.voice_commands_var.get(),
            "scratch_that_enabled": self.scratch_that_var.get(),
            "filler_removal_enabled": self.filler_var.get(),
            "filler_removal_aggressive": self.filler_aggressive_var.get(),
            "custom_fillers": self.config.get("custom_fillers", []),
            "custom_dictionary": self.custom_dictionary,
            "custom_vocabulary": self.custom_vocabulary,
            "custom_commands": self.custom_commands,
            "ai_cleanup_enabled": self.ai_cleanup_var.get(),
            "ai_cleanup_mode": self.ai_mode_var.get(),
            "ai_formality_level": self.ai_formality_var.get(),
            "ollama_model": self.ai_model_var.get(),
            "ollama_url": self.config.get("ollama_url", "http://localhost:11434"),
            "preview_enabled": self.preview_enabled_var.get(),
            "preview_position": preview_position,
            "preview_theme": preview_theme,
            "preview_auto_hide_delay": float(self.preview_delay_var.get() or 2.0),
            "preview_font_size": self.preview_font_size_var.get(),
        }

        config.save_config(new_config)
        config.set_startup_enabled(self.startup_var.get())

        if self.on_save_callback:
            self.on_save_callback(new_config)

        self.close()

    def get_selected_device_info(self):
        """Get selected device info."""
        selected_name = self.device_var.get()
        for name, info in self.devices_list:
            if name == selected_name:
                return info
        return None

    def _show_confirm_dialog(self, title, message):
        """Show a branded confirmation dialog. Returns True if confirmed."""
        result = [False]

        dlg = ctk.CTkToplevel(self.window)
        dlg.title(title)
        dlg.geometry("350x150")
        dlg.configure(fg_color=SLATE_900)
        dlg.transient(self.window)
        dlg.grab_set()
        dlg.resizable(False, False)

        # Set icon
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path):
                dlg.after(200, lambda: dlg.iconbitmap(icon_path))
        except Exception:
            pass

        # Center on parent
        dlg.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 350) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        dlg.geometry(f"350x150+{x}+{y}")

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=SPACE_LG, pady=SPACE_LG)

        ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color=SLATE_200,
            wraplength=300
        ).pack(pady=(SPACE_MD, SPACE_LG))

        def confirm():
            result[0] = True
            dlg.destroy()

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(side="bottom")

        ctk.CTkButton(
            btn_row, text="Yes", width=80, fg_color=PRIMARY,
            hover_color=PRIMARY_DARK, command=confirm
        ).pack(side="left", padx=(0, SPACE_SM))
        ctk.CTkButton(
            btn_row, text="No", width=80, fg_color=SLATE_700,
            hover_color=SLATE_600, command=dlg.destroy
        ).pack(side="left")

        dlg.wait_window()
        return result[0]

    def reset_defaults(self):
        """Reset all settings to defaults."""
        if not self._show_confirm_dialog(
            "Reset to Defaults",
            "Reset all settings to defaults?"
        ):
            return

        defaults = settings_logic.get_defaults()

        # General tab
        self.mode_var.set(RECORDING_MODE_LABELS.get(defaults["recording_mode"], "Push-to-Talk"))
        self._update_hotkey_help_text()  # Update help text after mode change
        self.lang_var.set(settings_logic.language_code_to_label(defaults["language"]))
        self.autopaste_var.set(defaults["auto_paste"])
        self.paste_mode_var.set(PASTE_MODE_LABELS.get(defaults["paste_mode"], "Clipboard"))
        self._update_paste_help_text()  # Update help text after paste mode change
        self.preview_enabled_var.set(defaults["preview_enabled"])
        self.preview_position_var.set(PREVIEW_POSITION_LABELS.get(defaults["preview_position"], "Bottom Right"))
        self.preview_theme_var.set(PREVIEW_THEME_LABELS.get(defaults["preview_theme"], "Dark"))
        self.preview_delay_var.set(str(defaults["preview_auto_hide_delay"]))
        self.preview_font_size_var.set(defaults["preview_font_size"])
        self.startup_var.set(defaults["start_with_windows"])

        # Audio tab
        self.device_var.set("System Default")
        self.rate_var.set(SAMPLE_RATE_OPTIONS.get(defaults["sample_rate"], "16000 Hz"))
        self.noise_gate_var.set(defaults["noise_gate_enabled"])
        self.noise_threshold_var.set(defaults["noise_gate_threshold_db"])
        self.feedback_var.set(defaults["audio_feedback"])
        self.volume_var.set(int(defaults["audio_feedback_volume"] * 100))
        self.sound_processing_var.set(defaults["sound_processing"])
        self.sound_success_var.set(defaults["sound_success"])
        self.sound_error_var.set(defaults["sound_error"])
        self.sound_command_var.set(defaults["sound_command"])

        # Recognition tab
        self.model_var.set(defaults["model_size"])
        self._model_display_var.set(config.MODEL_DISPLAY_NAMES.get(defaults["model_size"], defaults["model_size"]))
        self.silence_var.set(str(defaults["silence_duration_sec"]))
        self.processing_mode_var.set(config.PROCESSING_MODE_LABELS.get(defaults["processing_mode"], "Auto"))
        self.translation_enabled_var.set(defaults["translation_enabled"])
        self.trans_lang_var.set(settings_logic.language_code_to_label(defaults["translation_source_language"]))

        # Text tab
        self.voice_commands_var.set(defaults["voice_commands_enabled"])
        self.scratch_that_var.set(defaults["scratch_that_enabled"])
        self.filler_var.set(defaults["filler_removal_enabled"])
        self.filler_aggressive_var.set(defaults["filler_removal_aggressive"])

        # Advanced tab
        self.ai_cleanup_var.set(defaults["ai_cleanup_enabled"])
        self.ai_mode_var.set(defaults["ai_cleanup_mode"])
        self.ai_formality_var.set(defaults["ai_formality_level"])
        self.ai_model_var.set(defaults["ollama_model"])

    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation for accessibility."""
        # Escape key closes window
        self.window.bind("<Escape>", lambda e: self.close())

        # Tab navigation is automatic in CTk widgets
        # Additional keyboard shortcuts can be added here as needed

    def close(self):
        """Close the settings window."""
        # Flush any pending autosaves
        if self._text_debounce:
            self._text_debounce.flush()
        if self._slider_debounce:
            self._slider_debounce.flush()

        if self.noise_test_running:
            self.stop_noise_test()
        if self.window:
            self.window.destroy()
            self.window = None


def open_settings(current_config, on_save_callback=None):
    """Open the settings window."""
    settings = SettingsWindow(current_config, on_save_callback)
    settings.show()


if __name__ == "__main__":
    import config as cfg

    current = cfg.load_config()
    open_settings(current)
