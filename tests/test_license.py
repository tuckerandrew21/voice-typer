"""Tests for license validation and trial management."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import license


@pytest.fixture
def fresh_config():
    """Config for a user who just installed (no trial started)."""
    return {
        "license_key": "",
        "license_status": "trial",
        "trial_started_date": None,
        "license_last_checked": None,
    }


@pytest.fixture
def active_trial_config():
    """Config for a user with an active trial (5 days elapsed)."""
    trial_start = datetime.now() - timedelta(days=5)
    return {
        "license_key": "",
        "license_status": "trial",
        "trial_started_date": trial_start.isoformat(),
        "license_last_checked": None,
    }


@pytest.fixture
def expired_trial_config():
    """Config for a user with an expired trial (20 days elapsed)."""
    trial_start = datetime.now() - timedelta(days=20)
    return {
        "license_key": "",
        "license_status": "trial",
        "trial_started_date": trial_start.isoformat(),
        "license_last_checked": None,
    }


@pytest.fixture
def licensed_config():
    """Config for a user with an active license."""
    return {
        "license_key": "ABC123-DEF456",
        "license_status": "active",
        "trial_started_date": None,
        "license_last_checked": datetime.now().isoformat(),
    }


def test_start_trial(fresh_config):
    """Test starting a trial for a new user."""
    updated = license.start_trial(fresh_config)

    assert updated["license_status"] == "trial"
    assert updated["trial_started_date"] is not None
    assert updated["license_key"] == ""

    # Parse timestamp to verify it's valid ISO format
    datetime.fromisoformat(updated["trial_started_date"])


def test_start_trial_idempotent(active_trial_config):
    """Test that start_trial doesn't reset an existing trial."""
    original_start = active_trial_config["trial_started_date"]
    updated = license.start_trial(active_trial_config)

    assert updated["trial_started_date"] == original_start  # Unchanged


def test_get_trial_days_remaining_fresh(fresh_config):
    """Test days remaining for a user who hasn't started trial yet."""
    days = license.get_trial_days_remaining(fresh_config)
    assert days == 14  # Full trial period


def test_get_trial_days_remaining_active(active_trial_config):
    """Test days remaining for an active trial."""
    days = license.get_trial_days_remaining(active_trial_config)
    assert days == 9  # 14 - 5 days elapsed


def test_get_trial_days_remaining_expired(expired_trial_config):
    """Test days remaining for an expired trial."""
    days = license.get_trial_days_remaining(expired_trial_config)
    assert days < 0  # Negative indicates expiration


def test_get_trial_days_remaining_licensed(licensed_config):
    """Test that licensed users don't have trial days."""
    days = license.get_trial_days_remaining(licensed_config)
    assert days is None  # No trial for licensed users


def test_is_trial_expired_fresh(fresh_config):
    """Test expiration check for fresh install."""
    assert not license.is_trial_expired(fresh_config)


def test_is_trial_expired_active(active_trial_config):
    """Test expiration check for active trial."""
    assert not license.is_trial_expired(active_trial_config)


def test_is_trial_expired_expired(expired_trial_config):
    """Test expiration check for expired trial."""
    assert license.is_trial_expired(expired_trial_config)


def test_is_trial_expired_licensed(licensed_config):
    """Test expiration check for licensed user."""
    assert not license.is_trial_expired(licensed_config)  # Licensed users aren't "expired"


def test_can_revalidate_offline_never_checked(fresh_config):
    """Test offline validation for a license never checked online."""
    assert not license.can_revalidate_offline(fresh_config)


def test_can_revalidate_offline_recent():
    """Test offline validation within grace period."""
    recent_check = datetime.now() - timedelta(days=3)
    config = {
        "license_key": "ABC123",
        "license_status": "active",
        "license_last_checked": recent_check.isoformat(),
    }
    assert license.can_revalidate_offline(config)


def test_can_revalidate_offline_old():
    """Test offline validation beyond grace period."""
    old_check = datetime.now() - timedelta(days=10)
    config = {
        "license_key": "ABC123",
        "license_status": "active",
        "license_last_checked": old_check.isoformat(),
    }
    assert not license.can_revalidate_offline(config)


@patch('license.requests.post')
def test_validate_license_key_valid(mock_post, fresh_config):
    """Test validating a valid license key."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"valid": True}
    mock_post.return_value = mock_response

    is_valid, error = license.validate_license_key("VALID-KEY-123", fresh_config)

    assert is_valid
    assert error == ""
    assert fresh_config["license_status"] == "active"
    assert fresh_config["license_key"] == "VALID-KEY-123"
    assert fresh_config["license_last_checked"] is not None


@patch('license.requests.post')
def test_validate_license_key_invalid(mock_post, fresh_config):
    """Test validating an invalid license key."""
    # Mock API response for invalid key
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"valid": False, "error": "Invalid license key"}
    mock_post.return_value = mock_response

    is_valid, error = license.validate_license_key("INVALID-KEY", fresh_config)

    assert not is_valid
    assert "Invalid license key" in error
    assert fresh_config["license_status"] != "active"


@patch('license.requests.post')
def test_validate_license_key_timeout(mock_post):
    """Test license validation with network timeout (within grace period)."""
    import requests
    mock_post.side_effect = requests.exceptions.Timeout()

    # Config with recent validation (within grace period)
    config = {
        "license_key": "ABC123",
        "license_status": "active",
        "license_last_checked": datetime.now().isoformat(),
    }

    is_valid, error = license.validate_license_key("ABC123", config)

    # Should allow usage with cached validation within grace period
    assert is_valid
    assert error == ""


@patch('license.requests.post')
def test_validate_license_key_connection_error(mock_post, fresh_config):
    """Test license validation with no internet connection."""
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError()

    is_valid, error = license.validate_license_key("TEST-KEY", fresh_config)

    assert not is_valid
    assert "No internet connection" in error or "Offline" in error


def test_get_license_status_info_fresh(fresh_config):
    """Test status info for a fresh install."""
    info = license.get_license_status_info(fresh_config)

    assert info["status"] == "trial"
    assert info["days_remaining"] == 14
    assert info["can_use_app"]
    assert not info["needs_purchase"]


def test_get_license_status_info_active_trial(active_trial_config):
    """Test status info for an active trial."""
    info = license.get_license_status_info(active_trial_config)

    assert info["status"] == "trial"
    assert info["days_remaining"] == 9
    assert "9 days remaining" in info["message"]
    assert info["can_use_app"]
    assert not info["needs_purchase"]


def test_get_license_status_info_expired_trial(expired_trial_config):
    """Test status info for an expired trial."""
    info = license.get_license_status_info(expired_trial_config)

    assert info["status"] == "expired"
    assert info["days_remaining"] < 0
    assert "expired" in info["message"].lower()
    assert not info["can_use_app"]
    assert info["needs_purchase"]


def test_get_license_status_info_licensed(licensed_config):
    """Test status info for a licensed user."""
    info = license.get_license_status_info(licensed_config)

    assert info["status"] == "active"
    assert info["days_remaining"] is None
    assert info["message"] == "Licensed"
    assert info["can_use_app"]
    assert not info["needs_purchase"]


def test_deactivate_license_active(licensed_config):
    """Test deactivating an active license."""
    updated = license.deactivate_license(licensed_config)

    assert updated["license_key"] == ""
    assert updated["license_last_checked"] is None
    assert updated["license_status"] == "trial"  # Return to trial if not expired


def test_deactivate_license_expired_trial(expired_trial_config):
    """Test deactivating when trial is expired."""
    # Give it a fake license first
    expired_trial_config["license_key"] = "FAKE-KEY"
    expired_trial_config["license_status"] = "active"

    updated = license.deactivate_license(expired_trial_config)

    assert updated["license_key"] == ""
    assert updated["license_status"] == "expired"  # Trial expired, can't return to trial
