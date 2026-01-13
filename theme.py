"""
MurmurTone V1 Theme - Slate + Teal

Color constants and styling helpers for CustomTkinter.
Based on the V1 website branding.
"""

# =============================================================================
# V1 Brand Colors - Teal Primary
# =============================================================================

# Primary - Teal accents
PRIMARY = "#0d9488"        # Main brand color, buttons, links
PRIMARY_DARK = "#0f766e"   # Hover states, pressed buttons
PRIMARY_LIGHT = "#14b8a6"  # Bright accents, highlights

# =============================================================================
# Slate - Neutral grays (dark mode)
# =============================================================================

SLATE_900 = "#0f172a"      # Darkest - window background
SLATE_800 = "#1e293b"      # Card backgrounds, sidebar
SLATE_700 = "#334155"      # Hover states, tooltip bg
SLATE_600 = "#475569"      # Borders, disabled elements
SLATE_500 = "#64748b"      # Help text, secondary labels
SLATE_400 = "#94a3b8"      # Placeholder text, section headers
SLATE_300 = "#cbd5e1"      # Nav items, lighter text
SLATE_200 = "#e2e8f0"      # Primary text (light on dark)
SLATE_100 = "#f1f5f9"      # Bright text, titles

# =============================================================================
# Semantic Colors
# =============================================================================

SUCCESS = "#10b981"        # Emerald green - OK states, recording active
WARNING = "#f59e0b"        # Amber - warnings, caution
ERROR = "#ef4444"          # Red - errors, critical

# =============================================================================
# CustomTkinter Color Mapping
# =============================================================================

# CTk widgets use these for theming
CTK_COLORS = {
    # Window & frames
    "bg": SLATE_900,
    "bg_secondary": SLATE_800,
    "bg_hover": SLATE_700,

    # Borders
    "border": SLATE_600,
    "border_light": SLATE_500,

    # Text
    "text": SLATE_200,
    "text_secondary": SLATE_500,
    "text_disabled": SLATE_600,

    # Interactive
    "button_fg": PRIMARY,
    "button_hover": PRIMARY_DARK,
    "button_text": "#ffffff",

    # Switches/toggles
    "switch_on": PRIMARY,
    "switch_off": SLATE_600,

    # Status
    "success": SUCCESS,
    "warning": WARNING,
    "error": ERROR,
}


# =============================================================================
# Widget Style Helpers
# =============================================================================

def get_card_style():
    """Style settings for card containers."""
    return {
        "fg_color": SLATE_800,
        "corner_radius": 12,
        "border_width": 1,
        "border_color": SLATE_600,
    }


def get_button_style(variant="primary"):
    """Style settings for buttons.

    Args:
        variant: "primary", "secondary", "danger", or "ghost"
    """
    styles = {
        "primary": {
            "fg_color": PRIMARY,
            "hover_color": PRIMARY_DARK,
            "text_color": "#ffffff",
            "corner_radius": 8,
            "cursor": "hand2",
        },
        "secondary": {
            "fg_color": SLATE_700,
            "hover_color": SLATE_600,
            "text_color": SLATE_200,
            "corner_radius": 8,
            "cursor": "hand2",
        },
        "danger": {
            "fg_color": ERROR,
            "hover_color": "#dc2626",
            "text_color": "#ffffff",
            "corner_radius": 8,
            "cursor": "hand2",
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": SLATE_700,
            "text_color": SLATE_200,
            "corner_radius": 8,
            "cursor": "hand2",
        },
    }
    return styles.get(variant, styles["primary"])


def get_entry_style():
    """Style settings for text entry fields."""
    return {
        "fg_color": SLATE_700,
        "border_color": SLATE_600,
        "border_width": 1,
        "text_color": SLATE_200,
        "placeholder_text_color": SLATE_500,
        "corner_radius": 6,
    }


def get_switch_style():
    """Style settings for toggle switches."""
    return {
        "button_color": PRIMARY,
        "button_hover_color": PRIMARY_LIGHT,
        "fg_color": SLATE_600,
        "progress_color": PRIMARY,
        "cursor": "hand2",
    }


def get_dropdown_style():
    """Style settings for dropdown/combobox."""
    return {
        "fg_color": SLATE_700,
        "border_color": SLATE_600,
        "button_color": SLATE_600,
        "button_hover_color": SLATE_500,
        "dropdown_fg_color": SLATE_700,
        "dropdown_hover_color": SLATE_600,
        "text_color": SLATE_200,
        "corner_radius": 6,
        "cursor": "hand2",
    }


def get_label_style(variant="default"):
    """Style settings for labels.

    Args:
        variant: "default", "title", "subtitle", "help", "link"
    """
    styles = {
        "default": {
            "text_color": SLATE_200,
            "font": ("", 13),
        },
        "title": {
            "text_color": SLATE_100,
            "font": ("", 20, "bold"),
        },
        "subtitle": {
            "text_color": SLATE_200,
            "font": ("", 15, "bold"),
        },
        "help": {
            "text_color": SLATE_400,  # Improved contrast from SLATE_500
            "font": ("", 11),
        },
        "link": {
            "text_color": PRIMARY,
            "font": ("", 12),
        },
    }
    return styles.get(variant, styles["default"])


# =============================================================================
# Sidebar Navigation Style
# =============================================================================

def get_nav_item_style(active=False):
    """Style for sidebar navigation items.

    Args:
        active: Whether this is the currently selected item
    """
    if active:
        return {
            "fg_color": PRIMARY,  # Stronger active state
            "text_color": "#ffffff",
            "hover_color": PRIMARY_DARK,
            "corner_radius": 8,
            "font": ("", 13),
        }
    return {
        "fg_color": "transparent",
        "text_color": SLATE_300,  # Lighter for better visibility
        "hover_color": SLATE_700,
        "corner_radius": 8,
        "font": ("", 13),
    }


def get_nav_section_style():
    """Style for sidebar section headers."""
    return {
        "text_color": SLATE_400,  # Improved from SLATE_500
        "font": ("", 11, "bold"),
    }


# =============================================================================
# Status Indicator Colors
# =============================================================================

def get_status_color(status):
    """Get the appropriate color for a status indicator.

    Args:
        status: "success", "warning", "error", "inactive", or "loading"
    """
    colors = {
        "success": SUCCESS,
        "warning": WARNING,
        "error": ERROR,
        "inactive": SLATE_600,
        "loading": PRIMARY,
    }
    return colors.get(status, SLATE_500)


# =============================================================================
# Audio Meter Colors
# =============================================================================

def get_meter_color(level, is_gated=False):
    """Get color for audio level meter based on level.

    Args:
        level: Audio level from 0.0 to 1.0
        is_gated: Whether the audio is currently gated (below threshold)
    """
    if is_gated:
        return SLATE_600  # Muted gray when gated
    if level < 0.5:
        return SUCCESS    # Green for normal
    if level < 0.75:
        return WARNING    # Yellow for getting loud
    return ERROR          # Red for clipping


# =============================================================================
# Spacing Constants
# =============================================================================

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
}

# Standard paddings
PAD_TIGHT = 4
PAD_DEFAULT = 12
PAD_SPACIOUS = 24

# Card internal padding
CARD_PAD_X = 20
CARD_PAD_Y = 16

# Sidebar dimensions
SIDEBAR_WIDTH = 220
NAV_ITEM_HEIGHT = 40


# =============================================================================
# Font Sizes
# =============================================================================

FONT_SIZES = {
    "xs": 10,
    "sm": 11,
    "base": 12,
    "lg": 14,
    "xl": 16,
    "2xl": 20,
}


# =============================================================================
# Window Configuration
# =============================================================================

WINDOW_CONFIG = {
    "title": "MurmurTone Settings",
    "width": 900,
    "height": 650,
    "min_width": 700,
    "min_height": 500,
}
