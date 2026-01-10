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
