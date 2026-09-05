import assert from 'node:assert/strict';
import test from 'node:test';
import fixture from '../fixtures/controlled_demo_minimal.json' with { type: 'json' };
import {
  applyHumanDecision,
  buildCampaignWorkflow,
  buildControlledRun,
  buildCreatorRecord,
  buildIcpGeneration,
  buildWorkspace,
  deduplicateFixture,
  refreshControlledDemoRecord,
} from '../hosting/core.mjs';

test('hosted campaign planning preserves the original brief and proposes provider-neutral queries', () => {
  const brief = 'Find active partners in the US and Canada covering AI website tools and portfolios for designers and freelancers.';
  const workflow = buildCampaignWorkflow(brief);
  assert.equal(workflow.original_brief, brief);
  assert.equal(workflow.campaign_parse.status, 'complete');
  assert.deepEqual(workflow.campaign_parse.definition.target_markets, ['United States', 'Canada']);
  assert.equal(workflow.draft_search_plan.queries.length, 14);
});

test('hosted campaign planning requires a target market instead of inventing one', () => {
  const workflow = buildCampaignWorkflow('Find creators covering web design and portfolios.');
  assert.equal(workflow.campaign_parse.status, 'incomplete');
  assert.equal(workflow.draft_search_plan, null);
  assert.deepEqual(workflow.campaign_parse.missing_required_fields, ['target_markets']);
});

test('controlled fixture dedup keeps same handle on different platforms', () => {
  const records = deduplicateFixture(fixture);
  assert.equal(records.length, 10);
  assert.deepEqual(records.filter((row) => row.display_name === 'Dann Petty').map((row) => row.platform).sort(), ['instagram', 'x']);
});

test('controlled run stores only approved or edited executable queries', () => {
  const workflow = buildCampaignWorkflow('Find partners in the US and Canada covering AI website tools and portfolios for designers.');
  const actions = workflow.draft_search_plan.queries.map((query, index) => ({
    query_id: query.query_id,
    decision: index === 0 ? 'edited' : index === 1 ? 'rejected' : 'approved',
    edited_query_text: index === 0 ? 'AI portfolio builders US' : null,
    human_comment: null,
  }));
  const result = buildControlledRun(workflow, actions, fixture, new Set());
  assert.equal(result.review.reviewed_queries[0].original_query.query_text.includes('AI website'), true);
  assert.equal(result.approved_search_plan.queries[0].query_text, 'AI portfolio builders US');
  assert.equal(result.approved_search_plan.queries.some((query) => query.source_query_id === workflow.draft_search_plan.queries[1].query_id), false);
});

test('second controlled run reports saturation from existing records', () => {
  const workflow = buildCampaignWorkflow('Find partners in the US and Canada covering AI website tools and portfolios for designers.');
  const actions = workflow.draft_search_plan.queries.map((query) => ({ query_id: query.query_id, decision: 'approved' }));
  const first = buildControlledRun(workflow, actions, fixture, new Set());
  const existing = new Set(first.creator_records.map((record) => record.record_id));
  const second = buildControlledRun(workflow, actions, fixture, existing);
  assert.equal(first.run_summary.retrieved, 12);
  assert.equal(first.run_summary.new_creators, 10);
  assert.equal(second.run_summary.new_creators, 0);
  assert.equal(second.run_summary.duplicates, 12);
});

test('ICP demo returns exactly three hypotheses', () => {
  const result = buildIcpGeneration({ product_name: 'SiteSprint AI', product_description: 'AI portfolio builder', problem: 'Portfolios take too long', strongest_value: 'Publish faster', current_users: 'independent designers' });
  assert.equal(result.hypotheses.length, 3);
  assert.deepEqual(result.hypotheses.map((item) => item.recommended_order), [1, 2, 3]);
});

test('hosted workspace exposes dashboard provenance and latest human review', () => {
  const workflow = buildCampaignWorkflow('Find partners in the US and Canada covering AI website tools and portfolios for designers.');
  const actions = workflow.draft_search_plan.queries.map((query) => ({ query_id: query.query_id, decision: 'approved' }));
  const run = buildControlledRun(workflow, actions, fixture, new Set());
  const decision = {
    status: 'approve',
    structured_reason: 'strong_campaign_fit',
    comment: 'Strong evidence.',
    reviewed_at: '2026-09-03T08:00:00.000Z',
  };
  const reviewed = applyHumanDecision(run.creator_records[0], decision);
  const workspace = buildWorkspace([reviewed, ...run.creator_records.slice(1)], [{ ...run, completed_at: run.run_summary.completed_at }]);
  const summary = workspace.creators[0];
  assert.equal(summary.run_id, run.run_summary.run_id);
  assert.ok(summary.query_id);
  assert.ok(summary.source_query_id);
  assert.equal(summary.has_signals, true);
  assert.equal(summary.has_audience_inference, true);
  assert.equal(summary.has_priority_decision, true);
  assert.equal(summary.review_status, 'approve');
  assert.equal(summary.review_reason, 'strong_campaign_fit');
  assert.equal(summary.review_comment, 'Strong evidence.');
});

test('controlled demo identities and profile URLs describe the same public accounts', () => {
  const expected = new Map([
    ['creator_001', ['Jesse Showalter', 'imjesseshow']],
    ['creator_003', ['Jesse Showalter', 'imjesseshow']],
    ['creator_004', ['Charli Marie', 'charliprangley']],
    ['creator_005', ['Charli Marie', 'charliprangley']],
    ['creator_007', ['Femke', 'femkedotdesign']],
    ['creator_008', ['Mizko', 'mizko']],
    ['creator_009', ['Ran Segall', 'ransegall']],
    ['creator_010', ['Abduzeedo', 'abduzeedo']],
    ['creator_011', ['Dann Petty', 'dannpetty']],
    ['creator_012', ['Dann Petty', 'dannpetty']],
  ]);
  const records = deduplicateFixture(fixture);
  assert.equal(records.every((row) => row.source_connector === 'curated_public_fixture_v1'), true);
  assert.equal(records.every((row) => /^https:\/\/(?:www\.)?(?:instagram\.com|x\.com)\//i.test(row.profile_url)), true);
  assert.equal(records.every((row) => !row.profile_url.includes('demo_')), true);
  for (const row of records) {
    const handle = new URL(row.profile_url).pathname.split('/').filter(Boolean).at(-1).toLowerCase();
    assert.deepEqual([row.display_name, handle], expected.get(row.record_id));
  }
});

test('stored legacy demo records refresh to the matching curated public identity', () => {
  const legacyRaw = {
    ...fixture[0],
    profile_url: 'https://www.instagram.com/demo_astra_canvas_9f2a/',
    display_name: 'Astra Canvas Demo',
    source_connector: 'controlled_fixture_v1',
  };
  const provenance = {
    runId: 'run_original', queryId: 'query_original', completedAt: '2026-09-01T09:30:00Z',
    campaignId: 'campaign_original', approvedPlanId: 'plan_original', sourceQueryId: 'source_original',
    queryText: 'portfolio creators', searchAngle: 'core_topic',
  };
  const refreshed = refreshControlledDemoRecord(buildCreatorRecord(legacyRaw, provenance), fixture);
  assert.equal(refreshed.summary.display_name, 'Jesse Showalter');
  assert.equal(refreshed.summary.handle, '@imjesseshow');
  assert.equal(refreshed.summary.profile_url, 'https://www.instagram.com/imjesseshow/');
  assert.equal(refreshed.detail.observed_facts.run_id, 'run_original');
  assert.equal(refreshed.detail.observed_facts.query_text, 'portfolio creators');
});
