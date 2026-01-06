"""
Settings GUI for Voice Typer using tkinter.
"""
import tkinter as tk
from tkinter import ttk
import config


class HotkeyCapture:
    """Widget to capture hotkey combinations."""

    def __init__(self, parent, initial_hotkey):
        self.frame = ttk.Frame(parent)
        self.hotkey = initial_hotkey.copy()
        self.capturing = False

        self.label = ttk.Label(self.frame, text=config.hotkey_to_string(self.hotkey), width=20)
        self.label.pack(side=tk.LEFT, padx=(0, 5))

        self.button = ttk.Button(self.frame, text="Set Hotkey", command=self.start_capture)
        self.button.pack(side=tk.LEFT)

    def start_capture(self):
        self.capturing = True
        self.label.config(text="Press keys...")
        self.button.config(text="Press keys", state=tk.DISABLED)
        # Bind to root window for key capture
        self.frame.winfo_toplevel().bind("<KeyPress>", self.on_key)
        self.frame.winfo_toplevel().bind("<KeyRelease>", self.on_key_release)
        self.pressed_keys = set()
        self.main_key = None

    def on_key(self, event):
        if not self.capturing:
            return

        key_name = event.keysym.lower()

        # Track modifier keys
        if key_name in ("control_l", "control_r"):
            self.pressed_keys.add("ctrl")
        elif key_name in ("shift_l", "shift_r"):
            self.pressed_keys.add("shift")
        elif key_name in ("alt_l", "alt_r"):
            self.pressed_keys.add("alt")
        else:
            # This is the main key
            self.main_key = key_name

    def on_key_release(self, event):
        if not self.capturing:
            return

        # When a key is released and we have a main key, finalize
        if self.main_key:
            self.hotkey = {
                "ctrl": "ctrl" in self.pressed_keys,
                "shift": "shift" in self.pressed_keys,
                "alt": "alt" in self.pressed_keys,
                "key": self.main_key
            }
            self.finish_capture()

    def finish_capture(self):
        self.capturing = False
        self.label.config(text=config.hotkey_to_string(self.hotkey))
        self.button.config(text="Set Hotkey", state=tk.NORMAL)
        self.frame.winfo_toplevel().unbind("<KeyPress>")
        self.frame.winfo_toplevel().unbind("<KeyRelease>")

    def get_hotkey(self):
        return self.hotkey


class SettingsWindow:
    """Settings dialog window."""

    def __init__(self, current_config, on_save_callback=None):
        self.config = current_config.copy()
        self.on_save_callback = on_save_callback
        self.window = None

    def show(self):
        """Show the settings window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Tk()
        self.window.title("Voice Typer Settings")
        self.window.geometry("400x300")
        self.window.resizable(False, False)

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 400) // 2
        y = (self.window.winfo_screenheight() - 300) // 2
        self.window.geometry(f"+{x}+{y}")

        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Model size
        row = 0
        ttk.Label(main_frame, text="Model Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=self.config["model_size"])
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var,
                                   values=config.MODEL_OPTIONS, state="readonly", width=15)
        model_combo.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Model size hint
        row += 1
        hint = ttk.Label(main_frame, text="(tiny=fast, medium=accurate)",
                        font=("", 8), foreground="gray")
        hint.grid(row=row, column=1, sticky=tk.W)

        # Language
        row += 1
        ttk.Label(main_frame, text="Language:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.lang_var = tk.StringVar(value=self.config["language"])
        lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var,
                                  values=config.LANGUAGE_OPTIONS, state="readonly", width=15)
        lang_combo.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Sample rate
        row += 1
        ttk.Label(main_frame, text="Sample Rate:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.rate_var = tk.StringVar(value=str(self.config["sample_rate"]))
        rate_entry = ttk.Entry(main_frame, textvariable=self.rate_var, width=17)
        rate_entry.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Hotkey
        row += 1
        ttk.Label(main_frame, text="Hotkey:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.hotkey_capture = HotkeyCapture(main_frame, self.config["hotkey"])
        self.hotkey_capture.frame.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Buttons frame
        row += 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.close).pack(side=tk.LEFT, padx=5)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.window.mainloop()

    def save(self):
        """Save settings and close."""
        try:
            sample_rate = int(self.rate_var.get())
        except ValueError:
            sample_rate = 16000

        new_config = {
            "model_size": self.model_var.get(),
            "language": self.lang_var.get(),
            "sample_rate": sample_rate,
            "hotkey": self.hotkey_capture.get_hotkey()
        }

        config.save_config(new_config)

        if self.on_save_callback:
            self.on_save_callback(new_config)

        self.close()

    def close(self):
        """Close the window."""
        if self.window:
            self.window.destroy()
            self.window = None


def open_settings(current_config, on_save_callback=None):
    """Open settings window. Call from main app."""
    settings = SettingsWindow(current_config, on_save_callback)
    settings.show()


if __name__ == "__main__":
    # Test the settings GUI
    test_config = config.load_config()
    open_settings(test_config, lambda c: print("Saved:", c))
