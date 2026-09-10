# Exact publication verification

Task engine-http-lifecycle-01 generation 2. Source commit bee78064 follows a normal merge of the integrated PR25 prerequisite (24ac7af3). The normal library, documentation and attribution commit gates passed.

Before the merge, a binary staged patch and SHA256 manifest for all 114 scoped files were saved in task-local preservation storage. Stash 37be2b7ea15de4f4e8acb845d8abb89c7f676208 was retained, not dropped; unrelated untracked Saved logs were excluded. After reapplication, the committed Git patch equals that saved patch byte-for-byte. A stricter working-file hash comparison FAILED for the source/text files listed in checkout_byte_changes.json following Git checkout conversion. The assertion did not prevent the subsequent PowerShell commit command from executing; no publication occurred before resolving this verification gap. Original raw stdout/stderr run captures and result JSON still match the saved hashes. Do not claim all pre-merge working-file bytes were preserved.

To bind the actual publication source bytes, the independent private build was rebuilt with:

```text
cmake --build E:/ChimeraWork/slot-03/.tmp/engine_http_lifecycle_parent_review --clean-first -j2
```

The resulting engine_http_lifecycle_gen2_review executable ran each mode named in results.json as a separate hidden owned process with a three-second watchdog. All ten returned exit 0 without watchdog termination. Each launch first checked the harness port was free. Build output and raw per-mode output are retained here; hashes.json binds source, header, harness and executable bytes. The original baseline hangs, failed builds and superseded weak callback gate remain retained in their historical directories.

Claim: CPU Winsock server lifecycle behavior under finite nonthrowing callbacks. No whole-engine shutdown, GPU, DYAD, firewall-policy or performance certification. The next required task is engine-shutdown-order-01.
