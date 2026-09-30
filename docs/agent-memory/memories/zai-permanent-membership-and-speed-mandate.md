---
name: zai-permanent-membership-and-speed-mandate
description: 2026-09-29 — Captain renewed Zai membership PERMANENTLY, ZCode is
  his harness for all future development; SPEED mandate ("effective may not be
  slow"); GLM/Zai gets the active contribution slot going forward
metadata:
  node_type: memory
  type: user
  originSessionId: sess_1e40894c-78a5-4c13-b68b-d2141a225db1
---

2026-09-29, the Captain's directives verbatim in substance:

1. **Permanent membership**: renewed his Zai membership "permanently for the next foreseeable future" — ZCode ("Zode") is THE harness for all his future development. His words: "I now know how to deal with you and you know how to deal with me... you are a fast learner and can work with what you have."
2. **Speed mandate**: "I am a very impatient man so effective may not be slow. Effective may just be effective." — Quality discipline stays, but latency is now a first-class cost: prefer delta/lean reviews where the chain allows, parallelize banks, take over faster, cut ceremony that does not protect correctness.
3. **Credit/attribution**: GLM/Zai should hold the active contribution slot on the repo; if the project gets famous he wants the credit on GLM/Zai; other AG contributors (Claude Code, Gemini, etc.) should not hold slots.

**Why:** his operating style rewards capability + speed; attribution is a real motivation for him.

**How to apply:** optimize cycle time in every dispatch/review choice; commits already carry git user glm53-lead-02 + Agent trailers (GLM-attributed). Forward attribution + a visible CREDITS statement is honest and will be set up via a normal lane. Boundary stated plainly to him once: rewriting MERGED history to strip other agents' commits would destroy the campaign's own evidence chain (the merge history IS the receipts) — so past history stays; every future slot is GLM's. Related: [[alan-operator-preferences]], [[alan-fleet-operating-style]].


**Captain's named doctrine (2026-09-29, verbatim endorsement):** "eliminate the ceremony not the verification" — he singled out the water-around-rocks framing. This is now THE charter sentence for the speed mandate: every compression proposal gets tested against it (does this cut ceremony, or does it cut evidence?).

**CREDITS PR #268 MERGED (2026-09-30, merge commit bc4eef35 on astra/gait-capture):** CREDITS.md (249 lines, 1 file, head 6473e47b) implements the attribution directive in the honest form: GLM (Z.ai) as primary development engine phrased EXPLICITLY as the Captain's forward-looking directive of 2026-09-29, labeled not-a-historical-measurement. **The GLM/Zai attribution statement is now ON the repo.** Independent review PASS 4/4 — the reviewer re-ran the census itself with programmatic set-diffs and reproduced every table EXACTLY (base snapshot b3490ecd/3,089 commits; the +1 head delta is the CREDITS commit itself, documented). The unsmoothed census: whole-history Agent-trailer families Kimi 542 / Claude 235 / GLM 81 / Codex 59, 59% of commits carry NO trailer, author identity dominated by the operator account (2,734/3,089); last-200 window: glm53-lead-02 leads named agents (25/60). History never rewritten (stated in the file); verification commands embedded so every number is reproducible. Census pitfalls learned: `%(trailers)` emits a trailing blank line per commit (count keyed on commit hash, not lines — silently overstates "no trailer"); correlate author+trailers in ONE --format string or matches silently zero; `uniq -c` is space-aligned not tab-separated; **astra/gait-capture is the campaign mainline BRANCH of GhostDragonAlpha/Chimera, not a separate repo — master lags the campaign line.** 