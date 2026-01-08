"""
Settings GUI for MurmurTone using tkinter.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sounddevice as sd
import config


class Tooltip:
    """Hover tooltip for widgets."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        frame = tk.Frame(self.tooltip, bg="#333333", bd=1, relief=tk.SOLID)
        frame.pack()
        label = tk.Label(frame, text=self.text, bg="#333333", fg="#ffffff",
                        font=("", 9), justify=tk.LEFT, padx=8, pady=6)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


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

    def set_hotkey(self, hotkey):
        """Set hotkey from dict."""
        self.hotkey = hotkey.copy()
        self.label.config(text=config.hotkey_to_string(self.hotkey))


class SettingsWindow:
    """Settings dialog window."""

    def __init__(self, current_config, on_save_callback=None):
        self.config = current_config.copy()
        self.on_save_callback = on_save_callback
        self.window = None
        # Device test state
        self.test_stream = None
        self.test_running = False
        self.devices_list = []  # List of (display_name, device_info) tuples

    def show(self):
        """Show the settings window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Tk()
        self.window.title(f"{config.APP_NAME} Settings v{config.VERSION}")
        self.window.geometry("500x750")
        self.window.resizable(False, False)

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 500) // 2
        y = (self.window.winfo_screenheight() - 750) // 2
        self.window.geometry(f"+{x}+{y}")

        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Model size
        row = 0
        ttk.Label(main_frame, text="Model Size:").grid(row=row, column=0, sticky=tk.W, pady=5)
        model_frame = ttk.Frame(main_frame)
        model_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value=self.config["model_size"])
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var,
                                   values=config.MODEL_OPTIONS, state="readonly", width=15)
        model_combo.pack(side=tk.LEFT)
        model_help = ttk.Label(model_frame, text="?", font=("", 9, "bold"),
                               foreground="#888888", cursor="question_arrow")
        model_help.pack(side=tk.LEFT, padx=5)
        Tooltip(model_help, "tiny.en    - Fastest, basic accuracy\n"
                           "base.en   - Fast, good accuracy\n"
                           "small.en  - Balanced speed/accuracy\n"
                           "medium.en - Slowest, best accuracy")

        # Language
        row += 1
        ttk.Label(main_frame, text="Language:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.lang_var = tk.StringVar(value=self.config["language"])
        lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var,
                                  values=config.LANGUAGE_OPTIONS, state="readonly", width=15)
        lang_combo.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Input Device
        row += 1
        ttk.Label(main_frame, text="Input Device:").grid(row=row, column=0, sticky=tk.W, pady=5)
        device_frame = ttk.Frame(main_frame)
        device_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var,
                                         state="readonly", width=40)
        self.device_combo.pack(side=tk.LEFT)
        ttk.Button(device_frame, text="↻", width=2, command=self.refresh_devices).pack(side=tk.LEFT, padx=2)

        # Populate devices and select current
        self.refresh_devices()

        # Device hint
        row += 1
        device_hint = ttk.Label(main_frame, text="(showing enabled devices - restart app to detect new defaults)",
                                font=("", 8), foreground="gray")
        device_hint.grid(row=row, column=1, sticky=tk.W)

        # Test button and level meter
        row += 1
        test_frame = ttk.Frame(main_frame)
        test_frame.grid(row=row, column=1, sticky=tk.W, pady=2)
        self.test_btn = ttk.Button(test_frame, text="Test", width=6, command=self.toggle_test)
        self.test_btn.pack(side=tk.LEFT)
        self.level_canvas = tk.Canvas(test_frame, width=180, height=16, bg="#333333",
                                      highlightthickness=1, highlightbackground="#666666")
        self.level_canvas.pack(side=tk.LEFT, padx=5)
        # Draw empty level bar
        self.level_bar = self.level_canvas.create_rectangle(0, 0, 0, 16, fill="#00aa00", width=0)

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
        hotkey_help = ttk.Label(hotkey_frame, text="?", font=("", 9, "bold"),
                                foreground="#888888", cursor="question_arrow")
        hotkey_help.pack(side=tk.LEFT, padx=5)
        Tooltip(hotkey_help, "Recommended Hotkeys:\n\n"
                            "SINGLE KEYS (easiest):\n"
                            "• Scroll Lock - never conflicts\n"
                            "• Pause/Break - never used\n"
                            "• Insert - rarely used\n\n"
                            "NUMPAD (if available):\n"
                            "• Numpad + or Numpad 0\n\n"
                            "TWO-KEY COMBOS:\n"
                            "• Ctrl+\\ or Ctrl+;")

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

        # Auto-paste checkbox
        row += 1
        autopaste_frame = ttk.Frame(main_frame)
        autopaste_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.autopaste_var = tk.BooleanVar(value=self.config.get("auto_paste", True))
        autopaste_check = ttk.Checkbutton(autopaste_frame, text="Auto-paste after transcription",
                                          variable=self.autopaste_var)
        autopaste_check.pack(side=tk.LEFT)
        autopaste_help = ttk.Label(autopaste_frame, text="?", font=("", 9, "bold"),
                                   foreground="#888888", cursor="question_arrow")
        autopaste_help.pack(side=tk.LEFT, padx=5)
        Tooltip(autopaste_help, "When enabled, text is automatically typed (Ctrl+V)\n"
                               "into whichever text field has focus after\n"
                               "transcription.\n\n"
                               "When disabled, text is only copied to clipboard -\n"
                               "you must manually paste.")

        # Start with Windows checkbox
        row += 1
        self.startup_var = tk.BooleanVar(value=config.get_startup_enabled())
        startup_check = ttk.Checkbutton(main_frame, text="Start with Windows",
                                        variable=self.startup_var)
        startup_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Text Processing Section
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

        row += 1
        processing_label = ttk.Label(main_frame, text="Text Processing", font=("", 10, "bold"))
        processing_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Voice commands checkbox
        row += 1
        self.voice_commands_var = tk.BooleanVar(value=self.config.get("voice_commands_enabled", True))
        voice_cmd_frame = ttk.Frame(main_frame)
        voice_cmd_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        voice_cmd_check = ttk.Checkbutton(voice_cmd_frame, text="Voice commands (period, new line, etc.)",
                                          variable=self.voice_commands_var)
        voice_cmd_check.pack(side=tk.LEFT)
        voice_cmd_help = ttk.Label(voice_cmd_frame, text="?", font=("", 9, "bold"),
                                   foreground="#888888", cursor="question_arrow")
        voice_cmd_help.pack(side=tk.LEFT, padx=5)
        Tooltip(voice_cmd_help, "Converts spoken commands to punctuation:\n\n"
                               "\"period\" or \"full stop\" → .\n"
                               "\"comma\" → ,\n"
                               "\"question mark\" → ?\n"
                               "\"exclamation point\" → !\n"
                               "\"new line\" → line break\n"
                               "\"new paragraph\" → double line break")

        # Scratch that checkbox (indented under voice commands)
        row += 1
        self.scratch_that_var = tk.BooleanVar(value=self.config.get("scratch_that_enabled", True))
        scratch_frame = ttk.Frame(main_frame)
        scratch_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Label(scratch_frame, text="    ").pack(side=tk.LEFT)  # Indent
        scratch_check = ttk.Checkbutton(scratch_frame, text="\"Scratch that\" deletes last transcription",
                                        variable=self.scratch_that_var)
        scratch_check.pack(side=tk.LEFT)

        # Filler removal checkbox
        row += 1
        self.filler_var = tk.BooleanVar(value=self.config.get("filler_removal_enabled", True))
        filler_frame = ttk.Frame(main_frame)
        filler_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        filler_check = ttk.Checkbutton(filler_frame, text="Remove filler words (um, uh, etc.)",
                                       variable=self.filler_var)
        filler_check.pack(side=tk.LEFT)
        filler_help = ttk.Label(filler_frame, text="?", font=("", 9, "bold"),
                                foreground="#888888", cursor="question_arrow")
        filler_help.pack(side=tk.LEFT, padx=5)
        Tooltip(filler_help, "Removes common filler words:\num, uh, er, ah, hmm\nyou know, I mean, sort of, kind of")

        # Aggressive filler removal (indented)
        row += 1
        self.filler_aggressive_var = tk.BooleanVar(value=self.config.get("filler_removal_aggressive", False))
        aggressive_frame = ttk.Frame(main_frame)
        aggressive_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Label(aggressive_frame, text="    ").pack(side=tk.LEFT)  # Indent
        aggressive_check = ttk.Checkbutton(aggressive_frame, text="Aggressive mode (also removes \"like\" as filler)",
                                           variable=self.filler_aggressive_var)
        aggressive_check.pack(side=tk.LEFT)

        # Custom dictionary section
        row += 1
        dict_label_frame = ttk.Frame(main_frame)
        dict_label_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
        ttk.Label(dict_label_frame, text="Custom Dictionary:").pack(side=tk.LEFT)
        dict_help = ttk.Label(dict_label_frame, text="?", font=("", 9, "bold"),
                              foreground="#888888", cursor="question_arrow")
        dict_help.pack(side=tk.LEFT, padx=5)
        Tooltip(dict_help, "Replace misheard words/phrases:\n\n"
                          "\"murmur tone\" → \"MurmurTone\"\n"
                          "\"pie torch\" → \"PyTorch\"\n"
                          "\"J R R\" → \"J.R.R.\"")

        # Dictionary list
        row += 1
        dict_frame = ttk.Frame(main_frame)
        dict_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.dict_listbox = tk.Listbox(dict_frame, width=50, height=3, selectmode=tk.SINGLE)
        self.dict_listbox.pack(side=tk.LEFT)
        self.custom_dictionary = self.config.get("custom_dictionary", []).copy()
        self._refresh_dict_listbox()

        dict_btn_frame = ttk.Frame(dict_frame)
        dict_btn_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(dict_btn_frame, text="Add", width=6, command=self.add_dict_entry).pack(pady=1)
        ttk.Button(dict_btn_frame, text="Remove", width=6, command=self.remove_dict_entry).pack(pady=1)

        # Buttons frame
        row += 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.close).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to Defaults", command=self.reset_defaults).pack(side=tk.LEFT, padx=5)

        # Separator
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

        # About section
        row += 1
        about_frame = ttk.Frame(main_frame)
        about_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W)

        version_label = ttk.Label(about_frame, text=f"{config.APP_NAME} v{config.VERSION}",
                                  font=("", 9), foreground="gray")
        version_label.pack(side=tk.LEFT)

        help_link = ttk.Label(about_frame, text="Help", font=("", 9, "underline"),
                              foreground="#4a9eff", cursor="hand2")
        help_link.pack(side=tk.LEFT, padx=(15, 0))
        help_link.bind("<Button-1>", lambda e: self.open_url(config.HELP_URL))

        update_link = ttk.Label(about_frame, text="Check for Updates", font=("", 9, "underline"),
                                foreground="#4a9eff", cursor="hand2")
        update_link.pack(side=tk.LEFT, padx=(15, 0))
        update_link.bind("<Button-1>", lambda e: self.open_url(config.GITHUB_REPO + "/releases"))

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.window.mainloop()

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

    def refresh_devices(self):
        """Refresh the list of available input devices."""
        self.devices_list = config.get_input_devices()
        display_names = [name for name, _ in self.devices_list]

        # Check if current saved device is available
        saved_device = self.config.get("input_device")
        # First item is always System Default (with device name)
        current_selection = display_names[0] if display_names else "System Default"

        if saved_device is not None:
            saved_name = saved_device.get("name") if isinstance(saved_device, dict) else saved_device
            # Find matching device in list
            device_available = False
            for display_name, device_info in self.devices_list:
                if device_info and device_info.get("name") == saved_name:
                    current_selection = display_name
                    device_available = True
                    break
            # If not available, show it as unavailable
            if not device_available and saved_name:
                unavailable_name = f"{saved_name} (unavailable)"
                display_names.append(unavailable_name)
                current_selection = unavailable_name

        self.device_combo["values"] = display_names
        self.device_var.set(current_selection)

    def get_selected_device_info(self):
        """Get the device_info dict for the currently selected device."""
        selected = self.device_var.get()
        if "(unavailable)" in selected:
            # Return the original saved device
            return self.config.get("input_device")
        for display_name, device_info in self.devices_list:
            if display_name == selected:
                return device_info
        return None  # System Default

    def toggle_test(self):
        """Start or stop the microphone test."""
        if self.test_running:
            self.stop_test()
        else:
            self.start_test()

    def start_test(self):
        """Start testing the selected microphone with level meter."""
        device_info = self.get_selected_device_info()

        # Get device index
        device_index = None
        if device_info:
            device_index = device_info.get("index")

        try:
            sample_rate = int(self.rate_var.get())
        except ValueError:
            sample_rate = 16000

        try:
            self.test_stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
                device=device_index,
                callback=self.test_audio_callback
            )
            self.test_stream.start()
            self.test_running = True
            self.test_btn.config(text="Stop")
            # Schedule auto-stop after 5 seconds
            self.window.after(5000, self.auto_stop_test)
        except Exception as e:
            messagebox.showerror("Test Failed", f"Could not open device:\n{e}")

    def test_audio_callback(self, indata, frames, time_info, status):
        """Callback for test audio stream - updates level meter."""
        if not self.test_running:
            return
        # Calculate RMS level
        rms = np.sqrt(np.mean(indata**2))
        # Convert to dB (with floor at -60dB)
        db = 20 * np.log10(max(rms, 1e-6))
        # Normalize to 0-1 range (-60dB to 0dB)
        level = max(0, min(1, (db + 60) / 60))
        # Schedule UI update on main thread
        try:
            self.window.after_idle(lambda: self.update_level_meter(level))
        except Exception:
            pass  # Window may be closing

    def update_level_meter(self, level):
        """Update the level meter display."""
        if not self.test_running or not self.level_canvas:
            return
        width = int(level * 180)
        # Color gradient: green -> yellow -> red
        if level < 0.5:
            color = "#00aa00"  # Green
        elif level < 0.75:
            color = "#aaaa00"  # Yellow
        else:
            color = "#aa0000"  # Red
        self.level_canvas.coords(self.level_bar, 0, 0, width, 16)
        self.level_canvas.itemconfig(self.level_bar, fill=color)

    def auto_stop_test(self):
        """Auto-stop test after timeout."""
        if self.test_running:
            self.stop_test()

    def stop_test(self):
        """Stop the microphone test."""
        self.test_running = False
        if self.test_stream:
            try:
                self.test_stream.stop()
                self.test_stream.close()
            except Exception:
                pass
            self.test_stream = None
        self.test_btn.config(text="Test")
        # Reset level meter
        if self.level_canvas:
            self.level_canvas.coords(self.level_bar, 0, 0, 0, 16)

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

        # Get selected device info (None for System Default)
        device_info = self.get_selected_device_info()

        new_config = {
            "model_size": self.model_var.get(),
            "language": self.lang_var.get(),
            "sample_rate": sample_rate,
            "hotkey": self.hotkey_capture.get_hotkey(),
            "recording_mode": self.mode_var.get(),
            "silence_duration_sec": silence_duration,
            "audio_feedback": self.feedback_var.get(),
            "input_device": device_info,
            "auto_paste": self.autopaste_var.get(),
            "start_with_windows": self.startup_var.get(),
            # Text processing settings
            "voice_commands_enabled": self.voice_commands_var.get(),
            "scratch_that_enabled": self.scratch_that_var.get(),
            "filler_removal_enabled": self.filler_var.get(),
            "filler_removal_aggressive": self.filler_aggressive_var.get(),
            "custom_fillers": self.config.get("custom_fillers", []),  # Preserve existing
            "custom_dictionary": self.custom_dictionary
        }

        config.save_config(new_config)

        # Handle Windows startup setting
        config.set_startup_enabled(self.startup_var.get())

        if self.on_save_callback:
            self.on_save_callback(new_config)

        self.close()

    def reset_defaults(self):
        """Reset all settings to defaults."""
        if not messagebox.askyesno("Reset to Defaults",
                                   "Reset all settings to defaults?\nThis will not affect Windows startup setting."):
            return

        defaults = config.DEFAULTS
        self.model_var.set(defaults["model_size"])
        self.lang_var.set(defaults["language"])
        self.rate_var.set(str(defaults["sample_rate"]))
        self.hotkey_capture.set_hotkey(defaults["hotkey"])
        self.mode_var.set(defaults["recording_mode"])
        self.silence_var.set(str(defaults["silence_duration_sec"]))
        self.feedback_var.set(defaults["audio_feedback"])
        self.autopaste_var.set(defaults["auto_paste"])
        # Reset text processing settings
        self.voice_commands_var.set(defaults["voice_commands_enabled"])
        self.scratch_that_var.set(defaults["scratch_that_enabled"])
        self.filler_var.set(defaults["filler_removal_enabled"])
        self.filler_aggressive_var.set(defaults["filler_removal_aggressive"])
        self.custom_dictionary = []
        self._refresh_dict_listbox()
        # Reset device to System Default
        self.refresh_devices()
        # Update UI
        self.update_silence_visibility()
        self.on_mode_change()

    def open_url(self, url):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)

    def _refresh_dict_listbox(self):
        """Refresh the dictionary listbox display."""
        self.dict_listbox.delete(0, tk.END)
        for entry in self.custom_dictionary:
            from_text = entry.get("from", "")
            to_text = entry.get("to", "")
            self.dict_listbox.insert(tk.END, f'"{from_text}" → "{to_text}"')

    def add_dict_entry(self):
        """Show dialog to add a dictionary entry."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Dictionary Entry")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 350) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="From (what Whisper hears):").grid(row=0, column=0, sticky=tk.W, pady=5)
        from_var = tk.StringVar()
        from_entry = ttk.Entry(frame, textvariable=from_var, width=35)
        from_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="To (what you want):").grid(row=1, column=0, sticky=tk.W, pady=5)
        to_var = tk.StringVar()
        to_entry = ttk.Entry(frame, textvariable=to_var, width=35)
        to_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        def do_add():
            from_text = from_var.get().strip()
            to_text = to_var.get().strip()
            if from_text and to_text:
                self.custom_dictionary.append({
                    "from": from_text,
                    "to": to_text,
                    "case_sensitive": False
                })
                self._refresh_dict_listbox()
                dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Add", command=do_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        from_entry.focus_set()

    def remove_dict_entry(self):
        """Remove selected dictionary entry."""
        selection = self.dict_listbox.curselection()
        if selection:
            idx = selection[0]
            self.custom_dictionary.pop(idx)
            self._refresh_dict_listbox()

    def close(self):
        """Close the window."""
        # Stop any running test
        self.stop_test()
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
