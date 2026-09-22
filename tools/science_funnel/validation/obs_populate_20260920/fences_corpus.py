#!/usr/bin/env python3
"""THE OBS-POPULATE FENCES (F3 TABLE-INVARIANCE, F4 CORPUS-REFREEZE) + the
3-run determinism comparator (F5) -- lane/obs-populate-20260920, preregistered
in record.md BEFORE the delivery build.

Usage:
  python fences_corpus.py pins <control_aliased_pairs.json>
  python fences_corpus.py determinism <run1_dir> <run2_dir> <run3_dir>

pins   -- F3: the frozen 80-field table regenerates BYTE-IDENTICAL from the
          live code + the pinned section; F4: every pinned hash holds (P3
          manifest 9ca7e976, P3 action-stream replay 3-run e25406e8, section
          3de82a11, table file e8c2d698, slice 69babe84, legacy 64-literal),
          and the CONTROL mine's fresh aliased_pairs.json is byte-identical to
          the interface-freeze lane's pinned artifact (their instrument
          reproduces on the fresh trace -- the F2 census clause).
          The ONE declared mover (F4, cause registered in the prereg) is the
          observation stream itself: delivered field + mask census (measured
          by the mine, not here).
determ -- F5: the three treatment runs' artifacts are byte-identical.

Exit 0 iff every clause holds; any fired clause prints FIRED and exits 1
(never tuned away).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
VALDIR = os.path.join(REPO, "tools", "science_funnel", "validation")
IFREEZE = os.path.join(VALDIR, "policy_interface_freeze_20260920")
OBSSPLIT = os.path.join(VALDIR, "obs_split_channels_20260921")
P3VAL = os.path.join(VALDIR, "typeb_p3_20260921")
sys.path.insert(0, EXPORT)

TABLE_SHA = "e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c"
SECTION_SHA = "3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079"
MANIFEST_HASH = "9ca7e976dfb0dedd3f56dfa404673ee77c00801acb2753cdfd83604c480c35b7"
REPLAY_SHA = "e25406e86cbf5347683ee3824d385bc1d07bfd500e83eb6b9133a1e82d4bfbd9"
SLICE_SHA = "69babe846e2447333b527c7fd8c190499e5ac1d55733dbd043edd0422245daa2"

ok = True
def check(name: str, cond: bool, detail: str = "") -> None:
    global ok
    ok &= bool(cond)
    print(("GREEN " if cond else "FIRED ") + name + (" -- " + detail if detail else ""))


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def pins(control_json: str) -> None:
    import interface_freeze  # noqa: E402
    import legacy_v1_table  # noqa: E402
    import observation_schema as oschema  # noqa: E402

    # ---- F3: the table regenerates byte-identical
    committed = open(os.path.join(IFREEZE, "observation_interface_v2.json"), "rb").read()
    regen = interface_freeze.regen_bytes(os.path.join(OBSSPLIT, "obs_section_v2.json"))
    check("F3 table byte-regeneration", committed == regen,
          "sha %s (%d bytes)" % (hashlib.sha256(committed).hexdigest()[:16], len(committed)))
    check("F3 table file sha", sha256_file(os.path.join(IFREEZE, "observation_interface_v2.json")) == TABLE_SHA,
          "pinned " + TABLE_SHA[:16])
    check("F3 OBS_SCHEMA_VERSION stays 2", oschema.OBS_SCHEMA_VERSION == 2,
          "v%d, OBS_DIM %d" % (oschema.OBS_SCHEMA_VERSION, oschema.OBS_DIM))

    # ---- F4: the pins that must NOT move
    check("F4 section sha (normalization source)",
          sha256_file(os.path.join(OBSSPLIT, "obs_section_v2.json")) == SECTION_SHA,
          "pinned " + SECTION_SHA[:16])
    check("F4 legacy 64-literal",
          [{k: f[k] for k in ("name", "group", "source", "unit", "frame",
                              "privileged", "dtype", "shape")}
           for f in oschema.FIELDS[:64]] == legacy_v1_table.LEGACY_FIELDS,
          "FIELDS[:64] == the frozen v1 table")

    import policy_manifest as pman  # noqa: E402
    m = pman.load_manifest(os.path.join(P3VAL, "policy_manifest.json"),
                           os.path.join(P3VAL, "dummy_actor.npz"))
    check("F4 P3 manifest hash", m["manifest_hash"] == MANIFEST_HASH,
          "got %s" % m["manifest_hash"][:16])
    check("F4 P3 slice sha", sha256_file(os.path.join(P3VAL, "trace_slice_wave38.json")) == SLICE_SHA,
          "pinned " + SLICE_SHA[:16])

    # the P3 action stream replay, 3 runs in-process (the interface-freeze
    # test's procedure verbatim)
    import numpy as np  # noqa: E402
    from infer_numpy import NumpyPolicy  # noqa: E402
    from run_f_cpu_policy_bytes import fixed_obs_sequence, replay  # noqa: E402
    params = dict(np.load(os.path.join(P3VAL, "dummy_actor.npz")))
    ev = m["evaluation"]["fixed_obs_sequence"]
    seq = fixed_obs_sequence(os.path.join(P3VAL, "trace_slice_wave38.json"),
                             ev["passes"], ev["n_ticks"])
    shas = set()
    for _ in range(3):
        policy = NumpyPolicy(m, params)
        stream, decisions = replay(policy, seq)
        assert len(decisions) == ev["n_decisions"]
        shas.add(hashlib.sha256(stream).hexdigest())
    check("F4 P3 action-stream replay 3-run", shas == {REPLAY_SHA},
          "sha %s" % shas.pop()[:16])

    # the CONTROL instrument reproduces the pinned census on the fresh trace
    fresh = json.loads(open(control_json, "rb").read().decode("utf-8"))
    pinned = json.loads(open(os.path.join(IFREEZE, "aliased_pairs.json"),
                             "rb").read().decode("utf-8"))
    check("F2 control census byte-equal (fresh mine == pinned artifact)",
          fresh == pinned,
          "%d aliased pairs, %d distinct obs, trace %s..."
          % (len(pinned["aliased_pairs"]), pinned["distinct_observations"],
             pinned["trace_sha256"][:8]))

    print("FENCES VERDICT:", "GREEN" if ok else "FIRED")
    sys.exit(0 if ok else 1)


def determinism(dirs: list[str]) -> None:
    global ok
    names = ("aliased_pairs_after.json", "pair_ledger.json", "mine_obs_populate_out.txt")
    for n in names:
        blobs = [open(os.path.join(d, n), "rb").read() for d in dirs]
        check("F5 determinism 3-run byte-identical: " + n,
              all(b == blobs[0] for b in blobs),
              "sha %s" % hashlib.sha256(blobs[0]).hexdigest()[:16])
    print("FENCES VERDICT:", "GREEN" if ok else "FIRED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if sys.argv[1] == "pins":
        pins(sys.argv[2])
    elif sys.argv[1] == "determinism":
        determinism(sys.argv[2:5])
    else:
        raise SystemExit("unknown mode: " + sys.argv[1])
