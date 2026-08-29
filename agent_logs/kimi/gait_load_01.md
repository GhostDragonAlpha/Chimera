# H7/G3 — The Real-Load Gait: κ/σ Derivation, Re-Measured Bands, and the G4 Re-Run

**Agent:** kimi-code (k3-256k)
**Run date:** 2026-08-29
**Spec:** `agent_logs/kimi/contact_ref_01.md`'s named next step + the follow-up brief; `agent_logs/hy3/gait_packet_01.md` G2/G4/G5
**Constraints honoured:** CPU-only; zero engine contact (the engine is live; a frost integration is re-uploading the decode model concurrently); scratch in `.tmp` uncommitted; `tools/gsplat` untouched.
**Builds on:** commit `fae174a0` (deterministic contact solve, estimator B, 0 ULP gates).

## The membrane (Rule 0, stated before the runs)

- **STATEMENT.** A load channel's gain is set by the channel's **own maximal braking
  rate** `M = max_t (N(t)·cosφ(t))` — the strongest the Owaki term `φ̇ = ω − σ·N·cosφ`
  can pull against the phase, given the channel's curve and where its press windows sit
  in phase. The CPG is in its sensitive band — maximal load feedback that can never halt
  the phase — when the peak braking rate equals the design sweep's lower bound:
  `σ·κ*·M = ω_lo = π`, i.e.
  ```
  κ* = ω_lo / (σ · M) = π / (σ · M)
  ```
  Every factor is measured (M from the canonical reference stride at ω_ref) or
  design-derived (ω_lo = π, the 2 s slow-walk end of the packet's sweep; σ = 0.5, the
  packet's own gain). The surrogate's stall normalization (κ_stall = N0/peak,
  N0 = 2ω_ref/σ) saturated because the real channel's press *plateau* sits at 0.98 of
  peak: the operative statistic is the braking-rate maximum M, not the load peak P.
- **PREDICTION.**
  - P1: `κ*/κ_stall = (ω_lo/2ω_ref)·(P/M) = 0.20 × 1.20 = 0.24` — the earlier measured
    working point (×0.25 of κ_stall, tight walk) falls out of the derivation within ±0.05.
  - P2: the stall boundary at ω_ref sits at `κ_crit = κ*·ω_ref/π` = ×0.60 of κ_stall:
    a run there is **marginal** (heavily braked but advancing, cadence > 0) — bracketed
    by the measured ×0.5 (walks) and ×1.0 (parks at 0 Hz).
  - P3: at κ* the G2 bands with real λ lock with coherence R ≥ 0.97 on every pair and are
    at least as tight as the surrogate's (Σσ ≤ 1.02 rad).
  - P4 (the pre-registered G4 question): with real λ at κ*, the lag graph **changes**
    across ω ∈ [π, 4π] — the brake ratio spans ≈1.0 at the π end down to ≈0.25 at the 4π
    end, so the transition candidate is at the **low** end, where the walk goes marginal.
- **FALSIFIER.**
  - F1: κ*/κ_stall outside [0.19, 0.30] → the derivation does not explain the working point.
  - F2: the ×0.60 run parks (< 0.05 Hz) or walks free (≥ 1.2 Hz) → the stall-boundary
    prediction is wrong.
  - F3: any pair fails to lock (R < 0.9) or half-split drift > 5σ_band at κ* → the real
    channel does not entrain at the derived gain.
  - F4 (packet verbatim): lag graph constant within σ_band across the whole sweep → the
    real load channel produces no transition either → amend the packet's Owaki form.

## 1. The κ/σ derivation — and the ×0.25 point falls out of it

Measured from the canonical reference stride (`.tmp/contact_ref_out/stride_curves.npz`,
estimator B raw curve; machine JSON `.tmp/gait_load_out/derive.json`):

| leg | peak P (raw) | max_t(N·cosφ) = M (raw) | P/M |
|---|---|---|---|
| L | 27,216.8 | 22,132.9 | 1.2297 |
| R | 27,466.4 | 22,843.2 | 1.2024 |

M is reached in the *second* press window (φ ∈ (3π/2, 2π), cosφ > 0 — the only place the
Owaki term brakes; in the first window cosφ < 0 and the load *accelerates* the phase —
measured structure of the double-peak channel, used, not averaged away).

```
κ*        = π / (0.5 × 22,843.2) = 2.7506e-4
κ_stall   = N0/P = 31.416 / 27,466.4 = 1.1442e-3
κ*/κ_stall = 0.2405 = (ω_lo/2ω_ref)·(P/M) = 0.200 × 1.2024        → F1 PASS (in [0.19, 0.30])
```

So the ×0.25 point was never a knob: it is `sweep-placement (0.200) × channel dynamic
range (1.20)`. The two factors are independently meaningful: 0.200 puts the strongest
possible braking exactly at the slow end of the design sweep (below π the phase *can* be
halted — the entrainment boundary); P/M = 1.20 is the real channel's saturation tax (a
near-binary press plateau wastes 20% of the peak normalization that the surrogate's
momentary-peak shape did not).

Brake ratio at ω_ref with κ*: σ·κ*·M/ω_ref = π/ω_ref = **0.400** — the Owaki term brakes
up to 40% of the commanded phase rate at the press peak, never more.

**F2 boundary run (κ_crit = 6.876e-4 = ×0.601 of κ_stall):** cadence L 1.010 / R 1.004 Hz
(19% brake — heavily braked but **advancing**, not parked), Σσ = 6.003, min R = 0.436,
duty 0.60/0.60. **F2 PASS** — the predicted stall boundary is where the gait goes
marginal; the ×0.5 (walks) / ×1.0 (parks) bracket is explained, not just measured.

## 2. G2 bands with real λ at κ* (protocol of stage 1: burn-in 5 s, window 20 s, seed
20260829, circular statistics, branch-cut-safe)

Machine JSON `.tmp/gait_load_out/bands_load.json`; recording `.tmp/gait_load_out/bands_kappa_star.npz`.

| directed edge | target α (cyc) | settled Δ̄ (cyc) | σ_natural (rad) | δ_band = ±2σ (rad) | drift (rad) | R |
|---|---|---|---|---|---|---|
| LF_hip→LF_knee | 0 | +0.0098 | 0.0179 | ±0.0357 | 0.0111 | 1.000 |
| RF_hip→RF_knee | 0 | +0.0084 | 0.0152 | ±0.0304 | 0.0083 | 1.000 |
| LH_hip→LH_knee | 0 | +0.0091 | 0.1136 | ±0.2273 | 0.0005 | 0.994 |
| RH_hip→RH_knee | 0 | +0.0088 | 0.1228 | ±0.2455 | 0.0011 | 0.992 |
| LF_knee→RF_knee | 0.5 | −0.4997 | 0.0256 | ±0.0512 | 0.0076 | 1.000 |
| LH_knee→RH_knee | 0.5 | −0.4992 | 0.2121 | ±0.4242 | 0.0018 | 0.978 |
| LF_knee→RH_knee | 0.25 | +0.2688 | 0.1191 | ±0.2383 | 0.0054 | 0.993 |
| RF_knee→LH_knee | 0.25 | +0.2677 | 0.1102 | ±0.2203 | 0.0004 | 0.994 |

Headline: **Σσ_natural = 0.7364 rad** (surrogate: 1.0178 — the real channel's bands are
*TIGHTER*), max half-split drift 0.0111 rad, **min coherence R = 0.9778** (every pair
locks), cadence 1.240/1.240 Hz (0.8% Owaki brake), N duty L 0.447 / R 0.457, stance
correlation +0.557/+0.529 (load high when planted; not +1 by design — the double-peak
channel unloads at deepest stance). The hind diagonals settle at +0.269 cyc (canonical
target 0.25 — the real load shifted the diagonal lag by 0.019 cyc *inside its own band*,
the L/R-asymmetric press windows talking through the coupling; the surrogate settled at
+0.252). **F3 PASS** — the real channel entrains the CPG at the derived gain, and the
entrainment is better than the surrogate's.

## 3. THE G4 RE-RUN — ω-sweep with real λ at κ*

Protocol per the packet, exactly as stage 1 but with the real load channel:
ω ∈ [π, 4π], Δω = π/8 (25 dwells), dwell 10 s, state carried, up-sweep then down-sweep,
lag vector over the last 5 s of each dwell, branch-cut-safe dist_from_target + coherence
R, jump threshold 3·max(σ_band) = 0.636 rad. Per-dwell cadence and N duty recorded (the
stall signature). Machine JSON `.tmp/gait_load_out/sweep_load.json` (full 25×2 dwell
curves), log `.tmp/gait_load_out/sweep.log`.

**The curve (cadence and lock vs ω):**

| ω (×π) | cadence L (Hz) | brake vs free-run | min pair R | hind lag (cyc) |
|---|---|---|---|---|
| 1.000 | 0.491 | 98.2% | 0.906 | −0.498 |
| 1.250 | 0.605 | 96.8% | 0.927 | −0.498 |
| 1.500 | 0.726 | 96.8% | 0.947 | −0.493 |
| 1.750 | 0.871 | 99.6% | 0.957 | −0.496 |
| 2.000 | 0.991 | 99.1% | 0.966 | −0.499 |
| 2.500 | 1.247 | 99.8% | 0.978 | −0.497 |
| 3.000 | 1.497 | 99.8% | 0.984 | −0.500 |
| 3.500 | 1.740 | 99.4% | 0.989 | −0.500 |
| 4.000 | 1.992 | 99.6% | 0.991 | −0.499 |

Down-sweep: the same curve point-for-point within band tolerance (min R declines
smoothly 0.991 → 0.906 toward π; hind lag −0.497…−0.500 cyc everywhere; the ± sign
flips on the π-locked hind pair are stage 1's documented branch-cut artifact — same
physical state).

**Verdict, stated plainly:**

- Max step-to-step lag-vector jump: **0.108 rad (up), 0.036 rad (down)** — 6× under
  threshold. Zero crossings. **Δω_h = 0.** τ_trans: undefined (no ω* exists).
- Per-edge dist-from-target range across the whole up-sweep: **≤ 0.175 rad**.
- Per-edge minimum coherence across the sweep: **R ≥ 0.900** — every pair locked at
  every ω in both directions.
- The packet's FAIL condition — "Δ̄(ω) constant within σ_band across [π, 4π]" — is
  **TRIGGERED with real λ**: the lag graph is the same walk at every ω. **F4 FIRED.**
- P4 (my prediction of a low-end marginality transition) is **FALSIFIED**: at ω = π the
  gait walks at 98.2% of free-run with every pair locked (R ≥ 0.906). The peak-instant
  brake ratio does reach ≈1.0 at π (by construction of κ*), but a trap needs *sustained*
  σ·N·cosφ ≥ ω — the stride-averaged braking is ~2% (the press is 45% duty and the
  braking half of it), so the phase sails through. The stall trap measured in
  `contact_ref_01.md` needed the *plateau* at stall level (×1.0 normalization), not the
  instant.

**The honest conclusion for the packet:** the mandatory re-run is done and the answer is
NO again — the real load channel does not produce an ω-driven gait transition or
hysteresis on this substrate. The load phenomenon this system *does* exhibit is the
**gain-driven** one already measured: walk → in-phase park across the *load-strength*
boundary at fixed ω (the stall trap), with a clean re-patterning continuum through the
marginal point (F2's run: 19% brake, R 0.44, diagonal lags wandering). Owaki's
walk→trot transition is a *speed*-driven phenomenon, and on this substrate the speed
channel is dead at the gait level: (a) the load carries pose, not speed (the Baumgarte
clamp saturates — `contact_ref_01.md` falsifier iii); (b) the phase-dynamics brake ratio
averages ~2%, far from the marginality a transition needs; (c) the only thing in the
system that re-patterns the gait is load GAIN. **The amendment the packet needs
(candidates, not built):** (i) a load channel that carries velocity state (a drive that
doesn't plunge 5.8× slop into the support, or a band re-derived for the press regime);
(ii) load-dependent *coupling* (the bands breathe with load — the channel talks through
w, not just through N_i); (iii) swing/stance asymmetry in the drive (θ_amp or waveform
modulated by load — biology's own lever). Until one of those exists, G4's Δω_h > 0 is
**FALSIFIED at the CPU tier with real λ** — recorded, not waived. The engine port should
not promise the transition either; it inherits the same dynamics.

## 4. G5 energy with real λ

From the κ* band run (machine JSON `.tmp/gait_load_out/energy_load.json`):

- Measured stride period **0.8065 s** (1.240 Hz — 0.8% below free-run 1.250 Hz: the real
  channel's Owaki brake, vs the surrogate's 3.6%).
- **W_proxy = 580.30°/stride** vs the analytic limit-cycle 4·Σ|θ_amp| = 580.06° — 0.04%
  agreement (a clean limit cycle; the gait is the same sinusoid family, load-braked).
- **No-pump falsifier:** E_mech = Σ ½Iθ̇² halves 50.815 → 50.211 — no monotonic growth,
  **PASS** (structural at this tier, as in stage 1; the non-trivial energy gate remains
  the engine stage where hinge torque feeds back).
- **Cadence brake vs ω** (up-sweep): 96.8–100.5% of free-run across [π, 4π], no
  systematic trend — the brake is duty-limited, not ω-limited (consistent with the
  saturated load channel). COT anchor remains the engine stage's experiment (needs mass
  and stride distance; W_stride reported, not judged, per the packet).

## Contradictions / notices

1. **The surrogate's N0 derivation did not transfer** — it normalized the *peak* of a
   channel whose useful statistic is the *braking-rate maximum* M. Any future load
   channel (engine port) must normalize on M, not P. Recorded so the engine stage does
   not re-pay for it.
2. **The first press window accelerates the phase** (cosφ < 0 under load there) — the
   packet's picture "load brakes the stance limb" is only half the channel on this
   substrate: load *pushes* the phase through early stance and *brakes* it through late
   stance. The Owaki form admits this (the cosφ factor), the packet's prose does not say
   it — noted for the packet's next amendment.
3. **P4 was wrong about WHERE the transition would come from.** The derivation of κ*
   (sensitive band = maximal braking without stall capability in the sweep) is confirmed
   at every checkpoint (F1/F2/F3 PASS), but its corollary prediction — low-end
   marginality destabilizing the walk near π — failed: stride-averaged braking (~2%) is
   what governs the phase, and it is nowhere near marginal anywhere in [π, 4π]. A
   transition needs the *average* channel near the boundary, which is the ×0.6–×1.0 gain
   regime — where the reference walk itself is marginal or parked (measured), so there
   is no clean walk to transition *from*. On this substrate the Owaki form's transition
   regime and its walk regime do not overlap at any gain. That is the sharpest statement
   of why Δω_h = 0 here, and it is a statement about the packet's model, not about the
   measurement.
4. **What did change vs the surrogate (the re-run was not a null result):** bands
   TIGHTER with real λ (0.736 vs 1.018) — the load carries the L/R press asymmetry into
   the phase statistics and the coupling absorbs it *less* noisily than the surrogate's
   analytic stance proxy; the diagonal lags moved +0.252 → +0.269 cyc (real channel
   content, inside band); the cadence brake dropped 3.6% → 0.8%; stance correlation is
   now mechanical (+0.54, honest double-peak shape) instead of definitional (the
   surrogate's N was *built* from −sinφ). The G2 bands above are the port's new
   acceptance bands for the real-load engine stage.

## Falsifier table (every verdict, honest)

| # | Falsifier | Verdict |
|---|---|---|
| F1 | κ*/κ_stall ∈ [0.19, 0.30] (derivation explains the ×0.25 working point) | **PASS** — 0.2405 = 0.200 (sweep placement) × 1.202 (dynamic range P/M) |
| F2 | ×0.60 boundary run marginal (braked, advancing — not parked, not free) | **PASS** — 1.010/1.004 Hz (19% brake), Σσ 6.00, R 0.436 |
| F3 | bands lock at κ* (R ≥ 0.9, drift < 5σ_band) | **PASS** — min R 0.978, max drift 0.011 rad, Σσ 0.736 (tighter than surrogate) |
| F4 (packet) | lag graph constant within σ_band across [π, 4π] ⇒ no transition | **FIRED** — Δω_h = 0, max jump 0.108 rad, R ≥ 0.900 everywhere, both directions |
| P4 (mine) | low-end marginality transition near π | **FALSIFIED** — 98.2% of free-run at π, all pairs locked; average (not peak) braking governs |
| G5 | no energy pump: E_mech bounded | **PASS** — 50.815 → 50.211 (structural at this tier) |
| G5 | W_stride reported, COT anchor | **REPORTED** — 580.30°/stride (0.04% off analytic); anchor engine-side |

## Ready for the engine port (real-load stage) / what it must NOT promise

- The load law: estimator B at κ* = π/(σ·M) with M = max_t(N·cosφ) from the channel's own
  reference stride (κ* = 2.7506e-4 for the current channel; re-derive M if the drive or
  band changes). Normalize on M, never on the peak.
- The acceptance bands: the G2 table above (`.tmp/gait_load_out/bands_load.json`).
- The deterministic solve and its 0-ULP gates: `fae174a0` (`.tmp/contact_ref.py`).
- **Do not promise the ω-transition.** With this Owaki form on this substrate Δω_h = 0
  with real λ (F4). The transition candidates are named (velocity-carrying load,
  load-dependent coupling, swing/stance drive asymmetry) — each is a membrane of its own,
  none is built.
