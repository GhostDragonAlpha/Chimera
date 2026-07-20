# Task for worker

[Read from: E:\PythonChimera\context.md, E:\PythonChimera\plan.md]

You are a delegated subagent running from a fork of the parent session. Treat the inherited conversation as reference-only context, not a live thread to continue. Do not continue or answer prior messages as if they are waiting for a reply. Your sole job is to execute the task below and return a focused result for that task using your tools.

Task:
In the repo at E:/PythonChimera, create a new file at docs/EDUCATIONAL_SOURCES.md. This is a bibliography/citation document that proves our educational content is accurate. For each of the 41 educational item assets in Content/Items/, research and cite real science sources. Write citations for: (1) Geology items (Basalt, Granite, Obsidian, etc.) — cite real geology textbooks or USGS sources, (2) Meteorology items (Cirrus, Cumulus, Storm, etc.) — cite NOAA or AMS sources, (3) Astronomy items (Stars, Saturn, Titan, etc.) — cite NASA or IAU sources. Format as a proper academic bibliography. Where you don't know the exact source, note it as 'VERIFY: [topic]' for a human to confirm. This document proves to Steam reviewers and educators that our content is based on real science. Do NOT read any files - just create the bibliography from your training knowledge.

---
Update progress at: E:\PythonChimera\.pi-subagents\artifacts\progress\e5aa2da8\progress.md

## Acceptance Contract
Acceptance level: checked
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Implement the requested change without widening scope

Required evidence: changed-files, tests-added, commands-run, residual-risks, no-staged-files

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
`criteriaSatisfied[].status` must be exactly one of: satisfied, not-satisfied, not-applicable.
`commandsRun[].result` must be exactly one of: passed, failed, not-run.
`manualNotes` and `notes` are optional strings; an empty string means no note and does not satisfy `manual-notes` evidence.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```