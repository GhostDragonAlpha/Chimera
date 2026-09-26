# W03 DECISION REQUEST — the anchor-version ruling (walking chain, blocks W03→W05)

**From:** the play coordinator, per P02P03's W03 verdict. **Evidence:** receipts `reach_band_v1_anchor_drift_b643a850.txt` + `prereg_tie_v2_9376c3d8.txt` (committed on this branch); the tick-41 fixture `co8_t41_fixture/` at the game tip.

## The decision (Astra's, quoted from the receipt's own framing)

The reach-band v1 patch changes anchor bytes at the 6 band-entry sites the anchor walk passes through — sites CONSTRUCTED at the annulus edge by the wave-24 hold-arm bisections (the anchor's own machinery seeks the band). The receipt names the two lawful resolutions:

- **Option A — scope the band to non-constructed entries** (the v1 patch's byte changes at constructed seats are excluded; constructed seats keep legacy semantics);
- **Option B — re-baseline the anchor at the version bump** (the pre-v1 anchor is already retained in the fixture; the anchor registry records v1-preserved/v2-recorded per the tie-v2 prereg).

Either is legal; the choice changes which bytes the frozen walk anchors reproduce, which is why it is not ours.

## Everything else on W03's critical path (ready, no decision needed)

1. **tie-v2 execution** — REGISTERED (9376c3d8, prereg committed before any run): the contact-residual tie bound = kTouch (1e-5 m) → 3e-3 m/s in row velocity units, one-sided, falsifier cases frozen (kTouch/dt boundary ±1 ulp; replay past tick 41 on host AND GPU from the fixture state). Preserved unrun at the shutdown (a62b286e). Executing it is walking-authorized work under the existing runbook protections.
2. **Clean-window C3 bars re-measure** — the final bars need an uncontended window (gaming-aware scheduling; CPU/host side per the receipts).
3. **W01's residual boundary, charged here:** the tick-40/41 contact-residual knife (g0 = −6.9e-18) is exactly what tie-v2 addresses; the row-0 sign decision is registered as its own v2 item with its own scale candidate (the kTouch pad resolution quantum).

**Recommendation field: LEFT TO ASTRA** (options A/B above; or a third framing if the receipt's dichotomy is incomplete).
