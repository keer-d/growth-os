"""V1 creator-profile URL normalization for Instagram and X."""

from __future__ import annotations

from urllib.parse import unquote, urlsplit


_INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}
_X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
_RESERVED = {
    "instagram": {"accounts", "explore", "p", "reel", "reels", "stories", "tv"},
    "x": {"compose", "explore", "hashtag", "home", "i", "intent", "search", "settings"},
}


def normalize_profile_url(url: str, platform: str) -> str:
    """Return a canonical profile URL without changing the observed URL.

    V1 accepts profile URLs only. Post, reel, status, search, and other content
    URLs fail explicitly instead of being guessed into creator identities.
    """
    if platform not in {"instagram", "x"}:
        raise ValueError("platform must be 'instagram' or 'x'")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("profile_url must be a non-empty string")

    raw = url.strip()
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").lower()
    allowed_hosts = _INSTAGRAM_HOSTS if platform == "instagram" else _X_HOSTS
    if host not in allowed_hosts:
        raise ValueError(f"{url!r} is not a {platform} profile URL")

    parts = [unquote(part).strip() for part in parsed.path.split("/") if part.strip()]
    if len(parts) != 1:
        raise ValueError(f"{url!r} is not a creator profile URL")
    handle = parts[0].lstrip("@").lower()
    if not handle or handle in _RESERVED[platform]:
        raise ValueError(f"{url!r} is not a creator profile URL")

    if platform == "instagram":
        return f"https://www.instagram.com/{handle}"
    return f"https://x.com/{handle}"
