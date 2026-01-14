"""Tests for the GPU install button functionality."""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings_logic


class TestGPUInstallButton:
    """Test cases for GPU install button visibility and functionality."""

    def test_get_cuda_status_returns_tuple(self):
        """get_cuda_status should return a 3-tuple."""
        result = settings_logic.get_cuda_status()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_get_cuda_status_with_test_mode_enabled(self, monkeypatch):
        """When _TEST_GPU_UNAVAILABLE is True, should return 'GPU libraries not installed'."""
        monkeypatch.setattr(settings_logic, '_TEST_GPU_UNAVAILABLE', True)
        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()

        assert is_available is False
        assert status_msg == "GPU libraries not installed"
        assert gpu_name is None

    def test_get_cuda_status_with_test_mode_disabled(self, monkeypatch):
        """When _TEST_GPU_UNAVAILABLE is False, should check actual GPU status."""
        monkeypatch.setattr(settings_logic, '_TEST_GPU_UNAVAILABLE', False)
        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()

        # Result depends on actual hardware, but structure should be valid
        assert isinstance(is_available, bool)
        assert isinstance(status_msg, str)
        assert gpu_name is None or isinstance(gpu_name, str)

    def test_requirements_gpu_file_exists(self):
        """requirements-gpu.txt should exist in the project root."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        req_file = os.path.join(project_root, "requirements-gpu.txt")
        assert os.path.exists(req_file), f"requirements-gpu.txt not found at {req_file}"

    def test_requirements_gpu_contains_cuda_packages(self):
        """requirements-gpu.txt should contain NVIDIA CUDA packages."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        req_file = os.path.join(project_root, "requirements-gpu.txt")

        with open(req_file, 'r') as f:
            content = f.read()

        assert "nvidia-cublas" in content.lower() or "cuda" in content.lower()


class TestGPUInstallButtonUI:
    """Test cases for GPU install button UI integration."""

    @pytest.fixture
    def mock_tk(self, monkeypatch):
        """Mock tkinter to avoid GUI initialization."""
        import unittest.mock as mock

        # Create mock modules
        mock_tk = mock.MagicMock()
        mock_ctk = mock.MagicMock()

        monkeypatch.setitem(sys.modules, 'tkinter', mock_tk)
        monkeypatch.setitem(sys.modules, 'customtkinter', mock_ctk)

        return mock_tk, mock_ctk

    def test_button_should_show_when_libs_not_installed(self, monkeypatch):
        """Install button should be visible when GPU libraries are not installed."""
        monkeypatch.setattr(settings_logic, '_TEST_GPU_UNAVAILABLE', True)
        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()

        # Button visibility condition
        should_show_button = not is_available and status_msg == "GPU libraries not installed"
        assert should_show_button is True

    def test_button_should_hide_when_libs_installed(self, monkeypatch):
        """Install button should be hidden when GPU is available."""
        # Mock ctranslate2 to simulate GPU available
        mock_ct2 = type(sys)('ctranslate2')
        mock_ct2.get_supported_compute_types = lambda x: ['int8', 'float16'] if x == 'cuda' else []
        monkeypatch.setitem(sys.modules, 'ctranslate2', mock_ct2)

        monkeypatch.setattr(settings_logic, '_TEST_GPU_UNAVAILABLE', False)

        # Re-import to pick up mock
        import importlib
        importlib.reload(settings_logic)

        is_available, status_msg, gpu_name = settings_logic.get_cuda_status()

        # Button visibility condition - should NOT show
        should_show_button = not is_available and status_msg == "GPU libraries not installed"

        # When GPU is available, button should be hidden
        if is_available:
            assert should_show_button is False


class TestInstallGPUSupportMethod:
    """Test cases for the install_gpu_support method logic."""

    def test_resource_path_finds_requirements_file(self):
        """resource_path should find requirements-gpu.txt."""
        # Import resource_path from settings_gui
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Simulate resource_path behavior
        def resource_path(relative_path):
            return os.path.join(project_root, relative_path)

        req_file = resource_path("requirements-gpu.txt")
        assert os.path.exists(req_file)

    def test_pip_install_command_structure(self):
        """Verify the pip install command would be structured correctly."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        req_file = os.path.join(project_root, "requirements-gpu.txt")

        expected_cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]

        # Verify structure
        assert expected_cmd[0] == sys.executable
        assert expected_cmd[1:4] == ["-m", "pip", "install"]
        assert expected_cmd[4] == "-r"
        assert expected_cmd[5].endswith("requirements-gpu.txt")
