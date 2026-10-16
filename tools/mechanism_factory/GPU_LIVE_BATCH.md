# GPU learned-candidate live batch — NOT YET RUN

Status: the manifest is now ELIGIBLE (fit_job.py authored, CPU-validated,
pinned in identities); the live batch itself remains a separately
scheduled action. The CPU smoke fit ran unqualified (honest 1e-2 N
validation error vs the 1e-6 gate).

Exact command (one reservation; the batch never calls the unloaded model;
the job's own python is C:/Python314/python.exe, which carries torch):

```
D:/Chimera-Maintenance/Runtime/local-ai/Strata/.venv/Scripts/python.exe D:/Chimera-Maintenance/Runtime/local-ai/gpu_batch.py D:/Chimera-Maintenance/PythonChimera/docs/evidence/mechanism_factory/gpu_fit_manifest_20261016T044124.832275Z.json
```

It unloads once, runs the preregistered fit job (--device cuda --seed
1729 --packet), releases in cleanup (success/error/cancellation), and
writes evidence under `Runtime/local-ai/gpu-batches/`; results are read
only after it returns. If any pinned input changed meanwhile, regenerate
the manifest first.

