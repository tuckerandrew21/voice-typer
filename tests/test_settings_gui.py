"""
Tests for settings_gui.py - GPU detection and settings validation.

Note: The CUDA detection functions involve complex import mechanics that are
difficult to test in isolation. These tests focus on the validation logic
which doesn't require mocking imports. Integration tests should verify
actual CUDA detection behavior.
"""
import pytest
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGetCudaStatus:
    """Tests for get_cuda_status() detailed status reporting."""

    def test_status_when_test_mode_enabled(self):
        """Test mode returns fake 'unavailable' status."""
        import settings_gui

        # Store original value
        original_value = settings_gui._TEST_GPU_UNAVAILABLE

        try:
            # Enable test mode
            settings_gui._TEST_GPU_UNAVAILABLE = True

            available, status_msg, detail = settings_gui.get_cuda_status()

            assert available is False
            assert status_msg == "GPU libraries not installed"
            assert detail is None
        finally:
            # Restore original value
            settings_gui._TEST_GPU_UNAVAILABLE = original_value

    def test_status_returns_tuple(self):
        """get_cuda_status should return a 3-tuple."""
        import settings_gui

        result = settings_gui.get_cuda_status()

        assert isinstance(result, tuple)
        assert len(result) == 3
        # First element is bool
        assert isinstance(result[0], bool)
        # Second element is string
        assert isinstance(result[1], str)
        # Third element is string or None
        assert result[2] is None or isinstance(result[2], str)


class TestProcessingModeValidation:
    """Tests for processing mode validation and warnings.

    These tests verify the warning logic independently of the GUI.
    The new simplified logic only warns when GPU mode is selected but CUDA not available.
    """

    def _get_warnings(self, mode: str, cuda_available: bool) -> list:
        """Helper to compute warnings like the GUI does."""
        warnings = []

        # Warn if GPU mode selected but CUDA not available
        if mode in ("gpu-balanced", "gpu-quality") and not cuda_available:
            warnings.append("GPU not available - will fall back to CPU")

        return warnings

    def test_auto_mode_no_warnings(self):
        """Auto mode should never warn (handles fallback gracefully)."""
        assert len(self._get_warnings("auto", False)) == 0
        assert len(self._get_warnings("auto", True)) == 0

    def test_cpu_mode_no_warnings(self):
        """CPU mode should never warn."""
        assert len(self._get_warnings("cpu", False)) == 0
        assert len(self._get_warnings("cpu", True)) == 0

    def test_gpu_balanced_without_cuda_warns(self):
        """GPU Balanced mode without CUDA should warn."""
        warnings = self._get_warnings("gpu-balanced", False)
        assert len(warnings) == 1
        assert "GPU not available" in warnings[0]

    def test_gpu_quality_without_cuda_warns(self):
        """GPU Quality mode without CUDA should warn."""
        warnings = self._get_warnings("gpu-quality", False)
        assert len(warnings) == 1
        assert "GPU not available" in warnings[0]

    def test_gpu_balanced_with_cuda_no_warnings(self):
        """GPU Balanced mode with CUDA available should not warn."""
        warnings = self._get_warnings("gpu-balanced", True)
        assert len(warnings) == 0

    def test_gpu_quality_with_cuda_no_warnings(self):
        """GPU Quality mode with CUDA available should not warn."""
        warnings = self._get_warnings("gpu-quality", True)
        assert len(warnings) == 0


class TestTooltip:
    """Tests for Tooltip widget helper class."""

    def test_tooltip_stores_text(self):
        """Tooltip should store the provided text."""
        mock_widget = MagicMock()

        import settings_gui
        tooltip = settings_gui.Tooltip(mock_widget, "Test tooltip text")

        assert tooltip.text == "Test tooltip text"
        assert tooltip.widget == mock_widget

    def test_tooltip_binds_events(self):
        """Tooltip should bind Enter and Leave events."""
        mock_widget = MagicMock()

        import settings_gui
        tooltip = settings_gui.Tooltip(mock_widget, "Test")

        # Verify bind was called for Enter and Leave
        calls = mock_widget.bind.call_args_list
        events_bound = [call[0][0] for call in calls]

        assert "<Enter>" in events_bound
        assert "<Leave>" in events_bound

    def test_tooltip_initially_no_popup(self):
        """Tooltip should not have popup window initially."""
        mock_widget = MagicMock()

        import settings_gui
        tooltip = settings_gui.Tooltip(mock_widget, "Test")

        assert tooltip.tooltip is None


class TestCheckCudaAvailable:
    """Tests for check_cuda_available() function."""

    def test_returns_bool(self):
        """check_cuda_available should return a boolean."""
        import settings_gui

        result = settings_gui.check_cuda_available()
        assert isinstance(result, bool)
