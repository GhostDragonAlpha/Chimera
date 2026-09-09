# GPU-DEMO-RECOVERY-01 — fix preregistration (Rule 0, before any patch)

## Recovery facts (measured, not guessed)

- GLM's commit `35f97e34` exists ONLY in `chimera_pub` (never pushed; GitHub
  cannot resolve it). Transferred bit-identical onto branch
  `gpu-demo-recovery-01` as `0a412754` + recovery `913837a9`.
- 8 Windows Error Reporting dumps + 5 event-1000 records: ALL show
  `VCRUNTIME140!memcpy` fault writing to **dst=0xF, size=72**, decoded to
  `Engine::membrane_demo_init`'s `md_idx_host_.assign()` growth/overwrite
  memcpy (init:4115, B2's 18 indices) with `md_idx_host_._Myfirst=0xF`
  (six independent disasm anchors: member offsets, assign shape, gamma-store
  followers, string assigns, BSS src anchors, caller identity).
- Proven adjacent defects (measured live): H1 cross-size re-upload silently
  accepted + invalid_surface (host mapped-buffer overrun class); D1 gamma
  key-substring misparse (op-first order admits 0.0); D2 reset stale forces;
  init accepts degenerate/NaN geometry ok:true; H2 render_state_id=0 always;
  H5 unbounded n_steps.
- The 0xF header value's writer is NOT identified: no legitimate op produces
  it, no foreign writer is visible in source, H1-class overruns target
  driver heap (cannot reach main-stack headers). Triggering history is
  unrecoverable (no request log survived; GLM unavailable).

## STATEMENT

The crash class (wild host-mirror header + unbounded re-init writes into
create-once buffers) is eliminated by: refusing cross-size re-init by name,
refusing on incoherent host mirrors by name (with stderr evidence), refusing
invalid initial states by name, fixing the gamma key parse, refreshing reset
forces, and clamping n_steps — with zero change to membrane laws, material
meaning, tolerances, or acceptance criteria.

## PREDICTION

After the patch: same-size flows are bit-identical (state ids match
pre-patch values); cross-size re-upload → named refusal, process alive;
degenerate/NaN upload → named `invalid_surface` refusal; gamma admits 2.0
key-first with energy doubling at fixed state; reset reports fresh forces;
n_steps=1000000 clamps; full P1–P7 gate passes; the regression fails on the
unpatched build and passes on the patched one.

## FALSIFIER

Any AV/crash on the patched build across the full gate + marathon; any
same-size state-id drift vs pre-patch; any silent invalid acceptance; any
physics-number change beyond the frozen budgets. A fired falsifier stops the
milestone claim (fix re-derived, never widened).
