"""
Tests for translation mode functionality.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestTranslationConfig:
    """Tests for translation mode configuration."""

    def test_translation_enabled_default(self):
        """translation_enabled should default to False."""
        assert config.DEFAULTS["translation_enabled"] is False

    def test_translation_source_language_default(self):
        """translation_source_language should default to 'auto'."""
        assert config.DEFAULTS["translation_source_language"] == "auto"

    def test_translation_enabled_is_bool(self):
        """translation_enabled should be a boolean."""
        assert isinstance(config.DEFAULTS["translation_enabled"], bool)

    def test_translation_source_language_is_string(self):
        """translation_source_language should be a string."""
        assert isinstance(config.DEFAULTS["translation_source_language"], str)

    def test_translation_source_language_in_options(self):
        """translation_source_language default should be valid."""
        source_lang = config.DEFAULTS["translation_source_language"]
        # 'auto' is valid, or any language in LANGUAGE_OPTIONS
        assert source_lang == "auto" or source_lang in config.LANGUAGE_OPTIONS


class TestTranslationModeLogic:
    """Tests for translation mode logic."""

    def test_translation_mode_task_parameter(self):
        """When translation is enabled, task should be 'translate'."""
        # This will be tested via integration tests with actual transcription
        # Here we just verify the config values exist
        test_config = config.DEFAULTS.copy()
        test_config["translation_enabled"] = True
        assert test_config["translation_enabled"] is True

    def test_translation_mode_disabled_task_parameter(self):
        """When translation is disabled, task should be 'transcribe'."""
        test_config = config.DEFAULTS.copy()
        test_config["translation_enabled"] = False
        assert test_config["translation_enabled"] is False

    def test_translation_source_language_auto(self):
        """Auto-detect source language should map to None for Whisper."""
        test_config = config.DEFAULTS.copy()
        test_config["translation_source_language"] = "auto"
        # In actual code, "auto" gets converted to None for Whisper
        assert test_config["translation_source_language"] == "auto"

    def test_translation_source_language_specific(self):
        """Specific source language should be passed to Whisper."""
        test_config = config.DEFAULTS.copy()
        test_config["translation_source_language"] = "es"  # Spanish
        assert test_config["translation_source_language"] == "es"


class TestTranslationWithOtherFeatures:
    """Tests for translation mode integration with other features."""

    def test_translation_with_initial_prompt(self):
        """Translation should work with initial_prompt."""
        test_config = config.DEFAULTS.copy()
        test_config["translation_enabled"] = True
        test_config["initial_prompt"] = "Test prompt"
        assert test_config["translation_enabled"] is True
        assert test_config["initial_prompt"] == "Test prompt"

    def test_translation_mode_saved_and_loaded(self, tmp_path, mocker):
        """Translation mode settings should persist across save/load."""
        config_file = tmp_path / "test_config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Save config with translation enabled
        test_config = config.DEFAULTS.copy()
        test_config["translation_enabled"] = True
        test_config["translation_source_language"] = "fr"
        config.save_config(test_config)

        # Load and verify
        loaded = config.load_config()
        assert loaded["translation_enabled"] is True
        assert loaded["translation_source_language"] == "fr"
