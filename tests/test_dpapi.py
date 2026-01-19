"""
Tests for DPAPI encryption module.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dpapi


class TestDpapiAvailability:
    """Tests for DPAPI availability detection."""

    def test_is_available_returns_bool(self):
        """is_available should return a boolean."""
        result = dpapi.is_available()
        assert isinstance(result, bool)

    @patch('dpapi.sys.platform', 'win32')
    def test_is_available_on_windows(self):
        """Should return True on Windows."""
        # Note: This test checks the logic, actual platform detection
        # happens at import time so we test the function directly
        assert dpapi.is_available() == (sys.platform == "win32")

    @patch('dpapi.sys.platform', 'linux')
    def test_is_available_on_linux(self):
        """Should return False on non-Windows."""
        # The actual dpapi module checks sys.platform at function call time
        # so we verify the expected behavior
        if sys.platform != "win32":
            assert dpapi.is_available() is False


class TestEncryption:
    """Tests for encrypt function."""

    def test_encrypt_empty_string(self):
        """Empty string should return empty string."""
        result = dpapi.encrypt("")
        assert result == ""

    def test_encrypt_returns_string(self):
        """Encrypt should return a string."""
        result = dpapi.encrypt("test")
        assert isinstance(result, str)

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_encrypt_produces_different_output(self):
        """Encrypted output should differ from input."""
        plaintext = "my secret license key"
        encrypted = dpapi.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_encrypt_produces_base64(self):
        """Encrypted output should be valid base64."""
        import base64
        plaintext = "test data"
        encrypted = dpapi.encrypt(plaintext)
        # Should not raise
        base64.b64decode(encrypted)

    @pytest.mark.skipif(sys.platform == "win32", reason="Fallback test for non-Windows")
    def test_encrypt_fallback_on_non_windows(self):
        """Non-Windows should use insecure fallback with prefix."""
        result = dpapi.encrypt("test")
        assert result.startswith("INSECURE:")


class TestDecryption:
    """Tests for decrypt function."""

    def test_decrypt_empty_string(self):
        """Empty string should return empty string."""
        result = dpapi.decrypt("")
        assert result == ""

    def test_decrypt_returns_string(self):
        """Decrypt should return a string."""
        # Use the insecure fallback format for testing
        result = dpapi.decrypt("INSECURE:dGVzdA==")  # base64("test")
        assert isinstance(result, str)

    def test_decrypt_insecure_format(self):
        """Should handle INSECURE: prefixed data."""
        import base64
        plaintext = "test data"
        encoded = "INSECURE:" + base64.b64encode(plaintext.encode()).decode()
        result = dpapi.decrypt(encoded)
        assert result == plaintext

    def test_decrypt_invalid_insecure_format(self):
        """Invalid base64 in INSECURE format should return empty."""
        result = dpapi.decrypt("INSECURE:not-valid-base64!!!")
        assert result == ""

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_decrypt_invalid_data(self):
        """Invalid encrypted data should return empty string."""
        result = dpapi.decrypt("invalid-not-base64")
        assert result == ""


class TestRoundTrip:
    """Tests for encrypt/decrypt round-trip."""

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_roundtrip_simple(self):
        """Should be able to decrypt what was encrypted."""
        plaintext = "my license key 12345"
        encrypted = dpapi.encrypt(plaintext)
        decrypted = dpapi.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_roundtrip_unicode(self):
        """Should handle unicode characters."""
        plaintext = "license-key-with-emoji-\u2764-and-\u00e9"
        encrypted = dpapi.encrypt(plaintext)
        decrypted = dpapi.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_roundtrip_special_chars(self):
        """Should handle special characters."""
        plaintext = "key!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = dpapi.encrypt(plaintext)
        decrypted = dpapi.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_roundtrip_long_string(self):
        """Should handle long strings."""
        plaintext = "x" * 10000
        encrypted = dpapi.encrypt(plaintext)
        decrypted = dpapi.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.skipif(sys.platform == "win32", reason="Fallback test for non-Windows")
    def test_roundtrip_fallback(self):
        """Fallback mode should also round-trip correctly."""
        plaintext = "test license key"
        encrypted = dpapi.encrypt(plaintext)
        decrypted = dpapi.decrypt(encrypted)
        assert decrypted == plaintext


class TestConfigIntegration:
    """Tests for DPAPI integration with config module."""

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_config_encrypts_license_key(self, tmp_path, mocker):
        """Config should encrypt license key when saving."""
        import config

        # Mock config path
        config_file = tmp_path / "config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Create config with license key
        test_config = config.DEFAULTS.copy()
        test_config["license_key"] = "test-license-12345"

        # Save config
        config.save_config(test_config)

        # Read raw file
        import json
        with open(config_file) as f:
            saved_data = json.load(f)

        # License key should be encrypted
        assert saved_data.get("license_key") == ""
        assert "license_key_encrypted" in saved_data
        assert saved_data["license_key_encrypted"] != "test-license-12345"

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_config_decrypts_license_key(self, tmp_path, mocker):
        """Config should decrypt license key when loading."""
        import config

        # Mock config path
        config_file = tmp_path / "config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Create config with license key
        test_config = config.DEFAULTS.copy()
        test_config["license_key"] = "test-license-12345"

        # Save then reload
        config.save_config(test_config)
        loaded = config.load_config()

        # Should have decrypted license key
        assert loaded["license_key"] == "test-license-12345"
        assert "license_key_encrypted" not in loaded

    @pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only on Windows")
    def test_config_migrates_plain_text_key(self, tmp_path, mocker):
        """Config should migrate plain text keys to encrypted."""
        import config
        import json

        # Mock config path
        config_file = tmp_path / "config.json"
        mocker.patch('config.get_config_path', return_value=str(config_file))

        # Write config with plain text key (simulating old format)
        old_config = config.DEFAULTS.copy()
        old_config["license_key"] = "plain-text-key-123"
        with open(config_file, "w") as f:
            json.dump(old_config, f)

        # Load config (should trigger migration)
        loaded = config.load_config()

        # In-memory should have key
        assert loaded["license_key"] == "plain-text-key-123"

        # File should now have encrypted key
        with open(config_file) as f:
            saved_data = json.load(f)
        assert saved_data.get("license_key") == ""
        assert "license_key_encrypted" in saved_data
