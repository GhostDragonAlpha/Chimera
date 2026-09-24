First action: copy this brief verbatim to E:/PythonChimera/forearm_package/audits/A4_transforms/brief.md (create dir).

ROLE: audit agent (A4) — audit local-to-world transforms and bilateral correspondence.

CAMPAIGN CONTEXT (self-contained): forearm anatomy package to qualify the monkey's physical grasp for climbing. Audit campaign — an external architect (Astra) owns decisions; you produce evidence only. BASELINE (READ-ONLY): E:/PythonChimera/forearm_package/baseline_snapshot/ — code/ (attachment_candidates.py exports numeric per-body transforms R = Bp @ diag(scale) @ Bᵀ, t = fitted_origin, with fitted_pos_global = t + R @ source_pos_local; correspondence.py holds handedness policy preserve|mirror with mirror_plane_normal guard; experiment_transverse_fit.py step A verified reconstruction max err 1.15e-9 m and mirror max 0.63 mm / mean 0.055 mm across the sagittal plane x=0 — these are the CLAIMS you verify), runs/attachment_candidates.json (32 sites: source_pos_local, fitted_pos_global, per-body transforms) + actual_monkey_fit.json + runs/mirror_read.json (may record mirror details), session_reports/anatomy_compiler_05.md §3-4, MANIFEST.json.
NAMING: 32 sites = 16/side; right unsuffixed (BRD-P2), left _l (BRD_l-P2).
FROZEN BOUNDARIES: no edits to the baseline; discrepancies are FINDINGS, never repairs; no architectural decisions.
ENVIRONMENT: Windows, Git Bash; python 3.14 + NumPy; work from your audit dir with PYTHONDONTWRITEBYTECODE=1; copy any baseline module you need to import into your work/ dir first; never write into baseline_snapshot/. No network, no GPU, no git write commands.

OBJECTIVE: independently verify the exported transforms and the bilateral symmetry of the fit.

TASK STEPS:
1. Transforms: for every body carrying the 32 sites (radius, radius_l, and any other bodies involved per the packet), audit R: orthonormality ‖RᵀR−I‖max, det(R) (record sign + what the packet/correspondence says it should be); audit t. Then reconstruct fitted_pos_global = t + R @ source_pos_local for ALL 32 sites; per-site and max/mean reconstruction error vs the packet's stored fitted_pos_global; compare against the 1.15e-9 m claim.
2. Bilateral: pair the 16 right sites with their 16 left counterparts (name mapping strip/add _l; ALSO verify pairing via tendon family identity). Determine the sagittal plane from the fit's own data (mirror_read.json / experiment record; the claim is x = 0 in target world). Reflect right points across the plane; per-pair distance to the left points; max and mean vs claims (0.63 mm / 0.055 mm); full 16-pair table; flag any pair > 20 mm sanity bound.
3. Policy audit: which handedness mode the actual-monkey fit used (preserve|mirror), where it is recorded (quote file+line); whether correspondence.py's mirror_plane_normal guard is consistent with the plane used.
4. Cross-check: reconstruction at packet export precision — note export rounding (report 05 §3: "0.0 at export precision; verified < 1 µm in step A"); state the actual numbers you measure and reconcile.

PREREGISTRATION (frozen): PREDICTION: reconstruction max error ≤ 1e-8 m; mirror max in 0.4–0.9 mm with mean < 0.1 mm; mode recorded explicitly in the fit artifacts. FALSIFIER: any reconstruction error > 1 µm, or any bilateral pair > 20 mm — geometry divergence; report exact numbers.

ACCEPTANCE CRITERIA (verdict each PASS/FAIL/UNCERTAIN): (1) per-body transform audit table (orthonormality, det, origin); (2) 32-site reconstruction errors (max/mean, worst site named) vs claim; (3) 16-pair bilateral table (max/mean, worst pair) vs claims; (4) handedness mode + plane evidence quoted; (5) baseline integrity — paste git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot (must be empty).

OUTPUT CONTRACT: write ONLY inside E:/PythonChimera/forearm_package/audits/A4_transforms/ (brief.md, report.md, scripts/, receipts/, work/). report.md: verdicts per criterion; evidence with file+line+numbers; explicit uncertainty; negative findings preserved; receipts (exact commands + key output). A null result is a result.
STOP RULE: stop when all criteria have verdicts or a dependency is missing — record the blocker and stop. Do not repeat a failed approach more than twice.
