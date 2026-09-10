# PREREGISTRATION — elastic physical fixture packet

Date: 2026-09-10. This record is written before implementation.

STATEMENT: A versioned CPU fixture packet can preserve the physical E3d/h/E2 contract and provide reproducible full-vector references for a future float32 consumer while leaving immutable legacy fixture bytes and semantics unchanged.

PREDICTION: For the existing rational triangle and canonical patch inputs, the packet will reproduce finite nonzero energy, per-face corner forces, gathered vertex forces, and volume density; equivalent volumetric and explicit surface admissions will agree. A separately rounded float32 input stream will have a separately recorded binary64 reference, rather than being silently substituted for the original physical input.

FALSIFIER: Any omitted or repeated thickness, zero or altered component accepted by the packet; nonfinite output accepted; legacy fixture bytes changed; fixture reader loses provenance or source hashes; an existing output directory is overwritten; or a declared float32 reference is presented as GPU certification without executing a GPU.

Planned falsification controls:
- independent rational full-array oracle on a nonzero triangle, including energy, all corner forces, gathered vertex forces, and w_vol;
- canonical immutable v1 fixture byte hashes and legacy expected arrays checked before/after;
- physical h and 2h comparison with component-wise force/energy scaling and unchanged w_vol;
- explicit binary32 serialization followed by binary64 evaluation, with f32-vs-original references kept distinct;
- actual reader/evaluator mutations (omit h, apply h twice, zero/alter one force or energy, drop provenance, nonfinite value) must fail;
- fresh output paths refuse pre-existing directories/files and failed runs exit nonzero.

Open boundaries: no f32 acceptance budget or GPU certification is derived here; future GPU admission remains governed by GPU_HANDOFF.md Stage C.
