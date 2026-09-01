"""Transparent V1 creator priority policy for the public demo case."""

from __future__ import annotations

from domain.models import AudienceInference, CreatorSignals, PriorityDecision, utc_now_iso


def prioritize_creator(
    signals: CreatorSignals,
    audience_inference: AudienceInference,
) -> PriorityDecision:
    reasons: list[str] = []
    relevance = signals.content_relevance.value
    activity = signals.activity.value
    market = signals.market.value
    quality = signals.record_quality.value

    if quality in {"spam", "insufficient"}:
        priority = "Needs Review"
        reasons.append(signals.record_quality.reason)
    elif market == "conflicting":
        priority = "Needs Review"
        reasons.append("Market evidence conflicts and needs a human decision.")
    elif relevance == "unknown" or (activity == "unknown" and audience_inference.confidence == "low"):
        priority = "Needs Review"
        reasons.append("Available evidence is insufficient for a reliable priority decision.")
    elif relevance == "high" and activity == "high":
        priority = "P1"
        reasons.append("High relevance and strong publishing momentum support contacting first.")
    elif relevance == "high":
        priority = "P2"
        reasons.append("Strong relevance supports outreach even without very recent activity.")
    elif relevance == "moderate" and activity == "high":
        priority = "P2"
        reasons.append("Strong publishing momentum raises a moderately relevant creator's priority.")
    else:
        priority = "P3"
        reasons.append("The creator is usable but currently offers weaker or less timely campaign evidence.")

    if market == "outside" and priority == "P1":
        priority = "P2"
        reasons.append("The creator is outside the primary market, so priority is reduced but not rejected.")
    elif market == "outside":
        reasons.append("Outside-market evidence is context, not a hard rejection.")

    if signals.actionability.value == "available":
        reasons.append("A public collaboration/contact path improves actionability.")
    else:
        reasons.append("No contact path was observed; creator quality and priority were not penalized for it.")

    reasons.append(signals.audience_size.reason)
    evidence = {
        "activity": signals.activity.to_dict(),
        "content_relevance": signals.content_relevance.to_dict(),
        "audience_size": signals.audience_size.to_dict(),
        "market": signals.market.to_dict(),
        "actionability": signals.actionability.to_dict(),
        "record_quality": signals.record_quality.to_dict(),
        "audience_inference": {
            "likely_audience": list(audience_inference.likely_audience),
            "evidence": list(audience_inference.evidence),
            "confidence": audience_inference.confidence,
        },
    }
    return PriorityDecision(
        record_id=signals.record_id,
        priority=priority,
        reasons=tuple(reasons),
        signal_evidence=evidence,
        decided_at=utc_now_iso(),
    )
