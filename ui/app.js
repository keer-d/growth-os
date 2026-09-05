"use strict";

const TRANSLATIONS = {
  en: {
    "brand.description": "From ICP hypothesis to evidence-backed partner discovery for Growth & GTM teams.",
    "nav.aria": "Primary navigation", "nav.overview": "Overview", "nav.icp": "ICP", "nav.discover": "Discovery", "nav.partners": "Review", "nav.insights": "Runs", "nav.sources": "Data Sources",
    "icp.eyebrow": "Market hypothesis workspace", "icp.title": "Who should we target?", "icp.lede": "Turn product and market context into three testable customer hypotheses. You—not the AI—choose what to validate.", "icp.humanOwned": "Human-selected", "icp.knownKicker": "Direct path", "icp.knownTitle": "I already know my ICP", "icp.knownText": "Move straight to the existing discovery workflow and define the partners who can reach that audience.", "icp.openDiscovery": "Open Discovery", "icp.helpKicker": "Guided hypothesis", "icp.helpTitle": "Help me discover my ICP", "icp.helpText": "Capture business context, compare exactly three hypotheses, then translate one into reviewable discovery criteria.", "icp.start": "Start ICP Discovery",
    "icp.contextKicker": "01 · Business context", "icp.contextTitle": "Give the system facts, not a persona guess.", "icp.contextText": "The offline demo uses your manual description. A website URL is optional and is never silently treated as analyzed.", "icp.offlineProvider": "Deterministic demo · offline", "icp.product": "Product", "icp.productName": "Product name", "icp.website": "Website URL · optional", "icp.description": "What does the product do?", "icp.problemValue": "Problem & value", "icp.problem": "What painful problem does it solve?", "icp.value": "What is the strongest value?", "icp.usersAlternatives": "Users & alternatives", "icp.users": "Who uses or might use it?", "icp.alternatives": "Current alternatives · comma separated", "icp.marketSignals": "Signals & market", "icp.signals": "Observable pain signals · comma separated", "icp.markets": "Target markets · optional, comma separated", "icp.stage": "Company stage", "icp.prelaunch": "Pre-launch", "icp.early": "Early", "icp.growing": "Growing", "icp.scaling": "Scaling", "icp.generate": "Generate 3 ICP Hypotheses", "icp.generating": "Generating three testable hypotheses…", "icp.compareKicker": "02 · Compare hypotheses", "icp.compareTitle": "Three starting points—not an AI verdict.", "icp.disclaimer": "Scores are AI-estimated comparison aids. Validate every assumption with real market evidence.", "icp.regenerate": "Generate a new set", "icp.hypothesis": "Hypothesis", "icp.customer": "Customer ICP", "icp.who": "Who", "icp.context": "Context", "icp.corePain": "Core pain", "icp.whyPain": "Why it matters", "icp.alternative": "Current alternative", "icp.valueProposition": "Value proposition", "icp.trigger": "Trigger event", "icp.intentSignals": "Intent signals", "icp.where": "Where to find them", "icp.whyWork": "Why it may work", "icp.unknowns": "Unknowns / risks", "icp.testPriority": "Test priority", "icp.estimated": "AI-estimated", "icp.select": "Select to Test", "icp.edit": "Edit", "icp.saveLater": "Save for Later", "icp.saved": "Hypothesis saved for later.", "icp.saveVersion": "Save as new version", "icp.cancelEdit": "Cancel edit", "icp.version": "v{version}", "icp.criteriaKicker": "03 · Human confirmation", "icp.criteriaTitle": "Customer ICP → Partner Discovery Criteria", "icp.criteriaText": "The customer ICP describes who may buy or use. These criteria describe partners who may help you reach them. Edit before any query planning.", "icp.notPermission": "Draft · not permission to retrieve", "icp.partnerProfile": "Partner / creator profile to discover", "icp.criteriaGoal": "Discovery goal", "icp.themes": "Content themes · comma separated", "icp.audience": "Audience to reach · comma separated", "icp.criteriaSignals": "Intent signals · comma separated", "icp.exclusions": "Exclusions · comma separated", "icp.channels": "Channels", "icp.confirmCriteria": "Confirm Criteria & Draft Queries", "icp.criteriaConfirmed": "Human-confirmed ICP criteria", "icp.origin": "Started from ICP: {name} · v{version}", "icp.currentKicker": "Current ICP", "icp.testing": "TESTING", "icp.runs": "Discovery runs using this ICP", "icp.noRuns": "No discovery run has used this hypothesis yet.", "icp.noCurrent": "No ICP is being tested yet.", "icp.noCurrentText": "Start with a business context or continue directly if you already know the audience.", "icp.viewWorkspace": "Open ICP workspace", "icp.assumption": "Hypothesis—not market truth", "icp.edited": "A new version was saved. The earlier version remains unchanged.",
    "icp.dimension.pain_severity": "Pain severity", "icp.dimension.problem_frequency": "Problem frequency", "icp.dimension.value_proposition_strength": "Value strength", "icp.dimension.reachability": "Reachability", "icp.dimension.intent_signal_availability": "Intent signals", "icp.dimension.potential_commercial_value": "Commercial value", "icp.dimension.product_fit": "Product fit",
    "prefs.language": "Language", "prefs.appearance": "Appearance", "prefs.themeAria": "Theme", "prefs.light": "Light", "prefs.dark": "Dark",
    "workspace.local": "Local workspace", "workspace.guardrail": "Human approval remains the execution gate. Draft ≠ permission to retrieve.",
    "channel.instagram": "Instagram", "channel.x": "X", "channel.youtube": "YouTube", "channel.web": "Web", "channel.controlled": "Controlled Demo",
    "discover.eyebrow": "Campaign workspace", "discover.title": "Turn a brief into an approved discovery run.", "discover.lede": "Describe the partners you want to find. The system structures the campaign, proposes queries per channel, and keeps a human in control before retrieval.", "discover.ready": "Controlled Demo ready",
    "workflow.aria": "Discovery workflow", "workflow.brief": "Campaign brief", "workflow.briefNote": "Describe the partners", "workflow.review": "Query review", "workflow.reviewNote": "Approve, edit, reject", "workflow.run": "Discovery run", "workflow.runNote": "Retrieve and process",
    "brief.kicker": "01 · Describe campaign", "brief.title": "Who should this campaign discover?", "brief.provider": "Deterministic planning · offline", "brief.label": "Campaign brief", "brief.tipStrong": "Keep it concrete.", "brief.tip": "Include markets, themes, and who the partners should reach.", "brief.generate": "Generate Search Plan",
    "plan.kicker": "02 · Human query review", "plan.title": "Draft Search Plan", "plan.explanation": "These queries are proposals only. Review is required before execution.", "plan.draft": "Draft · not executable", "plan.everyDecision": "Every query needs a decision.", "plan.approveRemaining": "Approve remaining",
    "execution.kicker": "03 · Choose execution mode", "execution.title": "Run only the approved plan.", "execution.explanation": "Controlled Demo is offline and repeatable. Live retrieval uses configured channels and can incur external provider costs.", "execution.modeAria": "Discovery mode", "execution.controlled": "Controlled Demo", "execution.controlledNote": "Offline fixtures · safe default", "execution.live": "Live Discovery", "execution.liveConfirm": "I understand this will call configured external providers and may incur usage costs.", "execution.locked": "Review all proposed queries to unlock execution.", "execution.runControlled": "Run Controlled Discovery",
    "pipeline.retrieval": "Retrieval", "pipeline.retrievalNote": "Approved queries only", "pipeline.dedup": "Dedup", "pipeline.dedupNote": "Same-channel identity", "pipeline.signals": "Signal Extraction", "pipeline.signalsNote": "Observed evidence", "pipeline.audience": "AI Audience Inference", "pipeline.audienceNote": "Audience hypothesis", "pipeline.priority": "Priority", "pipeline.priorityNote": "Explainable decision",
    "overview.eyebrow": "Growth operating system", "overview.titleAccent": "Hypothesis to evidence", "overview.title": "with a human at every decision gate.", "overview.lede": "Define who may matter, translate the hypothesis into partner discovery, and preserve every source, query, and decision.", "overview.start": "Start a Discovery", "overview.pulse": "Workspace Pulse", "overview.pulseTitle": "What the system knows now",
    "dashboard.eyebrow": "Growth operations", "dashboard.title": "Growth Command Center", "dashboard.lede": "See who is being tested, where evidence is moving, and what needs a human decision.", "dashboard.sample": "Sample data", "dashboard.workspace": "Workspace data", "dashboard.currentIcp": "Current ICP", "dashboard.latestRun": "Latest run", "dashboard.systemStatus": "System status", "dashboard.lastUpdated": "Last updated", "dashboard.noIcp": "No ICP selected", "dashboard.noRun": "No run yet", "dashboard.operational": "Operational", "dashboard.attentionStatus": "Attention needed", "dashboard.viewIcp": "View ICP", "dashboard.runDiscovery": "Run discovery", "dashboard.reviewNow": "Review now", "dashboard.filterDate": "Date range", "dashboard.filterIcp": "ICP", "dashboard.filterSource": "Channel", "dashboard.filterRun": "Run", "dashboard.last30": "Last 30 days", "dashboard.last7": "Last 7 days", "dashboard.allTime": "All available data", "dashboard.allIcps": "All ICPs", "dashboard.allSources": "All channels", "dashboard.allRuns": "All runs", "dashboard.reset": "Reset", "dashboard.discovered": "Discovered", "dashboard.discoveredNote": "unique candidate records", "dashboard.highPriority": "High priority", "dashboard.highPriorityNote": "P1 + P2 · not a qualification score", "dashboard.reviewQueue": "Review queue", "dashboard.reviewQueueNote": "unresolved human decisions", "dashboard.approved": "Approved", "dashboard.approvedNote": "latest human decision", "dashboard.approvalRate": "Approval rate", "dashboard.approvalRateNote": "approved / final decisions", "dashboard.newLatest": "New in latest run", "dashboard.newLatestNote": "new unique candidates", "dashboard.noComparison": "No comparison yet", "dashboard.vsPrevious": "{value} vs previous run", "dashboard.pipelineKicker": "Current V1 pipeline", "dashboard.funnelTitle": "Where is evidence moving—or stopping?", "dashboard.rawResults": "Raw results", "dashboard.uniqueRecords": "New unique", "dashboard.signalsExtracted": "Signals extracted", "dashboard.audienceInferred": "Audience inferred", "dashboard.priorityAssigned": "Priority assigned", "dashboard.humanReviewed": "Human reviewed", "dashboard.finalApproved": "Approved", "dashboard.ofPrevious": "{value} of previous stage", "dashboard.noStageData": "No upstream records", "dashboard.biggestDrop": "Biggest drop", "dashboard.duplicateDrop": "Removed safely as duplicates.", "dashboard.reviewDrop": "Candidates are waiting for human judgment.", "dashboard.pipelineDrop": "Processing evidence is incomplete for some candidates.", "dashboard.noDrop": "No material drop is visible in this filtered cohort.", "dashboard.attentionTitle": "Needs your attention", "dashboard.whyMatters": "Why it matters", "dashboard.noAttention": "No urgent attention items in this view.", "dashboard.failedQueries": "{count} query executions failed", "dashboard.failedWhy": "Failures prevent evidence from entering the candidate pool.", "dashboard.pendingReviews": "{count} candidates need a final decision", "dashboard.pendingWhy": "Unresolved evidence cannot become an approved operating list.", "dashboard.untestedIcp": "The selected ICP has no linked discovery run", "dashboard.untestedWhy": "A hypothesis remains untested until run evidence is linked to it.", "dashboard.zeroQueries": "{count} queries returned zero results", "dashboard.zeroWhy": "These search directions produced no valid profiles in the selected period.", "dashboard.openRuns": "Open runs", "dashboard.currentIcpKicker": "Current hypothesis", "dashboard.who": "Who", "dashboard.corePain": "Core pain", "dashboard.keySignals": "Key signals", "dashboard.testPriority": "Test priority", "dashboard.discoveryRuns": "Linked runs", "dashboard.updated": "Updated", "dashboard.noLinkedRuns": "No discovery run is linked to this ICP yet.", "dashboard.hypothesisNote": "Hypothesis—not market truth.", "dashboard.qualityKicker": "Discovery quality", "dashboard.sourceTitle": "Which directions produce useful candidates?", "dashboard.qualityNote": "Discovery evidence, not customer conversion.", "dashboard.sourcePerformance": "Channel performance", "dashboard.queryPerformance": "Query performance", "dashboard.channel": "Channel", "dashboard.query": "Query", "dashboard.angle": "Angle", "dashboard.raw": "Raw", "dashboard.new": "New", "dashboard.freshYield": "Fresh yield", "dashboard.highPriorityShort": "P1/P2", "dashboard.finalDecisions": "Final decisions", "dashboard.errors": "Errors", "dashboard.insufficientReviews": "Not enough reviewed evidence", "dashboard.noSourceEvidence": "No source evidence matches these filters.", "dashboard.humanKicker": "Human operations", "dashboard.humanTitle": "Review decisions", "dashboard.pending": "Pending", "dashboard.reviewedToday": "Reviewed today", "dashboard.rejected": "Rejected", "dashboard.needsReview": "Needs review", "dashboard.timeToReview": "Time to first review", "dashboard.notDuration": "elapsed time, not active review duration", "dashboard.topRejections": "Top rejection reasons", "dashboard.noRejections": "No rejection evidence yet.", "dashboard.healthKicker": "System health", "dashboard.healthTitle": "Can the evidence pipeline run?", "dashboard.sourcesConnected": "Live sources connected", "dashboard.apiErrors": "Query errors", "dashboard.failedRuns": "Failed runs", "dashboard.llmErrors": "LLM output errors", "dashboard.dbErrors": "Database write errors", "dashboard.notTracked": "Not tracked here", "dashboard.duplicateRate": "Duplicate rate", "dashboard.lastSuccess": "Last successful run", "dashboard.trendKicker": "Quality trend", "dashboard.trendTitle": "Approval rate by run", "dashboard.trendEmpty": "No run has enough final human decisions for an approval trend.", "dashboard.trendNeedMore": "At least two comparable runs are needed for a trend.", "dashboard.runsKicker": "Execution evidence", "dashboard.runsTitle": "Recent runs", "dashboard.started": "Started", "dashboard.duration": "Duration", "dashboard.status": "Status", "dashboard.openRun": "Open run", "dashboard.lessThanSecond": "< 1 sec", "dashboard.seconds": "{count}s", "dashboard.learningsKicker": "Evidence-backed", "dashboard.learningsTitle": "Recent learnings", "dashboard.noLearnings": "More run or review evidence is needed before a defensible learning can be stated.", "dashboard.evidence": "View evidence", "dashboard.learningYield": "{channel} has the strongest fresh-result yield in this view ({value}).", "dashboard.learningSaturation": "Fresh-result yield fell from {before} to {after} in the latest run.", "dashboard.learningZero": "{count} search directions returned no valid profiles.", "dashboard.learningReject": "The most common rejection reason is “{reason}”.", "dashboard.nextKicker": "One next move", "dashboard.nextTitle": "Next best action", "dashboard.nextReview": "Review {count} unresolved candidates", "dashboard.nextFailure": "Inspect {count} failed query executions", "dashboard.nextIcp": "Run discovery for the selected ICP", "dashboard.nextRun": "Start the first discovery run", "dashboard.nextInspect": "Inspect low-yield search directions", "dashboard.nextHealthy": "Continue gathering review evidence", "dashboard.emptyTitle": "Your Growth OS is ready.", "dashboard.emptyText": "Build the first evidence loop without pretending empty data is performance.", "dashboard.emptyStep1": "Define or select an ICP", "dashboard.emptyStep2": "Run your first discovery", "dashboard.emptyStep3": "Review candidates", "dashboard.emptyStep4": "Build the first evidence loop", "dashboard.startIcp": "Start ICP discovery", "dashboard.knownIcp": "I already know my ICP", "dashboard.metricUnavailable": "—", "dashboard.demoNotice": "Controlled Demo values are sample evidence and never mixed with live provider results.",
    "partners.eyebrow": "Evidence workspace", "partners.lede": "Creators, KOLs, affiliates, communities, media and experts — compared on observed facts, derived signals, AI audience inference, and the human decision.", "partners.search": "Search partner, handle, bio…", "partners.poolKicker": "Partner pool", "partners.poolTitle": "What the pool holds now", "partners.channelFilter": "Filter by channel", "partners.allChannels": "All channels", "partners.typeFilter": "Filter by partner type", "partners.allTypes": "All partner types", "partners.priorityFilter": "Filter by priority", "partners.allPriorities": "All priorities", "partners.reviewFilter": "Filter by review state", "partners.allReviewStates": "All review states", "partners.emptyTitle": "No partners match this view.", "partners.emptyText": "Adjust the filters or run a Controlled Demo from Discover.", "partners.openDiscover": "Open Discover", "partners.total": "Total Partners", "partners.totalNote": "deduplicated records", "partners.p1": "P1 · Contact First", "partners.p1Note": "highest action priority", "partners.p2": "P2 · Worth Contacting", "partners.p2Note": "second wave", "partners.needsReview": "Needs Review", "partners.needsReviewNote": "requires human judgment", "partners.reviewed": "Human Decisions", "partners.reviewedNote": "partners reviewed", "partners.byChannel": "By channel", "partners.noChannelRecords": "No stored records on this channel yet.", "partners.demoType": "demo",
    "partnerType.creator": "Creator", "partnerType.kol": "KOL", "partnerType.influencer": "Influencer", "partnerType.micro_influencer": "Micro-influencer", "partnerType.affiliate": "Affiliate", "partnerType.community": "Community", "partnerType.media": "Media", "partnerType.industry_expert": "Industry Expert",
    "status.needsReview": "Needs Review", "status.unreviewed": "Unreviewed", "status.approved": "Approved", "status.rejected": "Rejected",
    "insights.eyebrow": "Discovery freshness", "insights.lede": "How much of the latest discovery produced partners the system had not seen before — and which search directions are going quiet.", "insights.emptyTitle": "No discovery evidence yet.", "insights.emptyText": "Run the Controlled Demo to produce the first real discovery evidence.", "insights.start": "Start first discovery",
    "insights.latest": "LATEST DISCOVERY", "insights.latestTitle": "What the last discovery produced", "insights.freshExplain": "Fresh-result yield is how much of this discovery run produced partners the system had not seen before.", "insights.saturated": "Most results have already been discovered.", "insights.saturatedAdvice": "Consider new search angles — the current directions are returning partners already in the pool.", "insights.freshTitle": "This discovery is still finding new partners.", "insights.freshAdvice": "Compare query-level yield below before changing search direction.", "insights.viewHistory": "View discovery history", "insights.viewHistoryNote": "Compare earlier discoveries to see saturation building.", "insights.historyItem": "Discovery {index}", "insights.queryTitle": "Query Performance", "insights.queryDesc": "Real query-level evidence; no autonomous optimization is implied.", "insights.angle": "Search angle", "insights.retrieved": "Retrieved", "insights.duplicates": "Duplicates", "insights.new": "New", "insights.status": "Status", "insights.lowYield": "Low fresh-result yield", "insights.healthyYield": "Fresh results found", "insights.noResults": "No valid profiles", "insights.technical": "Technical details", "insights.technicalNote": "Internal run IDs and timestamps, kept for traceability.", "insights.completed": "Completed", "insights.queryExecutions": "query executions", "insights.success": "Completed", "insights.skipped": "Skipped", "insights.failed": "Failed", "insights.discoveries": "discoveries", "insights.discovery": "discovery",
    "sources.eyebrow": "Channel connectivity", "sources.lede": "Which channels this workspace can discover partners on. Credentials live server-side and are never sent to the browser.", "sources.connected": "Connected", "sources.notConfigured": "Not configured", "sources.configure": "Configure", "sources.configureTitle": "Configuring {channel}", "sources.configureBody": "Set this channel's credential as a server-side environment variable, then restart the local server. The browser never receives the value.", "sources.developer": "Developer configuration", "sources.developerNote": "Variable names only — no value is ever displayed or sent to the browser.", "sources.credential": "Credential variable", "sources.optional": "Optional variables", "sources.connectedCount": "{count} connected", "sources.alwaysOn": "Always available", "sources.controlledPurpose": "Offline fixtures for the repeatable demo", "sources.storedRecords": "{count} stored partners",
    "general.partner": "partner", "general.partners": "partners", "general.run": "run", "general.runs": "runs", "general.of": "of", "general.reviewed": "reviewed", "general.notObserved": "Not observed", "general.notAvailable": "Not available", "general.none": "None", "general.unknown": "Unknown", "general.cancel": "Cancel",
    "campaign.goal": "Goal", "campaign.markets": "Target markets", "campaign.themes": "Content themes", "campaign.audience": "Target audience", "campaign.exclusions": "Exclusions", "campaign.current": "Current Campaign", "campaign.currentNote": "The original human brief stays separate from the structured definition.", "campaign.ready": "Ready to plan", "campaign.notGenerated": "No structured definition has been generated yet.", "campaign.original": "Original human brief",
    "query.proposed": "AI-proposed query", "query.approve": "Approve", "query.approved": "Approved", "query.edit": "Edit & approve", "query.edited": "Edited & approved", "query.reject": "Reject", "query.rejected": "Rejected", "query.final": "Final executable query", "query.comment": "Optional human comment", "query.commentPlaceholder": "Why was this approved, edited, or rejected?", "query.reviewAria": "Review decision",
    "execution.remaining": "{count} decisions remaining.", "execution.readyCount": "{count} executable queries ready.", "execution.allRejected": "No executable queries remain. Approve or edit at least one proposal.", "execution.runLive": "Run Live Discovery", "execution.liveConfigured": "{count} of {total} channels connected", "execution.liveNone": "No live channels configured", "execution.generating": "Structuring campaign and drafting queries…", "execution.runningControlled": "Running the offline Controlled Demo…", "execution.runningLive": "Calling configured live channels…", "execution.pipelineRunning": "Processing real backend stages…", "execution.pipelineComplete": "Pipeline completed from the backend response.",
    "run.output": "Actual implementation output", "run.complete": "Discovery complete", "run.completeIssues": "Discovery completed with channel issues", "run.retrieved": "Retrieved", "run.retrievedNote": "channel records", "run.duplicates": "Duplicates", "run.duplicatesNote": "removed safely", "run.newPartners": "New Partners", "run.newNote": "stored this discovery", "run.yield": "New Partner Yield", "run.yieldNote": "fresh-result rate", "run.contactFirst": "Contact First", "run.worth": "Worth Contacting", "run.opportunistic": "Opportunistic", "run.needsReview": "Needs Review", "run.humanAttention": "human attention", "run.executable": "{count} approved queries executed.", "run.zeroTitle": "No valid partner profiles were returned.", "run.zeroText": "The run is recorded truthfully. Review channel status and query evidence before trying a new search angle.",
    "overview.latest": "Latest Discovery", "overview.noRun": "No stored discovery yet", "overview.noRunText": "The Controlled Demo is the reliable way to create the first evidence set.", "overview.openDiscover": "Open Discover", "overview.partnerRecords": "Partner records", "overview.partnerRecordsNote": "deduplicated evidence", "overview.p1": "P1 · Contact First", "overview.p1Note": "highest action priority", "overview.needsReview": "Needs Review", "overview.needsReviewNote": "requires human judgment", "overview.humanDecisions": "Human decisions", "overview.humanDecisionsNote": "stored reviews", "overview.latestYield": "Latest New Partner Yield", "overview.latestYieldNote": "fresh-result rate", "overview.decisionQueue": "Priority distribution", "overview.decisionQueueTitle": "Where the pool stands", "overview.channelReadiness": "Channel readiness", "overview.channelReadinessTitle": "Where discovery can run", "overview.channelNote": "Connected is not the same as retrieval success.", "overview.ready": "Ready", "overview.configured": "Connected", "overview.notConfigured": "Not configured", "overview.currentRun": "{mode} discovery", "overview.newRecords": "{count} new partner records",
    "priority.P1": "Contact First", "priority.P2": "Worth Contacting", "priority.P3": "Opportunistic", "priority.Needs Review": "Needs Review",
    "signal.activity.high": "Highly Active", "signal.activity.moderate": "Active", "signal.activity.low": "Low Activity", "signal.activity.unknown": "Activity Unknown", "signal.relevance.high": "Strong Relevance", "signal.relevance.moderate": "Moderate Relevance", "signal.relevance.low": "Low Relevance", "signal.relevance.unknown": "Relevance Unknown", "signal.market.target": "Target Market", "signal.market.outside": "Outside Target", "signal.market.conflicting": "Conflicting Market", "signal.market.unknown": "Market Unknown",
    "signalField.activity": "Activity", "signalField.relevance": "Relevance", "signalField.content_relevance": "Relevance", "signalField.audience": "Audience", "signalField.audience_size": "Audience", "signalField.market": "Market", "signalField.actionability": "Actionability", "signalField.record_quality": "Record quality",
    "signalValue.high": "High", "signalValue.moderate": "Moderate", "signalValue.low": "Low", "signalValue.target": "Target", "signalValue.outside": "Outside target", "signalValue.available": "Available", "signalValue.missing": "Not observed", "signalValue.unavailable": "Unavailable", "signalValue.usable": "Usable", "signalValue.insufficient": "Insufficient", "signalValue.incomplete": "Incomplete", "signalValue.conflicting": "Conflicting", "signalValue.spam": "Spam signals", "signalValue.small": "Small", "signalValue.medium": "Medium", "signalValue.large": "Large", "signalValue.unknown": "Unknown",
    "executionStatus.SUCCESS_WITH_RESULTS": "Success with results", "executionStatus.SUCCESS_ZERO_RESULTS": "Successful zero results", "executionStatus.FAILED": "Failed", "executionStatus.SKIPPED_NOT_CONFIGURED": "Skipped · not configured",
    "partner.market": "Market", "partner.followers": "Audience", "partner.channel": "Channel", "partner.type": "Partner type", "partner.activity": "Activity", "partner.relevance": "Relevance", "partner.audience": "Likely audience", "partner.viewEvidence": "View Evidence", "partner.review": "Review", "partner.openProfile": "Open Profile", "partner.demoRecord": "Sample record", "partner.demoProfileNote": "Controlled Demo records are synthetic, so no external social profile exists.", "partner.profileUnavailable": "Profile unavailable", "partner.audienceUnknown": "Audience unclear", "partner.contactAvailable": "Contact Available",
    "detail.title": "Partner Evidence", "detail.close": "Close partner evidence", "detail.loading": "Loading partner evidence…",
    "detail.whyPriority": "WHY THIS PRIORITY?", "detail.keySignals": "KEY SIGNALS", "detail.aiAudienceTitle": "AI AUDIENCE", "detail.likelyAudience": "Likely Audience", "detail.confidence": "Confidence", "detail.whyAi": "Why? View AI evidence", "detail.hideAi": "Hide AI evidence", "detail.viewEvidence": "View evidence", "detail.hideEvidence": "Hide evidence", "detail.observedContent": "OBSERVED CONTENT", "detail.showMore": "Show more", "detail.showLess": "Show less", "detail.noEvidence": "No stored evidence for this signal.",
    "detail.observed": "Observed Facts", "detail.observedDesc": "What the source actually returned.", "detail.sourceObserved": "Source-observed", "detail.platform": "Channel", "detail.followers": "Audience", "detail.retrieved": "Retrieved", "detail.mode": "Discovery mode", "detail.bioEmpty": "No bio was returned.", "detail.samplesEmpty": "No content samples were returned.", "detail.dateUnknown": "Date not observed", "detail.query": "Source query", "detail.angle": "Search angle", "detail.connector": "Source connector", "detail.runId": "Run ID", "detail.provenance": "Provenance", "detail.derived": "Derived Signals", "detail.derivedDesc": "Deterministic interpretation of observed evidence.", "detail.systemDerived": "System-derived", "detail.ai": "AI Inference", "detail.aiDesc": "Audience hypothesis, kept separate from facts.", "detail.aiDerived": "AI-derived", "detail.modelUnavailable": "Model unavailable", "detail.audienceUnclear": "Audience remains unclear", "detail.human": "Human Decision", "detail.humanDesc": "The decision that controls operational use.", "detail.humanOwned": "Human-owned", "detail.decision": "Decision", "detail.reason": "Structured reason", "detail.reasonNone": "No structured reason", "detail.comment": "Optional comment", "detail.commentPlaceholder": "Add the context the system cannot know…", "detail.lastDecision": "Latest saved decision", "detail.noDecision": "No human decision stored yet.", "detail.save": "Save Decision", "detail.saved": "Human decision saved.", "detail.reasonStrong": "Strong evidence fit", "detail.reasonFollowup": "Needs evidence follow-up", "detail.reasonOut": "Outside campaign fit", "detail.contentSamples": "Content evidence", "detail.noSignals": "No derived signals are stored for this record.", "detail.fullEvidence": "Full evidence & provenance", "detail.fullEvidenceNote": "Every stored fact behind this partner, kept for traceability.",
    "angle.core_topic": "Core topic", "angle.creator_workflow": "Creator workflow", "angle.professional_identity": "Professional identity", "angle.use_case": "Use case", "angle.audience_problem": "Audience problem", "angle.adjacent_tool": "Adjacent tool",
    "review.approve": "Approved", "review.reject": "Rejected", "review.needs_review": "Needs Review", "review.unreviewed": "Unreviewed",
    "error.default": "The local UI service could not complete the request.", "error.brief_required": "Describe the partner campaign before generating a search plan.", "error.draft_plan_missing": "The brief is incomplete. Clarify the missing campaign requirements before query planning.", "error.query_review_invalid": "Review every query and add final text for edited queries.", "error.workflow_not_found": "This draft is no longer in the local server session. Generate it again.", "error.live_confirmation_required": "Confirm live channel usage before execution.", "error.creator_not_found": "Partner record not found.", "error.invalid_review": "Choose a valid human decision.", "error.insufficient_business_context": "Add enough product, problem, and value context to generate testable ICP hypotheses.", "error.website_analysis_unavailable": "The offline demo cannot analyze a website. Add a manual product description.", "error.malformed_icp_output": "The ICP provider returned malformed structured data.", "error.no_useful_icp_hypotheses": "The provider did not return three useful, testable hypotheses.", "error.incomplete_discovery_criteria": "Complete the required discovery criteria before confirming.", "error.icp_provider_not_configured": "Live ICP generation is not configured.", "error.icp_provider_failure": "The live ICP provider failed safely.",
  },
  zh: {
    "brand.description": "从 ICP 假设到证据驱动的合作伙伴发现，服务 Growth 与 GTM 团队。",
    "nav.aria": "主导航", "nav.overview": "概览", "nav.icp": "ICP", "nav.discover": "发现", "nav.partners": "审核", "nav.insights": "运行", "nav.sources": "数据源",
    "icp.eyebrow": "市场假设工作区", "icp.title": "我们应该寻找谁？", "icp.lede": "将产品与市场背景转化为三个可验证的客户假设。由你，而不是 AI，决定验证哪一个。", "icp.humanOwned": "人工选择", "icp.knownKicker": "直接路径", "icp.knownTitle": "我已经知道 ICP", "icp.knownText": "直接进入现有发现流程，定义能够触达该受众的合作伙伴。", "icp.openDiscovery": "打开发现", "icp.helpKicker": "引导式假设", "icp.helpTitle": "帮助我发现 ICP", "icp.helpText": "填写业务背景，对比恰好三个假设，再将其中一个转化为可审核的发现条件。", "icp.start": "开始 ICP 发现",
    "icp.contextKicker": "01 · 业务背景", "icp.contextTitle": "提供事实，而不是猜一个画像。", "icp.contextText": "离线演示使用你的人工描述。网站 URL 是可选项，系统不会默认为已分析。", "icp.offlineProvider": "确定性演示 · 离线", "icp.product": "产品", "icp.productName": "产品名称", "icp.website": "网站 URL · 可选", "icp.description": "产品做什么？", "icp.problemValue": "问题与价值", "icp.problem": "解决什么痛点？", "icp.value": "最强价值是什么？", "icp.usersAlternatives": "用户与替代方案", "icp.users": "谁正在或可能使用？", "icp.alternatives": "当前替代方案 · 逗号分隔", "icp.marketSignals": "信号与市场", "icp.signals": "可观察痛点信号 · 逗号分隔", "icp.markets": "目标市场 · 可选，逗号分隔", "icp.stage": "公司阶段", "icp.prelaunch": "发布前", "icp.early": "早期", "icp.growing": "增长期", "icp.scaling": "规模化", "icp.generate": "生成 3 个 ICP 假设", "icp.generating": "正在生成三个可验证假设…", "icp.compareKicker": "02 · 对比假设", "icp.compareTitle": "三个起点，而不是 AI 结论。", "icp.disclaimer": "分数仅为 AI 估计的比较辅助。所有假设都必须用真实市场证据验证。", "icp.regenerate": "生成一组新假设", "icp.hypothesis": "假设", "icp.customer": "客户 ICP", "icp.who": "是谁", "icp.context": "情境", "icp.corePain": "核心痛点", "icp.whyPain": "为什么重要", "icp.alternative": "当前替代方案", "icp.valueProposition": "价值主张", "icp.trigger": "触发事件", "icp.intentSignals": "意向信号", "icp.where": "在哪里找到", "icp.whyWork": "为什么可能有效", "icp.unknowns": "未知 / 风险", "icp.testPriority": "测试优先级", "icp.estimated": "AI 估计", "icp.select": "选择测试", "icp.edit": "编辑", "icp.saveLater": "稍后再看", "icp.saved": "假设已保存，供稍后查看。", "icp.saveVersion": "保存为新版本", "icp.cancelEdit": "取消编辑", "icp.version": "v{version}", "icp.criteriaKicker": "03 · 人工确认", "icp.criteriaTitle": "客户 ICP → 合作伙伴发现条件", "icp.criteriaText": "客户 ICP 描述谁可能购买或使用；这些条件描述谁可能帮助你触达他们。生成查询前请先编辑确认。", "icp.notPermission": "草稿 · 不代表检索许可", "icp.partnerProfile": "要发现的合作伙伴 / 创作者画像", "icp.criteriaGoal": "发现目标", "icp.themes": "内容主题 · 逗号分隔", "icp.audience": "要触达的受众 · 逗号分隔", "icp.criteriaSignals": "意向信号 · 逗号分隔", "icp.exclusions": "排除项 · 逗号分隔", "icp.channels": "渠道", "icp.confirmCriteria": "确认条件并起草查询", "icp.criteriaConfirmed": "人工已确认 ICP 条件", "icp.origin": "来源 ICP：{name} · v{version}", "icp.currentKicker": "当前 ICP", "icp.testing": "测试中", "icp.runs": "使用该 ICP 的发现运行", "icp.noRuns": "尚无发现运行使用该假设。", "icp.noCurrent": "尚未测试任何 ICP。", "icp.noCurrentText": "从业务背景开始；如果你已了解受众，也可以直接进入发现。", "icp.viewWorkspace": "打开 ICP 工作区", "icp.assumption": "假设，而非市场真相", "icp.edited": "新版本已保存，旧版本保持不变。",
    "icp.dimension.pain_severity": "痛点严重度", "icp.dimension.problem_frequency": "问题频率", "icp.dimension.value_proposition_strength": "价值强度", "icp.dimension.reachability": "可触达性", "icp.dimension.intent_signal_availability": "意向信号", "icp.dimension.potential_commercial_value": "商业价值", "icp.dimension.product_fit": "产品匹配",
    "prefs.language": "语言", "prefs.appearance": "外观", "prefs.themeAria": "主题", "prefs.light": "浅色", "prefs.dark": "深色",
    "workspace.local": "本地工作区", "workspace.guardrail": "人工批准始终是执行门槛。草稿 ≠ 检索许可。",
    "channel.instagram": "Instagram", "channel.x": "X", "channel.youtube": "YouTube", "channel.web": "网页", "channel.controlled": "Controlled Demo",
    "discover.eyebrow": "Campaign 工作区", "discover.title": "把自然语言需求变成经人工批准的发现任务。", "discover.lede": "描述你想找的合作对象。系统会结构化 Campaign、按渠道提出查询，并在检索前保留人工控制。", "discover.ready": "Controlled Demo 已就绪",
    "workflow.aria": "发现工作流", "workflow.brief": "Campaign 简报", "workflow.briefNote": "描述目标合作对象", "workflow.review": "查询审核", "workflow.reviewNote": "批准、编辑、拒绝", "workflow.run": "发现执行", "workflow.runNote": "检索与处理",
    "brief.kicker": "01 · 描述 Campaign", "brief.title": "这次 Campaign 要发现什么样的合作对象？", "brief.provider": "确定性规划 · 离线", "brief.label": "Campaign 简报", "brief.tipStrong": "尽量具体。", "brief.tip": "请包含市场、内容主题，以及合作对象应触达的人群。", "brief.generate": "生成 Search Plan",
    "plan.kicker": "02 · 人工查询审核", "plan.title": "Search Plan 草稿", "plan.explanation": "这些查询只是建议。执行前必须完成人工审核。", "plan.draft": "草稿 · 不可执行", "plan.everyDecision": "每条查询都需要人工决定。", "plan.approveRemaining": "批准其余查询",
    "execution.kicker": "03 · 选择执行模式", "execution.title": "只执行经批准的 Search Plan。", "execution.explanation": "Controlled Demo 离线且可重复。Live Discovery 会调用已连接的渠道，并可能产生费用。", "execution.modeAria": "发现模式", "execution.controlled": "Controlled Demo", "execution.controlledNote": "离线夹具 · 安全默认", "execution.live": "Live Discovery", "execution.liveConfirm": "我了解这会调用已配置的外部服务，并可能产生用量费用。", "execution.locked": "审核所有建议查询后才能执行。", "execution.runControlled": "运行 Controlled Discovery",
    "pipeline.retrieval": "检索", "pipeline.retrievalNote": "仅批准的查询", "pipeline.dedup": "去重", "pipeline.dedupNote": "同渠道身份", "pipeline.signals": "信号提取", "pipeline.signalsNote": "观察证据", "pipeline.audience": "AI 受众推断", "pipeline.audienceNote": "受众假设", "pipeline.priority": "优先级", "pipeline.priorityNote": "可解释判断",
    "overview.eyebrow": "Growth 运营系统", "overview.titleAccent": "从假设到证据", "overview.title": "每个决策门都由人工掌控。", "overview.lede": "定义谁可能重要，将假设转为合作伙伴发现，并保留每个来源、查询与决策。", "overview.start": "开始发现", "overview.pulse": "工作区脉搏", "overview.pulseTitle": "系统目前知道什么",
    "dashboard.eyebrow": "增长运营", "dashboard.title": "增长指挥中心", "dashboard.lede": "快速看清正在验证谁、证据流向哪里，以及什么需要人工判断。", "dashboard.sample": "样本数据", "dashboard.workspace": "工作区数据", "dashboard.currentIcp": "当前 ICP", "dashboard.latestRun": "最近运行", "dashboard.systemStatus": "系统状态", "dashboard.lastUpdated": "最后更新", "dashboard.noIcp": "未选择 ICP", "dashboard.noRun": "尚无运行", "dashboard.operational": "运行正常", "dashboard.attentionStatus": "需要关注", "dashboard.viewIcp": "查看 ICP", "dashboard.runDiscovery": "运行发现", "dashboard.reviewNow": "立即审核", "dashboard.filterDate": "日期范围", "dashboard.filterIcp": "ICP", "dashboard.filterSource": "渠道", "dashboard.filterRun": "运行", "dashboard.last30": "最近 30 天", "dashboard.last7": "最近 7 天", "dashboard.allTime": "全部可用数据", "dashboard.allIcps": "全部 ICP", "dashboard.allSources": "全部渠道", "dashboard.allRuns": "全部运行", "dashboard.reset": "重置", "dashboard.discovered": "已发现", "dashboard.discoveredNote": "唯一候选记录", "dashboard.highPriority": "高优先级", "dashboard.highPriorityNote": "P1 + P2，不是资格评分", "dashboard.reviewQueue": "审核队列", "dashboard.reviewQueueNote": "尚未形成最终人工决定", "dashboard.approved": "已批准", "dashboard.approvedNote": "最近一次人工决定", "dashboard.approvalRate": "批准率", "dashboard.approvalRateNote": "已批准 / 最终决定", "dashboard.newLatest": "最近运行新增", "dashboard.newLatestNote": "新增唯一候选", "dashboard.noComparison": "暂无可比较数据", "dashboard.vsPrevious": "较上次运行 {value}", "dashboard.pipelineKicker": "当前 V1 管线", "dashboard.funnelTitle": "证据在何处流动，或在哪里停住？", "dashboard.rawResults": "原始结果", "dashboard.uniqueRecords": "新增唯一记录", "dashboard.signalsExtracted": "已提取信号", "dashboard.audienceInferred": "已推断受众", "dashboard.priorityAssigned": "已分配优先级", "dashboard.humanReviewed": "已人工审核", "dashboard.finalApproved": "已批准", "dashboard.ofPrevious": "上一阶段的 {value}", "dashboard.noStageData": "没有上游记录", "dashboard.biggestDrop": "最大流失", "dashboard.duplicateDrop": "重复记录已安全移除。", "dashboard.reviewDrop": "候选人正在等待人工判断。", "dashboard.pipelineDrop": "部分候选人的证据处理尚未完成。", "dashboard.noDrop": "当前筛选范围没有明显流失。", "dashboard.attentionTitle": "需要你的关注", "dashboard.whyMatters": "为什么重要", "dashboard.noAttention": "当前视图没有紧急事项。", "dashboard.failedQueries": "{count} 条查询执行失败", "dashboard.failedWhy": "失败会阻止证据进入候选池。", "dashboard.pendingReviews": "{count} 个候选需要最终决定", "dashboard.pendingWhy": "未决证据无法进入已批准的运营名单。", "dashboard.untestedIcp": "已选择 ICP 尚无关联发现运行", "dashboard.untestedWhy": "只有关联运行证据后，假设才算进入验证。", "dashboard.zeroQueries": "{count} 条查询返回零结果", "dashboard.zeroWhy": "这些搜索方向在所选时段没有产生有效资料。", "dashboard.openRuns": "打开运行", "dashboard.currentIcpKicker": "当前假设", "dashboard.who": "是谁", "dashboard.corePain": "核心痛点", "dashboard.keySignals": "关键信号", "dashboard.testPriority": "测试优先级", "dashboard.discoveryRuns": "关联运行", "dashboard.updated": "更新时间", "dashboard.noLinkedRuns": "尚无发现运行关联到该 ICP。", "dashboard.hypothesisNote": "这是假设，不是市场真相。", "dashboard.qualityKicker": "发现质量", "dashboard.sourceTitle": "哪些方向正在产出有用候选？", "dashboard.qualityNote": "这里展示发现证据，不是客户转化。", "dashboard.sourcePerformance": "渠道表现", "dashboard.queryPerformance": "查询表现", "dashboard.channel": "渠道", "dashboard.query": "查询", "dashboard.angle": "角度", "dashboard.raw": "原始", "dashboard.new": "新增", "dashboard.freshYield": "新增率", "dashboard.highPriorityShort": "P1/P2", "dashboard.finalDecisions": "最终决定", "dashboard.errors": "错误", "dashboard.insufficientReviews": "人工审核证据不足", "dashboard.noSourceEvidence": "没有符合当前筛选条件的来源证据。", "dashboard.humanKicker": "人工运营", "dashboard.humanTitle": "审核决定", "dashboard.pending": "待处理", "dashboard.reviewedToday": "今日审核", "dashboard.rejected": "已拒绝", "dashboard.needsReview": "待复核", "dashboard.timeToReview": "首次审核等待时间", "dashboard.notDuration": "这是经过时间，不是实际审核时长", "dashboard.topRejections": "主要拒绝原因", "dashboard.noRejections": "尚无拒绝证据。", "dashboard.healthKicker": "系统健康", "dashboard.healthTitle": "证据管线能否正常运行？", "dashboard.sourcesConnected": "已连接 Live 来源", "dashboard.apiErrors": "查询错误", "dashboard.failedRuns": "失败运行", "dashboard.llmErrors": "LLM 输出错误", "dashboard.dbErrors": "数据库写入错误", "dashboard.notTracked": "当前未跟踪", "dashboard.duplicateRate": "重复率", "dashboard.lastSuccess": "最近成功运行", "dashboard.trendKicker": "质量趋势", "dashboard.trendTitle": "按运行的人工批准率", "dashboard.trendEmpty": "没有运行具备足够的最终人工决定，无法形成批准率趋势。", "dashboard.trendNeedMore": "至少需要两次可比较运行才能形成趋势。", "dashboard.runsKicker": "执行证据", "dashboard.runsTitle": "最近运行", "dashboard.started": "开始", "dashboard.duration": "耗时", "dashboard.status": "状态", "dashboard.openRun": "打开运行", "dashboard.lessThanSecond": "少于 1 秒", "dashboard.seconds": "{count} 秒", "dashboard.learningsKicker": "证据支持", "dashboard.learningsTitle": "最近洞察", "dashboard.noLearnings": "需要更多运行或审核证据，才能形成可信结论。", "dashboard.evidence": "查看证据", "dashboard.learningYield": "当前视图中，{channel} 的新增结果率最高（{value}）。", "dashboard.learningSaturation": "最近一次运行的新增率从 {before} 降至 {after}。", "dashboard.learningZero": "{count} 个搜索方向没有返回有效资料。", "dashboard.learningReject": "最常见的拒绝原因是“{reason}”。", "dashboard.nextKicker": "一个下一步", "dashboard.nextTitle": "下一最佳行动", "dashboard.nextReview": "审核 {count} 个未决候选", "dashboard.nextFailure": "检查 {count} 条失败查询", "dashboard.nextIcp": "为当前 ICP 运行发现", "dashboard.nextRun": "开始第一次发现运行", "dashboard.nextInspect": "检查低新增率搜索方向", "dashboard.nextHealthy": "继续积累人工审核证据", "dashboard.emptyTitle": "你的 Growth OS 已准备好。", "dashboard.emptyText": "从第一条证据闭环开始，不把空数据包装成绩效。", "dashboard.emptyStep1": "定义或选择 ICP", "dashboard.emptyStep2": "运行第一次发现", "dashboard.emptyStep3": "审核候选", "dashboard.emptyStep4": "建立第一条证据闭环", "dashboard.startIcp": "开始 ICP 发现", "dashboard.knownIcp": "我已经知道 ICP", "dashboard.metricUnavailable": "—", "dashboard.demoNotice": "Controlled Demo 数值均为样本证据，不会与 Live Provider 结果混合。",
    "partners.eyebrow": "证据工作区", "partners.lede": "创作者、KOL、联盟推广、社区、媒体与行业专家——基于已观察事实、衍生信号、AI 受众推断和人工判断进行比较。", "partners.search": "搜索合作对象、账号、简介…", "partners.poolKicker": "合作对象池", "partners.poolTitle": "当前池中有什么", "partners.channelFilter": "按渠道筛选", "partners.allChannels": "所有渠道", "partners.typeFilter": "按合作类型筛选", "partners.allTypes": "所有合作类型", "partners.priorityFilter": "按优先级筛选", "partners.allPriorities": "所有优先级", "partners.reviewFilter": "按审核状态筛选", "partners.allReviewStates": "所有审核状态", "partners.emptyTitle": "这个视图中没有匹配的合作对象。", "partners.emptyText": "调整筛选条件，或从「发现」运行 Controlled Demo。", "partners.openDiscover": "打开「发现」", "partners.total": "合作对象总数", "partners.totalNote": "已去重记录", "partners.p1": "P1 · 优先联系", "partners.p1Note": "最高行动优先级", "partners.p2": "P2 · 值得联系", "partners.p2Note": "第二批", "partners.needsReview": "待审核", "partners.needsReviewNote": "需要人工判断", "partners.reviewed": "人工判断", "partners.reviewedNote": "已审核合作对象", "partners.byChannel": "按渠道分布", "partners.noChannelRecords": "该渠道尚无已存储记录。", "partners.demoType": "演示",
    "partnerType.creator": "创作者", "partnerType.kol": "KOL", "partnerType.influencer": "影响力者", "partnerType.micro_influencer": "微影响力者", "partnerType.affiliate": "联盟推广", "partnerType.community": "社区伙伴", "partnerType.media": "媒体 / 发布方", "partnerType.industry_expert": "行业专家",
    "status.needsReview": "待审核", "status.unreviewed": "未审核", "status.approved": "已批准", "status.rejected": "已拒绝",
    "insights.eyebrow": "发现新鲜度", "insights.lede": "最近一次发现有多少产出了系统此前没见过的合作对象——以及哪些搜索方向正在变安静。", "insights.emptyTitle": "还没有发现证据。", "insights.emptyText": "运行 Controlled Demo，产生第一批真实发现证据。", "insights.start": "开始首次发现",
    "insights.latest": "最近一次发现", "insights.latestTitle": "上一次发现产出了什么", "insights.freshExplain": "新鲜结果率表示：这次发现中，有多少产出了系统此前没有见过的合作对象。", "insights.saturated": "大部分结果都已经被发现过了。", "insights.saturatedAdvice": "建议尝试新的搜索角度——当前方向返回的都是池中已有的合作对象。", "insights.freshTitle": "这次发现仍在找到新的合作对象。", "insights.freshAdvice": "改变搜索方向前，先比较下方的查询级新增率。", "insights.viewHistory": "查看发现历史", "insights.viewHistoryNote": "对比更早的发现，观察饱和是如何形成的。", "insights.historyItem": "第 {index} 次发现", "insights.queryTitle": "查询表现", "insights.queryDesc": "真实查询级证据；不暗示系统已经自主优化。", "insights.angle": "搜索角度", "insights.retrieved": "已检索", "insights.duplicates": "重复", "insights.new": "新增", "insights.status": "状态", "insights.lowYield": "新鲜结果率低", "insights.healthyYield": "发现新鲜结果", "insights.noResults": "无有效资料", "insights.technical": "技术详情", "insights.technicalNote": "内部运行 ID 与时间戳，保留用于追溯。", "insights.completed": "完成时间", "insights.queryExecutions": "条查询执行", "insights.success": "已完成", "insights.skipped": "已跳过", "insights.failed": "失败", "insights.discoveries": "次发现", "insights.discovery": "次发现",
    "sources.eyebrow": "渠道连接状态", "sources.lede": "本工作区可以在哪些渠道上发现合作对象。凭据只保存在服务端，永远不会发送到浏览器。", "sources.connected": "已连接", "sources.notConfigured": "未配置", "sources.configure": "配置", "sources.configureTitle": "配置 {channel}", "sources.configureBody": "把该渠道的凭据设置为服务端环境变量，然后重启本地服务。浏览器永远不会收到该值。", "sources.developer": "开发者配置", "sources.developerNote": "只显示变量名——任何值都不会被显示或发送到浏览器。", "sources.credential": "凭据变量", "sources.optional": "可选变量", "sources.connectedCount": "已连接 {count} 个", "sources.alwaysOn": "始终可用", "sources.controlledPurpose": "用于可重复演示的离线夹具", "sources.storedRecords": "已存储 {count} 个合作对象",
    "general.partner": "个合作对象", "general.partners": "个合作对象", "general.run": "次运行", "general.runs": "次运行", "general.of": "/", "general.reviewed": "已审核", "general.notObserved": "未观察到", "general.notAvailable": "暂无", "general.none": "无", "general.unknown": "未知", "general.cancel": "取消",
    "campaign.goal": "目标", "campaign.markets": "目标市场", "campaign.themes": "内容主题", "campaign.audience": "目标受众", "campaign.exclusions": "排除项", "campaign.current": "当前 Campaign", "campaign.currentNote": "原始人工简报与结构化定义始终分开保存。", "campaign.ready": "可开始规划", "campaign.notGenerated": "尚未生成结构化定义。", "campaign.original": "原始人工简报",
    "query.proposed": "AI 建议查询", "query.approve": "批准", "query.approved": "已批准", "query.edit": "编辑并批准", "query.edited": "编辑后批准", "query.reject": "拒绝", "query.rejected": "已拒绝", "query.final": "最终可执行查询", "query.comment": "可选人工备注", "query.commentPlaceholder": "为什么批准、编辑或拒绝这条查询？", "query.reviewAria": "审核决定",
    "execution.remaining": "还有 {count} 条查询未决定。", "execution.readyCount": "已有 {count} 条可执行查询。", "execution.allRejected": "没有可执行查询。请至少批准或编辑一条建议。", "execution.runLive": "运行 Live Discovery", "execution.liveConfigured": "{total} 个渠道中已连接 {count} 个", "execution.liveNone": "未连接任何 Live 渠道", "execution.generating": "正在结构化 Campaign 并起草查询…", "execution.runningControlled": "正在运行离线 Controlled Demo…", "execution.runningLive": "正在调用已连接的 Live 渠道…", "execution.pipelineRunning": "正在处理真实后端阶段…", "execution.pipelineComplete": "后端响应已完成整个 Pipeline。",
    "run.output": "实际实现输出", "run.complete": "发现运行完成", "run.completeIssues": "发现运行完成，但渠道存在问题", "run.retrieved": "已检索", "run.retrievedNote": "渠道返回记录", "run.duplicates": "重复项", "run.duplicatesNote": "已安全移除", "run.newPartners": "新增合作对象", "run.newNote": "本次已存储", "run.yield": "新增合作对象率", "run.yieldNote": "新鲜结果占比", "run.contactFirst": "优先联系", "run.worth": "值得联系", "run.opportunistic": "机会型", "run.needsReview": "待审核", "run.humanAttention": "需要人工关注", "run.executable": "已执行 {count} 条批准查询。", "run.zeroTitle": "没有返回有效的合作对象资料。", "run.zeroText": "本次运行已如实记录。请先查看渠道状态和查询证据，再尝试新的搜索角度。",
    "overview.latest": "最近一次发现", "overview.noRun": "还没有已存储的发现", "overview.noRunText": "Controlled Demo 是创建第一批证据的可靠方式。", "overview.openDiscover": "打开「发现」", "overview.partnerRecords": "合作对象记录", "overview.partnerRecordsNote": "已去重证据", "overview.p1": "P1 · 优先联系", "overview.p1Note": "最高行动优先级", "overview.needsReview": "待审核", "overview.needsReviewNote": "需要人工判断", "overview.humanDecisions": "人工判断", "overview.humanDecisionsNote": "已存储审核", "overview.latestYield": "最近新增合作对象率", "overview.latestYieldNote": "新鲜结果占比", "overview.decisionQueue": "优先级分布", "overview.decisionQueueTitle": "合作对象池的分布", "overview.channelReadiness": "渠道准备状态", "overview.channelReadinessTitle": "可以在哪些渠道发现", "overview.channelNote": "已连接不等于检索成功。", "overview.ready": "已就绪", "overview.configured": "已连接", "overview.notConfigured": "未配置", "overview.currentRun": "{mode} 发现", "overview.newRecords": "新增 {count} 条合作对象记录",
    "priority.P1": "优先联系", "priority.P2": "值得联系", "priority.P3": "机会型", "priority.Needs Review": "待审核",
    "signal.activity.high": "高度活跃", "signal.activity.moderate": "活跃", "signal.activity.low": "低活跃", "signal.activity.unknown": "活跃度未知", "signal.relevance.high": "强相关", "signal.relevance.moderate": "中等相关", "signal.relevance.low": "低相关", "signal.relevance.unknown": "相关度未知", "signal.market.target": "目标市场", "signal.market.outside": "目标市场外", "signal.market.conflicting": "市场证据冲突", "signal.market.unknown": "市场未知",
    "signalField.activity": "活跃度", "signalField.relevance": "相关度", "signalField.content_relevance": "相关度", "signalField.audience": "受众", "signalField.audience_size": "受众", "signalField.market": "市场", "signalField.actionability": "可行动性", "signalField.record_quality": "记录质量",
    "signalValue.high": "高", "signalValue.moderate": "中等", "signalValue.low": "低", "signalValue.target": "目标市场", "signalValue.outside": "目标市场外", "signalValue.available": "可用", "signalValue.missing": "未观察到", "signalValue.unavailable": "不可用", "signalValue.usable": "可用", "signalValue.insufficient": "证据不足", "signalValue.incomplete": "不完整", "signalValue.conflicting": "冲突", "signalValue.spam": "疑似垃圾信号", "signalValue.small": "小", "signalValue.medium": "中", "signalValue.large": "大", "signalValue.unknown": "未知",
    "executionStatus.SUCCESS_WITH_RESULTS": "成功返回结果", "executionStatus.SUCCESS_ZERO_RESULTS": "成功但无结果", "executionStatus.FAILED": "失败", "executionStatus.SKIPPED_NOT_CONFIGURED": "已跳过 · 未配置",
    "partner.market": "市场", "partner.followers": "受众规模", "partner.channel": "渠道", "partner.type": "合作类型", "partner.activity": "活跃度", "partner.relevance": "相关度", "partner.audience": "可能受众", "partner.viewEvidence": "查看证据", "partner.review": "审核", "partner.openProfile": "打开主页", "partner.demoRecord": "样本记录", "partner.demoProfileNote": "Controlled Demo 使用合成数据，因此不存在可打开的外部社媒主页。", "partner.profileUnavailable": "主页不可用", "partner.audienceUnknown": "受众不明确", "partner.contactAvailable": "可联系",
    "detail.title": "合作对象证据", "detail.close": "关闭合作对象证据", "detail.loading": "正在加载合作对象证据…",
    "detail.whyPriority": "为什么是这个优先级？", "detail.keySignals": "关键信号", "detail.aiAudienceTitle": "AI 受众推断", "detail.likelyAudience": "可能受众", "detail.confidence": "置信度", "detail.whyAi": "为什么？查看 AI 证据", "detail.hideAi": "收起 AI 证据", "detail.viewEvidence": "查看证据", "detail.hideEvidence": "收起证据", "detail.observedContent": "已观察内容", "detail.showMore": "显示更多", "detail.showLess": "收起", "detail.noEvidence": "该信号没有已存储的证据。",
    "detail.observed": "已观察事实", "detail.observedDesc": "来源实际返回的内容。", "detail.sourceObserved": "来源观察", "detail.platform": "渠道", "detail.followers": "受众规模", "detail.retrieved": "检索时间", "detail.mode": "发现模式", "detail.bioEmpty": "来源未返回简介。", "detail.samplesEmpty": "来源未返回内容样本。", "detail.dateUnknown": "未观察到日期", "detail.query": "来源查询", "detail.angle": "搜索角度", "detail.connector": "来源连接器", "detail.runId": "运行 ID", "detail.provenance": "来源溯源", "detail.derived": "衍生信号", "detail.derivedDesc": "对已观察证据的确定性解释。", "detail.systemDerived": "系统衍生", "detail.ai": "AI 推断", "detail.aiDesc": "受众假设，与事实分开保存。", "detail.aiDerived": "AI 衍生", "detail.modelUnavailable": "模型不可用", "detail.audienceUnclear": "受众仍不明确", "detail.human": "人工判断", "detail.humanDesc": "控制后续运营使用的决定。", "detail.humanOwned": "人工所有", "detail.decision": "决定", "detail.reason": "结构化原因", "detail.reasonNone": "无结构化原因", "detail.comment": "可选备注", "detail.commentPlaceholder": "补充系统无法知道的背景…", "detail.lastDecision": "最近保存的决定", "detail.noDecision": "尚未存储人工决定。", "detail.save": "保存决定", "detail.saved": "人工决定已保存。", "detail.reasonStrong": "证据匹配强", "detail.reasonFollowup": "需要补充证据", "detail.reasonOut": "不符合 Campaign", "detail.contentSamples": "内容证据", "detail.noSignals": "这条记录尚未存储衍生信号。", "detail.fullEvidence": "完整证据与溯源", "detail.fullEvidenceNote": "这个合作对象背后的每一条已存储事实，保留用于追溯。",
    "angle.core_topic": "核心主题", "angle.creator_workflow": "创作者工作流", "angle.professional_identity": "职业身份", "angle.use_case": "使用场景", "angle.audience_problem": "受众问题", "angle.adjacent_tool": "相邻工具",
    "review.approve": "已批准", "review.reject": "已拒绝", "review.needs_review": "待审核", "review.unreviewed": "未审核",
    "error.default": "本地 UI 服务未能完成请求。", "error.brief_required": "请先描述合作伙伴 Campaign，再生成 Search Plan。", "error.draft_plan_missing": "简报信息不完整。请先补充缺失的 Campaign 要求。", "error.query_review_invalid": "请审核每条查询，并为编辑后的查询填写最终文本。", "error.workflow_not_found": "该草稿已不在本地服务会话中，请重新生成。", "error.live_confirmation_required": "执行前请确认 Live 渠道用量。", "error.creator_not_found": "未找到合作对象记录。", "error.invalid_review": "请选择有效的人工决定。", "error.insufficient_business_context": "请补充足够的产品、问题与价值背景，以生成可验证的 ICP 假设。", "error.website_analysis_unavailable": "离线演示无法分析网站，请添加人工产品描述。", "error.malformed_icp_output": "ICP 服务返回的结构化数据格式错误。", "error.no_useful_icp_hypotheses": "服务没有返回三个有用、可验证的假设。", "error.incomplete_discovery_criteria": "确认前请补全必需的发现条件。", "error.icp_provider_not_configured": "尚未配置 Live ICP 生成。", "error.icp_provider_failure": "Live ICP 服务已安全失败。",
  },
};

const STORAGE_KEYS = { language: "creatorDiscoveryLanguage", theme: "creatorDiscoveryTheme" };
const state = {
  page: "discover", workflow: null, queryDecisions: new Map(), queryInputs: new Map(),
  bootstrap: null, lastRunSummary: null, activeCreatorId: null, activeCreatorDetail: null,
  icpGeneration: null, icpSelection: null, editingIcpId: null,
  language: "en", theme: "light", running: false,
  dashboardFilters: { date: "30", icp: "all", source: "all", run: "all" },
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
const t = (key, variables = {}) => {
  const dictionary = TRANSLATIONS[state.language] || TRANSLATIONS.en;
  let value = dictionary[key] ?? TRANSLATIONS.en[key] ?? key;
  Object.entries(variables).forEach(([name, replacement]) => { value = value.replaceAll(`{${name}}`, String(replacement)); });
  return value;
};
const safeStored = (key, fallback) => { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } };
const persist = (key, value) => { try { localStorage.setItem(key, value); } catch { /* local preferences are optional */ } };
const formatNumber = (value) => value == null ? t("general.notObserved") : new Intl.NumberFormat(state.language === "zh" ? "zh-CN" : "en-US", { notation: Number(value) >= 10000 ? "compact" : "standard", maximumFractionDigits: 1 }).format(Number(value));
const formatPercent = (value) => `${Math.round(Number(value || 0) * 100)}%`;
const formatDate = (value) => value ? new Intl.DateTimeFormat(state.language === "zh" ? "zh-CN" : "en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : t("general.notAvailable");
const humanize = (value) => String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const CHANNELS = ["instagram", "x", "youtube", "web"];
const PARTNER_TYPES = ["creator", "kol", "influencer", "micro_influencer", "affiliate", "community", "media", "industry_expert"];

const CHANNEL_SVG = {
  instagram: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.2" y="3.2" width="17.6" height="17.6" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.7" r="1.2" fill="currentColor"/></svg>',
  x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.9 2h3.7l-8.1 9.2L24 22h-7.4l-5.8-7.6L4.2 22H.5l8.6-9.8L0 2h7.6l5.2 6.9L18.9 2Zm-1.3 18.1h2L6.5 3.8H4.4l13.2 16.3Z"/></svg>',
  youtube: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M23 12s0-3.4-.4-5a2.8 2.8 0 0 0-2-2C18.9 4.5 12 4.5 12 4.5s-6.9 0-8.6.5a2.8 2.8 0 0 0-2 2C1 8.6 1 12 1 12s0 3.4.4 5a2.8 2.8 0 0 0 2 2c1.7.5 8.6.5 8.6.5s6.9 0 8.6-.5a2.8 2.8 0 0 0 2-2c.4-1.6.4-5 .4-5ZM9.8 15.3V8.7l5.7 3.3-5.7 3.3Z"/></svg>',
  web: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.9"/><ellipse cx="12" cy="12" rx="4" ry="9" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M3.5 9h17M3.5 15h17" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>',
  controlled: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Zm0 2.3L6 8.7v6.6l6 3.4 6-3.4V8.7l-6-3.4Z"/></svg>',
};

const channelLabel = (channel) => t(`channel.${channel}`) === `channel.${channel}` ? humanize(channel) : t(`channel.${channel}`);
const partnerTypeLabel = (type) => t(`partnerType.${type}`) === `partnerType.${type}` ? humanize(type) : t(`partnerType.${type}`);

function channelIcon(channel, withLabel = false) {
  const key = CHANNEL_SVG[channel] ? channel : "web";
  const label = channelLabel(key);
  const accessibility = withLabel ? 'aria-hidden="true"' : `role="img" aria-label="${escapeHtml(label)}"`;
  return `<span class="platform-mark platform-${key}" ${accessibility}>${CHANNEL_SVG[key]}</span>${withLabel ? `<span>${escapeHtml(label)}</span>` : ""}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.error?.message || t("error.default"));
    error.code = payload.error?.code || "default";
    throw error;
  }
  return payload;
}

function localizedError(error) {
  const key = `error.${error?.code || "default"}`;
  return t(key) === key ? (error?.message || t("error.default")) : t(key);
}

function applyStaticTranslations() {
  $$('[data-i18n]').forEach((element) => { element.textContent = t(element.dataset.i18n); });
  $$('[data-i18n-placeholder]').forEach((element) => { element.placeholder = t(element.dataset.i18nPlaceholder); });
  $$('[data-i18n-aria]').forEach((element) => { element.setAttribute("aria-label", t(element.dataset.i18nAria)); });
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
}

function captureQueryInputs() {
  $$('.query-card').forEach((card) => {
    state.queryInputs.set(card.dataset.queryId, {
      edited: $('.edited-query', card)?.value || "",
      comment: $('.query-comment', card)?.value || "",
    });
  });
}

function setLanguage(language, save = true) {
  if (!TRANSLATIONS[language]) return;
  captureQueryInputs();
  state.language = language;
  if (save) persist(STORAGE_KEYS.language, language);
  $$('.language-switch button').forEach((button) => { const active = button.dataset.lang === language; button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); });
  applyStaticTranslations();
  if (state.workflow) renderPlan();
  renderICP();
  renderBootstrap();
  if (state.lastRunSummary) renderRunResult(state.lastRunSummary);
  if (state.activeCreatorDetail) renderPartnerDetail(state.activeCreatorDetail);
}

function setTheme(theme, save = true) {
  if (!["light", "dark"].includes(theme)) return;
  state.theme = theme;
  document.documentElement.dataset.theme = theme;
  $('meta[name="theme-color"]').content = theme === "dark" ? "#12151f" : "#edf0f7";
  $$('.theme-switch button').forEach((button) => { const active = button.dataset.themeChoice === theme; button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active)); });
  if (save) persist(STORAGE_KEYS.theme, theme);
}

const PAGES = ["overview", "icp", "discover", "partners", "insights", "sources"];

// A partner's evidence is addressable: #partners/<record_id> opens the Partner
// Evidence sheet directly, so a reviewer can be sent straight to one partner.
function routeFromHash(hash) {
  const [page, recordId] = String(hash || "").replace(/^#/, "").split("/");
  return { page, recordId: recordId ? decodeURIComponent(recordId) : null };
}

function setPage(page, updateHash = true) {
  if (!PAGES.includes(page)) page = "overview";
  state.page = page;
  $$('.page').forEach((section) => section.classList.toggle("active", section.id === `page-${page}`));
  $$('.primary-nav button').forEach((button) => button.classList.toggle("active", button.dataset.page === page));
  if (updateHash) history.replaceState(null, "", `#${page}`);
  if (page === "partners") renderPartners();
  if (page === "icp") renderICP();
  if (page === "insights") renderInsights();
  if (page === "sources") renderDataSources();
  window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

function showAlert(element, message, kind = "error") {
  element.hidden = false;
  element.className = `inline-alert ${kind}`;
  element.textContent = message;
}
function clearAlert(element) { element.hidden = true; element.textContent = ""; }
function showToast(message) { const toast = $('#toast'); toast.textContent = message; toast.hidden = false; clearTimeout(showToast.timer); showToast.timer = setTimeout(() => { toast.hidden = true; }, 2600); }

/* ---- ICP discovery ------------------------------------------------------- */

const splitItems = (value) => String(value || "").split(",").map((item) => item.trim()).filter(Boolean);

function businessContextPayload() {
  const data = new FormData($('#business-context-form'));
  return {
    product_name: data.get("product_name"),
    website_url: data.get("website_url") || null,
    product_description: data.get("product_description") || null,
    problem: data.get("problem"),
    strongest_value: data.get("strongest_value"),
    current_users: data.get("current_users"),
    current_alternatives: splitItems(data.get("current_alternatives")),
    pain_signals: splitItems(data.get("pain_signals")),
    target_markets: splitItems(data.get("target_markets")),
    stage: data.get("stage"),
    provider_mode: "mock",
  };
}

function hypothesisDetail(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value || t("general.none"))}</dd></div>`;
}

function hypothesisList(label, values, tone = "") {
  return `<div class="hypothesis-list ${tone}"><dt>${escapeHtml(label)}</dt><dd>${(values || []).map((value) => `<span>${escapeHtml(value)}</span>`).join("") || escapeHtml(t("general.none"))}</dd></div>`;
}

function hypothesisEditForm(hypothesis) {
  return `<form class="hypothesis-edit-form" data-hypothesis-id="${escapeHtml(hypothesis.hypothesis_id)}" data-version="${hypothesis.version}">
    <label>${t("icp.hypothesis")}<input name="name" value="${escapeHtml(hypothesis.name)}" required /></label>
    <label>${t("icp.who")}<textarea name="who" rows="3" required>${escapeHtml(hypothesis.who)}</textarea></label>
    <label>${t("icp.corePain")}<textarea name="core_pain" rows="3" required>${escapeHtml(hypothesis.core_pain)}</textarea></label>
    <label>${t("icp.valueProposition")}<textarea name="value_proposition" rows="3" required>${escapeHtml(hypothesis.value_proposition)}</textarea></label>
    <label>${t("icp.unknowns")}<input name="unknowns" value="${escapeHtml((hypothesis.unknowns || []).join(", "))}" required /></label>
    <div class="form-actions"><button class="button mini" type="button" data-icp-cancel-edit>${t("icp.cancelEdit")}</button><button class="button primary mini" type="submit">${t("icp.saveVersion")}</button></div>
  </form>`;
}

function renderICPHypotheses() {
  const section = $('#icp-hypotheses');
  const stored = state.bootstrap?.icp_workspace?.hypotheses || [];
  const currentContextId = state.bootstrap?.icp_workspace?.current?.hypothesis?.business_context_id;
  const fallbackContextId = currentContextId || stored[0]?.business_context_id;
  const hypotheses = state.icpGeneration?.hypotheses
    || stored.filter((item) => item.business_context_id === fallbackContextId).sort((a, b) => a.recommended_order - b.recommended_order).slice(0, 3);
  section.hidden = hypotheses.length !== 3;
  if (section.hidden) return;
  $('#hypothesis-grid').innerHTML = hypotheses.map((hypothesis) => {
    const editing = state.editingIcpId === hypothesis.hypothesis_id;
    const evaluation = hypothesis.evaluation || {};
    const body = editing ? hypothesisEditForm(hypothesis) : `
      <p class="hypothesis-who"><strong>${t("icp.who")}</strong>${escapeHtml(hypothesis.who)}</p>
      <dl class="hypothesis-core">
        ${hypothesisDetail(t("icp.context"), hypothesis.context)}
        ${hypothesisDetail(t("icp.corePain"), hypothesis.core_pain)}
        ${hypothesisDetail(t("icp.whyPain"), hypothesis.why_pain_matters)}
        ${hypothesisDetail(t("icp.alternative"), hypothesis.current_alternative)}
        ${hypothesisDetail(t("icp.valueProposition"), hypothesis.value_proposition)}
        ${hypothesisDetail(t("icp.trigger"), hypothesis.trigger)}
        ${hypothesisList(t("icp.intentSignals"), hypothesis.intent_signals, "signals")}
        ${hypothesisList(t("icp.where"), hypothesis.where_to_find)}
      </dl>
      <details class="hypothesis-evidence"><summary>${t("icp.testPriority")} · ${evaluation.comparison_score}/100 <span>${t("icp.estimated")}</span></summary>
        <p>${escapeHtml(hypothesis.test_priority_reason)}</p>
        <div class="evaluation-bars">${Object.entries(evaluation).filter(([key]) => key !== "comparison_score").map(([key, value]) => `<div><span>${escapeHtml(t(`icp.dimension.${key}`))}</span><i><b style="width:${Number(value)}%"></b></i><strong>${Number(value)}</strong></div>`).join("")}</div>
      </details>
      <div class="hypothesis-proof">${hypothesisDetail(t("icp.whyWork"), hypothesis.why_may_work)}${hypothesisList(t("icp.unknowns"), hypothesis.unknowns, "risks")}</div>
      <footer><button class="button primary mini" type="button" data-icp-select="${escapeHtml(hypothesis.hypothesis_id)}" data-version="${hypothesis.version}">${t("icp.select")}</button><button class="button mini" type="button" data-icp-edit="${escapeHtml(hypothesis.hypothesis_id)}">${t("icp.edit")}</button><button class="button mini" type="button" data-icp-save-later>${t("icp.saveLater")}</button></footer>`;
    return `<article class="hypothesis-card ${hypothesis.recommended_order === 1 ? "recommended" : ""}">
      <header><div><span>${t("icp.customer")} · ${t("icp.version", { version: hypothesis.version })}</span><h3>${escapeHtml(hypothesis.name)}</h3></div><b>#${hypothesis.recommended_order}</b></header>
      ${body}
    </article>`;
  }).join("");
}

function renderCriteria() {
  const panel = $('#criteria-panel');
  const criteria = state.icpSelection?.criteria;
  panel.hidden = !criteria;
  if (!criteria) return;
  const channelSet = new Set(criteria.channels || []);
  $('#criteria-form').innerHTML = `
    <label class="wide">${t("icp.partnerProfile")}<textarea name="partner_profile" rows="3" required>${escapeHtml(criteria.partner_profile)}</textarea></label>
    <label class="wide">${t("icp.criteriaGoal")}<input name="goal" value="${escapeHtml(criteria.goal)}" required /></label>
    <label>${t("icp.markets")}<input name="target_markets" value="${escapeHtml((criteria.target_markets || []).join(", "))}" required /></label>
    <label>${t("icp.themes")}<input name="content_themes" value="${escapeHtml((criteria.content_themes || []).join(", "))}" required /></label>
    <label>${t("icp.audience")}<input name="target_audience" value="${escapeHtml((criteria.target_audience || []).join(", "))}" required /></label>
    <label>${t("icp.criteriaSignals")}<input name="intent_signals" value="${escapeHtml((criteria.intent_signals || []).join(", "))}" /></label>
    <label>${t("icp.exclusions")}<input name="exclusions" value="${escapeHtml((criteria.exclusions || []).join(", "))}" /></label>
    <fieldset class="criteria-channels"><legend>${t("icp.channels")}</legend>${CHANNELS.map((channel) => `<label><input type="checkbox" name="channels" value="${channel}" ${channelSet.has(channel) ? "checked" : ""}/>${channelIcon(channel, true)}</label>`).join("")}</fieldset>
    <div class="criteria-boundary"><strong>${t("icp.assumption")}</strong><span>${t("icp.notPermission")}</span></div>
    <div class="form-actions"><button class="button primary" type="submit"><span>${t("icp.confirmCriteria")}</span><span aria-hidden="true">→</span></button></div>`;
}

function renderCurrentICP() {
  const current = state.bootstrap?.icp_workspace?.current;
  const root = $('#icp-current');
  if (!root) return;
  if (!current?.hypothesis) { root.innerHTML = ""; return; }
  const item = current.hypothesis;
  const runs = current.runs || [];
  root.innerHTML = `<article class="current-icp operational-surface"><div class="current-icp-heading"><div><p class="section-kicker">${t("icp.currentKicker")}</p><h2>${escapeHtml(item.name)} <small>${t("icp.version", { version: item.version })}</small></h2></div><span class="icp-status">${t("icp.testing")}</span></div>
    <div class="current-icp-grid"><div><span>${t("icp.who")}</span><p>${escapeHtml(item.who)}</p></div><div><span>${t("icp.corePain")}</span><p>${escapeHtml(item.core_pain)}</p></div><div><span>${t("icp.valueProposition")}</span><p>${escapeHtml(item.value_proposition)}</p></div></div>
    <div class="current-icp-chips">${(item.intent_signals || []).map((value) => `<i>${escapeHtml(value)}</i>`).join("")}</div>
    <details><summary>${t("icp.unknowns")} · ${t("icp.runs")}</summary><div class="current-icp-details">${hypothesisList(t("icp.where"), item.where_to_find)}${hypothesisList(t("icp.unknowns"), item.unknowns, "risks")}<div><dt>${t("icp.runs")}</dt><dd>${runs.length ? runs.map((run) => `<span>${escapeHtml(formatDate(run.completed_at))} · ${formatPercent(run.new_creator_yield)} ${t("run.yield")}</span>`).join("") : escapeHtml(t("icp.noRuns"))}</dd></div></div></details></article>`;
}

function renderICP() {
  renderCurrentICP();
  renderICPHypotheses();
  if (state.icpSelection) renderCriteria();
}

async function generateICP(event) {
  event?.preventDefault();
  const alert = $('#icp-alert'); clearAlert(alert);
  const button = $('#business-context-form button[type="submit"]');
  button.disabled = true; button.querySelector("span").textContent = t("icp.generating");
  try {
    state.icpGeneration = await api("/api/icp/generate", { method: "POST", body: JSON.stringify(businessContextPayload()) });
    state.icpSelection = null; state.editingIcpId = null;
    renderICPHypotheses(); await refreshWorkspace();
    $('#icp-hypotheses').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  } catch (error) { showAlert(alert, localizedError(error)); }
  finally { button.disabled = false; button.innerHTML = `<span>${t("icp.generate")}</span><span aria-hidden="true">→</span>`; }
}

async function saveICPEdit(form) {
  const hypothesisId = form.dataset.hypothesisId;
  const data = new FormData(form);
  try {
    const edited = await api("/api/icp/edit", { method: "POST", body: JSON.stringify({ hypothesis_id: hypothesisId, version: Number(form.dataset.version), changes: { name: data.get("name"), who: data.get("who"), core_pain: data.get("core_pain"), value_proposition: data.get("value_proposition"), unknowns: splitItems(data.get("unknowns")) } }) });
    if (state.icpGeneration) {
      state.icpGeneration.hypotheses = state.icpGeneration.hypotheses.map((item) => item.hypothesis_id === hypothesisId ? edited : item);
    } else if (state.bootstrap?.icp_workspace?.hypotheses) {
      state.bootstrap.icp_workspace.hypotheses = state.bootstrap.icp_workspace.hypotheses.map((item) => item.hypothesis_id === hypothesisId ? edited : item);
    }
    state.editingIcpId = null; renderICPHypotheses(); await refreshWorkspace(); showToast(t("icp.edited"));
  } catch (error) { showToast(localizedError(error)); }
}

async function selectICP(hypothesisId, version) {
  try {
    state.icpSelection = await api("/api/icp/select", { method: "POST", body: JSON.stringify({ hypothesis_id: hypothesisId, version: Number(version) }) });
    renderCriteria(); await refreshWorkspace();
    $('#criteria-panel').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  } catch (error) { showToast(localizedError(error)); }
}

async function confirmCriteria(event) {
  event.preventDefault();
  const alert = $('#criteria-alert'); clearAlert(alert);
  const data = new FormData(event.currentTarget);
  const criteria = {
    partner_profile: data.get("partner_profile"), goal: data.get("goal"),
    target_markets: splitItems(data.get("target_markets")), content_themes: splitItems(data.get("content_themes")),
    target_audience: splitItems(data.get("target_audience")), intent_signals: splitItems(data.get("intent_signals")),
    exclusions: splitItems(data.get("exclusions")), channels: data.getAll("channels"),
  };
  try {
    state.workflow = await api("/api/icp/criteria/confirm", { method: "POST", body: JSON.stringify({ criteria_id: state.icpSelection.criteria.criteria_id, criteria }) });
    state.queryDecisions.clear(); state.queryInputs.clear(); state.lastRunSummary = null;
    renderPlan(); setPage("discover");
    $('#plan-section').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  } catch (error) { showAlert(alert, localizedError(error)); }
}

function definitionList(label, values) {
  const list = Array.isArray(values) && values.length ? values : [t("general.none")];
  return `<div><span>${escapeHtml(label)}</span><div class="definition-chips">${list.map((value) => `<i>${escapeHtml(value)}</i>`).join("")}</div></div>`;
}

function renderCampaignDefinition() {
  const definition = state.workflow?.campaign_parse?.definition;
  const root = $('#campaign-definition');
  if (!definition) { root.innerHTML = ""; return; }
  root.innerHTML = `
    <div class="definition-goal"><span>${t("campaign.goal")}</span><strong>${escapeHtml(definition.goal)}</strong></div>
    ${definitionList(t("campaign.markets"), definition.target_markets)}
    ${definitionList(t("campaign.themes"), definition.content_themes)}
    ${definitionList(t("campaign.audience"), definition.target_audience)}
    ${definitionList(t("campaign.exclusions"), definition.exclusions)}
  `;
}

function renderQueryGroups() {
  const queries = state.workflow?.draft_search_plan?.queries || [];
  const grouped = queries.reduce((result, query) => { (result[query.platform] ||= []).push(query); return result; }, {});
  let stagger = 0;
  // Only channels the plan actually proposed are shown — a campaign is never
  // forced onto every channel, so an absent channel simply has no group.
  $('#query-groups').innerHTML = CHANNELS.filter((channel) => grouped[channel]?.length).map((channel) => `
    <section class="query-platform-group">
      <h3>${channelIcon(channel, true)}<span>${grouped[channel].length}</span></h3>
      <div class="query-grid">${grouped[channel].map((query) => {
        const inputs = state.queryInputs.get(query.query_id) || {};
        const decision = state.queryDecisions.get(query.query_id) || "";
        const currentStagger = stagger++;
        return `<article class="query-card ${decision ? `decision-${decision}` : ""}" data-query-id="${escapeHtml(query.query_id)}" style="--stagger:${currentStagger}">
          <div class="query-card-top"><span class="angle-chip">${escapeHtml(t(`angle.${query.search_angle}`))}</span><span class="decision-result">${decision ? escapeHtml(t(`query.${decision === "edited" ? "edit" : decision}`)) : escapeHtml(t("query.proposed"))}</span></div>
          <h4>${escapeHtml(query.query_text)}</h4><p>${escapeHtml(query.rationale)}</p>
          <div class="query-actions" role="group" aria-label="${escapeHtml(t("query.reviewAria"))}">
            <button type="button" data-decision="approved" class="${decision === "approved" ? "selected" : ""}">✓ ${t("query.approve")}</button>
            <button type="button" data-decision="edited" class="${decision === "edited" ? "selected" : ""}">✎ ${t("query.edit")}</button>
            <button type="button" data-decision="rejected" class="${decision === "rejected" ? "selected" : ""}">× ${t("query.reject")}</button>
          </div>
          <div class="query-edit-fields" ${decision === "edited" ? "" : "hidden"}>
            <label>${t("query.final")}<input class="edited-query" value="${escapeHtml(inputs.edited || query.query_text)}" /></label>
          </div>
          <label class="query-comment-label">${t("query.comment")}<input class="query-comment" placeholder="${escapeHtml(t("query.commentPlaceholder"))}" value="${escapeHtml(inputs.comment || "")}" /></label>
        </article>`;
      }).join("")}</div>
    </section>`).join("");
  updateReviewState();
}

function renderPlan() {
  const origin = $('#icp-plan-origin');
  if (origin) {
    const icp = state.workflow?.icp_context;
    origin.hidden = !icp;
    origin.textContent = icp ? t("icp.origin", { name: icp.hypothesis_name, version: icp.hypothesis_version }) : "";
  }
  renderCampaignDefinition();
  renderQueryGroups();
  $('#plan-section').hidden = false;
}

function updateReviewState() {
  const queries = state.workflow?.draft_search_plan?.queries || [];
  const reviewed = queries.filter((query) => state.queryDecisions.has(query.query_id)).length;
  const executable = queries.filter((query) => ["approved", "edited"].includes(state.queryDecisions.get(query.query_id))).length;
  $('#review-progress').textContent = state.language === "zh" ? `${reviewed} / ${queries.length} ${t("general.reviewed")}` : `${reviewed} ${t("general.of")} ${queries.length} ${t("general.reviewed")}`;
  const mode = $('input[name="discovery-mode"]:checked')?.value || "controlled";
  const complete = queries.length > 0 && reviewed === queries.length;
  const confirmed = mode !== "live" || $('#confirm-live').checked;
  $('#run-discovery').disabled = !complete || executable === 0 || !confirmed || state.running;
  $('#execution-note').textContent = !complete ? t("execution.remaining", { count: queries.length - reviewed }) : executable === 0 ? t("execution.allRejected") : t("execution.readyCount", { count: executable });
  const runText = mode === "live" ? t("execution.runLive") : t("execution.runControlled");
  $('#run-discovery').innerHTML = `<span>${escapeHtml(runText)}</span><span aria-hidden="true">→</span>`;
  $$('.workflow-steps li').forEach((item, index) => { item.classList.toggle("active", index === (complete ? 2 : state.workflow ? 1 : 0)); item.classList.toggle("complete", index < (complete ? 2 : state.workflow ? 1 : 0)); });
}

function chooseDecision(queryId, decision) {
  captureQueryInputs();
  state.queryDecisions.set(queryId, decision);
  const card = $(`.query-card[data-query-id="${CSS.escape(queryId)}"]`);
  if (!card) return;
  card.className = `query-card decision-${decision}`;
  $$('.query-actions button', card).forEach((button) => button.classList.toggle("selected", button.dataset.decision === decision));
  $('.query-edit-fields', card).hidden = decision !== "edited";
  $('.decision-result', card).textContent = t(`query.${decision === "edited" ? "edit" : decision}`);
  if (decision === "edited" && !$('.edited-query', card).value) $('.edited-query', card).value = state.workflow.draft_search_plan.queries.find((query) => query.query_id === queryId)?.query_text || "";
  updateReviewState();
}

async function generatePlan() {
  const alert = $('#plan-alert');
  clearAlert(alert);
  const originalBrief = $('#campaign-brief').value.trim();
  const button = $('#generate-plan');
  button.disabled = true;
  button.querySelector('span').textContent = t("execution.generating");
  try {
    state.workflow = await api("/api/search-plan", { method: "POST", body: JSON.stringify({ original_brief: originalBrief }) });
    state.queryDecisions.clear(); state.queryInputs.clear(); state.lastRunSummary = null;
    if (!state.workflow.draft_search_plan) throw Object.assign(new Error("draft missing"), { code: "draft_plan_missing" });
    renderPlan();
    $('#plan-section').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
    renderOverview();
  } catch (error) { showAlert(alert, localizedError(error)); }
  finally { button.disabled = false; button.innerHTML = `<span>${t("brief.generate")}</span><span aria-hidden="true">→</span>`; }
}

function setPipelineState(status) {
  const pipeline = $('#pipeline-visual');
  pipeline.dataset.state = status;
  pipeline.setAttribute("aria-busy", String(status === "running"));
  $$('.pipeline-stage', pipeline).forEach((stage) => { stage.classList.toggle("running", status === "running"); stage.classList.toggle("complete", status === "complete"); stage.classList.toggle("error", status === "error"); });
}

function buildReviewActions() {
  captureQueryInputs();
  return (state.workflow?.draft_search_plan?.queries || []).map((query) => {
    const decision = state.queryDecisions.get(query.query_id);
    const inputs = state.queryInputs.get(query.query_id) || {};
    return { query_id: query.query_id, decision, edited_query_text: decision === "edited" ? inputs.edited : null, human_comment: inputs.comment || null };
  });
}

async function runDiscovery() {
  const alert = $('#run-alert'); clearAlert(alert);
  const mode = $('input[name="discovery-mode"]:checked')?.value || "controlled";
  const button = $('#run-discovery');
  state.running = true; button.disabled = true;
  button.querySelector('span').textContent = mode === "live" ? t("execution.runningLive") : t("execution.runningControlled");
  $('#execution-note').textContent = t("execution.pipelineRunning");
  setPipelineState("running");
  try {
    const result = await api("/api/run-discovery", { method: "POST", body: JSON.stringify({ workflow_id: state.workflow.workflow_id, actions: buildReviewActions(), mode, confirm_live: mode === "live" && $('#confirm-live').checked }) });
    state.lastRunSummary = result.run_summary;
    setPipelineState("complete");
    renderRunResult(result.run_summary);
    await refreshWorkspace();
    $('#execution-note').textContent = t("execution.pipelineComplete");
    $('#run-result').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  } catch (error) { setPipelineState("error"); showAlert(alert, localizedError(error)); }
  finally { state.running = false; updateReviewState(); }
}

function metricCard(value, label, note, tone) { return `<article class="result-metric tone-${tone}"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span><small>${escapeHtml(note)}</small></article>`; }

function renderRunResult(summary) {
  const root = $('#run-result');
  const priority = summary.priority_counts || {};
  const newPartners = summary.new_creators;
  root.hidden = false;
  root.innerHTML = `<div class="result-heading"><div><p class="section-kicker">${t("run.output")}</p><h2>${summary.run_status === "COMPLETED" ? t("run.complete") : t("run.completeIssues")}</h2></div><span class="run-mode-chip">${escapeHtml(summary.mode)}</span></div>
    <div class="result-metrics">
      ${metricCard(formatNumber(summary.retrieved), t("run.retrieved"), t("run.retrievedNote"), "blue")}
      ${metricCard(formatNumber(summary.duplicates), t("run.duplicates"), t("run.duplicatesNote"), "amber")}
      ${metricCard(formatNumber(newPartners), t("run.newPartners"), t("run.newNote"), "green")}
      ${metricCard(formatPercent(summary.new_creator_yield), t("run.yield"), t("run.yieldNote"), Number(summary.new_creator_yield) > .35 ? "green" : "amber")}
    </div>
    <div class="priority-strip">
      <span class="priority-p1"><b>${formatNumber(priority.P1 || 0)}</b>${t("run.contactFirst")}</span>
      <span class="priority-p2"><b>${formatNumber(priority.P2 || 0)}</b>${t("run.worth")}</span>
      <span class="priority-p3"><b>${formatNumber(priority.P3 || 0)}</b>${t("run.opportunistic")}</span>
      <span class="priority-review"><b>${formatNumber(priority["Needs Review"] || 0)}</b>${t("run.needsReview")}</span>
    </div>
    ${Number(summary.retrieved) === 0 ? `<div class="zero-result"><span>◎</span><div><strong>${t("run.zeroTitle")}</strong><p>${t("run.zeroText")}</p></div></div>` : ""}
    <p class="result-footnote">${t("run.executable", { count: summary.query_history?.length || 0 })}</p>`;
}

/* ---- channel readiness ---------------------------------------------------- */

function channelRows() {
  // Prefer the server's channel list; fall back to the legacy providers map so
  // the UI still renders truthfully against an older bootstrap payload.
  const supplied = state.bootstrap?.workspace?.channels;
  if (Array.isArray(supplied) && supplied.length) {
    return supplied.filter((row) => CHANNELS.includes(row.channel));
  }
  const providers = state.bootstrap?.workspace?.providers || {};
  return CHANNELS.map((channel) => ({
    channel,
    label: channelLabel(channel),
    configured: Boolean(providers[channel]?.configured),
    status: providers[channel]?.configured ? "connected" : "not_configured",
    environment_variables: [],
  }));
}

function renderChannelReadiness() {
  const rows = channelRows();
  const connected = rows.filter((row) => row.configured).length;
  const readiness = $('#live-readiness');
  if (readiness) readiness.textContent = connected ? t("execution.liveConfigured", { count: connected, total: rows.length }) : t("execution.liveNone");
}

function priorityLabel(priority) { return t(`priority.${priority || "Needs Review"}`); }
// "Needs Review" is its own label, so the code and the label collapse into one
// chip instead of reading "Needs Review Needs Review".
function priorityChipInner(priority) {
  const code = String(priority || "Needs Review");
  const label = priorityLabel(code);
  return label === code
    ? `<b>${escapeHtml(code)}</b>`
    : `<b>${escapeHtml(code)}</b>${escapeHtml(label)}`;
}
function priorityText(priority) {
  const code = String(priority || "Needs Review");
  const label = priorityLabel(code);
  return label === code ? code : `${code} · ${label}`;
}
function reviewLabel(status) { return t(`review.${status || "unreviewed"}`); }
function signalLabel(type, value) { const key = `signal.${type}.${value || "unknown"}`; return t(key) === key ? humanize(value) : t(key); }
function signalValueLabel(value) { const key = `signalValue.${value || "unknown"}`; return t(key) === key ? humanize(value) : t(key); }

/* ---- partner pool --------------------------------------------------------- */

function partnerPool() {
  // The server computes this; deriving it locally keeps the page truthful if an
  // older payload arrives, and never invents a channel that has no records.
  const supplied = state.bootstrap?.partner_pool;
  if (supplied) return supplied;
  const partners = state.bootstrap?.creators || [];
  const overview = state.bootstrap?.overview || {};
  const channelCounts = Object.fromEntries(CHANNELS.map((channel) => [channel, 0]));
  const typeCounts = {};
  partners.forEach((partner) => {
    const channel = partner.channel || partner.platform;
    if (channel in channelCounts) channelCounts[channel] += 1;
    const type = partner.partner_type;
    if (type) typeCounts[type] = (typeCounts[type] || 0) + 1;
  });
  const reviewed = partners.filter((partner) => partner.review_status && partner.review_status !== "unreviewed").length;
  return {
    total: partners.length,
    priority_counts: overview.priority_counts || {},
    reviewed,
    unreviewed: partners.length - reviewed,
    channel_counts: channelCounts,
    partner_type_counts: typeCounts,
  };
}

function renderPartnerPool() {
  const pool = partnerPool();
  const priority = pool.priority_counts || {};
  const metrics = [
    [formatNumber(pool.total || 0), t("partners.total"), t("partners.totalNote"), "blue"],
    [formatNumber(priority.P1 || 0), t("partners.p1"), t("partners.p1Note"), "pink"],
    [formatNumber(priority.P2 || 0), t("partners.p2"), t("partners.p2Note"), "purple"],
    [formatNumber(priority["Needs Review"] || 0), t("partners.needsReview"), t("partners.needsReviewNote"), "amber"],
    [formatNumber(pool.reviewed || 0), t("partners.reviewed"), t("partners.reviewedNote"), "green"],
  ];
  const metricsRoot = $('#partner-metrics');
  if (metricsRoot) metricsRoot.innerHTML = metrics.map(([value, label, note, tone]) => metricCard(value, label, note, tone)).join("");

  const counts = pool.channel_counts || {};
  const distribution = $('#channel-distribution');
  if (!distribution) return;
  // Every channel is listed so the product model is visible, but a channel with
  // no stored records shows a real 0 — never a fabricated count.
  distribution.innerHTML = `<span class="distribution-label">${t("partners.byChannel")}</span>${CHANNELS.map((channel) => {
    const count = Number(counts[channel] || 0);
    return `<span class="channel-count ${count ? "has-records" : "no-records"}" title="${escapeHtml(count ? `${count}` : t("partners.noChannelRecords"))}">${channelIcon(channel)}<b>${formatNumber(count)}</b><small>${escapeHtml(channelLabel(channel))}</small></span>`;
  }).join("")}`;
}

/* ---- overview ------------------------------------------------------------- */

const dashboardRatio = (numerator, denominator) => denominator > 0 ? numerator / denominator : null;
const dashboardTimestamp = (value) => { const timestamp = value ? new Date(value).getTime() : NaN; return Number.isFinite(timestamp) ? timestamp : null; };

function relativeTime(value) {
  const timestamp = dashboardTimestamp(value);
  if (timestamp == null) return t("general.notAvailable");
  const seconds = Math.round((timestamp - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat(state.language === "zh" ? "zh-CN" : "en-US", { numeric: "auto" });
  if (Math.abs(seconds) < 60) return formatter.format(seconds, "second");
  const minutes = Math.round(seconds / 60);
  if (Math.abs(minutes) < 60) return formatter.format(minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return formatter.format(hours, "hour");
  return formatter.format(Math.round(hours / 24), "day");
}

function durationLabel(startedAt, completedAt) {
  const started = dashboardTimestamp(startedAt);
  const completed = dashboardTimestamp(completedAt);
  if (started == null || completed == null) return t("general.notAvailable");
  const seconds = Math.max(0, Math.round((completed - started) / 1000));
  return seconds < 1 ? t("dashboard.lessThanSecond") : t("dashboard.seconds", { count: seconds });
}

function dashboardMetricCard({ value, label, note, tone, delta }) {
  const deltaClass = delta?.direction === "up" ? "positive" : delta?.direction === "down" ? "negative" : "neutral";
  return `<article class="command-kpi tone-${tone}"><div class="metric-label">${escapeHtml(label)}</div><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small><span class="metric-delta ${deltaClass}">${escapeHtml(delta?.label || t("dashboard.noComparison"))}</span></article>`;
}

function syncDashboardFilters() {
  const data = state.bootstrap || {};
  const current = data.icp_workspace?.current?.hypothesis;
  const runRows = [...(data.runs || [])].sort((a, b) => (dashboardTimestamp(b.completed_at) || 0) - (dashboardTimestamp(a.completed_at) || 0));
  const selects = {
    icp: $('#dashboard-icp-filter'),
    source: $('#dashboard-source-filter'),
    run: $('#dashboard-run-filter'),
  };
  if (!selects.icp || !selects.source || !selects.run) return;
  selects.icp.innerHTML = `<option value="all">${escapeHtml(t("dashboard.allIcps"))}</option>${current ? `<option value="${escapeHtml(current.hypothesis_id)}">${escapeHtml(current.name)} · ${escapeHtml(t("icp.version", { version: current.version }))}</option>` : ""}`;
  selects.source.innerHTML = `<option value="all">${escapeHtml(t("dashboard.allSources"))}</option>${CHANNELS.map((channel) => `<option value="${channel}">${escapeHtml(channelLabel(channel))}</option>`).join("")}`;
  selects.run.innerHTML = `<option value="all">${escapeHtml(t("dashboard.allRuns"))}</option>${runRows.map((run, index) => `<option value="${escapeHtml(run.run_id)}">${escapeHtml(t("insights.historyItem", { index: runRows.length - index }))} · ${escapeHtml(formatDate(run.completed_at))}</option>`).join("")}`;
  Object.entries(selects).forEach(([key, select]) => {
    const requested = state.dashboardFilters[key];
    select.value = [...select.options].some((option) => option.value === requested) ? requested : "all";
    state.dashboardFilters[key] = select.value;
  });
  $('#dashboard-date-filter').value = state.dashboardFilters.date;
}

function buildDashboardModel(data) {
  const allRuns = [...(data.runs || [])].sort((a, b) => (dashboardTimestamp(b.completed_at) || 0) - (dashboardTimestamp(a.completed_at) || 0));
  const allQueries = data.query_history || [];
  const allCreators = data.creators || [];
  const currentICP = data.icp_workspace?.current || null;
  const filters = state.dashboardFilters;
  const cutoff = filters.date === "all" ? null : Date.now() - Number(filters.date) * 86400000;
  const icpRunIds = new Set((currentICP?.runs || []).map((run) => run.run_id));
  const dateMatch = (value) => cutoff == null || (dashboardTimestamp(value) || 0) >= cutoff;
  const icpMatch = (runId) => filters.icp === "all" || icpRunIds.has(runId);
  const filteredRuns = allRuns.filter((run) => dateMatch(run.completed_at || run.started_at)
    && (filters.run === "all" || run.run_id === filters.run)
    && icpMatch(run.run_id));
  const runIds = new Set(filteredRuns.map((run) => run.run_id));
  const filteredQueries = allQueries.filter((row) => runIds.has(row.run_id)
    && (filters.source === "all" || row.platform === filters.source));
  const filteredCreators = allCreators.filter((creator) => dateMatch(creator.created_at)
    && (filters.run === "all" ? (filters.icp === "all" || icpRunIds.has(creator.run_id)) : creator.run_id === filters.run)
    && (filters.source === "all" || (creator.channel || creator.platform) === filters.source));

  const latestRun = filteredRuns[0] || null;
  const previousRun = filteredRuns[1] || null;
  const reviewed = filteredCreators.filter((creator) => creator.review_status && creator.review_status !== "unreviewed");
  const approved = filteredCreators.filter((creator) => creator.review_status === "approve");
  const rejected = filteredCreators.filter((creator) => creator.review_status === "reject");
  const needsReviewDecision = filteredCreators.filter((creator) => creator.review_status === "needs_review");
  const finalDecisions = approved.length + rejected.length;
  const queue = filteredCreators.filter((creator) => !["approve", "reject"].includes(creator.review_status)).length;
  const highPriority = filteredCreators.filter((creator) => ["P1", "P2"].includes(creator.priority)).length;
  const rawResults = filteredQueries.length
    ? filteredQueries.reduce((sum, row) => sum + Number(row.retrieved || 0), 0)
    : filteredRuns.reduce((sum, run) => sum + Number(run.retrieved || 0), 0);
  const duplicateCount = filteredQueries.length
    ? filteredQueries.reduce((sum, row) => sum + Number(row.duplicates || 0), 0)
    : filteredRuns.reduce((sum, run) => sum + Number(run.duplicates || 0), 0);
  const signalsExtracted = filteredCreators.filter((creator) => creator.has_signals !== false && creator.activity != null).length;
  const audienceInferred = filteredCreators.filter((creator) => creator.has_audience_inference !== false && Array.isArray(creator.likely_audience)).length;
  const priorityAssigned = filteredCreators.filter((creator) => creator.has_priority_decision !== false && creator.priority).length;
  const failedQueries = filteredQueries.filter((row) => row.execution_status === "FAILED");
  const zeroQueries = filteredQueries.filter((row) => row.execution_status === "SUCCESS_ZERO_RESULTS");
  const failedRuns = filteredRuns.filter((run) => run.status && run.status !== "COMPLETED");
  const approvalRate = dashboardRatio(approved.length, finalDecisions);
  const duplicateRate = dashboardRatio(duplicateCount, rawResults);
  const latestNew = Number(latestRun?.new_creators || 0);
  let newDelta = null;
  if (latestRun && previousRun) {
    const previous = Number(previousRun.new_creators || 0);
    const change = previous ? (latestNew - previous) / previous : latestNew ? 1 : 0;
    newDelta = { direction: change > 0 ? "up" : change < 0 ? "down" : "flat", label: t("dashboard.vsPrevious", { value: `${change > 0 ? "+" : ""}${Math.round(change * 100)}%` }) };
  }

  const stages = [
    ["raw", t("dashboard.rawResults"), rawResults],
    ["unique", t("dashboard.uniqueRecords"), filteredCreators.length],
    ["signals", t("dashboard.signalsExtracted"), signalsExtracted],
    ["audience", t("dashboard.audienceInferred"), audienceInferred],
    ["priority", t("dashboard.priorityAssigned"), priorityAssigned],
    ["reviewed", t("dashboard.humanReviewed"), reviewed.length],
    ["approved", t("dashboard.finalApproved"), approved.length],
  ].map(([key, label, count], index, rows) => ({ key, label, count, conversion: index ? dashboardRatio(count, rows[index - 1][2]) : null }));
  const drops = stages.slice(1).map((stage, index) => ({ from: stages[index], to: stage, count: Math.max(0, stages[index].count - stage.count) }));
  const biggestDrop = drops.sort((a, b) => b.count - a.count)[0] || null;
  const dropReason = biggestDrop?.to.key === "unique" ? t("dashboard.duplicateDrop")
    : biggestDrop?.to.key === "reviewed" || biggestDrop?.to.key === "approved" ? t("dashboard.reviewDrop")
      : biggestDrop?.count ? t("dashboard.pipelineDrop") : t("dashboard.noDrop");

  const creatorGroups = (keyFor) => filteredCreators.reduce((groups, creator) => {
    const key = keyFor(creator);
    if (!key) return groups;
    if (!groups[key]) groups[key] = [];
    groups[key].push(creator);
    return groups;
  }, {});
  const creatorsByChannel = creatorGroups((creator) => creator.channel || creator.platform);
  const creatorsByQuery = creatorGroups((creator) => creator.query_id);
  const sourceGroups = filteredQueries.reduce((groups, row) => {
    const key = row.platform || "web";
    if (!groups[key]) groups[key] = [];
    groups[key].push(row);
    return groups;
  }, {});
  const sourcePerformance = Object.entries(sourceGroups).map(([channel, rows]) => {
    const candidates = creatorsByChannel[channel] || [];
    const sourceApproved = candidates.filter((creator) => creator.review_status === "approve").length;
    const sourceRejected = candidates.filter((creator) => creator.review_status === "reject").length;
    const sourceFinal = sourceApproved + sourceRejected;
    const retrieved = rows.reduce((sum, row) => sum + Number(row.retrieved || 0), 0);
    const fresh = rows.reduce((sum, row) => sum + Number(row.new_creators || 0), 0);
    return { channel, retrieved, fresh, yield: dashboardRatio(fresh, retrieved), highPriority: candidates.filter((creator) => ["P1", "P2"].includes(creator.priority)).length, finalDecisions: sourceFinal, approved: sourceApproved, approvalRate: dashboardRatio(sourceApproved, sourceFinal), errors: rows.filter((row) => row.execution_status === "FAILED").length };
  }).sort((a, b) => (b.yield ?? -1) - (a.yield ?? -1));
  const queryPerformance = filteredQueries.map((row) => {
    const candidates = creatorsByQuery[row.query_id] || [];
    const queryApproved = candidates.filter((creator) => creator.review_status === "approve").length;
    const queryRejected = candidates.filter((creator) => creator.review_status === "reject").length;
    const queryFinal = queryApproved + queryRejected;
    return { ...row, highPriority: candidates.filter((creator) => ["P1", "P2"].includes(creator.priority)).length, finalDecisions: queryFinal, approvalRate: dashboardRatio(queryApproved, queryFinal) };
  }).sort((a, b) => (b.new_creator_yield ?? -1) - (a.new_creator_yield ?? -1)).slice(0, 8);

  const today = new Date();
  const reviewedToday = reviewed.filter((creator) => { const date = creator.reviewed_at ? new Date(creator.reviewed_at) : null; return date && date.getFullYear() === today.getFullYear() && date.getMonth() === today.getMonth() && date.getDate() === today.getDate(); }).length;
  const reviewWaits = reviewed.map((creator) => { const created = dashboardTimestamp(creator.created_at); const decided = dashboardTimestamp(creator.reviewed_at); return created != null && decided != null ? Math.max(0, decided - created) : null; }).filter((value) => value != null);
  const averageReviewMinutes = reviewWaits.length ? Math.round(reviewWaits.reduce((sum, value) => sum + value, 0) / reviewWaits.length / 60000) : null;
  const rejectionReasons = rejected.reduce((counts, creator) => { const reason = creator.review_reason || t("general.unknown"); counts[reason] = (counts[reason] || 0) + 1; return counts; }, {});
  const topRejections = Object.entries(rejectionReasons).sort((a, b) => b[1] - a[1]);

  const runTrend = filteredRuns.map((run) => {
    const candidates = filteredCreators.filter((creator) => creator.run_id === run.run_id);
    const runApproved = candidates.filter((creator) => creator.review_status === "approve").length;
    const runRejected = candidates.filter((creator) => creator.review_status === "reject").length;
    return { run, approvalRate: dashboardRatio(runApproved, runApproved + runRejected), reviewed: runApproved + runRejected };
  }).reverse();

  const currentRuns = currentICP?.runs || [];
  const attention = [];
  if (failedQueries.length || failedRuns.length) attention.push({ title: t("dashboard.failedQueries", { count: failedQueries.length }), why: t("dashboard.failedWhy"), page: "insights", action: t("dashboard.openRuns") });
  if (queue) attention.push({ title: t("dashboard.pendingReviews", { count: queue }), why: t("dashboard.pendingWhy"), page: "partners", action: t("dashboard.reviewNow") });
  if (currentICP?.hypothesis && !currentRuns.length) attention.push({ title: t("dashboard.untestedIcp"), why: t("dashboard.untestedWhy"), page: "discover", action: t("dashboard.runDiscovery") });
  if (zeroQueries.length) attention.push({ title: t("dashboard.zeroQueries", { count: zeroQueries.length }), why: t("dashboard.zeroWhy"), page: "insights", action: t("dashboard.openRuns") });
  const nextAction = failedQueries.length ? { title: t("dashboard.nextFailure", { count: failedQueries.length }), page: "insights", action: t("dashboard.openRuns") }
    : queue ? { title: t("dashboard.nextReview", { count: queue }), page: "partners", action: t("dashboard.reviewNow") }
      : currentICP?.hypothesis && !currentRuns.length ? { title: t("dashboard.nextIcp"), page: "discover", action: t("dashboard.runDiscovery") }
        : !allRuns.length ? { title: t("dashboard.nextRun"), page: "discover", action: t("dashboard.runDiscovery") }
          : queryPerformance.some((row) => Number(row.retrieved) > 0 && Number(row.new_creator_yield) < .2) ? { title: t("dashboard.nextInspect"), page: "insights", action: t("dashboard.openRuns") }
            : { title: t("dashboard.nextHealthy"), page: "partners", action: t("dashboard.reviewNow") };

  const learnings = [];
  if (latestRun && previousRun && Number(latestRun.new_creator_yield) < Number(previousRun.new_creator_yield)) learnings.push({ text: t("dashboard.learningSaturation", { before: formatPercent(previousRun.new_creator_yield), after: formatPercent(latestRun.new_creator_yield) }), page: "insights" });
  const bestSource = sourcePerformance.find((row) => row.retrieved > 0 && row.yield != null);
  if (bestSource) learnings.push({ text: t("dashboard.learningYield", { channel: channelLabel(bestSource.channel), value: formatPercent(bestSource.yield) }), page: "insights" });
  if (zeroQueries.length) learnings.push({ text: t("dashboard.learningZero", { count: zeroQueries.length }), page: "insights" });
  if (topRejections.length) learnings.push({ text: t("dashboard.learningReject", { reason: topRejections[0][0] }), page: "partners" });

  const latestSuccessful = filteredRuns.find((run) => run.status === "COMPLETED" && !run.error_code);
  const connectedSources = channelRows().filter((row) => row.configured).length;
  const updateCandidates = [latestRun?.completed_at, currentICP?.selection?.selected_at, ...reviewed.map((creator) => creator.reviewed_at)].map(dashboardTimestamp).filter((value) => value != null);
  const lastUpdated = updateCandidates.length ? new Date(Math.max(...updateCandidates)).toISOString() : null;
  const isDemo = allRuns.length > 0 && allRuns.every((run) => String(run.discovery_mode || "").includes("controlled"));
  return {
    allRuns, filteredRuns, filteredCreators, currentICP, latestRun, previousRun, reviewed, approved, rejected, needsReviewDecision,
    queue, highPriority, rawResults, duplicateCount, duplicateRate, finalDecisions, approvalRate, latestNew, newDelta,
    stages, biggestDrop, dropReason, sourcePerformance, queryPerformance, reviewedToday, averageReviewMinutes, topRejections,
    failedQueries, failedRuns, zeroQueries, runTrend, attention: attention.slice(0, 3), nextAction, learnings: learnings.slice(0, 3),
    currentRuns, connectedSources, latestSuccessful, lastUpdated, isDemo,
  };
}

function renderDashboardEmpty(model) {
  const hasICP = Boolean(model.currentICP?.hypothesis);
  $('#dashboard-empty').innerHTML = `<div class="empty-command-icon">◎</div><p class="eyebrow">${t("dashboard.eyebrow")}</p><h2>${t("dashboard.emptyTitle")}</h2><p>${t("dashboard.emptyText")}</p><ol><li>${t("dashboard.emptyStep1")}</li><li>${t("dashboard.emptyStep2")}</li><li>${t("dashboard.emptyStep3")}</li><li>${t("dashboard.emptyStep4")}</li></ol><div><button class="button primary" type="button" data-go="${hasICP ? "discover" : "icp"}">${hasICP ? t("dashboard.runDiscovery") : t("dashboard.startIcp")} →</button><button class="button secondary" type="button" data-go="discover">${t("dashboard.knownIcp")}</button></div>`;
}

function renderOverview() {
  const data = state.bootstrap;
  if (!data) return;
  syncDashboardFilters();
  const model = buildDashboardModel(data);
  const current = model.currentICP?.hypothesis;
  const hasData = model.allRuns.length > 0 || (data.creators || []).length > 0;
  $('#dashboard-data-mode').className = `data-mode-badge ${model.isDemo ? "sample" : "workspace"}`;
  $('#dashboard-data-mode').textContent = model.isDemo ? t("dashboard.sample") : t("dashboard.workspace");
  const statusHasIssues = model.failedQueries.length > 0 || model.failedRuns.length > 0;
  const currentStatus = model.currentICP?.selection?.status || current?.status || t("icp.testing");
  $('#command-context').innerHTML = `<div class="command-context-grid"><div><span>${t("dashboard.currentIcp")}</span><strong>${escapeHtml(current?.name || t("dashboard.noIcp"))}</strong><small>${current ? `${escapeHtml(t("icp.version", { version: current.version }))} · ${escapeHtml(currentStatus)}` : t("dashboard.hypothesisNote")}</small></div><div><span>${t("dashboard.latestRun")}</span><strong>${model.latestRun ? escapeHtml(t("insights.historyItem", { index: model.allRuns.length })) : t("dashboard.noRun")}</strong><small>${model.latestRun ? escapeHtml(model.latestRun.status || "COMPLETED") : t("dashboard.noComparison")}</small></div><div><span>${t("dashboard.systemStatus")}</span><strong class="${statusHasIssues ? "attention" : "healthy"}">${statusHasIssues ? t("dashboard.attentionStatus") : t("dashboard.operational")}</strong><small>${model.failedQueries.length ? t("dashboard.failedQueries", { count: model.failedQueries.length }) : t("workspace.guardrail")}</small></div><div><span>${t("dashboard.lastUpdated")}</span><strong>${escapeHtml(relativeTime(model.lastUpdated))}</strong><small>${escapeHtml(formatDate(model.lastUpdated))}</small></div></div><div class="command-actions"><button class="button primary" type="button" data-go="${model.queue ? "partners" : "discover"}">${model.queue ? t("dashboard.reviewNow") : t("dashboard.runDiscovery")} →</button><button class="button mini" type="button" data-go="icp">${t("dashboard.viewIcp")}</button></div>`;
  $('#dashboard-empty').hidden = hasData;
  $('#dashboard-content').hidden = !hasData;
  if (!hasData) { renderDashboardEmpty(model); return; }

  const metrics = [
    { value: formatNumber(model.filteredCreators.length), label: t("dashboard.discovered"), note: t("dashboard.discoveredNote"), tone: "blue" },
    { value: formatNumber(model.highPriority), label: t("dashboard.highPriority"), note: t("dashboard.highPriorityNote"), tone: "pink" },
    { value: formatNumber(model.queue), label: t("dashboard.reviewQueue"), note: t("dashboard.reviewQueueNote"), tone: "purple" },
    { value: formatNumber(model.approved.length), label: t("dashboard.approved"), note: t("dashboard.approvedNote"), tone: "green" },
    { value: model.approvalRate == null ? t("dashboard.metricUnavailable") : formatPercent(model.approvalRate), label: t("dashboard.approvalRate"), note: model.approvalRate == null ? t("dashboard.insufficientReviews") : t("dashboard.approvalRateNote"), tone: model.approvalRate == null ? "amber" : "green" },
    { value: formatNumber(model.latestNew), label: t("dashboard.newLatest"), note: t("dashboard.newLatestNote"), tone: "blue", delta: model.newDelta },
  ];
  $('#command-kpis').innerHTML = metrics.map(dashboardMetricCard).join("");

  const maxStage = Math.max(1, ...model.stages.map((stage) => stage.count));
  $('#dashboard-funnel').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.pipelineKicker")}</p><h2>${t("dashboard.funnelTitle")}</h2></div></div><div class="honest-funnel">${model.stages.map((stage, index) => `<div class="funnel-stage stage-${stage.key}"><div class="funnel-label"><span>${escapeHtml(stage.label)}</span><strong>${formatNumber(stage.count)}</strong></div><div class="funnel-track"><i style="width:${Math.max(stage.count ? 5 : 0, stage.count / maxStage * 100)}%"></i></div>${index ? `<small>${stage.conversion == null ? t("dashboard.noStageData") : t("dashboard.ofPrevious", { value: formatPercent(stage.conversion) })}</small>` : ""}</div>`).join("")}</div><div class="dropoff-callout"><span>↓</span><div><small>${t("dashboard.biggestDrop")}</small><strong>${model.biggestDrop?.count ? `${escapeHtml(model.biggestDrop.from.label)} → ${escapeHtml(model.biggestDrop.to.label)} · ${formatNumber(model.biggestDrop.count)}` : t("dashboard.noDrop")}</strong><p>${escapeHtml(model.dropReason)}</p></div></div>`;

  $('#dashboard-attention').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.attentionTitle")}</p><h2>${t("dashboard.attentionTitle")}</h2></div><span class="attention-count">${model.attention.length}</span></div><div class="attention-list">${model.attention.length ? model.attention.map((item) => `<article><strong>${escapeHtml(item.title)}</strong><span>${t("dashboard.whyMatters")}</span><p>${escapeHtml(item.why)}</p><button class="button mini" type="button" data-go="${item.page}">${escapeHtml(item.action)} →</button></article>`).join("") : `<div class="quiet-state"><span>✓</span><p>${t("dashboard.noAttention")}</p></div>`}</div>`;

  $('#dashboard-current-icp').innerHTML = current
    ? `<div class="icp-command-heading"><div><p class="section-kicker">${t("dashboard.currentIcpKicker")}</p><h2>${escapeHtml(current.name)}</h2><span>${escapeHtml(t("icp.version", { version: current.version }))} · ${escapeHtml(currentStatus)}</span></div><p>${t("dashboard.hypothesisNote")}</p></div><div class="icp-command-grid"><div><span>${t("dashboard.who")}</span><p>${escapeHtml(current.who)}</p></div><div><span>${t("dashboard.corePain")}</span><p>${escapeHtml(current.core_pain)}</p></div><div><span>${t("dashboard.keySignals")}</span><div class="campaign-summary-chips">${(current.intent_signals || []).slice(0, 4).map((item) => `<i>${escapeHtml(item)}</i>`).join("")}</div></div><div><span>${t("dashboard.testPriority")}</span><p>${escapeHtml(current.test_priority_reason)}</p></div><div class="icp-run-proof"><span>${t("dashboard.discoveryRuns")}</span><strong>${formatNumber(model.currentRuns.length)}</strong><small>${model.currentRuns.length ? formatDate(model.currentRuns[0].completed_at) : t("dashboard.noLinkedRuns")}</small></div></div><div class="icp-command-actions"><button class="button mini" type="button" data-go="icp">${t("dashboard.viewIcp")}</button><button class="button primary" type="button" data-go="discover">${t("dashboard.runDiscovery")} →</button></div>`
    : `<div class="quiet-state icp-quiet"><span>◎</span><div><h2>${t("icp.noCurrent")}</h2><p>${t("icp.noCurrentText")}</p><button class="button mini" type="button" data-go="icp">${t("dashboard.startIcp")} →</button></div></div>`;

  $('#dashboard-source-performance').innerHTML = `<div class="table-panel-heading"><div><p class="section-kicker">${t("dashboard.sourcePerformance")}</p><h3>${t("dashboard.sourcePerformance")}</h3></div><span>${t("dashboard.qualityNote")}</span></div>${model.sourcePerformance.length ? `<div class="command-table-scroll"><table class="command-table"><thead><tr><th>${t("dashboard.channel")}</th><th>${t("dashboard.raw")}</th><th>${t("dashboard.new")}</th><th>${t("dashboard.freshYield")}</th><th>${t("dashboard.highPriorityShort")}</th><th>${t("dashboard.finalDecisions")}</th><th>${t("dashboard.approvalRate")}</th><th>${t("dashboard.errors")}</th></tr></thead><tbody>${model.sourcePerformance.map((row) => `<tr><td><span class="table-channel">${channelIcon(row.channel)}<b>${escapeHtml(channelLabel(row.channel))}</b></span></td><td>${formatNumber(row.retrieved)}</td><td>${formatNumber(row.fresh)}</td><td><span class="yield-cell ${row.yield != null && row.yield < .2 ? "low" : ""}"><i style="width:${(row.yield || 0) * 100}%"></i><b>${row.yield == null ? "—" : formatPercent(row.yield)}</b></span></td><td>${formatNumber(row.highPriority)}</td><td>${formatNumber(row.finalDecisions)}</td><td>${row.approvalRate == null ? `<span class="unavailable-cell">—</span>` : formatPercent(row.approvalRate)}</td><td>${formatNumber(row.errors)}</td></tr>`).join("")}</tbody></table></div>` : `<div class="table-empty">${t("dashboard.noSourceEvidence")}</div>`}`;

  $('#dashboard-query-performance').innerHTML = `<div class="table-panel-heading"><div><p class="section-kicker">${t("dashboard.queryPerformance")}</p><h3>${t("dashboard.queryPerformance")}</h3></div><button class="button mini" type="button" data-go="insights">${t("dashboard.evidence")} →</button></div>${model.queryPerformance.length ? `<div class="command-table-scroll"><table class="command-table query-table"><thead><tr><th>${t("dashboard.query")}</th><th>${t("dashboard.angle")}</th><th>${t("dashboard.raw")}</th><th>${t("dashboard.new")}</th><th>${t("dashboard.freshYield")}</th><th>${t("dashboard.highPriorityShort")}</th><th>${t("dashboard.approvalRate")}</th></tr></thead><tbody>${model.queryPerformance.map((row) => `<tr><td><div class="query-cell">${channelIcon(row.platform)}<span><b>${escapeHtml(row.query_text)}</b><small>${escapeHtml(channelLabel(row.platform))}</small></span></div></td><td>${escapeHtml(t(`angle.${row.search_angle}`) === `angle.${row.search_angle}` ? humanize(row.search_angle) : t(`angle.${row.search_angle}`))}</td><td>${formatNumber(row.retrieved)}</td><td>${formatNumber(row.new_creators)}</td><td>${row.new_creator_yield == null ? "—" : formatPercent(row.new_creator_yield)}</td><td>${formatNumber(row.highPriority)}</td><td>${row.approvalRate == null ? `<span class="unavailable-cell">—</span>` : formatPercent(row.approvalRate)}</td></tr>`).join("")}</tbody></table></div>` : `<div class="table-empty">${t("dashboard.noSourceEvidence")}</div>`}`;

  $('#dashboard-human-review').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.humanKicker")}</p><h2>${t("dashboard.humanTitle")}</h2></div><button class="button mini" type="button" data-go="partners">${t("dashboard.reviewNow")} →</button></div><div class="review-ops-grid"><div><span>${t("dashboard.pending")}</span><strong>${formatNumber(model.queue)}</strong></div><div><span>${t("dashboard.reviewedToday")}</span><strong>${formatNumber(model.reviewedToday)}</strong></div><div><span>${t("dashboard.approved")}</span><strong class="good">${formatNumber(model.approved.length)}</strong></div><div><span>${t("dashboard.rejected")}</span><strong class="danger">${formatNumber(model.rejected.length)}</strong></div><div><span>${t("dashboard.needsReview")}</span><strong class="purple">${formatNumber(model.needsReviewDecision.length)}</strong></div><div><span>${t("dashboard.timeToReview")}</span><strong>${model.averageReviewMinutes == null ? "—" : `${formatNumber(model.averageReviewMinutes)}m`}</strong><small>${t("dashboard.notDuration")}</small></div></div><div class="reason-list"><strong>${t("dashboard.topRejections")}</strong>${model.topRejections.length ? model.topRejections.slice(0, 3).map(([reason, count]) => `<span><i>${escapeHtml(reason)}</i><b>${formatNumber(count)}</b></span>`).join("") : `<p>${t("dashboard.noRejections")}</p>`}</div>`;

  $('#dashboard-system-health').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.healthKicker")}</p><h2>${t("dashboard.healthTitle")}</h2></div><button class="button mini" type="button" data-go="sources">${t("nav.sources")} →</button></div><dl class="health-list"><div><dt>${t("dashboard.sourcesConnected")}</dt><dd>${formatNumber(model.connectedSources)} / ${CHANNELS.length}</dd></div><div><dt>${t("dashboard.apiErrors")}</dt><dd class="${model.failedQueries.length ? "danger" : "good"}">${formatNumber(model.failedQueries.length)}</dd></div><div><dt>${t("dashboard.failedRuns")}</dt><dd class="${model.failedRuns.length ? "danger" : "good"}">${formatNumber(model.failedRuns.length)}</dd></div><div><dt>${t("dashboard.llmErrors")}</dt><dd class="muted">${t("dashboard.notTracked")}</dd></div><div><dt>${t("dashboard.dbErrors")}</dt><dd class="muted">${t("dashboard.notTracked")}</dd></div><div><dt>${t("dashboard.duplicateRate")}</dt><dd>${model.duplicateRate == null ? "—" : formatPercent(model.duplicateRate)}</dd></div><div><dt>${t("dashboard.lastSuccess")}</dt><dd>${model.latestSuccessful ? escapeHtml(relativeTime(model.latestSuccessful.completed_at)) : "—"}</dd></div></dl>${model.isDemo ? `<p class="demo-truth">${t("dashboard.demoNotice")}</p>` : ""}`;

  const trendWithEvidence = model.runTrend.filter((point) => point.approvalRate != null);
  $('#dashboard-trend').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.trendKicker")}</p><h2>${t("dashboard.trendTitle")}</h2></div></div>${trendWithEvidence.length ? `<div class="approval-trend">${trendWithEvidence.map((point, index) => `<div><span>${escapeHtml(t("insights.historyItem", { index: index + 1 }))}</span><div><i style="height:${Math.max(4, point.approvalRate * 100)}%"></i></div><strong>${formatPercent(point.approvalRate)}</strong></div>`).join("")}</div>${trendWithEvidence.length < 2 ? `<p class="trend-note">${t("dashboard.trendNeedMore")}</p>` : ""}` : `<div class="quiet-state"><span>↗</span><p>${t("dashboard.trendEmpty")}</p></div>`}`;

  $('#dashboard-recent-runs').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.runsKicker")}</p><h2>${t("dashboard.runsTitle")}</h2></div><button class="button mini" type="button" data-go="insights">${t("dashboard.openRuns")} →</button></div><div class="recent-run-list">${model.filteredRuns.slice(0, 5).map((run, index) => `<article><div><strong>${escapeHtml(t("insights.historyItem", { index: model.filteredRuns.length - index }))}</strong><span class="run-status ${run.status === "COMPLETED" ? "good" : "danger"}">${escapeHtml(run.status || "COMPLETED")}</span></div><dl><div><dt>${t("dashboard.started")}</dt><dd>${escapeHtml(formatDate(run.started_at))}</dd></div><div><dt>${t("dashboard.duration")}</dt><dd>${escapeHtml(durationLabel(run.started_at, run.completed_at))}</dd></div><div><dt>${t("dashboard.raw")}</dt><dd>${formatNumber(run.retrieved)}</dd></div><div><dt>${t("dashboard.new")}</dt><dd>${formatNumber(run.new_creators)}</dd></div></dl><details><summary>${t("insights.technical")}</summary><code>${escapeHtml(run.run_id)}</code></details></article>`).join("")}</div>`;

  $('#dashboard-learnings').innerHTML = `<div class="panel-heading"><div><p class="section-kicker">${t("dashboard.learningsKicker")}</p><h2>${t("dashboard.learningsTitle")}</h2></div></div><div class="learning-list">${model.learnings.length ? model.learnings.map((learning) => `<article><span>↗</span><p>${escapeHtml(learning.text)}</p><button type="button" data-go="${learning.page}">${t("dashboard.evidence")} →</button></article>`).join("") : `<div class="quiet-state"><span>◎</span><p>${t("dashboard.noLearnings")}</p></div>`}</div>`;
  $('#dashboard-next-action').innerHTML = `<p class="section-kicker">${t("dashboard.nextKicker")}</p><h2>${t("dashboard.nextTitle")}</h2><strong>${escapeHtml(model.nextAction.title)}</strong><p>${model.nextAction.page === "partners" ? t("dashboard.pendingWhy") : model.nextAction.page === "insights" ? t("dashboard.failedWhy") : t("dashboard.untestedWhy")}</p><button class="button primary" type="button" data-go="${model.nextAction.page}">${escapeHtml(model.nextAction.action)} →</button>`;
}

/* ---- partners ------------------------------------------------------------- */

function partnerSignalChips(partner) {
  return `<span class="signal-chip activity-${escapeHtml(partner.activity)}">${escapeHtml(signalLabel("activity", partner.activity))}</span><span class="signal-chip relevance-${escapeHtml(partner.relevance)}">${escapeHtml(signalLabel("relevance", partner.relevance))}</span><span class="signal-chip market-${escapeHtml(partner.market_fit)}">${escapeHtml(signalLabel("market", partner.market_fit))}</span>`;
}

function partnerTypeChip(type, confidence) {
  if (!type) return "";
  const demo = confidence === "demo";
  return `<span class="partner-type-chip${demo ? " is-demo" : ""}">${escapeHtml(partnerTypeLabel(type))}${demo ? `<i>${escapeHtml(t("partners.demoType"))}</i>` : ""}</span>`;
}

function isControlledDemoRecord(record) {
  const mode = String(record?.discovery_mode || "").toLowerCase();
  const connector = String(record?.source_connector || "").toLowerCase();
  return mode.includes("controlled") || connector.includes("controlled_fixture") || record?.partner_type_confidence === "demo";
}

function profileAction(record, detail = false) {
  if (isControlledDemoRecord(record)) {
    if (detail) return `<div class="demo-profile-note detail" role="note"><strong>${t("partner.demoRecord")}</strong><span>${t("partner.demoProfileNote")}</span></div>`;
    return `<span class="demo-profile-note" role="note" title="${escapeHtml(t("partner.demoProfileNote"))}">◇ ${t("partner.demoRecord")}</span>`;
  }
  if (!record?.profile_url) return `<span class="demo-profile-note unavailable" role="note">${t("partner.profileUnavailable")}</span>`;
  return `<a class="button mini profile-link" href="${escapeHtml(record.profile_url)}" target="_blank" rel="noreferrer">${t("partner.openProfile")} ↗</a>`;
}

function syncTypeFilterOptions() {
  const select = $('#type-filter');
  if (!select) return;
  const present = new Set((state.bootstrap?.creators || []).map((partner) => partner.partner_type).filter(Boolean));
  const current = select.value;
  select.innerHTML = `<option value="all">${escapeHtml(t("partners.allTypes"))}</option>` +
    PARTNER_TYPES.filter((type) => present.has(type)).map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(partnerTypeLabel(type))}</option>`).join("");
  select.value = [...select.options].some((option) => option.value === current) ? current : "all";
}

function renderPartners() {
  renderPartnerPool();
  syncTypeFilterOptions();
  const partners = state.bootstrap?.creators || [];
  const search = ($('#creator-search')?.value || "").trim().toLowerCase();
  const channel = $('#platform-filter')?.value || "all";
  const type = $('#type-filter')?.value || "all";
  const priority = $('#priority-filter')?.value || "all";
  const review = $('#review-filter')?.value || "all";
  const filtered = partners.filter((partner) => {
    const partnerChannel = partner.channel || partner.platform;
    const haystack = [partner.display_name, partner.handle, partner.bio_text, partner.market, partner.partner_type, ...(partner.likely_audience || [])].join(" ").toLowerCase();
    return (!search || haystack.includes(search))
      && (channel === "all" || partnerChannel === channel)
      && (type === "all" || partner.partner_type === type)
      && (priority === "all" || partner.priority === priority)
      && (review === "all" || partner.review_status === review);
  });
  $('#partner-count').textContent = state.language === "zh" ? `${filtered.length} ${t("general.partners")}` : `${filtered.length} ${filtered.length === 1 ? t("general.partner") : t("general.partners")}`;
  $('#creator-list').innerHTML = filtered.map((partner, index) => {
    const partnerChannel = partner.channel || partner.platform;
    const audienceValues = partner.likely_audience || [];
    const audienceFull = audienceValues.length ? audienceValues.join(" / ") : t("partner.audienceUnknown");
    const audience = audienceValues.length > 2 ? `${audienceValues.slice(0, 2).join(" / ")} +${audienceValues.length - 2}` : audienceFull;
    return `<article class="creator-card priority-${escapeHtml(partner.priority.replaceAll(" ", "-").toLowerCase())}" style="--stagger:${index}">
      <div class="creator-rank">${index + 1}</div>
      <div class="creator-main"><div class="creator-identity"><span class="platform-avatar">${channelIcon(partnerChannel)}</span><div><h2>${escapeHtml(partner.display_name || partner.handle)}</h2><p>${escapeHtml(partner.handle)} · ${escapeHtml(channelLabel(partnerChannel))}</p></div>${partnerTypeChip(partner.partner_type, partner.partner_type_confidence)}</div><div class="creator-facts"><span><b>${t("partner.market")}</b>${escapeHtml(partner.market || t("general.notObserved"))}</span><span><b>${t("partner.followers")}</b>${escapeHtml(formatNumber(partner.follower_count))}</span></div><div class="creator-signals">${partnerSignalChips(partner)}<span class="signal-chip audience" title="${escapeHtml(audienceFull)}"><b>${t("partner.audience")}:</b> ${escapeHtml(audience)}</span></div></div>
      <div class="creator-decision"><span class="priority-chip ${escapeHtml(partner.priority.replaceAll(" ", "-").toLowerCase())}">${priorityChipInner(partner.priority)}</span><span class="review-chip review-${escapeHtml(partner.review_status)}">${escapeHtml(reviewLabel(partner.review_status))}</span><div class="creator-actions"><button type="button" class="button mini view-creator" data-record-id="${escapeHtml(partner.record_id)}">${t("partner.viewEvidence")}</button><button type="button" class="button mini review-creator" data-record-id="${escapeHtml(partner.record_id)}">${t("partner.review")}</button>${profileAction(partner)}</div></div>
    </article>`;
  }).join("");
  $('#creator-empty').hidden = filtered.length !== 0;
}

/* ---- discovery insights --------------------------------------------------- */

function renderInsights() {
  const runs = [...(state.bootstrap?.runs || [])].reverse();
  const queryHistory = state.bootstrap?.query_history || [];
  $('#run-count').textContent = `${runs.length} ${runs.length === 1 ? t("insights.discovery") : t("insights.discoveries")}`;
  $('#history-empty').hidden = runs.length !== 0;
  $('#latest-discovery').innerHTML = ""; $('#query-insights').innerHTML = ""; $('#technical-runs').innerHTML = "";
  const historyDetails = $('#history-details');
  if (historyDetails) historyDetails.hidden = true;
  if (!runs.length) return;

  // LATEST DISCOVERY is the primary story. Run numbering is an internal detail
  // and never appears above the fold.
  const latest = runs.at(-1);
  const latestYield = Number(latest.new_creator_yield || 0);
  const saturated = Number(latest.retrieved) > 0 && latestYield === 0;
  $('#latest-discovery').innerHTML = `<section class="latest-discovery operational-surface">
    <div class="section-heading"><div><p class="section-kicker">${t("insights.latest")}</p><h2>${t("insights.latestTitle")}</h2><p>${t("insights.freshExplain")}</p></div><span class="run-mode-chip">${escapeHtml(formatDate(latest.completed_at))}</span></div>
    <div class="result-metrics">
      ${metricCard(formatNumber(latest.retrieved), t("insights.retrieved"), t("run.retrievedNote"), "blue")}
      ${metricCard(formatNumber(latest.duplicates), t("insights.duplicates"), t("run.duplicatesNote"), "amber")}
      ${metricCard(formatNumber(latest.new_creators), t("run.newPartners"), t("run.newNote"), "green")}
      ${metricCard(formatPercent(latestYield), t("run.yield"), t("run.yieldNote"), latestYield > .35 ? "green" : "amber")}
    </div>
    <div class="saturation-callout ${saturated ? "detected" : "healthy"}"><span aria-hidden="true">${saturated ? "!" : "✓"}</span><div><strong>${saturated ? t("insights.saturated") : t("insights.freshTitle")}</strong><p>${saturated ? t("insights.saturatedAdvice") : t("insights.freshAdvice")}</p></div></div>
  </section>`;

  const runOrder = new Map(runs.map((run, index) => [run.run_id, index + 1]));
  const rows = [...queryHistory].sort((a, b) => (runOrder.get(a.run_id) || 0) - (runOrder.get(b.run_id) || 0));
  const latestRows = rows.filter((row) => row.run_id === latest.run_id);
  $('#query-insights').innerHTML = `<section class="query-insights-section"><div class="section-heading"><div><p class="section-kicker">${t("insights.queryTitle")}</p><h2>${t("insights.queryTitle")}</h2><p>${t("insights.queryDesc")}</p></div></div><div class="query-insight-list">${latestRows.map((row) => queryInsightCard(row)).join("")}</div></section>`;

  // Historical comparison is real evidence, but it is secondary — it lives
  // behind a disclosure so the primary story stays one understandable discovery.
  if (historyDetails && runs.length >= 2) {
    historyDetails.hidden = false;
    $('#history-body').innerHTML = `<div class="yield-comparison">${runs.map((run, index) => `<div><span>${escapeHtml(t("insights.historyItem", { index: index + 1 }))}</span><div class="yield-track"><i style="width:${Math.round(Number(run.new_creator_yield || 0) * 100)}%"></i></div><strong>${formatPercent(run.new_creator_yield)}</strong><small>${run.retrieved} ${t("insights.retrieved")} · ${run.duplicates} ${t("insights.duplicates")} · ${run.new_creators} ${t("insights.new")}</small></div>`).join("")}</div>`;
  }

  $('#technical-runs').innerHTML = `<details class="technical-details operational-surface"><summary><span><strong>${t("insights.technical")}</strong><small>${t("insights.technicalNote")}</small></span><b aria-hidden="true">＋</b></summary><div class="technical-run-list">${runs.map((run, index) => `<article><div><strong>${escapeHtml(t("insights.historyItem", { index: index + 1 }))}</strong><span>${escapeHtml(run.status || "COMPLETED")}</span></div><dl><dt>Run ID</dt><dd>${escapeHtml(run.run_id)}</dd><dt>${t("insights.completed")}</dt><dd>${escapeHtml(formatDate(run.completed_at))}</dd><dt>${t("insights.queryExecutions")}</dt><dd>${rows.filter((row) => row.run_id === run.run_id).length}</dd></dl></article>`).join("")}</div></details>`;
}

function queryInsightCard(row) {
  const yieldValue = Number(row.new_creator_yield || 0);
  const noResults = Number(row.retrieved) === 0;
  const low = !noResults && yieldValue <= .2;
  const statusText = noResults ? t("insights.noResults") : low ? t("insights.lowYield") : t("insights.healthyYield");
  const executionStatus = String(row.execution_status || "");
  return `<article class="query-insight ${low || noResults ? "low-yield" : "fresh-yield"}"><div class="query-insight-identity"><span class="platform-inline">${channelIcon(row.platform, true)}</span><h3>${escapeHtml(row.query_text)}</h3><p>${t("insights.angle")}: ${escapeHtml(t(`angle.${row.search_angle}`))}</p></div><div class="query-counts"><span><b>${row.retrieved}</b>${t("insights.retrieved")}</span><span><b>${row.duplicates}</b>${t("insights.duplicates")}</span><span><b>${row.new_creators}</b>${t("insights.new")}</span></div><div class="query-yield"><div><i style="width:${Math.round(yieldValue * 100)}%"></i></div><strong>${formatPercent(yieldValue)}</strong><span class="yield-status">${escapeHtml(statusText)}</span><small>${escapeHtml(executionStatus ? t(`executionStatus.${executionStatus}`) : t("insights.success"))}</small></div></article>`;
}

/* ---- data sources --------------------------------------------------------- */

function renderDataSources() {
  const rows = channelRows();
  const pool = partnerPool();
  const counts = pool.channel_counts || {};
  const connected = rows.filter((row) => row.configured).length;
  const countEl = $('#source-count');
  if (countEl) countEl.textContent = t("sources.connectedCount", { count: connected });

  const grid = $('#source-grid');
  if (!grid) return;
  const controlled = `<article class="source-card is-connected"><header><span class="source-mark">${CHANNEL_SVG.controlled}</span><div><h3>${escapeHtml(t("channel.controlled"))}</h3><p>${escapeHtml(t("sources.controlledPurpose"))}</p></div></header><div class="source-status"><span class="status-dot"></span>${escapeHtml(t("sources.alwaysOn"))}</div></article>`;
  grid.innerHTML = controlled + rows.map((row) => {
    const stored = Number(counts[row.channel] || 0);
    return `<article class="source-card ${row.configured ? "is-connected" : "is-unconfigured"}">
      <header><span class="source-mark">${channelIcon(row.channel)}</span><div><h3>${escapeHtml(row.label || channelLabel(row.channel))}</h3><p>${escapeHtml(row.purpose || "")}</p></div></header>
      <div class="source-status"><span class="${row.configured ? "status-dot" : "status-dot off"}"></span>${escapeHtml(row.configured ? t("sources.connected") : t("sources.notConfigured"))}</div>
      <p class="source-records">${escapeHtml(t("sources.storedRecords", { count: stored }))}</p>
      ${row.credential_variable ? `<details class="source-configure"><summary>${escapeHtml(t("sources.configure"))}</summary><p>${escapeHtml(t("sources.configureBody"))}</p><code>${escapeHtml(row.credential_variable)}</code></details>` : ""}
    </article>`;
  }).join("");

  const technical = $('#source-technical-body');
  if (technical) {
    technical.innerHTML = `<div class="technical-run-list">${rows.map((row) => `<article><div><strong>${escapeHtml(row.label || channelLabel(row.channel))}</strong><span>${escapeHtml(row.configured ? t("sources.connected") : t("sources.notConfigured"))}</span></div><dl><dt>${t("sources.credential")}</dt><dd>${escapeHtml(row.credential_variable || "—")}</dd><dt>${t("sources.optional")}</dt><dd>${escapeHtml((row.environment_variables || []).join(", ") || "—")}</dd></dl></article>`).join("")}</div>`;
  }
}

/* ---- partner evidence: summary first, evidence on demand ------------------ */

function factItem(label, value) { return `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? t("general.notObserved"))}</strong></div>`; }

// Only reasons the backend already stored are shown. Nothing here invents one.
function priorityReasons(detail) {
  const supplied = detail.priority_summary?.reasons;
  if (Array.isArray(supplied) && supplied.length) return supplied;
  return detail.priority_decision?.reasons || [];
}

function keySignalCards(detail) {
  const supplied = detail.key_signals;
  const signals = detail.derived_signals || {};
  const fallbackOrder = [["activity", "activity"], ["relevance", "content_relevance"], ["audience", "audience_size"], ["market", "market"], ["actionability", "actionability"]];
  const cards = Array.isArray(supplied) && supplied.length
    ? supplied.map((item) => ({ key: item.signal, value: item.value, summary: item.summary, evidence: item.evidence || [] }))
    : fallbackOrder.filter(([, source]) => signals[source]).map(([key, source]) => ({ key, value: signals[source].value, summary: signals[source].reason, evidence: signals[source].evidence || [] }));
  if (!cards.length) return `<p class="empty-copy">${t("detail.noSignals")}</p>`;
  return cards.map((card) => `<article class="key-signal">
    <span class="key-signal-name">${escapeHtml(t(`signalField.${card.key}`))}</span>
    <strong class="key-signal-value">${escapeHtml(signalValueLabel(card.value))}</strong>
    ${card.evidence.length ? `<details class="evidence-toggle"><summary>${escapeHtml(t("detail.viewEvidence"))}</summary><p>${escapeHtml(card.summary || "")}</p>${card.evidence.map((item) => `<i>${escapeHtml(item)}</i>`).join("")}</details>` : `<details class="evidence-toggle"><summary>${escapeHtml(t("detail.viewEvidence"))}</summary><p>${escapeHtml(card.summary || t("detail.noEvidence"))}</p></details>`}
  </article>`).join("");
}

function renderPartnerDetail(detail) {
  const raw = detail.observed_facts || {};
  const decision = detail.priority_decision || {};
  const human = detail.human_decision;
  const channel = raw.platform || "web";
  const ai = detail.ai_audience_summary || detail.ai_audience_inference || {};
  const partnerType = detail.partner_type || {};
  const handle = raw.profile_url?.split("/").filter(Boolean).at(-1) || detail.record_id;
  const priority = decision.priority || "Needs Review";

  $('#dialog-identity').innerHTML = `<div class="dialog-creator-identity"><span class="platform-avatar">${channelIcon(channel)}</span><div><p class="section-kicker">${t("detail.title")}</p><h2>${escapeHtml(raw.display_name || handle)}</h2><span>${escapeHtml(channelLabel(channel))}${partnerType.partner_type ? ` · ${escapeHtml(partnerTypeLabel(partnerType.partner_type))}` : ""}</span></div><span class="priority-chip ${escapeHtml(String(priority).replaceAll(" ", "-").toLowerCase())}">${priorityChipInner(priority)}</span></div>`;

  const samples = raw.content_samples || [];
  const previewCount = Number.isInteger(detail.content_samples_preview) ? detail.content_samples_preview : Math.min(3, samples.length);
  const preview = samples.slice(0, previewCount);
  const remaining = samples.slice(previewCount);
  const audienceValues = ai.likely_audience || [];
  const aiEvidence = ai.evidence || [];
  const marketLabel = signalLabel("market", detail.derived_signals?.market?.value);

  $('#detail-content').innerHTML = `<div class="partner-evidence">

    <section class="partner-identity-strip">
      ${factItem(t("partner.channel"), channelLabel(channel))}
      ${factItem(t("partner.type"), partnerType.partner_type ? `${partnerTypeLabel(partnerType.partner_type)}${partnerType.confidence === "demo" ? ` · ${t("partners.demoType")}` : ""}` : t("general.unknown"))}
      ${factItem(t("detail.decision"), priorityText(priority))}
      ${factItem(t("partner.followers"), formatNumber(raw.follower_count))}
      ${factItem(t("partner.market"), marketLabel)}
    </section>

    <section class="why-priority">
      <p class="section-kicker">${t("detail.whyPriority")}</p>
      <h3>${escapeHtml(priorityText(priority).replace(" · ", " — "))}</h3>
      <ul class="why-reasons">${priorityReasons(detail).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("") || `<li>${escapeHtml(t("detail.noEvidence"))}</li>`}</ul>
    </section>

    <section class="key-signals">
      <p class="section-kicker">${t("detail.keySignals")}</p>
      <div class="key-signal-grid">${keySignalCards(detail)}</div>
    </section>

    <section class="ai-audience-block">
      <p class="section-kicker">${t("detail.aiAudienceTitle")}</p>
      <div class="ai-audience-summary">
        <div><span>${t("detail.likelyAudience")}</span><strong>${audienceValues.length ? escapeHtml(audienceValues.join(" · ")) : escapeHtml(t("detail.audienceUnclear"))}</strong></div>
        <div><span>${t("detail.confidence")}</span><strong class="confidence-${escapeHtml(ai.confidence || "unknown")}">${escapeHtml(ai.confidence ? humanize(ai.confidence) : t("detail.modelUnavailable"))}</strong></div>
      </div>
      <details class="evidence-toggle ai-evidence"><summary>${escapeHtml(t("detail.whyAi"))}</summary>${aiEvidence.length ? aiEvidence.map((item) => `<blockquote>${escapeHtml(item)}</blockquote>`).join("") : `<p>${escapeHtml(t("detail.noEvidence"))}</p>`}${ai.model ? `<p class="ai-provenance">${escapeHtml(ai.provider || "")} · ${escapeHtml(ai.model)}</p>` : ""}</details>
    </section>

    <section class="observed-content">
      <p class="section-kicker">${t("detail.observedContent")}</p>
      ${raw.bio_text ? `<blockquote class="partner-bio">${escapeHtml(raw.bio_text)}</blockquote>` : `<p class="empty-copy">${t("detail.bioEmpty")}</p>`}
      ${preview.length ? `<div class="sample-list">${preview.map(contentSample).join("")}</div>` : `<p class="empty-copy">${t("detail.samplesEmpty")}</p>`}
      ${remaining.length ? `<details class="evidence-toggle"><summary>${escapeHtml(t("detail.showMore"))} (${remaining.length})</summary><div class="sample-list">${remaining.map(contentSample).join("")}</div></details>` : ""}
      ${profileAction(raw, true)}
    </section>

    <section class="detail-section human detail-human">
      <header><div><p class="section-kicker">${t("detail.humanOwned")}</p><h3>${t("detail.human")}</h3><p>${t("detail.humanDesc")}</p></div></header>
      <form id="review-form">
        <div class="review-choice">
          <label><input type="radio" name="creator-decision" value="approve" ${human?.status === "approve" ? "checked" : ""}/><span>✓ ${t("review.approve")}</span></label>
          <label><input type="radio" name="creator-decision" value="needs_review" ${!human || human?.status === "needs_review" ? "checked" : ""}/><span>? ${t("review.needs_review")}</span></label>
          <label><input type="radio" name="creator-decision" value="reject" ${human?.status === "reject" ? "checked" : ""}/><span>× ${t("review.reject")}</span></label>
        </div>
        <label>${t("detail.reason")}<select id="review-reason"><option value="">${t("detail.reasonNone")}</option><option value="Strong evidence fit" ${human?.structured_reason === "Strong evidence fit" ? "selected" : ""}>${t("detail.reasonStrong")}</option><option value="Needs evidence follow-up" ${human?.structured_reason === "Needs evidence follow-up" ? "selected" : ""}>${t("detail.reasonFollowup")}</option><option value="Outside campaign fit" ${human?.structured_reason === "Outside campaign fit" ? "selected" : ""}>${t("detail.reasonOut")}</option></select></label>
        <label>${t("detail.comment")}<textarea id="review-comment" rows="3" placeholder="${escapeHtml(t("detail.commentPlaceholder"))}">${escapeHtml(human?.comment || "")}</textarea></label>
        ${human ? `<p class="saved-decision"><strong>${t("detail.lastDecision")}:</strong> ${escapeHtml(reviewLabel(human.status))} · ${escapeHtml(formatDate(human.reviewed_at))}</p>` : `<p class="saved-decision">${t("detail.noDecision")}</p>`}
        <button class="button primary" type="submit">${t("detail.save")}</button>
      </form>
    </section>

    <details class="technical-details full-evidence">
      <summary><span><strong>${t("detail.fullEvidence")}</strong><small>${t("detail.fullEvidenceNote")}</small></span><b aria-hidden="true">＋</b></summary>
      <div class="fact-grid">
        ${factItem(t("detail.platform"), channelLabel(channel))}
        ${factItem(t("detail.followers"), formatNumber(raw.follower_count))}
        ${factItem(t("detail.retrieved"), formatDate(raw.retrieved_at))}
        ${factItem(t("detail.mode"), humanize(raw.discovery_mode))}
        ${factItem(t("detail.query"), raw.query_text)}
        ${factItem(t("detail.angle"), raw.search_angle ? t(`angle.${raw.search_angle}`) : null)}
        ${factItem(t("detail.connector"), raw.source_connector)}
        ${factItem(t("detail.runId"), raw.run_id)}
      </div>
      <div class="evidence-mini-grid">${renderFullSignalCards(detail.derived_signals)}</div>
    </details>
  </div>`;
  $('#detail-loading').hidden = true; $('#detail-content').hidden = false;
}

function contentSample(sample) {
  return `<article><p>${escapeHtml(sample.text)}</p><span>${escapeHtml(sample.published_at ? formatDate(sample.published_at) : t("detail.dateUnknown"))}</span></article>`;
}

function renderFullSignalCards(signals) {
  if (!signals) return `<p class="empty-copy">${t("detail.noSignals")}</p>`;
  return ["activity", "content_relevance", "audience_size", "market", "actionability", "record_quality"].filter((key) => signals[key]).map((key) => `<article class="evidence-mini-card"><span>${escapeHtml(t(`signalField.${key}`))}</span><strong>${escapeHtml(signalValueLabel(signals[key].value))}</strong><p>${escapeHtml(signals[key].reason)}</p>${(signals[key].evidence || []).map((item) => `<i>${escapeHtml(item)}</i>`).join("")}</article>`).join("");
}

async function openPartner(recordId, section = "evidence") {
  state.activeCreatorId = recordId; state.activeCreatorDetail = null;
  $('#detail-content').hidden = true; $('#detail-loading').hidden = false;
  $('#creator-dialog').showModal();
  try {
    const detail = await api(`/api/creators/${encodeURIComponent(recordId)}`);
    state.activeCreatorDetail = detail;
    renderPartnerDetail(detail);
    if (section === "human") requestAnimationFrame(() => $('.detail-human')?.scrollIntoView({ behavior: "smooth", block: "start" }));
  } catch (error) { $('#detail-loading').textContent = localizedError(error); }
}

async function submitReview(event) {
  event.preventDefault();
  const status = $('input[name="creator-decision"]:checked')?.value;
  try {
    await api(`/api/creators/${encodeURIComponent(state.activeCreatorId)}/review`, { method: "POST", body: JSON.stringify({ status, structured_reason: $('#review-reason').value || null, comment: $('#review-comment').value || null }) });
    showToast(t("detail.saved")); await refreshWorkspace();
    state.activeCreatorDetail = await api(`/api/creators/${encodeURIComponent(state.activeCreatorId)}`);
    renderPartnerDetail(state.activeCreatorDetail);
  } catch (error) { showToast(localizedError(error)); }
}

function renderBootstrap() {
  if (!state.bootstrap) return;
  renderChannelReadiness(); renderOverview(); renderICP(); renderPartners(); renderInsights(); renderDataSources();
}

async function refreshWorkspace() {
  try { state.bootstrap = await api("/api/bootstrap"); renderBootstrap(); }
  catch (error) { showToast(localizedError(error)); }
}

function bindEvents() {
  document.addEventListener("click", (event) => {
    const nav = event.target.closest("[data-page]"); if (nav) setPage(nav.dataset.page);
    const go = event.target.closest("[data-go]"); if (go) setPage(go.dataset.go);
    const language = event.target.closest("[data-lang]"); if (language) setLanguage(language.dataset.lang);
    const theme = event.target.closest("[data-theme-choice]"); if (theme) setTheme(theme.dataset.themeChoice);
    const decision = event.target.closest(".query-actions [data-decision]"); if (decision) chooseDecision(decision.closest('.query-card').dataset.queryId, decision.dataset.decision);
    const partner = event.target.closest(".view-creator, .review-creator"); if (partner) openPartner(partner.dataset.recordId, partner.classList.contains("review-creator") ? "human" : "evidence");
    const startICP = event.target.closest("#start-icp"); if (startICP) { $('#business-context-panel').hidden = false; $('#icp-entry').hidden = true; $('#business-context-panel').scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }); }
    const cancelICP = event.target.closest("#cancel-icp"); if (cancelICP) { $('#business-context-panel').hidden = true; $('#icp-entry').hidden = false; }
    const regenerateICP = event.target.closest("#regenerate-icp"); if (regenerateICP) $('#business-context-form').requestSubmit();
    const editICP = event.target.closest("[data-icp-edit]"); if (editICP) { state.editingIcpId = editICP.dataset.icpEdit; renderICPHypotheses(); }
    const cancelEdit = event.target.closest("[data-icp-cancel-edit]"); if (cancelEdit) { state.editingIcpId = null; renderICPHypotheses(); }
    const select = event.target.closest("[data-icp-select]"); if (select) selectICP(select.dataset.icpSelect, select.dataset.version);
    if (event.target.closest("[data-icp-save-later]")) showToast(t("icp.saved"));
  });
  $('#generate-plan').addEventListener("click", generatePlan);
  $('#business-context-form').addEventListener("submit", generateICP);
  $('#criteria-form').addEventListener("submit", confirmCriteria);
  $('#hypothesis-grid').addEventListener("submit", (event) => { if (event.target.matches(".hypothesis-edit-form")) { event.preventDefault(); saveICPEdit(event.target); } });
  $('#approve-all').addEventListener("click", () => { (state.workflow?.draft_search_plan?.queries || []).forEach((query) => { if (!state.queryDecisions.has(query.query_id)) state.queryDecisions.set(query.query_id, "approved"); }); renderQueryGroups(); });
  $('#run-discovery').addEventListener("click", runDiscovery);
  $$('input[name="discovery-mode"]').forEach((input) => input.addEventListener("change", () => { $$('.mode-card').forEach((card) => card.classList.toggle("selected", $('input', card).checked)); const live = input.value === "live" && input.checked; $('#live-confirmation').hidden = !live; if (!live) $('#confirm-live').checked = false; updateReviewState(); }));
  $('#confirm-live').addEventListener("change", updateReviewState);
  ['creator-search', 'platform-filter', 'type-filter', 'priority-filter', 'review-filter'].forEach((id) => $(`#${id}`)?.addEventListener(id === 'creator-search' ? 'input' : 'change', renderPartners));
  ['date', 'icp', 'source', 'run'].forEach((key) => $(`#dashboard-${key}-filter`)?.addEventListener('change', (event) => { state.dashboardFilters[key] = event.target.value; renderOverview(); }));
  $('#dashboard-filter-reset')?.addEventListener('click', () => { state.dashboardFilters = { date: '30', icp: 'all', source: 'all', run: 'all' }; renderOverview(); });
  $('#close-dialog').addEventListener("click", () => $('#creator-dialog').close());
  $('#creator-dialog').addEventListener("click", (event) => { if (event.target === $('#creator-dialog')) $('#creator-dialog').close(); });
  $('#detail-content').addEventListener("submit", (event) => { if (event.target.id === "review-form") submitReview(event); });
  window.addEventListener("hashchange", () => {
    const route = routeFromHash(location.hash);
    setPage(route.page, false);
    // Leaving a partner route must also leave its evidence sheet.
    if (route.recordId) openPartner(route.recordId);
    else if ($('#creator-dialog').open) $('#creator-dialog').close();
  });
}

async function init() {
  state.language = safeStored(STORAGE_KEYS.language, "en");
  state.theme = safeStored(STORAGE_KEYS.theme, "light");
  setTheme(state.theme, false); setLanguage(state.language, false);
  bindEvents();
  const route = routeFromHash(location.hash);
  setPage(route.page || "overview", false);
  setPipelineState("idle");
  await refreshWorkspace();
  if (route.recordId) openPartner(route.recordId);
}

init();
