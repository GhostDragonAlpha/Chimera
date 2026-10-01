# A1_XPBD DIAGNOSTIC — the piston table and the modal estimate, measured on the live world

**2026-09-14.** Agent A12-xpbd-prereg. Everything here was computed by
`tools/xpbd_diagnostic.py` (re-runnable) against the LIVE engine at
127.0.0.1:8107, GET-only (`/tick_state`, `/verts`, `/topology`), ticks
3,197,795, sealed=True, 4 cells, conserve −0.000117%. Raw numbers:
`diagnostic_results.json`. The preregistered design that consumes these
numbers is `PREREG.md`; the increment plan is `DESIGN.md`.

The physics being sized is Astra's stability gate for the coupled
XPBD volume solve (Astra is the source of truth for this lane, cited in
`PREREG.md`):

    eta = h * omega_max,   omega_max^2 = lambda_max(M^-1/2 K_tangent M^-1/2)
    K_water ~ J_V^T diag(1/(kappa V0_i)) J_V
    compliance alpha_i = kappa V0_i,  kappa = 4.6e-10 Pa^-1 (B = 1/kappa = 2.174 GPa)

kappa is ALSO the engine's own constant (`kappa_ = 4.6e-10f`,
`membrane_tick.hpp:206`, "kappa = water at 25 C") — Astra's answer and the
shipped code agree on the constitutive law `dP = -dV/(kappa V0)` to the last
digit. Explicit integration at h = 1/300 s demands omega_max < 600 rad/s
(f < 95.5 Hz). First diagnostic: the piston mode, eta^2 = h^2 A^2 / (kappa V0 m_eff).

---

## THE MODEL (stated, per Rule 0 — a membrane, not a fact)

The four sealed cells are the y-BANDS of the body solid (each seal cut is a
plane y = p_i; a cell is the solid between its bounding planes, closed by the
seal caps). The live `/topology` mesh is closed AS A WHOLE (divergence sum =
13.824538 m^3 vs live V_whole 13.824600, −4.5e-6 relative) but the seal caps
are internal to the engine's cell sums — they are not in the shared triangle
list. So the measurement instrument is a SLICER: triangle-plane intersection
gives oriented segments (each oriented by t = n x y_hat, globally consistent),
and since the polygon turns at every crossing point the segments tile the
cross-section boundary exactly once; the shoelace sum over ALL segments is the
net enclosed area. No loop chaining, no nesting tests — touch points cannot
break it. From A(y):

    V_cell = integral of A(y) dy over the band        (Route 1, validates the chain)
    dV_cell/dp = A(p) at a bounding plane             (the PISTON IDENTITY — Leibniz:
       the piston Jacobian row IS the cut cross-section area)

m_eff: the body carries rho = 1000 kg/m^3 on the sealed volumes (13.8245 m^3
-> 13,824.5 kg; our lumped per-vertex masses from the face tets sum to
13,824.5 exactly). The engine's DOF are joints + one rigid root; vertices are
skinned, so a joint drags a SUB-BODY. For the ring-piston at plane i the
effective mass is the REDUCED mass of the two sides,
mu_i = m_below*m_above/(m_below+m_above) (free-free, conservative). The
grounded variant (lower side planted — the balance rung's configuration,
m_eff = m_above) is reported alongside.

---

## ROUTE 1 — volume integrals vs the live law (the validation)

V_cell by midpoint integration of A(y), 1.25 mm slices:

| cell | band (ylo, yhi) | V_integral | live v0 | rel err |
|---|---|---|---|---|
| 0 feet | (−0.0195, 0.338) | 0.287915 | 0.287914 | +3.7e-6 |
| 1 calves | (0.338, 1.903) | 0.334577 | 0.334578 | −2.2e-6 |
| 2 thighs/hips | (1.903, 3.415) | 0.693005 | 0.693006 | −7.9e-7 |
| 3 torso | (3.415, 9.9712) | 12.572795 | 12.509100 | +5.09e-3 |

Three of four cells match the engine's own volumes to ~2 parts per million —
the slicer, the band model, the units and the winding are all pinned to the
live law. Cell 3 (the 6.5 m torso) integrates 0.51% high; that cell is the
least sensitive input to every number below (its eta is the smallest), and the
error is conservative in the direction that matters nowhere — but it is
reported, not hidden.

## ROUTE 2 — the cut-plane areas (the piston areas)

A(p_i) at the three cut planes, with ±1 mm brackets (the area field is smooth;
bracket spread 0.2–0.6%):

| plane y | A (m^2) | A at −1 mm | A at +1 mm | boundary segments |
|---|---|---|---|---|
| 0.338 (ankle) | **0.175356** | 0.176065 | 0.174656 | 128 |
| 1.903 (knee) | **0.254922** | 0.254951 | 0.254891 | 104 |
| 3.415 (hip) | **1.099935** | 1.099706 | 1.100166 | 388 |

The arithmetic for plane 0.338, stated plainly: 36,630 triangles, those with
vertices on both sides of y = 0.338 straddle it; each contributes one segment
of the slice polygon in (x, z); 128 segments; A = |(1/2) SUM (x1*z2 − z1*x2)|
over them = 0.175356 m^2. That is both ankles' cross-section at the ankle
band — two limbs of ~0.088 m^2 each on a ~10 m tall, 13.8 m^3 body.

## ROUTE 3 — the FD numeric probe (the engine's own doctrine, with an honest limit)

The engine's numeric-probe doctrine perturbs and measures dV per cell. Our
faithful mesh-representable piston velocity field is a linear-taper kernel
u(y) = delta*(1 − |y−p|/0.05 m) inside a 5 cm band, delta = 1e-4 m, central
difference; dV measured by re-slicing a local window:

| plane | J_below = dV_below/dy | J_above | Leibniz A | probe/A |
|---|---|---|---|---|
| 0.338 | +0.16539 | −0.16539 | 0.17536 | 94.3% |
| 1.903 | +0.00068 | −0.00068 | 0.25492 | 0.3% |
| 3.415 | −0.00354 | +0.00354 | 1.09993 | 0.3% |

The probe CONVERGES at the ankle plane (94.3%, the shortfall is the taper
averaging over a curved, 5 cm-wide band) but under-samples planes 1.903 and
3.415: only 50 and 246 vertices of 18,459 lie within 5 cm of those planes —
the seal loops there are not vertex-dense, so NO vertex-space probe can
recover the piston area. This is a real finding about the world's sampling,
not a defect of the probe: the piston Jacobian on this mesh is measured by the
validated slicer (Route 2, pinned to the live volume law by Route 1 at 2 ppm),
and the probe is kept as the convergence witness where sampling allows it.
Antisymmetry of the trade (dV_below = −dV_above) held to 0.3–8.7%.

---

## THE PISTON TABLE (Astra's first diagnostic, per cell)

eta^2 = h^2 A^2 / (kappa V0 * m_eff), h = 1/300 s, kappa = 4.6e-10 Pa^-1.
Governing plane per cell = its bounding plane with the larger A^2/mu.
Arithmetic shown for the governing cell (cell 2):

    omega^2 = A^2 / (kappa V0 mu) = 1.099935^2 / (4.6e-10 * 0.693006 * 1190.32)
            = 1.209857 / 3.79358e-7 = 3.189e6  ->  omega = 1785.6 rad/s
    eta = h*omega = 1785.6/300 = 5.952  (> 2: OUTSIDE the explicit bar)

| cell | V0 (m^3) | plane y | A (m^2) | mu_reduced (kg) | omega (rad/s) | f (Hz) | eta | verdict (eta<2) |
|---|---|---|---|---|---|---|---|---|
| 0 feet | 0.287914 | 0.338 | 0.175356 | 281.9 | 907.5 | 144.4 | **3.025** | OUTSIDE |
| 1 calves | 0.334578 | 1.903 | 0.254922 | 594.5 | 842.8 | 134.1 | **2.809** | OUTSIDE |
| 2 thighs/hips | 0.693006 | 3.415 | 1.099935 | 1190.3 | 1785.6 | 284.2 | **5.952** | OUTSIDE |
| 3 torso | 12.509100 | 3.415 | 1.099935 | 1190.3 | 420.3 | 66.9 | **1.401** | INSIDE |

Grounded variant (foot side planted, m_eff = m_above): eta = 0.437 / 0.596 /
**1.836** / 0.432 — all inside the bar, but the hip-bounded thigh cell sits at
92% of it, which no safe design budgets against.

## THE MODAL ESTIMATE (coupled coarse K_water, vs the 600 rad/s boundary)

Astra's K_water ~ J_V^T diag(1/(kappa V0_i)) J_V on the three ring-piston
directions. J (4 cells x 3 planes), from the validated slicer via Leibniz
(each ring direction trades the two neighboring cells' volumes — the sum stays
conserved, matching the live conserve_pct = −1.2e-6%):

    J = [ +A0   0    0  ]      A0 = 0.175356 (ankle)
        [ -A0  +A1   0  ]      A1 = 0.254922 (knee)
        [  0   -A1  +A2 ]      A2 = 1.099935 (hip)
        [  0    0   -A2 ]

K = J^T S^-1 J with S = diag(kappa*V0) (3x3, in N/m per unit ring
displacement):

    K = [  4.320e8  -2.905e8    0        ]
        [ -2.905e8   6.261e8   -8.796e8  ]
        [  0        -8.796e8    4.005e9  ]

M = diag(mu) = diag(281.9, 594.5, 1190.3) kg. omega_max^2 =
lambda_max(M^-1/2 K M^-1/2):

    eigenvalues omega^2 = [3.798e6, 1.860e6, 2.917e5] rad^2/s^2
    omega_max = 1949.0 rad/s  (f = 310.2 Hz)

The coupled mode is 9% STIFFER than the stiffest single-piston cell
(1785.6 rad/s) — the cells are chained through shared rings, and the coupled
mode loads springs in series/parallel across the knee and hip cuts at once.

## VERDICT

    Explicit bar at 300 Hz:  omega_max < 600 rad/s.
    Measured:                omega_max = 1949.0 rad/s — exceeded 3.25x.
    EXPLICIT AT 300 Hz FAILS on this world.
    Required substeps: n >= ceil(eta/2) = ceil(6.497/2) = 4
    (h/n = 8.333e-4 s; residual eta = 1.62 < 2, 23% headroom).

The one-line prereg falsifier this feeds: the coupled XPBD volume solve at
n = 4 must stay bounded under a probe press that diverges the explicit update
at n = 1 — with the reference model's piston-mode frequencies matching
omega = [907.5, 842.8, 1785.6, 420.3] rad/s (and the coupled 1949.0) within
±10%. See `PREREG.md`.

 (Agent: A12-xpbd-prereg)
