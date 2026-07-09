/**
 * Compaction Recovery Extension
 *
 * Generates a REAL structured summary of the compacted messages AND appends
 * autonomous-recovery instructions, so Pi preserves context AND never stalls
 * asking "what next?" after context compression.
 *
 * FIXED 2026-07-09 — the previous version had two defects:
 *   1. `import { pi } from "@earendil-works/pi-coding-agent"` — the package exports
 *      NO `pi` value, so `pi` was undefined and `pi.on(...)` threw
 *      `TypeError: Cannot read properties of undefined (reading 'on')` at load,
 *      crashing extension loading on every startup. Extensions must use the factory
 *      form: `export default function (pi: ExtensionAPI) { ... }`.
 *   2. It returned `compaction.summary` built only from `previousSummary` + boilerplate,
 *      which tells Pi to SKIP real summarization — discarding the entire conversation
 *      being compacted (total context loss on the first compaction).
 *
 * This rewrite mirrors the official examples/extensions/custom-compaction.ts:
 * summarize the real messages with the current model, append the recovery block,
 * and fall back to Pi's default compaction on ANY error (never worse than default).
 */

import { complete } from "@earendil-works/pi-ai/compat";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { convertToLlm, serializeConversation } from "@earendil-works/pi-coding-agent";

const RECOVERY_INSTRUCTIONS = `## IMMEDIATE RECOVERY INSTRUCTIONS

**DO NOT ASK THE USER FOR INSTRUCTIONS. Continue working autonomously.**

### Status check (follow this logic):
1. If you were building/compiling: check build logs, fix errors, rebuild
2. If you were editing code: verify your edits are correct, continue to the next file/task
3. If you were testing/debugging: run tests, check results, iterate on fixes
4. If unsure where you left off: read task_progress.md (NEXT section) and continue from there

### Chimera reminders:
- Update task_progress.md when completing a task
- Report exact UBT output verbatim (never summarize build errors)
- Use read/write/edit tools for file operations, never shell heredocs for code`;

export default function (pi: ExtensionAPI) {
	pi.on("session_before_compact", async (event, ctx) => {
		const { preparation, signal } = event;
		const {
			messagesToSummarize,
			turnPrefixMessages,
			tokensBefore,
			firstKeptEntryId,
			previousSummary,
			fileOps,
		} = preparation;

		// Need a model to summarize with. If none is active, let Pi's default
		// compaction run (returning undefined = "I didn't handle this").
		const model = ctx.model;
		if (!model) return;

		// Resolve API key/headers for the active model (LM Studio, in this setup).
		const auth = await ctx.modelRegistry.getApiKeyAndHeaders(model);
		if (!auth.ok) return;

		// Summarize the full span that is about to be dropped.
		const allMessages = [...messagesToSummarize, ...turnPrefixMessages];
		if (allMessages.length === 0) return;

		const conversationText = serializeConversation(convertToLlm(allMessages));
		const previousContext = previousSummary
			? `\n\nPrevious summary (fold this in for iterative context):\n${previousSummary}`
			: "";

		const promptText = `You are summarizing a coding session so work can continue after older messages are dropped from context.${previousContext}

Produce a thorough but concise structured markdown summary with these sections:

## Goal
## Constraints & Preferences
## Progress
### Done
### In Progress
### Blocked
## Key Decisions
## Next Steps
## Critical Context

This summary REPLACES the conversation below, so include every detail needed to continue the work (file paths, decisions, current state, exact next action).

<conversation>
${conversationText}
</conversation>`;

		try {
			const response = await complete(
				model,
				{
					messages: [
						{
							role: "user" as const,
							content: [{ type: "text" as const, text: promptText }],
							timestamp: Date.now(),
						},
					],
				},
				{
					apiKey: auth.apiKey,
					headers: auth.headers,
					env: auth.env,
					maxTokens: 8192,
					signal,
				},
			);

			const realSummary = response.content
				.filter((c: any): c is { type: "text"; text: string } => c.type === "text")
				.map((c: any) => c.text)
				.join("\n")
				.trim();

			// Empty (or aborted mid-stream) → fall back to default compaction.
			if (!realSummary) return;

			// Real context first, then the autonomous-recovery nudge.
			const summary = `${realSummary}\n\n---\n\n${RECOVERY_INSTRUCTIONS}`;

			return {
				compaction: {
					summary,
					firstKeptEntryId,
					tokensBefore,
					details: fileOps || {},
				},
			};
		} catch {
			// Any failure (network, endpoint down, bad response) → let Pi's default
			// compaction handle it. This path is never worse than doing nothing.
			return;
		}
	});
}
