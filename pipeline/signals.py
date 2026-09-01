"""Deterministic extraction of observable creator signals."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from domain.models import CreatorSignals, RawCreatorProfile, Signal, utc_now_iso


RELEVANCE_TERMS = {
    "web design": re.compile(r"\bweb\s*design(?:er|ers|ing)?\b", re.I),
    "portfolio": re.compile(r"\bportfolios?\b", re.I),
    "personal website": re.compile(r"\bpersonal\s+(?:web)?sites?\b", re.I),
    "Framer": re.compile(r"\bframer\b", re.I),
    "no-code": re.compile(r"\bno[ -]?code\b", re.I),
    "freelance design": re.compile(r"\bfreelanc(?:e|er|ers|ing)\b", re.I),
    "AI design tools": re.compile(r"\bai\b.{0,30}\b(?:design|website|creative|tool)s?\b", re.I),
    "AI website building": re.compile(r"\b(?:build|create|generate)\w*\b.{0,30}\bwebsites?\b", re.I),
}
TARGET_MARKET_RE = re.compile(
    r"\b(?:united states|u\.?s\.?a?\.?|canada|canadian|new york|san francisco|"
    r"los angeles|seattle|austin|toronto|vancouver|montreal)\b",
    re.I,
)
OUTSIDE_MARKET_RE = re.compile(
    r"\b(?:brazil|brasil|são paulo|sao paulo|argentina|india|mumbai|japan|tokyo|"
    r"australia|sydney|germany|berlin|france|paris)\b",
    re.I,
)
ACTIONABILITY_RE = re.compile(
    r"\b(?:contact|collab(?:oration)?|partnership|media kit|sponsor|work with me|email|dm me)\b",
    re.I,
)
SPAM_RE = re.compile(
    r"\b(?:buy followers|guaranteed followers|instant followers|follow for follow|"
    r"click every link|crypto giveaway|guaranteed income)\b",
    re.I,
)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _public_text(profile: RawCreatorProfile) -> str:
    return " ".join(
        part
        for part in (
            profile.display_name or "",
            profile.bio_text or "",
            *(sample.text for sample in profile.content_samples),
        )
        if part
    )


def _activity_signal(profile: RawCreatorProfile) -> Signal:
    retrieved = _parse_timestamp(profile.retrieved_at) or datetime.now(timezone.utc)
    timestamps = [
        timestamp
        for timestamp in (_parse_timestamp(item.published_at) for item in profile.content_samples)
        if timestamp is not None
    ]
    if not timestamps:
        return Signal("unknown", "No usable public content timestamps were available.")

    ages = sorted(max(0, (retrieved - timestamp).days) for timestamp in timestamps)
    recent_30 = sum(age <= 30 for age in ages)
    latest_age = ages[0]
    evidence = (f"Latest sampled content was {latest_age} days old.", f"{recent_30} samples were within 30 days.")
    if recent_30 >= 2:
        return Signal("high", "Multiple recent samples show strong publishing momentum.", evidence)
    if latest_age <= 90:
        return Signal("moderate", "At least one sampled post was published within 90 days.", evidence)
    return Signal("low", "The sampled public content is older, but the profile remains usable.", evidence)


def _relevance_signal(profile: RawCreatorProfile) -> Signal:
    text = _public_text(profile)
    if not text.strip():
        return Signal("unknown", "No public bio or content text was available.")
    matched = [label for label, pattern in RELEVANCE_TERMS.items() if pattern.search(text)]
    evidence = tuple(f"Observed theme: {label}." for label in matched[:5])
    if len(matched) >= 3:
        return Signal("high", "Several target creator-discovery themes are directly observable.", evidence)
    if matched:
        return Signal("moderate", "Some target themes are present, without perfect alignment.", evidence)
    return Signal("low", "Public evidence has little direct overlap with the campaign themes.")


def _audience_signal(profile: RawCreatorProfile) -> Signal:
    count = profile.follower_count
    if count is None:
        return Signal("unknown", "The source did not provide a follower count.")
    if count < 10_000:
        band = "small"
    elif count < 100_000:
        band = "medium"
    else:
        band = "large"
    return Signal(band, f"Observed follower count is {count:,}; audience size is context, not a quality verdict.")


def _market_signal(profile: RawCreatorProfile) -> Signal:
    text = _public_text(profile)
    target_hits = tuple(dict.fromkeys(match.group(0) for match in TARGET_MARKET_RE.finditer(text)))
    outside_hits = tuple(dict.fromkeys(match.group(0) for match in OUTSIDE_MARKET_RE.finditer(text)))
    if target_hits and outside_hits:
        return Signal(
            "conflicting",
            "Public text contains both target-market and other-market evidence.",
            tuple(f"Observed market term: {item}." for item in (*target_hits, *outside_hits)),
        )
    if target_hits:
        return Signal(
            "target",
            "Public text contains US or Canada market evidence.",
            tuple(f"Observed market term: {item}." for item in target_hits),
        )
    if outside_hits:
        return Signal(
            "outside",
            "Public text points to a market outside the primary US/Canada target.",
            tuple(f"Observed market term: {item}." for item in outside_hits),
        )
    return Signal("unknown", "No reliable market evidence was found in the supplied public text.")


def _actionability_signal(profile: RawCreatorProfile) -> Signal:
    text = _public_text(profile)
    evidence = []
    if profile.external_urls:
        evidence.append(f"{len(profile.external_urls)} public external URL(s) observed.")
    if ACTIONABILITY_RE.search(text):
        evidence.append("Bio/content contains public collaboration or contact language.")
    if evidence:
        return Signal("available", "A public path for further partnership research is visible.", tuple(evidence))
    return Signal(
        "missing",
        "No public contact or collaboration path was observed; this does not reduce creator quality.",
    )


def _quality_signal(profile: RawCreatorProfile) -> Signal:
    text = _public_text(profile)
    spam_hits = tuple(dict.fromkeys(match.group(0) for match in SPAM_RE.finditer(text)))
    if spam_hits:
        return Signal(
            "spam",
            "The public text contains obvious spam-style claims.",
            tuple(f"Spam phrase: {item}." for item in spam_hits),
        )
    if not (profile.bio_text or profile.content_samples):
        return Signal("insufficient", "The record lacks enough public evidence for a reliable decision.")
    return Signal("usable", "The record has a valid profile identity and usable public evidence.")


def extract_signals(profile: RawCreatorProfile) -> CreatorSignals:
    return CreatorSignals(
        record_id=profile.record_id,
        activity=_activity_signal(profile),
        content_relevance=_relevance_signal(profile),
        audience_size=_audience_signal(profile),
        market=_market_signal(profile),
        actionability=_actionability_signal(profile),
        record_quality=_quality_signal(profile),
        extracted_at=utc_now_iso(),
    )
