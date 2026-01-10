"""
Settings GUI for MurmurTone using tkinter.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sounddevice as sd
import subprocess
import sys
import threading
import os
import config
import text_processor


def check_cuda_available():
    """Check if CUDA is available for GPU acceleration."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        # torch not installed, try ctranslate2 directly
        try:
            import ctranslate2
            # ctranslate2 API requires device argument
            cuda_types = ctranslate2.get_supported_compute_types("cuda")
            return len(cuda_types) > 0
        except (ImportError, Exception):
            return False


# Set to True to test the "GPU not available" UI state
_TEST_GPU_UNAVAILABLE = False


def get_cuda_status():
    """
    Get detailed CUDA status info.
    Returns tuple: (is_available, status_message, gpu_name_or_reason)
    """
    # Test mode: simulate GPU unavailable
    if _TEST_GPU_UNAVAILABLE:
        return (False, "GPU libraries not installed", None)

    # Check if ctranslate2 supports CUDA compute types
    cuda_supported = False
    try:
        import ctranslate2
        # ctranslate2 API requires device argument
        cuda_types = ctranslate2.get_supported_compute_types("cuda")
        cuda_supported = len(cuda_types) > 0
    except (ImportError, Exception):
        pass

    if not cuda_supported:
        # Check if torch can detect CUDA
        try:
            import torch
            if torch.cuda.is_available():
                cuda_supported = True
        except ImportError:
            pass

    if not cuda_supported:
        return (False, "GPU libraries not installed", None)

    # CUDA is supported, try to get GPU name via torch
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return (True, "CUDA Available", gpu_name)
        else:
            # ctranslate2 supports CUDA but torch doesn't see a GPU
            # This means libraries are installed but no GPU hardware
            return (True, "CUDA Available", "via ctranslate2")
    except ImportError:
        # No torch, but ctranslate2 says CUDA works
        return (True, "CUDA Available", "via ctranslate2")


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
        self.devices_list = []  # List of (display_name, device_info) tuples
        # Audio test state (for noise gate level meter)
        self.noise_test_stream = None
        self.noise_test_running = False

    def show(self):
        """Show the settings window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Tk()
        self.window.title(f"{config.APP_NAME} Settings v{config.VERSION}")
        self.window.geometry("500x1250")
        self.window.resizable(False, False)

        # Center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 500) // 2
        y = (self.window.winfo_screenheight() - 1250) // 2
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

        # Processing Mode (combined device + compute type)
        row += 1
        ttk.Label(main_frame, text="Processing:").grid(row=row, column=0, sticky=tk.W, pady=5)
        processing_frame = ttk.Frame(main_frame)
        processing_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        self.processing_mode_var = tk.StringVar(value=self.config.get("processing_mode", "auto"))
        # Create display values for the combobox
        display_values = [config.PROCESSING_MODE_LABELS[m] for m in config.PROCESSING_MODE_OPTIONS]
        processing_combo = ttk.Combobox(processing_frame, textvariable=self.processing_mode_var,
                                        values=display_values, state="readonly", width=14)
        # Set display value based on stored mode
        current_mode = self.config.get("processing_mode", "auto")
        processing_combo.set(config.PROCESSING_MODE_LABELS.get(current_mode, "Auto"))
        processing_combo.pack(side=tk.LEFT)
        processing_help = ttk.Label(processing_frame, text="?", font=("", 9, "bold"),
                                    foreground="#888888", cursor="question_arrow")
        processing_help.pack(side=tk.LEFT, padx=5)
        Tooltip(processing_help, "Auto          - GPU if available, else CPU (recommended)\n"
                                "CPU           - Always use CPU (slower, reliable)\n"
                                "GPU - Balanced - Fast + accurate (float16)\n"
                                "GPU - Quality  - Highest quality (float32, slower)")
        self.processing_combo = processing_combo

        # Bind change event for warning updates
        processing_combo.bind("<<ComboboxSelected>>", self.on_gpu_setting_change)

        # GPU Status Section
        row += 1
        gpu_status_frame = ttk.Frame(main_frame)
        gpu_status_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        ttk.Label(gpu_status_frame, text="GPU Status:").pack(side=tk.LEFT)

        # Status indicator dot (using Unicode circle)
        self.gpu_status_dot = ttk.Label(gpu_status_frame, text="\u25cf", font=("", 12))
        self.gpu_status_dot.pack(side=tk.LEFT, padx=(5, 2))

        # Status text
        self.gpu_status_label = ttk.Label(gpu_status_frame, text="Checking...")
        self.gpu_status_label.pack(side=tk.LEFT)

        # Refresh button
        refresh_btn = ttk.Button(gpu_status_frame, text="\u21bb", width=3, command=self.refresh_gpu_status)
        refresh_btn.pack(side=tk.LEFT, padx=(10, 0))
        Tooltip(refresh_btn, "Refresh GPU status")

        # GPU details row (GPU name or reason for unavailability)
        row += 1
        self.gpu_details_frame = ttk.Frame(main_frame)
        self.gpu_details_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=(85, 0))
        self.gpu_details_label = ttk.Label(self.gpu_details_frame, text="", font=("", 8), foreground="gray")
        self.gpu_details_label.pack(side=tk.LEFT)

        # Install GPU Support button row (only visible when needed)
        row += 1
        self.install_gpu_frame = ttk.Frame(main_frame)
        self.install_gpu_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.install_gpu_btn = ttk.Button(self.install_gpu_frame, text="Install GPU Support",
                                          command=self.install_gpu_support)
        self.install_gpu_btn.pack(side=tk.LEFT)
        install_help = ttk.Label(self.install_gpu_frame, text="?", font=("", 9, "bold"),
                                 foreground="#888888", cursor="question_arrow")
        install_help.pack(side=tk.LEFT, padx=5)
        Tooltip(install_help, "Downloads and installs NVIDIA CUDA libraries\n"
                             "for GPU acceleration (~2-3 GB download).\n\n"
                             "Requires: NVIDIA GPU with CUDA support")

        # GPU warning label (for incompatible settings)
        row += 1
        self.gpu_warning_frame = ttk.Frame(main_frame)
        self.gpu_warning_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W)
        self.gpu_warning_label = ttk.Label(self.gpu_warning_frame, text="", foreground="#cc6600", font=("", 8))
        self.gpu_warning_label.pack(side=tk.LEFT)

        # Initialize GPU status display
        self.cuda_available = False
        self.cuda_libs_installed = True  # Assume installed until we check
        self.refresh_gpu_status()

        # Language
        row += 1
        ttk.Label(main_frame, text="Language:").grid(row=row, column=0, sticky=tk.W, pady=5)
        # Use friendly labels in dropdown
        lang_labels = [config.LANGUAGE_LABELS.get(code, code) for code in config.LANGUAGE_OPTIONS]
        current_lang = self.config["language"]
        current_label = config.LANGUAGE_LABELS.get(current_lang, current_lang)
        self.lang_var = tk.StringVar(value=current_label)
        self.lang_combo = ttk.Combobox(main_frame, textvariable=self.lang_var,
                                       values=lang_labels, state="readonly", width=15)
        self.lang_combo.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Translation Mode
        row += 1
        self.translation_enabled_var = tk.BooleanVar(value=self.config.get("translation_enabled", False))
        trans_check = ttk.Checkbutton(main_frame, text="Translation Mode (speak one language, output English)",
                                      variable=self.translation_enabled_var,
                                      command=self.on_translation_toggle)
        trans_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Translation Source Language
        row += 1
        ttk.Label(main_frame, text="Source Language:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(20, 0))
        current_trans_lang = self.config.get("translation_source_language", "auto")
        current_trans_label = config.LANGUAGE_LABELS.get(current_trans_lang, current_trans_lang)
        self.trans_lang_var = tk.StringVar(value=current_trans_label)
        self.trans_lang_combo = ttk.Combobox(main_frame, textvariable=self.trans_lang_var,
                                             values=lang_labels, state="readonly", width=15)
        self.trans_lang_combo.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Update initial state
        self.on_translation_toggle()

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

        # Noise gate section
        row += 1
        noise_gate_frame = ttk.Frame(main_frame)
        noise_gate_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.noise_gate_var = tk.BooleanVar(value=self.config.get("noise_gate_enabled", True))
        noise_gate_check = ttk.Checkbutton(noise_gate_frame, text="Noise gate",
                                           variable=self.noise_gate_var)
        noise_gate_check.pack(side=tk.LEFT)
        noise_gate_help = ttk.Label(noise_gate_frame, text="?", font=("", 9, "bold"),
                                    foreground="#888888", cursor="question_arrow")
        noise_gate_help.pack(side=tk.LEFT, padx=5)
        Tooltip(noise_gate_help, "Filters out audio below a threshold.\n"
                                "Helps ignore background noise and reduce\n"
                                "garbage transcriptions.\n\n"
                                "Lower values = more sensitive (picks up quiet sounds)\n"
                                "Higher values = less sensitive (only loud sounds)")

        # Combined noise gate level meter with draggable threshold marker (Discord-style)
        row += 1
        noise_level_frame = ttk.Frame(main_frame)
        noise_level_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))

        self.noise_test_btn = ttk.Button(noise_level_frame, text="Test", width=6,
                                          command=self.toggle_noise_test)
        self.noise_test_btn.pack(side=tk.LEFT)

        # Canvas dimensions
        self.meter_width = 200
        self.meter_height = 20

        self.noise_level_canvas = tk.Canvas(noise_level_frame, width=self.meter_width, height=self.meter_height,
                                             bg="#333333", highlightthickness=1,
                                             highlightbackground="#666666", cursor="hand2")
        self.noise_level_canvas.pack(side=tk.LEFT, padx=5)

        # Level bar (shows current audio level) - behind threshold marker
        self.noise_level_bar = self.noise_level_canvas.create_rectangle(
            0, 0, 0, self.meter_height, fill="#00aa00", width=0)

        # Threshold marker (vertical orange line) - draggable
        self.noise_threshold_var = tk.IntVar(value=self.config.get("noise_gate_threshold_db", -40))
        initial_x = self._db_to_x(self.noise_threshold_var.get())
        self.threshold_marker = self.noise_level_canvas.create_line(
            initial_x, 0, initial_x, self.meter_height, fill="#ff6600", width=3)

        # dB label
        self.threshold_label = ttk.Label(noise_level_frame, text=f"{self.noise_threshold_var.get()} dB", width=7)
        self.threshold_label.pack(side=tk.LEFT)

        # Make threshold marker draggable
        self.noise_level_canvas.bind("<Button-1>", self._on_threshold_click)
        self.noise_level_canvas.bind("<B1-Motion>", self._on_threshold_drag)

        # Update label when threshold changes
        def update_threshold_label(*args):
            self.threshold_label.config(text=f"{self.noise_threshold_var.get()} dB")
        self.noise_threshold_var.trace_add("write", update_threshold_label)

        # Audio feedback checkbox
        row += 1
        feedback_frame = ttk.Frame(main_frame)
        feedback_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.feedback_var = tk.BooleanVar(value=self.config.get("audio_feedback", True))
        feedback_check = ttk.Checkbutton(feedback_frame, text="Audio feedback",
                                         variable=self.feedback_var)
        feedback_check.pack(side=tk.LEFT)
        feedback_help = ttk.Label(feedback_frame, text="?", font=("", 9, "bold"),
                                  foreground="#888888", cursor="question_arrow")
        feedback_help.pack(side=tk.LEFT, padx=5)
        Tooltip(feedback_help, "Play sounds for different states:\n"
                              "• Start/stop recording clicks\n"
                              "• Processing sound while transcribing\n"
                              "• Success chime when text is typed\n"
                              "• Error buzz when no speech detected")

        # Sound type checkboxes (indented)
        row += 1
        sound_options_frame = ttk.Frame(main_frame)
        sound_options_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.sound_processing_var = tk.BooleanVar(value=self.config.get("sound_processing", True))
        ttk.Checkbutton(sound_options_frame, text="Processing",
                        variable=self.sound_processing_var).pack(side=tk.LEFT, padx=(0, 10))
        self.sound_success_var = tk.BooleanVar(value=self.config.get("sound_success", True))
        ttk.Checkbutton(sound_options_frame, text="Success",
                        variable=self.sound_success_var).pack(side=tk.LEFT, padx=(0, 10))
        self.sound_error_var = tk.BooleanVar(value=self.config.get("sound_error", True))
        ttk.Checkbutton(sound_options_frame, text="Error",
                        variable=self.sound_error_var).pack(side=tk.LEFT)

        # Volume slider
        row += 1
        volume_frame = ttk.Frame(main_frame)
        volume_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))
        ttk.Label(volume_frame, text="Volume:").pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=self.config.get("audio_feedback_volume", 0.3))
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
                                 variable=self.volume_var, length=120)
        volume_scale.pack(side=tk.LEFT, padx=5)
        self.volume_label = ttk.Label(volume_frame, text=f"{int(self.volume_var.get() * 100)}%", width=5)
        self.volume_label.pack(side=tk.LEFT)
        # Update label when slider moves
        def update_volume_label(*args):
            self.volume_label.config(text=f"{int(self.volume_var.get() * 100)}%")
        self.volume_var.trace_add("write", update_volume_label)

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

        # Paste mode selector
        row += 1
        paste_mode_frame = ttk.Frame(main_frame)
        paste_mode_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(paste_mode_frame, text="Paste mode:").pack(side=tk.LEFT)
        self.paste_mode_var = tk.StringVar(value=self.config.get("paste_mode", "clipboard"))
        paste_mode_combo = ttk.Combobox(paste_mode_frame, textvariable=self.paste_mode_var,
                                        values=["clipboard", "direct"], width=12, state="readonly")
        paste_mode_combo.pack(side=tk.LEFT, padx=(10, 5))
        paste_mode_help = ttk.Label(paste_mode_frame, text="?", font=("", 9, "bold"),
                                    foreground="#888888", cursor="question_arrow")
        paste_mode_help.pack(side=tk.LEFT, padx=5)
        Tooltip(paste_mode_help, "Clipboard: Uses Ctrl+V to paste. Faster for long text.\n"
                                 "Preserves your clipboard contents (e.g. screenshots).\n\n"
                                 "Direct: Types text character-by-character.\n"
                                 "Never touches clipboard. Slightly slower.")

        # Start with Windows checkbox
        row += 1
        self.startup_var = tk.BooleanVar(value=config.get_startup_enabled())
        startup_check = ttk.Checkbutton(main_frame, text="Start with Windows",
                                        variable=self.startup_var)
        startup_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Preview Window Section
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

        row += 1
        preview_label = ttk.Label(main_frame, text="Preview Window", font=("", 10, "bold"))
        preview_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Preview enabled checkbox
        row += 1
        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.preview_enabled_var = tk.BooleanVar(value=self.config.get("preview_enabled", True))
        preview_check = ttk.Checkbutton(preview_frame, text="Show preview overlay",
                                        variable=self.preview_enabled_var)
        preview_check.pack(side=tk.LEFT)
        preview_help = ttk.Label(preview_frame, text="?", font=("", 9, "bold"),
                                 foreground="#888888", cursor="question_arrow")
        preview_help.pack(side=tk.LEFT, padx=5)
        Tooltip(preview_help, "Shows a floating overlay with:\n"
                             "• \"Recording...\" while recording (red)\n"
                             "• \"Transcribing...\" while processing (yellow)\n"
                             "• Transcribed text briefly (white)")

        # Preview position dropdown
        row += 1
        position_frame = ttk.Frame(main_frame)
        position_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))
        ttk.Label(position_frame, text="Position:").pack(side=tk.LEFT)
        self.preview_position_var = tk.StringVar(value=self.config.get("preview_position", "bottom-right"))
        position_options = ["bottom-right", "bottom-left", "top-right", "top-left"]
        position_combo = ttk.Combobox(position_frame, textvariable=self.preview_position_var,
                                      values=position_options, state="readonly", width=12)
        position_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Preview auto-hide delay
        row += 1
        delay_frame = ttk.Frame(main_frame)
        delay_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))
        ttk.Label(delay_frame, text="Auto-hide delay:").pack(side=tk.LEFT)
        self.preview_delay_var = tk.StringVar(value=str(self.config.get("preview_auto_hide_delay", 2.0)))
        delay_entry = ttk.Entry(delay_frame, textvariable=self.preview_delay_var, width=5)
        delay_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(delay_frame, text="seconds").pack(side=tk.LEFT, padx=(5, 0))
        delay_help = ttk.Label(delay_frame, text="?", font=("", 9, "bold"),
                               foreground="#888888", cursor="question_arrow")
        delay_help.pack(side=tk.LEFT, padx=5)
        Tooltip(delay_help, "How long the transcribed text stays visible\n"
                           "before the preview window disappears.\n\n"
                           "Set to 0 to keep it visible until next recording.")

        # Preview theme dropdown
        row += 1
        theme_frame = ttk.Frame(main_frame)
        theme_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=(20, 0))
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        self.preview_theme_var = tk.StringVar(value=self.config.get("preview_theme", "dark"))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.preview_theme_var,
                                   values=config.PREVIEW_THEME_OPTIONS, state="readonly", width=8)
        theme_combo.pack(side=tk.LEFT, padx=(5, 0))

        # Preview font size
        ttk.Label(theme_frame, text="Font size:").pack(side=tk.LEFT, padx=(15, 0))
        self.preview_font_size_var = tk.IntVar(value=self.config.get("preview_font_size", 11))
        font_spin = ttk.Spinbox(theme_frame, from_=config.PREVIEW_FONT_SIZE_MIN,
                                to=config.PREVIEW_FONT_SIZE_MAX,
                                textvariable=self.preview_font_size_var, width=4)
        font_spin.pack(side=tk.LEFT, padx=(5, 0))

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

        # Custom Commands section
        row += 1
        cmd_label_frame = ttk.Frame(main_frame)
        cmd_label_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))
        ttk.Label(cmd_label_frame, text="Custom Commands:").pack(side=tk.LEFT)
        cmd_help = ttk.Label(cmd_label_frame, text="?", font=("", 9, "bold"),
                             foreground="#888888", cursor="question_arrow")
        cmd_help.pack(side=tk.LEFT, padx=5)
        Tooltip(cmd_help, "Trigger phrases that expand to text blocks:\n\n"
                         "\"email signature\" → full signature\n"
                         "\"my address\" → your address\n"
                         "\"bug template\" → bug report format")

        # Commands list
        row += 1
        cmd_frame = ttk.Frame(main_frame)
        cmd_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.cmd_listbox = tk.Listbox(cmd_frame, width=50, height=3, selectmode=tk.SINGLE)
        self.cmd_listbox.pack(side=tk.LEFT)
        self.custom_commands = self.config.get("custom_commands", []).copy()
        self._refresh_cmd_listbox()

        cmd_btn_frame = ttk.Frame(cmd_frame)
        cmd_btn_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(cmd_btn_frame, text="Add", width=6, command=self.add_cmd_entry).pack(pady=1)
        ttk.Button(cmd_btn_frame, text="Remove", width=6, command=self.remove_cmd_entry).pack(pady=1)

        # Separator before history
        row += 1
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)

        # Transcription History section
        row += 1
        history_label_frame = ttk.Frame(main_frame)
        history_label_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(5, 2))
        ttk.Label(history_label_frame, text="Transcription History", font=("", 10, "bold")).pack(side=tk.LEFT)
        ttk.Label(history_label_frame, text="(Recent transcriptions)", font=("", 9), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))

        row += 1
        history_frame = ttk.Frame(main_frame)
        history_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)

        # History listbox with scrollbar
        self.history_listbox = tk.Listbox(history_frame, width=60, height=4, selectmode=tk.SINGLE)
        history_scroll = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=history_scroll.set)
        self.history_listbox.pack(side=tk.LEFT)
        history_scroll.pack(side=tk.LEFT, fill=tk.Y)

        history_btn_frame = ttk.Frame(history_frame)
        history_btn_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(history_btn_frame, text="Refresh", width=8, command=self._refresh_history).pack(pady=1)
        ttk.Button(history_btn_frame, text="Clear", width=8, command=self._clear_history).pack(pady=1)

        self._refresh_history()

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

    def on_translation_toggle(self):
        """Update UI when translation mode is toggled."""
        translation_enabled = self.translation_enabled_var.get()
        if translation_enabled:
            # Disable regular language dropdown when translation is enabled
            self.lang_combo.config(state="disabled")
            self.trans_lang_combo.config(state="readonly")
        else:
            # Enable regular language dropdown when translation is disabled
            self.lang_combo.config(state="readonly")
            self.trans_lang_combo.config(state="disabled")

    def refresh_gpu_status(self):
        """Update the GPU status indicator."""
        is_available, status_msg, detail = get_cuda_status()
        self.cuda_available = is_available
        self.cuda_libs_installed = status_msg != "GPU libraries not installed"

        if is_available:
            # Green status
            self.gpu_status_dot.config(foreground="#00aa00")
            self.gpu_status_label.config(text=status_msg, foreground="#00aa00")
            if detail:
                self.gpu_details_label.config(text=f"\u2514 {detail}")
            else:
                self.gpu_details_label.config(text="")
            # Hide install button when CUDA is available
            self.install_gpu_frame.grid_remove()
        else:
            # Red status
            self.gpu_status_dot.config(foreground="#cc0000")
            self.gpu_status_label.config(text=status_msg, foreground="#cc0000")
            if detail:
                self.gpu_details_label.config(text=f"\u2514 {detail}")
            else:
                self.gpu_details_label.config(text="")
            # Show install button only if libraries aren't installed
            if not self.cuda_libs_installed:
                self.install_gpu_frame.grid()
            else:
                self.install_gpu_frame.grid_remove()

        # Update warnings based on current settings
        self.on_gpu_setting_change()

    def on_gpu_setting_change(self, event=None):
        """Update warnings when processing mode changes."""
        # Get current mode from display label
        display_value = self.processing_combo.get()
        # Find the internal mode key
        mode = "auto"
        for key, label in config.PROCESSING_MODE_LABELS.items():
            if label == display_value:
                mode = key
                break

        warnings = []

        # Warn if GPU mode selected but CUDA not available
        if mode in ("gpu-balanced", "gpu-quality") and not self.cuda_available:
            warnings.append("\u26a0 GPU not available - will fall back to CPU")

        if warnings:
            self.gpu_warning_label.config(text="\n".join(warnings))
            self.gpu_warning_frame.grid()
        else:
            self.gpu_warning_label.config(text="")
            self.gpu_warning_frame.grid_remove()

    def get_processing_mode(self):
        """Get the internal processing mode key from the display label."""
        display_value = self.processing_combo.get()
        for key, label in config.PROCESSING_MODE_LABELS.items():
            if label == display_value:
                return key
        return "auto"  # Default fallback

    def install_gpu_support(self):
        """Install GPU dependencies via pip using a modal dialog."""
        # Find requirements-gpu.txt relative to this file or the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        req_file = os.path.join(app_dir, "requirements-gpu.txt")

        if not os.path.exists(req_file):
            messagebox.showerror("File Not Found",
                               f"Could not find requirements-gpu.txt\n\n"
                               f"Expected at: {req_file}\n\n"
                               f"Please install manually:\n"
                               f"pip install -r requirements-gpu.txt")
            return

        # Confirm with user
        if not messagebox.askyesno("Install GPU Support",
                                   "This will download and install NVIDIA CUDA libraries.\n\n"
                                   "Download size: ~2-3 GB\n"
                                   "Requires: NVIDIA GPU with CUDA support\n\n"
                                   "Continue?",
                                   parent=self.window):
            return

        # Create modal dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Installing GPU Support")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()  # Make it modal

        # Center on parent window
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 400) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 180) // 2
        dialog.geometry(f"+{x}+{y}")

        # Prevent closing during install
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(frame, text="Installing NVIDIA CUDA Libraries",
                                font=("", 11, "bold"))
        title_label.pack(pady=(0, 15))

        # Progress bar
        progress = ttk.Progressbar(frame, mode='indeterminate', length=350)
        progress.pack(pady=5)
        progress.start(10)

        # Status label
        status_label = ttk.Label(frame, text="Downloading... this may take several minutes",
                                  font=("", 9), foreground="gray")
        status_label.pack(pady=10)

        # Size hint
        size_hint = ttk.Label(frame, text="(Download size: ~2-3 GB)",
                              font=("", 8), foreground="#888888")
        size_hint.pack()

        # Store references for the completion handler
        self._install_dialog = dialog
        self._install_progress = progress
        self._install_status = status_label

        def run_install():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file],
                    capture_output=True,
                    text=True,
                    cwd=app_dir
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr

                # Schedule UI update on main thread
                self.window.after(0, lambda: self.install_complete(success, output))
            except Exception as e:
                self.window.after(0, lambda: self.install_complete(False, str(e)))

        # Run in background thread
        thread = threading.Thread(target=run_install, daemon=True)
        thread.start()

    def install_complete(self, success, output):
        """Handle completion of GPU installation."""
        # Stop progress and close dialog
        if hasattr(self, '_install_progress'):
            self._install_progress.stop()
        if hasattr(self, '_install_dialog') and self._install_dialog:
            self._install_dialog.destroy()
            self._install_dialog = None

        if success:
            # Custom dialog with Restart Now / Later buttons
            self._show_restart_dialog()
            # Refresh status (may still show unavailable until restart)
            self.refresh_gpu_status()
        else:
            # Show error with manual instructions
            msg = ("Installation failed.\n\n"
                   "Try installing manually:\n"
                   "1. Open a terminal/command prompt\n"
                   "2. Navigate to the MurmurTone folder\n"
                   "3. Run: pip install -r requirements-gpu.txt\n\n")
            if output:
                # Truncate long output
                if len(output) > 500:
                    output = output[:500] + "..."
                msg += f"Error details:\n{output}"
            messagebox.showerror("Installation Failed", msg, parent=self.window)

    def _show_restart_dialog(self):
        """Show a dialog with Restart Now / Later options."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Installation Complete")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 350) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Success message
        ttk.Label(frame, text="GPU support installed successfully!",
                  font=("", 10, "bold")).pack(pady=(0, 10))
        ttk.Label(frame, text="Restart MurmurTone to use GPU acceleration.",
                  font=("", 9)).pack(pady=(0, 15))

        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        def restart_now():
            dialog.destroy()
            self.close()
            # Write restart signal file for parent process
            app_dir = os.path.dirname(os.path.abspath(__file__))
            restart_signal = os.path.join(app_dir, ".restart_signal")
            try:
                with open(restart_signal, "w") as f:
                    f.write("restart")
            except Exception:
                pass  # Best effort
            # Launch new instance - parent will see signal and exit
            script = os.path.join(app_dir, "murmurtone.py")
            subprocess.Popen([sys.executable, script], cwd=app_dir)

        def later():
            dialog.destroy()

        ttk.Button(btn_frame, text="Restart Now", command=restart_now).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Later", command=later).pack(side=tk.LEFT, padx=5)

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

    def _db_to_x(self, db):
        """Convert dB value (-60 to -20) to x pixel position."""
        # Map -60 to -20 dB → 0 to meter_width pixels
        return int((db + 60) / 40 * self.meter_width)

    def _x_to_db(self, x):
        """Convert x pixel position to dB value (-60 to -20)."""
        # Clamp x to valid range
        x = max(0, min(self.meter_width, x))
        # Map 0 to meter_width pixels → -60 to -20 dB
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

    def toggle_noise_test(self):
        """Start or stop the noise gate level test."""
        if self.noise_test_running:
            self.stop_noise_test()
        else:
            self.start_noise_test()

    def start_noise_test(self):
        """Start testing microphone with noise gate level visualization."""
        device_info = self.get_selected_device_info()

        device_index = None
        if device_info:
            device_index = device_info.get("index")

        try:
            sample_rate = int(self.rate_var.get())
        except ValueError:
            sample_rate = 16000

        try:
            self.noise_test_stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype='float32',
                device=device_index,
                callback=self.noise_test_audio_callback
            )
            self.noise_test_stream.start()
            self.noise_test_running = True
            self.noise_test_btn.config(text="Stop")
            # Schedule auto-stop after 10 seconds (longer than device test)
            self.window.after(10000, self.auto_stop_noise_test)
        except Exception as e:
            messagebox.showerror("Test Failed", f"Could not open device:\n{e}")

    def noise_test_audio_callback(self, indata, frames, time_info, status):
        """Callback for noise gate test - updates level meter with gating visual."""
        if not self.noise_test_running:
            return
        # Calculate RMS level
        rms = np.sqrt(np.mean(indata**2))
        # Convert to dB (with floor at -60dB)
        db = 20 * np.log10(max(rms, 1e-6))
        # Get threshold for comparison
        threshold_db = self.noise_threshold_var.get()
        # Normalize to 0-1 range (-60dB to 0dB) - same as level meter
        level = max(0, min(1, (db + 60) / 60))
        # Determine if gated (below threshold)
        is_gated = db < threshold_db
        # Schedule UI update on main thread
        try:
            self.window.after_idle(lambda: self.update_noise_level_meter(level, is_gated))
        except Exception:
            pass  # Window may be closing

    def update_noise_level_meter(self, level, is_gated):
        """Update the noise gate level meter display."""
        if not self.noise_test_running or not self.noise_level_canvas:
            return
        width = int(level * self.meter_width)
        # Color based on gating status
        if is_gated:
            color = "#555555"  # Dim gray when gated (below threshold)
        elif level < 0.5:
            color = "#00aa00"  # Green - normal
        elif level < 0.75:
            color = "#aaaa00"  # Yellow - getting loud
        else:
            color = "#aa0000"  # Red - very loud
        self.noise_level_canvas.coords(self.noise_level_bar, 0, 0, width, self.meter_height)
        self.noise_level_canvas.itemconfig(self.noise_level_bar, fill=color)

    def auto_stop_noise_test(self):
        """Auto-stop noise gate test after timeout."""
        if self.noise_test_running:
            self.stop_noise_test()

    def stop_noise_test(self):
        """Stop the noise gate test."""
        self.noise_test_running = False
        if self.noise_test_stream:
            try:
                self.noise_test_stream.stop()
                self.noise_test_stream.close()
            except Exception:
                pass
            self.noise_test_stream = None
        self.noise_test_btn.config(text="Test")
        # Reset level meter
        if self.noise_level_canvas:
            self.noise_level_canvas.coords(self.noise_level_bar, 0, 0, 0, 16)

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

        try:
            preview_delay = float(self.preview_delay_var.get())
            preview_delay = max(0.0, min(10.0, preview_delay))  # Clamp to reasonable range
        except ValueError:
            preview_delay = 2.0

        # Get selected device info (None for System Default)
        device_info = self.get_selected_device_info()

        # Convert language label back to code
        lang_label = self.lang_var.get()
        lang_code = next((code for code, label in config.LANGUAGE_LABELS.items()
                          if label == lang_label), lang_label)

        # Convert translation source language label back to code
        trans_lang_label = self.trans_lang_var.get()
        trans_lang_code = next((code for code, label in config.LANGUAGE_LABELS.items()
                               if label == trans_lang_label), trans_lang_label)

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
            # GPU/CUDA settings
            "processing_mode": self.get_processing_mode(),
            # Noise gate settings
            "noise_gate_enabled": self.noise_gate_var.get(),
            "noise_gate_threshold_db": self.noise_threshold_var.get(),
            # Audio feedback settings
            "audio_feedback_volume": self.volume_var.get(),
            "sound_processing": self.sound_processing_var.get(),
            "sound_success": self.sound_success_var.get(),
            "sound_error": self.sound_error_var.get(),
            # Text processing settings
            "voice_commands_enabled": self.voice_commands_var.get(),
            "scratch_that_enabled": self.scratch_that_var.get(),
            "filler_removal_enabled": self.filler_var.get(),
            "filler_removal_aggressive": self.filler_aggressive_var.get(),
            "custom_fillers": self.config.get("custom_fillers", []),  # Preserve existing
            "custom_dictionary": self.custom_dictionary,
            "custom_commands": self.custom_commands,
            # Preview window settings
            "preview_enabled": self.preview_enabled_var.get(),
            "preview_position": self.preview_position_var.get(),
            "preview_auto_hide_delay": preview_delay,
            "preview_theme": self.preview_theme_var.get(),
            "preview_font_size": self.preview_font_size_var.get()
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
        default_lang_label = config.LANGUAGE_LABELS.get(defaults["language"], defaults["language"])
        self.lang_var.set(default_lang_label)
        # Reset translation settings
        self.translation_enabled_var.set(defaults["translation_enabled"])
        default_trans_lang = defaults["translation_source_language"]
        default_trans_label = config.LANGUAGE_LABELS.get(default_trans_lang, default_trans_lang)
        self.trans_lang_var.set(default_trans_label)
        self.on_translation_toggle()  # Update UI state
        self.rate_var.set(str(defaults["sample_rate"]))
        self.hotkey_capture.set_hotkey(defaults["hotkey"])
        self.mode_var.set(defaults["recording_mode"])
        self.silence_var.set(str(defaults["silence_duration_sec"]))
        self.feedback_var.set(defaults["audio_feedback"])
        self.autopaste_var.set(defaults["auto_paste"])
        self.paste_mode_var.set(defaults["paste_mode"])
        # Reset GPU settings
        default_mode = defaults["processing_mode"]
        self.processing_combo.set(config.PROCESSING_MODE_LABELS.get(default_mode, "Auto"))
        # Reset noise gate settings
        self.noise_gate_var.set(defaults["noise_gate_enabled"])
        self.noise_threshold_var.set(defaults["noise_gate_threshold_db"])
        # Reset audio feedback settings
        self.sound_processing_var.set(defaults["sound_processing"])
        self.sound_success_var.set(defaults["sound_success"])
        self.sound_error_var.set(defaults["sound_error"])
        self.volume_var.set(defaults["audio_feedback_volume"])
        # Reset text processing settings
        self.voice_commands_var.set(defaults["voice_commands_enabled"])
        self.scratch_that_var.set(defaults["scratch_that_enabled"])
        self.filler_var.set(defaults["filler_removal_enabled"])
        self.filler_aggressive_var.set(defaults["filler_removal_aggressive"])
        self.custom_dictionary = []
        self._refresh_dict_listbox()
        self.custom_commands = []
        self._refresh_cmd_listbox()
        # Reset preview settings
        self.preview_enabled_var.set(defaults["preview_enabled"])
        self.preview_position_var.set(defaults["preview_position"])
        self.preview_delay_var.set(str(defaults["preview_auto_hide_delay"]))
        self.preview_theme_var.set(defaults["preview_theme"])
        self.preview_font_size_var.set(defaults["preview_font_size"])
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

    def _refresh_cmd_listbox(self):
        """Refresh the custom commands listbox display."""
        self.cmd_listbox.delete(0, tk.END)
        for entry in self.custom_commands:
            trigger = entry.get("trigger", "")
            replacement = entry.get("replacement", "")
            # Truncate long replacement for display
            display_repl = replacement[:30] + "..." if len(replacement) > 30 else replacement
            display_repl = display_repl.replace("\n", " ")
            self.cmd_listbox.insert(tk.END, f'"{trigger}" -> "{display_repl}"')

    def add_cmd_entry(self):
        """Show dialog to add a custom command entry."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Custom Command")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 400) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 250) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Trigger phrase:").grid(row=0, column=0, sticky=tk.W, pady=5)
        trigger_var = tk.StringVar()
        trigger_entry = ttk.Entry(frame, textvariable=trigger_var, width=40)
        trigger_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Expands to:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        replacement_text = tk.Text(frame, width=40, height=5, wrap=tk.WORD)
        replacement_text.grid(row=1, column=1, sticky=tk.W, pady=5)

        hint = ttk.Label(frame, text="Tip: Use multiple lines for templates",
                        font=("", 8), foreground="gray")
        hint.grid(row=2, column=1, sticky=tk.W)

        def do_add():
            trigger = trigger_var.get().strip()
            replacement = replacement_text.get("1.0", tk.END).strip()
            if trigger and replacement:
                self.custom_commands.append({
                    "trigger": trigger,
                    "replacement": replacement,
                    "enabled": True
                })
                self._refresh_cmd_listbox()
                dialog.destroy()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Add", command=do_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        trigger_entry.focus_set()

    def remove_cmd_entry(self):
        """Remove selected custom command entry."""
        selection = self.cmd_listbox.curselection()
        if selection:
            idx = selection[0]
            self.custom_commands.pop(idx)
            self._refresh_cmd_listbox()

    def _refresh_history(self):
        """Refresh the history listbox from disk."""
        self.history_listbox.delete(0, tk.END)
        entries = text_processor.TranscriptionHistory.load_from_disk()
        # Show newest first (entries are stored oldest first)
        for entry in reversed(entries):
            text = entry.get("text", "")
            # Truncate long entries for display
            display = text[:80] + "..." if len(text) > 80 else text
            # Replace newlines with spaces for single-line display
            display = display.replace("\n", " ")
            self.history_listbox.insert(tk.END, display)
        if not entries:
            self.history_listbox.insert(tk.END, "(No history yet)")

    def _clear_history(self):
        """Clear all history."""
        if messagebox.askyesno("Clear History", "Clear all transcription history?"):
            text_processor.TranscriptionHistory.clear_on_disk()
            self._refresh_history()

    def close(self):
        """Close the window."""
        # Stop any running test
        self.stop_noise_test()
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
