"""
Configuration management for Voice Typer.
Handles loading/saving settings to JSON file.
"""
import json
import os

# Default settings
DEFAULTS = {
    "model_size": "tiny.en",
    "sample_rate": 16000,
    "language": "en",
    "hotkey": {
        "ctrl": True,
        "shift": True,
        "alt": False,
        "key": "space"
    }
}

MODEL_OPTIONS = ["tiny.en", "base.en", "small.en", "medium.en"]
LANGUAGE_OPTIONS = ["en", "auto"]


def get_config_path():
    """Get path to settings.json in app directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "settings.json")


def load_config():
    """Load settings from JSON file, return defaults if not found."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                saved = json.load(f)
                # Merge with defaults to handle missing keys
                config = DEFAULTS.copy()
                config.update(saved)
                # Ensure hotkey has all required keys
                if "hotkey" in saved:
                    hotkey = DEFAULTS["hotkey"].copy()
                    hotkey.update(saved["hotkey"])
                    config["hotkey"] = hotkey
                return config
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULTS.copy()


def save_config(config):
    """Save settings to JSON file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def hotkey_to_string(hotkey):
    """Convert hotkey dict to display string like 'Ctrl+Shift+Space'."""
    parts = []
    if hotkey.get("ctrl"):
        parts.append("Ctrl")
    if hotkey.get("alt"):
        parts.append("Alt")
    if hotkey.get("shift"):
        parts.append("Shift")
    key = hotkey.get("key", "space")
    parts.append(key.capitalize() if len(key) > 1 else key.upper())
    return "+".join(parts)
