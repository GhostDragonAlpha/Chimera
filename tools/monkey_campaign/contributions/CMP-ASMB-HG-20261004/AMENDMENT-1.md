# AMENDMENT-1 -- CMP-ASMB-HG (PKT-G3-ASSEMBLY-HANDGROUND)

Sealed WITH the amended battery, BEFORE the amended rerun (the
prereg-first law; the pairpath AMENDMENT-1/2 pattern). Nothing here touches
WIN_LEDGER or any window; the frozen acceptance criteria are unchanged.

## A1.1 What the sealed evidence showed

Run 455b7c7d (seal 95e5c64d..., job 455b7c7db9cf478ca3c2e65c069f851d):
SC1_counted_once COMPLETED -- every enforced row held, INCLUDING the
per-tick sealed-trajectory parity gates (my SC1 prop_cz matched the
pairpath's published P1.2 prop_cz_trajectory within 1e-12 at every compared
tick) and the P1.1-form support identity at every SC1 tick. The run then
failed at SC3_release tick 14 with
support_identity_broken resid = 0.1641212673000001 and the recorded
decomposition: press_total 0.0, jn_gh 0.0, jn_pg 0.0, records {},
dp_stack_z = -m_prop*g*dt, grav_z_hand None (the hand is REMOVED from the
scene at the declared separation event). The residual is exactly
weight_stack - m_prop*g*dt = m_hand*g*dt.

## A1.2 The finding

The P1.1-form support identity (jn_hand_ground == press + weight stack +
measured dp_z) was enforced on EVERY tick of EVERY scenario. The pairpath
sealed it ONLY over S1's settle window (its rows[5:]), where the prop rides
the hand alone (jn_prop_ground == 0). On a SEPARATED tick the law is the
S4 exact-zero set (no records, W_contact == W_press == 0.0 J exactly, free
fall) -- the support form does not apply. The hand-only LHS is a vestigial
comparison when the prop also carries ground support; the intended law is
the WHOLE-PAIR form (the collaborator's source-level finding, adopted).

## A1.3 The amended enforced law (windows unchanged; 1e-12)

1. SUPPORTED ticks (the declared separation event has not fired): enforce
   the WHOLE-PAIR support identity
       jn_hand_ground_sum + jn_prop_ground_sum
           == measured_applied_press + weight_stack + dp_stack_z
   with the MEASURED applied press (the press dict's own z book, not the
   channel-derived value), window 1e-12. The hand-only residual is RECORDED
   every tick (it coincides with the whole-pair form whenever
   jn_prop_ground == 0 -- the sealed pairpath S1 case).
2. SEPARATED ticks: the S4 exact-zero laws remain the enforced set (no
   records; W_contact == W_press == 0.0 J exactly; free-fall recursion and
   closed form within 1e-9); the support form is recorded as
   not-applicable.
3. Per-contact signed-impulse instrumentation recorded (bounded): per tick,
   per record -- pair key, body ids, kind, mode, jn_Ns, signed z of the
   normal part on each body, tangent z on each body -- plus the hand+prop
   sums against the full-stack external z impulse (the ledger-z identity,
   enforced, window 1e-12).

## A1.4 The falsifiers (constructed triggers; each must bite)

- F-a (press-tamper): on a supported tick, recompute the whole-pair
  identity with the measured press tampered by +1e-3 -> the residual moves
  by 1e-3 >> 1e-12 -> the check FAILS inside the tampered replay. Always
  bites on a supported tick.
- F-b (prop-ground-drop): recompute the whole-pair identity WITHOUT the
  jn_prop_ground term -> bites exactly when the prop carries ground support
  (jn_prop_ground > 0); recorded conditionally with the observed term.
- F-c (tangent-z-drop): recompute the ledger-z stack account without the
  recorded tangent z contributions -> bites exactly when any record carries
  tangent z != 0; recorded conditionally with the observed term.

## A1.5 The SC1 sealed-window claim this amendment certifies

SC1's completed gates from run 455b7c7d (preserved in its runner.log): the
sealed-trajectory parity (my scene == the sealed pairpath S1 scene within
1e-12 per tick) and the P1.1-form identity at every SC1 tick. The amended
battery re-derives both and adds the whole-pair form; the tampered-slip
discriminator (F2) is unchanged.
