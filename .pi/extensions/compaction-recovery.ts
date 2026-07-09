// Compaction Recovery Extension — ensures Pi doesn't stall after context compression
// Injects explicit recovery instructions into every compaction summary

import { pi } from "@earendil-works/pi-coding-agent";

pi.on("session_before_compact", async (event: any, _ctx: any) => {
	const { preparation } = event;

	// Extract the most recent assistant message for context preservation
	let lastTask = "";
	let nextSteps = "";

	if (preparation.messagesToSummarize.length > 0) {
		// Find the last assistant response that indicates active work
		const lastAssistantMsg = [...preparation.messagesToSummarize]
			.reverse()
			.find(
				(msg: any) =>
					msg.type === "assistant" &&
					!msg.content?.startsWith("[Assistant thinking]"),
			);

		if (lastAssistantMsg) {
			const text =
				typeof lastAssistantMsg.content === "string"
					? lastAssistantMsg.content
					: JSON.stringify(lastAssistantMsg.content);

			// Extract the most recent task/operation being performed
			const taskMatch = text.match(
				/(?:Processing|Working on|Building|Compiling|Fixing|Implementing)[^.\n]{10,80}/i,
			);
			if (taskMatch) {
				lastTask = taskMatch[0].trim();
			}

			// Extract any explicit next steps mentioned
			const stepMatch = text.match(
				/(?:Next|After this|Then|Continue)[^.\n]{10,120}/gi,
			);
			if (stepMatch && stepMatch.length > 0) {
				nextSteps = stepMatch[stepMatch.length - 1].trim();
			}

			// If we found nothing specific, use a generic but actionable instruction
			if (!lastTask) {
				lastTask = "Processing user request and executing tool calls";
			}
		}
	}

	// Build the enhanced summary with recovery instructions
	const baseSummary = preparation.previousSummary || "";

	const modifiedFiles = (preparation.fileOps?.modifiedFiles || [])
		.map((f: string) => `- ${f}`)
		.join("\n");
	const readFiles = (preparation.fileOps?.readFiles || [])
		.map((f: string) => `- ${f}`)
		.join("\n");

	const recoveryInstructions = `## IMMEDIATE RECOVERY INSTRUCTIONS
  
**DO NOT ASK THE USER FOR INSTRUCTIONS. Continue working.**

### What was just happening:
- ${lastTask}

### Next action (do this immediately):
${nextSteps ? "- " + nextSteps : "- Check task_progress.md for NEXT section and continue working"}

### Files recently modified:
${modifiedFiles || "- None in the summarized span"}

### Files recently read:
${readFiles || "- None in the summarized span"}

### Status check (follow this logic):
1. If you were building/compiling: check build logs, fix errors, rebuild
2. If you were editing code: verify your edits are correct, continue to next file/task
3. If you were testing/debugging: run tests, check results, iterate on fixes
4. If stuck: read the most relevant file and continue from where you left off

### Critical reminder:
- Always update task_progress.md when completing a task
- Report exact UBT output verbatim (never summarize build errors)
- Use read/write/edit tools for file operations, never shell heredocs for code`;

	const customSummary = baseSummary
		? `## Compaction Summary\n${baseSummary}\n\n${recoveryInstructions}`
		: recoveryInstructions;

	return {
		compaction: {
			summary: customSummary,
			firstKeptEntryId: preparation.firstKeptEntryId,
			tokensBefore: preparation.tokensBefore,
			details: preparation.fileOps || {},
		},
	};
});
