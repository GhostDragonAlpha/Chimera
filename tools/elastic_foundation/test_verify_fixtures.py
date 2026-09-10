"""pytest controls for tools/elastic_foundation/verify_fixtures.py.

Gen5 correction evidence (elastic-ref-publish, lead review findings 1 and 2):

  NEGATIVE 1  mutating a NONMAXIMUM component of exp_vertex_f64 in a PRIVATE
              temp fixture copy (manifest hash refreshed, isolating the
              numerical oracle from the hash leg) must exit 1. Guards the
              declared relative-Linf comparison against any future regression
              to a scalar/extremum reduction.
  NEGATIVE 2  empty evidence cannot satisfy verification: a version directory
              with no run_* children exits 1; a run directory whose manifest
              lists zero fixtures exits 1. Neither writes a sidecar.
  POSITIVE    the real frozen v1 fixtures still verify (exit 0, rel err 0.0)
              from a TEMP COPY of the fixture root, and the recomputed
              sidecar stays byte-identical to the tracked one (gen-6 lead
              correction: the tracked tree is never a write target).

Synthetic fixtures are built with the committed law itself in pytest tmp_path
roots; no file under docs/evidence is ever written by the negative controls.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.elastic_foundation import geometry as G  # noqa: E402
from tools.elastic_foundation import law as L  # noqa: E402
from tools.elastic_foundation import materials as M  # noqa: E402
from tools.elastic_foundation import verify_fixtures as vf  # noqa: E402

REAL_FIX_ROOT = vf.FIX_ROOT


def _build_npz(dirp: Path, fname: str, cur_pos: np.ndarray,
               mutate=None) -> dict:
    """Write one synthetic fixture npz + return its manifest metadata.

    Reference answers are computed WITH the committed law from the fixture's
    own arrays, so an unmutated copy is exactly self-consistent.
    """
    pos_r = np.array([[0.0, 0.0, 0.0],
                      [1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])
    faces = np.array([[0, 1, 2]], dtype=np.int32)
    geom = G.build_rest_geometry(pos_r, faces.astype(np.int64))
    material = M.synthetic(E=1.0, nu=0.3, h=1.0)
    ev = L.evaluate_elastic(geom, material, np.asarray(cur_pos, dtype=np.float64))
    arrays = {
        "rest_pos": pos_r,
        "faces_int32": faces,
        "cur_pos": np.asarray(cur_pos, dtype=np.float64),
        "E_f64": np.float64(1.0),
        "nu_f64": np.float64(0.3),
        "h_f64": np.float64(1.0),
        "exp_energy_f64": np.float64(ev.energy),
        "exp_vertex_f64": np.asarray(ev.vertex_forces, dtype=np.float64),
        "exp_source": np.str_("synthetic"),
    }
    if mutate is not None:
        mutate(arrays)
    path = dirp / fname
    np.savez(path, **arrays)
    return {"file": fname, "sha256": vf.sha256_bytes(path.read_bytes())}


def _strained_cur():
    """A state with real force spread so a nonmaximum component exists."""
    return np.array([[0.0, 0.0, 0.0],
                     [1.05, 0.0, 0.0],
                     [0.0, 1.02, 0.0]])


def _make_run(run_dir: Path, fname: str, mutate=None) -> None:
    run_dir.mkdir(parents=True)
    meta = _build_npz(run_dir, fname, _strained_cur(), mutate=mutate)
    (run_dir / "manifest.json").write_text(
        json.dumps({"fixtures": {fname: meta}}, indent=2), encoding="utf8")


def _args(version: str, all_runs: bool = False):
    import argparse
    return argparse.Namespace(version=version, all=all_runs)


def test_nonmaximum_component_mutation_fails(tmp_path):
    # Positive control on the same synthetic construction: clean copy passes.
    good = tmp_path / "good"
    _make_run(good / "run_x", "tri.npz")
    rc = vf.run(_args("good"), fix_root=tmp_path)
    assert rc == 0
    clean = json.loads((good / ".verified.json").read_text(encoding="utf8"))
    rec = clean["fixtures"]["run_x/tri.npz"]
    assert clean["all_ok"] is True
    assert rec["vertex_rel_err"] == pytest.approx(0.0, abs=1e-12)

    # Negative control, mirroring the lead's reproduction protocol: mutate a
    # NONMAXIMUM component by -1000 (a negative spike; the old verifier compared
    # SIGNED maxima, so this was invisible), then refresh the manifest sha to
    # isolate oracle validation from hash validation. The SIGNED max of the
    # expected array must be unchanged by the mutant -- that is precisely why
    # the old scalar reduction returned 0.0.
    mutated = tmp_path / "mut"

    def bump(arrays):
        vref = arrays["exp_vertex_f64"]
        smax_idx = int(np.argmax(vref))          # signed max: what the old code compared
        idx = 1 if smax_idx != 1 else 0
        assert idx != smax_idx
        before_smax = float(np.max(vref))
        vref.flat[idx] -= 1000.0
        assert float(np.max(vref)) == pytest.approx(before_smax, rel=1e-12)

    _make_run(mutated / "run_x", "tri.npz", mutate=bump)
    rc = vf.run(_args("mut"), fix_root=tmp_path)
    assert rc == 1, "mutant passed: the oracle still misses a single component"
    out = json.loads((mutated / ".verified.json").read_text(encoding="utf8"))
    rec = out["fixtures"]["run_x/tri.npz"]
    assert out["all_ok"] is False
    # The mutated component dominates the Linf denominator, so the relative
    # error is O(1) -- thirteen orders of magnitude above the 512*eps budget.
    assert rec["vertex_rel_err"] > 0.5


def test_empty_version_directory_refused(tmp_path):
    (tmp_path / "hollow").mkdir()
    rc = vf.run(_args("hollow"), fix_root=tmp_path)
    assert rc == 1
    assert not (tmp_path / "hollow" / ".verified.json").exists()


def test_missing_version_directory_refused(tmp_path):
    rc = vf.run(_args("never-existed"), fix_root=tmp_path)
    assert rc == 1


def test_zero_fixture_manifest_refused(tmp_path):
    run_dir = tmp_path / "hollow" / "run_x"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(
        json.dumps({"fixtures": {}}), encoding="utf8")
    rc = vf.run(_args("hollow"), fix_root=tmp_path)
    assert rc == 1
    assert not (tmp_path / "hollow" / ".verified.json").exists()


def test_real_v1_baseline_green_and_sidecar_byte_identical(tmp_path):
    """The frozen v1 fixtures must still pass -- verified against a TEMP COPY
    of the fixture root (gen-6 lead correction: never run the verifier on the
    tracked tree, so the tracked historical sidecar is never a write target).
    The recomputed sidecar must be byte-identical to the tracked one, which
    additionally proves the tracked sidecar is exactly what a completed
    verification of the current frozen fixtures produces."""
    import shutil
    work = tmp_path / "fixtures"
    shutil.copytree(REAL_FIX_ROOT / "v1", work / "v1")
    before = (work / "v1" / ".verified.json").read_bytes()
    tracked = (REAL_FIX_ROOT / "v1" / ".verified.json").read_bytes()
    assert before == tracked, "tracked sidecar drifted from its committed copy"
    rc = vf.run(_args("v1"), fix_root=work)
    after = (work / "v1" / ".verified.json").read_bytes()
    assert rc == 0
    out = json.loads(after.decode("utf8"))
    assert out["all_ok"] is True
    for name, rec in out["fixtures"].items():
        assert rec["sha256_ok"] is True
        assert rec["energy_rel_err"] == 0.0
        assert rec["vertex_rel_err"] == 0.0
    assert before == after, "recompute changed the sidecar in the temp copy"
    assert tracked == after


def test_rel_array_rejects_shape_mismatch_and_nonfinite():
    a = np.zeros((3, 1))
    with pytest.raises(ValueError):
        vf.rel_array(a, np.zeros((4, 1)))
    with pytest.raises(ValueError):
        vf.rel_array(np.array([np.nan]), np.array([1.0]))
    with pytest.raises(ValueError):
        vf.rel_scalar(float("nan"), 1.0)


def test_rel_array_sees_nonmaximum_component():
    computed = np.array([0.111939437687397, -0.0006731960777193167])
    expected = np.array([0.111939437687397, -0.0006731960777193167])
    assert vf.rel_array(computed, expected) == pytest.approx(0.0, abs=1e-15)
    bumped = computed.copy()
    bumped[1] -= 1000.0
    # negative spike on a nonmaximum component (the old signed-max reduction
    # never saw it); the mutated value dominates the Linf denominator, so the
    # relative error is O(1) -- astronomically above the 512*eps budget
    err = vf.rel_array(bumped, expected)
    assert err > 0.5
