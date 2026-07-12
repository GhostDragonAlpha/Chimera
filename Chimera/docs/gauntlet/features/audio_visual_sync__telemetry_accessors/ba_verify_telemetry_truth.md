# Bachelor: which numbers can lie — audio_visual_sync/telemetry_accessors

The lying defaults, named (this feature's own rap sheet, H-32): count=0 while
feet move — the hardcoded initializer masquerading as a quiet world; the
read-back that exposes it is the paired velocity check (pawn speed > 0 over
the same interval the count stayed flat). latency=999 ms — the no-sample
initializer leaking through as if it were a measurement; exposed by asserting
the NO-SAMPLE sentinel explicitly at zero-state and asserting NOT-999 after
strides. Orphan count silently absent — a missing accessor reads as zero
orphans forever; exposed by runtime_report listing the accessor surface, so
absence is visible rather than reading as innocence.

The rule generalized for this feature: any accessor whose failure value is a
PLAUSIBLE success value is a lie waiting to be graphed — failure states must be
sentinels no honest measurement can produce.
