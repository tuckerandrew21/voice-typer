"""Tests for murmurtone.py pure functions."""
import pytest
import numpy as np
import wave
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from murmurtone import (
    calculate_rms,
    rms_to_db,
    apply_volume_to_wav,
    generate_click_sound,
    generate_two_tone_sound,
    generate_chime_sound,
    generate_double_beep_sound,
    generate_error_buzz_sound,
    generate_status_icon,
)


class TestCalculateRms:
    """Tests for RMS calculation."""

    def test_empty_array_returns_zero(self):
        """Empty array should return 0."""
        result = calculate_rms(np.array([]))
        assert result == 0

    def test_silence_returns_zero(self):
        """Array of zeros should return 0."""
        result = calculate_rms(np.zeros(100))
        assert result == 0

    def test_constant_signal(self):
        """Constant signal should return that value."""
        result = calculate_rms(np.ones(100) * 0.5)
        assert abs(result - 0.5) < 0.001

    def test_sine_wave_rms(self):
        """Sine wave RMS should be amplitude / sqrt(2)."""
        amplitude = 1.0
        samples = np.sin(np.linspace(0, 4 * np.pi, 1000)) * amplitude
        result = calculate_rms(samples)
        expected = amplitude / np.sqrt(2)
        assert abs(result - expected) < 0.01


class TestRmsToDb:
    """Tests for RMS to dB conversion."""

    def test_zero_returns_minus_100(self):
        """Zero RMS should return -100 dB (effectively silent)."""
        result = rms_to_db(0)
        assert result == -100

    def test_negative_returns_minus_100(self):
        """Negative RMS should return -100 dB."""
        result = rms_to_db(-0.5)
        assert result == -100

    def test_unity_returns_zero_db(self):
        """RMS of 1.0 with reference 1.0 should be 0 dB."""
        result = rms_to_db(1.0, reference=1.0)
        assert abs(result) < 0.001

    def test_half_amplitude(self):
        """Half amplitude should be about -6 dB."""
        result = rms_to_db(0.5, reference=1.0)
        assert abs(result - (-6.02)) < 0.1

    def test_double_amplitude(self):
        """Double amplitude should be about +6 dB."""
        result = rms_to_db(2.0, reference=1.0)
        assert abs(result - 6.02) < 0.1


class TestApplyVolumeToWav:
    """Tests for WAV volume scaling."""

    def _create_test_wav(self, samples):
        """Create a WAV file bytes from samples."""
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(44100)
            # Convert to 16-bit integers
            int_samples = (np.array(samples) * 32767).astype(np.int16)
            wav.writeframes(int_samples.tobytes())
        return output.getvalue()

    def _read_wav_samples(self, wav_data):
        """Read samples from WAV bytes."""
        wav_buffer = io.BytesIO(wav_data)
        with wave.open(wav_buffer, 'rb') as wav:
            frames = wav.readframes(wav.getnframes())
            return np.frombuffer(frames, dtype=np.int16)

    def test_none_returns_none(self):
        """None input should return None."""
        result = apply_volume_to_wav(None, 0.5)
        assert result is None

    def test_unity_volume_returns_same(self):
        """Volume 1.0 should return same data."""
        wav_data = self._create_test_wav([0.5, 0.5, 0.5])
        result = apply_volume_to_wav(wav_data, 1.0)
        assert result == wav_data

    def test_half_volume_halves_samples(self):
        """Volume 0.5 should halve sample values."""
        # Create WAV with known samples
        original_samples = [0.5, 0.5, 0.5]
        wav_data = self._create_test_wav(original_samples)

        # Apply half volume
        result = apply_volume_to_wav(wav_data, 0.5)

        # Read back and check
        result_samples = self._read_wav_samples(result)
        expected = int(0.5 * 32767 * 0.5)  # Original * volume
        # Allow for rounding
        assert all(abs(s - expected) <= 1 for s in result_samples)

    def test_zero_volume_silences(self):
        """Volume 0 should produce silence."""
        wav_data = self._create_test_wav([0.8, 0.8, 0.8])
        result = apply_volume_to_wav(wav_data, 0.0)
        result_samples = self._read_wav_samples(result)
        assert all(s == 0 for s in result_samples)


class TestSoundGeneration:
    """Tests for sound generation functions."""

    def _is_valid_wav(self, data):
        """Check if data is valid WAV bytes."""
        if data is None:
            return False
        try:
            wav_buffer = io.BytesIO(data)
            with wave.open(wav_buffer, 'rb') as wav:
                return wav.getnframes() > 0
        except Exception:
            return False

    def test_click_sound_returns_valid_wav(self):
        """generate_click_sound should return valid WAV bytes."""
        result = generate_click_sound()
        assert self._is_valid_wav(result)

    def test_click_sound_custom_params(self):
        """generate_click_sound should accept custom parameters."""
        result = generate_click_sound(frequency=440, duration_ms=100, volume=0.5)
        assert self._is_valid_wav(result)

    def test_two_tone_sound_returns_valid_wav(self):
        """generate_two_tone_sound should return valid WAV bytes."""
        result = generate_two_tone_sound()
        assert self._is_valid_wav(result)

    def test_chime_sound_returns_valid_wav(self):
        """generate_chime_sound should return valid WAV bytes."""
        result = generate_chime_sound()
        assert self._is_valid_wav(result)

    def test_double_beep_sound_returns_valid_wav(self):
        """generate_double_beep_sound should return valid WAV bytes."""
        result = generate_double_beep_sound()
        assert self._is_valid_wav(result)

    def test_error_buzz_sound_returns_valid_wav(self):
        """generate_error_buzz_sound should return valid WAV bytes."""
        result = generate_error_buzz_sound()
        assert self._is_valid_wav(result)

    def test_sounds_have_different_lengths(self):
        """Different sounds should have different durations."""
        click = generate_click_sound(duration_ms=50)
        chime = generate_chime_sound(duration_ms=150)

        click_buf = io.BytesIO(click)
        chime_buf = io.BytesIO(chime)

        with wave.open(click_buf, 'rb') as w1, wave.open(chime_buf, 'rb') as w2:
            # Chime should be longer than click
            assert w2.getnframes() > w1.getnframes()


class TestIconGeneration:
    """Tests for status icon generation."""

    def test_generate_status_icon_dimensions(self):
        """Icon should have correct dimensions."""
        icon = generate_status_icon('#0d9488')
        assert icon.size == (64, 64)
        assert icon.mode == 'RGBA'

    def test_generate_status_icon_different_colors(self):
        """Should generate icons with different colors."""
        icon_teal = generate_status_icon('#0d9488')
        icon_red = generate_status_icon('#ef4444')
        # Both should be valid RGBA images
        assert icon_teal.mode == 'RGBA'
        assert icon_red.mode == 'RGBA'
        # Images should be different (different circle colors)
        assert icon_teal.tobytes() != icon_red.tobytes()

    def test_generate_status_icon_transparency(self):
        """Corners should be transparent."""
        icon = generate_status_icon('#0d9488')
        # Check corner pixels are transparent (alpha channel = 0)
        assert icon.getpixel((0, 0))[3] == 0  # Top-left
        assert icon.getpixel((63, 0))[3] == 0  # Top-right
        assert icon.getpixel((0, 63))[3] == 0  # Bottom-left
        assert icon.getpixel((63, 63))[3] == 0  # Bottom-right

    def test_generate_status_icon_has_white_bars(self):
        """Icon should contain white pixels from waveform bars."""
        icon = generate_status_icon('#0d9488')
        pixels = list(icon.getdata())
        # Count white pixels (R=255, G=255, B=255, alpha>200)
        white_pixels = [p for p in pixels if p[0:3] == (255, 255, 255) and p[3] > 200]
        # Should have substantial white area from bars (at least 50 pixels)
        assert len(white_pixels) > 50

    def test_generate_status_icon_center_is_opaque(self):
        """Center of icon should be opaque (not transparent)."""
        icon = generate_status_icon('#0d9488')
        # Check center pixel is opaque
        center_pixel = icon.getpixel((32, 32))
        assert center_pixel[3] > 200  # Alpha channel should be near 255
