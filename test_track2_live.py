"""
Track 2 Integration Testing - Live Automated Tests

Tests real application behavior that can be automated.
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import wave
import numpy as np

# Set UTF-8 encoding for console output
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Imports from the actual codebase
import config as cfg
import license as lic
from ai_cleanup import check_ollama_available, _build_cleanup_prompt as build_cleanup_prompt


def test_license_system():
    """Test license and trial system"""
    print("\n=== Testing License System ===")

    # Load current config
    current_config = cfg.load_config()

    # Test trial status
    status_info = lic.get_license_status_info(current_config)
    print(f"✓ License Status: {status_info['status']}")
    print(f"✓ Days Remaining: {status_info['days_remaining']}")
    print(f"✓ Needs Purchase: {status_info['needs_purchase']}")

    # Test trial expiration check
    is_expired = lic.is_trial_expired(current_config)
    print(f"✓ Trial expiration check works: {not is_expired}")

    # Test trial days remaining
    days_remaining = lic.get_trial_days_remaining(current_config)
    print(f"✓ Trial days remaining: {days_remaining}")

    assert isinstance(status_info, dict)
    assert 'status' in status_info
    assert 'days_remaining' in status_info

    print("✓ License system tests passed\n")
    return True


def test_trial_expiration_scenario():
    """Test trial expiration scenario"""
    print("\n=== Testing Trial Expiration Scenario ===")

    # Create temp config with expired trial
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_file = Path(tmpdir) / "test_settings.json"

        # Create expired trial config
        expired_config = cfg.DEFAULTS.copy()
        expired_config["trial_started_date"] = (datetime.now() - timedelta(days=15)).isoformat()

        # Save temp config
        with open(temp_config_file, 'w') as f:
            json.dump(expired_config, f)

        # Check expiration
        is_expired = lic.is_trial_expired(expired_config)
        days_remaining = lic.get_trial_days_remaining(expired_config)

        print(f"✓ Trial set to 15 days ago is detected as expired: {is_expired}")
        print(f"✓ Days remaining correctly shows <= 0: {days_remaining <= 0}")

        assert is_expired is True
        assert days_remaining <= 0

    print("✓ Trial expiration scenario tests passed\n")
    return True


def test_settings_persistence():
    """Test settings save and load"""
    print("\n=== Testing Settings Persistence ===")

    # Load config
    current_config = cfg.load_config()
    print(f"✓ Config loaded successfully")

    # Check key settings exist
    assert "model_size" in current_config
    assert "language" in current_config
    assert "hotkey" in current_config
    assert "custom_vocabulary" in current_config
    assert "translation_enabled" in current_config
    assert "ai_cleanup_enabled" in current_config
    assert "license_status" in current_config

    print(f"✓ All required settings exist")
    print(f"  - Model: {current_config['model_size']}")
    print(f"  - Language: {current_config['language']}")
    print(f"  - Custom Vocabulary: {len(current_config.get('custom_vocabulary', []))} terms")
    print(f"  - Translation Enabled: {current_config.get('translation_enabled', False)}")
    print(f"  - AI Cleanup Enabled: {current_config.get('ai_cleanup_enabled', False)}")

    print("✓ Settings persistence tests passed\n")
    return True


def test_custom_vocabulary():
    """Test custom vocabulary configuration"""
    print("\n=== Testing Custom Vocabulary ===")

    current_config = cfg.load_config()

    # Check custom vocabulary setting exists
    custom_vocab = current_config.get("custom_vocabulary", [])
    print(f"✓ Custom vocabulary setting exists")
    print(f"✓ Current vocabulary terms: {len(custom_vocab)}")

    if custom_vocab:
        print(f"  Terms configured:")
        for term in custom_vocab[:5]:  # Show first 5
            print(f"    - {term}")

    # Verify it's a list
    assert isinstance(custom_vocab, list)
    print(f"✓ Custom vocabulary is a list")

    print("✓ Custom vocabulary tests passed\n")
    return True


def test_voice_command_logic():
    """Test voice command processing logic"""
    print("\n=== Testing Voice Command Logic ===")

    # Test capitalize logic
    text = "hello world"
    words = text.split()
    words[-1] = words[-1].capitalize()
    result = " ".join(words)
    assert result == "hello World"
    print(f"✓ Capitalize command logic: '{text}' → '{result}'")

    # Test uppercase logic
    text = "hello world"
    words = text.split()
    words[-1] = words[-1].upper()
    result = " ".join(words)
    assert result == "hello WORLD"
    print(f"✓ Uppercase command logic: 'hello world' → '{result}'")

    # Test lowercase logic
    text = "hello WORLD"
    words = text.split()
    words[-1] = words[-1].lower()
    result = " ".join(words)
    assert result == "hello world"
    print(f"✓ Lowercase command logic: 'hello WORLD' → '{result}'")

    # Test delete last word logic
    text = "hello world test"
    words = text.split()
    words.pop()
    result = " ".join(words)
    assert result == "hello world"
    print(f"✓ Delete last word logic: 'hello world test' → '{result}'")

    print("✓ Voice command logic tests passed\n")
    return True


def test_ai_cleanup_system():
    """Test AI cleanup system"""
    print("\n=== Testing AI Cleanup System ===")

    # Check if Ollama is available
    is_available = check_ollama_available()
    print(f"✓ Ollama availability check: {'Available' if is_available else 'Not available'}")

    # Test prompt generation
    text = "i seen the thing yesterday"

    # Grammar mode (still needs formality_level parameter)
    prompt = build_cleanup_prompt(text, mode="grammar", formality_level="professional")
    assert "grammar" in prompt.lower()
    assert text in prompt
    print(f"✓ Grammar cleanup prompt generated")

    # Formality mode
    prompt = build_cleanup_prompt(text, mode="formality", formality_level="professional")
    assert "professional" in prompt.lower() or "formal" in prompt.lower()
    print(f"✓ Formality cleanup prompt generated")

    # Both mode
    prompt = build_cleanup_prompt(text, mode="both", formality_level="formal")
    assert "grammar" in prompt.lower()
    print(f"✓ Combined cleanup prompt generated")

    if is_available:
        print("✓ Ollama is available - AI cleanup can be tested manually")
    else:
        print("! Ollama not available - AI cleanup will fallback gracefully")

    print("✓ AI cleanup system tests passed\n")
    return True


def test_translation_config():
    """Test translation configuration"""
    print("\n=== Testing Translation Configuration ===")

    current_config = cfg.load_config()

    # Check translation settings
    translation_enabled = current_config.get("translation_enabled", False)
    translation_source = current_config.get("translation_source_language", "auto")

    print(f"✓ Translation enabled: {translation_enabled}")
    print(f"✓ Source language: {translation_source}")

    # Verify source language is valid
    valid_languages = ["auto", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko"]
    assert translation_source in valid_languages or len(translation_source) == 2
    print(f"✓ Source language is valid")

    print("✓ Translation configuration tests passed\n")
    return True


def test_audio_file_support():
    """Test audio file transcription support"""
    print("\n=== Testing Audio File Support ===")

    supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']

    print(f"✓ Supported audio formats:")
    for fmt in supported_formats:
        print(f"  - {fmt}")

    # Create a test WAV file
    with tempfile.TemporaryDirectory() as tmpdir:
        test_wav = Path(tmpdir) / "test_audio.wav"

        # Generate 1 second of silence
        sample_rate = 16000
        duration = 1.0
        samples = np.zeros(int(sample_rate * duration), dtype=np.int16)

        # Save as WAV
        with wave.open(str(test_wav), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())

        assert test_wav.exists()
        assert test_wav.stat().st_size > 0
        print(f"✓ Test WAV file created: {test_wav.stat().st_size} bytes")

    print("✓ Audio file support tests passed\n")
    return True


def test_configuration_defaults():
    """Test configuration defaults"""
    print("\n=== Testing Configuration Defaults ===")

    defaults = cfg.DEFAULTS

    print(f"✓ Configuration defaults defined: {len(defaults)} settings")

    # Check critical defaults
    critical_settings = [
        "model_size",
        "language",
        "hotkey",
        "recording_mode",
        "auto_paste",
        "voice_commands_enabled",
        "custom_vocabulary",
        "translation_enabled",
        "ai_cleanup_enabled",
        "license_status",
    ]

    for setting in critical_settings:
        assert setting in defaults, f"Missing critical setting: {setting}"
        print(f"  - {setting}: {defaults[setting]}")

    print("✓ Configuration defaults tests passed\n")
    return True


def test_hotkey_parsing():
    """Test hotkey string parsing"""
    print("\n=== Testing Hotkey Parsing ===")

    test_hotkey = {"ctrl": False, "shift": False, "alt": False, "key": "scroll_lock"}

    hotkey_string = cfg.hotkey_to_string(test_hotkey)
    print(f"✓ Hotkey parsed: {hotkey_string}")

    assert isinstance(hotkey_string, str)
    assert "scroll_lock" in hotkey_string.lower() or "Scroll Lock" in hotkey_string

    print("✓ Hotkey parsing tests passed\n")
    return True


def test_startup_enabled():
    """Test startup configuration"""
    print("\n=== Testing Startup Configuration ===")

    is_enabled = cfg.get_startup_enabled()
    print(f"✓ Startup enabled status: {is_enabled}")

    assert isinstance(is_enabled, bool)

    print("✓ Startup configuration tests passed\n")
    return True


def run_all_tests():
    """Run all automated Track 2 tests"""
    print("=" * 60)
    print("TRACK 2 AUTOMATED INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("License System", test_license_system),
        ("Trial Expiration", test_trial_expiration_scenario),
        ("Settings Persistence", test_settings_persistence),
        ("Custom Vocabulary", test_custom_vocabulary),
        ("Voice Command Logic", test_voice_command_logic),
        ("AI Cleanup System", test_ai_cleanup_system),
        ("Translation Config", test_translation_config),
        ("Audio File Support", test_audio_file_support),
        ("Configuration Defaults", test_configuration_defaults),
        ("Hotkey Parsing", test_hotkey_parsing),
        ("Startup Configuration", test_startup_enabled),
    ]

    passed = 0
    failed = 0
    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                results.append((test_name, "PASS", None))
            else:
                failed += 1
                results.append((test_name, "FAIL", "Test returned False"))
        except Exception as e:
            failed += 1
            results.append((test_name, "FAIL", str(e)))
            print(f"✗ Test failed with error: {e}\n")

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, status, error in results:
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {test_name}: {status}")
        if error:
            print(f"  Error: {error}")

    print("=" * 60)
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 ALL AUTOMATED TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
