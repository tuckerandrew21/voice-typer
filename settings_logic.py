"""
Settings business logic - extracted from GUI for testability.

This module contains all configuration validation, detection logic,
and data transformation that can be tested independently of the UI.
"""

import config


# =============================================================================
# GPU/CUDA Detection
# =============================================================================

# Set to True to test the "GPU not available" UI state
_TEST_GPU_UNAVAILABLE = False


def check_cuda_available():
    """Check if CUDA is available for GPU acceleration.

    Returns:
        bool: True if CUDA is available, False otherwise.
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        # torch not installed, try ctranslate2 directly
        try:
            import ctranslate2
            cuda_types = ctranslate2.get_supported_compute_types("cuda")
            return len(cuda_types) > 0
        except (ImportError, Exception):
            return False


def get_cuda_status():
    """Get detailed CUDA status info.

    Returns:
        tuple: (is_available, status_message, gpu_name_or_reason)
            - is_available (bool): Whether CUDA is usable
            - status_message (str): Human-readable status
            - gpu_name_or_reason (str|None): GPU name if available, reason if not
    """
    # Test mode: simulate GPU unavailable
    if _TEST_GPU_UNAVAILABLE:
        return (False, "GPU libraries not installed", None)

    # Check if ctranslate2 supports CUDA compute types
    cuda_supported = False
    try:
        import ctranslate2
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
            return (True, "CUDA Available", "via ctranslate2")
    except ImportError:
        # No torch, but ctranslate2 says CUDA works
        return (True, "CUDA Available", "via ctranslate2")


# =============================================================================
# Configuration Validation
# =============================================================================

def validate_sample_rate(value, default=16000):
    """Validate and convert sample rate to integer.

    Args:
        value: Input value (string or int)
        default: Default value if invalid

    Returns:
        int: Valid sample rate
    """
    try:
        rate = int(value)
        # Only allow standard sample rates
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if rate in valid_rates:
            return rate
        return default
    except (ValueError, TypeError):
        return default


def validate_silence_duration(value, default=2.0, min_val=0.5, max_val=10.0):
    """Validate and clamp silence duration.

    Args:
        value: Input value
        default: Default value if invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        float: Valid silence duration
    """
    try:
        duration = float(value)
        return max(min_val, min(max_val, duration))
    except (ValueError, TypeError):
        return default


def validate_preview_delay(value, default=2.0, min_val=0.0, max_val=10.0):
    """Validate and clamp preview delay.

    Args:
        value: Input value
        default: Default value if invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        float: Valid preview delay
    """
    try:
        delay = float(value)
        return max(min_val, min(max_val, delay))
    except (ValueError, TypeError):
        return default


def validate_volume(value, default=100, min_val=0, max_val=100):
    """Validate and clamp volume percentage.

    Args:
        value: Input value
        default: Default value if invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        int: Valid volume percentage
    """
    try:
        vol = int(value)
        return max(min_val, min(max_val, vol))
    except (ValueError, TypeError):
        return default


def validate_noise_threshold(value, default=-40, min_val=-60, max_val=-20):
    """Validate and clamp noise threshold in dB.

    Args:
        value: Input value
        default: Default value if invalid
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        int: Valid noise threshold in dB
    """
    try:
        threshold = int(value)
        return max(min_val, min(max_val, threshold))
    except (ValueError, TypeError):
        return default


# =============================================================================
# Language Code/Label Conversion
# =============================================================================

def language_code_to_label(code):
    """Convert language code to display label.

    Args:
        code: ISO language code (e.g., "en", "es")

    Returns:
        str: Human-readable label or the code if not found
    """
    return config.LANGUAGE_LABELS.get(code, code)


def language_label_to_code(label):
    """Convert display label back to language code.

    Args:
        label: Human-readable label (e.g., "English", "Spanish")

    Returns:
        str: ISO language code or the label if not found
    """
    for code, lbl in config.LANGUAGE_LABELS.items():
        if lbl == label:
            return code
    return label


def get_language_labels():
    """Get list of all language labels for dropdown.

    Returns:
        list: List of human-readable language labels
    """
    return list(config.LANGUAGE_LABELS.values())


# =============================================================================
# Audio Device Detection
# =============================================================================

def get_input_devices():
    """Get list of available audio input devices.

    Returns:
        list: List of (display_name, device_info) tuples
              device_info is None for System Default
    """
    return config.get_input_devices()


def find_device_by_name(devices_list, device_name):
    """Find a device in the list by its name.

    Args:
        devices_list: List of (display_name, device_info) tuples
        device_name: Name of the device to find

    Returns:
        tuple: (display_name, device_info) or (None, None) if not found
    """
    for display_name, device_info in devices_list:
        if device_info and device_info.get("name") == device_name:
            return display_name, device_info
    return None, None


def get_device_display_name(saved_device, devices_list):
    """Get the display name for a saved device configuration.

    Args:
        saved_device: Saved device config (dict or string)
        devices_list: Current list of available devices

    Returns:
        str: Display name to show in dropdown
    """
    if saved_device is None:
        # System Default
        return devices_list[0][0] if devices_list else "System Default"

    saved_name = saved_device.get("name") if isinstance(saved_device, dict) else saved_device

    for display_name, device_info in devices_list:
        if device_info and device_info.get("name") == saved_name:
            return display_name

    # Device not found - mark as unavailable
    if saved_name:
        return f"{saved_name} (unavailable)"
    return devices_list[0][0] if devices_list else "System Default"


# =============================================================================
# Processing Mode
# =============================================================================

def get_processing_mode_from_ui(gpu_enabled, compute_type):
    """Convert UI settings to processing mode config.

    Args:
        gpu_enabled: Whether GPU is enabled
        compute_type: Compute type string (e.g., "int8", "float16")

    Returns:
        str: Processing mode ("cpu", "gpu_int8", "gpu_float16")
    """
    if not gpu_enabled:
        return "cpu"
    return f"gpu_{compute_type}"


def get_ui_from_processing_mode(processing_mode):
    """Convert processing mode config to UI settings.

    Args:
        processing_mode: Processing mode ("cpu", "gpu_int8", "gpu_float16")

    Returns:
        tuple: (gpu_enabled, compute_type)
    """
    if processing_mode == "cpu":
        return False, "int8"
    if processing_mode.startswith("gpu_"):
        compute_type = processing_mode[4:]  # Remove "gpu_" prefix
        return True, compute_type
    # Default fallback
    return False, "int8"


# =============================================================================
# Audio Level Meter Helpers
# =============================================================================

def db_to_linear(db, min_db=-60, max_db=-20):
    """Convert dB value to linear position (0.0 to 1.0).

    Args:
        db: Value in decibels
        min_db: Minimum dB value (maps to 0.0)
        max_db: Maximum dB value (maps to 1.0)

    Returns:
        float: Linear position from 0.0 to 1.0
    """
    return (db - min_db) / (max_db - min_db)


def linear_to_db(linear, min_db=-60, max_db=-20):
    """Convert linear position (0.0 to 1.0) to dB value.

    Args:
        linear: Linear position from 0.0 to 1.0
        min_db: Minimum dB value
        max_db: Maximum dB value

    Returns:
        int: Value in decibels (clamped and rounded)
    """
    db = min_db + linear * (max_db - min_db)
    return int(max(min_db, min(max_db, db)))


def rms_to_db(rms, ref=1.0, min_db=-60):
    """Convert RMS level to decibels.

    Args:
        rms: RMS value
        ref: Reference level (1.0 for normalized audio)
        min_db: Floor value to prevent -inf

    Returns:
        float: Level in decibels
    """
    import math
    if rms <= 0:
        return min_db
    db = 20 * math.log10(rms / ref)
    return max(min_db, db)


# =============================================================================
# Settings Data Model
# =============================================================================

def build_settings_dict(
    model_size,
    language,
    translation_enabled,
    translation_source_language,
    sample_rate,
    hotkey,
    recording_mode,
    silence_duration,
    audio_feedback,
    input_device,
    auto_paste,
    paste_mode,
    start_with_windows,
    processing_mode,
    noise_gate_enabled,
    noise_gate_threshold_db,
    audio_feedback_volume,
    sound_processing,
    sound_success,
    sound_error,
    sound_command,
    voice_commands_enabled,
    scratch_that_enabled,
    filler_removal_enabled,
    filler_removal_aggressive,
    custom_fillers,
    custom_dictionary,
    custom_vocabulary,
    custom_commands,
    ai_cleanup_enabled,
    ai_cleanup_mode,
    ai_formality_level,
    ollama_model,
    ollama_url,
    preview_enabled,
    preview_position,
    preview_auto_hide_delay,
    preview_theme,
    preview_font_size,
):
    """Build a complete settings dictionary from individual values.

    This creates the canonical settings dict that gets saved to config.

    Returns:
        dict: Complete settings dictionary
    """
    return {
        "model_size": model_size,
        "language": language,
        "translation_enabled": translation_enabled,
        "translation_source_language": translation_source_language,
        "sample_rate": sample_rate,
        "hotkey": hotkey,
        "recording_mode": recording_mode,
        "silence_duration_sec": silence_duration,
        "audio_feedback": audio_feedback,
        "input_device": input_device,
        "auto_paste": auto_paste,
        "paste_mode": paste_mode,
        "start_with_windows": start_with_windows,
        "processing_mode": processing_mode,
        "noise_gate_enabled": noise_gate_enabled,
        "noise_gate_threshold_db": noise_gate_threshold_db,
        "audio_feedback_volume": audio_feedback_volume,
        "sound_processing": sound_processing,
        "sound_success": sound_success,
        "sound_error": sound_error,
        "sound_command": sound_command,
        "voice_commands_enabled": voice_commands_enabled,
        "scratch_that_enabled": scratch_that_enabled,
        "filler_removal_enabled": filler_removal_enabled,
        "filler_removal_aggressive": filler_removal_aggressive,
        "custom_fillers": custom_fillers,
        "custom_dictionary": custom_dictionary,
        "custom_vocabulary": custom_vocabulary,
        "custom_commands": custom_commands,
        "ai_cleanup_enabled": ai_cleanup_enabled,
        "ai_cleanup_mode": ai_cleanup_mode,
        "ai_formality_level": ai_formality_level,
        "ollama_model": ollama_model,
        "ollama_url": ollama_url,
        "preview_enabled": preview_enabled,
        "preview_position": preview_position,
        "preview_auto_hide_delay": preview_auto_hide_delay,
        "preview_theme": preview_theme,
        "preview_font_size": preview_font_size,
    }


# =============================================================================
# Defaults
# =============================================================================

def get_defaults():
    """Get default settings from config.

    Returns:
        dict: Default settings dictionary
    """
    return config.DEFAULTS.copy()
