# GPU learned-candidate live batch — NOT YET RUN

Status: implementation-only seam (manifest + dry run complete; the fit
job script `gpu_learned_candidate_fit.py` is authored in the next seam).

Prerequisites before the live run: author the fit script, regenerate the
manifest (`python tools/mechanism_factory/gpu_fit_manifest.py`) so its
`identities` pin the script, and confirm `eligible_for_live_batch: true`.

Exact command (one reservation; the batch never calls the unloaded model):

```
D:/Chimera-Maintenance/Runtime/local-ai/Strata/.venv/Scripts/python.exe D:/Chimera-Maintenance/Runtime/local-ai/gpu_batch.py <stamped_manifest_path>
```

It unloads once, runs the preregistered job sequence, releases in cleanup
(success/error/cancellation), and writes evidence under
`Runtime/local-ai/gpu-batches/`; results are read only after it returns.
