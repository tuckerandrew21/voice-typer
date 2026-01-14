"""
Settings GUI for MurmurTone using CustomTkinter.

Modern dark theme with sidebar navigation, matching V1 brand.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np
import sounddevice as sd
import subprocess
import sys
import threading
import os
import webbrowser

import config
import text_processor
import license
import settings_logic
from theme import (
    # Colors
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT,
    SLATE_900, SLATE_800, SLATE_700, SLATE_600, SLATE_500, SLATE_400, SLATE_200, SLATE_100,
    SUCCESS, WARNING, ERROR,
    # Style helpers
    get_card_style, get_button_style, get_entry_style, get_switch_style,
    get_dropdown_style, get_label_style, get_nav_item_style, get_nav_section_style,
    make_combobox_clickable,
    get_status_color, get_meter_color,
    # Constants
    SPACING, PAD_DEFAULT, PAD_SPACIOUS, CARD_PAD_X, CARD_PAD_Y,
    SIDEBAR_WIDTH, NAV_ITEM_HEIGHT, FONT_SIZES, WINDOW_CONFIG,
)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in dev mode
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Sample rate options with user-friendly descriptions
SAMPLE_RATE_OPTIONS = {
    8000: "8000 Hz - Phone quality",
    16000: "16000 Hz - Speech (Recommended)",
    22050: "22050 Hz - Standard audio",
    44100: "44100 Hz - CD quality",
    48000: "48000 Hz - Studio quality",
}


class Tooltip:
    """Modern tooltip that appears on hover."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25

        self.tooltip = ctk.CTkToplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.configure(fg_color=SLATE_700)

        label = ctk.CTkLabel(
            self.tooltip,
            text=self.text,
            text_color=SLATE_200,
            font=("", 11),
            padx=8,
            pady=4,
            corner_radius=6,
        )
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class HotkeyCapture(ctk.CTkFrame):
    """Widget for capturing keyboard hotkeys."""

    def __init__(self, parent, initial_hotkey="scroll_lock"):
        super().__init__(parent, fg_color="transparent")

        self.hotkey = initial_hotkey
        self.capturing = False

        # Display label
        self.display_frame = ctk.CTkFrame(self, fg_color=SLATE_700, corner_radius=6)
        self.display_frame.pack(side="left", fill="x", expand=True)

        self.display_label = ctk.CTkLabel(
            self.display_frame,
            text=self._format_hotkey(initial_hotkey),
            text_color=SLATE_200,
            font=("", 12),
            anchor="w",
            padx=12,
            pady=8,
        )
        self.display_label.pack(fill="x")

        # Set button
        self.set_btn = ctk.CTkButton(
            self,
            text="Set",
            width=60,
            **get_button_style("secondary"),
            command=self.start_capture,
        )
        self.set_btn.pack(side="left", padx=(8, 0))
        Tooltip(self.set_btn, "Click to capture a new hotkey")

        # Listener reference (will be set up when capturing)
        self.listener = None

    def _format_hotkey(self, hotkey):
        """Format hotkey for display."""
        if not hotkey:
            return "Not set"
        # Handle dict format (from config.py)
        if isinstance(hotkey, dict):
            return config.hotkey_to_string(hotkey)
        # Handle string format
        parts = hotkey.split("+")
        formatted = [p.replace("_", " ").title() for p in parts]
        return " + ".join(formatted)

    def start_capture(self):
        """Start capturing a hotkey."""
        if self.capturing:
            return

        self.capturing = True
        self.set_btn.configure(text="...", state="disabled", fg_color=PRIMARY)
        self.display_label.configure(text="Press any key...")

        # Start keyboard listener
        try:
            from pynput import keyboard

            def on_press(key):
                try:
                    # Get key name
                    if hasattr(key, "char") and key.char:
                        key_name = key.char.lower()
                    else:
                        key_name = key.name.lower()

                    self.hotkey = key_name
                    self.display_label.configure(text=self._format_hotkey(key_name))
                except AttributeError:
                    pass

                self.stop_capture()
                return False

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
        except ImportError:
            self.display_label.configure(text="pynput not installed")
            self.stop_capture()

    def stop_capture(self):
        """Stop capturing."""
        self.capturing = False
        self.set_btn.configure(text="Set", state="normal", **get_button_style("secondary"))
        if self.listener:
            self.listener.stop()
            self.listener = None

    def get_hotkey(self):
        """Get the current hotkey."""
        return self.hotkey

    def set_hotkey(self, hotkey):
        """Set the hotkey programmatically."""
        self.hotkey = hotkey
        self.display_label.configure(text=self._format_hotkey(hotkey))


class NavItem(ctk.CTkButton):
    """Sidebar navigation item."""

    def __init__(self, parent, text, icon=None, command=None, **kwargs):
        super().__init__(
            parent,
            text=f"  {icon}  {text}" if icon else f"  {text}",
            anchor="w",
            height=NAV_ITEM_HEIGHT,
            command=command,
            **get_nav_item_style(active=False),
            **kwargs,
        )
        self._text = text
        self._icon = icon
        self._is_active = False

    def set_active(self, active):
        """Set the active state of this nav item."""
        self._is_active = active
        style = get_nav_item_style(active=active)
        self.configure(**style)


class SectionHeader(ctk.CTkLabel):
    """Sidebar section header (e.g., "Recording", "System")."""

    def __init__(self, parent, text):
        super().__init__(
            parent,
            text=text.upper(),
            anchor="w",
            **get_nav_section_style(),
        )


class Card(ctk.CTkFrame):
    """Card container for grouping related settings."""

    def __init__(self, parent, title=None, **kwargs):
        style = get_card_style()
        super().__init__(parent, **style, **kwargs)

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                **get_label_style("subtitle"),
                anchor="w",
            )
            self.title_label.pack(fill="x", padx=CARD_PAD_X, pady=(CARD_PAD_Y, 4))
            self.content_frame.pack(fill="both", expand=True, padx=CARD_PAD_X, pady=(0, CARD_PAD_Y))
        else:
            self.content_frame.pack(fill="both", expand=True, padx=CARD_PAD_X, pady=CARD_PAD_Y)


class SettingRow(ctk.CTkFrame):
    """A single setting row with label and control."""

    def __init__(self, parent, label, description=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Left side: label and description
        self.label_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_frame.pack(side="left", fill="x", expand=True)

        self.label = ctk.CTkLabel(
            self.label_frame,
            text=label,
            **get_label_style("default"),
            anchor="w",
        )
        self.label.pack(fill="x")

        if description:
            self.description = ctk.CTkLabel(
                self.label_frame,
                text=description,
                **get_label_style("help"),
                anchor="w",
            )
            self.description.pack(fill="x")

        # Right side: control (added by caller)
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(side="right")


class StatusIndicator(ctk.CTkFrame):
    """Status indicator with colored dot and text."""

    def __init__(self, parent, status="inactive", text=""):
        super().__init__(parent, fg_color="transparent")

        self.dot = ctk.CTkLabel(
            self,
            text="",
            width=10,
            height=10,
            corner_radius=5,
            fg_color=get_status_color(status),
        )
        self.dot.pack(side="left", padx=(0, 6))

        self.text_label = ctk.CTkLabel(
            self,
            text=text,
            **get_label_style("default"),
        )
        self.text_label.pack(side="left")

    def set_status(self, status, text=None):
        """Update the status indicator."""
        self.dot.configure(fg_color=get_status_color(status))
        if text is not None:
            self.text_label.configure(text=text)


class SettingsWindow:
    """Modern settings dialog window with sidebar navigation."""

    def __init__(self, current_config, on_save_callback=None):
        self.config = current_config.copy()
        self.on_save_callback = on_save_callback
        self.window = None
        self.devices_list = []
        self.noise_test_stream = None
        self.noise_test_running = False

        # Navigation state
        self.current_section = "general"
        self.nav_items = {}
        self.sections = {}

        # Search state
        self.searchable_items = []  # List of (section_id, widget, original_text) tuples
        self.current_search_query = ""

        # Custom data (preserved across saves)
        self.custom_dictionary = self.config.get("custom_dictionary", {})
        self.custom_vocabulary = self.config.get("custom_vocabulary", [])
        self.custom_commands = self.config.get("custom_commands", {})

    def show(self):
        """Show the settings window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        # Create main window
        self.window = ctk.CTk()
        self.window.title(WINDOW_CONFIG["title"])
        self.window.geometry(f"{WINDOW_CONFIG['width']}x{WINDOW_CONFIG['height']}")
        self.window.minsize(WINDOW_CONFIG["min_width"], WINDOW_CONFIG["min_height"])
        self.window.configure(fg_color=SLATE_900)

        # Set window icon
        try:
            icon_path = resource_path("assets/logo/murmurtone-logo-icon.ico")
            self.window.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")

        # Center on screen
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - WINDOW_CONFIG["width"]) // 2
        y = (screen_height - WINDOW_CONFIG["height"]) // 2
        self.window.geometry(f"+{x}+{y}")

        # Create layout
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

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.window.mainloop()

    def _create_sidebar(self):
        """Create the sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self.window,
            width=SIDEBAR_WIDTH,
            fg_color=SLATE_800,
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App title in sidebar
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(20, 28))

        ctk.CTkLabel(
            title_frame,
            text=config.APP_NAME,
            font=("", 20, "bold"),
            text_color=SLATE_100,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Settings",
            font=("", 13),
            text_color=SLATE_400,
        ).pack(anchor="w", pady=(2, 0))

        # Recording section
        SectionHeader(self.sidebar, "Recording").pack(
            fill="x", padx=12, pady=(0, 4)
        )

        self._add_nav_item("general", "General", icon=None)
        self._add_nav_item("audio", "Audio", icon=None)

        # Processing section
        SectionHeader(self.sidebar, "Processing").pack(
            fill="x", padx=12, pady=(16, 4)
        )

        self._add_nav_item("recognition", "Recognition", icon=None)
        self._add_nav_item("text", "Text", icon=None)
        self._add_nav_item("advanced", "Advanced", icon=None)

        # System section
        SectionHeader(self.sidebar, "System").pack(
            fill="x", padx=12, pady=(16, 4)
        )

        self._add_nav_item("about", "About", icon=None)

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent", height=1).pack(
            fill="both", expand=True
        )

        # Search box
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            search_frame,
            text="SEARCH",
            font=("", 11, "bold"),
            text_color=SLATE_500,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._on_search_changed())

        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search settings...",
            **get_entry_style(),
        )
        self.search_entry.pack(fill="x")

        # Footer links
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(fill="x", padx=16, pady=16)

        # Version info
        ctk.CTkLabel(
            footer_frame,
            text=f"v{config.VERSION}",
            font=("", 11),
            text_color=SLATE_400,
        ).pack(anchor="w")

        # Links
        links_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        links_frame.pack(anchor="w", pady=(6, 0))

        privacy_link = ctk.CTkLabel(
            links_frame,
            text="Privacy",
            font=("", 11),
            text_color=PRIMARY,
            cursor="hand2",
        )
        privacy_link.pack(side="left")
        privacy_link.bind("<Button-1>", lambda e: webbrowser.open("https://murmurtone.com/privacy"))

        ctk.CTkLabel(
            links_frame,
            text=" | ",
            font=("", 11),
            text_color=SLATE_500,
        ).pack(side="left")

        terms_link = ctk.CTkLabel(
            links_frame,
            text="Terms",
            font=("", 11),
            text_color=PRIMARY,
            cursor="hand2",
        )
        terms_link.pack(side="left")
        terms_link.bind("<Button-1>", lambda e: webbrowser.open("https://murmurtone.com/terms"))

    def _add_nav_item(self, section_id, text, icon=None):
        """Add a navigation item to the sidebar."""
        nav_item = NavItem(
            self.sidebar,
            text=text,
            icon=icon,
            command=lambda: self._show_section(section_id),
        )
        nav_item.pack(fill="x", padx=12, pady=2)
        self.nav_items[section_id] = nav_item

    def _create_content_area(self):
        """Create the main content area."""
        self.content_area = ctk.CTkFrame(
            self.window,
            fg_color=SLATE_900,
            corner_radius=0,
        )
        self.content_area.pack(side="right", fill="both", expand=True)

        # Header with section title
        self.header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=60)
        self.header.pack(fill="x", padx=PAD_SPACIOUS, pady=(PAD_SPACIOUS, 0))
        self.header.pack_propagate(False)

        self.section_title = ctk.CTkLabel(
            self.header,
            text="",
            **get_label_style("title"),
            anchor="w",
        )
        self.section_title.pack(side="left", fill="x", expand=True)

        # Scrollable content
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.content_area,
            fg_color="transparent",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Separator line above footer
        separator = ctk.CTkFrame(self.content_area, fg_color=SLATE_700, height=1)
        separator.pack(fill="x", padx=0, pady=0)

        # Footer with buttons - subtle background to distinguish from content
        self.footer = ctk.CTkFrame(self.content_area, fg_color=SLATE_800, height=56, corner_radius=0)
        self.footer.pack(fill="x", padx=0, pady=0)
        self.footer.pack_propagate(False)

        ctk.CTkButton(
            self.footer,
            text="Save",
            width=100,
            **get_button_style("primary"),
            command=self.save,
        ).pack(side="left", padx=(PAD_SPACIOUS, 8), pady=PAD_DEFAULT)

        ctk.CTkButton(
            self.footer,
            text="Cancel",
            width=100,
            **get_button_style("secondary"),
            command=self.close,
        ).pack(side="left", padx=(0, 8), pady=PAD_DEFAULT)

        ctk.CTkButton(
            self.footer,
            text="Reset to Defaults",
            width=140,
            **get_button_style("ghost"),
            command=self.reset_defaults,
        ).pack(side="right", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

    def _show_section(self, section_id):
        """Show a specific section in the content area."""
        # Update nav item states
        for nav_id, nav_item in self.nav_items.items():
            nav_item.set_active(nav_id == section_id)

        # Hide all sections
        for section in self.sections.values():
            section.pack_forget()

        # Show selected section
        if section_id in self.sections:
            self.sections[section_id].pack(fill="both", expand=True)

        # Update header
        titles = {
            "general": "General",
            "audio": "Audio",
            "recognition": "Recognition",
            "text": "Text Processing",
            "advanced": "Advanced",
            "about": "About",
        }
        self.section_title.configure(text=titles.get(section_id, section_id.title()))
        self.current_section = section_id

    def _create_general_section(self):
        """Create the General settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["general"] = section

        # Recording card
        recording_card = Card(section, title="Recording")
        recording_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("general", recording_card, "Recording hotkey push-to-talk mode language")

        # Hotkey
        hotkey_row = SettingRow(
            recording_card.content_frame,
            "Push-to-Talk Hotkey",
            "Press and hold to record audio",
        )
        hotkey_row.pack(fill="x", pady=(0, 12))

        self.hotkey_capture = HotkeyCapture(
            hotkey_row.control_frame,
            initial_hotkey=self.config.get("hotkey", "scroll_lock"),
        )
        self.hotkey_capture.pack()

        # Recording mode
        mode_row = SettingRow(
            recording_card.content_frame,
            "Recording Mode",
            "How recording stops",
        )
        mode_row.pack(fill="x", pady=(0, 12))

        self.mode_var = ctk.StringVar(value=self.config.get("recording_mode", "push_to_talk"))
        mode_combo = ctk.CTkComboBox(
            mode_row.control_frame,
            values=["push_to_talk", "toggle", "auto_stop"],
            variable=self.mode_var,
            width=160,
            state="readonly",
            **get_dropdown_style(),
        )
        mode_combo.pack()
        make_combobox_clickable(mode_combo)
        Tooltip(mode_combo,
            "Push-to-Talk: Hold key to record\n"
            "Toggle: Press once to start, again to stop\n"
            "Auto-stop: Stops when you pause speaking")

        # Language
        lang_row = SettingRow(
            recording_card.content_frame,
            "Language",
            "Primary transcription language",
        )
        lang_row.pack(fill="x", pady=(0, 12))

        self.lang_var = ctk.StringVar(
            value=settings_logic.language_code_to_label(
                self.config.get("language", "auto")
            )
        )
        lang_combo = ctk.CTkComboBox(
            lang_row.control_frame,
            values=settings_logic.get_language_labels(),
            variable=self.lang_var,
            width=160,
            state="readonly",
            **get_dropdown_style(),
        )
        lang_combo.pack()
        make_combobox_clickable(lang_combo)

        # Output card
        output_card = Card(section, title="Output")
        output_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("general", output_card, "Output auto-paste clipboard preview")

        # Auto-paste
        autopaste_row = SettingRow(
            output_card.content_frame,
            "Auto-paste",
            "Automatically paste transcribed text",
        )
        autopaste_row.pack(fill="x", pady=(0, 12))

        self.autopaste_var = ctk.BooleanVar(value=self.config.get("auto_paste", True))
        autopaste_switch = ctk.CTkSwitch(
            autopaste_row.control_frame,
            text="",
            variable=self.autopaste_var,
            **get_switch_style(),
        )
        autopaste_switch.pack()

        # Paste mode
        paste_mode_row = SettingRow(
            output_card.content_frame,
            "Paste Method",
            "How text is inserted",
        )
        paste_mode_row.pack(fill="x", pady=(0, 12))

        self.paste_mode_var = ctk.StringVar(value=self.config.get("paste_mode", "clipboard"))
        paste_mode_combo = ctk.CTkComboBox(
            paste_mode_row.control_frame,
            values=["clipboard", "type"],
            variable=self.paste_mode_var,
            width=120,
            state="readonly",
            **get_dropdown_style(),
        )
        paste_mode_combo.pack()
        make_combobox_clickable(paste_mode_combo)
        Tooltip(paste_mode_combo,
            "Clipboard: Copies to clipboard, then pastes\n"
            "Type: Types each character (slowest, most compatible)")

        # Preview window card
        preview_card = Card(section, title="Preview Window")
        preview_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Preview enabled
        preview_row = SettingRow(
            preview_card.content_frame,
            "Show Preview",
            "Display transcription preview overlay",
        )
        preview_row.pack(fill="x", pady=(0, 12))

        self.preview_enabled_var = ctk.BooleanVar(
            value=self.config.get("preview_enabled", True)
        )
        preview_switch = ctk.CTkSwitch(
            preview_row.control_frame,
            text="",
            variable=self.preview_enabled_var,
            **get_switch_style(),
        )
        preview_switch.pack()

        # Preview position
        position_row = SettingRow(
            preview_card.content_frame,
            "Position",
        )
        position_row.pack(fill="x", pady=(0, 12))

        self.preview_position_var = ctk.StringVar(
            value=self.config.get("preview_position", "bottom_right")
        )
        position_combo = ctk.CTkComboBox(
            position_row.control_frame,
            values=["top_left", "top_right", "bottom_left", "bottom_right", "center"],
            variable=self.preview_position_var,
            width=140,
            state="readonly",
            **get_dropdown_style(),
        )
        position_combo.pack()
        make_combobox_clickable(position_combo)

        # Preview theme
        theme_row = SettingRow(
            preview_card.content_frame,
            "Theme",
        )
        theme_row.pack(fill="x", pady=(0, 12))

        self.preview_theme_var = ctk.StringVar(
            value=self.config.get("preview_theme", "dark")
        )
        theme_combo = ctk.CTkComboBox(
            theme_row.control_frame,
            values=["dark", "light"],
            variable=self.preview_theme_var,
            width=100,
            state="readonly",
            **get_dropdown_style(),
        )
        theme_combo.pack()
        make_combobox_clickable(theme_combo)

        # Startup card
        startup_card = Card(section, title="Startup")
        startup_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Start with Windows
        startup_row = SettingRow(
            startup_card.content_frame,
            "Start with Windows",
            "Launch automatically on login",
        )
        startup_row.pack(fill="x")

        self.startup_var = ctk.BooleanVar(
            value=self.config.get("start_with_windows", False)
        )
        startup_switch = ctk.CTkSwitch(
            startup_row.control_frame,
            text="",
            variable=self.startup_var,
            **get_switch_style(),
        )
        startup_switch.pack()

    def _create_audio_section(self):
        """Create the Audio settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["audio"] = section

        # Input device card
        device_card = Card(section, title="Input Device")
        device_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("audio", device_card, "Input Device microphone sample rate")

        # Device selection
        device_row = SettingRow(
            device_card.content_frame,
            "Microphone",
            "Select your audio input device",
        )
        device_row.pack(fill="x", pady=(0, 12))

        self.devices_list = settings_logic.get_input_devices()
        display_names = [name for name, _ in self.devices_list]
        current_device = settings_logic.get_device_display_name(
            self.config.get("input_device"),
            self.devices_list,
        )

        self.device_var = ctk.StringVar(value=current_device)
        self.device_combo = ctk.CTkComboBox(
            device_row.control_frame,
            values=display_names,
            variable=self.device_var,
            width=240,
            state="readonly",
            **get_dropdown_style(),
        )
        self.device_combo.pack()
        make_combobox_clickable(self.device_combo)

        # Refresh button
        refresh_row = ctk.CTkFrame(device_card.content_frame, fg_color="transparent")
        refresh_row.pack(fill="x", pady=(0, 12))

        self.refresh_btn = ctk.CTkButton(
            refresh_row,
            text="Refresh Devices",
            width=120,
            **get_button_style("secondary"),
            command=self.refresh_devices,
        )
        self.refresh_btn.pack(side="left")

        # Sample rate
        rate_row = SettingRow(
            device_card.content_frame,
            "Sample Rate",
            "Audio sample rate in Hz",
        )
        rate_row.pack(fill="x")

        sample_rate = self.config.get("sample_rate", 16000)
        self.rate_var = ctk.StringVar(
            value=SAMPLE_RATE_OPTIONS.get(sample_rate, SAMPLE_RATE_OPTIONS[16000])
        )
        rate_combo = ctk.CTkComboBox(
            rate_row.control_frame,
            values=list(SAMPLE_RATE_OPTIONS.values()),
            variable=self.rate_var,
            width=220,
            state="readonly",
            **get_dropdown_style(),
        )
        rate_combo.pack()
        make_combobox_clickable(rate_combo)

        # Noise gate card
        gate_card = Card(section, title="Noise Gate")
        gate_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("audio", gate_card, "Noise Gate threshold filter background noise")

        # Enable noise gate
        gate_enable_row = SettingRow(
            gate_card.content_frame,
            "Enable Noise Gate",
            "Filter out background noise below threshold",
        )
        gate_enable_row.pack(fill="x", pady=(0, 12))

        self.noise_gate_var = ctk.BooleanVar(
            value=self.config.get("noise_gate_enabled", False)
        )
        gate_switch = ctk.CTkSwitch(
            gate_enable_row.control_frame,
            text="",
            variable=self.noise_gate_var,
            **get_switch_style(),
        )
        gate_switch.pack()

        # Combined noise gate level meter with draggable threshold (Discord-style)
        self.noise_threshold_var = ctk.IntVar(
            value=self.config.get("noise_gate_threshold_db", -40)
        )

        meter_row = ctk.CTkFrame(gate_card.content_frame, fg_color="transparent")
        meter_row.pack(fill="x", pady=(0, 12))

        # Canvas for audio meter with interactive threshold
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

        # Level bar (shows current audio level)
        self.noise_level_bar = self.noise_level_canvas.create_rectangle(
            0, 0, 0, self.meter_height, fill=SUCCESS, width=0
        )

        # Threshold marker (draggable)
        thresh_x = self._db_to_x(self.noise_threshold_var.get())
        self.threshold_marker = self.noise_level_canvas.create_line(
            thresh_x, 0, thresh_x, self.meter_height,
            fill=PRIMARY_LIGHT, width=3
        )

        # Make threshold marker draggable
        self.noise_level_canvas.bind("<Button-1>", self._on_threshold_click)
        self.noise_level_canvas.bind("<B1-Motion>", self._on_threshold_drag)

        # dB label
        self.threshold_label = ctk.CTkLabel(
            meter_row,
            text=f"{self.noise_threshold_var.get()} dB",
            width=60,
            **get_label_style("default"),
        )
        self.threshold_label.pack(side="left", padx=(8, 0))
        Tooltip(self.noise_level_canvas,
            "Click or drag to set noise gate threshold\n"
            "Audio below this level is ignored\n"
            "Try -40 for quiet rooms, -50 for noisy environments")

        # Update label when threshold changes
        def update_threshold_label(*args):
            self.threshold_label.configure(text=f"{self.noise_threshold_var.get()} dB")
        self.noise_threshold_var.trace_add("write", update_threshold_label)

        # Test button
        test_row = ctk.CTkFrame(gate_card.content_frame, fg_color="transparent")
        test_row.pack(fill="x")

        self.noise_test_btn = ctk.CTkButton(
            test_row,
            text="Test",
            width=80,
            **get_button_style("secondary"),
            command=self.toggle_noise_test,
        )
        self.noise_test_btn.pack(side="left")

        # Audio feedback card
        feedback_card = Card(section, title="Audio Feedback")
        feedback_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Enable audio feedback
        feedback_row = SettingRow(
            feedback_card.content_frame,
            "Enable Sounds",
            "Play sounds for recording states",
        )
        feedback_row.pack(fill="x", pady=(0, 12))

        self.feedback_var = ctk.BooleanVar(
            value=self.config.get("audio_feedback", True)
        )
        feedback_switch = ctk.CTkSwitch(
            feedback_row.control_frame,
            text="",
            variable=self.feedback_var,
            **get_switch_style(),
        )
        feedback_switch.pack()

        # Individual sound type toggles (shown/hidden based on master toggle)
        self.sound_toggles_frame = ctk.CTkFrame(
            feedback_card.content_frame, fg_color="transparent"
        )
        self.sound_toggles_frame.pack(fill="x", pady=(0, 12), padx=(20, 0))

        # Processing sound toggle
        processing_row = SettingRow(
            self.sound_toggles_frame,
            "Processing",
            "Sound when transcription starts",
        )
        processing_row.pack(fill="x", pady=(0, 8))

        self.sound_processing_var = ctk.BooleanVar(
            value=self.config.get("sound_processing", True)
        )
        processing_switch = ctk.CTkSwitch(
            processing_row.control_frame,
            text="",
            variable=self.sound_processing_var,
            **get_switch_style(),
        )
        processing_switch.pack()

        # Success sound toggle
        success_row = SettingRow(
            self.sound_toggles_frame,
            "Success",
            "Sound when transcription completes",
        )
        success_row.pack(fill="x", pady=(0, 8))

        self.sound_success_var = ctk.BooleanVar(
            value=self.config.get("sound_success", True)
        )
        success_switch = ctk.CTkSwitch(
            success_row.control_frame,
            text="",
            variable=self.sound_success_var,
            **get_switch_style(),
        )
        success_switch.pack()

        # Error sound toggle
        error_row = SettingRow(
            self.sound_toggles_frame,
            "Error",
            "Sound when transcription fails",
        )
        error_row.pack(fill="x", pady=(0, 8))

        self.sound_error_var = ctk.BooleanVar(
            value=self.config.get("sound_error", True)
        )
        error_switch = ctk.CTkSwitch(
            error_row.control_frame,
            text="",
            variable=self.sound_error_var,
            **get_switch_style(),
        )
        error_switch.pack()

        # Command sound toggle
        command_row = SettingRow(
            self.sound_toggles_frame,
            "Command",
            "Sound when voice command recognized",
        )
        command_row.pack(fill="x", pady=(0, 8))

        self.sound_command_var = ctk.BooleanVar(
            value=self.config.get("sound_command", True)
        )
        command_switch = ctk.CTkSwitch(
            command_row.control_frame,
            text="",
            variable=self.sound_command_var,
            **get_switch_style(),
        )
        command_switch.pack()

        # Show/hide sound toggles based on master toggle
        def toggle_sound_options(*args):
            if self.feedback_var.get():
                self.sound_toggles_frame.pack(fill="x", pady=(0, 12), padx=(20, 0))
            else:
                self.sound_toggles_frame.pack_forget()

        self.feedback_var.trace_add("write", toggle_sound_options)

        # Set initial visibility
        if not self.feedback_var.get():
            self.sound_toggles_frame.pack_forget()

        # Volume slider
        volume_row = SettingRow(
            feedback_card.content_frame,
            "Volume",
        )
        volume_row.pack(fill="x")

        volume_control = ctk.CTkFrame(volume_row.control_frame, fg_color="transparent")
        volume_control.pack()

        self.volume_var = ctk.IntVar(
            value=self.config.get("audio_feedback_volume", 100)
        )
        volume_slider = ctk.CTkSlider(
            volume_control,
            from_=0,
            to=100,
            variable=self.volume_var,
            width=150,
            button_color=PRIMARY,
            button_hover_color=PRIMARY_LIGHT,
            progress_color=PRIMARY,
        )
        volume_slider.pack(side="left")

        self.volume_label = ctk.CTkLabel(
            volume_control,
            text=f"{self.volume_var.get()}%",
            width=40,
            **get_label_style("default"),
        )
        self.volume_label.pack(side="left", padx=(8, 0))

        def update_volume_label(*args):
            self.volume_label.configure(text=f"{self.volume_var.get()}%")
        self.volume_var.trace_add("write", update_volume_label)

    def _create_recognition_section(self):
        """Create the Recognition settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["recognition"] = section

        # Model card
        model_card = Card(section, title="Whisper Model")
        model_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("recognition", model_card, "Whisper Model size accuracy speed tiny base small medium large")

        # Model selection
        model_row = SettingRow(
            model_card.content_frame,
            "Model Size",
            "Larger models are more accurate but slower",
        )
        model_row.pack(fill="x", pady=(0, 12))

        self.model_var = ctk.StringVar(value=self.config.get("model_size", "base"))
        model_combo = ctk.CTkComboBox(
            model_row.control_frame,
            values=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            variable=self.model_var,
            width=140,
            state="readonly",
            **get_dropdown_style(),
        )
        model_combo.pack()
        make_combobox_clickable(model_combo)
        Tooltip(model_combo,
            "Tiny: Fastest, less accurate\n"
            "Base: Good balance (recommended)\n"
            "Small/Medium: More accurate, slower\n"
            "Large: Most accurate, requires GPU")

        # Auto-stop settings
        autostop_row = SettingRow(
            model_card.content_frame,
            "Silence Duration",
            "Seconds of silence before auto-stop",
        )
        autostop_row.pack(fill="x")

        self.silence_var = ctk.StringVar(
            value=str(self.config.get("silence_duration_sec", 2.0))
        )
        silence_entry = ctk.CTkEntry(
            autostop_row.control_frame,
            textvariable=self.silence_var,
            width=80,
            **get_entry_style(),
        )
        silence_entry.pack()

        # GPU card
        gpu_card = Card(section, title="GPU Acceleration")
        gpu_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("recognition", gpu_card, "GPU Acceleration CUDA processing mode auto cpu balanced quality")

        # GPU status
        status_row = ctk.CTkFrame(gpu_card.content_frame, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 12))

        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()

        self.gpu_status = StatusIndicator(
            status_row,
            status="success" if is_available else "error",
            text=gpu_name or status_msg,
        )
        self.gpu_status.pack(side="left")

        ctk.CTkButton(
            status_row,
            text="Refresh",
            width=80,
            **get_button_style("ghost"),
            command=self.refresh_gpu_status,
        ).pack(side="right")

        # Processing mode dropdown
        processing_row = SettingRow(
            gpu_card.content_frame,
            "Processing Mode",
            "Auto uses GPU if available, otherwise CPU",
        )
        processing_row.pack(fill="x")

        processing_mode = self.config.get("processing_mode", "auto")
        # Convert mode to display label
        mode_label = config.PROCESSING_MODE_LABELS.get(processing_mode, "Auto")

        self.processing_mode_var = ctk.StringVar(value=mode_label)
        mode_combo = ctk.CTkComboBox(
            processing_row.control_frame,
            values=list(config.PROCESSING_MODE_LABELS.values()),
            variable=self.processing_mode_var,
            width=160,
            state="readonly",
            **get_dropdown_style(),
        )
        mode_combo.pack()
        make_combobox_clickable(mode_combo)
        Tooltip(mode_combo,
            "Auto: GPU if available, else CPU\n"
            "CPU: Always use CPU\n"
            "GPU - Balanced: GPU with float16 (faster)\n"
            "GPU - Quality: GPU with float32 (better quality)")

        # Translation card
        translation_card = Card(section, title="Translation")
        translation_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Enable translation
        trans_enable_row = SettingRow(
            translation_card.content_frame,
            "Enable Translation",
            "Translate speech to English",
        )
        trans_enable_row.pack(fill="x", pady=(0, 12))

        self.translation_enabled_var = ctk.BooleanVar(
            value=self.config.get("translation_enabled", False)
        )
        trans_switch = ctk.CTkSwitch(
            trans_enable_row.control_frame,
            text="",
            variable=self.translation_enabled_var,
            **get_switch_style(),
        )
        trans_switch.pack()

        # Source language
        trans_lang_row = SettingRow(
            translation_card.content_frame,
            "Source Language",
            "Language being spoken",
        )
        trans_lang_row.pack(fill="x")

        self.trans_lang_var = ctk.StringVar(
            value=settings_logic.language_code_to_label(
                self.config.get("translation_source_language", "auto")
            )
        )
        trans_lang_combo = ctk.CTkComboBox(
            trans_lang_row.control_frame,
            values=settings_logic.get_language_labels(),
            variable=self.trans_lang_var,
            width=160,
            state="readonly",
            **get_dropdown_style(),
        )
        trans_lang_combo.pack()
        make_combobox_clickable(trans_lang_combo)

    def _create_text_section(self):
        """Create the Text Processing settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["text"] = section

        # Voice commands card
        commands_card = Card(section, title="Voice Commands")
        commands_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("text", commands_card, "Voice Commands period comma new line scratch that")

        # Enable voice commands
        cmd_enable_row = SettingRow(
            commands_card.content_frame,
            "Enable Voice Commands",
            'Execute commands like "new line", "period"',
        )
        cmd_enable_row.pack(fill="x", pady=(0, 12))

        self.voice_commands_var = ctk.BooleanVar(
            value=self.config.get("voice_commands_enabled", True)
        )
        cmd_switch = ctk.CTkSwitch(
            cmd_enable_row.control_frame,
            text="",
            variable=self.voice_commands_var,
            **get_switch_style(),
        )
        cmd_switch.pack()

        # Scratch that
        scratch_row = SettingRow(
            commands_card.content_frame,
            '"Scratch That" Command',
            "Delete the last transcription",
        )
        scratch_row.pack(fill="x")

        self.scratch_that_var = ctk.BooleanVar(
            value=self.config.get("scratch_that_enabled", True)
        )
        scratch_switch = ctk.CTkSwitch(
            scratch_row.control_frame,
            text="",
            variable=self.scratch_that_var,
            **get_switch_style(),
        )
        scratch_switch.pack()

        # Filler removal card
        filler_card = Card(section, title="Filler Word Removal")
        filler_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Enable filler removal
        filler_enable_row = SettingRow(
            filler_card.content_frame,
            "Remove Filler Words",
            'Remove "um", "uh", "like", etc.',
        )
        filler_enable_row.pack(fill="x", pady=(0, 12))

        self.filler_var = ctk.BooleanVar(
            value=self.config.get("filler_removal_enabled", False)
        )
        filler_switch = ctk.CTkSwitch(
            filler_enable_row.control_frame,
            text="",
            variable=self.filler_var,
            **get_switch_style(),
        )
        filler_switch.pack()

        # Aggressive mode
        aggressive_row = SettingRow(
            filler_card.content_frame,
            "Aggressive Mode",
            "Remove more hesitation patterns",
        )
        aggressive_row.pack(fill="x")

        self.filler_aggressive_var = ctk.BooleanVar(
            value=self.config.get("filler_removal_aggressive", False)
        )
        aggressive_switch = ctk.CTkSwitch(
            aggressive_row.control_frame,
            text="",
            variable=self.filler_aggressive_var,
            **get_switch_style(),
        )
        aggressive_switch.pack()

        # Dictionary card
        dict_card = Card(section, title="Custom Dictionary")
        dict_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("text", dict_card, "Custom Dictionary vocabulary replacements words")

        dict_info = ctk.CTkLabel(
            dict_card.content_frame,
            text="Add word replacements and custom vocabulary for better recognition.",
            **get_label_style("help"),
            wraplength=400,
        )
        dict_info.pack(anchor="w", pady=(0, 8))

        dict_btn_row = ctk.CTkFrame(dict_card.content_frame, fg_color="transparent")
        dict_btn_row.pack(fill="x")

        ctk.CTkButton(
            dict_btn_row,
            text="Edit Dictionary",
            width=120,
            **get_button_style("secondary"),
            command=self._open_dictionary_editor,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            dict_btn_row,
            text="Edit Vocabulary",
            width=120,
            **get_button_style("secondary"),
            command=self._open_vocabulary_editor,
        ).pack(side="left")

    def _create_advanced_section(self):
        """Create the Advanced settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["advanced"] = section

        # AI Cleanup card
        ai_card = Card(section, title="AI Text Cleanup")
        ai_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("advanced", ai_card, "AI Text Cleanup Ollama LLM grammar professional casual creative")

        # Enable AI cleanup
        ai_enable_row = SettingRow(
            ai_card.content_frame,
            "Enable AI Cleanup",
            "Use local LLM to polish transcriptions",
        )
        ai_enable_row.pack(fill="x", pady=(0, 12))

        self.ai_cleanup_var = ctk.BooleanVar(
            value=self.config.get("ai_cleanup_enabled", False)
        )
        ai_switch = ctk.CTkSwitch(
            ai_enable_row.control_frame,
            text="",
            variable=self.ai_cleanup_var,
            **get_switch_style(),
        )
        ai_switch.pack()

        # Ollama status
        status_row = ctk.CTkFrame(ai_card.content_frame, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 12))

        self.ollama_status = StatusIndicator(
            status_row,
            status="inactive",
            text="Checking Ollama...",
        )
        self.ollama_status.pack(side="left")

        ctk.CTkButton(
            status_row,
            text="Check",
            width=70,
            **get_button_style("ghost"),
            command=lambda: self.check_ollama_status_bg(),
        ).pack(side="right")

        # Check Ollama status on load
        self.check_ollama_status_bg()

        # AI Mode
        ai_mode_row = SettingRow(
            ai_card.content_frame,
            "Cleanup Mode",
            "Grammar: fix errors. Professional/Casual/Creative: rewrite style",
        )
        ai_mode_row.pack(fill="x", pady=(0, 12))

        self.ai_mode_var = ctk.StringVar(value=self.config.get("ai_cleanup_mode", "grammar"))
        ai_mode_combo = ctk.CTkComboBox(
            ai_mode_row.control_frame,
            values=["grammar", "professional", "casual", "creative"],
            variable=self.ai_mode_var,
            width=140,
            state="readonly",
            **get_dropdown_style(),
        )
        ai_mode_combo.pack()
        make_combobox_clickable(ai_mode_combo)

        # Formality
        formality_row = SettingRow(
            ai_card.content_frame,
            "Formality Level",
            "Adjust language register for your audience",
        )
        formality_row.pack(fill="x", pady=(0, 12))

        self.ai_formality_var = ctk.StringVar(
            value=self.config.get("ai_formality_level", "neutral")
        )
        formality_combo = ctk.CTkComboBox(
            formality_row.control_frame,
            values=["casual", "neutral", "formal"],
            variable=self.ai_formality_var,
            width=100,
            state="readonly",
            **get_dropdown_style(),
        )
        formality_combo.pack()
        make_combobox_clickable(formality_combo)

        # Model selection
        model_row = SettingRow(
            ai_card.content_frame,
            "Ollama Model",
            "Local AI model (llama3.2 recommended)",
        )
        model_row.pack(fill="x")

        self.ai_model_var = ctk.StringVar(
            value=self.config.get("ollama_model", "llama3.2")
        )
        model_entry = ctk.CTkEntry(
            model_row.control_frame,
            textvariable=self.ai_model_var,
            width=140,
            **get_entry_style(),
        )
        model_entry.pack()

        # History card
        history_card = Card(section, title="Transcription History")
        history_card.pack(fill="x", pady=(0, PAD_DEFAULT))
        self._register_searchable("advanced", history_card, "Transcription History recent viewer")

        history_info = ctk.CTkLabel(
            history_card.content_frame,
            text="Recent transcriptions are stored for review.",
            **get_label_style("help"),
        )
        history_info.pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(
            history_card.content_frame,
            text="View History",
            width=120,
            **get_button_style("secondary"),
            command=self._open_history_viewer,
        ).pack(anchor="w")

    def _create_about_section(self):
        """Create the About section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["about"] = section

        # App info card
        info_card = Card(section, title="Application Info")
        info_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        # Logo/title area
        title_frame = ctk.CTkFrame(info_card.content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            title_frame,
            text=config.APP_NAME,
            font=("", 24, "bold"),
            text_color=PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="100% Offline Voice Typing",
            **get_label_style("help"),
        ).pack(anchor="w")

        # Version info
        info_grid = ctk.CTkFrame(info_card.content_frame, fg_color="transparent")
        info_grid.pack(fill="x")

        info_items = [
            ("Version", config.VERSION),
            ("Build", "Desktop"),
            ("Platform", "Windows"),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(info_grid, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=label,
                width=100,
                anchor="w",
                **get_label_style("help"),
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value,
                anchor="w",
                **get_label_style("default"),
            ).pack(side="left")

        # License card
        license_card = Card(section, title="License")
        license_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        license_status = license.get_license_status_info(self.config)
        if license_status.get("status") == "active":
            status_text = f"Licensed: {license_status.get('status_message', 'Active')}"
            status_color = SUCCESS
        elif license_status.get("status") == "trial":
            status_text = license_status.get("status_message", "Trial Mode")
            status_color = WARNING
        else:
            status_text = license_status.get("status_message", "Free Version")
            status_color = SLATE_500

        ctk.CTkLabel(
            license_card.content_frame,
            text=status_text,
            text_color=status_color,
        ).pack(anchor="w", pady=(0, 8))

        license_btn_row = ctk.CTkFrame(license_card.content_frame, fg_color="transparent")
        license_btn_row.pack(fill="x")

        ctk.CTkButton(
            license_btn_row,
            text="Enter License Key",
            width=140,
            **get_button_style("primary"),
            command=self._open_license_dialog,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            license_btn_row,
            text="Buy License",
            width=100,
            **get_button_style("secondary"),
            command=lambda: webbrowser.open("https://murmurtone.com/pricing"),
        ).pack(side="left")

        # Links card
        links_card = Card(section, title="Links")
        links_card.pack(fill="x", pady=(0, PAD_DEFAULT))

        links = [
            ("Website", "https://murmurtone.com"),
            ("Documentation", "https://murmurtone.com/docs"),
            ("Support", "https://murmurtone.com/support"),
            ("Privacy Policy", "https://murmurtone.com/privacy"),
            ("Terms of Service", "https://murmurtone.com/terms"),
        ]

        for text, url in links:
            link = ctk.CTkLabel(
                links_card.content_frame,
                text=text,
                text_color=PRIMARY,
                cursor="hand2",
            )
            link.pack(anchor="w", pady=2)
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def refresh_devices(self):
        """Refresh the list of available input devices."""
        # Show loading state
        self.refresh_btn.configure(text="Refreshing...", state="disabled")
        self.window.update()

        # Refresh device list
        self.devices_list = settings_logic.get_input_devices()
        display_names = [name for name, _ in self.devices_list]
        self.device_combo.configure(values=display_names)

        # Check if current selection is still valid
        current = self.device_var.get()
        if current not in display_names:
            if display_names:
                self.device_var.set(display_names[0])

        # Reset button state
        self.refresh_btn.configure(text="Refresh Devices", state="normal")

    def refresh_gpu_status(self):
        """Refresh GPU status display."""
        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()
        self.gpu_status.set_status(
            "success" if is_available else "error",
            gpu_name or status_msg,
        )

    def toggle_noise_test(self):
        """Start or stop the noise gate level test."""
        if self.noise_test_running:
            self.stop_noise_test()
        else:
            self.start_noise_test()

    def start_noise_test(self):
        """Start audio level monitoring for noise gate testing."""
        if self.noise_test_running:
            return

        self.noise_test_running = True
        self.noise_test_btn.configure(text="Stop")

        # Get selected device
        device_info = self.get_selected_device_info()
        device_idx = device_info.get("index") if device_info else None

        try:
            rate_str = self.rate_var.get()
            sample_rate = int(rate_str.split()[0])  # Parse "16000 Hz - ..." -> 16000
        except (ValueError, IndexError):
            sample_rate = 16000

        def audio_callback(indata, frames, time, status):
            if not self.noise_test_running:
                return

            # Calculate RMS level
            rms = np.sqrt(np.mean(indata ** 2))
            db = settings_logic.rms_to_db(rms)

            # Update meter on main thread
            self.window.after(0, self._update_meter, db)

        try:
            self.noise_test_stream = sd.InputStream(
                device=device_idx,
                samplerate=sample_rate,
                channels=1,
                callback=audio_callback,
            )
            self.noise_test_stream.start()
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not start audio: {e}")
            self.stop_noise_test()

    def stop_noise_test(self):
        """Stop audio level monitoring."""
        self.noise_test_running = False
        if self.noise_test_stream:
            self.noise_test_stream.stop()
            self.noise_test_stream.close()
            self.noise_test_stream = None
        self.noise_test_btn.configure(text="Test")
        # Reset meter
        self.noise_level_canvas.coords(self.noise_level_bar, 0, 0, 0, self.meter_height)

    def _update_meter(self, db):
        """Update the audio level meter display."""
        threshold = self.noise_threshold_var.get()
        is_gated = db < threshold

        # Calculate width
        linear = settings_logic.db_to_linear(db, -60, -20)
        width = int(linear * self.meter_width)
        width = max(0, min(self.meter_width, width))

        # Get color
        color = get_meter_color((db + 60) / 40, is_gated)

        # Update bar
        self.noise_level_canvas.coords(self.noise_level_bar, 0, 0, width, self.meter_height)
        self.noise_level_canvas.itemconfig(self.noise_level_bar, fill=color)

        # Update threshold marker
        thresh_x = settings_logic.db_to_linear(threshold, -60, -20) * self.meter_width
        self.noise_level_canvas.coords(
            self.threshold_marker, thresh_x, 0, thresh_x, self.meter_height
        )

    def _db_to_x(self, db):
        """Convert dB value (-60 to -20) to x pixel position."""
        return int((db + 60) / 40 * self.meter_width)

    def _x_to_db(self, x):
        """Convert x pixel position to dB value (-60 to -20)."""
        x = max(0, min(self.meter_width, x))
        return int(-60 + (x / self.meter_width) * 40)

    def _on_threshold_click(self, event):
        """Handle click on the level meter to set threshold."""
        db = self._x_to_db(event.x)
        self.noise_threshold_var.set(db)
        self._update_threshold_marker_position()

    def _on_threshold_drag(self, event):
        """Handle drag on the level meter to adjust threshold."""
        db = self._x_to_db(event.x)
        self.noise_threshold_var.set(db)
        self._update_threshold_marker_position()

    def _update_threshold_marker_position(self):
        """Update the threshold marker position on the canvas."""
        x = self._db_to_x(self.noise_threshold_var.get())
        self.noise_level_canvas.coords(self.threshold_marker, x, 0, x, self.meter_height)

    def get_selected_device_info(self):
        """Get the device_info dict for the currently selected device."""
        selected = self.device_var.get()
        if "(unavailable)" in selected:
            return self.config.get("input_device")
        for display_name, device_info in self.devices_list:
            if display_name == selected:
                return device_info
        return None

    def check_ollama_status_bg(self):
        """Check Ollama status in background thread."""
        def check():
            try:
                import requests
                url = self.config.get("ollama_url", "http://localhost:11434")
                response = requests.get(f"{url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    if models:
                        self.window.after(0, lambda: self.ollama_status.set_status(
                            "success", f"Connected ({len(models)} models)"
                        ))
                    else:
                        self.window.after(0, lambda: self.ollama_status.set_status(
                            "warning", "Connected (no models)"
                        ))
                else:
                    self.window.after(0, lambda: self.ollama_status.set_status(
                        "error", "Connection failed"
                    ))
            except Exception:
                self.window.after(0, lambda: self.ollama_status.set_status(
                    "error", "Ollama not running"
                ))

        threading.Thread(target=check, daemon=True).start()

    def _open_dictionary_editor(self):
        """Open dictionary editor dialog."""
        # Create modal dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Custom Dictionary")
        dialog.geometry("800x600")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 800) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 600) // 2
        dialog.geometry(f"+{x}+{y}")

        # Configure dialog colors
        dialog.configure(fg_color=SLATE_900)

        # Header
        header = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Custom Dictionary",
            **get_label_style("title"),
        ).pack(side="left", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Info label
        info_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        info_frame.pack(fill="x", padx=PAD_SPACIOUS, pady=(PAD_DEFAULT, 0))

        ctk.CTkLabel(
            info_frame,
            text="Define text replacements. When Whisper transcribes the 'Original' word, it will be replaced with 'Replacement'.",
            **get_label_style("help"),
            wraplength=750,
            anchor="w",
            justify="left",
        ).pack(fill="x")

        # Dictionary list area
        list_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=SLATE_800,
            corner_radius=8,
        )
        list_frame.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Column headers
        headers_frame = ctk.CTkFrame(list_frame, fg_color=SLATE_700, corner_radius=6)
        headers_frame.pack(fill="x", pady=(0, 8), padx=2)

        ctk.CTkLabel(
            headers_frame,
            text="Original",
            **get_label_style("default"),
            width=300,
            anchor="w",
        ).pack(side="left", padx=12, pady=8)

        ctk.CTkLabel(
            headers_frame,
            text="Replacement",
            **get_label_style("default"),
            width=300,
            anchor="w",
        ).pack(side="left", padx=12, pady=8)

        # Container for dictionary items
        items_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        items_container.pack(fill="both", expand=True)

        # Load existing dictionary items
        dict_items = []
        for original, replacement in self.custom_dictionary.items():
            dict_items.append({"original": original, "replacement": replacement})

        # Function to refresh the display
        def refresh_display():
            # Clear existing items
            for widget in items_container.winfo_children():
                widget.destroy()

            # Display all items
            for item in dict_items:
                item_frame = ctk.CTkFrame(items_container, fg_color=SLATE_700, corner_radius=6)
                item_frame.pack(fill="x", pady=(0, 4), padx=2)

                ctk.CTkLabel(
                    item_frame,
                    text=item["original"],
                    **get_label_style("default"),
                    width=300,
                    anchor="w",
                ).pack(side="left", padx=12, pady=8)

                ctk.CTkLabel(
                    item_frame,
                    text=item["replacement"],
                    **get_label_style("default"),
                    width=300,
                    anchor="w",
                ).pack(side="left", padx=12, pady=8)

                remove_btn = ctk.CTkButton(
                    item_frame,
                    text="Remove",
                    width=80,
                    **get_button_style("ghost"),
                    command=lambda i=item: remove_item(i),
                )
                remove_btn.pack(side="right", padx=12, pady=8)

        def add_item():
            # Create a dialog to add new item
            add_dialog = ctk.CTkToplevel(dialog)
            add_dialog.title("Add Dictionary Entry")
            add_dialog.geometry("400x200")
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            add_dialog.configure(fg_color=SLATE_900)

            # Center on parent
            add_dialog.update_idletasks()
            dx = dialog.winfo_x() + (dialog.winfo_width() - 400) // 2
            dy = dialog.winfo_y() + (dialog.winfo_height() - 200) // 2
            add_dialog.geometry(f"+{dx}+{dy}")

            content = ctk.CTkFrame(add_dialog, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_SPACIOUS)

            # Original field
            ctk.CTkLabel(
                content,
                text="Original:",
                **get_label_style("default"),
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

            original_entry = ctk.CTkEntry(content, **get_entry_style())
            original_entry.pack(fill="x", pady=(0, 12))
            original_entry.focus()

            # Replacement field
            ctk.CTkLabel(
                content,
                text="Replacement:",
                **get_label_style("default"),
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

            replacement_entry = ctk.CTkEntry(content, **get_entry_style())
            replacement_entry.pack(fill="x", pady=(0, 16))

            # Buttons
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack(fill="x")

            def save_new_item():
                original = original_entry.get().strip()
                replacement = replacement_entry.get().strip()

                if not original or not replacement:
                    messagebox.showwarning("Invalid Entry", "Both fields are required.", parent=add_dialog)
                    return

                # Check for duplicates
                if any(item["original"].lower() == original.lower() for item in dict_items):
                    messagebox.showwarning("Duplicate Entry", "An entry with this original text already exists.", parent=add_dialog)
                    return

                dict_items.append({"original": original, "replacement": replacement})
                refresh_display()
                add_dialog.destroy()

            ctk.CTkButton(
                btn_frame,
                text="Add",
                width=100,
                **get_button_style("primary"),
                command=save_new_item,
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                width=100,
                **get_button_style("secondary"),
                command=add_dialog.destroy,
            ).pack(side="left")

        def remove_item(item):
            dict_items.remove(item)
            refresh_display()

        def save_dictionary():
            # Update the custom_dictionary with new items
            self.custom_dictionary = {item["original"]: item["replacement"] for item in dict_items}
            dialog.destroy()

        # Initial display
        refresh_display()

        # Footer with buttons
        footer = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=56)
        footer.pack(fill="x", padx=0, pady=0)
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Add Entry",
            width=100,
            **get_button_style("primary"),
            command=add_item,
        ).pack(side="left", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        ctk.CTkButton(
            footer,
            text="Save",
            width=100,
            **get_button_style("primary"),
            command=save_dictionary,
        ).pack(side="right", padx=(0, PAD_SPACIOUS), pady=PAD_DEFAULT)

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=100,
            **get_button_style("secondary"),
            command=dialog.destroy,
        ).pack(side="right", padx=(8, 0), pady=PAD_DEFAULT)

    def _open_vocabulary_editor(self):
        """Open vocabulary editor dialog."""
        # Create modal dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Custom Vocabulary")
        dialog.geometry("600x500")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 600) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        # Configure dialog colors
        dialog.configure(fg_color=SLATE_900)

        # Header
        header = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Custom Vocabulary",
            **get_label_style("title"),
        ).pack(side="left", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Info label
        info_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        info_frame.pack(fill="x", padx=PAD_SPACIOUS, pady=(PAD_DEFAULT, 0))

        ctk.CTkLabel(
            info_frame,
            text="Add custom words and technical terms to improve recognition accuracy. Examples: TensorFlow, Kubernetes, Dr. Smith",
            **get_label_style("help"),
            wraplength=550,
            anchor="w",
            justify="left",
        ).pack(fill="x")

        # Vocabulary list area
        list_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=SLATE_800,
            corner_radius=8,
        )
        list_frame.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Container for vocabulary items
        items_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        items_container.pack(fill="both", expand=True)

        # Load existing vocabulary items
        vocab_items = list(self.custom_vocabulary)  # Make a copy

        # Function to refresh the display
        def refresh_display():
            # Clear existing items
            for widget in items_container.winfo_children():
                widget.destroy()

            # Display all items
            for word in vocab_items:
                item_frame = ctk.CTkFrame(items_container, fg_color=SLATE_700, corner_radius=6)
                item_frame.pack(fill="x", pady=(0, 4), padx=2)

                ctk.CTkLabel(
                    item_frame,
                    text=word,
                    **get_label_style("default"),
                    anchor="w",
                ).pack(side="left", fill="x", expand=True, padx=12, pady=8)

                remove_btn = ctk.CTkButton(
                    item_frame,
                    text="Remove",
                    width=80,
                    **get_button_style("ghost"),
                    command=lambda w=word: remove_word(w),
                )
                remove_btn.pack(side="right", padx=12, pady=8)

        def add_word():
            # Create a dialog to add new word
            add_dialog = ctk.CTkToplevel(dialog)
            add_dialog.title("Add Vocabulary Word")
            add_dialog.geometry("400x150")
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            add_dialog.configure(fg_color=SLATE_900)

            # Center on parent
            add_dialog.update_idletasks()
            dx = dialog.winfo_x() + (dialog.winfo_width() - 400) // 2
            dy = dialog.winfo_y() + (dialog.winfo_height() - 150) // 2
            add_dialog.geometry(f"+{dx}+{dy}")

            content = ctk.CTkFrame(add_dialog, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_SPACIOUS)

            # Word field
            ctk.CTkLabel(
                content,
                text="Word or phrase:",
                **get_label_style("default"),
                anchor="w",
            ).pack(fill="x", pady=(0, 4))

            word_entry = ctk.CTkEntry(content, **get_entry_style())
            word_entry.pack(fill="x", pady=(0, 16))
            word_entry.focus()

            # Buttons
            btn_frame = ctk.CTkFrame(content, fg_color="transparent")
            btn_frame.pack(fill="x")

            def save_new_word():
                word = word_entry.get().strip()

                if not word:
                    messagebox.showwarning("Invalid Entry", "Word field is required.", parent=add_dialog)
                    return

                # Check for duplicates (case-insensitive)
                if any(w.lower() == word.lower() for w in vocab_items):
                    messagebox.showwarning("Duplicate Entry", "This word already exists in the vocabulary.", parent=add_dialog)
                    return

                vocab_items.append(word)
                refresh_display()
                add_dialog.destroy()

            ctk.CTkButton(
                btn_frame,
                text="Add",
                width=100,
                **get_button_style("primary"),
                command=save_new_word,
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                width=100,
                **get_button_style("secondary"),
                command=add_dialog.destroy,
            ).pack(side="left")

        def remove_word(word):
            vocab_items.remove(word)
            refresh_display()

        def save_vocabulary():
            # Update the custom_vocabulary with new items
            self.custom_vocabulary = vocab_items[:]
            dialog.destroy()

        # Initial display
        refresh_display()

        # Footer with buttons
        footer = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=56)
        footer.pack(fill="x", padx=0, pady=0)
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Add Word",
            width=100,
            **get_button_style("primary"),
            command=add_word,
        ).pack(side="left", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        ctk.CTkButton(
            footer,
            text="Save",
            width=100,
            **get_button_style("primary"),
            command=save_vocabulary,
        ).pack(side="right", padx=(0, PAD_SPACIOUS), pady=PAD_DEFAULT)

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=100,
            **get_button_style("secondary"),
            command=dialog.destroy,
        ).pack(side="right", padx=(8, 0), pady=PAD_DEFAULT)

    def _open_history_viewer(self):
        """Open history viewer dialog."""
        # Create modal dialog
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Transcription History")
        dialog.geometry("700x500")
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 700) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 500) // 2
        dialog.geometry(f"+{x}+{y}")

        # Configure dialog colors
        dialog.configure(fg_color=SLATE_900)

        # Header
        header = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="Transcription History",
            **get_label_style("title"),
        ).pack(side="left", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Buttons frame
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="Refresh",
            width=80,
            **get_button_style("secondary"),
            command=lambda: self._refresh_history_list(listbox, status_label),
        )
        refresh_btn.pack(side="left", padx=(0, 8))

        clear_btn = ctk.CTkButton(
            btn_frame,
            text="Clear All",
            width=80,
            **get_button_style("ghost"),
            command=lambda: self._clear_history(listbox, status_label, dialog),
        )
        clear_btn.pack(side="left")

        # Status label
        status_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        status_frame.pack(fill="x", padx=PAD_SPACIOUS, pady=(PAD_DEFAULT, 0))

        status_label = ctk.CTkLabel(
            status_frame,
            text="",
            **get_label_style("help"),
            anchor="w",
        )
        status_label.pack(fill="x")

        # Scrollable listbox area
        listbox_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color=SLATE_800,
            corner_radius=8,
        )
        listbox_frame.pack(fill="both", expand=True, padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

        # Create a custom listbox using frames
        listbox = listbox_frame  # We'll add items as frames
        listbox.items = []  # Track items for refreshing

        # Load initial history
        self._refresh_history_list(listbox, status_label)

        # Footer with close button
        footer = ctk.CTkFrame(dialog, fg_color=SLATE_800, corner_radius=0, height=56)
        footer.pack(fill="x", padx=0, pady=0)
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            **get_button_style("secondary"),
            command=dialog.destroy,
        ).pack(side="right", padx=PAD_SPACIOUS, pady=PAD_DEFAULT)

    def _refresh_history_list(self, listbox, status_label):
        """Refresh the history list display."""
        # Clear existing items
        for item in listbox.items:
            item.destroy()
        listbox.items.clear()

        # Load history from file
        history = text_processor.TranscriptionHistory(persist=True)
        entries = history.get_all()  # Returns newest first

        if not entries:
            status_label.configure(text="No transcriptions in history")
            return

        status_label.configure(text=f"{len(entries)} transcription(s)")

        # Display entries
        for entry in entries:
            item_frame = ctk.CTkFrame(listbox, fg_color=SLATE_700, corner_radius=6)
            item_frame.pack(fill="x", pady=(0, 8), padx=2)

            # Timestamp and char count
            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=12, pady=(8, 4))

            timestamp_str = entry.get("timestamp", "")
            if timestamp_str:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp_str)
                    timestamp_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    timestamp_display = timestamp_str
            else:
                timestamp_display = "Unknown time"

            ctk.CTkLabel(
                info_frame,
                text=timestamp_display,
                **get_label_style("help"),
                anchor="w",
            ).pack(side="left")

            char_count = entry.get("char_count", 0)
            ctk.CTkLabel(
                info_frame,
                text=f"{char_count} characters",
                **get_label_style("help"),
                anchor="e",
            ).pack(side="right")

            # Text content
            text_content = entry.get("text", "")
            # Truncate if too long for display
            display_text = text_content if len(text_content) <= 200 else text_content[:200] + "..."

            text_label = ctk.CTkLabel(
                item_frame,
                text=display_text,
                **get_label_style("default"),
                anchor="w",
                justify="left",
                wraplength=640,
            )
            text_label.pack(fill="x", padx=12, pady=(0, 8))

            listbox.items.append(item_frame)

    def _clear_history(self, listbox, status_label, dialog):
        """Clear all transcription history after confirmation."""
        if not messagebox.askyesno(
            "Clear History",
            "Delete all transcription history?\nThis cannot be undone.",
            parent=dialog
        ):
            return

        # Clear the history
        history = text_processor.TranscriptionHistory(persist=True)
        history.clear()

        # Refresh the display
        self._refresh_history_list(listbox, status_label)

    def _open_license_dialog(self):
        """Open license entry dialog."""
        # TODO: Implement license dialog
        messagebox.showinfo("Coming Soon", "License dialog will be available soon.")

    # =========================================================================
    # Save/Reset/Close
    # =========================================================================

    def save(self):
        """Save settings."""
        # Validate inputs - parse numeric value from descriptive string
        rate_str = self.rate_var.get()
        rate_value = rate_str.split()[0]  # "16000 Hz - Speech (Recommended)" -> "16000"
        sample_rate = settings_logic.validate_sample_rate(rate_value)
        silence_duration = settings_logic.validate_silence_duration(self.silence_var.get())

        # Get selected device info
        device_info = self.get_selected_device_info()

        # Convert language labels back to codes
        lang_code = settings_logic.language_label_to_code(self.lang_var.get())
        trans_lang_code = settings_logic.language_label_to_code(self.trans_lang_var.get())

        # Convert processing mode label back to code
        processing_mode = settings_logic.processing_mode_label_to_code(
            self.processing_mode_var.get()
        )

        new_config = {
            "model_size": self.model_var.get(),
            "language": lang_code,
            "translation_enabled": self.translation_enabled_var.get(),
            "translation_source_language": trans_lang_code,
            "sample_rate": sample_rate,
            "hotkey": self.hotkey_capture.get_hotkey(),
            "recording_mode": self.mode_var.get(),
            "silence_duration_sec": silence_duration,
            "audio_feedback": self.feedback_var.get(),
            "input_device": device_info,
            "auto_paste": self.autopaste_var.get(),
            "paste_mode": self.paste_mode_var.get(),
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
            "preview_position": self.preview_position_var.get(),
            "preview_theme": self.preview_theme_var.get(),
        }

        config.save_config(new_config)

        # Handle Windows startup setting
        config.set_startup_enabled(self.startup_var.get())

        if self.on_save_callback:
            self.on_save_callback(new_config)

    def reset_defaults(self):
        """Reset all settings to defaults."""
        if not messagebox.askyesno(
            "Reset to Defaults",
            "Reset all settings to defaults?\nThis will not affect Windows startup setting."
        ):
            return

        defaults = settings_logic.get_defaults()

        # General
        self.model_var.set(defaults["model_size"])
        self.lang_var.set(settings_logic.language_code_to_label(defaults["language"]))
        self.mode_var.set(defaults["recording_mode"])
        self.silence_var.set(str(defaults["silence_duration_sec"]))
        self.hotkey_capture.set_hotkey(defaults["hotkey"])

        # Output
        self.autopaste_var.set(defaults["auto_paste"])
        self.paste_mode_var.set(defaults["paste_mode"])
        self.preview_enabled_var.set(defaults.get("preview_enabled", True))
        self.preview_position_var.set(defaults.get("preview_position", "bottom_right"))
        self.preview_theme_var.set(defaults.get("preview_theme", "dark"))

        # Audio
        self.rate_var.set(
            SAMPLE_RATE_OPTIONS.get(defaults["sample_rate"], SAMPLE_RATE_OPTIONS[16000])
        )
        self.noise_gate_var.set(defaults.get("noise_gate_enabled", False))
        self.noise_threshold_var.set(defaults.get("noise_gate_threshold_db", -40))
        self.feedback_var.set(defaults["audio_feedback"])
        self.volume_var.set(defaults.get("audio_feedback_volume", 100))
        self.sound_processing_var.set(defaults.get("sound_processing", True))
        self.sound_success_var.set(defaults.get("sound_success", True))
        self.sound_error_var.set(defaults.get("sound_error", True))
        self.sound_command_var.set(defaults.get("sound_command", True))

        # Recognition
        default_mode = defaults.get("processing_mode", "auto")
        default_mode_label = config.PROCESSING_MODE_LABELS.get(default_mode, "Auto")
        self.processing_mode_var.set(default_mode_label)
        self.translation_enabled_var.set(defaults["translation_enabled"])

        # Text
        self.voice_commands_var.set(defaults.get("voice_commands_enabled", True))
        self.scratch_that_var.set(defaults.get("scratch_that_enabled", True))
        self.filler_var.set(defaults.get("filler_removal_enabled", False))
        self.filler_aggressive_var.set(defaults.get("filler_removal_aggressive", False))

        # Advanced
        self.ai_cleanup_var.set(defaults.get("ai_cleanup_enabled", False))
        self.ai_mode_var.set(defaults.get("ai_cleanup_mode", "grammar"))
        self.ai_formality_var.set(defaults.get("ai_formality_level", "neutral"))

    def _register_searchable(self, section_id, widget, text):
        """Register a widget and text as searchable.

        Args:
            section_id: Section ID where this item belongs
            widget: The widget to highlight/show when searching
            text: The searchable text content
        """
        self.searchable_items.append((section_id, widget, text.lower()))

    def _on_search_changed(self):
        """Handle search query changes."""
        query = self.search_var.get().strip().lower()
        self.current_search_query = query

        if not query:
            # Clear search - restore all sections
            self._clear_search_highlights()
            return

        # Find matching sections and items
        matching_sections = set()
        for section_id, widget, text in self.searchable_items:
            if query in text:
                matching_sections.add(section_id)

        # If we have matches, highlight them
        if matching_sections:
            # Switch to first matching section
            first_section = sorted(matching_sections)[0]
            self._show_section(first_section)

            # Highlight matching nav items
            for section_id, nav_item in self.nav_items.items():
                if section_id in matching_sections:
                    nav_item.configure(fg_color=PRIMARY_DARK)
                else:
                    nav_item.configure(fg_color=SLATE_700 if section_id == self.current_section else "transparent")

    def _clear_search_highlights(self):
        """Clear all search highlights."""
        # Reset nav item colors
        for section_id, nav_item in self.nav_items.items():
            active = section_id == self.current_section
            style = get_nav_item_style(active=active)
            nav_item.configure(**style)

    def close(self):
        """Close the settings window."""
        # Stop any audio test
        if self.noise_test_running:
            self.stop_noise_test()

        if self.window:
            self.window.destroy()
            self.window = None


def open_settings(current_config, on_save_callback=None):
    """Open the settings window.

    Args:
        current_config: Current configuration dictionary
        on_save_callback: Optional callback called with new config when saved
    """
    settings = SettingsWindow(current_config, on_save_callback)
    settings.show()


if __name__ == "__main__":
    """Entry point when run as standalone script."""
    import config as cfg

    # Set working directory to script location
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Load config
    try:
        current = cfg.load_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        # Use defaults if config load fails
        current = cfg.DEFAULT_CONFIG

    # Open settings window
    open_settings(current)
