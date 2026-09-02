import assert from 'node:assert/strict';
import test from 'node:test';
import fixture from '../fixtures/controlled_demo_minimal.json' with { type: 'json' };
import { buildCampaignWorkflow, buildControlledRun, buildIcpGeneration, deduplicateFixture } from '../hosting/core.mjs';

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
  assert.equal(records.filter((row) => row.display_name.includes('Dual Maker')).length, 2);
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
