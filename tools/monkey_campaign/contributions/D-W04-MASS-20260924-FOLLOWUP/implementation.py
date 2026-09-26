"""Walking body/manifest consistency validator (D-W04-MASS-20260924-FOLLOWUP).

Source-bound, read-only, CPU-only, stdlib-only check that the first-skill
acceptance CoT denominator and the trainer env's simulated rigid-assembly
body mass are THE SAME body, resolved from pinned git objects with explicit
units and recorded blob provenance.

Implements the check accepted from the winning diagnostic D-W04-MASS-20260924
(merged PR #118, head 24db3062187e617cf576019adb131926df63a237): the frozen
denominator (membrane inventory 13824.5 kg) and the training body (Oku-2021
10.038 kg assembly) were proven to be different bodies (ratio 1377.2166x).
This tool does NOT substitute a body mass and does NOT touch any frozen
registration field — it only MEASURES and REPORTS the binding, refusing when
any lineage link cannot be resolved.

Usage:
  python -B implementation.py --source-repo PATH
        --acceptance-commit SHA --trainer-commit SHA --scene-numbers-commit SHA
        --out PATH
        [--expect-acceptance-blob SHA] [--expect-manifest-blob SHA]
        [--expect-scene-numbers-blob SHA] [--scene-json PATH]

Pins are required: the tool never measures an unpinned tree.

Resolved quantities:
  denominator_mass_kg   acceptance.py M_BODY_KG literal (frozen CoT denominator)
  training_body_mass_kg scene bundle mass (via --scene-json) or pinned
                        derived_numbers.json body_model.mass_kg
  ratio_dimensionless   denominator / training body
  weight_newton         training mass x g0 = 9.80665 m/s^2, cross-checked
                        against the recorded body_model.weight_N

Compatibility: COMPATIBLE requires denominator == training mass within
REL_TOL, all frozen definition sites (acceptance literal, run_manifest.json
definition, RUNBOOK step-5 line, checkpoint report label) to agree on the
same kg value, and the walker_model.py structural guard to be present.
Anything else is INCOMPATIBLE (a real verdict, exit 1) — never a refusal.

Refusals (environment/lineage problems, exit 3, named, NO output file):
  SOURCE_REPO_MISSING, PIN_UNRESOLVABLE, PATH_NOT_IN_PIN,
  BLOB_ANCHOR_MISMATCH, UNPARSEABLE_DENOMINATOR, UNPARSEABLE_TRAINING_MASS,
  NON_FINITE_MASS, SCENE_JSON_UNPARSEABLE, GIT_COMMAND_FAILED.

Exit codes: 0 COMPATIBLE, 1 INCOMPATIBLE, 3 refusal.
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

SCHEMA = "d-w04-mass-followup.body_manifest_consistency.v1"

G0_M_S2 = 9.80665          # standard gravity, m/s^2 (exact by definition)
WEIGHT_TOL_N = 0.01        # recorded weight_N may be rounded (98.439)
REL_TOL = 1e-9             # masses must agree to 1e-9 relative to be the SAME body

ACCEPTANCE_REL = "tools/science_funnel/first_skill/acceptance.py"
MANIFEST_REL = "tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json"
RUNBOOK_REL = "tools/science_funnel/validation/first_skill_prestage_20260922/RUNBOOK.md"
WALKER_MODEL_REL = "tools/science_funnel/typeb_gpu/walker_model.py"
REPORT_LABEL_REL = "tools/report_first_skill_checkpoint.py"
SCENE_NUMBERS_REL = "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"

WALKER_GUARD = 'self.body_mass[i] = float(b["mass_kg"])'
COT_EXPR = re.compile(r"cot\s*=\s*work\s*/\s*\(M_BODY_KG\s*\*\s*dist\)")
DENOM_LINE = re.compile(r"^\s*M_BODY_KG\s*=\s*([0-9]+\.[0-9]+|[0-9]+)\s*(?:#.*)?$")
HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")


class Refusal(RuntimeError):
    """Named refusal: exit 3, no output file."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_git(repo: pathlib.Path, argv, stdin: bytes = None) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo), *argv]
    proc = subprocess.run(cmd, capture_output=True, input=stdin)
    if proc.returncode != 0:
        raise Refusal("GIT_COMMAND_FAILED command=%r exit=%d stderr=%r" % (
            " ".join(cmd), proc.returncode,
            proc.stderr.decode("utf-8", errors="replace").strip()[:400]))
    return proc


def resolve_commit(repo: pathlib.Path, pin: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", pin + "^{commit}"],
        capture_output=True)
    if proc.returncode != 0:
        raise Refusal("PIN_UNRESOLVABLE pin=%r stderr=%r" % (
            pin, proc.stderr.decode("utf-8", errors="replace").strip()[:200]))
    full = proc.stdout.decode().strip()
    if not HEX40.match(full):
        raise Refusal("PIN_UNRESOLVABLE pin=%r resolved to non-40-hex %r" % (pin, full))
    return full


def blob_at(repo: pathlib.Path, commit: str, rel: str, expect_blob=None) -> dict:
    probe = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "%s:%s" % (commit, rel)],
        capture_output=True)
    if probe.returncode != 0:
        raise Refusal("PATH_NOT_IN_PIN path=%r commit=%s" % (rel, commit[:12]))
    blob = probe.stdout.decode().strip()
    if not HEX40.match(blob):
        raise Refusal("GIT_COMMAND_FAILED detail='rev-parse returned non-40-hex blob id %r'" % blob)
    if expect_blob is not None and blob != expect_blob:
        raise Refusal("BLOB_ANCHOR_MISMATCH path=%r commit=%s expected_blob=%s got_blob=%s"
                      % (rel, commit[:12], expect_blob, blob))
    data = check_git(repo, ["cat-file", "blob", blob]).stdout
    return {"path": rel, "commit": commit, "blob_id": blob, "bytes": len(data),
            "sha256_raw_bytes": sha256(data), "text": data.decode("utf-8", errors="replace")}


def find_line(text: str, pattern) -> dict:
    for i, ln in enumerate(text.splitlines(), start=1):
        if pattern.search(ln):
            return {"line_no": i, "line": ln.strip()}
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-repo", required=True)
    ap.add_argument("--acceptance-commit", required=True)
    ap.add_argument("--trainer-commit", required=True)
    ap.add_argument("--scene-numbers-commit", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-acceptance-blob", default=None)
    ap.add_argument("--expect-manifest-blob", default=None)
    ap.add_argument("--expect-scene-numbers-blob", default=None)
    ap.add_argument("--scene-json", default=None,
                    help="optional compiled scene bundle (bodies[].mass_kg, kg); "
                         "when present it is the PRIMARY training-body source")
    args = ap.parse_args(argv)

    repo = pathlib.Path(args.source_repo)
    if not repo.is_dir():
        raise Refusal("SOURCE_REPO_MISSING %r is not a directory" % str(repo))
    probe = subprocess.run(["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
                           capture_output=True)
    if probe.returncode != 0:
        raise Refusal("SOURCE_REPO_MISSING %r is not a git repository" % str(repo))

    acc_commit = resolve_commit(repo, args.acceptance_commit)
    trn_commit = resolve_commit(repo, args.trainer_commit)
    scn_commit = resolve_commit(repo, args.scene_numbers_commit)

    acc = blob_at(repo, acc_commit, ACCEPTANCE_REL, args.expect_acceptance_blob)
    man = blob_at(repo, acc_commit, MANIFEST_REL, args.expect_manifest_blob)
    run_txt = blob_at(repo, acc_commit, RUNBOOK_REL)
    wmod = blob_at(repo, trn_commit, WALKER_MODEL_REL)
    rlabel = blob_at(repo, trn_commit, REPORT_LABEL_REL)
    scn = blob_at(repo, scn_commit, SCENE_NUMBERS_REL, args.expect_scene_numbers_blob)

    checks = []

    def check(name, ok, detail, **extra):
        checks.append(dict({"check": name, "ok": bool(ok), "detail": detail}, **extra))
        return bool(ok)

    # -- denominator (acceptance CoT denominator, kg) -----------------------
    m = find_line(acc["text"], DENOM_LINE)
    if m is None:
        raise Refusal("UNPARSEABLE_DENOMINATOR no 'M_BODY_KG = <number>' line in %s@%s"
                      % (ACCEPTANCE_REL, acc_commit[:12]))
    den_val = float(m["line"].split("=", 1)[1].split("#", 1)[0].strip())
    if not math.isfinite(den_val) or den_val <= 0.0:
        raise Refusal("NON_FINITE_MASS denominator=%r" % den_val)
    den_literal = m["line"].split("=", 1)[1].split("#", 1)[0].strip()
    unit_den = "kg"
    check("denominator_literal_parsed", True,
          "M_BODY_KG = %s at %s:%d (blob %s); unit %s"
          % (den_literal, ACCEPTANCE_REL, m["line_no"], acc["blob_id"][:12], unit_den),
          value=den_val, unit=unit_den, line_no=m["line_no"])

    cotm = find_line(acc["text"], COT_EXPR)
    check("denominator_used_in_cot_expression", cotm is not None,
          ("cot = work / (M_BODY_KG * dist) at %s:%d" % (ACCEPTANCE_REL, cotm["line_no"]))
          if cotm else "no cot = work / (M_BODY_KG * dist) expression found")

    kg_token = "%s kg" % den_literal
    man_line = find_line(man["text"], re.compile(re.escape(kg_token)))
    check("manifest_definition_consistent", man_line is not None,
          ("run_manifest.json cot_within_band.definition names %s at line %d"
           % (kg_token, man_line["line_no"])) if man_line else
          ("manifest definition does NOT name %s — frozen-site disagreement" % kg_token))

    rb_line = find_line(run_txt["text"], re.compile(re.escape(kg_token)))
    check("runbook_definition_consistent", rb_line is not None,
          ("RUNBOOK.md names %s at line %d" % (kg_token, rb_line["line_no"]))
          if rb_line else "RUNBOOK does NOT name %s — frozen-site disagreement" % kg_token)

    rl_line = find_line(rlabel["text"], re.compile(re.escape(kg_token)))
    check("report_label_consistent", rl_line is not None,
          ("checkpoint report label names %s at line %d" % (kg_token, rl_line["line_no"]))
          if rl_line else "checkpoint report label does NOT name %s" % kg_token)

    # -- training body (the env's rigid assembly, kg) ------------------------
    training_sources = {}
    if args.scene_json:
        try:
            scene = json.loads(pathlib.Path(args.scene_json).read_text(encoding="utf-8"))
            bodies = [b for b in scene["bodies"] if float(b["mass_kg"]) > 0.0]
            scene_mass = sum(float(b["mass_kg"]) for b in bodies)
        except Exception as exc:  # noqa: BLE001 - any parse failure is a refusal
            raise Refusal("SCENE_JSON_UNPARSEABLE %r: %s" % (args.scene_json, exc))
        if not math.isfinite(scene_mass) or scene_mass <= 0.0:
            raise Refusal("NON_FINITE_MASS scene bundle mass=%r" % scene_mass)
        training_sources["compiled_scene_bundle"] = {
            "mass_kg": scene_mass, "nonzero_bodies": len(bodies),
            "path": str(args.scene_json)}
        train_val = scene_mass
        train_prov = "compiled_scene_bundle"
    else:
        scn_data = json.loads(scn["text"])
        try:
            train_val = float(scn_data["body_model"]["mass_kg"])
            weight_recorded = float(scn_data["body_model"]["weight_N"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Refusal("UNPARSEABLE_TRAINING_MASS %s@%s: %s"
                          % (SCENE_NUMBERS_REL, scn_commit[:12], exc))
        if not math.isfinite(train_val) or train_val <= 0.0:
            raise Refusal("NON_FINITE_MASS training mass=%r" % train_val)
        training_sources["pinned_derived_numbers"] = {
            "mass_kg": train_val, "recorded_weight_N": weight_recorded,
            "blob_id": scn["blob_id"], "unit": "kg"}
        train_prov = "pinned_derived_numbers"

    check("training_mass_resolved", True,
          "training body = %.6g kg from %s (unit kg)" % (train_val, train_prov),
          value=train_val, unit="kg", provenance=train_prov)

    guard = find_line(wmod["text"], re.compile(re.escape(WALKER_GUARD)))
    check("trainer_structural_binding", guard is not None,
          ("walker_model.py:%d loads body masses from the scene bundle (%s)"
           % (guard["line_no"], WALKER_GUARD)) if guard else
          "walker_model.py does not load body_mass from the scene bundle")

    weight = train_val * G0_M_S2
    weight_rec = training_sources.get("pinned_derived_numbers", {}).get("recorded_weight_N")
    weight_ok = weight_rec is not None and abs(weight - weight_rec) <= WEIGHT_TOL_N
    check("weight_consistency", weight_ok,
          ("%.7f N = mass x g0 (%.5f m/s^2); recorded %.3f N; |err| %.7f N <= %.2f N"
           % (weight, G0_M_S2, weight_rec, abs(weight - weight_rec), WEIGHT_TOL_N))
          if weight_rec is not None else
          "no recorded weight to cross-check (scene-bundle source)", unit="N")

    # -- the actual compatibility verdict ------------------------------------
    ratio = den_val / train_val
    same_body = abs(den_val - train_val) <= REL_TOL * max(1.0, abs(train_val))
    sites_ok = all(c["ok"] for c in checks
                   if c["check"] in ("manifest_definition_consistent",
                                     "runbook_definition_consistent",
                                     "report_label_consistent"))
    check("denominator_equals_training_mass", same_body,
          ("denominator %s kg == training body %s kg: SAME body"
           % (den_literal, train_val)) if same_body else
          ("denominator %s kg (membrane-inventory lineage, %s@%s) != training body "
           "%.6g kg (%s lineage): ratio %.12g — absolute CoT is mislabeled by this factor"
           % (den_literal, ACCEPTANCE_REL, acc_commit[:12], train_val, train_prov, ratio)),
          ratio_dimensionless=ratio if not same_body else 1.0)

    compatible = same_body and sites_ok and cotm is not None and guard is not None
    verdict = "COMPATIBLE" if compatible else "INCOMPATIBLE"

    result = {
        "schema": SCHEMA,
        "source_repo": str(repo),
        "pins": {"acceptance_commit": acc_commit, "trainer_commit": trn_commit,
                 "scene_numbers_commit": scn_commit},
        "units": {"denominator_mass": "kg", "training_body_mass": "kg",
                  "weight": "N", "ratio": "dimensionless", "g0": "m/s^2"},
        "g0_m_s2": G0_M_S2,
        "denominator_mass_kg": den_val,
        "training_body_mass_kg": train_val,
        "training_body_source": training_sources,
        "ratio_dimensionless": ratio,
        "weight_newton": weight,
        "verdict": verdict,
        "provenance": {
            "acceptance.py": {k: acc[k] for k in ("path", "commit", "blob_id", "bytes",
                                                  "sha256_raw_bytes")},
            "run_manifest.json": {k: man[k] for k in ("path", "commit", "blob_id", "bytes",
                                                      "sha256_raw_bytes")},
            "RUNBOOK.md": {k: run_txt[k] for k in ("path", "commit", "blob_id", "bytes",
                                                   "sha256_raw_bytes")},
            "walker_model.py": {k: wmod[k] for k in ("path", "commit", "blob_id", "bytes",
                                                     "sha256_raw_bytes")},
            "report_first_skill_checkpoint.py": {k: rlabel[k] for k in ("path", "commit",
                                                                        "blob_id", "bytes",
                                                                        "sha256_raw_bytes")},
            "derived_numbers.json": {k: scn[k] for k in ("path", "commit", "blob_id", "bytes",
                                                         "sha256_raw_bytes")},
        },
        "checks": checks,
        "notes": [
            "This tool measures and reports only; it does not amend any frozen "
            "registration field. Correcting the denominator requires a NEW "
            "lead-authorized registration (RUNBOOK frozen-field law).",
            "Verdict is a source-lineage statement, not native acceptance: no "
            "engine, GPU or training process is involved.",
        ],
    }
    passed = sum(1 for c in checks if c["ok"])
    result["summary"] = "%d/%d checks green — %s" % (passed, len(checks), verdict)

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation_result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")
    print(result["summary"])
    for c in checks:
        print(("PASS" if c["ok"] else "FAIL"), c["check"], "-", c["detail"][:110])
    print("VERDICT:", verdict)
    return 0 if compatible else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL %s" % r, file=sys.stderr)
        sys.exit(3)
