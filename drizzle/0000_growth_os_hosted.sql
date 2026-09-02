CREATE TABLE `workflows` (
	`workflow_id` text NOT NULL,
	`session_id` text NOT NULL,
	`payload_json` text NOT NULL,
	`created_at` text NOT NULL,
	PRIMARY KEY(`workflow_id`, `session_id`)
);
--> statement-breakpoint
CREATE INDEX `workflows_session_created_idx` ON `workflows` (`session_id`,`created_at`);
--> statement-breakpoint
CREATE TABLE `discovery_runs` (
	`run_id` text NOT NULL,
	`session_id` text NOT NULL,
	`payload_json` text NOT NULL,
	`completed_at` text NOT NULL,
	PRIMARY KEY(`run_id`, `session_id`)
);
--> statement-breakpoint
CREATE INDEX `discovery_runs_session_completed_idx` ON `discovery_runs` (`session_id`,`completed_at`);
--> statement-breakpoint
CREATE TABLE `creators` (
	`record_id` text NOT NULL,
	`session_id` text NOT NULL,
	`payload_json` text NOT NULL,
	`priority` text NOT NULL,
	`channel` text NOT NULL,
	`created_at` text NOT NULL,
	PRIMARY KEY(`record_id`, `session_id`)
);
--> statement-breakpoint
CREATE INDEX `creators_session_priority_idx` ON `creators` (`session_id`,`priority`);
--> statement-breakpoint
CREATE INDEX `creators_session_channel_idx` ON `creators` (`session_id`,`channel`);
--> statement-breakpoint
CREATE TABLE `creator_reviews` (
	`review_id` text PRIMARY KEY NOT NULL,
	`record_id` text NOT NULL,
	`session_id` text NOT NULL,
	`status` text NOT NULL,
	`structured_reason` text,
	`comment` text,
	`reviewed_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `creator_reviews_session_record_idx` ON `creator_reviews` (`session_id`,`record_id`,`reviewed_at`);
--> statement-breakpoint
CREATE TABLE `icp_hypotheses` (
	`hypothesis_id` text NOT NULL,
	`version` integer NOT NULL,
	`session_id` text NOT NULL,
	`context_id` text NOT NULL,
	`payload_json` text NOT NULL,
	`created_at` text NOT NULL,
	PRIMARY KEY(`hypothesis_id`, `version`, `session_id`)
);
--> statement-breakpoint
CREATE INDEX `icp_hypotheses_session_context_idx` ON `icp_hypotheses` (`session_id`,`context_id`);
--> statement-breakpoint
CREATE TABLE `icp_selections` (
	`selection_id` text PRIMARY KEY NOT NULL,
	`session_id` text NOT NULL,
	`hypothesis_id` text NOT NULL,
	`hypothesis_version` integer NOT NULL,
	`payload_json` text NOT NULL,
	`selected_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `icp_selections_session_selected_idx` ON `icp_selections` (`session_id`,`selected_at`);
