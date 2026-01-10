"""Tests for text_processor.py voice commands."""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import text_processor


class TestActionCommands:
    """Tests for ACTION_COMMANDS (keyboard shortcuts triggered by voice)."""

    def test_copy_command(self):
        """'copy' should trigger ctrl+c."""
        text, should_scratch, actions = text_processor.process_voice_commands("copy")
        assert "ctrl+c" in actions
        assert should_scratch is False

    def test_copy_that_command(self):
        """'copy that' should trigger ctrl+c."""
        text, should_scratch, actions = text_processor.process_voice_commands("copy that")
        assert "ctrl+c" in actions

    def test_paste_command(self):
        """'paste' should trigger ctrl+v."""
        text, should_scratch, actions = text_processor.process_voice_commands("paste")
        assert "ctrl+v" in actions

    def test_paste_that_command(self):
        """'paste that' should trigger ctrl+v."""
        text, should_scratch, actions = text_processor.process_voice_commands("paste that")
        assert "ctrl+v" in actions

    def test_cut_command(self):
        """'cut' should trigger ctrl+x."""
        text, should_scratch, actions = text_processor.process_voice_commands("cut")
        assert "ctrl+x" in actions

    def test_cut_that_command(self):
        """'cut that' should trigger ctrl+x."""
        text, should_scratch, actions = text_processor.process_voice_commands("cut that")
        assert "ctrl+x" in actions

    def test_select_all_command(self):
        """'select all' should trigger ctrl+a."""
        text, should_scratch, actions = text_processor.process_voice_commands("select all")
        assert "ctrl+a" in actions

    def test_undo_command(self):
        """'undo' should trigger ctrl+z."""
        text, should_scratch, actions = text_processor.process_voice_commands("undo")
        assert "ctrl+z" in actions

    def test_redo_command(self):
        """'redo' should trigger ctrl+y."""
        text, should_scratch, actions = text_processor.process_voice_commands("redo")
        assert "ctrl+y" in actions


class TestPunctuationCommands:
    """Tests for punctuation voice commands."""

    def test_period_command(self):
        """'period' should become '.'"""
        text, _, _ = text_processor.process_voice_commands("hello period")
        assert "." in text

    def test_comma_command(self):
        """'comma' should become ','"""
        text, _, _ = text_processor.process_voice_commands("hello comma world")
        assert "," in text

    def test_question_mark_command(self):
        """'question mark' should become '?'"""
        text, _, _ = text_processor.process_voice_commands("what question mark")
        assert "?" in text


class TestStructureCommands:
    """Tests for structure voice commands."""

    def test_new_line_command(self):
        """'new line' should become newline character."""
        text, _, _ = text_processor.process_voice_commands("hello new line world")
        assert "\n" in text

    def test_new_paragraph_command(self):
        """'new paragraph' should become double newline."""
        text, _, _ = text_processor.process_voice_commands("hello new paragraph world")
        assert "\n\n" in text


class TestEditingCommands:
    """Tests for editing voice commands."""

    def test_scratch_that_sets_flag(self):
        """'scratch that' should set should_scratch flag."""
        text, should_scratch, _ = text_processor.process_voice_commands("hello scratch that")
        assert should_scratch is True

    def test_delete_that_sets_flag(self):
        """'delete that' should set should_scratch flag."""
        text, should_scratch, _ = text_processor.process_voice_commands("hello delete that")
        assert should_scratch is True


class TestMixedCommands:
    """Tests for mixing regular text with commands."""

    def test_text_with_action_command(self):
        """Multi-word action command in text should be extracted."""
        text, _, actions = text_processor.process_voice_commands("please select all the text")
        assert "ctrl+a" in actions

    def test_select_all_with_copy_that(self):
        """Multi-word commands should work together."""
        text, _, actions = text_processor.process_voice_commands("select all copy that")
        assert "ctrl+a" in actions
        assert "ctrl+c" in actions


class TestStandaloneCommands:
    """Tests for standalone-only command behavior."""

    def test_paste_standalone_triggers(self):
        """'paste' alone should trigger ctrl+v."""
        text, _, actions = text_processor.process_voice_commands("paste")
        assert "ctrl+v" in actions

    def test_paste_in_sentence_does_not_trigger(self):
        """'paste' in a sentence should NOT trigger (prevents mishearing issues)."""
        text, _, actions = text_processor.process_voice_commands("I want peace and quiet")
        assert "ctrl+v" not in actions
        assert "peace" in text.lower()

    def test_copy_standalone_triggers(self):
        """'copy' alone should trigger ctrl+c."""
        text, _, actions = text_processor.process_voice_commands("copy")
        assert "ctrl+c" in actions

    def test_copy_in_sentence_does_not_trigger(self):
        """'copy' in a sentence should NOT trigger."""
        text, _, actions = text_processor.process_voice_commands("make a copy of the file")
        assert "ctrl+c" not in actions

    def test_paste_that_still_works(self):
        """'paste that' (multi-word) should still trigger even in context."""
        text, _, actions = text_processor.process_voice_commands("now paste that here")
        assert "ctrl+v" in actions

    def test_copy_that_still_works(self):
        """'copy that' (multi-word) should still trigger even in context."""
        text, _, actions = text_processor.process_voice_commands("please copy that")
        assert "ctrl+c" in actions


class TestFormattingCommands:
    """Tests for bold, italic, underline formatting commands."""

    def test_bold_command(self):
        """'bold' alone should trigger ctrl+b."""
        text, _, actions = text_processor.process_voice_commands("bold")
        assert "ctrl+b" in actions

    def test_bold_that_command(self):
        """'bold that' should trigger ctrl+b."""
        text, _, actions = text_processor.process_voice_commands("bold that")
        assert "ctrl+b" in actions

    def test_italic_command(self):
        """'italic' alone should trigger ctrl+i."""
        text, _, actions = text_processor.process_voice_commands("italic")
        assert "ctrl+i" in actions

    def test_italic_that_command(self):
        """'italic that' should trigger ctrl+i."""
        text, _, actions = text_processor.process_voice_commands("italic that")
        assert "ctrl+i" in actions

    def test_italics_command(self):
        """'italics' should trigger ctrl+i (alternate form)."""
        text, _, actions = text_processor.process_voice_commands("italics")
        assert "ctrl+i" in actions

    def test_underline_command(self):
        """'underline' alone should trigger ctrl+u."""
        text, _, actions = text_processor.process_voice_commands("underline")
        assert "ctrl+u" in actions

    def test_underline_that_command(self):
        """'underline that' should trigger ctrl+u."""
        text, _, actions = text_processor.process_voice_commands("underline that")
        assert "ctrl+u" in actions

    def test_bold_in_sentence_does_not_trigger(self):
        """'bold' in a sentence should NOT trigger formatting (standalone only)."""
        text, _, actions = text_processor.process_voice_commands("that was a bold move")
        assert "ctrl+b" not in actions
        assert "bold" in text.lower()

    def test_italic_in_sentence_does_not_trigger(self):
        """'italic' in a sentence should NOT trigger formatting."""
        text, _, actions = text_processor.process_voice_commands("the text was italic style")
        assert "ctrl+i" not in actions
        assert "italic" in text.lower()

    def test_underline_in_sentence_does_not_trigger(self):
        """'underline' in a sentence should NOT trigger formatting."""
        text, _, actions = text_processor.process_voice_commands("please underline this word")
        assert "ctrl+u" not in actions
        assert "underline" in text.lower()


class TestTranscriptionHistory:
    """Tests for TranscriptionHistory class."""

    def test_init_creates_empty_entries(self):
        """New history should have empty entries list."""
        history = text_processor.TranscriptionHistory(persist=False)
        assert isinstance(history.entries, list)
        assert len(history.entries) == 0

    def test_add_entry_increments_count(self):
        """Adding text should increment entry count."""
        history = text_processor.TranscriptionHistory(persist=False)
        initial = len(history.entries)
        history.add("test text")
        assert len(history.entries) == initial + 1

    def test_entry_has_required_fields(self):
        """Entry should have text, char_count, and timestamp."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("hello world")
        entry = history.entries[-1]
        assert "text" in entry
        assert "char_count" in entry
        assert "timestamp" in entry

    def test_entry_text_matches(self):
        """Entry text should match what was added."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("test message")
        assert history.entries[-1]["text"] == "test message"

    def test_entry_char_count_correct(self):
        """Entry char_count should match text length."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("hello")
        assert history.entries[-1]["char_count"] == 5

    def test_get_last_length_returns_char_count(self):
        """get_last_length should return last entry's character count."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("abc")
        assert history.get_last_length() == 3

    def test_get_last_length_empty_returns_zero(self):
        """get_last_length on empty history should return 0."""
        history = text_processor.TranscriptionHistory(persist=False)
        assert history.get_last_length() == 0

    def test_pop_last_removes_entry(self):
        """pop_last should remove and return the last entry."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("first")
        history.add("second")
        popped = history.pop_last()
        assert popped["text"] == "second"
        assert len(history.entries) == 1

    def test_pop_last_empty_returns_none(self):
        """pop_last on empty history should return None."""
        history = text_processor.TranscriptionHistory(persist=False)
        assert history.pop_last() is None

    def test_clear_removes_all_entries(self):
        """clear should remove all entries."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("one")
        history.add("two")
        history.clear()
        assert len(history.entries) == 0

    def test_max_entries_enforced(self):
        """History should not exceed max_entries."""
        history = text_processor.TranscriptionHistory(max_entries=3, persist=False)
        history.add("one")
        history.add("two")
        history.add("three")
        history.add("four")
        assert len(history.entries) == 3
        assert history.entries[0]["text"] == "two"  # First entry removed

    def test_empty_text_not_added(self):
        """Empty string should not be added to history."""
        history = text_processor.TranscriptionHistory(persist=False)
        history.add("")
        assert len(history.entries) == 0
