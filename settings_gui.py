"""
MurmurTone Settings GUI - V2
Rebuilt to exactly match the HTML mockup (Slack Examples/settings-mockup-v2.html)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import webbrowser
import os
import sys
from PIL import Image

import config
import settings_logic

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

# Font family (matches HTML mockup line 52)
FONT_FAMILY = "Segoe UI"

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


# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


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

    def show(self):
        """Show the settings window."""
        self.window = ctk.CTkToplevel()
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

        # Focus window
        self.window.focus_force()
        self.window.lift()
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
        sep.pack(fill="x", padx=SPACE_LG, pady=(0, SPACE_LG))

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
        header_row.pack(fill="x", pady=(0, SPACE_LG))

        self.page_title = ctk.CTkLabel(
            header_row,
            text="General",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=SLATE_100,
            anchor="w",
        )
        self.page_title.pack(side="left")

        # Close button (X) - 32x32, transparent, SLATE_400 text
        close_btn = ctk.CTkButton(
            header_row,
            text="✕",
            width=32,
            height=32,
            corner_radius=6,
            fg_color="transparent",
            hover_color=SLATE_700,
            text_color=SLATE_400,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16),
            command=self.close,
        )
        close_btn.pack(side="right")

        # Border below header
        border = ctk.CTkFrame(header_container, fg_color=SLATE_600, height=1)
        border.pack(fill="x")

        # Scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.content_area,
            fg_color="transparent",
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=SPACE_XL, pady=SPACE_LG)

        # Footer with Save/Cancel buttons
        footer_sep = ctk.CTkFrame(self.content_area, fg_color=SLATE_700, height=1)
        footer_sep.pack(fill="x")

        footer = ctk.CTkFrame(self.content_area, fg_color=SLATE_800, height=56, corner_radius=0)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        # Save button - primary style
        save_btn = ctk.CTkButton(
            footer,
            text="Save",
            width=100,
            height=36,
            corner_radius=8,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            text_color="white",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self.save,
        )
        save_btn.pack(side="left", padx=(SPACE_XL, SPACE_SM), pady=10)

        # Cancel button - secondary style
        cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            width=100,
            height=36,
            corner_radius=8,
            fg_color=SLATE_800,
            hover_color=SLATE_700,
            border_color=SLATE_600,
            border_width=1,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self.close,
        )
        cancel_btn.pack(side="left", pady=10)

        # Reset button - ghost style, right aligned
        reset_btn = ctk.CTkButton(
            footer,
            text="Reset to Defaults",
            width=140,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color=SLATE_700,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            command=self.reset_defaults,
        )
        reset_btn.pack(side="right", padx=SPACE_XL, pady=10)

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

    # =========================================================================
    # SECTION BUILDERS
    # =========================================================================

    def _create_section_header(self, parent, title, description=None):
        """Create a section header matching mockup exactly.

        Returns a frame for adding controls to.
        """
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_2XL))

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
        content.pack(fill="x", pady=(SPACE_LG, 0))

        return content

    def _create_toggle_setting(self, parent, label, help_text=None, variable=None, command=None):
        """Create toggle setting matching mockup: [toggle] [label + help on right]."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, SPACE_MD))

        # Toggle switch on left - 40x22
        switch = ctk.CTkSwitch(
            row,
            text="",
            variable=variable,
            command=command,
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
        switch.pack(side="left", pady=(2, 0))

        # Text content on right
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", padx=(SPACE_MD, 0), fill="x", expand=True)

        # Label - 13px, SLATE_200
        lbl = ctk.CTkLabel(
            text_frame,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        lbl.pack(fill="x")

        # Help text - 11px, SLATE_500
        if help_text:
            help_lbl = ctk.CTkLabel(
                text_frame,
                text=help_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=SLATE_500,
                anchor="w",
            )
            help_lbl.pack(fill="x", pady=(SPACE_XS, 0))

        return switch

    def _create_labeled_dropdown(self, parent, label, values, variable, help_text=None, width=160):
        """Create labeled dropdown: label above, dropdown below, help below."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_LG))

        # Label - 13px, SLATE_200
        lbl = ctk.CTkLabel(
            container,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            anchor="w",
        )
        lbl.pack(fill="x")

        # Dropdown - matches mockup styling
        dropdown = ctk.CTkComboBox(
            container,
            values=values,
            variable=variable,
            width=width,
            height=36,
            corner_radius=8,
            border_width=1,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            button_color=SLATE_700,
            button_hover_color=SLATE_600,
            dropdown_fg_color=SLATE_800,
            dropdown_hover_color=SLATE_700,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="readonly",
        )
        dropdown.pack(anchor="w", pady=(SPACE_SM, 0))

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

        return dropdown

    def _create_labeled_entry(self, parent, label, variable, help_text=None, width=80):
        """Create labeled entry: label above, entry below, help below."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_LG))

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
        entry.pack(anchor="w", pady=(SPACE_SM, 0))

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

    def _create_checkbox_setting(self, parent, label, variable):
        """Create checkbox setting matching mockup."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, SPACE_SM))

        checkbox = ctk.CTkCheckBox(
            row,
            text=label,
            variable=variable,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=SLATE_200,
            fg_color=PRIMARY,
            hover_color=PRIMARY_DARK,
            border_color=SLATE_500,
            checkmark_color="white",
            corner_radius=4,
            border_width=2,
            width=18,
            height=18,
        )
        checkbox.pack(anchor="w")

        return checkbox

    def _create_hotkey_button(self, parent, initial_hotkey):
        """Create hotkey button matching mockup: [badge] Change."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, SPACE_LG))

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
        btn_frame.pack(anchor="w", pady=(SPACE_SM, 0))

        inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner.pack(padx=SPACE_LG, pady=SPACE_SM)

        # Hotkey badge
        self.hotkey_badge = ctk.CTkLabel(
            inner,
            text=self._format_hotkey(initial_hotkey),
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=SLATE_300,
            fg_color=SLATE_700,
            corner_radius=4,
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
            widget.bind("<Button-1>", lambda e: self._start_hotkey_capture())
            widget.bind("<Enter>", lambda e: btn_frame.configure(fg_color=SLATE_700, border_color=SLATE_500))
            widget.bind("<Leave>", lambda e: btn_frame.configure(fg_color=SLATE_800, border_color=SLATE_600) if not self.capturing else None)

        self.hotkey_btn_frame = btn_frame

        # Help text
        help_lbl = ctk.CTkLabel(
            container,
            text="Press and hold to record audio",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=SLATE_500,
            anchor="w",
        )
        help_lbl.pack(fill="x", pady=(SPACE_XS, 0))

    def _format_hotkey(self, hotkey):
        """Format hotkey for display."""
        if not hotkey:
            return "Not set"
        if isinstance(hotkey, dict):
            return config.hotkey_to_string(hotkey)
        parts = hotkey.split("+")
        formatted = [p.replace("_", " ").title() for p in parts]
        return " + ".join(formatted)

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
        dot.pack(side="left")
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
        )

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
        output = self._create_section_header(section, "Output", "Control what happens with transcribed text")

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
        self._create_labeled_dropdown(
            output,
            "Paste Method",
            values=list(PASTE_MODE_LABELS.values()),
            variable=self.paste_mode_var,
            help_text="How text is inserted",
            width=120,
        )

        # Preview Window section
        preview = self._create_section_header(section, "Preview Window", "Floating overlay showing transcription progress")

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
        startup = self._create_section_header(section, "Startup")

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
            width=280,
            height=36,
            corner_radius=8,
            fg_color=SLATE_800,
            border_color=SLATE_600,
            button_color=SLATE_700,
            text_color=SLATE_200,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            state="readonly",
        )
        self.device_combo.pack(side="left")

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
        gate = self._create_section_header(section, "Noise Gate", "Filter out background noise below a threshold")

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

        # Level indicator bar (will be clipped via canvas width)
        self.noise_level_bar = self.noise_level_canvas.create_rectangle(
            0, 0, 90, self.meter_height, fill="", width=0, state="hidden"
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
        self.noise_test_btn.pack(anchor="w")

        # Audio Feedback section
        feedback = self._create_section_header(section, "Audio Feedback", "Sound notifications for recording events")

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
        """Start microphone test."""
        self.noise_test_running = True
        self.noise_test_btn.configure(text="Stop Test", fg_color=ERROR, hover_color="#dc2626")
        # Actual audio testing would go here

    def stop_noise_test(self):
        """Stop microphone test."""
        self.noise_test_running = False
        self.noise_test_btn.configure(text="Test Microphone", fg_color=SLATE_800, hover_color=SLATE_700)

    # =========================================================================
    # RECOGNITION SECTION
    # =========================================================================

    def _create_recognition_section(self):
        """Create Recognition settings section."""
        section = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections["recognition"] = section

        # Whisper Model section (first section - no separator)
        model = self._create_section_header(section, "Whisper Model", "Choose the speech recognition model")

        self.model_var = ctk.StringVar(value=self.config.get("model_size", "base"))
        self._create_labeled_dropdown(
            model,
            "Model Size",
            values=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            variable=self.model_var,
            help_text="Larger models are more accurate but slower",
            width=140,
        )

        self.silence_var = ctk.StringVar(value=str(self.config.get("silence_duration_sec", 2.0)))
        self._create_labeled_entry(
            model,
            "Silence Duration",
            variable=self.silence_var,
            help_text="Seconds of silence before auto-stop",
            width=80,
        )

        # GPU Acceleration section
        gpu = self._create_section_header(section, "GPU Acceleration", "Use graphics card for faster processing")

        # GPU status
        gpu_status = ctk.CTkFrame(gpu, fg_color="transparent")
        gpu_status.pack(fill="x", pady=(0, SPACE_MD))

        status_row = ctk.CTkFrame(gpu_status, fg_color="transparent")
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
        trans = self._create_section_header(section, "Translation", "Translate spoken audio to English")

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

    def refresh_gpu_status(self):
        """Refresh GPU status display."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                self.gpu_status_dot.configure(fg_color=SUCCESS)
                self.gpu_status_text.configure(text=gpu_name)
            else:
                self.gpu_status_dot.configure(fg_color=SLATE_500)
                self.gpu_status_text.configure(text="No GPU detected")
        except ImportError:
            self.gpu_status_dot.configure(fg_color=SLATE_500)
            self.gpu_status_text.configure(text="PyTorch not installed")

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
        filler = self._create_section_header(section, "Filler Word Removal", "Clean up hesitation sounds from transcriptions")

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
        dictionary = self._create_section_header(section, "Custom Dictionary", "Add word replacements and custom vocabulary")

        dict_row = ctk.CTkFrame(dictionary, fg_color="transparent")
        dict_row.pack(fill="x")

        dict_btn = self._create_button(dict_row, "Edit Dictionary", self._edit_dictionary, width=140)
        dict_btn.pack(side="left")

        vocab_btn = self._create_button(dict_row, "Edit Vocabulary", self._edit_vocabulary, width=140)
        vocab_btn.pack(side="left", padx=(SPACE_SM, 0))

        # Text Shortcuts section
        shortcuts = self._create_section_header(section, "Text Shortcuts", "Trigger phrases that expand to text blocks")

        shortcuts_btn = self._create_button(shortcuts, "Edit Shortcuts", self._edit_shortcuts, width=140)
        shortcuts_btn.pack(anchor="w")

    def _edit_dictionary(self):
        """Open dictionary editor."""
        messagebox.showinfo("Dictionary", "Dictionary editor not implemented")

    def _edit_vocabulary(self):
        """Open vocabulary editor."""
        messagebox.showinfo("Vocabulary", "Vocabulary editor not implemented")

    def _edit_shortcuts(self):
        """Open shortcuts editor."""
        messagebox.showinfo("Shortcuts", "Shortcuts editor not implemented")

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
            values=["grammar", "professional", "casual", "creative"],
            variable=self.ai_mode_var,
            help_text="Grammar fixes or full rewrite styles",
            width=140,
        )

        # Formality level
        self.ai_formality_var = ctk.StringVar(value=self.config.get("ai_formality_level", "neutral"))
        self._create_labeled_dropdown(
            ai,
            "Formality Level",
            values=["casual", "neutral", "formal"],
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
        history = self._create_section_header(section, "Transcription History", "Recent transcriptions stored for review")

        history_btn = self._create_button(history, "View History", self._view_history, width=120)
        history_btn.pack(anchor="w")

    def _check_ollama(self):
        """Check Ollama connection."""
        try:
            import requests
            url = self.config.get("ollama_url", "http://localhost:11434")
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
        messagebox.showinfo("History", "History viewer not implemented")

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
            ("View on GitHub", "https://github.com/murmurtone/voice-typer"),
            ("Open Logs Folder", None),
            ("Report an Issue", "https://github.com/murmurtone/voice-typer/issues"),
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

        # System Info section
        sys_info = self._create_section_header(section, "System Information")

        info_text = []
        try:
            import sys
            info_text.append(f"Python: {sys.version.split()[0]}")
        except:
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

        info_label = ctk.CTkLabel(
            sys_info,
            text="\n".join(info_text),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=SLATE_400,
            anchor="w",
            justify="left",
        )
        info_label.pack(fill="x")

    def _open_logs_folder(self):
        """Open logs folder."""
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        os.startfile(logs_dir)

    # =========================================================================
    # SAVE / RESET / CLOSE
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

        new_config = {
            "model_size": self.model_var.get(),
            "language": lang_code,
            "translation_enabled": self.translation_enabled_var.get(),
            "translation_source_language": trans_lang_code,
            "sample_rate": sample_rate,
            "hotkey": self.hotkey,
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

    def reset_defaults(self):
        """Reset all settings to defaults."""
        if not messagebox.askyesno(
            "Reset to Defaults",
            "Reset all settings to defaults?"
        ):
            return

        defaults = settings_logic.get_defaults()

        self.model_var.set(defaults["model_size"])
        self.lang_var.set(settings_logic.language_code_to_label(defaults["language"]))
        self.mode_var.set(RECORDING_MODE_LABELS.get(defaults["recording_mode"], "Push-to-Talk"))
        self.silence_var.set(str(defaults["silence_duration_sec"]))
        self.autopaste_var.set(defaults["auto_paste"])
        self.paste_mode_var.set(PASTE_MODE_LABELS.get(defaults["paste_mode"], "Clipboard"))
        self.preview_enabled_var.set(defaults.get("preview_enabled", True))
        self.preview_position_var.set(PREVIEW_POSITION_LABELS.get(defaults.get("preview_position", "bottom_right"), "Bottom Right"))
        self.preview_theme_var.set(PREVIEW_THEME_LABELS.get(defaults.get("preview_theme", "dark"), "Dark"))
        self.preview_delay_var.set(str(defaults.get("preview_auto_hide_delay", 2.0)))
        self.rate_var.set(SAMPLE_RATE_OPTIONS.get(defaults["sample_rate"], SAMPLE_RATE_OPTIONS[16000]))
        self.noise_gate_var.set(defaults.get("noise_gate_enabled", False))
        self.noise_threshold_var.set(defaults.get("noise_gate_threshold_db", -40))
        self.feedback_var.set(defaults["audio_feedback"])
        self.volume_var.set(defaults.get("audio_feedback_volume", 100))
        self.voice_commands_var.set(defaults.get("voice_commands_enabled", True))
        self.scratch_that_var.set(defaults.get("scratch_that_enabled", True))
        self.filler_var.set(defaults.get("filler_removal_enabled", False))
        self.ai_cleanup_var.set(defaults.get("ai_cleanup_enabled", False))

    def close(self):
        """Close the settings window."""
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
