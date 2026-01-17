"""Python version check for MurmurTone.

This module checks that Python version is compatible (3.12 or 3.13).
Import this FIRST in entry points, before heavy dependencies.
"""
import sys

REQUIRED_MIN = (3, 12)
REQUIRED_MAX = (3, 14)


def check_python_version():
    """Check Python version, show error if incompatible.

    Returns True if version is acceptable.
    Exits with error dialog if version is wrong.
    Skips check when running as frozen exe (PyInstaller bundle).
    """
    # Skip for PyInstaller bundle - version is fixed at build time
    if getattr(sys, 'frozen', False):
        return True

    version = sys.version_info[:2]
    if version >= REQUIRED_MIN and version < REQUIRED_MAX:
        return True

    _show_version_error(version)
    sys.exit(1)


def _show_version_error(current):
    """Show tkinter error dialog for version mismatch."""
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()

    messagebox.showerror(
        "Python Version Error",
        f"MurmurTone requires Python 3.12 or 3.13\n\n"
        f"You are running Python {current[0]}.{current[1]}\n\n"
        f"Download Python 3.12 from:\n"
        f"https://www.python.org/downloads/"
    )
    root.destroy()


# Auto-check on import
check_python_version()
