"""Presentation-level partner type for one stored raw creator record.

Partner type is a *label*, not a judgement. It never enters prioritization and
it never blends signals: every rule below turns one observable fact — a bio
keyword, or the follower count — into a name a person can re-check against the
record in a second. Richer classification is deliberately out of scope, because
a label nobody can audit is worse than no label at all.
"""

from __future__ import annotations

import re
from typing import Any


PARTNER_TYPES: tuple[str, ...] = (
    "creator",
    "kol",
    "influencer",
    "micro_influencer",
    "affiliate",
    "community",
    "media",
    "industry_expert",
)

PARTNER_TYPE_LABELS: dict[str, dict[str, str]] = {
    "creator": {"en": "Creator", "zh": "创作者"},
    "kol": {"en": "KOL", "zh": "KOL"},
    "influencer": {"en": "Influencer", "zh": "影响力者"},
    "micro_influencer": {"en": "Micro-influencer", "zh": "微影响力者"},
    "affiliate": {"en": "Affiliate", "zh": "联盟推广"},
    "community": {"en": "Community", "zh": "社群"},
    "media": {"en": "Media", "zh": "媒体"},
    "industry_expert": {"en": "Industry Expert", "zh": "行业专家"},
}

MICRO_INFLUENCER_CEILING = 10_000
INFLUENCER_CEILING = 100_000

_AFFILIATE_TERMS = ("affiliate", "referral", "referral link", "discount code", "promo code")
_COMMUNITY_TERMS = ("community", "discord", "slack", "forum", "meetup")
_EXPERT_TERMS = (
    "founder",
    "engineer",
    "consultant",
    "advisor",
    "researcher",
    "speaker",
    "author",
)
_PUBLICATION_TERMS = (
    "publication",
    "blog",
    "magazine",
    "news",
    "newsroom",
    "journal",
    "review",
    "editorial",
    "press",
)
# A web result with no publication wording but clear practitioner wording is a
# person's own site, so it borrows the social expert vocabulary.
_PRACTITIONER_TERMS = _EXPERT_TERMS + ("portfolio", "freelance", "consulting", "coaching")


def _compile_terms(terms: tuple[str, ...]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    # Word boundaries keep "author" out of "authorization" and "press" out of
    # "expression"; the optional plural covers the natural bio phrasing.
    return tuple(
        (
            term,
            re.compile(
                r"\b" + r"\s+".join(re.escape(word) for word in term.split()) + r"s?\b",
                re.I,
            ),
        )
        for term in terms
    )


_AFFILIATE_PATTERNS = _compile_terms(_AFFILIATE_TERMS)
_COMMUNITY_PATTERNS = _compile_terms(_COMMUNITY_TERMS)
_EXPERT_PATTERNS = _compile_terms(_EXPERT_TERMS)
_PUBLICATION_PATTERNS = _compile_terms(_PUBLICATION_TERMS)
_PRACTITIONER_PATTERNS = _compile_terms(_PRACTITIONER_TERMS)


def derive_partner_type(profile: dict[str, Any]) -> dict[str, str]:
    """Name the kind of partner one raw creator record looks like.

    Takes the stored raw creator JSON and returns ``partner_type``,
    ``confidence`` and a ``basis`` sentence naming the evidence that decided it.
    """
    if not isinstance(profile, dict):
        raise TypeError("profile must be a stored raw creator record dict")

    text = _profile_text(profile)
    # Demo provenance outranks evidence strength: a controlled fixture record can
    # carry a real-looking bio and follower count, and the surface still has to
    # present it as demo metadata rather than as something observed live.
    confidence = "demo" if _is_demo_record(profile) else "observed"

    if profile.get("platform") == "web":
        partner_type, basis = _web_partner_type(text)
    else:
        partner_type, basis = _social_partner_type(text, profile.get("follower_count"))
    return {"partner_type": partner_type, "confidence": confidence, "basis": basis}


def partner_type_label(partner_type: str, language: str = "en") -> str:
    entry = PARTNER_TYPE_LABELS.get(partner_type)
    if entry is None:
        return partner_type
    return entry.get(language, entry["en"])


def partner_type_counts(profiles: list[dict[str, Any]]) -> dict[str, int]:
    """Count records per partner type, in PARTNER_TYPES order.

    Every type is present, zeros included, so a caller can render a stable row
    without guarding for missing keys.
    """
    if not isinstance(profiles, (list, tuple)):
        raise TypeError("profiles must be a list of stored raw creator record dicts")
    counts = {partner_type: 0 for partner_type in PARTNER_TYPES}
    for profile in profiles:
        counts[derive_partner_type(profile)["partner_type"]] += 1
    return counts


def _social_partner_type(text: str, follower_value: Any) -> tuple[str, str]:
    # Keywords are checked before the follower band: a partner who states they
    # run affiliate links or a community is better described by that than by
    # whatever audience size happens to sit next to it.
    matched = _first_term(text, _AFFILIATE_PATTERNS)
    if matched:
        return "affiliate", f'Bio mentions "{matched}", which reads as affiliate promotion.'
    matched = _first_term(text, _COMMUNITY_PATTERNS)
    if matched:
        return "community", f'Bio mentions "{matched}", which reads as a community space.'
    matched = _first_term(text, _EXPERT_PATTERNS)
    if matched:
        return (
            "industry_expert",
            f'Bio mentions "{matched}", which reads as an industry practitioner.',
        )

    followers = _follower_count(follower_value)
    if followers is None:
        return (
            "creator",
            "No partner keyword in the bio and no follower count, so Creator is the neutral default.",
        )
    if followers < MICRO_INFLUENCER_CEILING:
        return (
            "micro_influencer",
            f"Follower count {followers:,} is under {MICRO_INFLUENCER_CEILING:,}.",
        )
    if followers < INFLUENCER_CEILING:
        return (
            "influencer",
            f"Follower count {followers:,} is at least {MICRO_INFLUENCER_CEILING:,} "
            f"but under {INFLUENCER_CEILING:,}.",
        )
    return "kol", f"Follower count {followers:,} is at or above {INFLUENCER_CEILING:,}."


def _web_partner_type(text: str) -> tuple[str, str]:
    matched = _first_term(text, _PUBLICATION_PATTERNS)
    if matched:
        return "media", f'Site title or description mentions "{matched}", which reads as a publication.'
    matched = _first_term(text, _PRACTITIONER_PATTERNS)
    if matched:
        return (
            "industry_expert",
            f'Site title or description mentions "{matched}", which reads as a personal practitioner site.',
        )
    # A web result has no follower count to fall back on, so the honest default
    # for an unlabelled site is the broad publisher bucket.
    return "media", "No publication or practitioner wording was found, so a web result stays Media."


def _first_term(text: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> str | None:
    if not text:
        return None
    for term, pattern in patterns:
        if pattern.search(text):
            return term
    return None


def _profile_text(profile: dict[str, Any]) -> str:
    # Bio plus display name only. Sampled post text is noisier than a stated
    # bio, and a label a person cannot verify at a glance defeats the purpose.
    parts = (profile.get("display_name"), profile.get("bio_text"))
    return " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())


def _follower_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _is_demo_record(profile: dict[str, Any]) -> bool:
    if profile.get("discovery_mode") == "controlled_demo":
        return True
    connector = profile.get("source_connector")
    return isinstance(connector, str) and "controlled_fixture" in connector.lower()
