"""
AI-powered text cleanup using local Ollama LLM.
Provides grammar fixes and formality adjustments while staying 100% offline.
"""
import requests
from typing import Optional, List


def check_ollama_available(url: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama is running and accessible.

    Args:
        url: Ollama API URL

    Returns:
        True if Ollama is reachable, False otherwise
    """
    try:
        response = requests.get(f"{url}/api/tags", timeout=2)
        return response.status_code == 200
    except (requests.RequestException, Exception):
        return False


def get_available_models(url: str = "http://localhost:11434") -> List[str]:
    """
    Query Ollama for list of installed models.

    Args:
        url: Ollama API URL

    Returns:
        List of model names, empty list if Ollama unavailable
    """
    try:
        response = requests.get(f"{url}/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get("models", []):
                name = model.get("name", "")
                if name:
                    models.append(name)
            return models
        return []
    except (requests.RequestException, Exception):
        return []


def _build_cleanup_prompt(text: str, mode: str, formality_level: str) -> str:
    """
    Build appropriate prompt for text cleanup.

    Args:
        text: Text to clean up
        mode: "grammar", "formality", or "both"
        formality_level: "casual", "professional", or "formal"

    Returns:
        Formatted prompt for Ollama
    """
    if mode == "grammar":
        prompt = f"""Fix any grammar, spelling, and punctuation errors in the following text. Preserve the original tone and style. Only output the corrected text, nothing else.

Text: {text}

Corrected:"""
    elif mode == "formality":
        level_desc = {
            "casual": "casual and conversational",
            "professional": "professional and polished",
            "formal": "formal and academic"
        }.get(formality_level, "professional")

        prompt = f"""Rewrite the following text to be {level_desc} while preserving the core message. Only output the rewritten text, nothing else.

Text: {text}

Rewritten:"""
    else:  # both
        level_desc = {
            "casual": "casual and conversational",
            "professional": "professional and polished",
            "formal": "formal and academic"
        }.get(formality_level, "professional")

        prompt = f"""Fix any grammar, spelling, and punctuation errors, and rewrite to be {level_desc}. Preserve the core message. Only output the improved text, nothing else.

Text: {text}

Improved:"""

    return prompt


def cleanup_text(
    text: str,
    mode: str = "grammar",
    formality_level: str = "professional",
    model: str = "llama3.2:3b",
    url: str = "http://localhost:11434",
    timeout: int = 30
) -> Optional[str]:
    """
    Send text to Ollama for cleanup and return improved version.

    Args:
        text: Text to clean up
        mode: "grammar", "formality", or "both"
        formality_level: "casual", "professional", or "formal"
        model: Ollama model to use
        url: Ollama API URL
        timeout: Request timeout in seconds

    Returns:
        Cleaned up text, or None if cleanup failed
    """
    if not text or not text.strip():
        return None

    try:
        # Build prompt
        prompt = _build_cleanup_prompt(text, mode, formality_level)

        # Send request to Ollama
        response = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent output
                    "top_p": 0.9,
                }
            },
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            cleaned = data.get("response", "").strip()

            # Basic validation - ensure we got something back
            if cleaned and len(cleaned) > 0:
                return cleaned
            else:
                return None
        else:
            return None

    except (requests.RequestException, Exception):
        return None


def test_ollama_connection(model: str, url: str = "http://localhost:11434") -> tuple[bool, str]:
    """
    Test connection to Ollama and verify model availability.

    Args:
        model: Model name to test
        url: Ollama API URL

    Returns:
        Tuple of (success, message)
    """
    # Check if Ollama is running
    if not check_ollama_available(url):
        return False, "Ollama is not running or not accessible."

    # Check if model is available
    models = get_available_models(url)
    if not models:
        return False, "Could not retrieve model list from Ollama."

    # Check if requested model is installed
    model_base = model.split(":")[0]  # Handle versions like "llama3.2:3b"
    if not any(model_base in m for m in models):
        return False, f"Model '{model}' is not installed. Available models: {', '.join(models)}"

    # Try a simple test
    test_result = cleanup_text(
        "test",
        mode="grammar",
        model=model,
        url=url,
        timeout=10
    )

    if test_result is not None:
        return True, f"Connection successful! Using model: {model}"
    else:
        return False, "Connection succeeded but model did not respond correctly."
