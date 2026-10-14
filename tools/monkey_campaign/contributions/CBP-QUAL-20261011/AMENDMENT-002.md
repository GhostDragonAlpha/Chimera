# CBP-PREREG-001-AMENDMENT-002 — Scoped repair of AMENDMENT-001's E4 drop bound, E1 applicability, window labels, and supersession sweep

Status: COMPLETE, UNPUBLISHED. Authored 2026-10-11 by the Lieutenant
(`wk-cbp-prereg` line, one-writer path). This is the scoped prospective
repair demanded by the fresh endorsement verdict `CHANGES_REQUIRED` on
AMENDMENT-001 (rev `2be48e44`, published as PR #353 at `81ee012c`). ZERO
runs were executed before or by this amendment; no observation preceded it,
so CBP-PREREG-001 section 7's amendment law is satisfied prospectively.
`SCIENTIFIC_PREREGISTRATION.md` (sha256
`0f62cbfa3212298eba6972a446998005369208a0caab774fdfa92889253c8dc2`) and
AMENDMENT-001's bytes stand unchanged; this document supersedes ONLY the
four items named in sections 1-4 below. Every other clause of
CBP-PREREG-001 and AMENDMENT-001 stands as reviewed.

Trigger of record: the fresh endorsement review verified the E4 drop bound
of AMENDMENT-001 section 2 against the sealed constraint graph and found it
repeats the exact defect class (L1) the amendment was commissioned to
remove — a frozen kinematic number inconsistent with the sealed dynamics.
The reviewer's recompute (RK4 from the sealed authored inertia
I_pivot = 0.02424 kg·m², mgr/I = 48.5478 s⁻²): on the physically correct
post-C2 trajectory the per-interval bound `0.5·g·T²` is exceeded by the
arm-COM 2.19× on the second checkpoint interval and by the pad-COM
1.48–4.39× — because the bound omits the INHERITED VELOCITY term (the
original P6 had the correct velocity-aware form) and because the pad is not
pivoted at all (springs can pull it downward harder than gravity). Endorsing
as-is would lock a new guaranteed false negative into G4. The failed checks
are preserved against rev `2be48e44`.

Fix choice: option (a) of the required changes — RESTATE the drop bound
velocity-aware, cumulative from segment start, arm-COM only; remove the
pad-COM drop clause. Option (b) (deleting all per-body drop bounds) is
DECLINED: a correct kinematic sanity bound has qualification value the
identity clauses alone do not cover. The C2 scenario, the sealed package
(`9102816d`), the fixture bytes (`d7963115`), and every other frozen number
are unchanged.

---

## 1. E4 restated (supersedes AMENDMENT-001 section 2, bullet E4)

- E4 (drop bound — ARM-COM ONLY, cumulative from segment start): within
  each segment (segments delimited by the C2 window start, every recorded
  joint-limit event, and the C2 window end), the arm-COM cumulative
  vertical displacement over the segment, measured from the segment-start
  state, satisfies

  `drop(T_seg) <= d(0)·T_seg + 0.5·g·T_seg²`

  where `d(0)` is the MEASURED downward arm-COM vertical velocity at the
  segment start (downward positive; if the measured `d(0)` is negative —
  upward — it enters as its negative value, making the bound tighter),
  `T_seg` is the segment duration in seconds, and `g = 9.80665 m/s²`.
  Quantifier: the bound holds from EVERY measured segment-start state, not
  only from rest; it is evaluated per segment, never per checkpoint
  interval. Basis: for the world-pivoted arm the pivot reaction's vertical
  component on the arm is non-negative upward, so the arm-COM downward
  acceleration never exceeds `g`; integrating that acceleration bound from
  the measured segment-start velocity gives the stated displacement bound.
  (An acceleration bound does NOT transfer to a per-interval displacement
  bound unless every gated interval starts at zero velocity — L4 below.)
- The PAD-COM drop bound is REMOVED. The pad is not pivoted: the 9-spring
  network can pull it downward with force beyond its weight, so no
  gravity-derived displacement bound exists for it. The pad's gated
  quantities are E1 (segment identity), the scoped E5 monotonicity, and the
  named contradicting observation "upward COM motion inside the limits
  without a spring term to pay for it."

## 2. E1 applicability restated (supersedes the applicability sentence of AMENDMENT-001 section 2, bullet E1)

E1 (identity, primary gate) applies over **every checkpoint interval of C2
CONTAINING no recorded joint-limit event**, with segments delimited by the
C2 window start, each recorded joint-limit event, and the C2 window end.
The identity is NOT claimed across any interval that contains an event
(those intervals carry E2 event rows instead). This set-membership form
replaces the relational phrasing "strictly between recorded joint-limit
events," which degenerates to an EMPTY applicability set on the
anticipated single-engagement trajectory (the arm pins at the limit and one
event divides the window into two segments, both of which contain
event-free intervals that MUST remain gated).

## 3. Window-table label repair (supersedes the two labeled rows of AMENDMENT-001 section 4)

The two rows' tick ranges and checkpoint lists are UNCHANGED; only the
duration labels were wrong (each window spans 0.15 s, not 0.2 s). Corrected
table (the standing L2 example):

| Window | Tick range | Checkpoints | Count |
|---|---|---|---|
| P1(i) last 3-checkpoint sustained window of phase A (0.15 s) | 1020-1199 | 1020, 1080, 1140 | 3 |
| P1(ii) all of phase A | 0-1199 | 0, 60, ..., 1140 | 20 |
| P3 press bound, last 3-checkpoint sustained window of phase B (0.15 s) | 2220-2399 | 2220, 2280, 2340 | 3 |
| P6/E5 first pre-limit segment | C2 start .. first event | measured; >= 2 required, else NOT EVALUABLE | measured |

## 4. Supersession sweep (amends AMENDMENT-001 section 7's enumeration)

AMENDMENT-001's supersession list is amended to read: "This amendment
supersedes only: P6 (section 2, including section 1's restated C2 V-law
rows), P3's unpowered-window denominator (section 3), the checkpoint
cadence and windowed clauses (section 4), and P4's dangling budget
reference (section 5)." This document (AMENDMENT-002) supersedes only:
AMENDMENT-001 §2 E4 (by §1 herein), AMENDMENT-001 §2 E1's applicability
sentence (by §2 herein), AMENDMENT-001 §4's two window labels (by §3
herein), and AMENDMENT-001 §7's enumeration (by this section). Nothing
else.

## 5. Standing law additions (extend AMENDMENT-001 §6)

- L4. An acceleration bound does not transfer to a per-interval
  displacement bound unless every gated interval starts at zero velocity.
  Frozen kinematic bounds must state their quantifier over the initial
  state and be derived from the sealed constraint graph.
- L5. Freeze window arithmetic as ONE consistent (label, range, checkpoint
  list, count) tuple; derive the duration label from the range, never
  carry it forward from a draft.
- L6. Write gate applicability as set membership over intervals
  ("containing no recorded event"), with window boundaries included in the
  segment set — never as relational phrasing ("between events") that can
  degenerate to an empty set.

## 6. Endorsement scope

G4 remains LOCKED for C2 until this amendment is pinned and published
through the one serialized publication owner and a fresh endorsement
verdict is recorded. The prior endorsement's verified-clean findings (the
per-segment identity architecture, E2 event rows, E3 invariance, scoped
E5, E6 references, the P3 denominator, all NOTE 1 counts, the NOTE 2
envelope, L1-L3) are not reopened by this document; only the four repaired
items require fresh verification. No gated run of any kind has been
submitted.
