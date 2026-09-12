# Corrective CPU preregistration

The original CPU harness copied the helper, compared a fixed event vector to itself, entered boot_cancel with closing already true, and mutated applied without its mutex. Its reported passes do not establish the advertised gates. Original source/harness/output remain retained.

STATEMENT: the actual main.cpp cancellation helpers wake genuinely parked channel/boot waits; cancelled unapplied operations throw the named cancellation, while already-applied work returns true. Notifying while holding the matching mutex closes the check-to-park lost-wake window.

PREDICTION: extract the exact helper block from main.cpp at run time without rewriting it, compile it with nine standard channel fixtures, and exercise waiting/cancelled/already-applied/boot states. The boot test starts with closing false and acquires the wait mutex after the worker announces entry, so a nonfinished parked worker is observed before cancel. A condition test witness rejects notification without matching lock ownership.

FALSIFIERS: any noncancelled unapplied result; cancellation of already-applied work; a copied implementation substituted for the actual source; unobserved boot wait; unlocked notification; or mutation that removes closing from the wait predicate or replaces cancellation with success still passing. The per-subprocess five-second watchdog is a preregistered test safety policy; mutant waits use sixty-second requested waits to distinguish notification from natural timeout without changing production timeouts. Failures and mutation sources/results remain retained.

Actual shutdown ordering, recursive session behavior and late API entry require the real native executable. The old constant-vector check is explicitly superseded, not counted as evidence.
