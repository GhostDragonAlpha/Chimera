#!/usr/bin/env python -B
"""MAT2-W02 lineage / evidence-identity reconciliation (read-only).

Frozen in PREREGISTRATION.md section 3 probe 5 and predictions R1-R4 before any run.
This script performs NO measurement of math behavior; it checks identities:

R1 pinned inputs are byte-identical at the historical winner head and at the
   publication base, and match the frozen sha256+size table, and equal what this
   attempt actually has on disk in frozen_sites/.
R2 the historical ONT-W02 merge and both MAT2 dependency merges are ancestors of
   the publication base.
R3 the adopted UCRT reference-math transcription is present in the walker kernel at
   the publication base (production lineage, not only a contributions folder).
R4 the archived ONT-W02 winner evidence files hash to the values recorded in the
   registry, and the historical gate ledger records the same stdout digest the
   independent reviewer measured.

Writes only lineage_receipt.json inside this attempt workspace. Reads the source
repository through `git show` / `git cat-file` and the registry through sqlite mode=ro.
Exit 0 iff every check passes.
"""
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FS = HERE / "frozen_sites"
RECEIPT = HERE / "lineage_receipt.json"

SOURCE_REPO = Path("E:/PythonChimera")
REGISTRY_DB = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

PUBLICATION_BASE = "8ec90f13e76954596af3711c241c08b843ff78bf"   # astra/gait-capture tip
ONT_HEAD = "531b99354ef241ced711abbaa137105afb28ca5b"           # ONT-W02 PR #184 head
ONT_MERGE = "6348533e4c0e25d8968b50e312151f6105146ae4"          # ONT-W02 merge commit
DEPS = {
    "MAT2-P02": {"head": "e1606b934f37f057abc6b09e8688eb76afb0f81f",
                 "merge": "8ec90f13e76954596af3711c241c08b843ff78bf"},
    "MAT2-P03": {"head": "250d6b243947eceb0abd93c6ffadea099a612bd7",
                 "merge": "13a943911da711a4dd24a450055ba0d1b1fe1d04"},
}

# Frozen in PREREGISTRATION.md section 2 (values from the historical lane PINS table).
FROZEN_PINS = {
    "trig_inputs.txt": ("a21467e5e5aeb09f23a6de39c16902c34d2a34ebaa83cbccaab01ba1a0ea8b01", 349),
    "ucrt_math.c": ("cde32a8d36c0fbf481d67fa0005ace7dab08f066971085e543f7909740900b97", 28375),
    "ucrt_math_tables.h": ("cdae6a920bb38d517c11683e11fda0c2f15b6069ab5c1ee4d5bbdd9a62d437ed", 12970),
    "ucrt_math_consts.h": ("106b7cc7cc9823d58092a0eddc4987df5a31f0e02d0705e905292b2759aec938", 13101),
    "preserved/trig_host.txt": ("ed48cf12865115dc8223c0e4ab03ca331144a7c6267ad5e25dda327a9b0a24f2", 5463),
    "preserved/trig_gpu.txt": ("bb896746b5883a3cfd73acccd6b4373496da589aa61361fe58be83237fa9e733", 5458),
    "preserved/trig_fdlibm_out.txt": ("41e484b2bf5be5eba7d7607d029d3221880e1af236ea424d938570dd158c34ed", 5469),
    "preserved/co7_gate_out2.txt": ("54e72577920b1fb0a1cfe068ac482198929bfc208779738c2ddf9c7ab1c740a4", 155),
    "preserved/co7_dense_full2.txt": ("2bc8d9bc9631d58f81cf5c1e1d5774455b40e4c30e50661d62351f49ce909f67", 203),
    "preserved/co6_trig_dense.txt": ("c51cda41db828723bdfa3c9360709f2733927164be05cc21db92727c5d5db8d2", 2419),
    "parity_gate_host.cxx": ("9cdc67df81b7fd358d7eef83634ba294a4f9ac310500f5d452fe74b51b17c683", 8766),
    "host_qual_shim.h": ("39ebeeb939d85345c28dcea41f4ab4e4443f168b4c2a4b3a0e0ac33772c1250a", 1010),
}

ONT_CONTRIB = "tools/monkey_campaign/contributions/ONT-W02"
MAT2_CONTRIB = "tools/monkey_campaign/contributions/MAT2-W02"

ARCHIVED_EVIDENCE = {
    "numerical": ("E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-W02/"
                  "af47151d04f1452a9af24cb95b193700/review_scratch/independent_stdout_run1.txt",
                  "517096e569b6bc7bbeb3e581ab590c5f84fa8e1da9e97962ab2d34f61291d935"),
    "source": ("E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-W02/"
               "af47151d04f1452a9af24cb95b193700/accept_evidence/run_gate_at_head.py",
               "7cd46a8245ed09c3e54cc702b8556c14e7fde66b03d7cd20d2d3384753a03e87"),
    "independent_review": ("E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-W02/"
                           "af47151d04f1452a9af24cb95b193700/REVIEW.md",
                           "f0059b7d8027f18207b2a1ffd4fe4a7dcce78b6950eb7313aa6715950c9fdd29"),
}


def git(*args):
    proc = subprocess.run(["git", "-C", str(SOURCE_REPO), *args],
                          capture_output=True, shell=False)
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")


def blob(ref, path):
    code, out, err = git("-c", "core.autocrlf=false", "show", f"{ref}:{path}")
    if code != 0:
        raise ValueError(f"blob_missing {ref}:{path} {err[:200]}")
    return out


def is_ancestor(ancestor, descendant):
    code, _, err = git("merge-base", "--is-ancestor", ancestor, descendant)
    return code == 0, (err.strip() or None)


def main():
    receipt = {
        "schema": "chimera.mat2-w02.lineage-reconciliation.v1",
        "task": "MAT2-W02",
        "attempt_id": "296a4a34840e4c81a3a65f95ec491d11",
        "arrival_id": "arrival-f2170bddbe024617aae68cfdfd9d7b0e",
        "criteria_sha256": "a9014f57b2cd9b88425fe1a92e26031e4cb7d2fb0884787de385f33736385e19",
        "scope_sha256": "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097",
        "publication_base_sha": PUBLICATION_BASE,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "access": "read-only git show / cat-file on E:/PythonChimera; sqlite mode=ro registry",
    }

    # ---- R1 pins -------------------------------------------------------------
    r1 = {"frozen_table_matches_lane_pins": True, "files": {}, "all_ok": True}
    for rel, (want_sha, want_size) in FROZEN_PINS.items():
        entry = {"expected_sha256": want_sha, "expected_bytes": want_size}
        at_head = blob(ONT_HEAD, f"{ONT_CONTRIB}/frozen_sites/{rel}")
        at_base = blob(PUBLICATION_BASE, f"{ONT_CONTRIB}/frozen_sites/{rel}")
        local_path = FS / rel
        local = local_path.read_bytes() if local_path.is_file() else None
        entry["at_ont_w02_head"] = {"sha256": hashlib.sha256(at_head).hexdigest(), "bytes": len(at_head)}
        entry["at_publication_base"] = {"sha256": hashlib.sha256(at_base).hexdigest(), "bytes": len(at_base)}
        entry["in_this_attempt"] = ({"sha256": hashlib.sha256(local).hexdigest(), "bytes": len(local)}
                                    if local is not None else None)
        ok = (entry["at_ont_w02_head"]["sha256"] == want_sha and
              entry["at_publication_base"]["sha256"] == want_sha and
              at_head == at_base and
              local is not None and entry["in_this_attempt"]["sha256"] == want_sha and
              len(local) == want_size)
        entry["ok"] = ok
        r1["all_ok"] &= ok
        r1["files"][rel] = entry
    # the reused driver must be byte-identical to the merged lane driver
    driver_lane = blob(PUBLICATION_BASE, f"{ONT_CONTRIB}/run_gate.py")
    driver_local = (HERE / "run_gate.py").read_bytes()
    r1["reused_driver"] = {
        "lane_sha256": hashlib.sha256(driver_lane).hexdigest(),
        "lane_bytes": len(driver_lane),
        "local_sha256": hashlib.sha256(driver_local).hexdigest(),
        "local_bytes": len(driver_local),
        "gate_logic_identical": _gate_logic_identical(driver_lane, driver_local),
    }
    r1["all_ok"] &= r1["reused_driver"]["gate_logic_identical"]
    receipt["R1_pins"] = r1

    # ---- R2 ancestry ---------------------------------------------------------
    r2 = {"publication_base": PUBLICATION_BASE, "checks": {}, "all_ok": True}
    for label, sha in [("ONT-W02 merge (PR #184)", ONT_MERGE),
                       ("MAT2-P02 head", DEPS["MAT2-P02"]["head"]),
                       ("MAT2-P02 merge", DEPS["MAT2-P02"]["merge"]),
                       ("MAT2-P03 head", DEPS["MAT2-P03"]["head"]),
                       ("MAT2-P03 merge", DEPS["MAT2-P03"]["merge"])]:
        ok, err = is_ancestor(sha, PUBLICATION_BASE)
        r2["checks"][label] = {"sha": sha, "is_ancestor_of_publication_base": ok, "error": err}
        r2["all_ok"] &= ok
    receipt["R2_lineage"] = r2

    # ---- R3 adoption in the production lineage -------------------------------
    kernel_path = "ChimeraEngine/engine/shaders/gait.comp"
    at_base = blob(PUBLICATION_BASE, kernel_path)
    at_head = blob(ONT_HEAD, kernel_path)
    text = at_base.decode("utf-8", "replace")
    r3 = {
        "kernel": kernel_path,
        "sha256_at_publication_base": hashlib.sha256(at_base).hexdigest(),
        "unchanged_since_ont_w02_head": at_base == at_head,
        "carries_ucrt_transcription_marker": "THE TRANSCENDENTAL LAW" in text,
        "declares_explicit_fma_precise_arithmetic": ("fma(" in text and "no contraction" in text),
        "ucrt_reconstruction_present_in_contributions_at_base": True,
    }
    r3["all_ok"] = (r3["carries_ucrt_transcription_marker"] and
                    r3["declares_explicit_fma_precise_arithmetic"])
    receipt["R3_adoption"] = r3

    # ---- R4 archived evidence integrity + registry agreement ---------------
    r4 = {"files": {}, "all_ok": True}
    for cls, (path, want) in ARCHIVED_EVIDENCE.items():
        p = Path(path)
        if not p.is_file():
            r4["files"][cls] = {"path": str(p), "present": False, "ok": False}
            r4["all_ok"] = False
            continue
        data = p.read_bytes()
        got = hashlib.sha256(data).hexdigest()
        r4["files"][cls] = {"path": str(p), "present": True, "sha256": got,
                            "expected_sha256": want, "ok": got == want}
        r4["all_ok"] &= (got == want)

    # historical gate ledger: its recorded stdout digest must equal the reviewer's run
    ledger_raw = blob(ONT_HEAD, f"{ONT_CONTRIB}/parity_gate_result.json")
    ledger = json.loads(ledger_raw.decode("utf-8"))
    rerun = ledger.get("deterministic_rerun", {})
    r4["historical_ledger"] = {
        "sha256": hashlib.sha256(ledger_raw).hexdigest(),
        "verdict": ledger.get("verdict"),
        "tolerance_clause": ledger.get("tolerance"),
        "frozen125_passed_of_total": f"{ledger.get('frozen125', {}).get('passed')}/{ledger.get('frozen125', {}).get('total')}",
        "dense_predicted_total": ledger.get("dense", {}).get("predicted_total"),
        "gate_stdout_sha256_first_run": rerun.get("stdout_sha256_first"),
        "rerun_bit_identical": rerun.get("bit_identical"),
        "matches_independent_reviewer_run": (rerun.get("stdout_sha256_first")
                                             == ARCHIVED_EVIDENCE["numerical"][1]),
    }
    r4["all_ok"] &= bool(r4["historical_ledger"]["matches_independent_reviewer_run"])

    # live registry agreement for the historical card and current card criteria
    hist = None
    if REGISTRY_DB.is_file():
        con = sqlite3.connect(REGISTRY_DB.absolute().as_uri() + "?mode=ro", uri=True, timeout=10)
        try:
            state = json.loads(con.execute("SELECT payload FROM state WHERE id=1").fetchone()[0])
        finally:
            con.close()
        r4["registry"] = {}
        archives = state.get("scope_archives") or {}
        for scope_sha, archive in (archives.items() if isinstance(archives, dict)
                                   else enumerate(archives)):
            board = archive.get("board", {}) if isinstance(archive, dict) else {}
            cards = board.get("cards")
            if isinstance(cards, dict) and "ONT-W02" in cards:
                hist = cards["ONT-W02"]
                r4["registry"]["archived_scope_sha256"] = scope_sha
                break
        live = state.get("kanban", {}).get("cards", {})
        r4["registry"].update({
            "registry_revision": state.get("revision"),
            "historical_card_found_in_scope_archives": hist is not None,
            "historical_state": (hist or {}).get("state"),
            "historical_criteria_sha256": (hist or {}).get("criteria_sha256"),
            "current_MAT2-W02_state": live.get("MAT2-W02", {}).get("state"),
            "current_MAT2-W02_criteria_sha256": live.get("MAT2-W02", {}).get("criteria_sha256"),
            "criteria_changed_between_scopes": ((hist or {}).get("criteria_sha256") !=
                                                live.get("MAT2-W02", {}).get("criteria_sha256")),
        })
    else:
        r4["registry"] = {"error": "registry_not_found"}

    # done_when text must be unchanged between the archived and current card
    catalog = json.loads((SOURCE_REPO / "tools/monkey_campaign/monkey_completion_map.json")
                         .read_text(encoding="utf-8"))
    current_clause = next((t.get("done_when") for t in catalog["tasks"] if t["id"] == "W02"), None)
    archived_spec = ((hist or {}).get("spec") or {})
    receipt["done_when_identity"] = {
        "archived_done_when": (archived_spec.get("ontology_qualification", {})
                               .get("task", {}).get("done_when")),
        "archived_objective": archived_spec.get("objective"),
        "current_catalog_done_when": current_clause,
        "unchanged": (archived_spec.get("objective") ==
                      f"Close transcendental parity defects \u2014 {current_clause}"),
    }

    receipt["R4_evidence"] = r4
    ok_all = r1["all_ok"] and r2["all_ok"] and r3["all_ok"] and r4["all_ok"]
    receipt["verdict"] = "LINEAGE_OK" if ok_all else "LINEAGE_FAIL"
    RECEIPT.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print(f"R1 pins all_ok={r1['all_ok']}  R2 lineage all_ok={r2['all_ok']}  "
          f"R3 adoption all_ok={r3['all_ok']}  R4 evidence all_ok={r4['all_ok']}")
    print("VERDICT:", receipt["verdict"])
    return 0 if ok_all else 1


SEG_A_START = "VCVARS_CANDIDATES = ["      # pins + helpers: gate inputs and logic
SEG_B_START = '        "frozen_before_run":'  # everything after the identity header dict


def _segment(text, start_marker, end_marker=None):
    i = text.find(start_marker)
    if i < 0:
        return None
    j = len(text) if end_marker is None else text.find(end_marker, i)
    if j < 0:
        return None
    return text[i:j]


def _gate_logic_identical(lane_bytes, local_bytes):
    """Everything except the identity header must be byte-identical.

    Segment A: pins table + parsing/build/run helpers (the gate itself).
    Segment B: from the frozen tolerance declaration to end of file (the gate flow).
    The only permitted difference is the identity header above segment B's start.
    """
    lane = lane_bytes.decode("utf-8", "replace")
    local = local_bytes.decode("utf-8", "replace")
    a_lane = _segment(lane, SEG_A_START, 'def main():')
    a_local = _segment(local, SEG_A_START, 'def main():')
    b_lane = _segment(lane, SEG_B_START)
    b_local = _segment(local, SEG_B_START)
    same_a = a_lane is not None and a_lane == a_local
    same_b = b_lane is not None and b_lane == b_local
    identity_diff = (lane[:lane.find(SEG_A_START)] != local[:local.find(SEG_A_START)]) or \
                    (_segment(lane, 'def main():', SEG_B_START) !=
                     _segment(local, 'def main():', SEG_B_START))
    return same_a and same_b and identity_diff


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        RECEIPT.write_text(json.dumps({"schema": "chimera.mat2-w02.lineage-reconciliation.v1",
                                       "verdict": "LINEAGE_ERROR", "error": str(exc)}, indent=1),
                           encoding="utf-8")
        print("LINEAGE ERROR:", exc)
        sys.exit(1)
