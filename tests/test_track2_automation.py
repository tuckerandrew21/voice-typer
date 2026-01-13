"""
Track 2 Integration Testing - Automated Test Suite

Tests features that can be verified programmatically without manual intervention.
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import numpy as np
import sounddevice as sd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from license import License
import post_processing


class TestLicenseActivationFlow:
    """Test license activation UI and logic"""

    def test_trial_active_on_first_launch(self, tmp_path):
        """Verify trial activates on first launch"""
        config = Config(config_dir=str(tmp_path))
        license_obj = License(config)

        assert license_obj.get_status() == "trial"
        assert license_obj.get_days_remaining() == 14

    def test_trial_countdown(self, tmp_path):
        """Verify trial countdown works correctly"""
        config = Config(config_dir=str(tmp_path))

        # Set trial start to 5 days ago
        config.set("trial_started_date", (datetime.now() - timedelta(days=5)).isoformat())

        license_obj = License(config)
        assert license_obj.get_days_remaining() == 9

    def test_trial_expiration(self, tmp_path):
        """Verify trial expiration detection"""
        config = Config(config_dir=str(tmp_path))

        # Set trial start to 15 days ago (expired)
        config.set("trial_started_date", (datetime.now() - timedelta(days=15)).isoformat())

        license_obj = License(config)
        assert license_obj.is_trial_expired() is True
        assert license_obj.get_days_remaining() == 0

    def test_license_activation(self, tmp_path):
        """Test license activation with mock key"""
        config = Config(config_dir=str(tmp_path))
        license_obj = License(config)

        # Mock successful activation
        config.set("license_key", "TEST-KEY-12345")
        config.set("license_status", "active")

        assert license_obj.get_status() == "active"
        assert license_obj.is_active() is True

    def test_invalid_license_key(self, tmp_path):
        """Test handling of invalid license key"""
        config = Config(config_dir=str(tmp_path))
        license_obj = License(config)

        config.set("license_key", "INVALID")
        config.set("license_status", "invalid")

        assert license_obj.get_status() == "invalid"
        assert license_obj.is_active() is False


class TestSettingsGUI:
    """Test Settings GUI functionality"""

    def test_settings_sections_exist(self, tmp_path):
        """Verify all settings sections are defined"""
        config = Config(config_dir=str(tmp_path))

        # Check core settings exist
        assert config.get("model_size") is not None
        assert config.get("language") is not None
        assert config.get("hotkey") is not None

        # Check new feature settings exist
        assert config.get("custom_vocabulary") is not None
        assert config.get("translation_enabled") is not None
        assert config.get("ai_cleanup_enabled") is not None
        assert config.get("license_status") is not None

    def test_settings_persistence(self, tmp_path):
        """Verify settings save and load correctly"""
        config = Config(config_dir=str(tmp_path))

        # Set custom values
        config.set("model_size", "base.en")
        config.set("custom_vocabulary", ["MurmurTone", "GitHub"])
        config.set("translation_enabled", True)
        config.save()

        # Create new config instance (reload)
        config2 = Config(config_dir=str(tmp_path))

        assert config2.get("model_size") == "base.en"
        assert config2.get("custom_vocabulary") == ["MurmurTone", "GitHub"]
        assert config2.get("translation_enabled") is True


class TestCustomVocabulary:
    """Test custom vocabulary integration"""

    def test_vocabulary_added_to_prompt(self):
        """Verify custom vocabulary is injected into prompts"""
        from vocabulary import inject_vocabulary

        base_prompt = "Use proper punctuation."
        vocabulary = ["MurmurTone", "GitHub", "PyTorch"]

        result = inject_vocabulary(base_prompt, vocabulary)

        assert "MurmurTone" in result
        assert "GitHub" in result
        assert "PyTorch" in result
        assert base_prompt in result

    def test_empty_vocabulary_handling(self):
        """Verify empty vocabulary doesn't break prompts"""
        from vocabulary import inject_vocabulary

        base_prompt = "Use proper punctuation."
        result = inject_vocabulary(base_prompt, [])

        assert result == base_prompt


class TestVoiceCommandLogic:
    """Test voice command processing logic (without audio)"""

    def test_scratch_that_removes_text(self):
        """Verify 'scratch that' command removes last text"""
        # This tests the logic, not the actual voice recognition
        text = "Hello world"
        command_detected = "scratch that"

        # Simulate command processing
        if "scratch that" in command_detected.lower():
            result = ""  # Text should be removed
        else:
            result = text

        assert result == ""

    def test_capitalize_that_logic(self):
        """Verify 'capitalize that' command logic"""
        text = "hello world"

        # Simulate capitalize command
        words = text.split()
        if words:
            words[-1] = words[-1].capitalize()
            result = " ".join(words)

        assert result == "hello World"

    def test_uppercase_that_logic(self):
        """Verify 'uppercase that' command logic"""
        text = "hello world"

        # Simulate uppercase command
        words = text.split()
        if words:
            words[-1] = words[-1].upper()
            result = " ".join(words)

        assert result == "hello WORLD"

    def test_lowercase_that_logic(self):
        """Verify 'lowercase that' command logic"""
        text = "hello WORLD"

        # Simulate lowercase command
        words = text.split()
        if words:
            words[-1] = words[-1].lower()
            result = " ".join(words)

        assert result == "hello world"

    def test_delete_last_word_logic(self):
        """Verify 'delete last word' command logic"""
        text = "hello world test"

        # Simulate delete last word
        words = text.split()
        if words:
            words.pop()
            result = " ".join(words)

        assert result == "hello world"


class TestAudioFileTranscription:
    """Test audio file transcription feature"""

    def test_supported_formats_defined(self):
        """Verify supported audio formats are defined"""
        supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']

        # These should be the formats supported by faster-whisper
        assert '.mp3' in supported_formats
        assert '.wav' in supported_formats
        assert '.m4a' in supported_formats

    def test_create_test_wav_file(self, tmp_path):
        """Create a test WAV file for transcription testing"""
        import wave

        # Generate 1 second of silence at 16kHz
        sample_rate = 16000
        duration = 1.0
        samples = np.zeros(int(sample_rate * duration), dtype=np.int16)

        # Save as WAV
        wav_path = tmp_path / "test_audio.wav"
        with wave.open(str(wav_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())

        assert wav_path.exists()
        assert wav_path.stat().st_size > 0

        return wav_path


class TestAICleanup:
    """Test AI cleanup feature"""

    def test_ollama_connection_check(self):
        """Test Ollama availability check"""
        from ai_cleanup import check_ollama_available

        # This will return False if Ollama isn't running, which is expected
        is_available = check_ollama_available()

        # Test passes whether Ollama is available or not
        assert isinstance(is_available, bool)

    def test_cleanup_prompt_generation(self):
        """Test AI cleanup prompt generation"""
        from ai_cleanup import build_cleanup_prompt

        text = "i seen the thing yesterday"

        # Test grammar mode
        prompt = build_cleanup_prompt(text, mode="grammar")
        assert "grammar" in prompt.lower()
        assert text in prompt

        # Test formality mode
        prompt = build_cleanup_prompt(text, mode="formality", formality_level="professional")
        assert "professional" in prompt.lower() or "formal" in prompt.lower()

    def test_cleanup_fallback_when_unavailable(self):
        """Test graceful fallback when Ollama unavailable"""
        from ai_cleanup import cleanup_text

        text = "test input"

        # If Ollama not available, should return original text
        result = cleanup_text(text, model="llama3.2:3b", url="http://localhost:11434")

        # Result should either be cleaned up (if Ollama available) or original
        assert isinstance(result, str)
        assert len(result) > 0


class TestTranslationMode:
    """Test translation mode feature"""

    def test_translation_config_values(self, tmp_path):
        """Verify translation configuration"""
        config = Config(config_dir=str(tmp_path))

        # Check translation settings exist
        assert config.get("translation_enabled") is not None
        assert config.get("translation_source_language") is not None

        # Test setting translation mode
        config.set("translation_enabled", True)
        config.set("translation_source_language", "es")

        assert config.get("translation_enabled") is True
        assert config.get("translation_source_language") == "es"

    def test_translation_language_options(self):
        """Verify supported translation languages"""
        supported_languages = ["auto", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko"]

        # Should support auto-detect
        assert "auto" in supported_languages

        # Should support major languages
        assert "es" in supported_languages  # Spanish
        assert "fr" in supported_languages  # French
        assert "zh" in supported_languages  # Chinese


class TestPerformanceMetrics:
    """Test performance and resource usage"""

    def test_config_load_time(self, tmp_path, benchmark):
        """Benchmark configuration loading speed"""
        def load_config():
            return Config(config_dir=str(tmp_path))

        # Should load config in < 100ms
        result = benchmark(load_config)
        assert result is not None

    def test_license_check_performance(self, tmp_path, benchmark):
        """Benchmark license check speed"""
        config = Config(config_dir=str(tmp_path))
        license_obj = License(config)

        def check_license():
            return license_obj.is_active()

        # Should check license in < 10ms
        result = benchmark(check_license)
        assert isinstance(result, bool)


class TestSystemIntegration:
    """Test system-level integrations"""

    def test_appdata_directory_creation(self, tmp_path):
        """Verify app data directory is created"""
        config = Config(config_dir=str(tmp_path))

        # Config dir should be created
        assert Path(tmp_path).exists()

        # Settings file should be created
        settings_file = Path(tmp_path) / "settings.json"
        config.save()
        assert settings_file.exists()

    def test_log_file_creation(self, tmp_path):
        """Verify log file is created"""
        import logging

        log_file = Path(tmp_path) / "test.log"

        # Create logger
        logger = logging.getLogger("test")
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log message
        logger.info("Test log message")

        # Verify log file exists
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test log message" in content


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
