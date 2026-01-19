"""
Windows DPAPI (Data Protection API) wrapper for secure credential storage.

DPAPI encrypts data using the current Windows user's credentials, meaning:
- Only the same Windows user can decrypt the data
- No need to manage encryption keys manually
- Data is secure even if the config file is copied to another machine

On non-Windows platforms, falls back to base64 encoding (not secure, but allows
the app to function). A warning is logged when this fallback is used.
"""
import base64
import sys
import logging

logger = logging.getLogger(__name__)

# Windows-specific imports
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        """Windows DATA_BLOB structure for CryptProtectData/CryptUnprotectData."""
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char))
        ]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32

    # Function signatures
    _crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),  # pDataIn
        wintypes.LPCWSTR,           # szDataDescr
        ctypes.POINTER(DATA_BLOB),  # pOptionalEntropy
        ctypes.c_void_p,            # pvReserved
        ctypes.c_void_p,            # pPromptStruct
        wintypes.DWORD,             # dwFlags
        ctypes.POINTER(DATA_BLOB)   # pDataOut
    ]
    _crypt32.CryptProtectData.restype = wintypes.BOOL

    _crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),  # pDataIn
        ctypes.POINTER(wintypes.LPWSTR),  # ppszDataDescr
        ctypes.POINTER(DATA_BLOB),  # pOptionalEntropy
        ctypes.c_void_p,            # pvReserved
        ctypes.c_void_p,            # pPromptStruct
        wintypes.DWORD,             # dwFlags
        ctypes.POINTER(DATA_BLOB)   # pDataOut
    ]
    _crypt32.CryptUnprotectData.restype = wintypes.BOOL


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string using Windows DPAPI.

    Args:
        plaintext: The string to encrypt

    Returns:
        Base64-encoded encrypted data, or empty string if encryption fails.
        On non-Windows platforms, returns base64-encoded plaintext (not secure).
    """
    if not plaintext:
        return ""

    if sys.platform != "win32":
        # Fallback for non-Windows: just base64 encode (NOT SECURE)
        logger.warning("DPAPI not available on this platform. Using insecure fallback.")
        return "INSECURE:" + base64.b64encode(plaintext.encode('utf-8')).decode('ascii')

    try:
        # Convert string to bytes
        data = plaintext.encode('utf-8')

        # Create input blob
        input_blob = DATA_BLOB()
        input_blob.cbData = len(data)
        input_blob.pbData = ctypes.cast(
            ctypes.create_string_buffer(data, len(data)),
            ctypes.POINTER(ctypes.c_char)
        )

        # Create output blob
        output_blob = DATA_BLOB()

        # Call CryptProtectData
        # Flags: 0 = default (user-specific encryption)
        result = _crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            None,  # No description
            None,  # No entropy
            None,  # Reserved
            None,  # No prompt
            0,     # Flags
            ctypes.byref(output_blob)
        )

        if result:
            # Extract encrypted data
            encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            # Free the memory allocated by Windows
            _kernel32.LocalFree(output_blob.pbData)
            # Return as base64 for safe storage in JSON
            return base64.b64encode(encrypted).decode('ascii')
        else:
            logger.error("CryptProtectData failed")
            return ""

    except Exception as e:
        logger.error(f"DPAPI encryption failed: {e}")
        return ""


def decrypt(encrypted: str) -> str:
    """
    Decrypt a string that was encrypted with Windows DPAPI.

    Args:
        encrypted: Base64-encoded encrypted data from encrypt()

    Returns:
        The original plaintext string, or empty string if decryption fails.
    """
    if not encrypted:
        return ""

    # Handle non-Windows fallback format
    if encrypted.startswith("INSECURE:"):
        logger.warning("Decrypting insecure fallback data (non-Windows)")
        try:
            return base64.b64decode(encrypted[9:]).decode('utf-8')
        except Exception:
            return ""

    if sys.platform != "win32":
        logger.error("Cannot decrypt DPAPI data on non-Windows platform")
        return ""

    try:
        # Decode base64
        data = base64.b64decode(encrypted)

        # Create input blob
        input_blob = DATA_BLOB()
        input_blob.cbData = len(data)
        input_blob.pbData = ctypes.cast(
            ctypes.create_string_buffer(data, len(data)),
            ctypes.POINTER(ctypes.c_char)
        )

        # Create output blob
        output_blob = DATA_BLOB()

        # Call CryptUnprotectData
        result = _crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,  # Don't need description
            None,  # No entropy
            None,  # Reserved
            None,  # No prompt
            0,     # Flags
            ctypes.byref(output_blob)
        )

        if result:
            # Extract decrypted data
            decrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
            # Free the memory allocated by Windows
            _kernel32.LocalFree(output_blob.pbData)
            return decrypted.decode('utf-8')
        else:
            logger.error("CryptUnprotectData failed")
            return ""

    except Exception as e:
        logger.error(f"DPAPI decryption failed: {e}")
        return ""


def is_available() -> bool:
    """Check if DPAPI is available on this platform."""
    return sys.platform == "win32"
