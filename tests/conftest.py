"""
Shared pytest fixtures for MurmurTone tests.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_cuda_available(mocker):
    """Mock CUDA as available with a test GPU."""
    mock_ct2 = mocker.patch('settings_gui.ctranslate2')
    mock_ct2.get_supported_compute_types.return_value = ['float16', 'float32', 'int8']

    mock_torch = mocker.patch('settings_gui.torch')
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.get_device_name.return_value = "NVIDIA GeForce RTX 3080"

    return mock_ct2, mock_torch


@pytest.fixture
def mock_cuda_unavailable(mocker):
    """Mock CUDA as completely unavailable."""
    mock_ct2 = mocker.patch('settings_gui.ctranslate2')
    mock_ct2.get_supported_compute_types.side_effect = Exception("CUDA not available")

    mock_torch = mocker.patch('settings_gui.torch')
    mock_torch.cuda.is_available.return_value = False

    return mock_ct2, mock_torch


@pytest.fixture
def mock_cuda_libs_missing(mocker):
    """Mock scenario where CUDA libraries are not installed."""
    # Make ctranslate2 import fail
    mocker.patch.dict('sys.modules', {'ctranslate2': None})

    # Make torch import fail
    mocker.patch.dict('sys.modules', {'torch': None})

    return None


@pytest.fixture
def temp_config(tmp_path, mocker):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "murmurtone_settings.json"

    # Mock the config path
    mocker.patch('config.CONFIG_FILE', str(config_file))

    return config_file
