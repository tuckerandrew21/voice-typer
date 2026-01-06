"""
Simple Voice Typer - Press hotkey to record, release to transcribe and type.
"""
import sys
import os
import threading
import time
import numpy as np
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Controller, Key
from PIL import Image
import pystray
import config

# Global state
app_config = None
model = None
model_ready = False
model_loading = False
keyboard_controller = Controller()
current_keys = set()
is_recording = False
audio_data = []
stream = None
tray_icon = None
key_listener = None


def load_model(model_size=None):
    """Load or reload the Whisper model."""
    global model, model_ready, model_loading

    if model_size is None:
        model_size = app_config["model_size"]

    model_ready = False
    model_loading = True

    if tray_icon:
        tray_icon.title = f"Voice Typer - Loading {model_size}..."

    print(f"Loading Whisper model ({model_size})...", flush=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    model_ready = True
    model_loading = False
    print("Model loaded! Ready.", flush=True)

    if tray_icon:
        tray_icon.title = "Voice Typer - Ready"


def audio_callback(indata, frames, time_info, status):
    global audio_data, is_recording
    if is_recording:
        audio_data.append(indata.copy())


def start_recording():
    global is_recording, audio_data, stream
    if not model_ready:
        print("Model still loading, please wait...", flush=True)
        return
    if is_recording:
        return
    print("\n>> Recording...", flush=True)
    is_recording = True
    audio_data = []
    sample_rate = app_config.get("sample_rate", 16000)
    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32, callback=audio_callback)
    stream.start()


def stop_recording():
    global is_recording, stream, audio_data
    if not is_recording:
        return
    is_recording = False
    if stream:
        stream.stop()
        stream.close()
        stream = None

    if not audio_data:
        print("No audio.", flush=True)
        return

    print(">> Transcribing...", flush=True)
    audio = np.concatenate(audio_data, axis=0).flatten()

    language = app_config.get("language", "en")
    if language == "auto":
        language = None

    segments, _ = model.transcribe(audio, language=language)
    text = "".join(segment.text for segment in segments).strip()

    if text:
        print(f">> Typing: {text}", flush=True)
        time.sleep(0.1)
        keyboard_controller.type(text + " ")
    else:
        print(">> No speech detected.", flush=True)

    hotkey_str = config.hotkey_to_string(app_config["hotkey"])
    print(f"\nReady. Press {hotkey_str}.", flush=True)


def check_hotkey():
    """Check if the configured hotkey is currently pressed."""
    hotkey = app_config["hotkey"]

    # Check modifiers
    ctrl_required = hotkey.get("ctrl", False)
    shift_required = hotkey.get("shift", False)
    alt_required = hotkey.get("alt", False)
    main_key = hotkey.get("key", "space").lower()

    ctrl_pressed = Key.ctrl_l in current_keys or Key.ctrl_r in current_keys
    shift_pressed = Key.shift in current_keys or Key.shift_l in current_keys or Key.shift_r in current_keys
    alt_pressed = Key.alt_l in current_keys or Key.alt_r in current_keys or Key.alt_gr in current_keys

    if ctrl_required != ctrl_pressed:
        return False
    if shift_required != shift_pressed:
        return False
    if alt_required != alt_pressed:
        return False

    # Check main key
    for key in current_keys:
        try:
            if hasattr(key, 'char') and key.char and key.char.lower() == main_key:
                return True
            if hasattr(key, 'name') and key.name and key.name.lower() == main_key:
                return True
        except AttributeError:
            pass

    # Check special keys like space
    if main_key == "space" and Key.space in current_keys:
        return True

    return False


def on_press(key):
    global current_keys
    current_keys.add(key)
    if check_hotkey() and not is_recording:
        start_recording()


def on_release(key):
    global current_keys
    current_keys.discard(key)
    if is_recording:
        threading.Thread(target=stop_recording).start()


# System tray
def get_icon_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "icon.ico")


def on_quit(icon, item):
    print("\nExiting...", flush=True)
    icon.stop()
    os._exit(0)


def on_settings(icon, item):
    """Open settings window in a separate thread."""
    threading.Thread(target=open_settings_window, daemon=True).start()


def open_settings_window():
    """Open the settings GUI."""
    import settings_gui
    settings_gui.open_settings(app_config, on_settings_saved)


def on_settings_saved(new_config):
    """Called when settings are saved."""
    global app_config

    old_model = app_config.get("model_size")
    new_model = new_config.get("model_size")

    app_config = new_config

    # Reload model if changed
    if old_model != new_model:
        print(f"Model changed from {old_model} to {new_model}, reloading...", flush=True)
        threading.Thread(target=load_model, args=(new_model,), daemon=True).start()

    hotkey_str = config.hotkey_to_string(app_config["hotkey"])
    print(f"Settings saved. Hotkey: {hotkey_str}", flush=True)


def get_status_text(item):
    if model_loading:
        return f"Status: Loading {app_config['model_size']}..."
    if model_ready:
        return "Status: Ready"
    return "Status: Initializing..."


def create_tray_icon():
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        image = Image.open(icon_path)
    else:
        image = Image.new('RGB', (64, 64), color='#4a9eff')

    menu = pystray.Menu(
        pystray.MenuItem("Voice Typer", None, enabled=False),
        pystray.MenuItem(get_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Settings", on_settings),
        pystray.MenuItem("Exit", on_quit)
    )

    icon = pystray.Icon("voice_typer", image, "Voice Typer - Loading...", menu)
    return icon


def run_keyboard_listener():
    global key_listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        key_listener = listener
        listener.join()


def main():
    global tray_icon, app_config

    # Load configuration
    app_config = config.load_config()
    hotkey_str = config.hotkey_to_string(app_config["hotkey"])

    # Start keyboard listener
    listener_thread = threading.Thread(target=run_keyboard_listener, daemon=True)
    listener_thread.start()

    # Load model in background
    model_thread = threading.Thread(target=load_model, daemon=True)
    model_thread.start()

    # Create and run tray icon (blocks)
    tray_icon = create_tray_icon()
    print("System tray icon started.", flush=True)
    print(f"Press {hotkey_str} to record (after model loads).", flush=True)
    tray_icon.run()


if __name__ == "__main__":
    main()
