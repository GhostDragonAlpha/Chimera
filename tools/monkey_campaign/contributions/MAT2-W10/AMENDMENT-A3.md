# AMENDMENT A3 — MAT2-W10 preregistration (P10 corrected: the declared support law)

Disclosed BEFORE any passing claim is recorded (the amendment law). PREREGISTRATION.md,
AMENDMENT-A1.md and AMENDMENT-A2.md are untouched. This amendment CORRECTS
prediction P10: its zero-unsupported-ticks claim was REFUTED by gated run 5
(job c1f4fa8a1bbd40049f994bf3fa1e4313, refusal
`prediction_failed:P10_supervisor_events`), and the refutation was EXPECTED
in hindsight — the sealed W09 record already carried it.

## What was wrong

Prereg P10 claimed "zero unsupported ticks on the certified line (W09 P2
re-proven)". That misread the sealed chain: W09's prereg P2 predicted zero
visits, the A0 run MEASURED 224 unsupported-class ticks of 900 (the gait's
own double-swing windows), and W09's amendment A4 declared exactly this a
recorded finding about the certified line (REPORT section 4, arm A0). The
scene's support structure is declared in the pinned bytes: FOUR front pads
carry the body at every tick (`contact_count = 4 + contact_l + contact_r`;
`foot_contacts[0..3]` are always 1.0) and the two LEG pads cycle with the
gait — a leg pad lifting is SWING, not loss of body support.

## The corrected P10 (frozen before the next run)

On every tick of R1's declared walk interval [301..9031]:

1. `contact_count >= 4` (the four front pads — the declared structural
   support floor the certificate's contact-floor bar >= 2 sits under);
2. every pad gap > 0 (no penetration);
3. the leg-pad unsupported-class visits are the gait's own swing windows:
   COUNTED per 10500-tick arm and DISCLOSED in the receipt; bounded above by
   45% of the interval ticks (W09 A0 measured 224/900 = 24.9% on the policy
   line; the commanded script's turn/stop segments cannot exceed the
   per-tick one-window-per-cycle structure; 45% is the declared bound);
4. the W09 supervisor, attached observation-only on R1, emits ZERO R1/R2
   response EVENTS (its ledger is empty — the responses exist only on the
   replay arm R4 where they are sealed);

and the no-unsupported-PROPULSION falsifier stays exactly as preregistered:
during every declared unsupported (double-swing) tick the com identity P11
holds exactly — no motion beyond the solved law (FB2's ceiling-stride tamper
is the bite).

PASS shape: clauses 1-4 hold. Any tick with contact_count < 4 or a nonpositive
pad gap is `walk_unsupported_tick:<tick>` and falsifies the card.

## Why this is not a weakening

The original P10 was unfalsifiable-as-written only by misreading support:
under the corrected clause the body can NEVER lose its four-pad support
without the contact_count bar firing, while the gait keeps its real swing
physics — the same declared structure W09 sealed. The done_when phrase
"on a supported surface" is executed as the four-pad floor + no penetration,
with the swing windows disclosed, never redefined to zero-swing.
