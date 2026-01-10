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
import array
import winsound
import argparse
import numpy as np
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Controller, Key
from PIL import Image, ImageDraw
import pystray
import config
import text_processor
import stats
import preview_window
import clipboard_utils
from logger import log


def setup_nvidia_dll_path():
    """Preload NVIDIA CUDA DLLs on Windows.

    This is required because pip-installed nvidia-cublas-cu12 and nvidia-cudnn-cu12
    place DLLs in site-packages, which isn't in the system DLL search path.

    We preload the DLLs using ctypes before importing ctranslate2/faster_whisper
    so they're already in memory when needed.
    """
    if sys.platform != "win32":
        return

    import ctypes

    # Find the site-packages directory
    site_packages = None
    for path in sys.path:
        if "site-packages" in path and os.path.exists(path):
            site_packages = path
            break

    if not site_packages:
        return

    # NVIDIA DLLs to preload (order matters for dependencies)
    dlls_to_load = [
        ("nvidia", "cublas", "bin", "cublas64_12.dll"),
        ("nvidia", "cublas", "bin", "cublasLt64_12.dll"),
        ("nvidia", "cudnn", "bin", "cudnn64_9.dll"),
    ]

    for parts in dlls_to_load:
        dll_path = os.path.join(site_packages, *parts)
        if os.path.exists(dll_path):
            try:
                ctypes.WinDLL(dll_path)
            except OSError:
                pass  # DLL may already be loaded or have missing dependencies


# Set up NVIDIA DLL paths before importing faster-whisper
setup_nvidia_dll_path()

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
last_tray_click_time = 0  # For double-click detection
tray_icon = None
key_listener = None
transcription_history = text_processor.TranscriptionHistory()

# Audio feedback sounds
start_sound = None
stop_sound = None
processing_sound = None
success_sound = None
error_sound = None
command_sound = None

# Silence detection state
silence_start_time = None

# Recording duration tracking
recording_start_time = None
last_duration_update = 0

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


def generate_two_tone_sound(freq1=400, freq2=600, duration_ms=100, volume=0.3):
    """Generate a two-tone ascending sound as WAV bytes."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)
    half_samples = num_samples // 2

    t1 = np.linspace(0, duration_ms / 2000, half_samples, dtype=np.float32)
    t2 = np.linspace(0, duration_ms / 2000, num_samples - half_samples, dtype=np.float32)

    # First tone then second tone
    wave1 = np.sin(2 * np.pi * freq1 * t1) * volume
    wave2 = np.sin(2 * np.pi * freq2 * t2) * volume
    wave_data = np.concatenate([wave1, wave2])

    # Apply fade envelope
    fade_samples = int(num_samples * 0.1)
    if fade_samples > 0:
        wave_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Convert to 16-bit PCM
    pcm_data = (wave_data * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return buffer.getvalue()


def generate_chime_sound(frequency=800, duration_ms=150, volume=0.3):
    """Generate a pleasant chime sound with harmonics as WAV bytes."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)

    t = np.linspace(0, duration_ms / 1000, num_samples, dtype=np.float32)
    # Main frequency plus harmonics for richer sound
    wave_data = (np.sin(2 * np.pi * frequency * t) * 0.6 +
                 np.sin(2 * np.pi * frequency * 2 * t) * 0.25 +
                 np.sin(2 * np.pi * frequency * 3 * t) * 0.15) * volume

    # Apply longer fade for chime effect
    fade_in = int(num_samples * 0.05)
    fade_out = int(num_samples * 0.4)
    if fade_in > 0:
        wave_data[:fade_in] *= np.linspace(0, 1, fade_in)
    if fade_out > 0:
        wave_data[-fade_out:] *= np.linspace(1, 0, fade_out)

    pcm_data = (wave_data * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return buffer.getvalue()


def generate_double_beep_sound(frequency=900, duration_ms=40, gap_ms=30, volume=0.3):
    """Generate a quick double-beep sound for command confirmation."""
    sample_rate = 44100
    beep_samples = int(sample_rate * duration_ms / 1000)
    gap_samples = int(sample_rate * gap_ms / 1000)

    t = np.linspace(0, duration_ms / 1000, beep_samples, dtype=np.float32)
    beep = np.sin(2 * np.pi * frequency * t) * volume

    # Quick fade to avoid clicks
    fade = int(beep_samples * 0.15)
    if fade > 0:
        beep[:fade] *= np.linspace(0, 1, fade)
        beep[-fade:] *= np.linspace(1, 0, fade)

    # Two beeps with gap
    gap = np.zeros(gap_samples, dtype=np.float32)
    wave_data = np.concatenate([beep, gap, beep])

    pcm_data = (wave_data * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return buffer.getvalue()


def generate_error_buzz_sound(freq_start=400, freq_end=200, duration_ms=120, volume=0.3):
    """Generate a descending buzz sound for errors (clearly 'bad')."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)

    t = np.linspace(0, duration_ms / 1000, num_samples, dtype=np.float32)
    # Descending frequency sweep
    freq = np.linspace(freq_start, freq_end, num_samples)
    wave_data = np.sin(2 * np.pi * freq * t) * volume

    # Add slight buzz with second harmonic
    wave_data += np.sin(2 * np.pi * freq * 2 * t) * volume * 0.2

    # Fade envelope
    fade = int(num_samples * 0.1)
    if fade > 0:
        wave_data[:fade] *= np.linspace(0, 1, fade)
        wave_data[-fade:] *= np.linspace(1, 0, fade)

    pcm_data = (wave_data * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data.tobytes())

    return buffer.getvalue()


def apply_volume_to_wav(wav_data, volume):
    """Apply volume scaling to WAV bytes.

    Args:
        wav_data: WAV file as bytes
        volume: Volume multiplier (0.0 to 1.0)

    Returns:
        New WAV bytes with volume applied
    """
    if wav_data is None or volume == 1.0:
        return wav_data

    # Read the WAV data
    wav_buffer = io.BytesIO(wav_data)
    with wave.open(wav_buffer, 'rb') as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)

    # Scale the samples (assuming 16-bit audio)
    samples = array.array('h', frames)
    for i in range(len(samples)):
        samples[i] = int(samples[i] * volume)

    # Write back to WAV
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(samples.tobytes())

    return output.getvalue()


def init_sounds():
    """Initialize audio feedback sounds at full volume (volume applied at playback)."""
    global start_sound, stop_sound, processing_sound, success_sound, error_sound, command_sound
    try:
        # Generate reference sounds at full volume - volume is applied at playback time
        # Each sound is designed to be distinct:
        # - start: high pitch click (1200Hz) - "listening"
        # - stop: lower pitch click (500Hz) - "got it"
        # - processing: ascending two-tone - "thinking"
        # - success: pleasant chime - "done"
        # - error: descending buzz - "problem"
        # - command: quick double-beep - "action triggered"
        start_sound = generate_click_sound(frequency=1200, duration_ms=40, volume=1.0)
        stop_sound = generate_click_sound(frequency=500, duration_ms=60, volume=1.0)
        processing_sound = generate_two_tone_sound(freq1=400, freq2=600, duration_ms=100, volume=1.0)
        success_sound = generate_chime_sound(frequency=800, duration_ms=150, volume=1.0)
        error_sound = generate_error_buzz_sound(freq_start=400, freq_end=200, duration_ms=120, volume=1.0)
        command_sound = generate_double_beep_sound(frequency=900, duration_ms=40, gap_ms=30, volume=1.0)
    except Exception as e:
        log.warning(f"Could not initialize sounds: {e}")
        start_sound = stop_sound = processing_sound = success_sound = error_sound = command_sound = None


def play_sound(sound_data, sound_type=None):
    """Play a sound asynchronously (non-blocking).

    Args:
        sound_data: WAV bytes to play
        sound_type: Optional type ('processing', 'success', 'error') to check specific setting
    """
    if not app_config.get("audio_feedback", True):
        return

    # Check specific sound type setting if provided
    if sound_type:
        setting_key = f"sound_{sound_type}"
        if not app_config.get(setting_key, True):
            return

    if sound_data:
        # Read current volume from config file (hot reload)
        current_volume = config.load_config().get("audio_feedback_volume", 0.3)
        scaled_sound = apply_volume_to_wav(sound_data, current_volume)

        threading.Thread(
            target=lambda: winsound.PlaySound(scaled_sound, winsound.SND_MEMORY),
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


def get_device_and_compute_type():
    """Determine device and compute type based on processing_mode config."""
    processing_mode = app_config.get("processing_mode", "auto")
    mode_config = config.PROCESSING_MODE_MAP.get(processing_mode, config.PROCESSING_MODE_MAP["auto"])

    device_setting = mode_config["device"]
    compute_type_setting = mode_config["compute_type"]

    cuda_available = check_cuda_available()

    # Determine actual device
    if device_setting == "auto":
        device = "cuda" if cuda_available else "cpu"
    elif device_setting == "cuda":
        if cuda_available:
            device = "cuda"
        else:
            log.warning("GPU mode requested but CUDA not available. Falling back to CPU.")
            device = "cpu"
    else:
        device = "cpu"

    # Determine compute type (CPU only supports int8)
    if device == "cpu":
        compute_type = "int8"
    else:
        compute_type = compute_type_setting

    return device, compute_type


def load_model(model_size=None):
    """Load or reload the Whisper model."""
    global model, model_ready, model_loading

    if model_size is None:
        model_size = app_config["model_size"]

    model_ready = False
    model_loading = True

    if tray_icon:
        tray_icon.title = f"MurmurTone - Loading {model_size}..."

    log.info(f"Loading Whisper model ({model_size})...")
    from faster_whisper import WhisperModel

    # Determine device and compute type
    device, compute_type = get_device_and_compute_type()
    log.info(f"Using device: {device}, compute type: {compute_type}")

    # Use bundled model if available, otherwise download from HuggingFace
    model_path = get_model_path(model_size)
    model = WhisperModel(model_path, device=device, compute_type=compute_type)
    model_ready = True
    model_loading = False
    log.info("Model loaded! Ready.")

    if tray_icon:
        hotkey_str = config.hotkey_to_string(app_config["hotkey"])
        action = "Press" if app_config.get("recording_mode") == "auto_stop" else "Hold"
        tray_icon.title = f"MurmurTone - Ready\n{action} {hotkey_str} to record"


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

    log.info("Auto-stopped (silence detected)")
    silence_start_time = None
    stop_recording()


def audio_callback(indata, frames, time_info, status):
    global audio_data, is_recording, silence_start_time, last_duration_update

    if not is_recording:
        return

    # Calculate current audio level
    rms = calculate_rms(indata)
    db = rms_to_db(rms)

    # Get noise gate settings
    noise_gate_enabled = app_config.get("noise_gate_enabled", True)
    threshold_db = app_config.get("noise_gate_threshold_db", -40)

    # Apply noise gate - skip frames below threshold
    if noise_gate_enabled and db < threshold_db:
        # Don't record this frame - it's below the noise gate
        pass
    else:
        # Record this frame
        audio_data.append(indata.copy())

    # Update preview window with duration once per second
    if recording_start_time is not None and app_config.get("preview_enabled", True):
        elapsed = time.time() - recording_start_time
        elapsed_int = int(elapsed)
        if elapsed_int > last_duration_update:
            last_duration_update = elapsed_int
            preview_window.show_recording(duration_seconds=elapsed)

    # Only check silence-based auto_stop in auto_stop mode
    if app_config.get("recording_mode") != "auto_stop":
        return

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
    global is_recording, audio_data, stream, silence_start_time, recording_start_time, last_duration_update
    if not model_ready:
        log.info("Model still loading, please wait...")
        return
    if is_recording:
        return

    play_sound(start_sound)
    update_tray_icon(recording=True)

    # Track recording start time for duration display
    recording_start_time = time.time()
    last_duration_update = 0

    # Show preview window if enabled
    if app_config.get("preview_enabled", True):
        preview_window.show_recording(duration_seconds=0)

    log.info("Recording...")
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
        log.debug("No audio captured")
        if app_config.get("preview_enabled", True):
            preview_window.hide()
        return

    log.info("Transcribing...")
    play_sound(processing_sound, sound_type="processing")
    if app_config.get("preview_enabled", True):
        preview_window.show_transcribing()
    audio = np.concatenate(audio_data, axis=0).flatten()

    language = app_config.get("language", "en")
    if language == "auto":
        language = None

    # Get initial_prompt for punctuation optimization
    initial_prompt = app_config.get("initial_prompt", "")

    # Transcribe with optional initial_prompt
    transcribe_params = {"language": language}
    if initial_prompt:
        transcribe_params["initial_prompt"] = initial_prompt

    segments, _ = model.transcribe(audio, **transcribe_params)
    raw_text = "".join(segment.text for segment in segments).strip()

    # Process text through the pipeline (dictionary, fillers, commands)
    text, should_scratch, scratch_length, actions = text_processor.process_text(
        raw_text, app_config, transcription_history
    )

    # Execute any action commands (select all, undo, redo)
    actions_executed = False
    for action in actions:
        if action.startswith("ctrl+"):
            key = action.split("+")[1]
            keyboard_controller.press(Key.ctrl)
            keyboard_controller.press(key)
            keyboard_controller.release(key)
            keyboard_controller.release(Key.ctrl)
            time.sleep(0.05)
            actions_executed = True

    # Handle "scratch that" - delete previous transcription
    if should_scratch and scratch_length > 0:
        log.info(f"Scratching last {scratch_length} characters")
        if app_config.get("preview_enabled", True):
            preview_window.hide()
        time.sleep(0.1)
        for _ in range(scratch_length):
            keyboard_controller.press(Key.backspace)
            keyboard_controller.release(Key.backspace)
        # Don't output anything else for this transcription
        hotkey_str = config.hotkey_to_string(app_config["hotkey"])
        log.info(f"Ready. Press {hotkey_str}.")
        return

    if text:
        # Track this transcription for potential "scratch that"
        text_with_space = text + " "
        transcription_history.add(text_with_space)

        # Record usage statistics
        stats.record_transcription(text)

        # Show transcribed text in preview (will auto-hide)
        if app_config.get("preview_enabled", True):
            preview_window.show_text(text, auto_hide=True)

        # Output text using configured paste mode
        paste_mode = app_config.get("paste_mode", "clipboard")

        if paste_mode == "direct":
            # Direct typing mode - never touches clipboard
            # Types character-by-character with delay for visual typewriter effect
            log.info(f"Typing directly: {text}")
            time.sleep(0.2)  # Brief pause before typing
            typing_delay = app_config.get("direct_typing_delay_ms", 5) / 1000.0
            for char in text_with_space:
                keyboard_controller.type(char)
                if typing_delay > 0:
                    time.sleep(typing_delay)
        elif app_config.get("auto_paste", True):
            # Clipboard mode with auto-paste
            # Save current clipboard contents first
            saved_clipboard = clipboard_utils.save_clipboard()

            # Copy to clipboard using tkinter (more reliable than ctypes)
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text_with_space)
                root.update()
                root.destroy()
            except Exception as e:
                log.error(f"Clipboard error: {e}")

            # Paste
            log.info(f"Pasting: {text}")
            time.sleep(0.3)  # Wait for focus to return after clipboard
            keyboard_controller.press(Key.ctrl_l)
            time.sleep(0.05)
            keyboard_controller.press('v')
            keyboard_controller.release('v')
            time.sleep(0.05)
            keyboard_controller.release(Key.ctrl_l)

            # Restore clipboard contents asynchronously
            if saved_clipboard:
                clipboard_utils.restore_clipboard_async(saved_clipboard, delay_ms=400)
        else:
            # Clipboard mode without auto-paste (manual paste by user)
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                root.clipboard_clear()
                root.clipboard_append(text_with_space)
                root.update()
                root.destroy()
                log.info(f"Copied to clipboard: {text}")
            except Exception as e:
                log.error(f"Clipboard error: {e}")
        # Success sound after text output
        play_sound(success_sound, sound_type="success")
    elif actions_executed:
        log.info(f"Action executed: {', '.join(actions)}")
        play_sound(command_sound, sound_type="command")
        if app_config.get("preview_enabled", True):
            preview_window.hide()
    else:
        log.info("No speech detected")
        play_sound(error_sound, sound_type="error")
        if app_config.get("preview_enabled", True):
            preview_window.hide()

    hotkey_str = config.hotkey_to_string(app_config["hotkey"])
    log.info(f"Ready. Press {hotkey_str}.")


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
    log.info("Exiting...")
    icon.stop()
    os._exit(0)


def on_settings(icon, item=None):
    """Open settings window in a separate thread."""
    threading.Thread(target=open_settings_window, daemon=True).start()


def on_history(icon, item=None):
    """Open history viewer in a separate thread."""
    def show_history():
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title("Transcription History")
        root.geometry("500x400")

        # Load history from disk
        entries = text_processor.TranscriptionHistory.load_from_disk()

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Recent Transcriptions", font=("", 11, "bold")).pack(anchor=tk.W)

        # Listbox with scrollbar
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox (newest first)
        for entry in reversed(entries):
            timestamp = entry.get("timestamp", "")[:16]  # Trim to YYYY-MM-DD HH:MM
            text = entry.get("text", "").strip()[:50]  # First 50 chars
            if len(entry.get("text", "")) > 50:
                text += "..."
            listbox.insert(tk.END, f"[{timestamp}] {text}")

        # Store full entries for copy
        full_entries = list(reversed(entries))

        def copy_selected():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                full_text = full_entries[idx].get("text", "")
                root.clipboard_clear()
                root.clipboard_append(full_text)
                root.update()

        def clear_history():
            if tk.messagebox.askyesno("Clear History", "Delete all transcription history?"):
                text_processor.TranscriptionHistory.clear_on_disk()
                listbox.delete(0, tk.END)
                full_entries.clear()

        def export_history():
            """Export history to file with format selection."""
            if not entries:
                tk.messagebox.showinfo("Export History", "No history to export.")
                return

            # Format selection dialog
            dialog = tk.Toplevel(root)
            dialog.title("Export Format")
            dialog.geometry("300x180")
            dialog.transient(root)
            dialog.grab_set()

            ttk.Label(dialog, text="Select export format:", font=("", 10, "bold")).pack(pady=10)

            format_var = tk.StringVar(value="txt")
            ttk.Radiobutton(dialog, text="Plain Text (.txt)", variable=format_var, value="txt").pack(anchor=tk.W, padx=20)
            ttk.Radiobutton(dialog, text="CSV with timestamps (.csv)", variable=format_var, value="csv").pack(anchor=tk.W, padx=20)
            ttk.Radiobutton(dialog, text="JSON with metadata (.json)", variable=format_var, value="json").pack(anchor=tk.W, padx=20)

            result = {"cancelled": True}

            def on_export():
                result["cancelled"] = False
                result["format"] = format_var.get()
                dialog.destroy()

            btn_dialog_frame = ttk.Frame(dialog)
            btn_dialog_frame.pack(pady=15)
            ttk.Button(btn_dialog_frame, text="Export", command=on_export).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_dialog_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            dialog.wait_window()

            if result["cancelled"]:
                return

            # File save dialog
            from tkinter import filedialog
            format_ext = result["format"]
            ext_map = {"txt": ".txt", "csv": ".csv", "json": ".json"}
            file_types = {
                "txt": [("Text files", "*.txt"), ("All files", "*.*")],
                "csv": [("CSV files", "*.csv"), ("All files", "*.*")],
                "json": [("JSON files", "*.json"), ("All files", "*.*")]
            }

            filename = filedialog.asksaveasfilename(
                defaultextension=ext_map[format_ext],
                filetypes=file_types[format_ext],
                title="Export History"
            )

            if not filename:
                return

            try:
                if format_ext == "txt":
                    export_txt(filename, entries)
                elif format_ext == "csv":
                    export_csv(filename, entries)
                elif format_ext == "json":
                    export_json(filename, entries)
                tk.messagebox.showinfo("Export Successful", f"History exported to:\n{filename}")
            except Exception as e:
                tk.messagebox.showerror("Export Failed", f"Failed to export history:\n{str(e)}")

        def export_txt(filename, entries):
            """Export history as plain text with timestamps."""
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Transcription History\n")
                f.write("=" * 60 + "\n\n")
                for entry in entries:
                    timestamp = entry.get("timestamp", "")
                    text = entry.get("text", "")
                    f.write(f"[{timestamp}]\n{text}\n\n")

        def export_csv(filename, entries):
            """Export history as CSV with timestamp, text, and character count."""
            import csv
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Text", "Characters"])
                for entry in entries:
                    timestamp = entry.get("timestamp", "")
                    text = entry.get("text", "")
                    char_count = entry.get("char_count", len(text))
                    writer.writerow([timestamp, text, char_count])

        def export_json(filename, entries):
            """Export history as JSON with full metadata."""
            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"entries": entries}, f, indent=2, ensure_ascii=False)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Copy Selected", command=copy_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Export", command=export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear History", command=clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=root.destroy).pack(side=tk.RIGHT, padx=5)

        if not entries:
            listbox.insert(tk.END, "(No transcriptions yet)")

        root.mainloop()

    threading.Thread(target=show_history, daemon=True).start()


def on_stats(icon, item=None):
    """Open statistics viewer in a separate thread."""
    def show_stats():
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title("Usage Statistics")
        root.geometry("350x300")

        data = stats.load_stats()

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Your Voice Typing Stats", font=("", 12, "bold")).pack(anchor=tk.W, pady=(0, 15))

        # Stats grid
        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill=tk.X)

        minutes_saved, _ = stats.calculate_time_saved(data.get('total_characters', 0))
        labels = [
            ("Total Transcriptions:", f"{data.get('total_transcriptions', 0):,}"),
            ("Total Words:", f"{data.get('total_words', 0):,}"),
            ("Total Characters:", f"{data.get('total_characters', 0):,}"),
            ("Time Saved:", stats.format_time_saved(minutes_saved)),
        ]

        for i, (label, value) in enumerate(labels):
            ttk.Label(stats_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Label(stats_frame, text=value, font=("", 10, "bold")).grid(row=i, column=1, sticky=tk.E, pady=3, padx=(20, 0))

        # First use date
        first_use = data.get("first_use_date")
        if first_use:
            ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
            ttk.Label(frame, text=f"Using MurmurTone since: {first_use[:10]}").pack(anchor=tk.W)

        ttk.Button(frame, text="Close", command=root.destroy).pack(side=tk.BOTTOM, pady=10)

        root.mainloop()

    threading.Thread(target=show_stats, daemon=True).start()


def on_tray_click(icon, item=None):
    """Handle tray icon click - only open settings on double-click."""
    global last_tray_click_time
    current_time = time.time()

    if current_time - last_tray_click_time < 0.5:  # 500ms threshold
        on_settings(icon, item)
        last_tray_click_time = 0  # Reset to prevent triple-click
    else:
        last_tray_click_time = current_time


def open_settings_window():
    """Open the settings GUI as a separate process.

    pystray runs callbacks from background threads, but tkinter requires
    the main thread. Running settings as a subprocess gives it its own
    main thread, avoiding the 'main thread is not in main loop' error.
    """
    import subprocess
    app_dir = os.path.dirname(os.path.abspath(__file__))
    settings_script = os.path.join(app_dir, "settings_gui.py")
    subprocess.Popen([sys.executable, settings_script])


def on_settings_saved(new_config):
    """Called when settings are saved."""
    global app_config

    old_model = app_config.get("model_size")
    new_model = new_config.get("model_size")
    old_mode = app_config.get("processing_mode")
    new_mode = new_config.get("processing_mode")

    app_config = new_config

    # Reload model if model or processing mode changed
    model_changed = old_model != new_model
    mode_changed = old_mode != new_mode

    if model_changed or mode_changed:
        reason = []
        if model_changed:
            reason.append(f"model: {old_model} -> {new_model}")
        if mode_changed:
            reason.append(f"mode: {old_mode} -> {new_mode}")
        log.info(f"Reloading model ({', '.join(reason)})...")
        threading.Thread(target=load_model, args=(new_model,), daemon=True).start()

    # Update preview window configuration
    preview_window.configure(
        enabled=app_config.get("preview_enabled", True),
        position=app_config.get("preview_position", "bottom-right"),
        auto_hide_delay=app_config.get("preview_auto_hide_delay", 2.0),
        theme=app_config.get("preview_theme", "dark"),
        font_size=app_config.get("preview_font_size", 11)
    )

    hotkey_str = config.hotkey_to_string(app_config["hotkey"])
    log.info(f"Settings saved. Hotkey: {hotkey_str}")

    # Update tray tooltip with new hotkey
    if tray_icon and model_ready:
        action = "Press" if app_config.get("recording_mode") == "auto_stop" else "Hold"
        tray_icon.title = f"MurmurTone - Ready\n{action} {hotkey_str} to record"


def get_status_text(item):
    if model_loading:
        return f"Status: Loading {app_config['model_size']}..."
    if model_ready:
        return "Status: Ready"
    return "Status: Initializing..."


def create_tray_icon():
    menu = pystray.Menu(
        pystray.MenuItem("Open", on_tray_click, default=True, visible=False),
        pystray.MenuItem("MurmurTone", None, enabled=False),
        pystray.MenuItem(get_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("History", on_history),
        pystray.MenuItem("Statistics", on_stats),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Settings", on_settings),
        pystray.MenuItem("Exit", on_quit)
    )

    icon = pystray.Icon("murmurtone", icon_ready, "MurmurTone - Loading...", menu)
    return icon


def run_keyboard_listener():
    global key_listener
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        key_listener = listener
        listener.join()


def check_restart_signal():
    """Check for restart signal from settings and exit if found."""
    import time
    app_dir = os.path.dirname(os.path.abspath(__file__))
    signal_file = os.path.join(app_dir, ".restart_signal")

    while True:
        time.sleep(1)  # Check every second
        if os.path.exists(signal_file):
            try:
                os.remove(signal_file)
            except Exception:
                pass
            log.info("Restart signal received, exiting...")
            if tray_icon:
                tray_icon.stop()
            break


# Track config file modification time for hot-reload
_config_last_mtime = 0


def watch_config_file():
    """Watch config file for changes and hot-reload settings."""
    import time
    global _config_last_mtime

    config_path = config.get_config_path()

    # Initialize with current mtime
    try:
        _config_last_mtime = os.path.getmtime(config_path)
    except OSError:
        _config_last_mtime = 0

    while True:
        time.sleep(1)  # Check every second
        try:
            current_mtime = os.path.getmtime(config_path)
            if current_mtime > _config_last_mtime:
                _config_last_mtime = current_mtime
                log.info("Config file changed, reloading settings...")
                new_config = config.load_config()
                on_settings_saved(new_config)
        except OSError:
            pass  # File doesn't exist or not accessible


def main():
    global tray_icon, app_config

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MurmurTone - Voice to text")
    parser.add_argument("--settings", action="store_true", help="Open settings on startup")
    args = parser.parse_args()

    # Clean up any stale restart signal from previous runs
    app_dir = os.path.dirname(os.path.abspath(__file__))
    signal_file = os.path.join(app_dir, ".restart_signal")
    if os.path.exists(signal_file):
        try:
            os.remove(signal_file)
        except Exception:
            pass

    # Load configuration
    app_config = config.load_config()
    hotkey_str = config.hotkey_to_string(app_config["hotkey"])

    # Initialize audio feedback sounds
    init_sounds()

    # Initialize status icons
    init_icons()

    # Configure preview window
    preview_window.configure(
        enabled=app_config.get("preview_enabled", True),
        position=app_config.get("preview_position", "bottom-right"),
        auto_hide_delay=app_config.get("preview_auto_hide_delay", 2.0),
        theme=app_config.get("preview_theme", "dark"),
        font_size=app_config.get("preview_font_size", 11)
    )

    # Start keyboard listener
    listener_thread = threading.Thread(target=run_keyboard_listener, daemon=True)
    listener_thread.start()

    # Load model in background
    model_thread = threading.Thread(target=load_model, daemon=True)
    model_thread.start()

    # Start restart signal watcher
    restart_thread = threading.Thread(target=check_restart_signal, daemon=True)
    restart_thread.start()

    # Start config file watcher for hot-reload
    config_watcher_thread = threading.Thread(target=watch_config_file, daemon=True)
    config_watcher_thread.start()

    # Open settings on startup if requested
    if args.settings:
        threading.Thread(target=open_settings_window, daemon=True).start()

    # Create and run tray icon (blocks)
    tray_icon = create_tray_icon()
    log.info("System tray icon started.")
    log.info(f"Press {hotkey_str} to record (after model loads).")
    tray_icon.run()


if __name__ == "__main__":
    main()
