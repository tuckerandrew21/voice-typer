"""
Tests for AI cleanup functionality (Ollama integration).
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ai_cleanup


class TestOllamaConnection:
    """Tests for Ollama connection checking."""

    @patch('ai_cleanup.requests.get')
    def test_check_ollama_available_success(self, mock_get):
        """Should return True when Ollama is accessible."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert ai_cleanup.check_ollama_available() is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=2)

    @patch('ai_cleanup.requests.get')
    def test_check_ollama_available_connection_error(self, mock_get):
        """Should return False when connection fails."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        assert ai_cleanup.check_ollama_available() is False

    @patch('ai_cleanup.requests.get')
    def test_check_ollama_available_timeout(self, mock_get):
        """Should return False on timeout."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timed out")

        assert ai_cleanup.check_ollama_available() is False

    @patch('ai_cleanup.requests.get')
    def test_check_ollama_available_with_custom_url(self, mock_get):
        """Should use custom URL when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        ai_cleanup.check_ollama_available("http://custom:8080")
        mock_get.assert_called_with("http://custom:8080/api/tags", timeout=2)


class TestGetAvailableModels:
    """Tests for retrieving available Ollama models."""

    @patch('ai_cleanup.requests.get')
    def test_get_available_models_success(self, mock_get):
        """Should return list of model names."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "mistral:7b"},
                {"name": "phi:latest"}
            ]
        }
        mock_get.return_value = mock_response

        models = ai_cleanup.get_available_models()

        assert len(models) == 3
        assert "llama3.2:3b" in models
        assert "mistral:7b" in models
        assert "phi:latest" in models

    @patch('ai_cleanup.requests.get')
    def test_get_available_models_empty(self, mock_get):
        """Should return empty list when no models installed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_get.return_value = mock_response

        models = ai_cleanup.get_available_models()

        assert models == []

    @patch('ai_cleanup.requests.get')
    def test_get_available_models_connection_error(self, mock_get):
        """Should return empty list on connection error."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")

        models = ai_cleanup.get_available_models()

        assert models == []


class TestBuildCleanupPrompt:
    """Tests for prompt building logic."""

    def test_build_grammar_prompt(self):
        """Grammar mode should create grammar-focused prompt."""
        prompt = ai_cleanup._build_cleanup_prompt("test text", "grammar", "professional")

        assert "Fix any grammar" in prompt
        assert "test text" in prompt
        assert "Corrected:" in prompt

    def test_build_formality_prompt(self):
        """Formality mode should create formality-focused prompt."""
        prompt = ai_cleanup._build_cleanup_prompt("test text", "formality", "professional")

        assert "professional and polished" in prompt
        assert "test text" in prompt
        assert "Rewritten:" in prompt

    def test_build_both_prompt(self):
        """Both mode should create combined prompt."""
        prompt = ai_cleanup._build_cleanup_prompt("test text", "both", "formal")

        assert "grammar" in prompt
        assert "formal and academic" in prompt
        assert "test text" in prompt
        assert "Improved:" in prompt

    def test_build_formality_casual(self):
        """Casual formality level should be in prompt."""
        prompt = ai_cleanup._build_cleanup_prompt("test text", "formality", "casual")

        assert "casual and conversational" in prompt

    def test_build_formality_formal(self):
        """Formal formality level should be in prompt."""
        prompt = ai_cleanup._build_cleanup_prompt("test text", "formality", "formal")

        assert "formal and academic" in prompt


class TestCleanupText:
    """Tests for text cleanup functionality."""

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_success(self, mock_post):
        """Should return cleaned text on success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is cleaned text."}
        mock_post.return_value = mock_response

        result = ai_cleanup.cleanup_text(
            "this is test text",
            mode="grammar",
            model="llama3.2:3b"
        )

        assert result == "This is cleaned text."
        assert mock_post.called

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_with_formality(self, mock_post):
        """Should handle formality mode."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Formal version of text"}
        mock_post.return_value = mock_response

        result = ai_cleanup.cleanup_text(
            "casual text",
            mode="formality",
            formality_level="formal",
            model="llama3.2:3b"
        )

        assert result == "Formal version of text"

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_empty_input(self, mock_post):
        """Should return None for empty input."""
        result = ai_cleanup.cleanup_text("")

        assert result is None
        assert not mock_post.called

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_connection_error(self, mock_post):
        """Should return None on connection error."""
        import requests
        mock_post.side_effect = requests.RequestException("Connection failed")

        result = ai_cleanup.cleanup_text("test text")

        assert result is None

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_empty_response(self, mock_post):
        """Should return None if response is empty."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": ""}
        mock_post.return_value = mock_response

        result = ai_cleanup.cleanup_text("test text")

        assert result is None

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_with_custom_url(self, mock_post):
        """Should use custom Ollama URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "cleaned"}
        mock_post.return_value = mock_response

        ai_cleanup.cleanup_text("test", url="http://custom:8080")

        call_args = mock_post.call_args
        assert "http://custom:8080/api/generate" in call_args[0]

    @patch('ai_cleanup.requests.post')
    def test_cleanup_text_timeout_parameter(self, mock_post):
        """Should pass timeout parameter to request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "cleaned"}
        mock_post.return_value = mock_response

        ai_cleanup.cleanup_text("test", timeout=10)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 10


class TestTestOllamaConnection:
    """Tests for Ollama connection testing."""

    @patch('ai_cleanup.check_ollama_available')
    def test_test_ollama_not_running(self, mock_check):
        """Should return False when Ollama not running."""
        mock_check.return_value = False

        success, message = ai_cleanup.test_ollama_connection("llama3.2:3b")

        assert success is False
        assert "not running" in message

    @patch('ai_cleanup.check_ollama_available')
    @patch('ai_cleanup.get_available_models')
    def test_test_ollama_no_models(self, mock_get_models, mock_check):
        """Should return False when no models available."""
        mock_check.return_value = True
        mock_get_models.return_value = []

        success, message = ai_cleanup.test_ollama_connection("llama3.2:3b")

        assert success is False
        assert "Could not retrieve" in message

    @patch('ai_cleanup.check_ollama_available')
    @patch('ai_cleanup.get_available_models')
    def test_test_ollama_model_not_installed(self, mock_get_models, mock_check):
        """Should return False when requested model not installed."""
        mock_check.return_value = True
        mock_get_models.return_value = ["mistral:7b", "phi:latest"]

        success, message = ai_cleanup.test_ollama_connection("llama3.2:3b")

        assert success is False
        assert "not installed" in message
        assert "llama3.2:3b" in message

    @patch('ai_cleanup.check_ollama_available')
    @patch('ai_cleanup.get_available_models')
    @patch('ai_cleanup.cleanup_text')
    def test_test_ollama_success(self, mock_cleanup, mock_get_models, mock_check):
        """Should return True when test succeeds."""
        mock_check.return_value = True
        mock_get_models.return_value = ["llama3.2:3b", "mistral:7b"]
        mock_cleanup.return_value = "test response"

        success, message = ai_cleanup.test_ollama_connection("llama3.2:3b")

        assert success is True
        assert "successful" in message.lower()

    @patch('ai_cleanup.check_ollama_available')
    @patch('ai_cleanup.get_available_models')
    @patch('ai_cleanup.cleanup_text')
    def test_test_ollama_model_no_response(self, mock_cleanup, mock_get_models, mock_check):
        """Should return False when model doesn't respond."""
        mock_check.return_value = True
        mock_get_models.return_value = ["llama3.2:3b"]
        mock_cleanup.return_value = None

        success, message = ai_cleanup.test_ollama_connection("llama3.2:3b")

        assert success is False
        assert "did not respond correctly" in message


class TestOfflineVerification:
    """Tests to ensure no external API calls."""

    @patch('ai_cleanup.requests.post')
    @patch('ai_cleanup.requests.get')
    def test_only_local_requests(self, mock_get, mock_post):
        """Should only make requests to localhost."""
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"models": [{"name": "llama3.2:3b"}]}
        mock_get.return_value = mock_get_response

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"response": "cleaned"}
        mock_post.return_value = mock_post_response

        # Check connection
        ai_cleanup.check_ollama_available()
        assert "localhost" in mock_get.call_args[0][0]

        # Get models
        ai_cleanup.get_available_models()
        assert "localhost" in mock_get.call_args[0][0]

        # Cleanup text
        ai_cleanup.cleanup_text("test")
        assert "localhost" in mock_post.call_args[0][0]

    def test_no_cloud_api_references(self):
        """Module should not contain references to cloud APIs."""
        import inspect
        source = inspect.getsource(ai_cleanup)

        # Check for common cloud API domains
        cloud_apis = ["openai.com", "anthropic.com", "api.cloud"]
        for api in cloud_apis:
            assert api not in source.lower(), f"Found reference to cloud API: {api}"
