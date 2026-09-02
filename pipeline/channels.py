"""The channel vocabulary shared by discovery, the UI service, and Data Sources.

The business surface talks about **channels** (Instagram, X, YouTube, Web).
Vendor and connector identity (Apify, the search API, the internal actor id) is
an implementation detail that lives here and in Technical Details only — it is
never the primary label anywhere in the product UI.

Configuration status is read from the environment by *name*. No value is ever
returned, logged, or serialized: callers receive a boolean and nothing else.
"""

from __future__ import annotations

import os
from typing import Any


CHANNELS: tuple[str, ...] = ("instagram", "x", "youtube", "web")

CHANNEL_LABELS: dict[str, dict[str, str]] = {
    "instagram": {"en": "Instagram", "zh": "Instagram"},
    "x": {"en": "X", "zh": "X"},
    "youtube": {"en": "YouTube", "zh": "YouTube"},
    "web": {"en": "Web", "zh": "网页"},
}

# What each channel is for, in partner terms — this is the Data Sources card copy.
CHANNEL_PURPOSE: dict[str, dict[str, str]] = {
    "instagram": {
        "en": "Creator profiles & public content",
        "zh": "创作者主页与公开内容",
    },
    "x": {
        "en": "Public posts & author profiles",
        "zh": "公开帖子与作者主页",
    },
    "youtube": {
        "en": "Channels & creator content",
        "zh": "频道与创作者内容",
    },
    "web": {
        "en": "Public partner & publisher discovery",
        "zh": "公开合作方与媒体发现",
    },
}

# The credential that decides whether a channel can run live. Names only.
CHANNEL_CREDENTIAL_ENV: dict[str, str] = {
    "instagram": "APIFY_API_TOKEN",
    "x": "X_BEARER_TOKEN",
    "youtube": "YOUTUBE_API_KEY",
    "web": "WEB_SEARCH_API_KEY",
}

# Every optional variable a channel understands, for documentation and the
# developer-facing section of Data Sources. Values are never read for display.
CHANNEL_ENV_VARS: dict[str, tuple[str, ...]] = {
    "instagram": (
        "APIFY_API_TOKEN",
        "APIFY_INSTAGRAM_ACTOR_ID",
        "APIFY_INSTAGRAM_RESULTS_LIMIT",
        "APIFY_INSTAGRAM_TIMEOUT_SECONDS",
        "APIFY_INSTAGRAM_MAX_TOTAL_CHARGE_USD",
    ),
    "x": (
        "X_BEARER_TOKEN",
        "X_API_BASE_URL",
        "X_API_TIMEOUT_SECONDS",
        "X_RESULTS_PER_QUERY",
    ),
    "youtube": (
        "YOUTUBE_API_KEY",
        "YOUTUBE_API_BASE_URL",
        "YOUTUBE_API_TIMEOUT_SECONDS",
        "YOUTUBE_RESULTS_PER_QUERY",
    ),
    "web": (
        "WEB_SEARCH_API_KEY",
        "WEB_SEARCH_BASE_URL",
        "WEB_SEARCH_ENGINE_ID",
        "WEB_SEARCH_TIMEOUT_SECONDS",
        "WEB_RESULTS_PER_QUERY",
    ),
}

# Internal connector identity, surfaced only in Technical Details.
CONNECTOR_TO_CHANNEL: dict[str, str] = {
    "controlled_fixture_v1": "controlled",
    "apify_instagram_search_scraper": "instagram",
    "x_api_v2_recent_search": "x",
    "youtube_data_api_v3_search": "youtube",
    "web_search_api_v1": "web",
}


def channel_label(channel: str, language: str = "en") -> str:
    entry = CHANNEL_LABELS.get(channel)
    if entry is None:
        return channel
    return entry.get(language, entry["en"])


def is_channel_configured(channel: str) -> bool:
    """True when this channel's credential is present in the environment.

    Only presence is checked. The value is never returned or logged.
    """
    name = CHANNEL_CREDENTIAL_ENV.get(channel)
    if not name:
        return False
    return bool(os.getenv(name, "").strip())


def channel_status(channel: str, language: str = "en") -> dict[str, Any]:
    """Credential-safe status for one channel, for the Data Sources surface."""

    configured = is_channel_configured(channel)
    return {
        "channel": channel,
        "label": channel_label(channel, language),
        "purpose": CHANNEL_PURPOSE.get(channel, {}).get(
            language, CHANNEL_PURPOSE.get(channel, {}).get("en", "")
        ),
        "configured": configured,
        "status": "connected" if configured else "not_configured",
        # Names only — the UI renders these in the developer section so a person
        # cloning the repo knows what to set. No value is ever included.
        "environment_variables": list(CHANNEL_ENV_VARS.get(channel, ())),
        "credential_variable": CHANNEL_CREDENTIAL_ENV.get(channel),
    }


def all_channel_status(language: str = "en") -> list[dict[str, Any]]:
    return [channel_status(channel, language) for channel in CHANNELS]


def configured_channels() -> tuple[str, ...]:
    return tuple(channel for channel in CHANNELS if is_channel_configured(channel))
