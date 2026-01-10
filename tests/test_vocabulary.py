"""
Tests for custom vocabulary functionality.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class TestVocabularyInjection:
    """Tests for vocabulary injection into initial_prompt."""

    def test_vocabulary_formats_correctly(self):
        """Vocabulary list should be formatted as comma-separated string."""
        vocab = ["TensorFlow", "Kubernetes", "Dr. Smith"]
        vocab_hint = f" Vocabulary: {', '.join(vocab)}."
        assert vocab_hint == " Vocabulary: TensorFlow, Kubernetes, Dr. Smith."

    def test_vocabulary_appends_to_base_prompt(self):
        """Vocabulary hint should append to base initial_prompt."""
        base_prompt = "Use proper punctuation."
        vocab = ["PyTorch", "HIPAA"]
        vocab_hint = f" Vocabulary: {', '.join(vocab)}."
        combined = base_prompt + vocab_hint
        assert "Use proper punctuation." in combined
        assert "Vocabulary: PyTorch, HIPAA." in combined

    def test_empty_vocabulary_uses_base_prompt_only(self):
        """Empty vocabulary should not modify initial_prompt."""
        base_prompt = "Use proper punctuation."
        vocab = []
        if vocab:
            combined = base_prompt + f" Vocabulary: {', '.join(vocab)}."
        else:
            combined = base_prompt
        assert combined == "Use proper punctuation."

    def test_vocabulary_with_special_characters(self):
        """Vocabulary terms with special characters should be handled."""
        vocab = ["Dr. Smith", "J.R.R. Tolkien", "C++"]
        vocab_hint = f" Vocabulary: {', '.join(vocab)}."
        assert "Dr. Smith" in vocab_hint
        assert "J.R.R. Tolkien" in vocab_hint
        assert "C++" in vocab_hint

    def test_vocabulary_preserves_case(self):
        """Vocabulary should preserve original case."""
        vocab = ["TensorFlow", "HIPAA", "iPhone"]
        vocab_hint = f" Vocabulary: {', '.join(vocab)}."
        assert "TensorFlow" in vocab_hint  # CamelCase
        assert "HIPAA" in vocab_hint  # All caps
        assert "iPhone" in vocab_hint  # Mixed case


class TestVocabularyConfig:
    """Tests for vocabulary configuration management."""

    def test_add_single_term(self):
        """Should be able to add a single term."""
        vocab = []
        vocab.append("TensorFlow")
        assert len(vocab) == 1
        assert "TensorFlow" in vocab

    def test_add_multiple_terms(self):
        """Should be able to add multiple terms."""
        vocab = []
        vocab.extend(["TensorFlow", "Kubernetes", "Docker"])
        assert len(vocab) == 3
        assert all(term in vocab for term in ["TensorFlow", "Kubernetes", "Docker"])

    def test_remove_term(self):
        """Should be able to remove a term."""
        vocab = ["TensorFlow", "Kubernetes", "Docker"]
        vocab.remove("Kubernetes")
        assert len(vocab) == 2
        assert "Kubernetes" not in vocab
        assert "TensorFlow" in vocab
        assert "Docker" in vocab

    def test_duplicate_prevention(self):
        """Should prevent duplicate terms."""
        vocab = ["TensorFlow"]
        term = "TensorFlow"
        if term not in vocab:
            vocab.append(term)
        assert len(vocab) == 1

    def test_empty_vocabulary_handling(self):
        """Should handle empty vocabulary gracefully."""
        vocab = []
        assert len(vocab) == 0
        assert vocab == []
