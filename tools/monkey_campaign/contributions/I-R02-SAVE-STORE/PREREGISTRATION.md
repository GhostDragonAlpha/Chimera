# PREREGISTRATION — I-R02-SAVE-STORE

Bounded implementation claim `I-R02-SAVE-STORE` (planning id R02), attempt
`ee0799d3f9d445928350c932be0c6805`, base revision
`9afbddcd90164b5544a16fd0bc72278d985eb6e3`. Frozen **before** any edit to
`save_store.py`, per the brief's step 1 and Rule-0 of AGENTS.md.

## STATEMENT (someone could disagree with this)

A user save is a *self-contained envelope* — one JSON document that carries its
own format version, build/scene/policy identities, a sha256 of the opaque
payload, and the payload itself base64-encoded inside it — written atomically
(temp file in the destination directory + flush + fsync + `os.replace`). The
envelope is the unit of durability: because the whole document replaces atomically
and the previous document stays on disk until the new one fully succeeds, an
interrupted write can never destroy or half-overwrite a previously valid save.

The payload is treated as **opaque bytes**. This store does not know, compress,
reorder, or serialize any physics — it only records *what* was saved (identities +
hash) and guarantees the *bytes* come back byte-exact. The engine owns snapshot
serialization; this envelope owns durability and identity refusal.

## PREDICTION (not yet measured at freeze time)

If a caller saves slot `A`, then an interrupted save of slot `B` fails **after**
its temp file is written but **before** `os.replace`, then:

  * `load("A")` still returns the exact previously-saved payload byte-for-byte,
  * no partial document exists under any real slot name in the user directory, and
  * the failed `B` write leaves exactly one stray temp file (`.B.save.tmp-<pid>`)
    that is never enumerated by `list()` and never mistaken for a save.

If a caller saves an envelope with identities `(v3, buildX, sceneY, policyZ)` and
then loads it requesting any ONE of those identities with a different value, the
load refuses with a named identity refusal rather than returning bytes; if the
stored payload is truncated by even one byte or flipped by one bit, the recomputed
sha256 will not match the stored `payload_sha256` and the load refuses.

## FALSIFIER (named before the run — this build LOSES if it fails)

The build is WRONG if any of:

  1. **Interrupted write destroys a prior save** — an exception during `save()`
     that occurs after the temp file exists but before `os.replace` leaves the
     earlier valid slot unreadable, corrupted, or missing; or leaves a partial
     document under a real slot name.
  2. **Traversal escapes the caller directory** — a `slot_name` containing `..`,
     an absolute path, a drive letter, or a separator resolves to a file outside
     the explicitly-supplied user directory and is accepted for read or write.
  3. **Mismatched identities are accepted** — `load()` returns bytes when a
     supplied expected identity differs from the stored one, or silently defaults
     a missing expected identity instead of refusing; or tampered/truncated
     payload passes the hash check.

## REUSED CONVENTION (not duplicated)

`input_settings.py` at base revision already implements the exact atomic-write
law this store must reuse: canonical deterministic UTF-8 bytes -> temp file in the
destination directory -> flush + fsync -> `os.replace`, with the temp removed on
any failure; and a TOTAL, refusing load parser (duplicate JSON keys, NaN/Infinity,
unknown schema/version, wrong types each refuse by name). `save_store.py` reuses
that convention verbatim for the write path and its refusing-parser shape for the
read path. It does NOT import or copy `input_settings.py`; it is a standalone
stdlib-only module so tests stay CPU-bounded with no engine dependency.

Extracted source (recorded hashes, read-only under `reference/`):

  * tools/monkey_campaign/product/input_settings.py   sha256=8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1
  * tools/monkey_campaign/product/session_flow.py      sha256=30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf
  * tools/monkey_campaign/product/input_mapper.py      sha256=7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44
