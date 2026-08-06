# THE PRINTER — RULE 0 for authored seed structures

*2026-08-06. Operator's directive: we are looking for seed structures that stabilize
into desired form and function — print the matter, then play the 4th dimension and see
what holds. The 3D-printer metaphor made physical: geometry is authored, time is not.*

## STATEMENT (someone could disagree)

A printed form persists only if the print supplies the physics that form needs. A bare
shell of points has no enclosed mass and falls inward (there is no Oort cloud without
a sun); a solid with points not at bond spacing is a liquid waiting to happen. So the
printer is not a sculptor — it is a compiler: it translates a desired form into
positions AND velocities derived from the same force laws that will then judge it.
Authored geometry is the story (allowed); authored force constants are not (never).

## THE THREE CANONICAL PRINTS

1. **CORE+SHELL (the solar system).** A central blob — points at bond spacing r_bond,
   holding fraction f_core of N — plus the rest on a thin spherical shell at radius
   R_shell, each with tangential speed `v = sqrt(G * M_enc / R_shell)` where
   `M_enc = f_core * N` is the enclosed mass. The orbital speed is DERIVED from the
   draw law; a shell without it implodes, a shell above escape speed evaporates.
   The printed numbers (f_core, R_shell) are story, declared before the run:
   f_core = 0.5, R_shell = 4.0 lu.
2. **DISK.** Same orbital law, flattened to a plane of thickness ~ r_bond — the form
   that angular momentum sculpts anyway. Declared: R_disk = 4.0 lu.
3. **LATTICE (condensed matter).** Points on a simple cubic grid at spacing r_bond,
   small thermal velocities (sigma = 0.01 * v_bond where
   `v_bond = sqrt(K_BOND * r_bond)` is the derived bond energy scale) — tests the
   bond spring as a solid. A 16^3 = 4096-point crystal, no free numbers at all.

## PREDICTION (not yet measured)

Printed forms whose velocities are derived from the force laws persist through the
observation window (10 t_ff of the printed system's own free-fall time):

- CORE+SHELL: shell radius mean stays within 50% of R_shell and its dispersion stays
  thin (shell does not implode, evaporate, or smear into the core); the core stays
  one bound cluster.
- DISK: same radius persistence; the disk stays thin (z-dispersion < 25% of R_disk).
- LATTICE: bond retention (fraction of points whose nearest-neighbor distance stays
  within [r_wall, r_c]) stays above 50%; the crystal holds its extent.

## FALSIFIER (named before the runs)

Any printed form that dissolves within its window — shell radius off by >50%, disk
puffed, lattice bond retention < 50% — refutes the claim that this form is an
attractor of THIS force pair (draw + softened wall + bond + contact radiation) at
THIS printed geometry. The verdict attaches to the force laws as much as to the
print: a universe whose only two forces cannot hold a solar system is a fact worth
knowing before a game is built on them. The successor, if refuted: the modifier M —
membranes that read their neighbors' type, making bonds selective — which is the
light-era's next membrane after the seed settles.

## THE GATE

```bash
python LightEngine/demo_seed.py --structure core_shell --tag core_shell
python LightEngine/demo_seed.py --structure disk       --tag disk
python LightEngine/demo_seed.py --structure lattice    --tag lattice
```

Standard verdict block still applies (clusters / bound / radius / flicker); print
persistence metrics are reported alongside it.
