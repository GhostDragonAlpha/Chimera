# LESSON ONE: "THE FALL" — report (lane lesson-one-fall-20260920)

Date: 2026-09-22 · Base: 2c7f9b08 (origin/master tip, INTEGRATION PASS 6) ·
Worktree: E:/ChimeraWork/buffy-lesson-agent · Agent: lesson

## What was asked

The physics-teaching game's first lesson: the player watches the REAL
CT-derived monkey body FALL, land, and settle — and the physics that moved
it becomes VISIBLE (the project law: all invisible elements should be seen
when put in motion), every displayed number traced to the engine's own API.

## Result: ALL FALSIFIERS PASS, 3/3 identical confirming runs

**The lesson's measured minute** (worst of three):

| moment | measured | budget |
|---|---|---|
| page load | 0.18 s | — |
| first rendered body frame | 0.76 s | — |
| engine ready (page's own state) | 1.11 s | — |
| **the stranger's own F press, server-acked** | **1.24 s** | — |
| landed (the engine's verdict) | 6.12 s | **60 s** |
| lesson UNDERSTOOD (all three beats + banner) | 6.32 s | — |

**The physics, visible and true:** the two bars are the lesson — FLOOR HOLD
(the engine's own `g_contact_n`) vs WEIGHT (m·g = 135,618.345 N, banked
membrane_tick constants). Falling: hold 0 N while the body moves at up to
4 m/s against an unchanged weight. The catch: the hold rises to ~131,867 N
and spikes past the weight (the engine's cap, honestly scaled). Rest: hold
== weight to **0.0003%**. The three teaching lines are driven by the
ENGINE's phases, never a timer; what the player understands after 60 s:
*things fall because of gravity, land because of contact, and rest where
the forces balance.*

**The law's own constants, reproduced live on the page:** terminal descent
**0.2237 m/s vs the banked m·g/c = 0.2237 — to four decimals, every run**
(the body visibly reaches the drag law's fixed point mid-air); landed at
the derived attractor −(m·g/k)−ymin = 0.124641 (measured 0.1244–0.1248).

**Zero errors:** on-page beacon 0 and harness console 0 in all three runs,
through boot, fall, and settle. All 9 named keys verified by effect.

## What shipped

- `tools/lesson_shell/lesson_server.py` — one-command boot
  (`run_lesson.ps1`, 1.7–5.1 s to answers); owns its own engine on a free
  port; boots THE REAL CT BODY by reusing the slice's `scene_boot.py` as a
  module (the slice page untouched — that lane owns it).
- `tools/lesson_shell/index.html` — the lesson: guide, keys card, live
  force bars, height/speed numbers, the root_y trace with the attractor
  dashed in, phase-driven teaching lines, H help, error beacon, serialized
  polling with timeouts (the stranger lane's hardening, inherited).

## The honest amendments (each earned BEFORE its confirming run; every RED kept)

The prereg's original fall-shape bars treated two quantities as constants
that are actually ONE discretization draw: the launch spike (the engine's
contact cap integrated over ~1 tick) and the apex (its ballistic integral —
runs with a higher spike have a higher apex). Ten realizations: spike
3.5455–3.9742 m/s, apex 0.8945–0.9702 m; the banked 3.6792/0.9009 are
single draws of the same classes. **The lesson now bars the two LAW
constants — terminal velocity and the attractor, reproduced exactly — and
reports the spike/apex classes in full.** The ten RED artifacts that drove
each amendment are kept beside the receipt, along with three product bugs
the falsifiers caught (a status poller never started, a phase that never
advanced, a tuple sent as HTTP bytes) — each fixed, none hidden.

## Provenance

Prereg `record.md` committed before any code (e2fee0e5); receipt
`receipt.json`; instrument `walkthrough.js` + `run_walkthrough.ps1`;
confirming runs `lesson_walk_185714_{1,2,3}.json` + screenshots. Bundled
chromium only (MACHINE_FINDINGS). Branch `lane/lesson-one-fall-20260920`
only; master untouched.
