First action: copy this brief verbatim to E:/PythonChimera/forearm_package/audits/A3_site_audit/brief.md (create dir).

ROLE: audit agent (A3) — audit all 32 forearm sites against the source XML: units, identities, endpoint roles.

CAMPAIGN CONTEXT (self-contained): forearm anatomy package to qualify the monkey's physical grasp for climbing. Audit campaign — an external architect (Astra) owns decisions; you produce evidence only. BASELINE (READ-ONLY): E:/PythonChimera/forearm_package/baseline_snapshot/ — code/ (intake.py parses the XML; attachment_candidates.py writes the packet; S13 in run_tests.py is the existing unit-identity test — you must NOT simply rerun S13 and call it done; reimplement the checks independently), runs/attachment_candidates.json (the 32-site v5 packet with per-site source_pos_local, roles, provenance_hashes), source_xml/chimanoid.xml (19 bodies, 937 sites, 468 tendon-referenced, 120 spatial tendons, 121 actuators; site pos in source SI metres), session_reports/anatomy_compiler_05.md (§1 documents the session-5 unit correction: source coordinates export verbatim, the target mesh factor MESH_UNIT_TO_M=0.065 must NEVER enter them; §3 documents roles first_endpoint/last_endpoint/waypoint and the measured law: 8 last-endpoints per side, 0 first-endpoints, 24 waypoints), MANIFEST.json.
NAMING: 32 sites = 16/side; right unsuffixed (BRD-P2), left _l (BRD_l-P2); right body `radius`, left `radius_l`.
FROZEN BOUNDARIES: no edits to the baseline; audit only; discrepancies are FINDINGS, never repairs.
ENVIRONMENT: Windows, Git Bash; python 3.14 + NumPy; run your own scripts from your audit dir with PYTHONDONTWRITEBYTECODE=1; never write into baseline_snapshot/. No network, no GPU, no git write commands.

OBJECTIVE: verify every one of the 32 sites against the raw XML, independently of the pipeline's own test suite.

TASK STEPS:
1. Parse source_xml/chimanoid.xml with stdlib ElementTree yourself. Enumerate the 32 packet sites (from runs/attachment_candidates.json) and locate each in the XML by name.
2. Per site: (a) EXACT comparison of packet source_pos_local vs XML pos — report XML raw string, XML float triple, packet float triple, exact-equality boolean (no tolerance rounding); (b) unit check: prove 0.065 was not applied (packet == XML value AND compute the would-be scaled value to show the check can detect application); (c) identity: owning body, every tendon referencing the site, path index within each tendon; (d) role: index 0 ⇒ first_endpoint, last ⇒ last_endpoint, interior ⇒ waypoint — verify against packet role field; state the actual measured counts (right side, left side, total) vs the report-05 law (8 last / 0 first / 24 waypoints per its scope — verify what the true per-side numbers are).
3. Completeness: all 32 sites exist in XML; every site belongs to ≥1 spatial tendon; no invented sites; sites' provenance_hashes blocks uniform across all 32 (source_xml_raw_sha256 675e00d0…, source_xml_canonical_sha256 7caa32c6…, fitted_packet_sha256 a4475550… — flag any per-site deviation).
4. Canonical hash recipe: find where the code computes source_xml_canonical_sha256 (search code/), reimplement it, verify it reproduces 7caa32c6… from chimanoid.xml. If you cannot reproduce it, record exactly what you tried — that is an UNCERTAIN, not a pass.

PREREGISTRATION (frozen): PREDICTION: 32/32 exact float identity, roles consistent, one uniform provenance block, canonical hash reproduces. FALSIFIER: any single mismatch (float, unit, role, count, hash) fails the audit — itemize both values exactly; do not repair anything.

ACCEPTANCE CRITERIA (verdict each PASS/FAIL/UNCERTAIN): (1) 32-row table complete, each row PASS/FAIL with values; (2) measured role counts stated and reconciled with report-05's law; (3) provenance uniformity verdict; (4) canonical-hash recipe reproduced (or UNCERTAIN with attempts); (5) baseline integrity — paste git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot (must be empty).

OUTPUT CONTRACT: write ONLY inside E:/PythonChimera/forearm_package/audits/A3_site_audit/ (brief.md, report.md, scripts/, receipts/). report.md: verdicts per criterion; evidence with file+line+numbers; explicit uncertainty; negative findings preserved; receipts (exact commands + key output). A null result is a result.
STOP RULE: stop when all criteria have verdicts or a dependency is missing — record the blocker and stop. Do not repeat a failed approach more than twice.
