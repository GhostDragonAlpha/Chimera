# SKIN v1 print report

Run: `python -m LightEngine.demo_seed --structure skin --tag skin_v1 --skin-settle-ticks 3000`
Date: 2026-08-07
Seed: 20260806
Dt: 0.0005
Settle ticks: 3000 (derived from sheet flat settling; short settle fails end-settle conform)

## Print geometry

- Total points: 352
- Muscle droplet: 4^3 = 64 grains
- Anchor plates: 2 x 4x4 = 32 grains (pinned)
- Mat: 16x16 = 256 grains (unpinned)
- Derived d_eq_2D: 0.04005
- Derived s0: 0.24814
- Conform band: [0.01500, 0.09840]
- Slide bar: 0.10000 (2 muscle lattice steps)

## Verbatim falsifier verdict

```
[skin] SKIN FALSIFIERS:
  (a) CONFORM   : PASS  end-settle=0.996  stroke min=0.984 (bar 0.5)
  (b) NO SLIDE-OFF: PASS  max drift=0.0047 (bar 0.1000)
  (c) COVERAGE  : PASS  end-settle=1.000 (bar 0.5)
  (d) INTEGRITY : PASS  mat clusters max=1  droplet clusters max=1
```

## Conform summary

The mat begins as a flat sheet one lattice step above the droplet top face,
so only the central grains are in cushion contact at tick 0 (conform = 0.234).
Free settling drapes the outer mat grains down the droplet flanks:

- tick 0:   conform 0.234
- tick 500: conform 0.969
- tick 1000-3000: conform 0.992-0.996
- stroke (extend + converge): conform never drops below 0.984

Coverage of the droplet top-hemisphere surface grains is 1.000 at every
sample, including the initial print.

## Stroke trajectory

The muscle plates were driven at 5% bond sound speed (v_plate = 0.05):

- tick 0:    separation 0.24804 (s0)
- tick 7119: separation 0.35094 (s0 * sqrt(2), extension target reached)
- tick 11235: separation 0.24812 (converged back to s0)

Both the mat and the droplet remained single connected clusters throughout the
entire settle and stroke.  No fragmentation was observed.

## Slide-off check

Post-settle relative COM (mat COM - droplet COM): (-0.0021, -0.0015, 0.0354).
Maximum drift from this baseline during the stroke: 0.0047 lu, well below the
2-lattice-step bar of 0.1000 lu.  The mat does not slide off.

## Conclusion

All four SKIN v1 falsifiers PASS.  The 16x16 mat settles into a conformal drape
on the muscle droplet within ~1000 ticks, remains conformal through the muscle's
extension-to-s0*sqrt(2)-and-back stroke, covers the droplet top hemisphere,
stays in one cluster, and shows negligible COM drift relative to the droplet.
The mat survives the stroke.

## Output frames

- `LightEngine/output/skin_v1_skin_begin.png`
- `LightEngine/output/skin_v1_skin_end.png`

## Raw log

`LightEngine/output/print_skin_v1_log.txt`
