# PROPOSED FIX — `core/council.py::_ensure_model` (NOT APPLIED)

> Status: **prepared only**. Do NOT apply while the lead is live on the council/dyad
> (tb-0214 / dyad drives). Apply after the doc-sync settles, and only if/when model
> swapping is actually enabled.

## Important correction (verified 2026-07-19)

The night-hang we hit was **NOT** caused by this function. In this environment:

```
CHIMERA_FAST_MODEL = None
CHIMERA_DEEP_MODEL = None
=> _SWAP_ENABLED = False  => _ensure_model() is a no-op (returns on `if not model_id`)
```

The observed hang was the `expectation_violator` *generation request* stalling in the
lm_gateway fair-queue (`concurrency=1`): `[lm_gateway] violator: waited 51.1s in queue`,
then its own call never returned. That is mitigated by the **already-applied**
180s guarded-thread timeout in `core/dream_loop.py` (see `docs/NEXT_STEPS.md` progress
log). This `_ensure_model` fix targets the **separate, latent** defect the Will noted
(`_ensure_model evicts all before loading, :N suffix not recognized`), which would
bite the moment swap is enabled.

## The two documented defects

1. **evict-all-before-load** — current order is `evict_others(model_id)` THEN
   `load_model(...)`. If the load fails (or stalls), the previously-resident model is
   already gone, leaving the endpoint EMPTY. The subsequent `resolve_model()` raises
   `NoModelLoaded` for every queued request — a self-inflicted bad state.
2. **`:N` suffix not recognized** — `load_model` posts `{"model": model_id}` verbatim.
   If `model_id` carries an LM Studio-rejected `:N` quantization suffix, the load
   endpoint may reject or hang, and the swap silently falls back to "adopt mode" with
   nothing resident.

## Current code (`core/council.py`)

```python
def _ensure_model(model_id: str):
    if not model_id:
        return
    if model_id in loaded_models():
        return
    try:
        # Unload current model first (frees VRAM for the new one)
        evict_others(model_id)
        load_model(model_id, timeout=_SWAP_TIMEOUT, context_length=100000)
        print(f"[council] swapped to {model_id}", flush=True)
    except Exception as _se:
        print(f"[council] swap to {model_id} failed: {_se}")
        print(f"[council] continuing with the currently resident model (adopt mode)")
```

## Proposed replacement

```python
def _normalize_model_id(model_id: str) -> str:
    """LM Studio's /api/v1/models/load rejects some `:N` quantization suffixes
    (e.g. `uns loth/qwen3.6-35b-a3b:UD-q4_k_m`). If the suffix is not a recognized
    LM Studio tag, fall back to the base id (the resident model usually matches the
    base). Logs the normalization so a bad env value is visible, not silent."""
    base, sep, suffix = model_id.partition(":")
    if not suffix:
        return model_id
    recognized = {"q4_k_m", "q4_k_s", "q5_k_m", "q8_0", "q4_0", "q3_k_m",
                  "q6_k_m", "f16", "f32", "q2_k_m"}
    if suffix.lower() in recognized:
        return model_id                      # LM Studio understands this tag
    print(f"[council] model suffix ':{suffix}' not recognized by LM Studio; "
          f"using base id '{base}'")
    return base


def _ensure_model(model_id: str):
    """Swap LM Studio to `model_id`. No-op if already resident.

    Robust swap (fixes the 'evict-all-before-load' + ':N-suffix' defects):
      - Normalize the id first (strip/reject unrecognized `:N` suffixes).
      - LOAD the target BEFORE evicting the old one, so a failed/slow load leaves
        the previously-resident model in place (no empty-VRAM window, no
        NoModelLoaded cascade for queued requests).
      - If the load fails AND nothing is resident afterward, fail loudly instead of
        silently continuing into a broken (empty) endpoint state."""
    if not model_id:
        return
    model_id = _normalize_model_id(model_id)
    if model_id in loaded_models():
        return
    try:
        # Load the target FIRST; only free the old model once the new one is resident.
        load_model(model_id, timeout=_SWAP_TIMEOUT, context_length=100000)
        evict_others(model_id)
        print(f"[council] swapped to {model_id}", flush=True)
    except Exception as _se:
        resident = loaded_models()
        if not resident:
            # Swap failed AND we evicted everything (or it was already empty) ->
            # the endpoint is now dead. Surface it instead of pretending adopt-mode works.
            raise RuntimeError(
                f"model swap to {model_id} failed ({_se}) and no model is resident; "
                f"load a model in LM Studio before continuing") from _se
        print(f"[council] swap to {model_id} failed: {_se}")
        print(f"[council] continuing with resident model {resident[0]} (adopt mode)")
```

## Trade-off to confirm before applying

`load-then-evict` briefly holds TWO models in VRAM (the new one loading alongside the
old). If they don't both fit, `load_model` raises `TimeoutError`/`RuntimeError`, which
is caught and falls back to adopt mode (old model still resident) — strictly safer than
today's evict-then-load. Confirm the chosen FAST+DEEP pair fits concurrently, or set
`_SWAP_TIMEOUT` high enough that LM Studio finishes the load before the fallback.

## How to test (after applying)

1. Set `CHIMERA_FAST_MODEL` / `CHIMERA_DEEP_MODEL` to the two resident-capable ids.
2. `python -m core.council "test swap" --rounds 1` — watch for `[council] swapped to ...`
   and confirm no `NoModelLoaded` afterwards.
3. Deliberately set a bad `:N` suffix in one env var; confirm it normalizes + loads (or
   fails loudly) instead of hanging the endpoint.

## Companion fix for the ACTUAL night hang (recommended, separate)

Because the real hang was a *stalled generation* (not the swap), also add a hard
per-request timeout on the violator's generation so a wedged model can't occupy the
`concurrency=1` queue slot indefinitely. The 180s guarded thread in `dream_loop.py`
already makes the night survive this; a request-level timeout in `expectation_violator`
would make the violator itself skip cleanly instead of burning the full 180s.
