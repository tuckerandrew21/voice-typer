"""
File transcription module for MurmurTone.
Handles loading and transcribing audio/video files.
"""
import os
import numpy as np
from typing import Callable, Optional, Tuple


# Supported audio/video formats
SUPPORTED_FORMATS = [
    ".mp3", ".wav", ".m4a", ".mp4", ".avi", ".mov", ".flac", ".ogg", ".opus", ".webm"
]


def is_supported_format(file_path: str) -> bool:
    """Check if file format is supported for transcription."""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_FORMATS


def get_file_duration(file_path: str) -> Optional[float]:
    """
    Get duration of audio file in seconds.
    Returns None if duration cannot be determined.

    Note: This uses ffmpeg via faster-whisper's built-in support.
    For now, returns None as duration is not critical for MVP.
    """
    # TODO: Could use ffprobe to get duration, but not essential for Phase 3
    return None


def transcribe_file(
    file_path: str,
    model,
    app_config: dict,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[str, bool]:
    """
    Transcribe audio file with progress updates.

    Args:
        file_path: Path to audio/video file
        model: faster-whisper model instance
        app_config: Application configuration dict
        progress_callback: Optional callback(progress: float, status: str)
                          progress is 0.0-1.0, status is human-readable text

    Returns:
        Tuple of (transcription_text, success)
    """
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            if progress_callback:
                progress_callback(0.0, "Error: File not found")
            return "", False

        # Validate format
        if not is_supported_format(file_path):
            if progress_callback:
                progress_callback(0.0, "Error: Unsupported file format")
            return "", False

        if progress_callback:
            progress_callback(0.0, "Loading audio file...")

        # Build transcription parameters (same as live dictation)
        if app_config.get("translation_enabled"):
            task = "translate"
            language = app_config.get("translation_source_language", "auto")
            if language == "auto":
                language = None
        else:
            task = "transcribe"
            language = app_config.get("language", "en")
            if language == "auto":
                language = None

        # Build initial_prompt with custom vocabulary
        base_prompt = app_config.get("initial_prompt", "")
        custom_vocab = app_config.get("custom_vocabulary", [])
        if custom_vocab:
            vocab_hint = f" Vocabulary: {', '.join(custom_vocab)}."
            initial_prompt = base_prompt + vocab_hint
        else:
            initial_prompt = base_prompt

        transcribe_params = {"task": task, "language": language}
        if initial_prompt:
            transcribe_params["initial_prompt"] = initial_prompt

        if progress_callback:
            progress_callback(0.1, "Transcribing...")

        # Transcribe file (faster-whisper accepts file path directly)
        segments, info = model.transcribe(file_path, **transcribe_params)

        # Collect segments into text
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text)
            if progress_callback:
                # Approximate progress (we don't have duration, so this is a guess)
                # Progress 0.1-0.9 during transcription
                progress_callback(0.5, "Transcribing...")

        transcription = " ".join(text_parts).strip()

        if progress_callback:
            progress_callback(0.9, "Processing...")

        # Apply text processing (same as live dictation)
        from text_processor import process_text

        # Voice commands
        if app_config.get("voice_commands_enabled", True):
            transcription = process_text(transcription)

        # Filler removal
        if app_config.get("filler_removal_enabled", True):
            from text_processor import remove_filler_words
            aggressive = app_config.get("filler_removal_aggressive", False)
            custom_fillers = app_config.get("custom_fillers", [])
            transcription = remove_filler_words(transcription, aggressive, custom_fillers)

        # Custom dictionary (text replacement)
        custom_dict = app_config.get("custom_dictionary", [])
        if custom_dict:
            for entry in custom_dict:
                from_text = entry.get("from", "")
                to_text = entry.get("to", "")
                case_sensitive = entry.get("case_sensitive", False)
                if from_text and to_text:
                    if case_sensitive:
                        transcription = transcription.replace(from_text, to_text)
                    else:
                        # Case-insensitive replacement
                        import re
                        pattern = re.compile(re.escape(from_text), re.IGNORECASE)
                        transcription = pattern.sub(to_text, transcription)

        if progress_callback:
            progress_callback(1.0, "Complete!")

        return transcription, True

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if progress_callback:
            progress_callback(0.0, error_msg)
        return "", False


def save_transcription(
    text: str,
    original_file_path: str,
    save_location: Optional[str] = None
) -> Optional[str]:
    """
    Save transcription to text file.

    Args:
        text: Transcription text to save
        original_file_path: Path to original audio file (used for naming)
        save_location: Optional directory to save to (uses dialog if None)

    Returns:
        Path to saved file, or None if save failed/cancelled
    """
    try:
        # Generate default filename based on original file
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        default_filename = f"{base_name}_transcription.txt"

        if save_location:
            save_path = os.path.join(save_location, default_filename)
        else:
            # Use file dialog
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()  # Hide root window

            save_path = filedialog.asksaveasfilename(
                title="Save Transcription",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialfile=default_filename
            )

            root.destroy()

            if not save_path:
                return None  # User cancelled

        # Write transcription to file
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)

        return save_path

    except Exception:
        return None
