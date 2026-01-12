"""
License validation and trial management for MurmurTone.
Handles 14-day free trial and LemonSqueezy license key validation.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


# LemonSqueezy API configuration
LEMONSQUEEZY_API_URL = "https://api.lemonsqueezy.com/v1/licenses/validate"
TRIAL_DURATION_DAYS = 14
OFFLINE_GRACE_PERIOD_DAYS = 7  # Allow 7 days offline before requiring revalidation


class LicenseStatus:
    """License status constants."""
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"


def start_trial(config: Dict) -> Dict:
    """
    Initialize trial period if not already started.
    Returns updated config dict.
    """
    if config.get("trial_started_date") is None:
        now = datetime.now().isoformat()
        config["trial_started_date"] = now
        config["license_status"] = LicenseStatus.TRIAL
        config["license_key"] = ""
    return config


def get_trial_days_remaining(config: Dict) -> Optional[int]:
    """
    Calculate days remaining in trial period.
    Returns None if trial never started or if license is active.
    Returns negative number if trial expired.
    """
    if config.get("license_status") == LicenseStatus.ACTIVE:
        return None  # Not in trial mode

    trial_start_str = config.get("trial_started_date")
    if not trial_start_str:
        return TRIAL_DURATION_DAYS  # Trial not started yet

    try:
        trial_start = datetime.fromisoformat(trial_start_str)
        elapsed = datetime.now() - trial_start
        remaining = TRIAL_DURATION_DAYS - elapsed.days
        return remaining
    except (ValueError, TypeError):
        # Invalid timestamp, treat as expired
        return -1


def is_trial_expired(config: Dict) -> bool:
    """Check if trial period has expired."""
    days_remaining = get_trial_days_remaining(config)
    if days_remaining is None:
        return False  # Active license, not in trial
    return days_remaining < 0


def can_revalidate_offline(config: Dict) -> bool:
    """
    Check if license can be used without online validation.
    Allows OFFLINE_GRACE_PERIOD_DAYS since last successful check.
    """
    last_checked_str = config.get("license_last_checked")
    if not last_checked_str:
        return False  # Never validated, must go online

    try:
        last_checked = datetime.fromisoformat(last_checked_str)
        elapsed = datetime.now() - last_checked
        return elapsed.days < OFFLINE_GRACE_PERIOD_DAYS
    except (ValueError, TypeError):
        return False


def validate_license_key(license_key: str, config: Dict) -> Tuple[bool, str]:
    """
    Validate license key with LemonSqueezy API.

    Args:
        license_key: The license key to validate
        config: Current config dict (will be updated with validation result)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        - (True, "") if valid
        - (False, "Offline - using cached validation") if offline but within grace period
        - (False, "error message") if invalid or network error
    """
    # Check if we can skip online validation (within grace period)
    if config.get("license_key") == license_key and can_revalidate_offline(config):
        if config.get("license_status") == LicenseStatus.ACTIVE:
            return (True, "")

    # Attempt online validation
    try:
        response = requests.post(
            LEMONSQUEEZY_API_URL,
            json={"license_key": license_key},
            headers={"Accept": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            is_valid = data.get("valid", False)

            if is_valid:
                # Update config with successful validation
                config["license_key"] = license_key
                config["license_status"] = LicenseStatus.ACTIVE
                config["license_last_checked"] = datetime.now().isoformat()
                return (True, "")
            else:
                # Invalid license key
                error = data.get("error", "Invalid license key")
                return (False, error)
        else:
            # API error response
            return (False, f"Validation failed (HTTP {response.status_code})")

    except requests.exceptions.Timeout:
        # Network timeout - check grace period
        if can_revalidate_offline(config):
            return (False, "Offline - using cached validation")
        return (False, "Network timeout. Please try again when online.")

    except requests.exceptions.ConnectionError:
        # No internet connection - check grace period
        if can_revalidate_offline(config):
            return (False, "Offline - using cached validation")
        return (False, "No internet connection. Please connect to validate license.")

    except Exception as e:
        # Unexpected error
        return (False, f"Validation error: {str(e)}")


def get_license_status_info(config: Dict) -> Dict:
    """
    Get comprehensive license status information for UI display.

    Returns dict with:
        - status: "trial", "active", or "expired"
        - message: Human-readable status message
        - days_remaining: Days remaining in trial (None if not in trial)
        - can_use_app: Boolean - whether app can be used
        - needs_purchase: Boolean - whether user should be prompted to buy
    """
    status = config.get("license_status", LicenseStatus.TRIAL)
    license_key = config.get("license_key", "")

    # Active license
    if status == LicenseStatus.ACTIVE and license_key:
        return {
            "status": LicenseStatus.ACTIVE,
            "message": "Licensed",
            "days_remaining": None,
            "can_use_app": True,
            "needs_purchase": False,
        }

    # Trial mode
    days_remaining = get_trial_days_remaining(config)

    if days_remaining is None:
        # This shouldn't happen, but handle gracefully
        return {
            "status": LicenseStatus.EXPIRED,
            "message": "License status unknown",
            "days_remaining": None,
            "can_use_app": False,
            "needs_purchase": True,
        }

    if days_remaining > 0:
        # Trial active
        return {
            "status": LicenseStatus.TRIAL,
            "message": f"{days_remaining} day{'s' if days_remaining != 1 else ''} remaining in trial",
            "days_remaining": days_remaining,
            "can_use_app": True,
            "needs_purchase": False,
        }
    else:
        # Trial expired
        return {
            "status": LicenseStatus.EXPIRED,
            "message": "Trial expired",
            "days_remaining": days_remaining,
            "can_use_app": False,
            "needs_purchase": True,
        }


def deactivate_license(config: Dict) -> Dict:
    """
    Deactivate current license and return to trial mode (if trial not expired).
    This is useful for transferring license to another machine.

    Returns updated config dict.
    """
    config["license_key"] = ""
    config["license_last_checked"] = None

    # Temporarily set status to trial to correctly check expiration
    # (is_trial_expired checks status and returns False if status==active)
    config["license_status"] = LicenseStatus.TRIAL

    # Check if trial is still valid
    if is_trial_expired(config):
        config["license_status"] = LicenseStatus.EXPIRED
    # else: status is already set to TRIAL above

    return config
