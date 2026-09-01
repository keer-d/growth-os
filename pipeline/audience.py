"""Provider-agnostic audience inference with a safe deterministic demo provider."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import AudienceInference, CreatorSignals, RawCreatorProfile, utc_now_iso


PROMPT_VERSION = "audience-only-v1"


class AudienceInferenceProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def infer(
        self, profile: RawCreatorProfile, signals: CreatorSignals
    ) -> AudienceInference:
        """Infer likely audience only; never decide creator quality or priority."""


class DeterministicAudienceProvider(AudienceInferenceProvider):
    provider_name = "mock"
    model_name = "deterministic-audience-v1"

    def infer(
        self, profile: RawCreatorProfile, signals: CreatorSignals
    ) -> AudienceInference:
        text = " ".join(
            [profile.bio_text or "", *(sample.text for sample in profile.content_samples)]
        ).lower()
        audiences: list[str] = []
        evidence: list[str] = []

        if "portfolio" in text or "personal website" in text:
            audiences.append("people building portfolios or personal websites")
            evidence.append("Public content explicitly discusses portfolios or personal websites.")
        if "freelanc" in text:
            audiences.append("freelance designers and independent creatives")
            evidence.append("Public content explicitly refers to freelance work.")
        if "framer" in text or "no-code" in text or "no code" in text:
            audiences.append("web designers and no-code builders")
            evidence.append("Public content mentions Framer or no-code website building.")
        if "ai" in text and ("design" in text or "website" in text):
            audiences.append("creators exploring AI-assisted design tools")
            evidence.append("Public content connects AI with design or website creation.")

        audiences = list(dict.fromkeys(audiences))
        evidence = list(dict.fromkeys(evidence))
        if len(evidence) >= 2:
            confidence = "high"
        elif evidence:
            confidence = "medium"
        else:
            confidence = "low"
            audiences = ["audience unclear from available public evidence"]
            evidence = ["The supplied public evidence contains no strong audience indicators."]

        return AudienceInference(
            record_id=profile.record_id,
            likely_audience=tuple(audiences),
            evidence=tuple(evidence),
            confidence=confidence,
            provider=self.provider_name,
            model=self.model_name,
            prompt_version=PROMPT_VERSION,
            inferred_at=utc_now_iso(),
        )
