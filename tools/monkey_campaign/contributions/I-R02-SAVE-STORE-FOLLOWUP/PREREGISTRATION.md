# PREREGISTRATION — I-R02-SAVE-STORE-FOLLOWUP

Card: I-R02-SAVE-STORE-FOLLOWUP (planning ID R02, verification profile: recovery)
Attempt: 21e3724ba8f84dd2bce9ed079c59979a, agent c95e1722350849bca846b237c1f60997
Criteria sha256: e6011f9304d14799c953cd323881d28674a5491b1eb702625082085f0f1fce5d
Written BEFORE any adapter/test edits (frozen before the run, per Rule 0).

## SUBJECT UNDER TEST (exact bytes, not a stand-in)

The MERGED save-store from parent card I-R02-SAVE-STORE:

- Winning PR: https://github.com/GhostDragonAlpha/Chimera/pull/117
- PR head (merged): `9ba1be77228e181f55ed2e4d2eb3e73e2f09685f` (= branch-4 HEAD of this
  attempt checkout; merge recorded 2026-09-25T16:03:36Z)
- Path in merged tree: `tools/monkey_campaign/contributions/I-R02-SAVE-STORE/save_store.py`
- Raw SHA-256 of the exact bytes under test:
  `cf175ea73508927697905cb9faa96737bb454ce7e946caa1ccc247338e4f9347`

The harness REFUSES to run (named refusal `stand_in_module`) against any
`save_store.py` whose SHA-256 differs from the value above. The falsifier of this
card is partly self-enforcing: a rewritten stand-in cannot even be loaded.

## STATEMENT (a theory that can lose)

The merged atomic-write law — canonical bytes → temp file in the destination
directory → flush → fsync → `os.replace` — plus the flat-slot-name law and the
refusing parse of stored envelopes, makes a REAL process death at any point before
the atomic replace unobservable at the slot level: the previously saved envelope
remains the exact bytes it was, still loads byte-exact through the accepted module,
and no corrupt or partial content is ever reachable under a real slot name
(`*.save.json`), because crash debris can only exist under temp names that the
store's own scanner never lists.

## PREDICTION (not yet measured)

Measured with a subprocess fault-injection harness that kills a real writer
process (`os._exit`, no cleanup, no exception unwinding) at four deterministic
injection points inside `SaveStore.save` — `before_open`, `mid_write`
(half the envelope bytes written), `before_fsync` (fully written, not synced),
`before_replace` (fully written + fsynced, death immediately before `os.replace`):

1. In EVERY interruption trial over a pre-existing valid save A, the slot file
   bytes are unchanged (SHA-256 equal to A's), `load` returns `status="loaded"`
   with `payload == A_payload` byte-exact, and `list()` reports exactly one slot
   with `status="ok"`. Expected: 4/4 points pass, including the targeted
   `before_replace`.
2. An interrupted FIRST save (no prior save) leaves `load -> first_run` and
   `list -> []`; the debris temp file (when one exists) does not end with
   `.save.json` and is never listed.
3. Byte-level corruption of a stored envelope — raw truncation, payload_b64 flip,
   stored-hash tamper, payload_size tamper, invalid UTF-8, textual duplicate key,
   NaN literal, wrong schema, non-positive/wrong-typed format_version, deleted
   identity — refuses on load with the SPECIFIC named code (never a silent or
   generic failure), and expected-identity mismatches on an intact envelope
   refuse as `*_mismatch`.
4. A crash loop (repeated interrupted overwrites, rotating injection points)
   never exposes partial content; the first subsequent clean save restores normal
   operation and loads byte-exact.
5. Refusal laws hold identically inside the child process path: a traversal slot
   name is refused with code `slot_traversal` in the subprocess.

## FALSIFIER (named before the run)

Any of the following fails this card:

- F1: any interruption trial where the real slot file's SHA-256 changes, `load`
  does not return the prior payload byte-exact, or `list` shows an extra/absent
  slot;
- F2: any corrupted/truncated envelope that LOADS (`status="loaded"`), or refuses
  without a named refusal code;
- F3: any interruption that produces observable content under a real
  `*.save.json` slot name (partial or new);
- F4: the harness exercising any module whose SHA-256 differs from the accepted
  merged bytes above (stand-in), or claiming physics-state restore qualification
  — out of scope: payload opacity is preserved; no engine snapshot semantics are
  tested or claimed.

## BOUNDS

CPU-only, stdlib only, temporary directories only, each subprocess capped at 30 s
and each test invocation bounded well under 120 s; no GPU, no network installs, no
production-checkout edits; the merged source file is read-only in this workspace.
