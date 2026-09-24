# MATERIAL-VOLUME CAMPAIGN — RECOVERY RECORD (append-only)

## CHECKPOINT T0 (2026-09-24) — campaign opened

**Setup verified:** worktree E:/ChimeraWork/mvc-20260924 on branch material-volume-campaign-20260924 (base = exporter tip 3db8bc4e, clean checkout 5118 files); frozen proof rev 1af0bbde identified; 27 material-volume files in tools/; docs incl. 59/66 verification receipt + contract v0.9 (5 Astra decisions open); prior export worktree already cleaned by its own lane (branch carries everything).
**Dispatched at T0:** M01–M10 (ten background agents, exclusive dirs under material_volume_campaign/agents/).
**Parallel context:** the forearm anatomy campaign's wave-4 agents (O1/O2/R1) run concurrently in E:/PythonChimera (separate campaign, separate branch) — integrate their notifications as they land; no resource conflict (all CPU-light).
**Next:** collect M-receipts as they land -> verify -> integrate in small batches -> refill from backlog B1-B10 -> checkpoint each pass. Worktree audit each integration pass.

## CHECKPOINT T1 — M09 integrated (first mv-campaign receipt)

**Verified:** M09 suite re-run by coordinator (11/11 PASS, 3.6s); read-only proof reproduced (415 files, 0 changed); integrity clean. Implementation on the reader's public API (read_json_file, summarize_export_report, canonical_json); exit codes {0,2,4}; readiness false in all outputs; exit-4 alarm never fired.
**Finding banked (U7):** reader correct on blocked/refused; summary drops CON-4/6/7 diagnostics; CLI passes through. Coordinator disposition: candidate reader-improvement (a tools/ change) goes to the defect/change queue with M09's receipts — not executed yet (exclusive-ownership rule).
**Refill:** B2a dispatched (independent non-author review of the M09 CLI).
