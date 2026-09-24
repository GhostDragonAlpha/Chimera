# M07 harness incident — 2026-09-24 (preserved failure; agent-side, NOT an exporter defect)

First execution attempt: all seven cases exited 1 with empty stdout and the identical stderr:

```
Traceback (most recent call last):
  File "E:\ChimeraWork\mvc-20260924\material_volume_campaign\agents\M07_ownership\work\material_volume_body_export.py", line 27, in <module>
    import material_volume_admission as admission
  File "E:\ChimeraWork\mvc-20260924\material_volume_campaign\agents\M07_ownership\work\material_volume_admission.py", line 25, in <module>
    import material_volume as mv
ModuleNotFoundError: No module named 'material_volume'
```

Cause: my work/ copy set omitted `tools/material_volume.py` (the tetrahedral compiler) which
`material_volume_admission.py` imports. tools/ was never written; the failure was entirely in the
agent harness. Fix: copied the compiler into work/ and re-ran the full matrix from scratch.
No case data from the failed run was used as evidence. All receipts under receipts/ are from the
post-fix run (the failed run's stderr files were overwritten by the rerun; this file preserves
the traceback verbatim).

Lesson inherited by the next agent: the body-export lane's transitive local dependency set is
{material_volume, material_volume_admission, material_volume_body_export,
material_volume_body_export_reader} — copy all four before executing.
