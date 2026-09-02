"""Verified TLS context selection for live provider HTTPS calls."""

from __future__ import annotations

from pathlib import Path
import ssl


def trusted_ssl_context() -> ssl.SSLContext:
    """Return a verifying context using system trust or the installed certifi bundle."""

    paths = ssl.get_default_verify_paths()
    if _usable_path(paths.cafile) or _usable_path(paths.capath):
        return ssl.create_default_context()

    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()

    certifi_bundle = certifi.where()
    if not _usable_path(certifi_bundle):
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi_bundle)


def _usable_path(value: str | None) -> bool:
    return bool(value and Path(value).exists())
