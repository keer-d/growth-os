"""Provider-neutral generation of validated, non-executable draft search plans."""

from __future__ import annotations

from abc import ABC, abstractmethod
from hashlib import sha256
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from domain.campaign import CampaignDefinition
from domain.models import PLATFORMS, utc_now_iso
from domain.search_plan import (
    DraftSearchPlan,
    SEARCH_ANGLES,
    SearchPlanProvenance,
    SearchQuery,
)


PROMPT_VERSION = "draft-search-plan-v1"
REQUIRED_CAMPAIGN_FIELDS = ("goal", "target_markets", "content_themes", "target_audience")
MAX_QUERIES = 8


class SearchPlanError(RuntimeError):
    """A draft search plan could not be produced safely."""


class IncompleteCampaignError(SearchPlanError):
    """Generation was blocked because the Campaign Definition is incomplete."""


class SearchPlanProviderError(SearchPlanError):
    """A provider could not propose usable output."""


class SearchPlanProviderConfigurationError(SearchPlanProviderError):
    """Live provider configuration is missing or incomplete."""


class MalformedSearchPlanOutput(SearchPlanProviderError):
    """Provider output was not valid enough to become a draft plan."""


class SearchPlanProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, campaign: CampaignDefinition) -> str:
        """Return JSON containing query proposals, but no system IDs or execution state."""


class DeterministicSearchPlanProvider(SearchPlanProvider):
    """Small, credentials-free query proposer for the synthetic Controlled Demo."""

    provider_name = "mock"
    model_name = "deterministic-search-plan-v1"

    _SINGULAR_AUDIENCE = {
        "designers": "designer",
        "freelancers": "freelancer",
        "independent makers": "independent maker",
        "no-code builders": "no-code builder",
    }
    _MARKET_SHORT_NAMES = {
        "United States": "US",
        "United Kingdom": "UK",
    }

    def generate(self, campaign: CampaignDefinition) -> str:
        themes = list(campaign.content_themes)
        audiences = list(campaign.target_audience)
        core_theme = themes[0]
        secondary_theme = themes[1] if len(themes) > 1 else themes[0]
        practice_theme = next(
            (
                preferred
                for preferred in ("web design", "no-code", "personal websites", "freelancing")
                if preferred in themes
            ),
            secondary_theme,
        )
        primary_audience = audiences[0]
        secondary_audience = audiences[1] if len(audiences) > 1 else audiences[0]
        identity = self._SINGULAR_AUDIENCE.get(
            primary_audience,
            primary_audience[:-1] if primary_audience.endswith("s") else primary_audience,
        )
        markets = " ".join(
            self._MARKET_SHORT_NAMES.get(market, market) for market in campaign.target_markets
        )
        core_workflow = {
            "AI website tools": "building websites with AI",
            "no-code": "building with no-code",
        }.get(core_theme, f"working with {core_theme}")

        proposals = [
            {
                "platform": "instagram",
                "query_text": f"{core_theme} creator",
                "rationale": f"Finds Instagram creator accounts centered on {core_theme}.",
                "search_angle": "core_topic",
            },
            {
                "platform": "instagram",
                "query_text": f"{secondary_theme} workflow",
                "rationale": f"Looks for visual process and tutorial content about {secondary_theme}.",
                "search_angle": "creator_workflow",
            },
            {
                "platform": "instagram",
                "query_text": f"{identity} sharing {practice_theme}",
                "rationale": f"Looks for self-identified {primary_audience} with explicit topic fit.",
                "search_angle": "professional_identity",
            },
            {
                "platform": "instagram",
                "query_text": f"{secondary_theme} tips for {primary_audience}",
                "rationale": "Targets practical content intended for the campaign audience.",
                "search_angle": "use_case",
            },
            {
                "platform": "x",
                "query_text": core_workflow,
                "rationale": f"Finds people discussing hands-on work with {core_theme} on X.",
                "search_angle": "core_topic",
            },
            {
                "platform": "x",
                "query_text": f"{secondary_theme} challenges for {primary_audience}",
                "rationale": "Explores questions and pain points relevant to the intended audience.",
                "search_angle": "audience_problem",
            },
            {
                "platform": "x",
                "query_text": f"{practice_theme} tools for {secondary_audience}",
                "rationale": "Surfaces practitioners comparing or recommending relevant tools.",
                "search_angle": "adjacent_tool",
            },
            {
                "platform": "x",
                "query_text": f"{markets} {identity} sharing {core_theme}",
                "rationale": "Combines explicit market and professional-identity context for review.",
                "search_angle": "professional_identity",
            },
        ]
        return json.dumps({"queries": self._remove_excluded(proposals, campaign.exclusions)})

    @staticmethod
    def _remove_excluded(
        proposals: list[dict[str, str]], exclusions: tuple[str, ...]
    ) -> list[dict[str, str]]:
        blocked = tuple(exclusion.casefold() for exclusion in exclusions)
        return [
            proposal
            for proposal in proposals
            if not any(term in proposal["query_text"].casefold() for term in blocked)
        ]


class EnvironmentLLMSearchPlanProvider(SearchPlanProvider):
    """OpenAI-compatible live proposer configured only through environment variables."""

    def __init__(self) -> None:
        self.base_url = os.getenv("SEARCH_PLAN_LLM_BASE_URL", "").strip()
        self.credential = os.getenv("SEARCH_PLAN_LLM_API_KEY", "").strip()
        self.model_name = os.getenv("SEARCH_PLAN_LLM_MODEL", "").strip()
        self.provider_name = os.getenv(
            "SEARCH_PLAN_LLM_PROVIDER", "environment_llm"
        ).strip()
        missing = [
            name
            for name, value in (
                ("SEARCH_PLAN_LLM_BASE_URL", self.base_url),
                ("SEARCH_PLAN_LLM_API_KEY", self.credential),
                ("SEARCH_PLAN_LLM_MODEL", self.model_name),
            )
            if not value
        ]
        if missing:
            raise SearchPlanProviderConfigurationError(
                "Missing live search-plan configuration: " + ", ".join(missing)
            )

    def generate(self, campaign: CampaignDefinition) -> str:
        endpoint = self.base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        payload = {
            "model": self.model_name,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": _LIVE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(campaign.to_dict(), ensure_ascii=False),
                },
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
            with urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise SearchPlanProviderError(
                f"Live search-plan request failed: {exc.__class__.__name__}"
            ) from exc


_LIVE_SYSTEM_PROMPT = """You propose a small draft creator search plan from a validated Campaign Definition.
Return exactly one JSON object with a `queries` array. Each query must contain:
{
  "platform": "instagram" or "x",
  "query_text": non-empty human-readable string,
  "rationale": non-empty plain-language reason,
  "search_angle": one of "core_topic", "creator_workflow", "audience_problem",
                  "adjacent_tool", "professional_identity", "use_case"
}
Return at most 8 queries, cover both platforms, and use meaningfully different search angles.
Respect explicit exclusions. Do not invent missing campaign requirements.
Do not return IDs, scores, creators, retrieval instructions, priorities, outreach fields,
approval state, provider syntax, or autonomous diversification instructions.
"""


class SearchPlanGenerator:
    def __init__(self, provider: SearchPlanProvider):
        self.provider = provider

    def generate(self, campaign: CampaignDefinition) -> DraftSearchPlan:
        self._require_complete_campaign(campaign)
        try:
            raw_output = self.provider.generate(campaign)
        except SearchPlanError:
            raise
        except Exception as exc:
            raise SearchPlanProviderError(
                f"Search-plan provider failed with {exc.__class__.__name__}"
            ) from exc

        try:
            data = json.loads(raw_output)
            raw_queries = self._validated_query_list(data)
            deduplicated = self._deduplicate_exact_text(raw_queries)[:MAX_QUERIES]
            if not deduplicated:
                raise ValueError("queries must not be empty")
            search_plan_id = self._search_plan_id(campaign.campaign_id, deduplicated)
            queries = tuple(
                SearchQuery(
                    query_id=f"{search_plan_id}_q{index:03d}",
                    campaign_id=campaign.campaign_id,
                    platform=query["platform"],
                    query_text=query["query_text"],
                    rationale=query["rationale"],
                    search_angle=query["search_angle"],
                )
                for index, query in enumerate(deduplicated, start=1)
            )
            return DraftSearchPlan(
                search_plan_id=search_plan_id,
                campaign_id=campaign.campaign_id,
                status="draft",
                queries=queries,
                provenance=SearchPlanProvenance(
                    provider=self.provider.provider_name,
                    model=self.provider.model_name,
                    prompt_version=PROMPT_VERSION,
                    generated_at=utc_now_iso(),
                ),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise MalformedSearchPlanOutput(
                f"Provider output failed validation: {exc}"
            ) from exc

    @staticmethod
    def _require_complete_campaign(campaign: CampaignDefinition) -> None:
        missing = [
            field_name
            for field_name in REQUIRED_CAMPAIGN_FIELDS
            if not getattr(campaign, field_name)
        ]
        if missing:
            raise IncompleteCampaignError(
                "Search-plan generation blocked; Campaign Definition is missing: "
                + ", ".join(missing)
            )

    @staticmethod
    def _validated_query_list(data: Any) -> list[dict[str, str]]:
        if not isinstance(data, dict):
            raise ValueError("top-level provider output must be an object")
        value = data.get("queries")
        if not isinstance(value, list):
            raise ValueError("queries must be an array")
        cleaned = []
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValueError(f"queries[{index}] must be an object")
            platform = item.get("platform")
            if platform not in PLATFORMS:
                raise ValueError(f"queries[{index}].platform must be one of {sorted(PLATFORMS)}")
            search_angle = item.get("search_angle")
            if search_angle not in SEARCH_ANGLES:
                raise ValueError(
                    f"queries[{index}].search_angle must be one of {sorted(SEARCH_ANGLES)}"
                )
            cleaned.append(
                {
                    "platform": platform,
                    "query_text": _required_query_text(item.get("query_text"), f"queries[{index}].query_text"),
                    "rationale": _required_query_text(item.get("rationale"), f"queries[{index}].rationale"),
                    "search_angle": search_angle,
                }
            )
        return cleaned

    @staticmethod
    def _deduplicate_exact_text(queries: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        unique = []
        for query in queries:
            key = " ".join(query["query_text"].casefold().split())
            if key not in seen:
                seen.add(key)
                unique.append(query)
        return unique

    @staticmethod
    def _search_plan_id(campaign_id: str, queries: list[dict[str, str]]) -> str:
        signature = json.dumps(
            {"campaign_id": campaign_id, "queries": queries},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"searchplan_{sha256(signature.encode('utf-8')).hexdigest()[:12]}"


def _required_query_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return " ".join(value.split())
