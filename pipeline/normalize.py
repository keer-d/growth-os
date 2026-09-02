"""Partner-identity URL normalization for the four supported channels.

Product-facing these are "channels"; the argument stays ``platform`` so the
frozen backend contract is unchanged.
"""

from __future__ import annotations

from urllib.parse import unquote, urlsplit


_INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}
_X_HOSTS = {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
_RESERVED = {
    "instagram": {"accounts", "explore", "p", "reel", "reels", "stories", "tv"},
    "x": {"compose", "explore", "hashtag", "home", "i", "intent", "search", "settings"},
    "youtube": {
        "watch",
        "shorts",
        "playlist",
        "results",
        "feed",
        "channel",
        "c",
        "user",
        "embed",
        "live",
        "hashtag",
        "account",
        "premium",
        "gaming",
    },
}
# A web result that points at a channel with its own connector is not a separate
# "web" partner; rejecting it here keeps one real partner from being counted twice.
_CHANNEL_OWNED_HOSTS = _INSTAGRAM_HOSTS | _X_HOSTS | _YOUTUBE_HOSTS
_WEB_NON_PARTNER_HOSTS = {
    "google.com",
    "www.google.com",
    "bing.com",
    "www.bing.com",
    "duckduckgo.com",
    "www.duckduckgo.com",
    "facebook.com",
    "www.facebook.com",
    "t.co",
    "bit.ly",
}


def normalize_profile_url(url: str, platform: str) -> str:
    """Return a canonical partner URL without changing the observed URL.

    Profile/channel/site URLs only. Post, reel, status, video, search, and other
    content URLs fail explicitly instead of being guessed into partner identities.
    """
    if platform not in {"instagram", "x", "youtube", "web"}:
        raise ValueError("platform must be instagram, x, youtube, or web")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("profile_url must be a non-empty string")

    raw = url.strip()
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").lower()

    if platform == "web":
        return _normalize_web(parsed, host, url)
    if platform == "youtube":
        return _normalize_youtube(parsed, host, url)

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


def _normalize_youtube(parsed, host: str, url: str) -> str:
    """Canonicalize a YouTube channel URL in any of its four public forms."""

    if host not in _YOUTUBE_HOSTS:
        raise ValueError(f"{url!r} is not a YouTube channel URL")
    parts = [unquote(part).strip() for part in parsed.path.split("/") if part.strip()]
    if not parts:
        raise ValueError(f"{url!r} is not a YouTube channel URL")

    # /@handle — handles are case-insensitive, so they fold to lowercase.
    if parts[0].startswith("@"):
        handle = parts[0].lstrip("@").lower()
        if len(parts) != 1 or not handle:
            raise ValueError(f"{url!r} is not a YouTube channel URL")
        return f"https://www.youtube.com/@{handle}"

    # /channel/<id> — channel IDs are case-sensitive and must be preserved.
    if parts[0] == "channel":
        if len(parts) != 2 or not parts[1]:
            raise ValueError(f"{url!r} is not a YouTube channel URL")
        return f"https://www.youtube.com/channel/{parts[1]}"

    # /c/<name> and /user/<name> — legacy custom URLs.
    if parts[0] in {"c", "user"}:
        if len(parts) != 2 or not parts[1]:
            raise ValueError(f"{url!r} is not a YouTube channel URL")
        return f"https://www.youtube.com/{parts[0]}/{parts[1].lower()}"

    if len(parts) != 1 or parts[0].lower() in _RESERVED["youtube"]:
        raise ValueError(f"{url!r} is not a YouTube channel URL")
    # Bare /<customname> is the oldest custom-URL form.
    return f"https://www.youtube.com/{parts[0].lower()}"


def _normalize_web(parsed, host: str, url: str) -> str:
    """Canonicalize a public web partner (site, publication, or page) URL."""

    if parsed.scheme not in {"http", "https", ""}:
        raise ValueError(f"{url!r} is not a public web URL")
    if not host or "." not in host:
        raise ValueError(f"{url!r} is not a public web URL")
    if host in _CHANNEL_OWNED_HOSTS:
        raise ValueError(f"{url!r} belongs to a channel with its own connector")
    if host in _WEB_NON_PARTNER_HOSTS:
        raise ValueError(f"{url!r} is a search or redirect host, not a partner site")

    canonical_host = host[4:] if host.startswith("www.") else host
    path = "/".join(
        unquote(part).strip() for part in parsed.path.split("/") if part.strip()
    )
    # Query strings and fragments are tracking, not identity.
    return f"https://{canonical_host}/{path}".rstrip("/") if path else f"https://{canonical_host}"
