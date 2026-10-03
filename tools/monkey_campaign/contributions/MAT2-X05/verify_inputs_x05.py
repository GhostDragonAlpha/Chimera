#!/usr/bin/env python3
"""MAT2-X05: the frozen input-pin verifier (prereg section 1) — the X05
ADD-ON pin layer.

The certified-line pin table is verified by W10's OWN verify_inputs.py,
extracted UNMODIFIED and executed first (the X04 discipline: "reuse verified
work; do not repeat completed implementation"). The U07 layer is executed
for the accepted trace/adapter modules (imported, never copied). This module
adds and verifies exactly the X05 pins: the base-tip identity, the prereg
commit law (95ddd906: parent == the base e814433c, touches ONLY the prereg
file, blob bytes == THIS card's frozen PREREGISTRATION.md), the section-1
base blobs at e814433c, the section-1 evidence-store pins, the sealed
attempt-12 driver records (the coupling-determination inputs), and the X05
card identity READ-ONLY from the registry (profile checked BEFORE any
capture; G7).

Run:  python -B verify_inputs_x05.py
Exit: 0 green / 2 named refusal (`input_pin_mismatch` / `input_pin_missing`).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
U07_SIBLING = HERE.parent / "MAT2-U07"          # the byte-verified package
X04_SIBLING = HERE.parent / "MAT2-X04"          #   siblings (read-only)
CONTRIB_ROOT = HERE.parent                      # .../contributions
TOOLS_ROOT = HERE.parents[1]                    # .../tools

_SA = None


def source_access():
    """The DECLARED read-only blob reader — the PINNED MAT2-U07
    source_access.py bytes from THIS package's sibling extraction
    (byte-asserted against the section-1 pin; imported, never copied)."""
    global _SA
    if _SA is None:
        import importlib.util
        path = U07_SIBLING / "source_access.py"
        if not path.exists():
            raise Refusal("input_pin_missing:source_access.py")
        data = path.read_bytes()
        require(sha_bytes(data)
                == "0563d123b51bd65a28f74b01afa0daa766001830890b4babb458f407e475759b",
                "input_pin_mismatch:source_access.py")
        spec = importlib.util.spec_from_file_location("x05_source_access",
                                                      path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["x05_source_access"] = mod
        spec.loader.exec_module(mod)
        _SA = mod
    return _SA


def git_read(args):
    """Read-only git against the source repo (the prereg-commit law; no ref,
    index or worktree mutation)."""
    import subprocess
    out = subprocess.run(["git", "-c",
                          "safe.directory=" + source_access().source_repo(),
                          "-C", source_access().source_repo(), *args],
                         capture_output=True, check=False)
    if out.returncode != 0:
        raise Refusal("git_read_refused:" + args[0] + ":"
                      + out.stderr.decode("utf-8", "replace")[:160])
    return out.stdout

CARD_ID = "MAT2-X05"
BASE_SHA = "95ddd90641c2de6cab01d711f39abbd9ff7fa2be"     # the prereg pin
PIN_BASE = "e814433c8dd18d2fe9abf467b563afc440efc815"     # the section-1 base
PREREG_COMMIT = BASE_SHA
PREREG_PATH = ("tools/monkey_campaign/contributions/"
               "X05-VISIBLE-MOTION-20261002/PREREGISTRATION.md")
PREREG = HERE / "PREREGISTRATION.md"
X04_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-X04")
W10_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-W10")
U07_DIR = ("tools", "monkey_campaign", "contributions", "MAT2-U07")

A12_JOB = Path("E:/ChimeraWork/task-runner/results/"
               "ca111cdc917e420eb78c41339d88c41b")

SCRATCH = Path(os.environ.get("TMP", ".")) / "x05_pins_impl"
PINNED_ROOT = SCRATCH / "pinned_root"

# (group, pinned path parts, sha256) — prereg section 1.
PINS = [
    # base blobs — content sha256 at e814433c (the prereg's declared base;
    # THIS package's base 95ddd906 is its only child, touching only the
    # prereg file — verified below — so the bytes are identical here too;
    # both are read and compared).
    ("blob", X04_DIR + ("PREREGISTRATION.md",),
     "2e62487fa4569990c1e569b6829295fa6a7f498b0d07a12c97f1ebbcac56d418"),
    ("blob", X04_DIR + ("presentation_harness.py",),
     "6ab579a41bc92348b89fedb9def6d3ca24e87e73bd98ee973d28db1051f890da"),
    ("blob", X04_DIR + ("state_readout.py",),
     "fe8bcf421430141a1825d5065e5b3a2aa1ce34400456e64ef0b943d14d01a556"),
    ("blob", X04_DIR + ("capture_card", "card", "view_spec.json"),
     "f87e2574b7bdb7706d2d17f6f557df311ceb54c78dacee7783919bebd24f5180"),
    ("blob", X04_DIR + ("capture_card", "card", "card_prereg.json"),
     "f7cab07e0a44388e0d654ce5e73953c7ae5acd3a7b91a10f749de92b970ce715"),
    ("blob", X04_DIR + ("capture_card", "TEMPLATE_MANIFEST.json"),
     "1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7"),
    ("blob", W10_DIR + ("visualization.py",),
     "2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb"),
    ("blob", W10_DIR + ("walking_demo.py",),
     "fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1"),
    ("blob", W10_DIR + ("command_model.py",),
     "0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa"),
    ("blob", W10_DIR + ("verify_inputs.py",),
     "25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6"),
    ("blob", U07_DIR + ("camera_views.py",),
     "0bb53f98de48df1b0541370930614a937e0287b99b8a1a10845a8947786d4b8c"),
    ("blob", U07_DIR + ("controls_harness.py",),
     "b4c71813fe05008976611d12b954c5a07dbdfb616556dff62ecc513ca1e28b95"),
    ("blob", U07_DIR + ("pixel_gate.py",),
     "784b78032da10816647245b535ab9b88e17586f0e5d76d5183f799c5aadcb0d7"),
    ("blob", U07_DIR + ("source_access.py",),
     "0563d123b51bd65a28f74b01afa0daa766001830890b4babb458f407e475759b"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "monkey_campaign",
              "product", "input_mapper.py"),
     "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-U01",
              "reconcile", "pinned_seam", "tools", "science_funnel",
              "typeb_export", "command_record.py"),
     "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-F04",
              "implementation.py"),
     "5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083"),
    ("blob", ("tools", "monkey_campaign", "contributions", "MAT2-M12",
              "m12_lod.py"),
     "f08fd1d2e24f8b72b9833936d49db23cae9d5ef8c3bbedd1bdc2b9ec792849cc"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "K01-CLIMB-20261001", "capture_card", "card",
              "view_spec.json"),
     "ce5c82d5e04f44af4819c76ef725eddc9c5502dd8e9ef04e07069a4182e00534"),
    ("blob", ("tools", "monkey_campaign", "contributions",
              "K01-CLIMB-20261001", "capture_card", "card",
              "render_k01.py"),
     "3659f5448f1b3abd86c7634b79e26b6955df2128779830790d230139e9c62b54"),
    ("blob", ("tools", "monkey_campaign", "visual_capture.py"),
     "5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05"),
    # evidence store (durable vault) — prereg section 1
    ("store", ("MAT2-P06", "numerical", "numerical"),
     "a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8"),
    ("store", ("MAT2-W10", "numerical", "walking_demo_receipt.json"),
     "2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02"),
    ("store", ("MAT2-W10", "numerical", "checks_receipt.json"),
     "999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2"),
    ("store", ("MAT2-X04", "numerical", "REPORT.md"),
     "3e24a78a6126b0bf881db01be357286d4165f69d019409f29729962217a27463"),
    ("store", ("MAT2-X04", "numerical", "result.json"),
     "699aa1a1b188819994568fd2461f046dbf376c64a0209ca59ed82fd9759b9728"),
    ("store", ("MAT2-X04", "numerical", "checks_receipt.json"),
     "7e5a42fb02389d9a3a5249b2c8f2cfddbc73458fee9cfb55f2df7e8d41a6cb33"),
    ("store", ("MAT2-X04", "numerical", "presentation_receipt.json"),
     "4d0e52849d2d2c18ea609c9f702296d33c1bc3c445c5bfa570ad4ab6c83c7603"),
    ("store", ("MAT2-X04", "numerical", "capture_manifest.json"),
     "4856dc1fd2b220b844454053ffedea87fad9d97be4fde28db0f19a9c97578188"),
    ("store", ("MAT2-X04", "visual", "capture_x04_presentation.mkv"),
     "f648372d2928620635077bf734b7ebd41b858836a025e87418a46920b1672570"),
    ("store", ("WK-LATENCY-20261002", "numerical",
               "REPORT_a12_structural_invisibility.md"),
     "4520ec3d168c8c1174030af914b1a7166bf73316b08a1f2c975a8bfb3df48efd"),
    ("store", ("WK-LATENCY-20261002", "numerical", "result_a12.json"),
     "959e0114acb2297077e76d7dbe7ac05f25ec801fb6941e4cbc133b6631111df6"),
    ("store", ("WK-LATENCY-20261002", "numerical",
               "pair_receipt_P01_BRAKE-SHORT_a12.json"),
     "7d22b68cb7cc85a2dedec95b729404ae013a68985fa3ffb9782395ee5ac3ca6f"),
    ("store", ("WK-LATENCY-20261002", "numerical",
               "pair_receipt_P02_BRAKE-LONG_a12.json"),
     "e3120fb066d29fb86fc2d16bd6f806ccc10af9f84f34ee8d49490acad0a921fb"),
    ("store", ("WK-LATENCY-20261002", "numerical",
               "depth_law_receipt_a12.json"),
     "0ae8c5874cd008c76e6158544db16c7771f332780ae916f2689d16cd754eee4b"),
    ("store", ("WK-LATENCY-20261002", "numerical", "cadence_receipt.json"),
     "ad031ab1215864f7e4bfcb9b2beba1278499370ae152cd084ca3091c740e5172"),
]

# the coupling-determination inputs (sealed attempt-12 runner records)
DRIVER_PINS = [
    (A12_JOB / "receipt.json",
     "f85c0447ce0ff8cf9b27840dca31dd2dc4b309212171724d96c20359a761ef24"),
    (A12_JOB / "artifacts" / "outputs" / "driver_pair_P01_BRAKE-SHORT.json",
     "5a3ca1be4778a60d9c99ec424b3047c503f473fe665ebb1e8df079f7f77f14fb"),
    (A12_JOB / "artifacts" / "outputs" / "driver_pair_P02_BRAKE-LONG.json",
     "d63301e76da53a2ec3ae6d368a3439dbca2b78ed65281a347f58f12c90dcbc48"),
]


class Refusal(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def prereg_sha256() -> str:
    return sha_bytes(PREREG.read_bytes())


def pin_path(group, parts):
    if group == "blob":
        return PINNED_ROOT.joinpath(*parts)
    return STORE.joinpath(*parts)


def verify() -> list:
    rows = []
    for group, parts, expected in PINS:
        if group == "blob":
            data = source_access().read_blob(PIN_BASE, "/".join(parts))
        else:
            path = pin_path(group, parts)
            require(path.exists(), "input_pin_missing:" + "/".join(parts))
            data = path.read_bytes()
        got = sha_bytes(data)
        require(got == expected,
                "input_pin_mismatch:" + parts[-1] + ":" + got[:12])
        rows.append({"path": "/".join((group,) + parts), "sha256": got,
                     "expected": expected, "ok": True})
    for path, expected in DRIVER_PINS:
        require(path.exists(), "input_pin_missing:" + path.name)
        got = sha_bytes(path.read_bytes())
        require(got == expected,
                "input_pin_mismatch:" + path.name + ":" + got[:12])
        rows.append({"path": "a12:" + path.name, "sha256": got,
                     "expected": expected, "ok": True})
    return rows


def verify_base_identity() -> dict:
    parent = git_read(["rev-parse", BASE_SHA + "^"]).decode().strip()
    require(parent == PIN_BASE,
            "input_pin_mismatch:base_parent:" + parent)
    subject = git_read(["show", "-s", "--format=%s", BASE_SHA]
                          ).decode().strip()
    return {"base": BASE_SHA, "parent": parent, "subject": subject[:100]}


def verify_prereg_commit() -> dict:
    """The prereg-first law, executed: the separate-first commit exists,
    sits DIRECTLY on the X04-merged tip, touches ONLY the prereg file, and
    its blob is byte-identical to THIS card's frozen file."""
    kind = git_read(["cat-file", "-t", PREREG_COMMIT]).decode().strip()
    require(kind == "commit", "prereg_commit_not_commit:" + kind)
    parent = git_read(["rev-parse", PREREG_COMMIT + "^"]).decode().strip()
    require(parent == PIN_BASE,
            "prereg_commit_parent_not_base:" + parent)
    changed = git_read(["diff", "--name-only", PIN_BASE, PREREG_COMMIT]
                          ).decode().strip().split()
    require(changed == [PREREG_PATH],
            "prereg_commit_touches_more:" + repr(changed))
    blob = git_read(["cat-file", "blob",
                        PREREG_COMMIT + ":" + PREREG_PATH])
    got = sha_bytes(blob)
    require(got == prereg_sha256(),
            "prereg_commit_bytes_mismatch:" + got[:12])
    return {"commit": PREREG_COMMIT, "parent": parent,
            "preregistration_sha256": got, "changed_files": changed}


def verify_registry() -> dict:
    """READ-ONLY registry identity + profile check (BEFORE any capture; G7).
    The registry card for MAT2-X05 exists (state OPEN); its `presentation`
    profile carries the camera_required_fields and the three declared
    diagnostic layer names this card draws."""
    con = sqlite3.connect("file:" + str(REGISTRY).replace("\\", "/")
                          + "?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
    card = (state.get("kanban", {}).get("cards", {}) or {}).get(CARD_ID)
    require(card is not None, "criteria_pin_mismatch:card_missing")
    profile = (card["spec"]["ontology_qualification"]["task"]
               ["verification_profile"])
    require(profile.get("id") == "presentation"
            and profile.get("kind") == "motion",
            "criteria_pin_mismatch:profile_identity")
    return {"card_state": card.get("state"),
            "registry_revision": state.get("revision"),
            "profile": {"id": profile.get("id"), "kind": profile.get("kind"),
                        "subject": profile.get("subject"),
                        "scenario": profile.get("scenario"),
                        "views": profile.get("views"),
                        "clean_view_required":
                            profile.get("clean_view_required"),
                        "diagnostic_layers":
                            profile.get("diagnostic_layers"),
                        "camera_required_fields":
                            profile.get("camera_required_fields"),
                        "numerical_evidence_required":
                            profile.get("numerical_evidence_required"),
                        "falsifier": profile.get("falsifier")},
            "falsifier": (card["spec"]["ontology_qualification"]["task"]
                          .get("falsifier")),
            "done_when": (card["spec"]["ontology_qualification"]["task"]
                          .get("done_when"))}


def extract_x05_tree() -> Path:
    """Materialize THIS card's pinned blobs under slot scratch
    (byte-verified) for import identity."""
    if PINNED_ROOT.exists():
        shutil.rmtree(PINNED_ROOT)
    require(source_access().resolve_base(PIN_BASE) == "commit",
            "input_pin_mismatch:base_unresolvable")
    for group, parts, expected in PINS:
        if group != "blob":
            continue
        data = source_access().read_blob(PIN_BASE, "/".join(parts))
        require(sha_bytes(data) == expected,
                "input_pin_mismatch:extract:" + parts[-1])
        target = PINNED_ROOT.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return PINNED_ROOT


def load_pinned_module(name: str, rel_parts: tuple):
    """Import a pinned NON-package module by file path (import identity)."""
    path = PINNED_ROOT.joinpath(*rel_parts)
    require(path.exists(), "input_pin_missing:" + "/".join(rel_parts))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_package_pinned(name: str, path: Path, expected_sha: str):
    """Import a pinned module that ships INSIDE this package (the read-only
    sibling extraction), asserting its bytes against the section-1 pin."""
    require(path.exists(), "input_pin_missing:" + path.name)
    require(sha_bytes(path.read_bytes()) == expected_sha,
            "input_pin_mismatch:package:" + path.name)
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def w10_layer() -> dict:
    """Execute the W10 certified-line pin/extract layer, UNMODIFIED.

    W10's verify_inputs.py does `import source_access` at module top: the
    pinned MAT2-U07 bytes of that module (byte-verified in THIS card's
    extraction) are put on sys.path first, so the import resolves to the
    PINNED source_access — this card carries no copy of it (imported,
    never copied)."""
    u07_dir = str(PINNED_ROOT.joinpath(*U07_DIR))
    if u07_dir not in sys.path:
        sys.path.insert(0, u07_dir)
    wvi = load_pinned_module("w10_verify_inputs",
                             W10_DIR + ("verify_inputs.py",))
    rows = wvi.verify()
    reg = wvi.verify_registry()
    root = wvi.extract_pinned_tree()
    wvi.bootstrap_pinned_imports()
    w10_dir = str(PINNED_ROOT.joinpath(*W10_DIR))
    while w10_dir in sys.path:
        sys.path.remove(w10_dir)
    sys.path.insert(0, w10_dir)
    return {"w10_pin_rows": len(rows), "w10_extraction": str(root),
            "w10_registry": {k: reg[k] for k in
                             ("card_state", "criteria_sha256")}}


def u07_layer() -> dict:
    """Execute the U07 add-on pin layer (the accepted trace modules).

    verify_inputs_u07.py is NOT one of THIS card's section-1 pins (the
    frozen prereg pins U07's camera_views/controls_harness/pixel_gate/
    source_access, not its pin layer). It is loaded from THIS package's
    byte-verified MAT2-U07 sibling AFTER asserting byte-equality with the
    shared object database at THIS package's base (a runtime-recorded
    identity, never a silent copy)."""
    rel = "/".join(U07_DIR + ("verify_inputs_u07.py",))
    base_bytes = source_access().read_blob(BASE_SHA, rel)
    path = U07_SIBLING / "verify_inputs_u07.py"
    require(path.exists(), "input_pin_missing:" + rel)
    require(sha_bytes(path.read_bytes()) == sha_bytes(base_bytes),
            "input_pin_mismatch:u07_pin_layer:" + rel)
    import importlib.util
    spec = importlib.util.spec_from_file_location("u07_verify_inputs", path)
    vi7 = importlib.util.module_from_spec(spec)
    sys.modules["u07_verify_inputs"] = vi7
    spec.loader.exec_module(vi7)
    rows = vi7.verify()
    root = vi7.extract_u07_tree()
    return {"u07_pin_rows": len(rows), "u07_extraction": str(root)}


_TRACE_MODULES = None


def load_accepted_trace_modules():
    """The ACCEPTED trace module + adapter (imported, never copied) — the
    U07 layer's byte-verified extraction. Loaded ONCE and cached (one module
    identity for the whole sealed run)."""
    global _TRACE_MODULES
    if _TRACE_MODULES is not None:
        return _TRACE_MODULES
    vi7 = sys.modules.get("u07_verify_inputs")
    require(vi7 is not None, "u07_layer_not_executed")
    it = vi7.load_pinned_module(
        "u07_accepted_input_trace",
        ("tools", "monkey_campaign", "contributions", "I-U07-TRACE",
         "input_trace.py"))
    ad = vi7.load_pinned_module(
        "u07_accepted_adapter",
        ("tools", "monkey_campaign", "contributions",
         "I-U07-TRACE-FOLLOWUP", "adapter.py"))
    _TRACE_MODULES = (it, ad)
    return _TRACE_MODULES


def load_w10_modules():
    """The W10 sealed line modules (walking_demo + visualization), imported
    from THIS card's byte-verified extraction."""
    wd = load_pinned_module(
        "x05_walking_demo", W10_DIR + ("walking_demo.py",))
    vz = load_pinned_module(
        "x05_visualization", W10_DIR + ("visualization.py",))
    return wd, vz


def load_x04_state_readout():
    """The PINNED X04 state_readout (the layer machinery this card imports
    for its diagnostic context frames), byte-asserted against the section-1
    pin and loaded by file path (import identity; never edited)."""
    pin = [p for p in PINS if p[1] == X04_DIR + ("state_readout.py",)][0]
    return load_package_pinned("x04_state_readout",
                               X04_SIBLING / "state_readout.py", pin[2])


def load_visual_capture():
    """The pinned visual validator (import identity)."""
    return load_pinned_module("x05_visual_capture",
                              ("tools", "monkey_campaign",
                               "visual_capture.py"))


def driver_records() -> dict:
    """The sealed attempt-12 driver records (byte-verified above)."""
    out = {}
    for cls, name in (("SHORT", "driver_pair_P01_BRAKE-SHORT.json"),
                      ("LONG", "driver_pair_P02_BRAKE-LONG.json")):
        out[cls] = json.loads(
            (A12_JOB / "artifacts" / "outputs" / name).read_bytes())
    return out


def main() -> int:
    rows = verify()
    base = verify_base_identity()
    prereg_commit = verify_prereg_commit()
    reg = verify_registry()
    extract_x05_tree()
    w10 = w10_layer()
    u07 = u07_layer()
    summary = {"schema": "chimera.x05_input_pins.v1",
               "card": CARD_ID,
               "agent_id": "wk-x05-impl",
               "base_sha256": BASE_SHA,
               "pin_base": PIN_BASE,
               "preregistration_sha256": prereg_sha256(),
               "prereg_commit": prereg_commit,
               "base_identity": base,
               "pin_rows": rows,
               "registry": {"card_state": reg["card_state"],
                            "profile_id": reg["profile"]["id"],
                            "profile_kind": reg["profile"]["kind"]},
               "w10_layer": w10, "u07_layer": u07}
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "pins_x05.json").write_bytes(
            json.dumps(summary, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"),
                       allow_nan=False).encode("utf-8") + b"\n")
    print("pins: %d X05 rows green; W10 layer %d rows; U07 layer %d rows; "
          "profile %s/%s"
          % (len(rows), w10["w10_pin_rows"], u07["u07_pin_rows"],
             reg["profile"]["id"], reg["profile"]["kind"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as r:
        print("REFUSAL: " + str(r), file=sys.stderr)
        sys.exit(2)
