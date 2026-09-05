import { env } from 'cloudflare:workers';
import fixture from '@/fixtures/controlled_demo_minimal.json';
import {
  applyHumanDecision,
  buildCampaignWorkflow,
  buildControlledRun,
  buildIcpGeneration,
  buildIcpSelection,
  buildWorkspace,
  channelStatuses,
  criteriaToWorkflow,
  makeId,
  nowIso,
  refreshControlledDemoRecord,
} from './core.mjs';

const SESSION_COOKIE = 'growth_os_session';
const MAX_BODY_BYTES = 128 * 1024;
let schemaReady = false;

const schemaStatements = [
  `CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (workflow_id, session_id)
  )`,
  'CREATE INDEX IF NOT EXISTS workflows_session_created_idx ON workflows (session_id, created_at)',
  `CREATE TABLE IF NOT EXISTS discovery_runs (
    run_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (run_id, session_id)
  )`,
  'CREATE INDEX IF NOT EXISTS discovery_runs_session_completed_idx ON discovery_runs (session_id, completed_at)',
  `CREATE TABLE IF NOT EXISTS creators (
    record_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    priority TEXT NOT NULL,
    channel TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (record_id, session_id)
  )`,
  'CREATE INDEX IF NOT EXISTS creators_session_priority_idx ON creators (session_id, priority)',
  'CREATE INDEX IF NOT EXISTS creators_session_channel_idx ON creators (session_id, channel)',
  `CREATE TABLE IF NOT EXISTS creator_reviews (
    review_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    status TEXT NOT NULL,
    structured_reason TEXT,
    comment TEXT,
    reviewed_at TEXT NOT NULL
  )`,
  'CREATE INDEX IF NOT EXISTS creator_reviews_session_record_idx ON creator_reviews (session_id, record_id, reviewed_at)',
  `CREATE TABLE IF NOT EXISTS icp_hypotheses (
    hypothesis_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (hypothesis_id, version, session_id)
  )`,
  'CREATE INDEX IF NOT EXISTS icp_hypotheses_session_context_idx ON icp_hypotheses (session_id, context_id)',
  `CREATE TABLE IF NOT EXISTS icp_selections (
    selection_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,
    hypothesis_version INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    selected_at TEXT NOT NULL
  )`,
  'CREATE INDEX IF NOT EXISTS icp_selections_session_selected_idx ON icp_selections (session_id, selected_at)',
];

function getDatabase(): D1Database {
  if (!env.DB) throw Object.assign(new Error('Hosted persistence is unavailable.'), { code: 'storage_unavailable' });
  return env.DB;
}

async function ensureSchema(database: D1Database) {
  if (schemaReady) return;
  await database.batch(schemaStatements.map((statement) => database.prepare(statement)));
  schemaReady = true;
}

function sessionFor(request: Request) {
  const cookies = request.headers.get('cookie') || '';
  const match = cookies.match(new RegExp(`(?:^|;\\s*)${SESSION_COOKIE}=([a-zA-Z0-9_-]+)`));
  return { sessionId: match?.[1] || makeId('visitor'), isNew: !match };
}

function responseHeaders(sessionId: string, isNew: boolean) {
  const headers = new Headers({
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
  });
  if (isNew) headers.set('Set-Cookie', `${SESSION_COOKIE}=${sessionId}; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax`);
  return headers;
}

function json(payload: unknown, status: number, sessionId: string, isNew: boolean) {
  return new Response(JSON.stringify(payload), { status, headers: responseHeaders(sessionId, isNew) });
}

async function body(request: Request) {
  const length = Number(request.headers.get('content-length') || '0');
  if (length > MAX_BODY_BYTES) throw Object.assign(new Error('Request body is too large.'), { code: 'invalid_request', status: 413 });
  const value = await request.json();
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw Object.assign(new Error('Request body must be a JSON object.'), { code: 'invalid_request', status: 400 });
  return value as Record<string, unknown>;
}

async function rows<T>(statement: D1PreparedStatement) {
  const result = await statement.all<T>();
  return result.results || [];
}

function parsed<T>(value: string) { return JSON.parse(value) as T; }

async function loadCreators(database: D1Database, sessionId: string) {
  const creatorRows = await rows<{ payload_json: string }>(database.prepare('SELECT payload_json FROM creators WHERE session_id = ? ORDER BY created_at ASC').bind(sessionId));
  const reviewRows = await rows<{ record_id: string; status: string; structured_reason: string | null; comment: string | null; reviewed_at: string }>(database.prepare('SELECT record_id, status, structured_reason, comment, reviewed_at FROM creator_reviews WHERE session_id = ? ORDER BY reviewed_at ASC').bind(sessionId));
  const latest = new Map(reviewRows.map((review) => [review.record_id, review]));
  return creatorRows
    .map((row) => refreshControlledDemoRecord(parsed<any>(row.payload_json), fixture))
    .map((record) => latest.has(record.record_id) ? applyHumanDecision(record, latest.get(record.record_id)) : record);
}

async function loadRuns(database: D1Database, sessionId: string) {
  const result = await rows<{ payload_json: string; completed_at: string }>(database.prepare('SELECT payload_json, completed_at FROM discovery_runs WHERE session_id = ? ORDER BY completed_at ASC').bind(sessionId));
  return result.map((row) => ({ ...parsed<any>(row.payload_json), completed_at: row.completed_at }));
}

async function loadHypotheses(database: D1Database, sessionId: string) {
  const result = await rows<{ payload_json: string }>(database.prepare('SELECT payload_json FROM icp_hypotheses WHERE session_id = ? ORDER BY created_at ASC').bind(sessionId));
  return result.map((row) => parsed<any>(row.payload_json));
}

async function loadCurrentSelection(database: D1Database, sessionId: string) {
  const result = await database.prepare('SELECT payload_json FROM icp_selections WHERE session_id = ? ORDER BY selected_at DESC LIMIT 1').bind(sessionId).first<{ payload_json: string }>();
  return result ? parsed<any>(result.payload_json) : null;
}

async function bootstrap(database: D1Database, sessionId: string) {
  const [creators, runs, hypothesisRecords, currentSelection] = await Promise.all([
    loadCreators(database, sessionId), loadRuns(database, sessionId), loadHypotheses(database, sessionId), loadCurrentSelection(database, sessionId),
  ]);
  return buildWorkspace(creators, runs, hypothesisRecords.map((item) => item.hypothesis), currentSelection);
}

async function saveWorkflow(database: D1Database, sessionId: string, workflow: any) {
  await database.prepare('INSERT OR REPLACE INTO workflows (workflow_id, session_id, payload_json, created_at) VALUES (?, ?, ?, ?)')
    .bind(workflow.workflow_id, sessionId, JSON.stringify(workflow), nowIso()).run();
}

async function routeGet(database: D1Database, sessionId: string, segments: string[]) {
  if (segments.length === 1 && segments[0] === 'health') return { status: 200, payload: { status: 'ok', runtime: 'sites' } };
  if (segments.length === 1 && segments[0] === 'bootstrap') return { status: 200, payload: await bootstrap(database, sessionId) };
  if (segments.length === 1 && segments[0] === 'data-sources') return { status: 200, payload: { channels: channelStatuses().filter((item) => item.channel !== 'controlled') } };
  if (segments.length === 2 && segments[0] === 'creators') {
    const result = await database.prepare('SELECT payload_json FROM creators WHERE record_id = ? AND session_id = ?').bind(segments[1], sessionId).first<{ payload_json: string }>();
    if (!result) throw Object.assign(new Error('Partner record not found.'), { code: 'creator_not_found', status: 404 });
    const record = refreshControlledDemoRecord(parsed<any>(result.payload_json), fixture);
    const review = await database.prepare('SELECT status, structured_reason, comment, reviewed_at FROM creator_reviews WHERE record_id = ? AND session_id = ? ORDER BY reviewed_at DESC LIMIT 1').bind(segments[1], sessionId).first<any>();
    return { status: 200, payload: review ? applyHumanDecision(record, review).detail : record.detail };
  }
  throw Object.assign(new Error('Route not found.'), { code: 'not_found', status: 404 });
}

async function routePost(database: D1Database, sessionId: string, segments: string[], payload: Record<string, any>) {
  if (segments.join('/') === 'search-plan') {
    const workflow = buildCampaignWorkflow(payload.original_brief);
    await saveWorkflow(database, sessionId, workflow);
    return { status: 201, payload: workflow };
  }
  if (segments.join('/') === 'icp/generate') {
    if (payload.provider_mode && payload.provider_mode !== 'mock') throw Object.assign(new Error('Live ICP generation is not configured in the hosted portfolio demo.'), { code: 'icp_provider_not_configured' });
    const result = buildIcpGeneration(payload);
    await database.batch(result.hypotheses.map((hypothesis: any) => database.prepare('INSERT INTO icp_hypotheses (hypothesis_id, version, session_id, context_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)')
      .bind(hypothesis.hypothesis_id, hypothesis.version, sessionId, hypothesis.business_context_id, JSON.stringify({ hypothesis, context: result.context }), hypothesis.created_at)));
    return { status: 201, payload: result };
  }
  if (segments.join('/') === 'icp/edit') {
    const source = await database.prepare('SELECT payload_json FROM icp_hypotheses WHERE hypothesis_id = ? AND version = ? AND session_id = ?').bind(payload.hypothesis_id, Number(payload.version), sessionId).first<{ payload_json: string }>();
    if (!source) throw Object.assign(new Error('ICP hypothesis not found.'), { code: 'icp_not_found', status: 404 });
    const record = parsed<any>(source.payload_json);
    const allowed = ['name', 'who', 'core_pain', 'value_proposition', 'unknowns'];
    const changes = Object.fromEntries(Object.entries(payload.changes || {}).filter(([key]) => allowed.includes(key)));
    if (!Object.keys(changes).length) throw Object.assign(new Error('ICP edits are required.'), { code: 'invalid_icp_edit' });
    const hypothesis = { ...record.hypothesis, ...changes, version: record.hypothesis.version + 1, created_at: nowIso() };
    await database.prepare('INSERT INTO icp_hypotheses (hypothesis_id, version, session_id, context_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)')
      .bind(hypothesis.hypothesis_id, hypothesis.version, sessionId, hypothesis.business_context_id, JSON.stringify({ ...record, hypothesis }), hypothesis.created_at).run();
    return { status: 201, payload: hypothesis };
  }
  if (segments.join('/') === 'icp/select') {
    const source = await database.prepare('SELECT payload_json FROM icp_hypotheses WHERE hypothesis_id = ? AND version = ? AND session_id = ?').bind(payload.hypothesis_id, Number(payload.version), sessionId).first<{ payload_json: string }>();
    if (!source) throw Object.assign(new Error('ICP hypothesis not found.'), { code: 'icp_not_found', status: 404 });
    const record = parsed<any>(source.payload_json);
    const selected = buildIcpSelection(record.hypothesis, record.context);
    await database.prepare('INSERT INTO icp_selections (selection_id, session_id, hypothesis_id, hypothesis_version, payload_json, selected_at) VALUES (?, ?, ?, ?, ?, ?)')
      .bind(selected.selection.selection_id, sessionId, record.hypothesis.hypothesis_id, record.hypothesis.version, JSON.stringify(selected), selected.selection.selected_at).run();
    return { status: 201, payload: { selection: selected.selection, criteria: selected.criteria } };
  }
  if (segments.join('/') === 'icp/criteria/confirm') {
    const selectionRows = await rows<{ payload_json: string }>(database.prepare('SELECT payload_json FROM icp_selections WHERE session_id = ? ORDER BY selected_at DESC').bind(sessionId));
    const selected = selectionRows.map((row) => parsed<any>(row.payload_json)).find((item) => item.criteria.criteria_id === payload.criteria_id);
    if (!selected) throw Object.assign(new Error('Discovery criteria not found.'), { code: 'incomplete_discovery_criteria', status: 404 });
    const required = ['partner_profile', 'goal', 'target_markets', 'content_themes', 'target_audience', 'channels'];
    if (required.some((key) => !payload.criteria?.[key] || (Array.isArray(payload.criteria[key]) && !payload.criteria[key].length))) throw Object.assign(new Error('Complete the required discovery criteria before confirming.'), { code: 'incomplete_discovery_criteria' });
    const { criteria, workflow } = criteriaToWorkflow(selected, payload.criteria);
    const updated = { ...selected, criteria };
    await database.prepare('UPDATE icp_selections SET payload_json = ? WHERE selection_id = ? AND session_id = ?').bind(JSON.stringify(updated), selected.selection.selection_id, sessionId).run();
    await saveWorkflow(database, sessionId, workflow);
    return { status: 201, payload: workflow };
  }
  if (segments.join('/') === 'run-discovery') {
    const source = await database.prepare('SELECT payload_json FROM workflows WHERE workflow_id = ? AND session_id = ?').bind(payload.workflow_id, sessionId).first<{ payload_json: string }>();
    if (!source) throw Object.assign(new Error('This draft is no longer available. Generate it again.'), { code: 'workflow_not_found', status: 404 });
    if (payload.mode === 'live') {
      if (!payload.confirm_live) throw Object.assign(new Error('Confirm live channel usage before execution.'), { code: 'live_confirmation_required' });
      throw Object.assign(new Error('Live providers are intentionally not configured in this hosted portfolio demo. Use Controlled Demo.'), { code: 'provider_not_configured' });
    }
    const existing = await rows<{ record_id: string }>(database.prepare('SELECT record_id FROM creators WHERE session_id = ?').bind(sessionId));
    const result = buildControlledRun(parsed<any>(source.payload_json), payload.actions, fixture, new Set(existing.map((row) => row.record_id)));
    if (result.creator_records.length) {
      await database.batch(result.creator_records.map((record: any) => database.prepare('INSERT OR IGNORE INTO creators (record_id, session_id, payload_json, priority, channel, created_at) VALUES (?, ?, ?, ?, ?, ?)')
        .bind(record.record_id, sessionId, JSON.stringify(record), record.summary.priority, record.summary.channel, record.summary.created_at)));
    }
    const completedAt = result.run_summary.query_history[0]?.completed_at || nowIso();
    await database.prepare('INSERT INTO discovery_runs (run_id, session_id, payload_json, completed_at) VALUES (?, ?, ?, ?)')
      .bind(result.run_summary.run_id, sessionId, JSON.stringify({ review: result.review, approved_search_plan: result.approved_search_plan, run_summary: result.run_summary }), completedAt).run();
    return { status: 201, payload: { review: result.review, approved_search_plan: result.approved_search_plan, run_summary: result.run_summary } };
  }
  if (segments.length === 3 && segments[0] === 'creators' && segments[2] === 'review') {
    if (!['approve', 'reject', 'needs_review'].includes(payload.status)) throw Object.assign(new Error('Choose a valid review decision.'), { code: 'invalid_review' });
    const exists = await database.prepare('SELECT record_id FROM creators WHERE record_id = ? AND session_id = ?').bind(segments[1], sessionId).first();
    if (!exists) throw Object.assign(new Error('Partner record not found.'), { code: 'creator_not_found', status: 404 });
    const decision = { review_id: makeId('creatorreview'), record_id: segments[1], status: payload.status, structured_reason: payload.structured_reason || null, comment: payload.comment || null, reviewed_at: nowIso() };
    await database.prepare('INSERT INTO creator_reviews (review_id, record_id, session_id, status, structured_reason, comment, reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(decision.review_id, decision.record_id, sessionId, decision.status, decision.structured_reason, decision.comment, decision.reviewed_at).run();
    return { status: 201, payload: decision };
  }
  throw Object.assign(new Error('Route not found.'), { code: 'not_found', status: 404 });
}

export async function handleApi(request: Request, segments: string[]) {
  const { sessionId, isNew } = sessionFor(request);
  try {
    const database = getDatabase();
    await ensureSchema(database);
    const result = request.method === 'GET'
      ? await routeGet(database, sessionId, segments)
      : request.method === 'POST'
        ? await routePost(database, sessionId, segments, await body(request))
        : { status: 405, payload: { error: { code: 'method_not_allowed', message: 'Method not allowed.' } } };
    return json(result.payload, result.status, sessionId, isNew);
  } catch (error) {
    const typed = error as Error & { code?: string; status?: number };
    return json({ error: { code: typed.code || 'internal_error', message: typed.code ? typed.message : 'The hosted UI service failed safely.' } }, typed.status || 422, sessionId, isNew);
  }
}
