const CHANNELS = ['instagram', 'x', 'youtube', 'web'];

const PRIORITY_BY_RECORD = {
  creator_001: 'P1', creator_003: 'P2', creator_004: 'P3', creator_005: 'P1',
  creator_007: 'P2', creator_008: 'P2', creator_009: 'Needs Review',
  creator_010: 'Needs Review', creator_011: 'P1', creator_012: 'P1',
};

const ACTIVITY_BY_RECORD = { creator_007: 'low', creator_009: 'unknown' };
const RELEVANCE_BY_RECORD = {
  creator_001: 'high', creator_003: 'moderate', creator_004: 'low', creator_005: 'high',
  creator_007: 'high', creator_008: 'high', creator_009: 'low', creator_010: 'low',
  creator_011: 'high', creator_012: 'high',
};

export function makeId(prefix) {
  return `${prefix}_${crypto.randomUUID().replaceAll('-', '').slice(0, 12)}`;
}

export function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

export function channelStatuses() {
  return [
    { channel: 'controlled', label: 'Controlled Demo', purpose: 'Offline fixture records, always available', configured: true, status: 'connected', environment_variables: [], credential_variable: null },
    { channel: 'instagram', label: 'Instagram', purpose: 'Creator profiles & public content', configured: false, status: 'not_configured', environment_variables: ['APIFY_API_TOKEN'], credential_variable: 'APIFY_API_TOKEN' },
    { channel: 'x', label: 'X', purpose: 'Public posts & author profiles', configured: false, status: 'not_configured', environment_variables: ['X_BEARER_TOKEN'], credential_variable: 'X_BEARER_TOKEN' },
    { channel: 'youtube', label: 'YouTube', purpose: 'Channels & creator content', configured: false, status: 'not_configured', environment_variables: ['YOUTUBE_API_KEY'], credential_variable: 'YOUTUBE_API_KEY' },
    { channel: 'web', label: 'Web', purpose: 'Public partner & publisher discovery', configured: false, status: 'not_configured', environment_variables: ['WEB_SEARCH_API_KEY'], credential_variable: 'WEB_SEARCH_API_KEY' },
  ];
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function detectMarkets(brief) {
  const pairs = [
    [/\b(us|usa|united states)\b/i, 'United States'], [/\bcanada\b/i, 'Canada'],
    [/\b(uk|united kingdom)\b/i, 'United Kingdom'], [/\bireland\b/i, 'Ireland'],
    [/\bfrance\b/i, 'France'], [/\bgermany\b/i, 'Germany'], [/\baustralia\b/i, 'Australia'],
    [/\bsingapore\b/i, 'Singapore'], [/\bglobal\b/i, 'Global'],
  ];
  return pairs.filter(([pattern]) => pattern.test(brief)).map(([, label]) => label);
}

function detectTerms(brief, catalog) {
  const lower = brief.toLowerCase();
  return catalog.filter(([needle]) => lower.includes(needle)).map(([, label]) => label);
}

export function buildCampaignWorkflow(originalBrief) {
  const brief = String(originalBrief || '').trim();
  if (!brief) throw Object.assign(new Error('Describe the partner campaign before generating a search plan.'), { code: 'brief_required' });
  const campaignId = makeId('campaign');
  const searchPlanId = makeId('searchplan');
  const parsedAt = nowIso();
  const markets = unique(detectMarkets(brief));
  const themes = unique(detectTerms(brief, [
    ['ai website', 'AI website tools'], ['no-code', 'no-code'], ['nocode', 'no-code'],
    ['web design', 'web design'], ['portfolio', 'portfolio building'], ['freelanc', 'freelancing'],
    ['creator partnership', 'creator partnerships'], ['growth', 'growth'], ['marketing', 'marketing'],
    ['saas', 'SaaS'], ['ecommerce', 'ecommerce'], ['e-commerce', 'ecommerce'],
  ]));
  const audiences = unique(detectTerms(brief, [
    ['designer', 'designers'], ['freelanc', 'freelancers'], ['founder', 'founders'],
    ['marketer', 'marketers'], ['developer', 'developers'], ['creator', 'creators'],
    ['small business', 'small business owners'], ['agency', 'agencies'],
  ]));
  const exclusions = [];
  const exclusionMatch = brief.match(/(?:exclude|excluding|avoid|not\s+)([^.;]+)/i);
  if (exclusionMatch) exclusions.push(exclusionMatch[1].trim());
  const missing = [];
  if (!markets.length) missing.push('target_markets');
  if (!themes.length) missing.push('content_themes');
  const definition = {
    campaign_id: campaignId,
    goal: 'Discover partners for potential collaborations',
    target_markets: markets,
    content_themes: themes,
    target_audience: audiences,
    exclusions,
  };
  const campaignParse = {
    brief: { campaign_id: campaignId, original_brief: brief },
    definition,
    status: missing.length ? 'incomplete' : 'complete',
    missing_required_fields: missing,
    clarification_questions: missing.map((field) => field === 'target_markets' ? 'Which target market should this campaign focus on?' : 'Which content themes should partners cover?'),
    provenance: { provider: 'mock', model: 'deterministic-campaign-v1', prompt_version: 'campaign-brief-v1', parsed_at: parsedAt },
    error_code: null,
    error_message: null,
  };
  const draft = missing.length ? null : buildDraftPlan(definition, searchPlanId, parsedAt);
  return { workflow_id: makeId('workflow'), original_brief: brief, campaign_parse: campaignParse, draft_search_plan: draft };
}

function buildDraftPlan(definition, searchPlanId, generatedAt) {
  const themes = definition.content_themes;
  const audience = definition.target_audience[0] || 'target audience';
  const market = definition.target_markets.join(' ');
  const primary = themes[0];
  const secondary = themes[1] || themes[0];
  const specs = [
    ['instagram', `${primary} creator`, 'Finds Instagram accounts centered on the campaign theme.', 'core_topic'],
    ['instagram', `${secondary} workflow`, 'Looks for visual process and tutorial content.', 'creator_workflow'],
    ['instagram', `${audience} sharing ${primary}`, 'Looks for self-identified practitioners with explicit topic fit.', 'professional_identity'],
    ['instagram', `${secondary} tips for ${audience}`, 'Targets practical content intended for the campaign audience.', 'use_case'],
    ['x', `building with ${primary}`, 'Finds people discussing hands-on work on X.', 'core_topic'],
    ['x', `${secondary} challenges for ${audience}`, 'Explores questions and pain points relevant to the intended audience.', 'audience_problem'],
    ['x', `${primary} tools for ${audience}`, 'Surfaces practitioners comparing or recommending relevant tools.', 'adjacent_tool'],
    ['x', `${market} ${audience} sharing ${primary}`, 'Combines market and professional-identity context for review.', 'professional_identity'],
    ['youtube', `${primary} tutorial for ${audience}`, 'Finds channels that teach the topic at explanatory length.', 'core_topic'],
    ['youtube', `${secondary} walkthrough for ${audience}`, 'Looks for start-to-finish project videos.', 'creator_workflow'],
    ['youtube', `${primary} tools review`, 'Surfaces channels that review and compare relevant tools.', 'adjacent_tool'],
    ['web', `${primary} blog for ${audience}`, 'Finds publishers and independent blogs covering the theme.', 'core_topic'],
    ['web', `best ${secondary} resources ${market}`, 'Surfaces curated resource pages and directories in the target markets.', 'use_case'],
    ['web', `${audience} writing about ${primary}`, 'Looks for named experts publishing on the campaign theme.', 'professional_identity'],
  ];
  return {
    search_plan_id: searchPlanId,
    campaign_id: definition.campaign_id,
    status: 'draft',
    queries: specs.map(([platform, queryText, rationale, searchAngle], index) => ({
      query_id: `${searchPlanId}_q${String(index + 1).padStart(3, '0')}`,
      campaign_id: definition.campaign_id,
      platform, query_text: queryText, rationale, search_angle: searchAngle,
    })),
    provenance: { provider: 'mock', model: 'deterministic-search-plan-v1', prompt_version: 'draft-search-plan-v1', generated_at: generatedAt },
  };
}

function titleCase(value) {
  return String(value || '').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function buildIcpGeneration(payload) {
  const product = String(payload.product_name || '').trim();
  const problem = String(payload.problem || '').trim();
  const value = String(payload.strongest_value || '').trim();
  const users = String(payload.current_users || '').trim();
  if (!product || !problem || !value || !users) throw Object.assign(new Error('Add enough product, problem, and value context to generate testable ICP hypotheses.'), { code: 'insufficient_business_context' });
  const created = nowIso();
  const contextId = makeId('context');
  const alternative = payload.current_alternatives?.[0] || 'the current manual workflow';
  const trigger = payload.pain_signals?.[0] || 'asking peers for a better workflow';
  const common = {
    version: 1, business_context_id: contextId, audience_type: 'customer',
    context: `They encounter this problem while trying to use or deliver the outcome promised by ${product}.`,
    core_pain: problem,
    why_pain_matters: 'The current workflow consumes time, delays outcomes, and creates an observable reason to look for an alternative.',
    current_alternative: alternative,
    value_proposition: value,
    trigger,
    status: 'DRAFT', created_at: created,
  };
  const hypotheses = [
    {
      ...common, hypothesis_id: makeId('icp'), name: `Active ${titleCase(users)} With Urgent Workflow Pain`,
      who: `${users} who experience the problem repeatedly and are currently trying to improve the workflow.`,
      intent_signals: [trigger, 'comparing tools or workflows', 'requesting recommendations from peers'],
      where_to_find: ['X professional conversations', 'YouTube how-to communities', 'specialist web communities'],
      why_may_work: 'They already recognize the problem and expose observable research or comparison behavior.',
      unknowns: ['Whether the pain is severe enough to fund', 'Whether the described value is differentiated'],
      evaluation: { pain_severity: 84, problem_frequency: 82, value_proposition_strength: 78, reachability: 80, intent_signal_availability: 82, potential_commercial_value: 75, product_fit: 86 },
      recommended_order: 1, test_priority_reason: 'Recognized pain and visible intent make this the fastest hypothesis to test.',
    },
    {
      ...common, hypothesis_id: makeId('icp'), name: `Lean Teams Scaling ${product} Outcomes`,
      who: 'Small cross-functional teams responsible for producing the outcome without a dedicated specialist function.',
      intent_signals: ['hiring for the workflow', 'sharing a new initiative', 'asking for a faster process'],
      where_to_find: ['LinkedIn operator communities', 'X startup conversations', 'industry newsletters'],
      why_may_work: 'A constrained team can understand a time-to-value improvement without changing the whole organization.',
      unknowns: ['Team ownership may be fragmented', 'Budget authority may sit elsewhere'],
      evaluation: { pain_severity: 75, problem_frequency: 79, value_proposition_strength: 82, reachability: 84, intent_signal_availability: 73, potential_commercial_value: 72, product_fit: 81 },
      recommended_order: 2, test_priority_reason: 'Reachability is good, but buying authority and ownership need confirmation.',
    },
    {
      ...common, hypothesis_id: makeId('icp'), name: `Service Teams Delivering ${product} Outcomes`,
      who: 'Specialist service providers who repeat the workflow across multiple clients and must protect delivery margin.',
      intent_signals: ['hiring delivery support', 'promoting a related client service', 'discussing capacity constraints'],
      where_to_find: ['Web service directories', 'agency owner groups', 'YouTube specialist channels'],
      why_may_work: 'Repeated use creates a measurable capacity and margin story.',
      unknowns: ['Requirements may vary across clients', 'Service providers may build their own workflow'],
      evaluation: { pain_severity: 78, problem_frequency: 88, value_proposition_strength: 76, reachability: 68, intent_signal_availability: 65, potential_commercial_value: 88, product_fit: 74 },
      recommended_order: 3, test_priority_reason: 'Potential value is high, while complexity and weaker public signals raise testing cost.',
    },
  ];
  return {
    context: { ...payload, context_id: contextId, created_at: created }, hypotheses,
    status: 'complete', provenance: { provider: 'mock', model: 'deterministic-icp-v1', prompt_version: 'icp-hypotheses-v1', generated_at: created, duration_ms: 1 },
    error_code: null, error_message: null,
  };
}

export function buildIcpSelection(hypothesis, context) {
  const selectedAt = nowIso();
  const selection = { selection_id: makeId('selection'), hypothesis_id: hypothesis.hypothesis_id, hypothesis_version: hypothesis.version, status: 'TESTING', selected_at: selectedAt };
  const description = String(context.product_description || '').toLowerCase();
  const themes = unique(['no-code', 'portfolio', 'AI tools', 'growth'].filter((term) => description.includes(term.toLowerCase()))).slice(0, 3);
  const criteria = {
    criteria_id: makeId('criteria'), source_criteria_id: null, hypothesis_id: hypothesis.hypothesis_id,
    hypothesis_version: hypothesis.version, hypothesis_name: hypothesis.name, discovery_subject: 'partner',
    partner_profile: `Partners who publish credible content about ${(themes.length ? themes : ['the relevant workflow']).join(', ')} and can reach people matching this customer hypothesis: ${hypothesis.who}`,
    goal: `Discover partners who can help reach and validate ${hypothesis.name}.`,
    target_markets: context.target_markets?.length ? context.target_markets : ['United States', 'Canada'],
    content_themes: themes.length ? themes : ['workflow improvement'],
    target_audience: [hypothesis.name, hypothesis.who], intent_signals: hypothesis.intent_signals,
    exclusions: [], channels: ['instagram', 'x', 'youtube', 'web'], status: 'draft',
    criteria_version: 'icp-to-partner-criteria-v1', created_at: selectedAt, confirmed_at: null,
  };
  return { selection, criteria, hypothesis, context };
}

export function criteriaToWorkflow(savedSelection, editedCriteria) {
  const confirmedAt = nowIso();
  const criteria = { ...savedSelection.criteria, ...editedCriteria, status: 'confirmed', confirmed_at: confirmedAt };
  const brief = `${criteria.goal} Target markets: ${criteria.target_markets.join(', ')}. Content themes: ${criteria.content_themes.join(', ')}. Audiences: ${criteria.target_audience.join(', ')}.`;
  const workflow = buildCampaignWorkflow(brief);
  workflow.campaign_parse.definition = {
    ...workflow.campaign_parse.definition,
    goal: criteria.goal,
    target_markets: criteria.target_markets,
    content_themes: criteria.content_themes,
    target_audience: criteria.target_audience,
    exclusions: criteria.exclusions || [],
  };
  workflow.draft_search_plan = buildDraftPlan(workflow.campaign_parse.definition, makeId('searchplan'), confirmedAt);
  workflow.icp_context = { hypothesis_id: savedSelection.hypothesis.hypothesis_id, hypothesis_version: savedSelection.hypothesis.version, hypothesis_name: savedSelection.hypothesis.name, criteria_id: criteria.criteria_id };
  return { criteria, workflow };
}

function normalizedProfileUrl(raw) {
  const url = new URL(raw.profile_url);
  let host = url.hostname.toLowerCase().replace(/^www\./, '');
  if (host === 'twitter.com') host = 'x.com';
  const path = url.pathname.replace(/\/+$/, '').toLowerCase();
  return `https://${host === 'instagram.com' ? 'www.instagram.com' : host}${path}`;
}

export function deduplicateFixture(rawProfiles) {
  const seen = new Set();
  return rawProfiles.filter((raw) => {
    const key = `${raw.platform}:${normalizedProfileUrl(raw)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function marketSignals(raw) {
  const text = `${raw.bio_text || ''} ${(raw.content_samples || []).map((item) => item.text).join(' ')}`;
  const lower = text.toLowerCase();
  if (raw.record_id === 'creator_009') return { market: 'US', fit: 'conflicting', evidence: ['Public text contains conflicting market references.'] };
  if (lower.includes('são paulo')) return { market: 'São Paulo', fit: 'outside', evidence: ['Observed market term: São Paulo.'] };
  for (const [needle, label] of [['seattle', 'Seattle'], ['vancouver', 'Vancouver'], ['toronto', 'Toronto'], ['canadian', 'Canada'], ['canada', 'Canada'], ['us ', 'US']]) {
    if (lower.includes(needle)) return { market: label, fit: 'target', evidence: [`Observed market term: ${label}.`] };
  }
  return { market: null, fit: 'unknown', evidence: [] };
}

function audienceFor(raw, relevance) {
  if (relevance === 'low') return ['audience unclear from available public evidence'];
  const text = `${raw.bio_text || ''} ${(raw.content_samples || []).map((item) => item.text).join(' ')}`.toLowerCase();
  return unique([
    /portfolio|personal website/.test(text) && 'people building portfolios or personal websites',
    /freelanc|independent creative/.test(text) && 'freelance designers and independent creatives',
    /web design|framer|no-code/.test(text) && 'web designers and no-code builders',
    /ai .*design|ai .*website|ai tools/.test(text) && 'creators exploring AI-assisted design tools',
  ]);
}

function partnerType(followers) {
  if (followers == null) return { partner_type: 'creator', confidence: 'demo', basis: 'No follower count was provided; the broad creator label is retained.' };
  if (followers >= 100000) return { partner_type: 'kol', confidence: 'demo', basis: `Follower count ${followers.toLocaleString('en-US')} is at least 100,000.` };
  if (followers >= 10000) return { partner_type: 'influencer', confidence: 'demo', basis: `Follower count ${followers.toLocaleString('en-US')} is at least 10,000 but under 100,000.` };
  return { partner_type: 'micro_influencer', confidence: 'demo', basis: `Follower count ${followers.toLocaleString('en-US')} is under 10,000.` };
}

function signal(value, reason, evidence = []) { return { value, reason, evidence }; }

export function buildCreatorRecord(raw, provenance) {
  const recordId = `demo_${raw.record_id}`;
  const activity = ACTIVITY_BY_RECORD[raw.record_id] || 'high';
  const relevance = RELEVANCE_BY_RECORD[raw.record_id] || 'low';
  const market = marketSignals(raw);
  const actionAvailable = Boolean(raw.external_urls?.length) || /collab|contact|partnership|media kit|sponsor/i.test(raw.bio_text || '');
  const priority = PRIORITY_BY_RECORD[raw.record_id] || 'Needs Review';
  const audience = audienceFor(raw, relevance);
  const followerLabel = raw.follower_count == null ? 'The source did not provide a follower count.' : `Observed follower count is ${raw.follower_count.toLocaleString('en-US')}; audience size is context, not a quality verdict.`;
  const reasons = priority === 'P1'
    ? ['High relevance and strong publishing momentum support contacting first.', actionAvailable ? 'A public collaboration/contact path improves actionability.' : 'No contact path was observed; creator quality and priority were not penalized for it.', followerLabel]
    : priority === 'P2'
      ? [relevance === 'high' ? 'Strong relevance supports outreach with a small evidence caveat.' : 'Strong publishing momentum raises a moderately relevant partner\'s priority.', market.fit === 'outside' ? 'The partner is outside the primary market, so priority is reduced but not rejected.' : (actionAvailable ? 'A public collaboration/contact path improves actionability.' : 'No contact path was observed.'), followerLabel]
      : priority === 'P3'
        ? ['The partner is usable but currently offers weaker campaign relevance.', 'A public collaboration/contact path improves actionability.', followerLabel]
        : [raw.record_id === 'creator_010' ? 'The public text contains obvious spam-style claims.' : 'Market evidence conflicts and needs a human decision.', actionAvailable ? 'A public collaboration/contact path improves actionability.' : 'No contact path was observed; partner quality and priority were not penalized for it.', followerLabel];
  const audienceSize = raw.follower_count == null ? 'unknown' : raw.follower_count >= 100000 ? 'large' : raw.follower_count >= 10000 ? 'medium' : 'small';
  const derived = {
    record_id: recordId,
    activity: signal(activity, activity === 'high' ? 'Multiple recent samples show strong publishing momentum.' : activity === 'low' ? 'Public samples are relevant but not recent.' : 'Available dates are insufficient for an activity conclusion.', activity === 'unknown' ? [] : [`${raw.content_samples?.length || 0} public content samples were observed.`]),
    content_relevance: signal(relevance, relevance === 'high' ? 'Several campaign themes are directly observable.' : relevance === 'moderate' ? 'Some campaign themes are observable.' : 'Direct campaign relevance is weak or unclear.', relevance === 'low' ? [] : ['Portfolio, web-design, no-code, or AI-tool language is present.']),
    audience_size: signal(audienceSize, followerLabel),
    market: signal(market.fit, market.fit === 'target' ? 'Public text contains target-market evidence.' : market.fit === 'outside' ? 'Public text points outside the primary market.' : market.fit === 'conflicting' ? 'Public market evidence conflicts.' : 'No reliable market evidence was observed.', market.evidence),
    actionability: signal(actionAvailable ? 'available' : 'not_observed', actionAvailable ? 'A public path for further partnership research is visible.' : 'No public contact path was observed.', actionAvailable ? ['Public contact or collaboration evidence is visible.'] : []),
    record_quality: signal(raw.record_id === 'creator_010' ? 'needs_review' : 'usable', raw.record_id === 'creator_010' ? 'Spam-style claims require human review.' : 'The record has a valid profile identity and usable public evidence.'),
    extracted_at: provenance.completedAt,
  };
  const aiEvidence = relevance === 'low' ? ['Available public evidence does not support a narrow audience conclusion.'] : [
    'Public content explicitly discusses portfolios, websites, freelance work, or creator workflows.',
    'The audience description is inferred from observed public content and remains a hypothesis.',
  ];
  const inference = { record_id: recordId, likely_audience: audience, evidence: aiEvidence, confidence: relevance === 'low' ? 'low' : 'high', provider: 'mock', model: 'deterministic-audience-v1', prompt_version: 'audience-only-v1', inferred_at: provenance.completedAt };
  const type = partnerType(raw.follower_count);
  const observed = {
    ...raw, record_id: recordId, normalized_profile_url: normalizedProfileUrl(raw),
    run_id: provenance.runId, query_id: provenance.queryId, retrieved_at: provenance.completedAt,
    campaign_id: provenance.campaignId, approved_search_plan_id: provenance.approvedPlanId,
    source_query_id: provenance.sourceQueryId, query_text: provenance.queryText, search_angle: provenance.searchAngle,
  };
  const detail = {
    record_id: recordId, observed_facts: observed, derived_signals: derived,
    ai_audience_inference: inference,
    priority_decision: { priority, reasons, signal_evidence: { ...derived, audience_inference: { likely_audience: audience, evidence: aiEvidence, confidence: inference.confidence } }, decided_at: provenance.completedAt },
    human_decision: null, partner_type: type,
    priority_summary: { priority, headline: priority, reasons: reasons.slice(0, 3).map((reason) => reason.split(';')[0].replace(/\.$/, '')) },
    key_signals: ['activity', 'content_relevance', 'audience_size', 'market', 'actionability'].map((key) => ({ signal: key === 'content_relevance' ? 'relevance' : key === 'audience_size' ? 'audience' : key, value: derived[key].value, summary: derived[key].reason, evidence: derived[key].evidence })),
    ai_audience_summary: { likely_audience: audience, confidence: inference.confidence, evidence: aiEvidence, provider: inference.provider, model: inference.model },
    content_samples_preview: Math.min(3, raw.content_samples?.length || 0),
  };
  const handle = `@${new URL(raw.profile_url).pathname.split('/').filter(Boolean).at(-1).toLowerCase()}`;
  const summary = {
    record_id: recordId, display_name: raw.display_name, handle, platform: raw.platform, channel: raw.platform,
    partner_type: type.partner_type, partner_type_confidence: type.confidence, profile_url: raw.profile_url,
    follower_count: raw.follower_count, bio_text: raw.bio_text, market: market.market, market_fit: market.fit,
    activity, relevance, likely_audience: audience, audience_confidence: inference.confidence,
    priority, priority_reasons: reasons, review_status: 'unreviewed', reviewed_at: null, created_at: provenance.completedAt,
  };
  return { record_id: recordId, summary, detail };
}

function reviewApprovedQueries(workflow, actions) {
  const draft = workflow.draft_search_plan;
  if (!draft || draft.status !== 'draft') throw Object.assign(new Error('Only a complete Draft Search Plan can be reviewed.'), { code: 'draft_plan_missing' });
  if (!Array.isArray(actions) || actions.length !== draft.queries.length) throw Object.assign(new Error('Review every query before execution.'), { code: 'query_review_invalid' });
  const actionMap = new Map(actions.map((action) => [action.query_id, action]));
  const reviewedAt = nowIso();
  const reviewedQueries = [];
  const approved = [];
  const finalSeen = new Set();
  for (const query of draft.queries) {
    const action = actionMap.get(query.query_id);
    if (!action || !['approved', 'edited', 'rejected'].includes(action.decision)) throw Object.assign(new Error('Review every query before execution.'), { code: 'query_review_invalid' });
    const finalText = action.decision === 'edited' ? String(action.edited_query_text || '').trim() : query.query_text;
    if (action.decision === 'edited' && !finalText) throw Object.assign(new Error('Edited queries need final text.'), { code: 'query_review_invalid' });
    reviewedQueries.push({ original_query: query, final_query_text: finalText, decision: action.decision, human_comment: action.human_comment || null, reviewed_at: reviewedAt });
    const dedupKey = `${query.platform}:${finalText.toLowerCase()}`;
    if (action.decision !== 'rejected' && !finalSeen.has(dedupKey)) {
      finalSeen.add(dedupKey);
      approved.push({ ...query, query_text: finalText, review_decision: action.decision });
    }
  }
  return { reviewedAt, reviewedQueries, approved };
}

export function buildControlledRun(workflow, actions, rawProfiles, existingRecordIds = new Set()) {
  const { reviewedAt, reviewedQueries, approved } = reviewApprovedQueries(workflow, actions);
  const reviewId = makeId('review');
  const approvedPlanId = makeId('approvedplan');
  const runId = makeId('discovery');
  const completedAt = nowIso();
  const executable = approved.map((query, index) => ({ query_id: `${approvedPlanId}_q${String(index + 1).padStart(3, '0')}`, source_query_id: query.query_id, campaign_id: query.campaign_id, platform: query.platform, query_text: query.query_text, search_angle: query.search_angle, review_decision: query.review_decision }));
  const queryHistory = [];
  const distribution = { instagram: [[2, 0], [2, 1], [1, 0], [1, 0]], x: [[2, 0], [2, 0], [1, 1], [1, 0]], youtube: [[0, 0], [0, 0], [0, 0]], web: [[0, 0], [0, 0], [0, 0]] };
  const platformCounts = Object.fromEntries(CHANNELS.map((platform) => [platform, 0]));
  const newCapacity = {};
  for (const query of executable) {
    const index = platformCounts[query.platform]++;
    const [retrieved, intrinsicDuplicate] = distribution[query.platform]?.[index] || [0, 0];
    newCapacity[query.platform] = (newCapacity[query.platform] || 0) + Math.max(0, retrieved - intrinsicDuplicate);
    queryHistory.push({ query, retrieved, intrinsicDuplicate, index });
  }
  const deduped = deduplicateFixture(rawProfiles);
  const selectedRaw = [];
  for (const platform of CHANNELS) selectedRaw.push(...deduped.filter((raw) => raw.platform === platform).slice(0, newCapacity[platform] || 0));
  const newRaw = selectedRaw.filter((raw) => !existingRecordIds.has(`demo_${raw.record_id}`));
  const newByPlatform = Object.fromEntries(CHANNELS.map((platform) => [platform, newRaw.filter((raw) => raw.platform === platform).length]));
  const histories = queryHistory.map(({ query, retrieved, intrinsicDuplicate }) => {
    const fresh = Math.min(Math.max(0, retrieved - intrinsicDuplicate), newByPlatform[query.platform] || 0);
    newByPlatform[query.platform] -= fresh;
    return {
      run_id: runId, campaign_id: workflow.campaign_parse.definition.campaign_id, approved_search_plan_id: approvedPlanId,
      query_id: query.query_id, platform: query.platform, source_connector: 'controlled_fixture_v1', query_text: query.query_text,
      search_angle: query.search_angle, execution_status: retrieved ? 'SUCCESS_WITH_RESULTS' : 'SUCCESS_ZERO_RESULTS',
      retrieved, duplicates: retrieved - fresh, new_creators: fresh, new_creator_yield: retrieved ? fresh / retrieved : 0,
      error_code: null, started_at: completedAt, completed_at: completedAt,
    };
  });
  const queryForPlatform = Object.fromEntries(executable.filter((query) => ['instagram', 'x'].includes(query.platform)).map((query) => [query.platform, query]));
  const creatorRecords = newRaw.map((raw) => {
    const query = queryForPlatform[raw.platform];
    return buildCreatorRecord(raw, { runId, queryId: query?.query_id || null, completedAt, campaignId: workflow.campaign_parse.definition.campaign_id, approvedPlanId, sourceQueryId: query?.source_query_id || null, queryText: query?.query_text || null, searchAngle: query?.search_angle || null });
  });
  const priorityCounts = { P1: 0, P2: 0, P3: 0, 'Needs Review': 0 };
  creatorRecords.forEach((record) => { priorityCounts[record.summary.priority] += 1; });
  const retrieved = histories.reduce((total, row) => total + row.retrieved, 0);
  const duplicates = histories.reduce((total, row) => total + row.duplicates, 0);
  const runSummary = { run_id: runId, mode: 'controlled', run_status: 'COMPLETED', run_error_code: null, retrieved, duplicates, new_creators: creatorRecords.length, new_creator_yield: retrieved ? creatorRecords.length / retrieved : 0, signals: creatorRecords.length, audience_inferences: creatorRecords.length, priority_counts: priorityCounts, query_history: histories };
  return {
    review: { review_id: reviewId, draft_search_plan_id: workflow.draft_search_plan.search_plan_id, campaign_id: workflow.campaign_parse.definition.campaign_id, status: 'complete', reviewed_queries: reviewedQueries, completed_at: reviewedAt },
    approved_search_plan: { approved_search_plan_id: approvedPlanId, source_draft_search_plan_id: workflow.draft_search_plan.search_plan_id, review_id: reviewId, campaign_id: workflow.campaign_parse.definition.campaign_id, status: 'approved', queries: executable, approved_at: reviewedAt },
    run_summary: runSummary, creator_records: creatorRecords,
  };
}

export function applyHumanDecision(record, decision) {
  const summary = {
    ...record.summary,
    review_status: decision.status,
    reviewed_at: decision.reviewed_at,
    review_reason: decision.structured_reason || null,
    review_comment: decision.comment || null,
  };
  const detail = { ...record.detail, human_decision: decision };
  return { ...record, summary, detail };
}

export function buildWorkspace(creators, runs, hypotheses = [], currentSelection = null) {
  const summaries = creators.map((record) => {
    const observed = record.detail?.observed_facts || {};
    return {
      ...record.summary,
      run_id: record.summary.run_id || observed.run_id || null,
      query_id: record.summary.query_id || observed.query_id || null,
      source_query_id: record.summary.source_query_id || observed.source_query_id || null,
      query_text: record.summary.query_text || observed.query_text || null,
      search_angle: record.summary.search_angle || observed.search_angle || null,
      campaign_id: record.summary.campaign_id || observed.campaign_id || null,
      discovery_mode: record.summary.discovery_mode || observed.discovery_mode || null,
      has_signals: Boolean(record.detail?.derived_signals),
      has_audience_inference: Boolean(record.detail?.ai_audience_inference),
      has_priority_decision: Boolean(record.detail?.priority_decision),
    };
  });
  const priorityCounts = { P1: 0, P2: 0, P3: 0, 'Needs Review': 0 };
  const channelCounts = { instagram: 0, x: 0, youtube: 0, web: 0 };
  const partnerTypeCounts = { creator: 0, kol: 0, influencer: 0, micro_influencer: 0, affiliate: 0, community: 0, media: 0, industry_expert: 0 };
  summaries.forEach((item) => { priorityCounts[item.priority] += 1; channelCounts[item.channel] += 1; partnerTypeCounts[item.partner_type] += 1; });
  const latestRun = runs.at(-1)?.run_summary || null;
  const runRows = runs.map((run) => ({ run_id: run.run_summary.run_id, campaign_id: run.approved_search_plan?.campaign_id || null, approved_search_plan_id: run.approved_search_plan?.approved_search_plan_id || null, discovery_mode: run.run_summary.mode, status: run.run_summary.run_status, error_code: run.run_summary.run_error_code, started_at: run.completed_at, completed_at: run.completed_at, retrieved: run.run_summary.retrieved, duplicates: run.run_summary.duplicates, new_creators: run.run_summary.new_creators, new_creator_yield: run.run_summary.new_creator_yield }));
  const currentHypothesis = currentSelection?.hypothesis || null;
  return {
    overview: { total_creators: summaries.length, priority_counts: priorityCounts, review_count: summaries.filter((item) => item.review_status !== 'unreviewed').length, latest_run: runRows.at(-1) || null },
    latest_discovery: latestRun ? { retrieved: latestRun.retrieved, duplicates: latestRun.duplicates, new_partners: latestRun.new_creators, new_partner_yield: latestRun.new_creator_yield, mode: latestRun.mode, status: latestRun.run_status, completed_at: runs.at(-1).completed_at, run_id: latestRun.run_id } : null,
    partner_pool: { total: summaries.length, priority_counts: priorityCounts, reviewed: summaries.filter((item) => item.review_status !== 'unreviewed').length, unreviewed: summaries.filter((item) => item.review_status === 'unreviewed').length, channel_counts: channelCounts, partner_type_counts: partnerTypeCounts },
    runs: runRows,
    query_history: runs.flatMap((run) => run.run_summary.query_history || []).reverse(),
    creators: summaries,
    icp_workspace: { current: currentHypothesis ? { hypothesis: currentHypothesis, selection: currentSelection.selection, criteria: currentSelection.criteria, runs: runRows.filter((row) => row.icp_hypothesis_id === currentHypothesis.hypothesis_id) } : null, hypotheses },
    workspace: { database_name: 'growth-os-sites-d1', providers: { controlled: { configured: true, label: 'Offline fixtures' }, instagram: { configured: false, label: 'Apify Instagram' }, x: { configured: false, label: 'X API recent search' } }, channels: channelStatuses() },
  };
}

export { CHANNELS };
