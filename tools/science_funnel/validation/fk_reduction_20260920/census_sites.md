# CENSUS SITE TABLE — GaitWalker::evaluate call sites at 4a241439 (FROZEN with PREREG)

Every `evaluate(` occurrence in `ChimeraEngine/engine/gait_controller.hpp` at
4a241439 (verified by exhaustive grep; line numbers at this commit). The pinned
tickcost counter (`fk.evaluate`) scopes the WRAPPER at line 616 — therefore only
wrapper calls count against 86549/302. Line 2015 calls `model_->evaluate`
DIRECTLY (constructor, once per walker, outside every tick) and is NOT part of
the pinned counter — counted separately as S_CTOR for completeness.

| site | line | source context | executed |
|------|------|----------------|----------|
| S_MECH | 617 | `mechanical()` | reset (e_ref_) + any caller |
| S_CAP | 1110 | `capture_paws()` | once at entry capture |
| S_FORE | 1223 | `update_fore_clock` non-converged branch | per call |
| S_LAWFE | 1564/1614/1643/1677 | `have_fe` lazy evals in the controller laws | per first need |
| S_RATE | 1713 | `rate()` entry | 1 per rate() call |
| S_FSE0 | 1764 | `free_step` plane check (e0) | 1 per free_step (walk: contact_&&mu_>0) |
| S_FSP0 | 1781 | `free_step` p0 = evaluate(start) | 1 per free_step |
| S_FSP1 | 1781 | `free_step` p1 = evaluate(end) | 1 per free_step |
| S_IMP | 1785 | `impact()` base | 1 per impact() call |
| S_PCEC | 1843 | poscorr ec (unconditional inside `if(contact_)`) | 1 per impact() call |
| S_PCUB | 1846 | poscorr u_before | per poscorr fire |
| S_PCAR | 1847 | poscorr arows (per pen point, loop) | per fire x pen points |
| S_PCDU | 1856 | poscorr du (AFTER q correction) | per poscorr fire |
| S_TR1 | 1885 | TRACE build only (advance depth dump) | trace builds |
| S_ES | 1890 | advance estart (post-impact start) | per entry not caught-recursing |
| S_EE | 1905 | advance eend (integrated end) | per entry reaching it |
| S_TR2 | 1917 | TRACE build only (clamp dump) | trace builds |
| S_PIN1 | 1938 | clamp u_pin: evaluate(pinned) | per clamp |
| S_PIN2 | 1938 | clamp u_pin: evaluate(start) | per clamp |
| S_CROSS | 1951 | crossing gap require | per contact event |
| S_BISECT_GAP | 1909 | `gap_of(evaluate(free_step(...)),k)` — the contact-bisection probe's OWN evaluate of each probe state | 1 per bisection iteration (AMENDMENT 1 — see below) |
| S_CTOR | 2015 | constructor — DIRECT model_->evaluate (NOT in the pinned counter) | once |
| S_RESET | 2235 | reset touching_prev_ + initial-penetration require | once per reset |
| S_REFLEX | 2278 | step() reflex-clock stage | 1 per tick |
| S_HULL | 2643 | step() support-hull stage | 1 per tick |
| S_SAT | 2656 | step() saturation census (paws_captured_) | per tick after capture |
| S_STATUS | 2701 | status() | 1 per tick (harness) |
| S_U0 | 2751 | status() ledger u0 | 1 per tick (harness) |

## CALL-SITE COUNTERS (the same instrument also bumps before free_step/impact/
## advance CALL SITES, to close the event structure)

| counter | line | meaning |
|---------|------|---------|
| C_FS_MAIN | 1892 | free_step(start,h) — the substep's main integration |
| C_FS_DRV | 1903 | free_step(start,mid) inside the 42-iteration DRIVE-stop bisection |
| C_FS_CON | 1909 | free_step(start,mid) inside the 42-iteration CONTACT bisection |
| C_FS_CROSS | 1950 | free_step(start,hit) — contact-event crossing state |
| C_FS_WALL | 1954 | free_step(start,hit) — drive-wall crossing state |
| C_FS_TRACE | 1942 | TRACE build only |
| C_IMP_ENT | 1888 | impact() at advance entry |
| C_IMP_PIN | 1948 | impact(pinned) — clamp path |
| C_IMP_CROSS | 1951 | impact(crossing) — contact event |
| C_IMP_WALL | 1955 | impact(wall_state) — wall event |
| C_ADV_TRIAL | 2665 | the substep trial advance |
| C_ADV_BISECT | 2675 | store-bisection advance (40-iteration, per violating drive) |
| C_ADV_RETRY | 2679 | post-scale retry advance |
| C_CAUGHT | 1889 | caught-impact recursion (2 child entries each) |
| C_CLAMP | 1912 | the hit<=1e-12 clamp branch |
| C_EVT_CON | 1950 | contact-event resolution |
| C_EVT_WALL | 1954 | wall-event resolution |

## CLOSED-FORM IDENTITY (the reconciliation target)

  Sum(SITE counters over the walk) MUST equal the tickcost fk.evaluate hits
  (86549 over 302 ticks = 286.586/tick) EXACTLY — same wrapper, same run.

  Structural identities graded at the PREREG tolerance (+/-5 evals/tick):
    R == 4 x F                (source line 1766: exactly four rate() per free_step;
                               measured 35520 == 4 x 8880 EXACT)
    F == C_FS_MAIN + C_FS_DRV + C_FS_CON + C_FS_CROSS + C_FS_WALL (+C_FS_TRACE)
    I == C_IMP_ENT + C_IMP_PIN + C_IMP_CROSS + C_IMP_WALL
    E == S_RATE + S_FSE0 + S_FSP0 + S_FSP1 + S_IMP + S_PCEC + S_PCUB + S_PCAR
         + S_PCDU + S_ES + S_EE + S_PIN1 + S_PIN2 + S_CROSS + S_MECH + S_CAP
         + S_FORE + S_LAWFE + S_REFLEX + S_HULL + S_SAT + S_STATUS + S_U0 + S_RESET
    with the structural predictions:
    S_RATE == 4F;  S_FSE0 == S_FSP0 == F (walk: contact+friction always);
    S_FSP1 == F;  S_IMP == S_PCEC == I;
    S_ES == S_EE == (entries reaching them — from C_CAUGHT and the event counts).

## AMENDMENT 1 (2026-09-20, post-first-census — F1 FIRED AND RESOLVED)

The frozen table above MISSED one site: line 1909's contact-bisection probe
carries its own `evaluate(...)` of each integrated probe state (the original
read "no direct evaluates" for the event loops — wrong for the CONTACT loop;
the drive-stop loop at 1903 genuinely has none). The first census run measured
the site sum at 80333 vs the pinned 86549 — a 6216 deficit — and the lane's own
call counter C_FS_CON measured EXACTLY 6216 contact-bisection probes. F1
(fires: "find which side is wrong") resolved: the MEASUREMENT was exact on both
sides; the SOURCE READING (this table) was wrong by one site. The instrument
was amended (S_BISECT_GAP), rebuilt, and re-run ×2: the site sum is now 86549
EXACT, matching the pinned counter to the hit. The pre-amendment runs
(census1/census2) remain in raw/ as the F1 evidence; census3/census4 carry the
amended reconciliation.
