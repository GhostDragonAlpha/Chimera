# THE SECOND RECORDED SESSION — the physics is live and the picture does not show it

> Goal rung 9: *"re-record with everything above in… F1–F3 all PASS on video."* Recorded
> 2026-08-04, 121 frames across 10 beats, all beats landed. **The recording is the finding, and
> the finding is negative.**

## WHAT THE SESSION LOG PROVES — the world is real and reports itself

Straight from `session_log.txt`, unedited:

```
"touch": "E: pick up the stone (65.1 kg)"
"touch": "the stone -- 65.1 kg of basalt (Quaglio 2020), mu 0.84 = tan(40.03 deg repose)"
"touch": "the pile -- 400 grains of regolith (d50 0.35 mm, 0.06 mg each),
          repose cone 0.84 m tall -- footprint 1.08 m"
```

Every number traces. The stone's mass is basalt density on its measured volume; its friction is
`tan(40.03°)` — the repose angle the granular membrane *emerged*, not a coefficient anyone typed.
The pile's footprint reads **1.08 m**, the same number the HUD proved in the rung-3 session. The
GRAB fires, the load is priced, the drop deforms the pile. **F1 holds: everything on the line
traces to a membrane.**

## WHAT THE FRAMES SHOW — none of it

`04_picked.jpg` (the stone in hand) and `07_pile.jpg` (standing at the pile) both show: **a pale
mannequin on a featureless dark-green plane under a dark blue sky.** No stone reading as rock. No
pile. No vegetation. The carried object is a small grey slab with no material identity; at the
pile beat there is nothing on the ground at all.

**This is F2, stated exactly.** The touch line carries the world; the picture does not. And it is
a sharper statement than the rung-3 blind read could make, because that read had a recorder fault
mixed into it — this recorder is the fixed one, closed-loop, all beats landed. **The remaining
gap is purely render.**

## AND IT DOES NOT REPRODUCE TWO CLAIMS MADE THIS WEEK

Recorded as a disagreement, not an accusation — both were validated in their own instruments and
neither appears in the product:

| claim | its own instrument | this recording |
|---|---|---|
| *M5: stone reads as rock (denser splat sphere)* | PASS | carried object is a grey slab; no rock |
| *M6 membrane 4: 13 blades, the tuft reads as stalks* | PASS | **no vegetation visible in any hero frame** |

A membrane can pass its own falsifier and still not reach the screen — the legibility instruments
measure the object in isolation; the session measures it **at the camera the player uses**, at
that exposure, over that ground. Those are different questions and only the second one is the
game. **Which of the two is wrong is not settled here**; what is settled is that they disagree,
and the disagreement is the next rung's work.

## THE INSTRUMENT DEFECT THIS COST, paid in evidence

`slice_record.py` named its output `slice_session_{YYYYMMDD}` — **date only**. Re-recording on the
same day overwrote the previous session frame for frame, and the path is gitignored, so **the
rung-3/4 session the earlier blind read was taken from is gone.** Not recoverable. My run did it.

Fixed: the name now carries seconds, and an existing directory is **refused**, never entered. A
recording is evidence, and an instrument that overwrites evidence without saying so is the same
species as a witness keeping a stale copy — the failure this project has a rule for.

## STATUS

- **F1 — PASS.** Every published number on the touch line traces to its membrane.
- **F2 — STILL FIRED**, and now with the cleanest evidence yet: a closed-loop recorder, all beats
  landed, physics reporting correctly, and a frame a blind reader would describe as an empty field.
- **F3 — PASS**, by `tools/f3_stand.py` (exit 0). *Not yet on this tape:* the session is driven by
  the Walker mover, so the musculoskeletal stand is proven in its own harness and has never been
  recorded. Goal rung 9 asks for it **on camera**; that bridge is unbuilt and is named here rather
  than glossed.
