"""
Tests for config.py - Configuration loading, saving, and defaults.
"""
import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestConfigDefaults:
    """Tests for configuration default values."""

    def test_defaults_exist(self):
        """DEFAULTS dictionary should contain expected keys."""
        required_keys = [
            'model_size',
            'language',
            'hotkey',
            'audio_feedback',
        ]
        for key in required_keys:
            assert key in config.DEFAULTS, f"Missing required default: {key}"

    def test_default_model_size_valid(self):
        """Default model size should be in MODEL_OPTIONS list."""
        assert config.DEFAULTS['model_size'] in config.MODEL_OPTIONS

    def test_default_language_valid(self):
        """Default language should be in LANGUAGE_OPTIONS list."""
        assert config.DEFAULTS['language'] in config.LANGUAGE_OPTIONS

    def test_gpu_defaults_exist(self):
        """GPU-related defaults should exist."""
        assert 'processing_mode' in config.DEFAULTS

    def test_processing_mode_options_include_required(self):
        """Processing mode options should include auto, cpu, and gpu modes."""
        assert 'auto' in config.PROCESSING_MODE_OPTIONS
        assert 'cpu' in config.PROCESSING_MODE_OPTIONS
        assert 'gpu-balanced' in config.PROCESSING_MODE_OPTIONS
        assert 'gpu-quality' in config.PROCESSING_MODE_OPTIONS

    def test_processing_mode_map_valid(self):
        """Each processing mode should map to valid device and compute type."""
        for mode, settings in config.PROCESSING_MODE_MAP.items():
            assert 'device' in settings
            assert 'compute_type' in settings
            assert settings['device'] in ('auto', 'cpu', 'cuda')
            assert settings['compute_type'] in ('int8', 'float16', 'float32')


class TestConfigLoadSave:
    """Tests for config file loading and saving."""

    def test_load_config_returns_defaults_when_no_file(self, tmp_path, mocker):
        """load_config should return defaults when config file doesn't exist."""
        # Mock get_config_path to return path to non-existent file
        fake_config = tmp_path / "nonexistent.json"
        mocker.patch('config.get_config_path', return_value=str(fake_config))

        result = config.load_config()

        # Should have all default keys
        for key in config.DEFAULTS:
            assert key in result

    def test_save_and_load_config(self, tmp_path, mocker):
        """Saved config should be loadable and match."""
        config_file = tmp_path / "test_config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        test_config = config.DEFAULTS.copy()
        test_config.update({
            'model_size': 'medium.en',
            'language': 'auto',
            'audio_feedback': False,
        })

        config.save_config(test_config)
        loaded = config.load_config()

        assert loaded['model_size'] == 'medium.en'
        assert loaded['language'] == 'auto'
        assert loaded['audio_feedback'] is False

    def test_load_config_merges_with_defaults(self, tmp_path, mocker):
        """Loading partial config should fill in missing keys from defaults."""
        config_file = tmp_path / "partial_config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Write partial config (missing most keys)
        partial = {'model_size': 'tiny.en'}
        with open(config_file, 'w') as f:
            json.dump(partial, f)

        loaded = config.load_config()

        # Should have the saved value
        assert loaded['model_size'] == 'tiny.en'
        # Should have defaults for missing keys
        assert loaded['language'] == config.DEFAULTS['language']

    def test_load_config_handles_corrupt_file(self, tmp_path, mocker):
        """load_config should handle corrupt JSON gracefully."""
        config_file = tmp_path / "corrupt.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Write invalid JSON
        with open(config_file, 'w') as f:
            f.write("{ not valid json }")

        # Should return defaults, not crash
        result = config.load_config()
        assert 'model_size' in result
        assert result['model_size'] == config.DEFAULTS['model_size']


class TestInputDevices:
    """Tests for audio input device enumeration."""

    def test_get_input_devices_returns_list(self, mocker):
        """get_input_devices should return a list of (name, info) tuples."""
        # Mock sounddevice
        mock_sd = mocker.patch('config.sd')
        mock_sd.query_devices.return_value = [
            {'name': 'Microphone 1', 'max_input_channels': 2, 'hostapi': 0},
            {'name': 'Microphone 2', 'max_input_channels': 1, 'hostapi': 0},
            {'name': 'Speaker (output only)', 'max_input_channels': 0, 'hostapi': 0},
        ]
        mock_sd.query_hostapis.return_value = [{'name': 'Windows WASAPI'}]
        mock_sd.default.device = (0, 1)  # (input, output)

        result = config.get_input_devices()

        # Should be a list
        assert isinstance(result, list)
        # First should be system default
        assert 'Default' in result[0][0]
        assert result[0][1] is None  # System default has None as device info


class TestModelOptions:
    """Tests for model size options."""

    def test_model_options_not_empty(self):
        """MODEL_OPTIONS should contain at least one option."""
        assert len(config.MODEL_OPTIONS) > 0

    def test_model_options_include_common(self):
        """MODEL_OPTIONS should include commonly used sizes."""
        # Should have at least tiny and small variants
        options = config.MODEL_OPTIONS
        assert any('tiny' in s.lower() for s in options)


class TestProcessingModes:
    """Tests for processing mode configurations."""

    def test_cpu_mode_uses_int8(self):
        """CPU mode should use int8 compute type."""
        mode = config.PROCESSING_MODE_MAP['cpu']
        assert mode['device'] == 'cpu'
        assert mode['compute_type'] == 'int8'

    def test_auto_mode_uses_float16(self):
        """Auto mode should use float16 for GPU (when available)."""
        mode = config.PROCESSING_MODE_MAP['auto']
        assert mode['device'] == 'auto'
        assert mode['compute_type'] == 'float16'

    def test_gpu_balanced_uses_float16(self):
        """GPU Balanced mode should use float16."""
        mode = config.PROCESSING_MODE_MAP['gpu-balanced']
        assert mode['device'] == 'cuda'
        assert mode['compute_type'] == 'float16'

    def test_gpu_quality_uses_float32(self):
        """GPU Quality mode should use float32."""
        mode = config.PROCESSING_MODE_MAP['gpu-quality']
        assert mode['device'] == 'cuda'
        assert mode['compute_type'] == 'float32'


class TestMigrateGpuSettings:
    """Tests for config migration from old device/compute to processing_mode."""

    def test_migrate_cpu_int8(self):
        """cpu + int8 should migrate to 'cpu' mode."""
        old_config = {'whisper_device': 'cpu', 'compute_type': 'int8'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'cpu'
        assert 'whisper_device' not in old_config
        assert 'compute_type' not in old_config

    def test_migrate_cuda_float16(self):
        """cuda + float16 should migrate to 'gpu-balanced' mode."""
        old_config = {'whisper_device': 'cuda', 'compute_type': 'float16'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'gpu-balanced'

    def test_migrate_cuda_float32(self):
        """cuda + float32 should migrate to 'gpu-quality' mode."""
        old_config = {'whisper_device': 'cuda', 'compute_type': 'float32'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'gpu-quality'

    def test_migrate_auto_float16(self):
        """auto + float16 should migrate to 'auto' mode."""
        old_config = {'whisper_device': 'auto', 'compute_type': 'float16'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'auto'

    def test_migrate_cuda_int8(self):
        """cuda + int8 should migrate to 'auto' mode."""
        old_config = {'whisper_device': 'cuda', 'compute_type': 'int8'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'auto'

    def test_migrate_auto_int8(self):
        """auto + int8 should migrate to 'auto' mode."""
        old_config = {'whisper_device': 'auto', 'compute_type': 'int8'}
        config.migrate_gpu_settings(old_config)
        assert old_config['processing_mode'] == 'auto'

    def test_no_migration_when_no_old_keys(self):
        """Config with processing_mode should not be migrated."""
        new_config = {'processing_mode': 'gpu-balanced'}
        result = config.migrate_gpu_settings(new_config)
        assert result is False
        assert new_config['processing_mode'] == 'gpu-balanced'


class TestHotkeyHelpers:
    """Tests for hotkey conversion functions."""

    def test_hotkey_to_string_full(self):
        """Full hotkey with all modifiers."""
        hotkey = {'ctrl': True, 'shift': True, 'alt': True, 'key': 'space'}
        result = config.hotkey_to_string(hotkey)
        assert 'Ctrl' in result
        assert 'Shift' in result
        assert 'Alt' in result
        assert 'Space' in result

    def test_hotkey_to_string_minimal(self):
        """Hotkey with no modifiers."""
        hotkey = {'ctrl': False, 'shift': False, 'alt': False, 'key': 'f1'}
        result = config.hotkey_to_string(hotkey)
        assert result == 'F1'

    def test_hotkey_to_string_single_char(self):
        """Hotkey with single character key."""
        hotkey = {'ctrl': True, 'shift': False, 'alt': False, 'key': 'a'}
        result = config.hotkey_to_string(hotkey)
        assert result == 'Ctrl+A'


class TestLanguageConfig:
    """Tests for language options and labels."""

    def test_language_options_has_common_languages(self):
        """LANGUAGE_OPTIONS should include common languages."""
        assert "en" in config.LANGUAGE_OPTIONS
        assert "es" in config.LANGUAGE_OPTIONS
        assert "fr" in config.LANGUAGE_OPTIONS
        assert "de" in config.LANGUAGE_OPTIONS
        assert "auto" in config.LANGUAGE_OPTIONS

    def test_language_options_minimum_count(self):
        """Should have at least 10 language options."""
        assert len(config.LANGUAGE_OPTIONS) >= 10

    def test_all_language_options_have_labels(self):
        """Every language option should have a corresponding label."""
        for code in config.LANGUAGE_OPTIONS:
            assert code in config.LANGUAGE_LABELS, f"Missing label for language: {code}"

    def test_language_labels_are_human_readable(self):
        """Labels should be human-readable names, not codes."""
        assert config.LANGUAGE_LABELS["en"] == "English"
        assert config.LANGUAGE_LABELS["es"] == "Spanish"
        assert config.LANGUAGE_LABELS["fr"] == "French"
        assert config.LANGUAGE_LABELS["auto"] == "Auto-detect"

    def test_language_labels_not_same_as_codes(self):
        """Labels should be different from codes (human readable)."""
        for code, label in config.LANGUAGE_LABELS.items():
            # Labels should be longer/different than 2-3 char codes
            assert len(label) > len(code), f"Label '{label}' too short for code '{code}'"

    def test_default_language_has_label(self):
        """Default language should have a label."""
        default_lang = config.DEFAULTS.get("language", "en")
        assert default_lang in config.LANGUAGE_LABELS


class TestWhisperOptimizationConfig:
    """Tests for Whisper transcription optimization configuration."""

    def test_initial_prompt_default_exists(self):
        """initial_prompt should have a default value."""
        assert "initial_prompt" in config.DEFAULTS

    def test_initial_prompt_is_string(self):
        """initial_prompt should be a string."""
        assert isinstance(config.DEFAULTS["initial_prompt"], str)

    def test_initial_prompt_not_empty(self):
        """Default initial_prompt should not be empty (optimization hint)."""
        assert len(config.DEFAULTS["initial_prompt"]) > 0


class TestPasteModeConfig:
    """Tests for paste mode configuration."""

    def test_paste_mode_default_exists(self):
        """paste_mode should have a default value."""
        assert "paste_mode" in config.DEFAULTS

    def test_paste_mode_default_is_clipboard(self):
        """Default paste mode should be 'clipboard'."""
        assert config.DEFAULTS["paste_mode"] == "clipboard"

    def test_direct_typing_delay_default_exists(self):
        """direct_typing_delay_ms should have a default value."""
        assert "direct_typing_delay_ms" in config.DEFAULTS

    def test_direct_typing_delay_is_positive(self):
        """Direct typing delay should be a positive number."""
        assert config.DEFAULTS["direct_typing_delay_ms"] >= 0


class TestTranslationModeConfig:
    """Tests for translation mode configuration."""

    def test_translation_enabled_default_exists(self):
        """translation_enabled should have a default value."""
        assert "translation_enabled" in config.DEFAULTS

    def test_translation_enabled_is_bool(self):
        """translation_enabled should be a boolean."""
        assert isinstance(config.DEFAULTS["translation_enabled"], bool)

    def test_translation_source_language_default_exists(self):
        """translation_source_language should have a default value."""
        assert "translation_source_language" in config.DEFAULTS

    def test_translation_source_language_is_string(self):
        """translation_source_language should be a string."""
        assert isinstance(config.DEFAULTS["translation_source_language"], str)

    def test_translation_source_language_valid(self):
        """translation_source_language default should be valid."""
        source_lang = config.DEFAULTS["translation_source_language"]
        # Should be 'auto' or a language in LANGUAGE_OPTIONS
        assert source_lang == "auto" or source_lang in config.LANGUAGE_OPTIONS


class TestCustomVocabularyConfig:
    """Tests for custom vocabulary configuration."""

    def test_custom_vocabulary_default_exists(self):
        """custom_vocabulary should have a default value."""
        assert "custom_vocabulary" in config.DEFAULTS

    def test_custom_vocabulary_is_list(self):
        """custom_vocabulary should be a list."""
        assert isinstance(config.DEFAULTS["custom_vocabulary"], list)

    def test_custom_vocabulary_default_empty(self):
        """custom_vocabulary should default to empty list."""
        assert config.DEFAULTS["custom_vocabulary"] == []

    def test_custom_vocabulary_saved_and_loaded(self, tmp_path, mocker):
        """Custom vocabulary should persist across save/load."""
        config_file = tmp_path / "test_config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Save config with custom vocabulary
        test_config = config.DEFAULTS.copy()
        test_config["custom_vocabulary"] = ["TensorFlow", "Kubernetes", "Dr. Smith"]
        config.save_config(test_config)

        # Load and verify
        loaded = config.load_config()
        assert "TensorFlow" in loaded["custom_vocabulary"]
        assert "Kubernetes" in loaded["custom_vocabulary"]
        assert "Dr. Smith" in loaded["custom_vocabulary"]
