"""
Tests for file transcription functionality.
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import file_transcription


class TestFormatSupport:
    """Tests for supported file format detection."""

    def test_mp3_is_supported(self):
        """MP3 files should be supported."""
        assert file_transcription.is_supported_format("audio.mp3")
        assert file_transcription.is_supported_format("AUDIO.MP3")

    def test_wav_is_supported(self):
        """WAV files should be supported."""
        assert file_transcription.is_supported_format("recording.wav")

    def test_m4a_is_supported(self):
        """M4A files should be supported."""
        assert file_transcription.is_supported_format("voice.m4a")

    def test_mp4_is_supported(self):
        """MP4 video files should be supported."""
        assert file_transcription.is_supported_format("video.mp4")

    def test_unsupported_format(self):
        """Unsupported formats should return False."""
        assert not file_transcription.is_supported_format("document.pdf")
        assert not file_transcription.is_supported_format("image.png")

    def test_no_extension(self):
        """Files without extension should not be supported."""
        assert not file_transcription.is_supported_format("audiofile")


class TestFileTranscription:
    """Tests for file transcription logic."""

    def test_transcribe_file_not_found(self):
        """Should handle missing file gracefully."""
        mock_model = Mock()
        config = {"language": "en", "initial_prompt": ""}

        text, success = file_transcription.transcribe_file(
            "nonexistent.mp3", mock_model, config
        )

        assert not success
        assert text == ""

    def test_transcribe_unsupported_format(self):
        """Should reject unsupported file formats."""
        mock_model = Mock()
        config = {"language": "en", "initial_prompt": ""}

        # Create temp file with unsupported extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name

        try:
            text, success = file_transcription.transcribe_file(
                temp_path, mock_model, config
            )

            assert not success
            assert text == ""
        finally:
            os.unlink(temp_path)

    def test_transcribe_basic_file(self, tmp_path):
        """Should transcribe a valid audio file."""
        # Create a temp file with supported extension
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy audio data")

        # Mock model with transcribe method
        mock_segment = Mock()
        mock_segment.text = "Hello world"
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], None)

        config = {
            "language": "en",
            "initial_prompt": "Use proper punctuation.",
            "custom_vocabulary": [],
            "translation_enabled": False,
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": []
        }

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config
        )

        assert success
        assert "Hello world" in text
        mock_model.transcribe.assert_called_once()

    def test_transcribe_with_vocabulary(self, tmp_path):
        """Should include custom vocabulary in initial_prompt."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"dummy audio")

        mock_segment = Mock()
        mock_segment.text = "Using TensorFlow"
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], None)

        config = {
            "language": "en",
            "initial_prompt": "Use punctuation.",
            "custom_vocabulary": ["TensorFlow", "Kubernetes"],
            "translation_enabled": False,
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": []
        }

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config
        )

        assert success
        # Verify initial_prompt was passed with vocabulary
        call_args = mock_model.transcribe.call_args
        assert "initial_prompt" in call_args[1]
        assert "TensorFlow" in call_args[1]["initial_prompt"]
        assert "Kubernetes" in call_args[1]["initial_prompt"]

    def test_transcribe_translation_mode(self, tmp_path):
        """Should use translate task when translation enabled."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy")

        mock_segment = Mock()
        mock_segment.text = "Translated text"
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], None)

        config = {
            "language": "en",
            "initial_prompt": "",
            "custom_vocabulary": [],
            "translation_enabled": True,
            "translation_source_language": "es",
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": []
        }

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config
        )

        assert success
        # Verify task=translate was used
        call_args = mock_model.transcribe.call_args
        assert call_args[1]["task"] == "translate"
        assert call_args[1]["language"] == "es"

    def test_transcribe_progress_callback(self, tmp_path):
        """Should call progress callback during transcription."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"dummy")

        mock_segment = Mock()
        mock_segment.text = "Test"
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], None)

        config = {
            "language": "en",
            "initial_prompt": "",
            "custom_vocabulary": [],
            "translation_enabled": False,
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": []
        }

        progress_calls = []

        def progress_callback(progress, status):
            progress_calls.append((progress, status))

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config, progress_callback
        )

        assert success
        assert len(progress_calls) > 0
        # Should have "Complete!" as final status
        assert any("Complete" in status for _, status in progress_calls)

    def test_transcribe_multiple_segments(self, tmp_path):
        """Should combine multiple segments into single transcription."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"dummy")

        # Multiple segments
        seg1 = Mock()
        seg1.text = "First segment"
        seg2 = Mock()
        seg2.text = "Second segment"
        seg3 = Mock()
        seg3.text = "Third segment"

        mock_model = Mock()
        mock_model.transcribe.return_value = ([seg1, seg2, seg3], None)

        config = {
            "language": "en",
            "initial_prompt": "",
            "custom_vocabulary": [],
            "translation_enabled": False,
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": []
        }

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config
        )

        assert success
        assert "First segment" in text
        assert "Second segment" in text
        assert "Third segment" in text

    def test_transcribe_applies_custom_dictionary(self, tmp_path):
        """Should apply custom dictionary replacements."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"dummy")

        mock_segment = Mock()
        mock_segment.text = "Hello world with abbrev"
        mock_model = Mock()
        mock_model.transcribe.return_value = ([mock_segment], None)

        config = {
            "language": "en",
            "initial_prompt": "",
            "custom_vocabulary": [],
            "translation_enabled": False,
            "voice_commands_enabled": False,
            "filler_removal_enabled": False,
            "custom_dictionary": [
                {"from": "abbrev", "to": "abbreviation", "case_sensitive": False}
            ]
        }

        text, success = file_transcription.transcribe_file(
            str(audio_file), mock_model, config
        )

        assert success
        # Custom dictionary should be applied
        assert "abbreviation" in text or "abbrev" in text


class TestSaveTranscription:
    """Tests for saving transcription to file."""

    def test_save_with_specified_location(self, tmp_path):
        """Should save to specified location."""
        text = "This is a test transcription."
        original_file = "interview.mp3"
        save_location = str(tmp_path)

        saved_path = file_transcription.save_transcription(
            text, original_file, save_location
        )

        assert saved_path is not None
        assert os.path.exists(saved_path)
        assert saved_path.endswith("_transcription.txt")

        # Verify content
        with open(saved_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == text

    def test_save_preserves_original_filename(self, tmp_path):
        """Should use original filename as base for transcription file."""
        text = "Test content"
        original_file = "/path/to/my_audio_file.mp3"
        save_location = str(tmp_path)

        saved_path = file_transcription.save_transcription(
            text, original_file, save_location
        )

        assert "my_audio_file" in saved_path
        assert saved_path.endswith("_transcription.txt")

    @patch('tkinter.filedialog.asksaveasfilename')
    def test_save_with_dialog(self, mock_dialog, tmp_path):
        """Should use file dialog when save_location is None."""
        save_path = str(tmp_path / "custom_name.txt")
        mock_dialog.return_value = save_path

        text = "Test transcription"
        original_file = "audio.mp3"

        result = file_transcription.save_transcription(
            text, original_file, None
        )

        assert result == save_path
        mock_dialog.assert_called_once()

    @patch('tkinter.filedialog.asksaveasfilename')
    def test_save_dialog_cancelled(self, mock_dialog):
        """Should return None when user cancels save dialog."""
        mock_dialog.return_value = ""  # User cancelled

        text = "Test"
        original_file = "audio.mp3"

        result = file_transcription.save_transcription(
            text, original_file, None
        )

        assert result is None


class TestFileDuration:
    """Tests for file duration detection."""

    def test_get_file_duration_returns_none(self):
        """Duration detection returns None (not implemented yet)."""
        # This is a placeholder test since duration is not critical for Phase 3
        duration = file_transcription.get_file_duration("test.mp3")
        assert duration is None
