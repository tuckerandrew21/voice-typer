"""
Settings GUI for Voice Typer using tkinter.
"""
import tkinter as tk
from tkinter import ttk, messagebox
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
        self.window.geometry("400x420")
        self.window.resizable(False, False)

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 400) // 2
        y = (self.window.winfo_screenheight() - 420) // 2
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
        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.hotkey_capture = HotkeyCapture(hotkey_frame, self.config["hotkey"])
        self.hotkey_capture.frame.pack(side=tk.LEFT)
        ttk.Button(hotkey_frame, text="?", width=2, command=self.show_hotkey_help).pack(side=tk.LEFT, padx=5)

        # Recording Mode
        row += 1
        ttk.Label(main_frame, text="Recording Mode:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.mode_var = tk.StringVar(value=self.config.get("recording_mode", "push_to_talk"))
        mode_combo = ttk.Combobox(main_frame, textvariable=self.mode_var,
                                  values=config.RECORDING_MODE_OPTIONS, state="readonly", width=15)
        mode_combo.grid(row=row, column=1, sticky=tk.W, pady=5)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        # Mode hint
        row += 1
        self.mode_hint = ttk.Label(main_frame, text=self.get_mode_hint(),
                                   font=("", 8), foreground="gray", wraplength=250)
        self.mode_hint.grid(row=row, column=0, columnspan=2, sticky=tk.W)

        # Silence timeout (only visible in auto_stop mode)
        row += 1
        self.silence_frame = ttk.Frame(main_frame)
        self.silence_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(self.silence_frame, text="Silence Timeout:").pack(side=tk.LEFT)
        self.silence_var = tk.StringVar(value=str(self.config.get("silence_duration_sec", 2.0)))
        silence_entry = ttk.Entry(self.silence_frame, textvariable=self.silence_var, width=5)
        silence_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.silence_frame, text="seconds").pack(side=tk.LEFT)
        self.update_silence_visibility()

        # Audio feedback checkbox
        row += 1
        self.feedback_var = tk.BooleanVar(value=self.config.get("audio_feedback", True))
        feedback_check = ttk.Checkbutton(main_frame, text="Audio feedback (click sounds)",
                                         variable=self.feedback_var)
        feedback_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Buttons frame
        row += 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.close).pack(side=tk.LEFT, padx=5)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.window.mainloop()

    def show_hotkey_help(self):
        """Show hotkey suggestions dialog."""
        help_text = """Recommended Hotkeys:

SINGLE KEYS (easiest):
• Scroll Lock - never used by anything
• Pause/Break - never used
• Insert - rarely used

NUMPAD (if you have one):
• Numpad + - easy to reach
• Numpad 0 - large key

TWO-KEY COMBOS (if needed):
• Ctrl+\\ - rarely conflicts
• Ctrl+; - rarely conflicts

Tip: Scroll Lock is the cleanest option
if your keyboard has it."""
        messagebox.showinfo("Hotkey Suggestions", help_text)

    def get_mode_hint(self):
        """Return description text for current recording mode."""
        mode = self.mode_var.get()
        if mode == "push_to_talk":
            return "Hold hotkey to record, release to transcribe"
        else:
            return "Press hotkey to start, auto-stops after silence"

    def on_mode_change(self, event=None):
        """Update UI when recording mode changes."""
        self.mode_hint.config(text=self.get_mode_hint())
        self.update_silence_visibility()

    def update_silence_visibility(self):
        """Show/hide silence settings based on mode."""
        if self.mode_var.get() == "auto_stop":
            self.silence_frame.grid()
        else:
            self.silence_frame.grid_remove()

    def save(self):
        """Save settings and close."""
        try:
            sample_rate = int(self.rate_var.get())
        except ValueError:
            sample_rate = 16000

        try:
            silence_duration = float(self.silence_var.get())
            silence_duration = max(0.5, min(10.0, silence_duration))  # Clamp to reasonable range
        except ValueError:
            silence_duration = 2.0

        new_config = {
            "model_size": self.model_var.get(),
            "language": self.lang_var.get(),
            "sample_rate": sample_rate,
            "hotkey": self.hotkey_capture.get_hotkey(),
            "recording_mode": self.mode_var.get(),
            "silence_duration_sec": silence_duration,
            "audio_feedback": self.feedback_var.get()
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
