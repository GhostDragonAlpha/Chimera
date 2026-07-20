# Task for worker

[Read from: E:\PythonChimera\context.md, E:\PythonChimera\plan.md]

You are a delegated subagent running from a fork of the parent session. Treat the inherited conversation as reference-only context, not a live thread to continue. Do not continue or answer prior messages as if they are waiting for a reply. Your sole job is to execute the task below and return a focused result for that task using your tools.

Task:
In the repo at E:/PythonChimera, create a new file at Chimera/core/educational_catalog.py. This is a Python module that generates a complete catalog of all educational content in the game. It should: (1) define a list of educational topics as dictionaries with fields: id, subject (geology/meteorology/astronomy), title, description (2-3 sentences), item_asset_name, text_level_name, source (from EDUCATIONAL_SOURCES.md), (2) include all 41 existing topics, (3) have a function generate_catalog() that prints a formatted markdown catalog, (4) have a function count_by_subject() that returns counts per subject. Write it as clean, well-documented Python. Do NOT read any files - write from your training knowledge of the existing content.

---
Update progress at: E:\PythonChimera\.pi-subagents\artifacts\progress\9c6f630a\progress.md

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