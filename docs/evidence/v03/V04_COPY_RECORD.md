# V04 — publication copy record (2026-09-07)

Committed by the BP-V04 assignment (GLM). This record is APPEND-ONLY evidence;
it is not part of the V03 packet.

## Sources (all UNTRACKED in E:\PythonChimera, verified 2026-09-07)

| Source | Destination (this repo) |
|---|---|
| `E:\PythonChimera\tools\dyad_timed_capture.py` (25,336 B) | `tools/dyad_timed_capture.py` — VERBATIM, no edits |
| `E:\PythonChimera\.tmp\v02_20260906_190511\` → evidence tree | `docs/evidence/v03/...` — relative structure preserved |

## Excluded (stated, per task)

| Path | Size | Reason |
|---|---|---|
| `v03_packet\images\*.png` (14 files) | 14 × 14,748,233 B (~206 MB) | large binaries; retained only in the source `.tmp` tree |
| `v03_packet.zip` | 3,421,251 B | duplicative binary archive of the unpacked `v03_packet/` tree (incl. the excluded images); manifest (`v03_packet_manifest.txt`) already documents it and is published |
| `.marker` | 15 B | scratch marker, not in the assignment's evidence list |

Credential scan (patterns: api key/secret/token/password/bearer/authorization):
**no credentials found** in the instrument or any published evidence file. The
single pattern hit was the phrase "token context window" in
`evidence/BRIEFING.md` (model-context text, not a credential).

## Staging method (byte-exact, stated per task)

This repo sets `core.autocrlf=true` + `.gitattributes` `* text=auto`, so a plain
`git add` would normalize CRLF→LF and change the blob vs. the source bytes.
The instrument (654 CR bytes) and 15 of the 29 evidence files carry CRLF.

Method: every V04 file was staged with

    git hash-object -w --no-filters <file>
    git update-index --add --cacheinfo 100644,<blob>,<path>

so the committed blob content is byte-identical to the E:\PythonChimera source.
Verification: per-file `git cat-file blob HEAD:<path>` content computed to the
same SHA-256 as the source file (table in the assignment reply). Consequence:
`git status` may report some of these files as locally "modified" afterwards —
that is autocrlf's clean-side CRLF→LF view of a deliberately CRLF blob, not a
real change; the blob bytes are the commitment (and equal the working tree).

## Contents (29 evidence files + 1 instrument; LF-only files also staged
byte-exact for uniformity)

`_probe2.py`, `_probe_bridge.py`, `README.md`, `V02_REPORT.md`,
`V03_LEDGER.md`, `V03_QUALIFICATION.md`, `v03_packet_manifest.txt`,
`evidence/{_audit_links.py,_audit_phase.py,_audit_stride.py,_links_raw.txt,
BRIEFING.md,dyad_log.txt,P02_PLATFORM_AUDIT.md,stride.json,
v02_burst_reports.txt,v02_dyad_reports.txt}`,
`v03_packet/analysis/{_audit_links.py,_audit_phase.py,_audit_stride.py,_dup.py,
_l1.py,_l2.py,_links_raw.txt,v02_burst_reports.txt,v02_dyad_reports.txt}`,
`v03_packet/reports/{README.md,V02_REPORT.md,V03_LEDGER.md}`,
`tools/dyad_timed_capture.py` (instrument).