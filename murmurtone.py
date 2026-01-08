"""
MurmurTone - Private, local voice-to-text for Windows.
Press hotkey to record, release to transcribe and type.
"""
import sys
import os
import threading
import time
import io
import wave
import winsound
import numpy as np
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Controller, Key
from PIL import Image, ImageDraw
import pystray
import config
import text_processor

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
transcription_history = text_processor.TranscriptionHistory()

# Audio feedback sounds
start_sound = None
stop_sound = None

# Silence detection state
silence_start_time = None

# Status icons
icon_ready = None
icon_recording = None


# Path helpers for PyInstaller bundled exe
def get_resource_path(filename):
    """Get path to bundled resource, handling PyInstaller frozen exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - resources in temp _MEIPASS folder
        return os.path.join(sys._MEIPASS, filename)
    else:
        # Running as script - resources in script directory
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


def get_model_path(model_size):
    """Get path to Whisper model, checking for bundled model first."""
    if getattr(sys, 'frozen', False):
        # Check for bundled model in exe
        bundled = os.path.join(sys._MEIPASS, "models", model_size)
        if os.path.exists(bundled):
            return bundled
    # Fall back to HuggingFace download (will cache in ~/.cache/huggingface/)
    return model_size


def generate_click_sound(frequency=800, duration_ms=50, volume=0.3):
    """Generate a simple click sound as WAV bytes."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)

    # Generate sine wave
    t = np.linspace(0, duration_ms / 1000, num_samples, dtype=np.float32)
    wave_data = np.sin(2 * np.pi * frequency * t) * volume

    # Apply fade envelope to avoid clicks
    fade_samples = int(num_samples * 0.1)
    if fade_samples > 0:
        wave_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Convert to 16-bit PCM
    pcm_data = (wave_data * 32767).astype(np.int16)

    # Create WAV in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return buffer.getvalue()


def init_sounds():
    """Initialize audio feedback sounds at startup."""
    global start_sound, stop_sound
    try:
        start_sound = generate_click_sound(frequency=1000, duration_ms=50)
        stop_sound = generate_click_sound(frequency=600, duration_ms=80)
    except Exception as e:
        print(f"Warning: Could not initialize sounds: {e}", flush=True)
        start_sound = stop_sound = None


def play_sound(sound_data):
    """Play a sound asynchronously (non-blocking)."""
    if not app_config.get("audio_feedback", True):
        return
    if sound_data:
        threading.Thread(
            target=lambda: winsound.PlaySound(sound_data, winsound.SND_MEMORY),
            daemon=True
        ).start()


def generate_status_icon(color):
    """Generate a simple colored circle icon."""
    size = 64
    image = Image.new('RGB', (size, size), color=color)
    return image


def init_icons():
    """Initialize status icons."""
    global icon_ready, icon_recording
    icon_ready = generate_status_icon('#4CAF50')      # Green
    icon_recording = generate_status_icon('#F44336')  # Red


def update_tray_icon(recording=False):
    """Update tray icon based on recording state."""
    if tray_icon:
        tray_icon.icon = icon_recording if recording else icon_ready


def load_model(model_size=None):
    """Load or reload the Whisper model."""
    global model, model_ready, model_loading

    if model_size is None:
        model_size = app_config["model_size"]

    model_ready = False
    model_loading = True

    if tray_icon:
        tray_icon.title = f"MurmurTone - Loading {model_size}..."

    print(f"Loading Whisper model ({model_size})...", flush=True)
    from faster_whisper import WhisperModel

    # Use bundled model if available, otherwise download from HuggingFace
    model_path = get_model_path(model_size)
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    model_ready = True
    model_loading = False
    print("Model loaded! Ready.", flush=True)

    if tray_icon:
        tray_icon.title = "MurmurTone - Ready"


def calculate_rms(audio_chunk):
    """Calculate RMS (root mean square) amplitude of audio chunk."""
    if len(audio_chunk) == 0:
        return 0
    return np.sqrt(np.mean(audio_chunk ** 2))


def rms_to_db(rms, reference=1.0):
    """Convert RMS value to decibels."""
    if rms <= 0:
        return -100  # Effectively silent
    return 20 * np.log10(rms / reference)


def auto_stop_recording():
    """Called when silence threshold is reached in auto-stop mode."""
    global is_recording, silence_start_time

    if not is_recording:
        return

    print(">> Auto-stopped (silence detected)", flush=True)
    silence_start_time = None
    stop_recording()


def audio_callback(indata, frames, time_info, status):
    global audio_data, is_recording, silence_start_time

    if not is_recording:
        return

    audio_data.append(indata.copy())

    # Only check silence in auto_stop mode
    if app_config.get("recording_mode") != "auto_stop":
        return

    # Calculate current audio level
    rms = calculate_rms(indata)
    db = rms_to_db(rms)

    threshold_db = -40  # dB threshold for silence
    silence_duration = app_config.get("silence_duration_sec", 2.0)

    current_time = time.time()

    if db < threshold_db:
        # Below threshold - silence detected
        if silence_start_time is None:
            silence_start_time = current_time
        elif (current_time - silence_start_time) >= silence_duration:
            # Silence duration exceeded - trigger stop via thread to avoid callback blocking
            threading.Thread(target=auto_stop_recording, daemon=True).start()
            silence_start_time = None  # Prevent re-triggering
    else:
        # Above threshold - reset silence timer
        silence_start_time = None


def start_recording():
    global is_recording, audio_data, stream, silence_start_time
    if not model_ready:
        print("Model still loading, please wait...", flush=True)
        return
    if is_recording:
        return

    play_sound(start_sound)
    update_tray_icon(recording=True)

    print("\n>> Recording...", flush=True)
    is_recording = True
    audio_data = []
    silence_start_time = None
    sample_rate = app_config.get("sample_rate", 16000)
    # Get selected input device (None = system default)
    device_index = config.get_device_index(app_config.get("input_device"))
    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.float32,
                            device=device_index, callback=audio_callback)
    stream.start()


def stop_recording():
    global is_recording, stream, audio_data, silence_start_time
    if not is_recording:
        return
    is_recording = False
    silence_start_time = None

    play_sound(stop_sound)
    update_tray_icon(recording=False)

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
    raw_text = "".join(segment.text for segment in segments).strip()

    # Process text through the pipeline (dictionary, fillers, commands)
    text, should_scratch, scratch_length = text_processor.process_text(
        raw_text, app_config, transcription_history
    )

    # Handle "scratch that" - delete previous transcription
    if should_scratch and scratch_length > 0:
        print(f">> Scratching last {scratch_length} characters...", flush=True)
        time.sleep(0.1)
        for _ in range(scratch_length):
            keyboard_controller.press(Key.backspace)
            keyboard_controller.release(Key.backspace)
        # Don't output anything else for this transcription
        hotkey_str = config.hotkey_to_string(app_config["hotkey"])
        print(f"\nReady. Press {hotkey_str}.", flush=True)
        return

    if text:
        # Track this transcription for potential "scratch that"
        text_with_space = text + " "
        transcription_history.add(text_with_space)

        # Copy to clipboard
        try:
            import ctypes
            # Open clipboard
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            # Copy text (CF_UNICODETEXT = 13)
            hMem = ctypes.windll.kernel32.GlobalAlloc(0x0042, len(text_with_space) * 2 + 2)
            pMem = ctypes.windll.kernel32.GlobalLock(hMem)
            ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pMem), text_with_space)
            ctypes.windll.kernel32.GlobalUnlock(hMem)
            ctypes.windll.user32.SetClipboardData(13, hMem)
            ctypes.windll.user32.CloseClipboard()
        except Exception as e:
            print(f">> Clipboard error: {e}", flush=True)

        # Auto-paste if enabled
        if app_config.get("auto_paste", True):
            print(f">> Pasting: {text}", flush=True)
            time.sleep(0.1)
            keyboard_controller.press(Key.ctrl)
            keyboard_controller.press('v')
            keyboard_controller.release('v')
            keyboard_controller.release(Key.ctrl)
        else:
            print(f">> Copied to clipboard: {text}", flush=True)
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

    if check_hotkey():
        if is_recording:
            # In auto_stop mode, pressing hotkey again stops recording (toggle)
            if app_config.get("recording_mode") == "auto_stop":
                threading.Thread(target=stop_recording, daemon=True).start()
        else:
            start_recording()


def on_release(key):
    global current_keys
    current_keys.discard(key)

    # Only stop on release in push_to_talk mode
    if is_recording and app_config.get("recording_mode") == "push_to_talk":
        threading.Thread(target=stop_recording, daemon=True).start()


# System tray
def get_icon_path():
    return get_resource_path("icon.ico")


def on_quit(icon, item):
    print("\nExiting...", flush=True)
    icon.stop()
    os._exit(0)


def on_settings(icon, item=None):
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
    menu = pystray.Menu(
        pystray.MenuItem("MurmurTone", None, enabled=False),
        pystray.MenuItem(get_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Settings", on_settings, default=True),
        pystray.MenuItem("Exit", on_quit)
    )

    icon = pystray.Icon("murmurtone", icon_ready, "MurmurTone - Loading...", menu)
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

    # Initialize audio feedback sounds
    init_sounds()

    # Initialize status icons
    init_icons()

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
