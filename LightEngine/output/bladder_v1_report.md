# BLADDER v1 print report

Run: `python -m LightEngine.demo_seed --structure bladder --tag bladder_v1`
Date: 2026-08-07
Seed: 20260806
Dt: 0.0005

## Print geometry

- Total points: 307
- Squeeze plates: 2 x 4x4 = 32 grains (pinned)
- Spherical shell: 211 grains (unpinned, grain_id=1)
- Contents: 4^3 = 64 grains (unpinned, grain_id=2)
- Shell radius r_b: 0.20000
- Shell spacing d_eq: 0.04840
- Derived shell count: 211 (surface area / d_eq^2, then neck hole removed)
- Derived plate separation s0: 0.49680 (= 2 * (r_b + d_eq))
- Derived hold force F_hold: 551.83
- Yield threshold 2*F_hold: 1103.66
- Geometric convergence limit: 0.10000 (2 muscle lattice spacings)
- Neck center: (0.2484, 0.0000, 0.2000)
- Neck axis: (0.0000, 0.0000, 1.0000)

## Verbatim falsifier verdict

```
[bladder] BLADDER FALSIFIERS:
  (a) SEAL      : PASS  force<F_hold samples=26 escapes=0 shell_clust max=1
  (b) YIELD     : FAIL  at tick=15888 force=661.10 sep=0.09999 escapes=0/32 shell_clust max=1
  (c) NECK      : FAIL  escaped=0 in_neck=0 out_neck=0 (bar 0.1000 from axis)
  (d) INTEGRITY : FAIL  post-yield shell_clust max=1 max disp=0.1823 (bar 0.1000)
```

## Squeeze trajectory

The plates converged quasistatically from s0 = 0.49680 inward at the muscle's
5% sound speed (v_plate = 0.05):

- tick 0:    separation 0.49698, force 551.89, shell cluster 1, escapes 0
- tick 7500: peak force 1017.95 at separation 0.30957
- tick 15888: geometric limit reached, separation 0.09999, force 661.10
- No content grains ever escaped the shell radius + d_eq threshold.
- Shell cluster count remained 1 for the entire run.
- Shell grain displacement relative to the print neighborhood rose to ~0.146
  by tick 500 and stayed ~0.16-0.19 through convergence, release, and hold.

After the geometric limit the plates released back to s0 over ~15881 ticks and
held at s0 for 1000 ticks. Force during release fluctuated between ~160 and
~1049, never reaching the 2*F_hold yield threshold while contents were still
contained.

## Neck selectivity

No content grains escaped, so neck selectivity is untested. The recorded count
is escaped=0, in_neck=0, out_neck=0. By the rule "untested = FAIL", this
falsifier fails.

## Shell integrity post-yield

The shell remained a single connected cluster throughout the run, but shell
grains were displaced well beyond the 2-spacing (0.10) bar from their print
neighborhood (max displacement 0.1823 during the post-yield window). The shell
did not rupture, but it did not hold its spherical form.

## Conclusion

Only falsifier (a) SEAL passes. The bladder seals under low pressure, but the
v1 print does not yield contents through the neck before the geometric squeeze
limit, and the shell deforms/collapses rather than staying a closed spherical
mat. This is the honest result for a hollow shell in a universe with no bending
stiffness: the shell stays one cluster but cannot hold its shape against the
plates. A bladder v2 would need a stiffer shell or a parent bulk (the muscle)
to carry the squeeze load instead of the shell itself.

## Output frames

- `LightEngine/output/bladder_v1_bladder_begin.png`
- `LightEngine/output/bladder_v1_bladder_end.png`

## Raw log

`LightEngine/output/print_bladder_v1_log.txt`
