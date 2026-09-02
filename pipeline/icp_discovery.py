"""Generate validated ICP hypotheses and translate one into discovery criteria."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
import json
import logging
import os
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from domain.icp import (
    BusinessContext,
    DiscoveryCriteria,
    ICPEvaluation,
    ICPGenerationProvenance,
    ICPGenerationResult,
    ICPHypothesis,
)
from domain.models import utc_now_iso
from pipeline.tls import trusted_ssl_context


PROMPT_VERSION = "icp-hypotheses-v1"
CRITERIA_VERSION = "icp-to-partner-criteria-v1"
LOGGER = logging.getLogger("growth_os.icp")


class ICPDiscoveryError(RuntimeError):
    error_code = "icp_generation_failure"


class InsufficientBusinessContextError(ICPDiscoveryError):
    error_code = "insufficient_business_context"


class WebsiteContextUnavailableError(ICPDiscoveryError):
    error_code = "website_analysis_unavailable"


class ICPProviderConfigurationError(ICPDiscoveryError):
    error_code = "icp_provider_not_configured"


class ICPProviderError(ICPDiscoveryError):
    error_code = "icp_provider_failure"


class MalformedICPOutputError(ICPDiscoveryError):
    error_code = "malformed_icp_output"


class NoUsefulHypothesesError(ICPDiscoveryError):
    error_code = "no_useful_icp_hypotheses"


class IncompleteDiscoveryCriteriaError(ICPDiscoveryError):
    error_code = "incomplete_discovery_criteria"


class ICPProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, context: BusinessContext) -> str:
        """Return a JSON object containing exactly three hypotheses."""


class DeterministicICPProvider(ICPProvider):
    """Credential-free provider for the controlled product walkthrough."""

    provider_name = "mock"
    model_name = "deterministic-icp-v1"

    def generate(self, context: BusinessContext) -> str:
        if not context.product_description:
            raise WebsiteContextUnavailableError(
                "The offline demo cannot read a website. Add a manual product description."
            )
        signal = " ".join(
            (
                context.product_name,
                context.product_description,
                context.problem,
                context.strongest_value,
                context.current_users,
                *context.current_alternatives,
                *context.pain_signals,
            )
        ).casefold()
        if "video" in signal or "视频" in signal:
            hypotheses = self._video_hypotheses(context)
        else:
            hypotheses = self._contextual_hypotheses(context)
        return json.dumps({"hypotheses": hypotheses}, ensure_ascii=False)

    @staticmethod
    def _video_hypotheses(context: BusinessContext) -> list[dict[str, Any]]:
        alternative = context.current_alternatives[0] if context.current_alternatives else "manual video production"
        return [
            {
                "name": "B2B SaaS Product Marketing Teams",
                "who": "Product marketing managers at B2B SaaS companies preparing launches, feature announcements, and sales enablement.",
                "context": "They need product stories in multiple formats while launch calendars keep moving.",
                "core_pain": "Producing polished demo and launch videos takes too much specialist time.",
                "why_pain_matters": "Slow production delays launches and leaves sales teams without current visual proof.",
                "current_alternative": alternative,
                "value_proposition": f"{context.product_name} can turn product inputs into usable campaign video faster.",
                "trigger": "A product launch, major feature release, or sales enablement refresh is approaching.",
                "intent_signals": ["asking how to make product demo videos", "hiring product marketing video support", "sharing an upcoming launch"],
                "where_to_find": ["LinkedIn product marketing communities", "X SaaS launch conversations", "YouTube product demo channels"],
                "why_may_work": "The pain is tied to a visible deadline and the value can be demonstrated with before-and-after workflow evidence.",
                "unknowns": ["Whether output quality meets brand standards", "Whether teams have enough repeat video volume"],
                "evaluation": {"pain_severity": 86, "problem_frequency": 78, "value_proposition_strength": 88, "reachability": 82, "intent_signal_availability": 84, "potential_commercial_value": 87, "product_fit": 91},
                "recommended_order": 1,
                "test_priority_reason": "Strong workflow fit, visible triggers, and reachable professional communities make this the clearest first test.",
            },
            {
                "name": "Early-Stage Startup Growth Teams",
                "who": "Lean growth managers and founders at funded startups who ship campaigns without an in-house video team.",
                "context": "A small team owns acquisition, launch content, social distribution, and experiment velocity.",
                "core_pain": "Campaign ideas outnumber the videos the team can afford to produce.",
                "why_pain_matters": "Low creative throughput slows experimentation and makes it harder to learn which message converts.",
                "current_alternative": "Canva templates, founder-recorded clips, freelancers, or skipping video",
                "value_proposition": f"{context.product_name} can expand creative output without adding a production function.",
                "trigger": "A fundraising announcement, launch sprint, paid-social test, or new growth hire.",
                "intent_signals": ["asking for faster content production", "posting growth experiments", "hiring a first growth marketer"],
                "where_to_find": ["X startup and growth communities", "founder newsletters", "YouTube growth channels"],
                "why_may_work": "The team values speed and experiments, so a bounded workflow trial is easy to understand.",
                "unknowns": ["Budget may be constrained", "Founders may prefer general-purpose tools"],
                "evaluation": {"pain_severity": 75, "problem_frequency": 84, "value_proposition_strength": 83, "reachability": 88, "intent_signal_availability": 79, "potential_commercial_value": 68, "product_fit": 85},
                "recommended_order": 2,
                "test_priority_reason": "High frequency and reachability are attractive, but budget and willingness to pay need validation.",
            },
            {
                "name": "Boutique Content and Marketing Agencies",
                "who": "Small agencies delivering recurring product, social, and campaign content for several client accounts.",
                "context": "They must protect margin while accommodating revisions, varied brand guidelines, and uneven client demand.",
                "core_pain": "Repeat video production consumes delivery capacity and makes project margins unpredictable.",
                "why_pain_matters": "Capacity limits growth, while missed deadlines and inconsistent output put client retention at risk.",
                "current_alternative": "Freelance editors, template libraries, and internal production handoffs",
                "value_proposition": f"{context.product_name} may standardize repeatable production and increase delivery capacity.",
                "trigger": "The agency wins a content-heavy client, adds a retainer, or starts hiring production support.",
                "intent_signals": ["hiring freelance video editors", "publishing a new client launch", "discussing agency capacity or margins"],
                "where_to_find": ["Agency owner communities", "LinkedIn agency operations groups", "Web agency directories"],
                "why_may_work": "The workflow repeats across clients and time saved has a direct margin story.",
                "unknowns": ["Multi-brand control requirements may be complex", "Agencies may require white-label workflows"],
                "evaluation": {"pain_severity": 82, "problem_frequency": 89, "value_proposition_strength": 80, "reachability": 72, "intent_signal_availability": 70, "potential_commercial_value": 90, "product_fit": 79},
                "recommended_order": 3,
                "test_priority_reason": "Commercial value may be high, but requirements and public intent signals are less certain.",
            },
        ]

    @staticmethod
    def _contextual_hypotheses(context: BusinessContext) -> list[dict[str, Any]]:
        users = context.current_users if context.current_users.casefold() not in {"unknown", "i don't know", "不知道"} else "teams already attempting this workflow"
        alternative = context.current_alternatives[0] if context.current_alternatives else "manual work and general-purpose tools"
        pain_signal = context.pain_signals[0] if context.pain_signals else "publicly asking how to solve the problem"
        base = {
            "context": f"They encounter this problem while trying to use or deliver the outcome promised by {context.product_name}.",
            "core_pain": context.problem,
            "why_pain_matters": "The current workflow consumes time, delays outcomes, and creates an observable reason to look for an alternative.",
            "current_alternative": alternative,
            "value_proposition": context.strongest_value,
            "trigger": pain_signal,
        }
        return [
            {
                **base,
                "name": f"Active {users.title()} With Urgent Workflow Pain",
                "who": f"{users} who experience the problem repeatedly and are currently trying to improve the workflow.",
                "intent_signals": [pain_signal, "comparing tools or workflows", "requesting recommendations from peers"],
                "where_to_find": ["X professional conversations", "YouTube how-to communities", "specialist web communities"],
                "why_may_work": "They already recognize the problem and expose observable research or comparison behavior.",
                "unknowns": ["Whether the pain is severe enough to fund", "Whether the described value is differentiated"],
                "evaluation": {"pain_severity": 84, "problem_frequency": 82, "value_proposition_strength": 78, "reachability": 80, "intent_signal_availability": 82, "potential_commercial_value": 75, "product_fit": 86},
                "recommended_order": 1,
                "test_priority_reason": "Recognized pain and visible intent make this the fastest hypothesis to test.",
            },
            {
                **base,
                "name": f"Lean Teams Scaling {context.product_name} Outcomes",
                "who": f"Small cross-functional teams responsible for producing the outcome without a dedicated specialist function.",
                "intent_signals": ["hiring for the workflow", "sharing a new initiative", "asking for a faster process"],
                "where_to_find": ["LinkedIn operator communities", "X startup conversations", "industry newsletters"],
                "why_may_work": "A constrained team can understand a time-to-value improvement without changing the whole organization.",
                "unknowns": ["Team ownership may be fragmented", "Budget authority may sit elsewhere"],
                "evaluation": {"pain_severity": 75, "problem_frequency": 79, "value_proposition_strength": 82, "reachability": 84, "intent_signal_availability": 73, "potential_commercial_value": 72, "product_fit": 81},
                "recommended_order": 2,
                "test_priority_reason": "Reachability is good, but buying authority and ownership need confirmation.",
            },
            {
                **base,
                "name": f"Service Teams Delivering {context.product_name} Outcomes",
                "who": "Specialist service providers who repeat the workflow across multiple clients and must protect delivery margin.",
                "intent_signals": ["hiring delivery support", "promoting a related client service", "discussing capacity constraints"],
                "where_to_find": ["Web service directories", "agency owner groups", "YouTube specialist channels"],
                "why_may_work": "Repeated use creates a measurable capacity and margin story.",
                "unknowns": ["Requirements may vary across clients", "Service providers may build their own workflow"],
                "evaluation": {"pain_severity": 78, "problem_frequency": 88, "value_proposition_strength": 76, "reachability": 68, "intent_signal_availability": 65, "potential_commercial_value": 88, "product_fit": 74},
                "recommended_order": 3,
                "test_priority_reason": "Potential value is high, while complexity and weaker public signals raise testing cost.",
            },
        ]


class EnvironmentLLMICPProvider(ICPProvider):
    """OpenAI-compatible provider configured entirely through environment variables."""

    def __init__(self) -> None:
        self.base_url = os.getenv("ICP_LLM_BASE_URL", "").strip()
        self.credential = os.getenv("ICP_LLM_API_KEY", "").strip()
        self.model_name = os.getenv("ICP_LLM_MODEL", "").strip()
        self.provider_name = os.getenv("ICP_LLM_PROVIDER", "environment_llm").strip()
        missing = [
            name
            for name, value in (
                ("ICP_LLM_BASE_URL", self.base_url),
                ("ICP_LLM_API_KEY", self.credential),
                ("ICP_LLM_MODEL", self.model_name),
            )
            if not value
        ]
        if missing:
            raise ICPProviderConfigurationError(
                "Missing live ICP configuration: " + ", ".join(missing)
            )

    def generate(self, context: BusinessContext) -> str:
        endpoint = self.base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint += "/chat/completions"
        request = Request(
            endpoint,
            data=json.dumps(
                {
                    "model": self.model_name,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": _LIVE_SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(context.to_dict(), ensure_ascii=False)},
                    ],
                    "response_format": {"type": "json_object"},
                }
            ).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.credential}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=60, context=trusted_ssl_context()) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ICPProviderError(
                f"Live ICP request failed: {exc.__class__.__name__}"
            ) from exc


class ICPDiscoveryService:
    def __init__(self, provider: ICPProvider) -> None:
        self.provider = provider

    def generate(self, context: BusinessContext) -> ICPGenerationResult:
        self._validate_context(context)
        started = monotonic()
        try:
            raw = self.provider.generate(context)
            data = json.loads(raw)
            items = self._validate_output(data)
            generated_at = utc_now_iso()
            hypotheses = tuple(
                self._build_hypothesis(context, item, generated_at) for item in items
            )
        except ICPDiscoveryError:
            raise
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise MalformedICPOutputError(
                f"ICP provider output failed validation: {exc}"
            ) from exc
        except Exception as exc:
            raise ICPProviderError(
                f"ICP provider failed with {exc.__class__.__name__}"
            ) from exc
        duration_ms = round((monotonic() - started) * 1000)
        provenance = ICPGenerationProvenance(
            provider=self.provider.provider_name,
            model=self.provider.model_name,
            prompt_version=PROMPT_VERSION,
            generated_at=generated_at,
            duration_ms=duration_ms,
        )
        LOGGER.info(
            json.dumps(
                {
                    "event": "icp_hypotheses_generated",
                    "context_id": context.context_id,
                    "provider": provenance.provider,
                    "model": provenance.model,
                    "prompt_version": provenance.prompt_version,
                    "duration_ms": duration_ms,
                    "hypothesis_count": 3,
                },
                sort_keys=True,
            )
        )
        return ICPGenerationResult(
            context=context,
            hypotheses=hypotheses,
            provenance=provenance,
            status="complete",
        )

    @staticmethod
    def _validate_context(context: BusinessContext) -> None:
        if len(context.problem) < 12 or len(context.strongest_value) < 12:
            raise InsufficientBusinessContextError(
                "Describe the problem and strongest value in enough detail to form a hypothesis."
            )

    @staticmethod
    def _validate_output(data: Any) -> list[dict[str, Any]]:
        if not isinstance(data, dict) or not isinstance(data.get("hypotheses"), list):
            raise ValueError("top-level output must contain a hypotheses array")
        items = data["hypotheses"]
        if len(items) != 3:
            raise ValueError("hypotheses must contain exactly three items")
        if not all(isinstance(item, dict) for item in items):
            raise ValueError("every hypothesis must be an object")
        names = [str(item.get("name", "")).strip().casefold() for item in items]
        if len(set(names)) != 3:
            raise ValueError("hypothesis names must be distinct")
        if any(name in {"marketers", "creators", "companies", "businesses", "users"} for name in names):
            raise NoUsefulHypothesesError(
                "The provider returned broad labels instead of testable hypotheses."
            )
        return items

    @staticmethod
    def _build_hypothesis(
        context: BusinessContext, item: dict[str, Any], generated_at: str
    ) -> ICPHypothesis:
        evaluation_data = item.get("evaluation")
        if not isinstance(evaluation_data, dict):
            raise ValueError("evaluation must be an object")
        evaluation = ICPEvaluation(
            **{name: evaluation_data.get(name) for name in ICPEvaluation.__dataclass_fields__}
        )
        return ICPHypothesis(
            hypothesis_id=f"icp_{uuid4().hex[:12]}",
            version=1,
            business_context_id=context.context_id,
            audience_type="customer",
            name=item.get("name"),
            who=item.get("who"),
            context=item.get("context"),
            core_pain=item.get("core_pain"),
            why_pain_matters=item.get("why_pain_matters"),
            current_alternative=item.get("current_alternative"),
            value_proposition=item.get("value_proposition"),
            trigger=item.get("trigger"),
            intent_signals=item.get("intent_signals"),
            where_to_find=item.get("where_to_find"),
            why_may_work=item.get("why_may_work"),
            unknowns=item.get("unknowns"),
            evaluation=evaluation,
            recommended_order=item.get("recommended_order"),
            test_priority_reason=item.get("test_priority_reason"),
            status="DRAFT",
            created_at=generated_at,
        )


def generate_discovery_criteria(
    hypothesis: ICPHypothesis, context: BusinessContext
) -> DiscoveryCriteria:
    """Translate a customer hypothesis into a partner-search contract, not queries."""

    themes = _criteria_themes(context)
    channels = _criteria_channels(hypothesis.where_to_find)
    status = "draft" if context.target_markets and themes and channels else "incomplete"
    return DiscoveryCriteria(
        criteria_id=f"criteria_{uuid4().hex[:12]}",
        source_criteria_id=None,
        hypothesis_id=hypothesis.hypothesis_id,
        hypothesis_version=hypothesis.version,
        hypothesis_name=hypothesis.name,
        discovery_subject="partner",
        partner_profile=(
            f"Partners who publish credible content about {', '.join(themes)} and can reach "
            f"people matching this customer hypothesis: {hypothesis.who}"
        ),
        goal=f"Discover partners who can help reach and validate {hypothesis.name}.",
        target_markets=context.target_markets,
        content_themes=themes,
        target_audience=(hypothesis.name, hypothesis.who),
        intent_signals=hypothesis.intent_signals,
        exclusions=(),
        channels=channels,
        status=status,
        criteria_version=CRITERIA_VERSION,
        created_at=utc_now_iso(),
    )


def confirm_discovery_criteria(
    draft: DiscoveryCriteria,
    *,
    partner_profile: str,
    goal: str,
    target_markets: tuple[str, ...],
    content_themes: tuple[str, ...],
    target_audience: tuple[str, ...],
    intent_signals: tuple[str, ...],
    exclusions: tuple[str, ...],
    channels: tuple[str, ...],
) -> DiscoveryCriteria:
    """Create an immutable confirmed snapshot; the draft remains unchanged."""

    try:
        return DiscoveryCriteria(
            criteria_id=f"criteria_{uuid4().hex[:12]}",
            source_criteria_id=draft.criteria_id,
            hypothesis_id=draft.hypothesis_id,
            hypothesis_version=draft.hypothesis_version,
            hypothesis_name=draft.hypothesis_name,
            discovery_subject=draft.discovery_subject,
            partner_profile=partner_profile,
            goal=goal,
            target_markets=target_markets,
            content_themes=content_themes,
            target_audience=target_audience,
            intent_signals=intent_signals,
            exclusions=exclusions,
            channels=channels,
            status="confirmed",
            criteria_version=draft.criteria_version,
            created_at=utc_now_iso(),
            confirmed_at=utc_now_iso(),
        )
    except (TypeError, ValueError) as exc:
        raise IncompleteDiscoveryCriteriaError(str(exc)) from exc


def next_hypothesis_version(
    hypothesis: ICPHypothesis, changes: dict[str, Any]
) -> ICPHypothesis:
    """Return an edited version without mutating the original hypothesis."""

    allowed = {
        "name",
        "who",
        "context",
        "core_pain",
        "why_pain_matters",
        "current_alternative",
        "value_proposition",
        "trigger",
        "intent_signals",
        "where_to_find",
        "why_may_work",
        "unknowns",
    }
    unknown = set(changes) - allowed
    if unknown:
        raise ValueError(f"unsupported ICP edit fields: {sorted(unknown)}")
    cleaned = dict(changes)
    for field_name in ("intent_signals", "where_to_find", "unknowns"):
        if field_name in cleaned:
            cleaned[field_name] = tuple(cleaned[field_name])
    return replace(
        hypothesis,
        **cleaned,
        version=hypothesis.version + 1,
        status="DRAFT",
        created_at=utc_now_iso(),
    )


def _criteria_themes(context: BusinessContext) -> tuple[str, ...]:
    signal = " ".join(
        (
            context.product_name,
            context.product_description or "",
            context.problem,
            context.strongest_value,
        )
    ).casefold()
    known = (
        "AI video",
        "product marketing",
        "product launches",
        "demo videos",
        "content marketing",
        "web design",
        "no-code",
        "freelancing",
        "portfolio",
        "growth marketing",
        "SaaS",
    )
    selected = [term for term in known if term.casefold() in signal]
    if "video" in signal and "AI video" not in selected:
        selected.insert(0, "video production")
    if len(selected) < 2:
        selected.extend((context.product_name, context.strongest_value[:80]))
    return tuple(dict.fromkeys(item.strip() for item in selected if item.strip()))[:4]


def _criteria_channels(where_to_find: tuple[str, ...]) -> tuple[str, ...]:
    signal = " ".join(where_to_find).casefold()
    channels = []
    if "instagram" in signal:
        channels.append("instagram")
    if "x " in f"{signal} " or "twitter" in signal:
        channels.append("x")
    if "youtube" in signal:
        channels.append("youtube")
    if any(term in signal for term in ("web", "newsletter", "director", "communit", "blog", "linkedin")):
        channels.append("web")
    # Criteria describe a multi-channel test. X and Web are the conservative
    # fallbacks because they cover public conversation and publisher evidence;
    # this does not authorize either channel to execute.
    for fallback in ("x", "web"):
        if len(channels) >= 2:
            break
        if fallback not in channels:
            channels.append(fallback)
    order = ("instagram", "x", "youtube", "web")
    return tuple(channel for channel in order if channel in channels)


_LIVE_SYSTEM_PROMPT = """Generate exactly three specific, testable customer ICP hypotheses from the supplied human-confirmed Business Context.
Return one JSON object with a `hypotheses` array. Every item must contain: name,
who, context, core_pain, why_pain_matters, current_alternative, value_proposition,
trigger, intent_signals (array), where_to_find (array), why_may_work, unknowns
(array), recommended_order (1, 2, or 3), test_priority_reason, and evaluation.
Evaluation must contain integer 0-100 estimates for pain_severity,
problem_frequency, value_proposition_strength, reachability,
intent_signal_availability, potential_commercial_value, and product_fit.
Do not call any hypothesis correct or validated. Make uncertainty explicit. Do not
return queries, creators, outreach, scoring weights, or autonomous actions.
"""
