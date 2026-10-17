# S0 contract review (step 3.7 Flash, adjudicator)

Artifact: `docs/evidence/mechanism_factory/S0_mechanism_scale_contract.md` (287 lines)
Repo pin: `bd1af446` (working tree).
Reviewer: step 3.7 Flash (independent verification, CPU only).

---

## 1. Similarity check reproduction

**Command run:**
```
cd D:/Chimera-Maintenance/Runtime/local-ai/math-tools
PYTHONPATH="D:/Chimera-Maintenance/Runtime/local-ai/math-tools;D:/Chimera-Maintenance/PythonChimera;D:/Chimera-Maintenance/PythonChimera/tools;D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory;D:/Chimera-Maintenance/PythonChimera/tools/membrane_scale_lab" C:/Python314/python.exe checks_tmp/s0_scale_similarity_check.py
```

**Result:** ALL S0 SCALE-MAPPING CHECKS DONE. Exit 0.

Key reproduced values:
- A (s=1.0, F=0.8): apex_z = -0.2633079630900263 wu, U = 3.2481643966448956 J
- B (s=0.5, F=0.4): apex_z = -0.13165398154501315 wu, U = 0.8120410991612239 J
- Negative control C (s=0.5, F=0.8): deviation = 0.164225 wu > 10 * tol_z (0.000200 wu)

Algebraic identities exact to machine precision (max_abs_error 0.0). Solver-level similarity holds: apex_z(B) = 0.5 * apex_z(A), U(B) = 0.25 * U(A), pin reactions scale by 0.5. Dimensionless collapse eta(A) = eta(B) at Pi = 0.8.

**Verdict: PASS — all seven checks reproduced independently.**

---

## 2. Owner inventory verification

**Law pin hash:** independently computed sha256 of `tools/membrane_scale_lab/surface_energy_reference.py` = `ee9effcfbddad8d02e03f71d414b27da177f0656de535eaab0d76ae39796f0b7`. Matches the record's `law_revision` and the contract's pin. Verified equal.

**Units:** packet `units` = {length: m, force: N, energy: J}. Record `physical_definition.units` identical. Law uses gamma in J/wu² with 1 wu = 1 m. Consistent: energies in J, reactions in N (J/wu = N). No unit mismatch found.

**Duplicate physics:** contract distinguishes `surface_energy_reference.py` (constant-gamma current-area law) from `tools/ca_triangle.py` (signed-area / frozen-normal law). The distinction is documented in the law's header and proven by negative controls in `surface_energy_checks.py`. No duplicate physics found in the inventory table.

**Verdict: PASS — law pin hash correct, units consistent, no duplicate physics.**

---

## 3. Seven gap items verification

All seven items reported in §7 of the contract are real, confirmed by direct inspection of the retained record and cited receipts.

1. **Cross-product unmeasured.** The `load_domain_study_20261017.json` title reads "at scale 1.0". The record's `valid_scales` = [0.75, 1.0, 1.5, 2.0] were measured at 0.8 N only; `valid_loads_N` were measured at s = 1.0 only. The compile path `native_binding._in_domain` treats the domain as the Cartesian product (scale in valid_scales AND load in valid_loads_N), so (2.0, 3.0) would compile although no cited receipt measures that cell. **CONFIRMED.**

2. **Packet/record load-axis conflict.** The packet `example_packet.json` `admitted_domain.loads.max_force_N` = 2.0. The record `assembly.star-k2.json` `valid_loads_N` = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0]. `bounded_fit.py` `predict()` enforces the packet's 2.0 N limit directly (lines 142-144, 225-230); `native_binding._in_domain` enforces the record's 3.0 N claim. The two layers disagree. **CONFIRMED — this is the retraction decision under review.**

3. **No self-intersection / ground-crossing refusal.** At 3.0 N the load-domain study records `apex_z_wu` = -0.05953787307855677, below the rim plane. The law validates triangle nondegeneracy but has no self-contact/self-intersection variable. The record's `excluded_phenomena` do not name it. The in-domain claim at high load rests on the residual gate alone. **CONFIRMED.**

4. **Stale function-card prose.** The record's `function_card.operating_domain` reads "rigid scales 0.75x and 1.0x ONLY (1.5x/2.0x measured over the unchanged gate)" and `failures` lists "scale drift at 1.5x/2.0x". Both are superseded by the `physical_definition.domain_amendment_history` entry that extended scales to 1.5/2.0. The record layer has no amendment path for function_card prose. **CONFIRMED.**

5. **eta(Pi) not tabulated.** The contract derives dimensionless coordinates and verifies two points of the patch's curve; the star's curve is measured but not tabulated as a reusable artifact. Contract correctly assigns this to S3. **CONFIRMED.**

6. **Gamma axis degenerate.** Every qualified case runs gamma = 1.0 J/wu². Under the derived mapping, varying gamma at fixed F is a Pi sweep (Pi = F/(gamma·L)), so the missing measurement is a gamma-axis ray, not a new group. **CONFIRMED.**

7. **Dynamics not named.** The law is quasistatic by construction; the record's `excluded_phenomena` do not explicitly name transients/inertia. The overdamped descent path in the lab is separate machinery. **CONFIRMED.**

**Verdict: PASS — all seven gap items are real and honestly reported.**

---

## 4. Ruling on the retraction decision

**Coordinator's proposed ruling:** Retract the record's `valid_loads_N` to [0.0, 0.4, 0.8, 1.2, 1.6, 2.0].

**My ruling: UPHOLD.**

Reasoning:

The packet `example_packet.json` is the preregistered work packet. Its `admitted_domain.loads.max_force_N` = 2.0 is a frozen threshold (packet prose: "frozen thresholds (never widened by any consumer)"). The established discipline quoted in the coordinator's message — "the packet's law is quoted, never widened" — is explicit and was set before any load-domain measurements were taken. The record's extension to 2.5/3.0 N via `amend_domain_measurements` is a post-hoc widening of the record's measured-domain claim that conflicts with the packet's frozen port contract.

The conflict is not merely cosmetic:
- `native_binding._in_domain` admits 2.5/3.0 N because it reads the record's `valid_loads_N`.
- `bounded_fit.predict` refuses >2.0 N because it reads the packet's `admitted_domain.loads.max_force_N` directly.
- The packet is the consumer of the record; a record that claims a domain the packet does not admit is internally inconsistent.

The coordinator's four reasons for retraction are sound:
(a) The no-post-hoc-widening rule is a real discipline. The packet's 2.0 N was set before the load-domain study ran; widening it after observing 3.0 N successes would be exactly the forbidden move.
(b) The 2.5/3.0 N measurements are not lost. `load_domain_study_20261017.json` is append-only, untouched, and remains valid scientific evidence. Retraction narrows the PORT CONTRACT (what the packet admits), not the evidence base.
(c) The game loop is unaffected. Frozen objective 1.6 N and failure demo 0.9 N are both ≤ 2.0. Criterion 3's failure predicate gets strictly stronger: 2.5/3.0 N cases will be refused, which is the correct behavior if the packet's port contract is respected.
(d) The star record's port prose (`ports[0].variables.prescribed` = "vertical dead load 0.8 N") and the patch record's port prose already bind to values ≤ 2.0 N.

The alternative — amending the packet to 3.0 N — would require breaking the "frozen thresholds" discipline. While the load-domain study legitimately demonstrates that the solver can converge at 3.0 N within the 1e-6 N gate, the packet is not a scientific paper; it is the preregistered port contract that all consumers (`bounded_fit`, `compile_transaction`, qualification receipts) enforce. Amending it post-hoc would undermine the discipline that prevents p-hacking across the entire mechanism-factory lineage. The correct long-term path to 3.0 N is a new packet version (e.g., `candidate-2`) with a preregistered higher `max_force_N`, accompanied by a new load-domain study that was preregistered before running.

**Uphold the retraction.** The record's `valid_loads_N` must be retracted to [0.0, 0.4, 0.8, 1.2, 1.6, 2.0]. The load-domain study remains valid evidence. A future packet amendment (new candidate revision, preregistered before measurement) is the only legitimate path to 3.0 N.

---

## 5. "Closed-except" honesty review

The contract's verdict line reads: "S0 is **closed-except**: the missing-variable list in §7 must be carried into S1 and the record/packet owners; it is not a silent closure."

This claim is **honest** with one caveat.

The seven items in §7 are real, non-trivial, and explicitly named. They are not silent omissions. The contract correctly identifies that:
- The cross-product gap (item 1) is the most consequential for S1.
- The packet/record conflict (item 2) is acknowledged as an open decision owed.
- The self-intersection gap (item 3) is a physics-level omission in the law's boundary variables, not just a record-keeping issue.
- The stale function-card prose (item 4) is a record-layer staleness that has no amendment path.

However, the "closed-except" label is slightly overstated because item 2 (packet/record conflict) is not merely a "missing variable" — it is an active inconsistency between two layers that blocks the gate from being fully clean. The coordinator's retraction decision resolves it, but until the record is actually retracted, the gate's exit evidence is "missing variables reported" plus "one active conflict pending resolution."

**Verdict: PASS with caveat — "closed-except" is honest given the missing items are reported, but item 2 is an active inconsistency, not just a missing variable, and should be tracked as such until the retraction is executed.**

---

## 6. Summary of verdicts

| Claim | Verdict | Evidence |
|---|---|---|
| Similarity check reproduced (all 7 checks) | PASS | Independent run: exit 0, all numeric matches exact to machine precision |
| Derived scale mapping correct for constant-gamma current-area law | PASS | Dimensional analysis: [γ]=N/m, γ·s·r₀ has units of force; Pi = F/(γ·s·r₀) is dimensionless and unique |
| Owner inventory: no duplicate physics | PASS | Law distinction documented; negative controls in `surface_energy_checks.py` |
| Law pin hash correct | PASS | Independent sha256 = `ee9effcfbddad8d0...` matches record and contract |
| Units consistent | PASS | Packet and record both use m/N/J; 1 wu = 1 m makes gamma J/wu² = J/m² exact |
| All seven gap items real | PASS | Direct inspection of record, packet, load-domain study, and code confirms all 7 |
| Retraction decision | UPHOLD | Packet is frozen preregistered law; post-hoc widening forbidden; 3.0 N evidence preserved in load-domain study |
| "Closed-except" honest | PASS with caveat | Seven items honestly reported; item 2 is an active inconsistency pending resolution |

---

## 7. Reviewer's own decision challenged

The coordinator instructed me to challenge the retraction decision. I have done so by examining the alternative (packet amendment) and confronting the no-post-hoc-widening rule. I conclude the rule is binding here: the packet's `admitted_domain.loads.max_force_N` = 2.0 is a frozen threshold set before measurement, and the record's 3.0 N claim is a post-hoc widening that creates a layer conflict. The retraction is the correct resolution under current discipline. The alternative (packet amendment) would require a new candidate revision and preregistration, which is the proper long-term path but not the immediate fix.

**Review file location:** `docs/evidence/mechanism_factory/reviews/step_review_s0_contract.md`
