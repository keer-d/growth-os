"""Validated natural-language Campaign Brief parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from domain.campaign import (
    CampaignBrief,
    CampaignDefinition,
    CampaignParseProvenance,
    CampaignParseResult,
)
from domain.models import utc_now_iso
from pipeline.tls import trusted_ssl_context


PROMPT_VERSION = "campaign-brief-v1"
REQUIRED_FIELDS = ("goal", "target_markets", "content_themes", "target_audience")
QUESTION_BY_FIELD = {
    "goal": "What creator-partnership outcome should this campaign achieve?",
    "target_markets": "Which countries or markets should the campaign prioritize?",
    "content_themes": "Which content themes should the creators cover?",
    "target_audience": "Which audience groups should these creators reach?",
}


class CampaignProviderError(RuntimeError):
    """A provider could not generate usable output."""


class CampaignProviderConfigurationError(CampaignProviderError):
    """Live provider configuration is missing or incomplete."""


class CampaignParserProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, brief: CampaignBrief) -> str:
        """Return a JSON object string matching the CampaignDefinition fields."""


class DeterministicCampaignProvider(CampaignParserProvider):
    """Offline parser for known synthetic demo-style campaign briefs."""

    provider_name = "mock"
    model_name = "deterministic-campaign-v1"

    _THEMES = {
        "AI website tools": re.compile(r"\bai\b.{0,30}\b(?:website|web design|design tool)s?\b", re.I),
        "portfolio building": re.compile(r"\bportfolios?\b", re.I),
        "freelancing": re.compile(r"\bfreelanc(?:e|er|ers|ing)\b", re.I),
        "no-code": re.compile(r"\bno[ -]?code\b", re.I),
        "web design": re.compile(r"\bweb\s*design(?:er|ers|ing)?\b", re.I),
        "personal websites": re.compile(r"\bpersonal\s+(?:web)?sites?\b", re.I),
    }
    _MARKETS = {
        "United States": re.compile(r"\b(?:united states|u\.?s\.?a?\.?)\b", re.I),
        "Canada": re.compile(r"\bcanada|canadian\b", re.I),
        "United Kingdom": re.compile(r"\b(?:united kingdom|u\.?k\.?)\b", re.I),
        "Ireland": re.compile(r"\bireland|irish\b", re.I),
    }
    _AUDIENCES = {
        "designers": re.compile(r"\bdesigners?\b", re.I),
        "freelancers": re.compile(r"\bfreelancers?\b", re.I),
        "independent makers": re.compile(r"\bindependent makers?\b", re.I),
        "no-code builders": re.compile(r"\bno[ -]?code (?:builders?|makers?)\b", re.I),
    }

    def generate(self, brief: CampaignBrief) -> str:
        text = brief.original_brief
        markets = [label for label, pattern in self._MARKETS.items() if pattern.search(text)]
        themes = [label for label, pattern in self._THEMES.items() if pattern.search(text)]
        audience = [label for label, pattern in self._AUDIENCES.items() if pattern.search(text)]
        exclusions = self._extract_exclusions(text)
        goal = (
            "Discover partners for potential collaborations"
            if re.search(r"\b(?:find|discover|want|looking for)\b", text, re.I)
            else None
        )
        return json.dumps(
            {
                "goal": goal,
                "target_markets": markets,
                "content_themes": themes,
                "target_audience": audience,
                "exclusions": exclusions,
            }
        )

    @staticmethod
    def _extract_exclusions(text: str) -> list[str]:
        match = re.search(r"\bexclude\s+(.+?)(?:[.;]|$)", text, re.I)
        if not match:
            return []
        return [
            item.strip().lower()
            for item in re.split(r"\s+and\s+|,", match.group(1), flags=re.I)
            if item.strip()
        ]


class EnvironmentLLMCampaignProvider(CampaignParserProvider):
    """OpenAI-compatible live provider configured only through environment variables."""

    def __init__(self) -> None:
        self.base_url = os.getenv("CAMPAIGN_LLM_BASE_URL", "").strip()
        self.credential = os.getenv("CAMPAIGN_LLM_API_KEY", "").strip()
        self.model_name = os.getenv("CAMPAIGN_LLM_MODEL", "").strip()
        self.provider_name = os.getenv("CAMPAIGN_LLM_PROVIDER", "environment_llm").strip()
        missing = [
            name
            for name, value in (
                ("CAMPAIGN_LLM_BASE_URL", self.base_url),
                ("CAMPAIGN_LLM_API_KEY", self.credential),
                ("CAMPAIGN_LLM_MODEL", self.model_name),
            )
            if not value
        ]
        if missing:
            raise CampaignProviderConfigurationError(
                "Missing live campaign parser configuration: " + ", ".join(missing)
            )

    def generate(self, brief: CampaignBrief) -> str:
        endpoint = self.base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        payload = {
            "model": self.model_name,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": _LIVE_SYSTEM_PROMPT},
                {"role": "user", "content": brief.original_brief},
            ],
            "response_format": {"type": "json_object"},
        }
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.credential}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60, context=trusted_ssl_context()) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise CampaignProviderError(f"Live campaign parser request failed: {exc.__class__.__name__}") from exc


_LIVE_SYSTEM_PROMPT = """You parse a creator-partnership campaign brief into JSON.
Return exactly these keys:
{
  "goal": string or null,
  "target_markets": array of explicit market names,
  "content_themes": array of explicit content themes,
  "target_audience": array of explicit audience groups,
  "exclusions": array of explicit exclusions
}
Do not create search queries, scores, creator records, priorities, outreach fields, or audience inference.
Do not invent missing markets, themes, audiences, or exclusions. Use empty arrays or null when absent.
"""


class CampaignBriefParser:
    def __init__(self, provider: CampaignParserProvider):
        self.provider = provider

    def parse(self, brief: CampaignBrief) -> CampaignParseResult:
        provenance = CampaignParseProvenance(
            provider=self.provider.provider_name,
            model=self.provider.model_name,
            prompt_version=PROMPT_VERSION,
            parsed_at=utc_now_iso(),
        )
        try:
            raw_output = self.provider.generate(brief)
        except CampaignProviderError as exc:
            return self._failed(brief, provenance, "provider_error", str(exc))
        except Exception as exc:
            return self._failed(
                brief,
                provenance,
                "unexpected_provider_error",
                f"Provider failed with {exc.__class__.__name__}",
            )

        try:
            data = json.loads(raw_output)
            definition = self._validated_definition(brief.campaign_id, data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return self._failed(
                brief,
                provenance,
                "malformed_provider_output",
                f"Provider output failed validation: {exc}",
            )

        missing = tuple(
            field
            for field in REQUIRED_FIELDS
            if not getattr(definition, field)
        )
        if not missing:
            status = "complete"
        elif len(missing) == 1:
            status = "incomplete"
        else:
            status = "needs_clarification"
        questions = tuple(QUESTION_BY_FIELD[field] for field in missing)
        return CampaignParseResult(
            brief=brief,
            definition=definition,
            status=status,
            missing_required_fields=missing,
            clarification_questions=questions,
            provenance=provenance,
        )

    @staticmethod
    def _validated_definition(campaign_id: str, data: Any) -> CampaignDefinition:
        if not isinstance(data, dict):
            raise ValueError("top-level provider output must be an object")
        goal = data.get("goal")
        if goal is not None and not isinstance(goal, str):
            raise ValueError("goal must be a string or null")
        goal = goal.strip() if isinstance(goal, str) and goal.strip() else None
        return CampaignDefinition(
            campaign_id=campaign_id,
            goal=goal,
            target_markets=_validated_string_list(data.get("target_markets", []), "target_markets"),
            content_themes=_validated_string_list(data.get("content_themes", []), "content_themes"),
            target_audience=_validated_string_list(data.get("target_audience", []), "target_audience"),
            exclusions=_validated_string_list(data.get("exclusions", []), "exclusions"),
        )

    @staticmethod
    def _failed(
        brief: CampaignBrief,
        provenance: CampaignParseProvenance,
        error_code: str,
        error_message: str,
    ) -> CampaignParseResult:
        return CampaignParseResult(
            brief=brief,
            definition=None,
            status="failed",
            missing_required_fields=(),
            clarification_questions=(),
            provenance=provenance,
            error_code=error_code,
            error_message=error_message,
        )


def _validated_string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be an array")
    cleaned = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} entries must be strings")
        item = item.strip()
        if item and item not in cleaned:
            cleaned.append(item)
    return tuple(cleaned)
