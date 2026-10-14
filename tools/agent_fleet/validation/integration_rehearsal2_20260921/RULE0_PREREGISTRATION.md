# RULE 0 PRE-REGISTRATION — INTEGRATION REHEARSAL, ROUND 2

Date: 2026-09-21 (banked BEFORE any merge; commit of this file precedes merge step 1)
Agent: GLM 5.3
Clone: E:/ChimeraWork/rehearsal2-agent (scratch; canonical = git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git)
Branch: agent/integration-rehearsal-2-20260921, cut from origin/master
Master before ANY work: 6946f3b99f04b794bca948a1b2cdc44688c2354d
  (= round-1's "before" AND round-1's "after" — master has NOT moved since round 1;
   every lane that "landed" landed as a BRANCH, none touched master.)

## STATEMENT (disagreeable)

The refreshed lane set (round-1's 11 lanes + the 12 families that landed since) can be
brought onto the walk chain in the dependency order below with ONLY the pre-registered
conflicts (.gitattributes unions, engdet's two instrument files, THE_CHECKLIST add/add),
and the merged walk state reproduces the wave-28 family's banked refusal while the
wiseman pin repair turns round-1's 12 fresh-clone ERRORs into passes.

## PREDICTION (not yet measured)

1. The walk chain has FORKED, not extended: wave-28 (0557fc99) and wave-28b (0759f4b2)
   are SIBLINGS, both with parent d981bc04 (round-1's tip); merge-base(28,28b)=d981bc04.
   The briefing's wave-29 ab60a20b does NOT exist on canonical (ls-remote + local object
   store + all refs, checked). Still "one FF" per sibling arm, but NO single FF reaches
   both waves — the second is a real merge.
2. Wave-28/28b merge is TEXT-CLEAN (file-disjoint: 28 = engine gait_controller.hpp +
   gait_unit.cpp + 3 validation files; 28b = 5 validation files, zero engine files);
   the sibling risk is SEMANTIC (28b's receipts were measured against d981bc04), so the
   post-merge gait_unit run is the arbiter, not the merge exit code.
3. Exactly 3 merge steps will conflict, all pre-registered in round 1 or forced by the
   topology: matter B (.gitattributes, union), engine-determinism (ct_skeleton_layer.py
   take-theirs + skeleton_movie.py split), constitution (docs/THE_CHECKLIST.md add/add
   take-theirs). Plus TWO watched-risk merges that I predict CLEAN only because of
   ancestor containment: record-movie (engine-side content already contained via
   visual/MCP ancestry; own delta touches only walk_movie.py + native/ snapshots +
   validation records) and wiseman-pin-repair + VM (.gitattributes three-way appends —
   pin-repair M's .gitattributes, VM appends visible_monkey rules at EOF; different
   lines vs a 32105f18 base, so auto-union is LIKELY but adjacent-hunk conflict is
   possible; if it fires it is a pre-registered union resolution, not a surprise).
4. Wiseman pin repair (68730eab) merges clean over everything (it branches at aede5de9;
   every other wiseman-family lane inherits those blobs UNCHANGED from aede5de9, so the
   repair is one-sided everywhere) and the 12 test_wiseman_osim fresh-clone ERRORs of
   round 1 become passes on this clone.

## FALSIFIERS (named before the runs)

- F1 MASTER UNCHANGED: `git ls-remote origin refs/heads/master` identical before/after.
  Recorded in .rehearsal2_master_before.txt (6946f3b9…). A changed hash = falsified run.
- F2 EVERY CLAIM BACKED BY A COMMIT: every "clean" claim is a --no-ff merge commit in
  this clone (hashes recorded in merge_log.txt); every conflict claim carries its file
  list and resolution.
- F3 MISSING LANES REPORTED, NOT GUESSED: wave-29 ab60a20b, a "row-readmission" branch,
  and "joint-class records" have NO ref on canonical (measured, checked twice) — they
  are reported missing and NOT substituted. Nearest measured content is cited for
  orientation only: quarantine-forensics 72d02366 (rows diagnosed READ-ONLY, 2
  RECOVERABLE — diagnosis, not readmission) and the Vanhoof citation inside research
  memo 77f3d279 (ancestor of the VM lane; there is no Vanhoof prestage lane).
- F4 WALK STATE: post-merge gait_unit reproduces the wave-28 family's banked refusal
  (receipt_wave28/receipt_wave28b states — measured at run time, compared verbatim);
  drift = finding, not something to tune away.
- F5 NEVER THE SCIENCE_FUNNEL SUITE MID-COMMIT: the root suite runs ONCE, at the final
  committed state; the 15 evidence files it regenerates in-tree are `git checkout --`
  restored BEFORE any further commit (round-1 risk #2).

## THE PRE-REGISTERED SEQUENCE (dependency order, 19 steps)

Round-1 replay (verification phase — tips all verified UNCHANGED on canonical):
  1. chain d981bc04      FF, CLEAN predicted (re-verify round-1)
  2. wave-28 0557fc99    FF, CLEAN predicted (chain extension, sibling arm A)
  3. wave-28b 0759f4b2   MERGE, CLEAN predicted (file-disjoint sibling; F4 arbitrates)
  4. matter B 53affb9c   CONFLICT .gitattributes predicted (contains matter A 2d585c7b;
                         union resolution, round-1 pattern)
  5. reality gate 4d1c0ffa  CLEAN (round-1 verified)
  6. visual 1b08b29d        CLEAN (round-1 verified)
  7. engine determinism ee2dec83  CONFLICTS: ct_skeleton_layer.py (take-theirs, strict
     superset) + skeleton_movie.py (integrator split, round-1 resolution re-applied)
  8. workflow MCP a672b16b  CLEAN (follows visual)
  9. checklist e9c8b394     CLEAN (before constitution)
 10. constitution c0e130c5  CONFLICT docs/THE_CHECKLIST.md (add/add, take-theirs)

New-lane phase (the lanes that landed since round 1):
 11. wiseman-pin-repair 68730eab  CLEAN predicted (supersedes round-1's wiseman step;
     contains fc45106c + aede5de9; .gitattributes append watch). TEST after: the
     wiseman osim battery must PASS on this fresh clone (round-1 risk #1 resolved?).
 12. quarantine-forensics 72d02366  CLEAN predicted (supersedes round-1's adapter step;
     contains adapter bbbc4d67 + guimaraes 2098797b; additive dirs)
 13. pennation-correction 37d053ac  CLEAN predicted (sibling of 12 above 2098797b;
     additive pennation_correction dir)
 14. deposit-mass 5f54a161  CLEAN predicted (W1 arm tip; brings pulley 376fc92b +
     hind-torque b17cbf6c + ankle-arms b15ff31e + k-forensics 5a5914b3)
 15. ankle-unblocked-statics 90636814  CLEAN predicted (W1 second arm; brings
     measured-caps eab707f5; disjoint validation dirs from 14)
 16. record-movie 0d78e6d6  CLEAN predicted (brings skeleton-movie ef02772d + the
     walk-movie prestage 6ff615d3 + the legibility/record-walk chain; base vs HEAD =
     MCP tip; engine-side one-sided-ours)
 17. visible-monkey-intake ebbe814d  CLEAN predicted except .gitattributes WATCH (brings
     the arm-architecture/Vanhoof memo 77f3d279)
 18. P6 13d7c31e  CLEAN predicted (base = matter A via matter B; brings axial-adjacency
     3539fdb9 + hip-bond 1dc38688 + articulation-semantics 7b752929 + hip-pivot 427e9d07;
     new docs/THE_ARTICULATION_LAW.md)
 19. tarsal-cycle-pivots cf1857c2  CLEAN predicted (one commit on 18; M matter A's
     infant_skeleton.body.json one-sided)

Round-1 lanes SUPERSEDED (brought by their descendants, not merged separately):
  research memo fc45106c (ancestor of steps 11-17), wiseman aede5de9 (ancestor of 11),
  adapter bbbc4d67 (ancestor of 12/13). Round-1 steps 9-11 collapse into steps 11-13.

NOT LANDED on canonical (reported, per F3): wave-29 ab60a20b; "row-readmission" branch;
"joint-class records"; a "Vanhoof prestage" branch. matter B is PRESENT (53affb9c —
note: round-1 recorded the tip as "53aff9f9c"; the actual tip is 53affb9c, one hex pair
different — the round-1 receipt had a transcription slip; measured here from the ref).

## TEST DELTAS pre-registered

- T1 after step 3: gait_unit MSVC build + run → refusal state must equal the wave-28
  family's banked receipt state (F4).
- T2 after step 11: wiseman osim battery on this fresh clone → round-1's 12 ERRORs
  must now pass, else the pin repair did NOT survive integration (falsified claim).
- T3 at final state: creature_graph tests; gait_unit final walk state; engine full
  build (visual+engdet+record-movie engine state must LINK); science_funnel root suite
  ONCE (F5 protocol), with the round-1 pre-existing 16-error class expected unchanged.

If the measured conflict set is EXACTLY the pre-registered set, the integrator's map is
confirmed. Any extra conflict, or any "clean" that fails, is a FINDING reported as such.
