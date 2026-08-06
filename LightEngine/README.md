# LightEngine

First kernel of the light era: identical points under two forces — a blind long-range DRAW (gravity) and a reading short-range RESISTANCE (EM wall + bond). Mass=1, charge=1, no authored properties.

## Gate commands

```bash
python -m pytest LightEngine/tests -q
python LightEngine/demo_seed.py
```

`demo_seed.py` runs N=4096 from a structureless start, prints cluster metrics and the pre-registered falsifier verdict (PASS / COLLAPSE / DISPERSE / FLICKER), and dumps frames to `LightEngine/output/`.

## v2 notes

- `compute_draw(positions, masses) -> accelerations` is an interface boundary: v2 swaps the direct O(N²) sum for a Barnes-Hut tree without changing callers.
- `compute_resistance(positions, velocities) -> accelerations` is direct-pair with cutoff in this build; a GPU uniform-grid cell-hash neighbor list is the planned v2 acceleration.
- Contact radiation (the successor named in `docs/THE_KERNEL.md`) adds radial damping inside the wall only.  The strength `gamma_w` is a derived constant in `LightEngine/constants.py`, not a free parameter.

Constants live in `LightEngine/constants.py` (FREE dict), declared once and never retuned after a falsifier result.
