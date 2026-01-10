"""
Preview window for MurmurTone - shows real-time transcription status.

Thread-safe implementation using a dedicated tkinter thread with command queue.
All tkinter operations happen on the dedicated thread, while commands can be
sent from any thread via the queue.
"""
import tkinter as tk
import threading
import queue
import atexit
import logging

log = logging.getLogger("murmurtone")

# Theme definitions (also in config.py, duplicated here to avoid import issues)
THEMES = {
    "dark": {
        "bg": "#1a1a1a",
        "text": "#ffffff",
        "recording": "#ff6b6b",
        "transcribing": "#ffd93d",
        "success": "#ffffff",
    },
    "light": {
        "bg": "#f5f5f5",
        "text": "#1a1a1a",
        "recording": "#e53935",
        "transcribing": "#f9a825",
        "success": "#1a1a1a",
    },
}


class PreviewWindow:
    """
    Floating preview window that shows transcription status.
    - Shows "Recording..." while recording (red)
    - Shows "Transcribing..." while processing (yellow)
    - Shows transcribed text briefly before/after paste (white)
    - Auto-hides after configurable delay

    Thread-safe: all public methods can be called from any thread.
    """

    # Command types for the queue
    CMD_SHOW = "show"
    CMD_HIDE = "hide"
    CMD_CONFIGURE = "configure"
    CMD_QUIT = "quit"

    def __init__(self):
        self._command_queue = queue.Queue()
        self._thread = None
        self._started = threading.Event()
        self._stopped = threading.Event()

        # Configuration (can be updated via configure())
        self.enabled = True
        self.position = "bottom-right"  # top-right, bottom-right, top-left, bottom-left
        self.auto_hide_delay = 2.0  # seconds, 0 to disable
        self.opacity = 0.9
        self.theme = "dark"  # dark, light
        self.font_size = 11  # 8-18

        # Internal state (only accessed from tkinter thread)
        self._window = None
        self._label = None
        self._frame = None
        self._hide_timer_id = None

    def start(self):
        """Start the preview window thread. Safe to call multiple times."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stopped.clear()
        self._thread = threading.Thread(target=self._run_tkinter_loop, daemon=True)
        self._thread.start()
        # Wait for tkinter to initialize
        self._started.wait(timeout=2.0)

    def stop(self):
        """Stop the preview window thread."""
        if self._thread is None or not self._thread.is_alive():
            return

        self._command_queue.put((self.CMD_QUIT, None))
        self._stopped.wait(timeout=2.0)
        self._thread = None

    def _get_theme_color(self, key):
        """Get color from current theme."""
        theme_colors = THEMES.get(self.theme, THEMES["dark"])
        return theme_colors.get(key, "#ffffff")

    def show_recording(self, duration_seconds=None):
        """Show 'Recording...' status (red), optionally with duration."""
        if not self.enabled:
            return
        if duration_seconds is not None:
            mins, secs = divmod(int(duration_seconds), 60)
            text = f"Recording... {mins}:{secs:02d}"
        else:
            text = "Recording..."
        self._send_show(text, self._get_theme_color("recording"), auto_hide=False)

    def show_transcribing(self):
        """Show 'Transcribing...' status (yellow)."""
        if not self.enabled:
            return
        self._send_show("Transcribing...", self._get_theme_color("transcribing"), auto_hide=False)

    def show_text(self, text, auto_hide=True):
        """Show transcribed text, optionally auto-hiding."""
        if not self.enabled:
            return
        # Truncate very long text for display
        display_text = text[:200] + "..." if len(text) > 200 else text
        self._send_show(display_text, self._get_theme_color("success"), auto_hide=auto_hide)

    def hide(self):
        """Hide the preview window."""
        self._command_queue.put((self.CMD_HIDE, None))

    def configure(self, enabled=None, position=None, auto_hide_delay=None, opacity=None,
                  theme=None, font_size=None):
        """
        Update configuration. Thread-safe.

        Args:
            enabled: Enable/disable preview window
            position: Screen position (top-right, bottom-right, top-left, bottom-left)
            auto_hide_delay: Seconds before auto-hiding (0 to disable)
            opacity: Window opacity (0.0 to 1.0)
            theme: Color theme (dark, light)
            font_size: Font size (8-18)
        """
        config = {}
        if enabled is not None:
            self.enabled = enabled
            config["enabled"] = enabled
        if position is not None:
            self.position = position
            config["position"] = position
        if auto_hide_delay is not None:
            self.auto_hide_delay = auto_hide_delay
            config["auto_hide_delay"] = auto_hide_delay
        if opacity is not None:
            self.opacity = opacity
            config["opacity"] = opacity
        if theme is not None:
            self.theme = theme
            config["theme"] = theme
        if font_size is not None:
            self.font_size = font_size
            config["font_size"] = font_size

        if config:
            self._command_queue.put((self.CMD_CONFIGURE, config))

    def _send_show(self, text, color, auto_hide):
        """Send a show command to the tkinter thread."""
        self.start()  # Ensure thread is running
        self._command_queue.put((self.CMD_SHOW, {
            "text": text,
            "color": color,
            "auto_hide": auto_hide
        }))

    def _run_tkinter_loop(self):
        """Main loop running in dedicated tkinter thread."""
        try:
            self._create_window()
            self._started.set()
            self._process_commands()
        except Exception as e:
            log.error(f"Preview window error: {e}")
        finally:
            self._cleanup()
            self._stopped.set()

    def _create_window(self):
        """Create the tkinter window (called from tkinter thread)."""
        self._window = tk.Tk()
        self._window.title("")
        self._window.overrideredirect(True)  # No title bar/borders
        self._window.attributes("-topmost", True)  # Always on top
        self._window.attributes("-alpha", self.opacity)

        # Get theme colors
        bg_color = self._get_theme_color("bg")
        text_color = self._get_theme_color("text")

        # Apply background color
        self._window.configure(bg=bg_color)

        # Main frame with padding
        self._frame = tk.Frame(self._window, bg=bg_color, padx=15, pady=10)
        self._frame.pack(fill=tk.BOTH, expand=True)

        # Text label
        self._label = tk.Label(
            self._frame,
            text="",
            font=("Segoe UI", self.font_size),
            fg=text_color,
            bg=bg_color,
            wraplength=350,
            justify=tk.LEFT
        )
        self._label.pack()

        # Hide initially
        self._window.withdraw()

        # Handle window close (shouldn't happen with overrideredirect, but be safe)
        self._window.protocol("WM_DELETE_WINDOW", self._on_close_request)

    def _process_commands(self):
        """Process commands from the queue (runs in tkinter thread)."""
        try:
            while True:
                # Check for commands (non-blocking with short timeout)
                try:
                    cmd, data = self._command_queue.get(timeout=0.05)
                except queue.Empty:
                    # No command, just update tkinter
                    self._window.update()
                    continue

                if cmd == self.CMD_QUIT:
                    break
                elif cmd == self.CMD_SHOW:
                    self._do_show(data["text"], data["color"], data["auto_hide"])
                elif cmd == self.CMD_HIDE:
                    self._do_hide()
                elif cmd == self.CMD_CONFIGURE:
                    self._do_configure(data)

                self._window.update()

        except tk.TclError:
            # Window was destroyed
            pass

    def _do_show(self, text, color, auto_hide):
        """Actually show the text (called from tkinter thread)."""
        # Cancel any pending hide timer
        self._cancel_hide_timer()

        # Update label
        self._label.config(text=text, fg=color)

        # Position and show window
        self._position_window()
        self._window.deiconify()

        # Schedule auto-hide if requested
        if auto_hide and self.auto_hide_delay > 0:
            delay_ms = int(self.auto_hide_delay * 1000)
            self._hide_timer_id = self._window.after(delay_ms, self._do_hide)

    def _do_hide(self):
        """Actually hide the window (called from tkinter thread)."""
        self._cancel_hide_timer()
        self._window.withdraw()

    def _do_configure(self, config):
        """Apply configuration changes (called from tkinter thread)."""
        if "opacity" in config:
            try:
                self._window.attributes("-alpha", config["opacity"])
            except tk.TclError:
                pass

        if "position" in config:
            self.position = config["position"]
            # Reposition if currently visible
            if self._window.state() == "normal":
                self._position_window()

        if "theme" in config:
            self.theme = config["theme"]
            # Update colors
            bg_color = self._get_theme_color("bg")
            try:
                self._window.configure(bg=bg_color)
                self._frame.configure(bg=bg_color)
                self._label.configure(bg=bg_color)
            except tk.TclError:
                pass

        if "font_size" in config:
            self.font_size = config["font_size"]
            try:
                self._label.configure(font=("Segoe UI", self.font_size))
            except tk.TclError:
                pass

    def _position_window(self):
        """Position the window based on settings."""
        self._window.update_idletasks()

        # Get screen dimensions
        screen_width = self._window.winfo_screenwidth()
        screen_height = self._window.winfo_screenheight()

        # Window dimensions
        win_width = max(200, self._window.winfo_reqwidth())
        win_height = self._window.winfo_reqheight()

        # Padding from screen edges
        padding = 20
        taskbar_height = 50  # Approximate Windows taskbar height

        if self.position == "top-right":
            x = screen_width - win_width - padding
            y = padding + 40
        elif self.position == "top-left":
            x = padding
            y = padding + 40
        elif self.position == "bottom-left":
            x = padding
            y = screen_height - win_height - padding - taskbar_height
        else:  # bottom-right (default)
            x = screen_width - win_width - padding
            y = screen_height - win_height - padding - taskbar_height

        self._window.geometry(f"+{x}+{y}")

    def _cancel_hide_timer(self):
        """Cancel any pending hide timer."""
        if self._hide_timer_id is not None:
            try:
                self._window.after_cancel(self._hide_timer_id)
            except tk.TclError:
                pass
            self._hide_timer_id = None

    def _on_close_request(self):
        """Handle window close request."""
        self._do_hide()

    def _cleanup(self):
        """Clean up tkinter resources."""
        try:
            if self._window:
                self._window.destroy()
        except tk.TclError:
            pass
        self._window = None
        self._label = None


# Global singleton instance
_preview = None
_preview_lock = threading.Lock()


def get_preview():
    """Get the global preview window instance (thread-safe singleton)."""
    global _preview
    with _preview_lock:
        if _preview is None:
            _preview = PreviewWindow()
        return _preview


def show_recording(duration_seconds=None):
    """Show recording status, optionally with duration."""
    get_preview().show_recording(duration_seconds=duration_seconds)


def show_transcribing():
    """Show transcribing status."""
    get_preview().show_transcribing()


def show_text(text, auto_hide=True):
    """Show transcribed text."""
    get_preview().show_text(text, auto_hide)


def hide():
    """Hide the preview."""
    get_preview().hide()


def configure(**kwargs):
    """Configure the preview window."""
    get_preview().configure(**kwargs)


def start():
    """Start the preview window thread."""
    get_preview().start()


def stop():
    """Stop the preview window thread."""
    get_preview().stop()


# Ensure cleanup on exit
def _cleanup_on_exit():
    global _preview
    if _preview:
        _preview.stop()


atexit.register(_cleanup_on_exit)


if __name__ == "__main__":
    # Test the preview window standalone
    import time

    print("Testing preview window...")
    print("1. Showing 'Recording...' (red)")
    show_recording()
    time.sleep(2)

    print("2. Showing 'Transcribing...' (yellow)")
    show_transcribing()
    time.sleep(1.5)

    print("3. Showing transcribed text (white, will auto-hide)")
    show_text("Hello, this is a test transcription that should appear briefly and then auto-hide after 2 seconds.")
    time.sleep(4)

    print("4. Testing position change")
    configure(position="top-left")
    show_text("Now in top-left corner!", auto_hide=True)
    time.sleep(3)

    print("5. Done! Stopping...")
    stop()
    print("Test complete.")
