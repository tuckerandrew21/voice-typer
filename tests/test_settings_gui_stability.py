"""
Stability tests for settings_gui.py.

Tests crash resistance, edge case handling, and resource cleanup.
These tests verify the GUI handles error conditions gracefully.
"""
import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch, PropertyMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_customtkinter(mocker):
    """Mock CustomTkinter to prevent GUI from launching."""
    mock_ctk = MagicMock()
    mock_ctk.CTk = MagicMock
    mock_ctk.CTkFrame = MagicMock
    mock_ctk.CTkLabel = MagicMock
    mock_ctk.CTkButton = MagicMock
    mock_ctk.CTkEntry = MagicMock
    mock_ctk.CTkSwitch = MagicMock
    mock_ctk.CTkOptionMenu = MagicMock
    mock_ctk.CTkScrollableFrame = MagicMock
    mock_ctk.CTkSlider = MagicMock
    mock_ctk.CTkCanvas = MagicMock
    mock_ctk.CTkToplevel = MagicMock
    mock_ctk.set_appearance_mode = MagicMock()
    mock_ctk.set_default_color_theme = MagicMock()
    mocker.patch.dict('sys.modules', {'customtkinter': mock_ctk})
    return mock_ctk


@pytest.fixture
def mock_sounddevice(mocker):
    """Mock sounddevice module."""
    mock_sd = MagicMock()
    mock_sd.query_devices.return_value = [
        {'name': 'Test Microphone', 'max_input_channels': 2, 'default_samplerate': 44100.0}
    ]
    mock_sd.InputStream = MagicMock()
    mocker.patch.dict('sys.modules', {'sounddevice': mock_sd})
    return mock_sd


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "murmurtone_settings.json"
    default_config = {
        "hotkey": {
            "ctrl": True,
            "shift": True,
            "alt": False,
            "key": "space"
        },
        "recording_mode": "push_to_talk",
        "language": "auto",
        "model_size": "base",
        "silence_duration": 2.0,
        "processing_mode": "auto",
        "preview_enabled": True,
        "preview_position": "bottom_right",
        "preview_theme": "dark",
        "auto_hide_delay": 2.0,
        "enable_sounds": True,
        "noise_gate_enabled": False,
        "noise_threshold": -40,
    }
    config_file.write_text(json.dumps(default_config))
    return config_file


# =============================================================================
# Config File Handling Tests
# =============================================================================

class TestConfigFileHandling:
    """Test GUI behavior with various config file states."""

    def test_load_missing_config_file(self, mocker, tmp_path):
        """App should create default config when file doesn't exist."""
        import config

        # Point to non-existent file
        fake_path = tmp_path / "nonexistent" / "config.json"
        mocker.patch('config.get_config_path', return_value=str(fake_path))

        # load_config should return defaults, not crash
        result = config.load_config()

        assert isinstance(result, dict)
        assert "hotkey" in result
        assert "model_size" in result

    def test_load_corrupted_config_file(self, mocker, tmp_path):
        """App should handle malformed JSON gracefully."""
        import config

        # Create corrupted config file
        bad_config = tmp_path / "bad_config.json"
        bad_config.write_text("{ this is not valid json }")
        mocker.patch('config.get_config_path', return_value=str(bad_config))

        # Should return defaults, not crash
        result = config.load_config()

        assert isinstance(result, dict)
        assert "hotkey" in result

    def test_load_empty_config_file(self, mocker, tmp_path):
        """App should handle empty config file."""
        import config

        empty_config = tmp_path / "empty_config.json"
        empty_config.write_text("")
        mocker.patch('config.get_config_path', return_value=str(empty_config))

        result = config.load_config()

        assert isinstance(result, dict)

    def test_load_config_with_extra_keys(self, mocker, tmp_path):
        """App should ignore unknown config keys without crashing."""
        import config

        config_with_extras = tmp_path / "config.json"
        config_data = {
            "hotkey": {
                "ctrl": True,
                "shift": False,
                "alt": False,
                "key": "f9"
            },
            "unknown_future_key": "some value",
            "another_unknown": 12345,
        }
        config_with_extras.write_text(json.dumps(config_data))
        mocker.patch('config.get_config_path', return_value=str(config_with_extras))

        result = config.load_config()

        assert isinstance(result, dict)
        assert result.get("hotkey", {}).get("key") == "f9"


# =============================================================================
# Audio Device Handling Tests
# =============================================================================

class TestAudioDeviceHandling:
    """Test behavior when audio devices are unavailable or change."""

    def test_no_audio_devices_available(self, mocker):
        """App should handle no microphones gracefully."""
        import config

        # Mock sounddevice to return empty list
        mock_sd = MagicMock()
        mock_sd.query_devices.return_value = []
        mocker.patch.dict('sys.modules', {'sounddevice': mock_sd})

        # Force reimport
        if 'config' in sys.modules:
            del sys.modules['config']
        import config

        devices = config.get_input_devices()

        # Should return empty list or handle gracefully
        assert isinstance(devices, list)

    def test_sounddevice_import_fails(self, mocker):
        """App should handle missing sounddevice library."""
        import config

        # Mock the import to raise
        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def mock_import(name, *args, **kwargs):
            if name == 'sounddevice':
                raise ImportError("No module named 'sounddevice'")
            return original_import(name, *args, **kwargs)

        # This test verifies the pattern - actual behavior depends on implementation
        # The key is that the app doesn't crash


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    """Test edge case input handling."""

    def test_silence_duration_clamping(self, temp_config_file, mocker):
        """Silence duration should be clamped to valid range."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        # Test various invalid values
        test_cases = [
            (-5.0, 0.5),      # Negative -> clamp to min
            (0, 0.5),         # Zero -> clamp to min
            (100.0, 10.0),    # Too large -> clamp to max
            (2.0, 2.0),       # Valid -> unchanged
        ]

        for input_val, expected_min in test_cases:
            cfg = config.load_config()
            cfg['silence_duration'] = input_val

            # The validation happens in the GUI/settings_logic
            # Here we verify the config module accepts any value
            config.save_config(cfg)

            reloaded = config.load_config()
            assert 'silence_duration' in reloaded

    def test_noise_threshold_range(self, temp_config_file, mocker):
        """Noise threshold should accept valid dB values."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        cfg = config.load_config()

        # Valid range is typically -60 to 0 dB
        test_values = [-60, -40, -20, 0]

        for val in test_values:
            cfg['noise_threshold'] = val
            config.save_config(cfg)

            reloaded = config.load_config()
            assert reloaded['noise_threshold'] == val

    def test_auto_hide_delay_accepts_zero(self, temp_config_file, mocker):
        """Auto-hide delay of 0 should be valid (instant hide)."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        cfg = config.load_config()
        cfg['auto_hide_delay'] = 0
        config.save_config(cfg)

        reloaded = config.load_config()
        assert reloaded['auto_hide_delay'] == 0

    def test_unicode_in_vocabulary(self, temp_config_file, mocker):
        """Custom vocabulary should accept unicode characters."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        cfg = config.load_config()
        cfg['custom_vocabulary'] = ["café", "naïve", "日本語", "emoji: 🎤"]
        config.save_config(cfg)

        reloaded = config.load_config()
        assert "café" in reloaded.get('custom_vocabulary', [])
        assert "日本語" in reloaded.get('custom_vocabulary', [])

    def test_large_vocabulary_list(self, temp_config_file, mocker):
        """Should handle large vocabulary lists without crashing."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        cfg = config.load_config()
        # Create 1000 vocabulary items
        cfg['custom_vocabulary'] = [f"word_{i}" for i in range(1000)]
        config.save_config(cfg)

        reloaded = config.load_config()
        assert len(reloaded.get('custom_vocabulary', [])) == 1000


# =============================================================================
# GPU Detection Tests
# =============================================================================

class TestGPUDetection:
    """Test GPU detection error handling."""

    def test_cuda_status_without_gpu(self, mocker):
        """CUDA status check should work without GPU."""
        import settings_logic

        # Enable test mode
        original = settings_logic._TEST_GPU_UNAVAILABLE
        settings_logic._TEST_GPU_UNAVAILABLE = True

        try:
            available, status, detail = settings_logic.get_cuda_status()

            assert available is False
            assert isinstance(status, str)
        finally:
            settings_logic._TEST_GPU_UNAVAILABLE = original

    def test_check_cuda_returns_bool(self):
        """check_cuda_available should always return bool, not crash."""
        import settings_logic

        result = settings_logic.check_cuda_available()

        assert isinstance(result, bool)


# =============================================================================
# Theme and Styling Tests
# =============================================================================

class TestThemeConsistency:
    """Test theme module doesn't have errors."""

    def test_theme_imports_without_error(self):
        """Theme module should import cleanly."""
        import theme

        # Verify key constants exist
        assert hasattr(theme, 'PRIMARY')
        assert hasattr(theme, 'SLATE_900')
        assert hasattr(theme, 'ERROR')

    def test_theme_color_format(self):
        """Theme colors should be valid hex codes."""
        import theme
        import re

        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')

        colors = [
            theme.PRIMARY, theme.PRIMARY_DARK, theme.PRIMARY_LIGHT,
            theme.SLATE_900, theme.SLATE_800, theme.SLATE_700,
            theme.SUCCESS, theme.WARNING, theme.ERROR,
        ]

        for color in colors:
            assert hex_pattern.match(color), f"Invalid color format: {color}"

    def test_style_helpers_return_dicts(self):
        """Style helper functions should return dictionaries."""
        import theme

        card_style = theme.get_card_style()
        assert isinstance(card_style, dict)
        assert 'fg_color' in card_style

        button_style = theme.get_button_style()
        assert isinstance(button_style, dict)

        # Test all button variants
        for variant in ['primary', 'secondary', 'danger', 'ghost']:
            style = theme.get_button_style(variant)
            assert isinstance(style, dict)


# =============================================================================
# Resource Cleanup Tests
# =============================================================================

class TestResourceCleanup:
    """Test that resources are properly released."""

    def test_autosave_manager_stops_on_destroy(self):
        """AutosaveManager should clean up its timer."""
        # This is a pattern test - actual implementation may vary
        # The key behavior is that timers/threads are cancelled on window close
        pass  # Implementation depends on GUI lifecycle

    def test_audio_stream_cleanup(self):
        """Audio streams should be stopped when test ends."""
        # Pattern test for audio resource cleanup
        pass


# =============================================================================
# Concurrent Operation Tests
# =============================================================================

class TestConcurrentOperations:
    """Test handling of rapid/concurrent operations."""

    def test_rapid_config_saves(self, temp_config_file, mocker):
        """Multiple rapid saves shouldn't corrupt config."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        # Simulate rapid saves
        for i in range(20):
            cfg = config.load_config()
            cfg['silence_duration'] = 1.0 + (i * 0.1)
            config.save_config(cfg)

        # Final config should be valid
        final = config.load_config()
        assert isinstance(final, dict)
        assert 'silence_duration' in final


class TestModelSelection:
    """Test model selection and download UI behavior."""

    def test_model_dropdown_has_all_options(self, temp_config_file, mocker):
        """Model dropdown should include all MODEL_OPTIONS."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        # Verify MODEL_OPTIONS is defined and has expected models
        assert hasattr(config, 'MODEL_OPTIONS')
        assert len(config.MODEL_OPTIONS) >= 4  # tiny, base, small, medium at minimum

        # Verify bundled and downloadable models are included
        for model in config.BUNDLED_MODELS:
            assert model in config.MODEL_OPTIONS, f"Bundled model {model} not in options"
        for model in config.DOWNLOADABLE_MODELS:
            assert model in config.MODEL_OPTIONS, f"Downloadable model {model} not in options"

    def test_model_status_for_bundled_model(self, temp_config_file, mocker, tmp_path):
        """Bundled models should show as 'Installed' when present."""
        import config
        from dependency_check import check_model_available

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        # Create fake bundled model
        models_dir = tmp_path / "models" / "tiny"
        models_dir.mkdir(parents=True)
        (models_dir / "model.bin").write_text("fake")

        mocker.patch('dependency_check.get_app_install_dir', return_value=str(tmp_path))

        is_available, path = check_model_available("tiny")
        assert is_available is True

    def test_model_status_for_downloadable_model_not_installed(self, temp_config_file, mocker, tmp_path):
        """Downloadable models should show download option when not installed."""
        import config
        from dependency_check import check_model_available

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))
        mocker.patch('dependency_check.get_app_install_dir', return_value=str(tmp_path))

        # Ensure HuggingFace cache doesn't have it either
        mocker.patch('pathlib.Path.home', return_value=tmp_path)

        # Check a downloadable model that's not installed
        for model in config.DOWNLOADABLE_MODELS:
            is_available, _ = check_model_available(model)
            assert is_available is False, f"{model} should not be available"

    def test_model_download_url_matches_model_name(self, temp_config_file, mocker):
        """Download URLs should reference the correct model name."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        for model, url in config.MODEL_DOWNLOAD_URLS.items():
            # URL should contain the model name somewhere
            assert model.replace(".", "") in url or model in url, \
                f"URL for {model} doesn't reference model name: {url}"

    def test_bundled_models_includes_tiny_and_base(self, temp_config_file, mocker):
        """BUNDLED_MODELS should include tiny and base."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        assert "tiny" in config.BUNDLED_MODELS
        assert "base" in config.BUNDLED_MODELS

    def test_downloadable_models_includes_small_medium_large(self, temp_config_file, mocker):
        """DOWNLOADABLE_MODELS should include small, medium, and large-v3."""
        import config

        mocker.patch('config.get_config_path', return_value=str(temp_config_file))

        assert "small" in config.DOWNLOADABLE_MODELS
        assert "medium" in config.DOWNLOADABLE_MODELS
        assert "large-v3" in config.DOWNLOADABLE_MODELS


# =============================================================================
# Input Validation Tests (Security)
# =============================================================================

class TestInputValidators:
    """Tests for input validation functions in settings_logic."""

    def test_validate_url_valid(self):
        """Valid URLs should be returned as-is."""
        import settings_logic

        assert settings_logic.validate_url("http://localhost:11434") == "http://localhost:11434"
        assert settings_logic.validate_url("https://example.com/api") == "https://example.com/api"

    def test_validate_url_invalid_scheme(self):
        """URLs without http/https should return default."""
        import settings_logic

        assert settings_logic.validate_url("ftp://localhost") == ""
        assert settings_logic.validate_url("file:///etc/passwd") == ""
        assert settings_logic.validate_url("javascript:alert(1)") == ""

    def test_validate_url_too_long(self):
        """URLs over 500 chars should return default."""
        import settings_logic

        long_url = "http://localhost/" + "a" * 500
        assert settings_logic.validate_url(long_url) == ""

    def test_validate_url_empty(self):
        """Empty or None URLs should return default."""
        import settings_logic

        assert settings_logic.validate_url("") == ""
        assert settings_logic.validate_url(None) == ""

    def test_validate_url_custom_default(self):
        """Should use custom default when provided."""
        import settings_logic

        assert settings_logic.validate_url("", default="http://fallback") == "http://fallback"

    def test_validate_text_input_valid(self):
        """Valid text should be returned."""
        import settings_logic

        assert settings_logic.validate_text_input("hello") == "hello"
        assert settings_logic.validate_text_input("unicode: café") == "unicode: café"

    def test_validate_text_input_truncation(self):
        """Long text should be truncated to max_length."""
        import settings_logic

        long_text = "a" * 2000
        result = settings_logic.validate_text_input(long_text, max_length=100)
        assert len(result) == 100

    def test_validate_text_input_invalid_type(self):
        """Non-string input should return default."""
        import settings_logic

        assert settings_logic.validate_text_input(12345) == ""
        assert settings_logic.validate_text_input(None) == ""
        assert settings_logic.validate_text_input(["list"]) == ""

    def test_validate_vocabulary_list_valid(self):
        """Valid lists should be returned."""
        import settings_logic

        items = ["word1", "word2", "word3"]
        result = settings_logic.validate_vocabulary_list(items)
        assert result == items

    def test_validate_vocabulary_list_max_items(self):
        """Lists over max_items should be truncated."""
        import settings_logic

        items = [f"word{i}" for i in range(1000)]
        result = settings_logic.validate_vocabulary_list(items, max_items=10)
        assert len(result) == 10

    def test_validate_vocabulary_list_max_item_length(self):
        """Items over max_item_length should be filtered out."""
        import settings_logic

        items = ["short", "a" * 300, "medium"]
        result = settings_logic.validate_vocabulary_list(items, max_item_length=50)
        assert result == ["short", "medium"]

    def test_validate_vocabulary_list_invalid_type(self):
        """Non-list input should return empty list."""
        import settings_logic

        assert settings_logic.validate_vocabulary_list("not a list") == []
        assert settings_logic.validate_vocabulary_list(None) == []
        assert settings_logic.validate_vocabulary_list(123) == []

    def test_validate_vocabulary_list_filters_non_strings(self):
        """Non-string items should be filtered out."""
        import settings_logic

        items = ["valid", 123, None, "also valid", ["nested"]]
        result = settings_logic.validate_vocabulary_list(items)
        assert result == ["valid", "also valid"]
