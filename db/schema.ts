import { index, integer, primaryKey, sqliteTable, text } from 'drizzle-orm/sqlite-core';

export const workflows = sqliteTable('workflows', {
  workflowId: text('workflow_id').notNull(),
  sessionId: text('session_id').notNull(),
  payloadJson: text('payload_json').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => [
  primaryKey({ columns: [table.workflowId, table.sessionId] }),
  index('workflows_session_created_idx').on(table.sessionId, table.createdAt),
]);

export const discoveryRuns = sqliteTable('discovery_runs', {
  runId: text('run_id').notNull(),
  sessionId: text('session_id').notNull(),
  payloadJson: text('payload_json').notNull(),
  completedAt: text('completed_at').notNull(),
}, (table) => [
  primaryKey({ columns: [table.runId, table.sessionId] }),
  index('discovery_runs_session_completed_idx').on(table.sessionId, table.completedAt),
]);

export const creators = sqliteTable('creators', {
  recordId: text('record_id').notNull(),
  sessionId: text('session_id').notNull(),
  payloadJson: text('payload_json').notNull(),
  priority: text('priority').notNull(),
  channel: text('channel').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => [
  primaryKey({ columns: [table.recordId, table.sessionId] }),
  index('creators_session_priority_idx').on(table.sessionId, table.priority),
  index('creators_session_channel_idx').on(table.sessionId, table.channel),
]);

export const creatorReviews = sqliteTable('creator_reviews', {
  reviewId: text('review_id').primaryKey(),
  recordId: text('record_id').notNull(),
  sessionId: text('session_id').notNull(),
  status: text('status').notNull(),
  structuredReason: text('structured_reason'),
  comment: text('comment'),
  reviewedAt: text('reviewed_at').notNull(),
}, (table) => [index('creator_reviews_session_record_idx').on(table.sessionId, table.recordId, table.reviewedAt)]);

export const icpHypotheses = sqliteTable('icp_hypotheses', {
  hypothesisId: text('hypothesis_id').notNull(),
  version: integer('version').notNull(),
  sessionId: text('session_id').notNull(),
  contextId: text('context_id').notNull(),
  payloadJson: text('payload_json').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => [
  primaryKey({ columns: [table.hypothesisId, table.version, table.sessionId] }),
  index('icp_hypotheses_session_context_idx').on(table.sessionId, table.contextId),
]);

export const icpSelections = sqliteTable('icp_selections', {
  selectionId: text('selection_id').primaryKey(),
  sessionId: text('session_id').notNull(),
  hypothesisId: text('hypothesis_id').notNull(),
  hypothesisVersion: integer('hypothesis_version').notNull(),
  payloadJson: text('payload_json').notNull(),
  selectedAt: text('selected_at').notNull(),
}, (table) => [index('icp_selections_session_selected_idx').on(table.sessionId, table.selectedAt)]);
