"""
Tests for stats.py - Usage statistics tracking.
"""
import pytest
import sys
import os
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stats


class TestCalculateTimeSaved:
    """Tests for calculate_time_saved function."""

    def test_returns_tuple(self):
        """calculate_time_saved should return (minutes, hours) tuple."""
        result = stats.calculate_time_saved(1000)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_zero_characters_returns_zero(self):
        """Zero characters should return zero time saved."""
        minutes, hours = stats.calculate_time_saved(0)
        assert minutes == 0
        assert hours == 0

    def test_positive_characters_returns_positive_time(self):
        """Positive characters should return positive time saved."""
        minutes, hours = stats.calculate_time_saved(1000)
        assert minutes > 0
        assert hours > 0

    def test_hours_equals_minutes_divided_by_60(self):
        """Hours should equal minutes / 60."""
        minutes, hours = stats.calculate_time_saved(5000)
        assert hours == minutes / 60

    def test_time_saved_increases_with_characters(self):
        """More characters should mean more time saved."""
        minutes_1000, _ = stats.calculate_time_saved(1000)
        minutes_5000, _ = stats.calculate_time_saved(5000)
        assert minutes_5000 > minutes_1000


class TestFormatTimeSaved:
    """Tests for format_time_saved function."""

    def test_less_than_one_minute(self):
        """Less than 1 minute should return '< 1 minute'."""
        result = stats.format_time_saved(0.5)
        assert "< 1 minute" in result

    def test_one_minute(self):
        """One minute should be singular."""
        result = stats.format_time_saved(1)
        assert "1 minute" in result
        assert "minutes" not in result

    def test_multiple_minutes(self):
        """Multiple minutes should be plural."""
        result = stats.format_time_saved(30)
        assert "minute" in result

    def test_one_hour_range(self):
        """60+ minutes should show hours."""
        result = stats.format_time_saved(90)
        assert "hour" in result

    def test_multiple_hours(self):
        """Large values should show hours."""
        result = stats.format_time_saved(120)
        assert "hour" in result

    def test_days_for_large_values(self):
        """Very large values (24+ hours) should show days."""
        result = stats.format_time_saved(24 * 60 + 1)  # Just over 24 hours
        assert "day" in result


class TestLoadStats:
    """Tests for load_stats function."""

    def test_returns_dict(self):
        """load_stats should return a dictionary."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert isinstance(result, dict)

    def test_has_total_transcriptions(self):
        """Stats dict should have total_transcriptions key."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert "total_transcriptions" in result

    def test_has_total_characters(self):
        """Stats dict should have total_characters key."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert "total_characters" in result

    def test_has_total_words(self):
        """Stats dict should have total_words key."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert "total_words" in result

    def test_has_daily_stats(self):
        """Stats dict should have daily_stats key."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert "daily_stats" in result
            assert isinstance(result["daily_stats"], dict)

    def test_defaults_to_zero(self):
        """Default stats should be zero."""
        with patch('stats.os.path.exists', return_value=False):
            result = stats.load_stats()
            assert result["total_transcriptions"] == 0
            assert result["total_characters"] == 0


class TestGetStatsSummary:
    """Tests for get_stats_summary function."""

    def test_returns_dict(self):
        """get_stats_summary should return a dictionary."""
        with patch('stats.load_stats') as mock_load:
            mock_load.return_value = {
                "total_transcriptions": 10,
                "total_characters": 500,
                "total_words": 100,
                "first_use_date": "2024-01-01",
                "daily_stats": {}
            }
            result = stats.get_stats_summary()
            assert isinstance(result, dict)

    def test_has_minutes_saved(self):
        """Summary should include minutes_saved."""
        with patch('stats.load_stats') as mock_load:
            mock_load.return_value = {
                "total_transcriptions": 10,
                "total_characters": 500,
                "total_words": 100,
                "first_use_date": "2024-01-01",
                "daily_stats": {}
            }
            result = stats.get_stats_summary()
            assert "minutes_saved" in result

    def test_has_hours_saved(self):
        """Summary should include hours_saved."""
        with patch('stats.load_stats') as mock_load:
            mock_load.return_value = {
                "total_transcriptions": 10,
                "total_characters": 500,
                "total_words": 100,
                "first_use_date": "2024-01-01",
                "daily_stats": {}
            }
            result = stats.get_stats_summary()
            assert "hours_saved" in result


class TestRecordTranscription:
    """Tests for record_transcription function."""

    def test_empty_text_does_nothing(self):
        """Empty text should not record anything."""
        with patch('stats.load_stats') as mock_load, \
             patch('stats.save_stats') as mock_save:
            stats.record_transcription("")
            mock_save.assert_not_called()

    def test_none_text_does_nothing(self):
        """None text should not record anything."""
        with patch('stats.load_stats') as mock_load, \
             patch('stats.save_stats') as mock_save:
            stats.record_transcription(None)
            mock_save.assert_not_called()

    def test_valid_text_increments_count(self):
        """Valid text should increment transcription count."""
        mock_stats = {
            "total_transcriptions": 5,
            "total_characters": 100,
            "total_words": 20,
            "first_use_date": "2024-01-01",
            "daily_stats": {}
        }
        with patch('stats.load_stats', return_value=mock_stats), \
             patch('stats.save_stats') as mock_save:
            stats.record_transcription("hello world")
            # Check that save was called with incremented values
            saved_stats = mock_save.call_args[0][0]
            assert saved_stats["total_transcriptions"] == 6

    def test_valid_text_adds_characters(self):
        """Valid text should add to total characters."""
        mock_stats = {
            "total_transcriptions": 0,
            "total_characters": 0,
            "total_words": 0,
            "first_use_date": None,
            "daily_stats": {}
        }
        with patch('stats.load_stats', return_value=mock_stats), \
             patch('stats.save_stats') as mock_save:
            stats.record_transcription("hello")
            saved_stats = mock_save.call_args[0][0]
            assert saved_stats["total_characters"] == 5


class TestStatsConstants:
    """Tests for stats module constants."""

    def test_typing_chars_per_min_positive(self):
        """TYPING_CHARS_PER_MIN should be positive."""
        assert stats.TYPING_CHARS_PER_MIN > 0

    def test_speech_chars_per_min_positive(self):
        """SPEECH_CHARS_PER_MIN should be positive."""
        assert stats.SPEECH_CHARS_PER_MIN > 0

    def test_speech_faster_than_typing(self):
        """Speech should be faster than typing (more chars per min)."""
        assert stats.SPEECH_CHARS_PER_MIN > stats.TYPING_CHARS_PER_MIN
