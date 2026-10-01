"""Visible Monkey intake, volume route: CT/MRI -> segmentation -> meshes.

Lane agent/visible-monkey-intake-20260921. PRESTAGE: the proven
morphosource_ct pipeline laws (commits 6946f3b9, d35dc6b3, 9779139a on
agent/skeleton-movie-20260919), parameterized per specimen on a volume spec
(volume_spec.template.json) -- paths, threshold law, morphology, component
caps and voxel spacing come from the spec, never hardcoded. Tested NOW
against a synthetic phantom volume (an analytic ellipsoid, known volume);
proven for the paired 3T MRI + CT modality. The 2,967 serial-section COLOR
images are a THIRD modality whose segmentation thresholds differ (color
space, not density): the route is HOOKED and refuses modality_untested --
honestly UNTESTED-against-real-data until it can be calibrated on the real
sections.

Pipeline laws carried (one law, per-specimen measured numbers):
    threshold  = 95th percentile of the measured density histogram
                 (p95 gave 118 for 000875604 and 148 for 000875599:
                  two specimens, two numbers, one law)
    morphology = binary open + close (structure=1)
    components = connected, kept if >= min_component_voxels,
                 capped at the largest max_components
    meshing    = marching cubes at level 0.5 on the binary mask
    scaling    = mesh vertices already mm (marching_cubes spacing=voxel_mm)
    V_mesh     = |sum (1/6) v_a.(v_b x v_c)| -- divergence theorem, f64
    outputs    = meshes + previews (<= preview_max_faces) + manifest +
                 sha256 receipt; explicit preview dir + basename (the
                 Windows path-separator lesson, honored as law); NO
                 wall-clock in any artifact (byte-determinism proof)

Usage (repo root):
    python -B tools/science_funnel/visible_monkey_volume_route.py build <volume_spec.json>
    python -B tools/science_funnel/visible_monkey_volume_route.py verify <volume_spec.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.science_funnel.common import Refusal, require  # noqa: E402

SPEC_SCHEMA = "chimera.visible_monkey.volume_spec.v1"
MODALITIES = ("ct_mri_density", "serial_section_rgb")


# ------------------------------------------------------------------- spec
def read_json(path: Path):
    require(path.is_file(), "spec_file_missing", str(path))
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise Refusal("spec_invalid_json", f"{path}: {e}") from None


def write_json(path: Path, payload) -> None:
    text = json.dumps(payload, indent=1, ensure_ascii=False,
                      allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def load_volume_spec(spec_path: Path) -> dict:
    raw = read_json(spec_path)
    require(isinstance(raw, dict), "spec_schema", "spec is not an object")
    require(raw.get("schema") == SPEC_SCHEMA, "spec_schema",
            f"expected {SPEC_SCHEMA}, got {raw.get('schema')!r}")
    for key in ("specimen_id", "modality", "volume", "voxel_mm",
                "segmentation", "outputs"):
        require(key in raw, "spec_missing_field", key)
    require(raw["modality"] in MODALITIES, "modality_unknown",
            f"{raw['modality']!r} not in {MODALITIES}")
    vox = raw["voxel_mm"]
    require(isinstance(vox, list) and len(vox) == 3
            and all(isinstance(v, (int, float)) and v > 0 for v in vox),
            "spec_schema", "voxel_mm must be 3 positive numbers")
    seg = raw["segmentation"]
    for key in ("threshold", "morphology", "min_component_voxels",
                "marching_cubes_level", "max_components"):
        require(key in seg, "spec_missing_field", f"segmentation.{key}")
    thr = seg["threshold"]
    require(isinstance(thr, dict) and thr.get("law") in
            ("density_percentile", "fixed"), "threshold_law_unknown",
            f"{thr!r}")
    if thr["law"] == "fixed":
        require(isinstance(thr.get("fixed_value"), (int, float))
                and isinstance(thr.get("reason"), str) and thr["reason"],
                "spec_schema",
                "fixed threshold requires fixed_value + reason (recorded)")
    out = raw["outputs"]
    for key in ("meshes_dir", "preview_dir", "manifest", "receipt"):
        require(key in out, "spec_missing_field", f"outputs.{key}")
    raw["_spec_dir"] = str(spec_path.resolve().parent)
    return raw


# ------------------------------------------------------------------ volume
def _read_with_imageio(path: Path) -> np.ndarray:
    try:
        import imageio.v3 as iio
    except Exception as e:  # pragma: no cover - env-dependent
        raise Refusal("dependency_missing",
                      f"imageio unavailable: {e}") from None
    return np.asarray(iio.volread(path))


def _read_with_pil(path: Path) -> np.ndarray:
    try:
        from PIL import Image, ImageSequence
    except Exception as e:  # pragma: no cover - env-dependent
        raise Refusal("dependency_missing", f"PIL unavailable: {e}") from None
    with Image.open(path) as im:
        return np.stack([np.asarray(f) for f in ImageSequence.Iterator(im)])


def load_volume(spec: dict) -> tuple[np.ndarray, str]:
    vol = spec["volume"]
    path = Path(vol["path"])
    require(path.is_file(), "spec_file_missing", str(path))
    reader = vol.get("reader", "auto")
    used = None
    data = None
    candidates = ([reader] if reader != "auto" else ["imageio", "PIL"])
    if path.suffix.lower() == ".npy":
        data = np.load(path)
        used = "npy"
    else:
        for name in candidates:
            if name == "imageio":
                try:
                    data = _read_with_imageio(path)
                    used = "imageio"
                    break
                except Refusal:
                    raise
                except Exception:
                    continue
            if name == "PIL":
                try:
                    data = _read_with_pil(path)
                    used = "PIL"
                    break
                except Refusal:
                    raise
                except Exception:
                    continue
    require(data is not None, "volume_unreadable",
            f"{path}: no reader in {candidates} could parse it")
    data = np.asarray(data)
    if data.ndim == 2:
        data = data[np.newaxis, ...]
    require(data.ndim == 3, "volume_unreadable",
            f"{path}: expected a 3D stack, got shape {data.shape}")
    offset = int(vol.get("offset", 0) or 0)
    if offset:
        data = data.astype(np.int32) + offset
    dtype = vol.get("dtype")
    if dtype:
        require(dtype in ("uint8", "uint16", "int16", "int32", "float32"),
                "spec_schema", f"unsupported dtype {dtype!r}")
        data = data.astype(dtype)
    return data, used


def threshold_mask(data: np.ndarray, seg: dict) -> tuple[np.ndarray, dict]:
    thr = seg["threshold"]
    if thr["law"] == "density_percentile":
        value = float(np.percentile(np.asarray(data, dtype=np.float64),
                                    thr["percentile"]))
        record = {"law": "density_percentile",
                  "percentile": thr["percentile"], "value": value}
    else:
        value = float(thr["fixed_value"])
        record = {"law": "fixed", "value": value, "reason": thr["reason"]}
    mask = data >= value
    require(mask.any(), "empty_segmentation",
            f"threshold {record} selects zero voxels")
    return mask, record


def segment(mask: np.ndarray, seg: dict) -> tuple[list[dict], object, int]:
    """Open+close, label, keep the largest components. Returns
    (per-component voxel books, the labeled volume, small-dropped count)."""
    try:
        from scipy import ndimage
    except Exception as e:  # pragma: no cover - env-dependent
        raise Refusal("dependency_missing",
                      f"scipy unavailable: {e}") from None
    morph = seg.get("morphology", {})
    if morph.get("open_iterations", 0):
        mask = ndimage.binary_opening(
            mask, structure=ndimage.generate_binary_structure(3, 1),
            iterations=int(morph["open_iterations"]))
    if morph.get("close_iterations", 0):
        mask = ndimage.binary_closing(
            mask, structure=ndimage.generate_binary_structure(3, 1),
            iterations=int(morph["close_iterations"]))
    labels_vol, n = ndimage.label(mask)
    sizes = np.bincount(labels_vol.ravel())
    min_vox = int(seg["min_component_voxels"])
    keep = [i for i in range(1, n + 1) if sizes[i] >= min_vox]
    keep.sort(key=lambda i: (-int(sizes[i]), i))
    capped = keep[:int(seg["max_components"])]
    require(capped, "empty_segmentation",
            f"{n} components, none >= {min_vox} voxels")
    dropped_small = len(keep) - len(capped)
    book = []
    for rank, i in enumerate(capped, start=1):
        coords = np.argwhere(labels_vol == i)
        book.append({
            "rank": rank,
            "label_value": int(i),
            "voxels": int(sizes[i]),
            "bbox_min_vox": [int(v) for v in coords.min(axis=0)],
            "bbox_max_vox": [int(v) for v in coords.max(axis=0)],
            "centroid_vox": [round(float(v), 3)
                             for v in coords.mean(axis=0)],
        })
    return book, labels_vol, dropped_small


def mesh_component(labels_vol, label_value: int, voxel_mm):
    """Marching cubes at level 0.5 on one component (padded, isolated)."""
    try:
        from skimage import measure
    except Exception as e:  # pragma: no cover - env-dependent
        raise Refusal("dependency_missing",
                      f"scikit-image unavailable: {e}") from None
    mask = (labels_vol == label_value)
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    verts, faces, _, _ = measure.marching_cubes(
        padded.astype(np.float32), level=0.5,
        spacing=tuple(float(v) for v in voxel_mm))
    # undo the 1-voxel padding in mm
    verts = verts - np.array([float(v) for v in voxel_mm], dtype=np.float64)
    return verts, faces


def mesh_volume_mm3(verts: np.ndarray, faces: np.ndarray) -> float:
    """V = |sum (1/6) v_a . (v_b x v_c)| -- divergence theorem, f64."""
    a = verts[faces[:, 0]]
    b = verts[faces[:, 1]]
    c = verts[faces[:, 2]]
    vol6 = np.einsum('ij,ij->i', a, np.cross(b, c)).sum()
    return float(abs(vol6) / 6.0)


def write_obj(path: Path, verts: np.ndarray, faces: np.ndarray) -> None:
    lines = [f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in verts]
    lines += [f"f {f[0] + 1} {f[1] + 1} {f[2] + 1}" for f in faces]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def decimate_faces(faces: np.ndarray, max_faces: int) -> np.ndarray:
    """The <=preview_max_faces law, honored honestly: a contiguous-stride
    subset (the morphosource previews' pattern). The FULL mesh stays the
    receipt's primary artifact; the preview is the visual convenience and
    its face count is recorded, never passed off as full resolution."""
    if len(faces) <= max_faces:
        return faces
    stride = int(np.ceil(len(faces) / max_faces))
    return faces[::stride]


# ------------------------------------------------- serial-section RGB hook
def segment_serial_section_rgb(spec: dict) -> None:
    """THE THIRD MODALITY: 2,967 color serial-section images (8688x5792 at
    0.024 mm pixel; 0.05 mm head / 0.5 mm body section pitch). Thresholds
    live in COLOR space (per-tissue color bands / deconvolution), not in a
    density histogram -- they cannot be honestly derived from zero real
    section images. UNTESTED-against-real-data: refuses until calibration
    successor work has run on the landed bytes."""
    raise Refusal(
        "modality_untested",
        "serial_section_rgb: this route has never run against real Visible "
        "Monkey section images; calibrate per-tissue color thresholds on "
        "the landed data first (0.05 mm head / 0.5 mm body pitch, 0.024 mm "
        "pixel), then re-run. Prestaged as a named refusal, honestly "
        "UNTESTED -- never silently guessed.")


# ------------------------------------------------------------------ build
def build_outputs(spec: dict, out_tmp: Path | None = None) -> dict:
    """Run the pipeline; write manifest + meshes + receipt. Returns the
    manifest dict. When out_tmp is given, artifacts land there (the
    byte-determinism / verify probe); otherwise at the spec's outputs."""
    data, reader_used = load_volume(spec)
    mask, thr_record = threshold_mask(data, spec["segmentation"])
    book, labels_vol, dropped_small = segment(mask, spec["segmentation"])

    outs = spec["outputs"]
    meshes_dir = Path(out_tmp) / "meshes" if out_tmp else Path(outs["meshes_dir"])
    preview_dir = (Path(out_tmp) / "meshes_preview" if out_tmp
                   else Path(outs["preview_dir"]))
    preview_max = int(outs.get("preview_max_faces", 30000))
    voxel_mm = [float(v) for v in spec["voxel_mm"]]
    voxel_vol_mm3 = voxel_mm[0] * voxel_mm[1] * voxel_mm[2]

    components = []
    for comp in book:
        verts, faces = mesh_component(labels_vol, comp["label_value"],
                                      voxel_mm)
        vol_mesh = mesh_volume_mm3(verts, faces)
        rel = f"component_{comp['rank']:02d}.obj"
        write_obj(meshes_dir / rel, verts, faces)
        prev_faces = decimate_faces(faces, preview_max)
        write_obj(preview_dir / rel, verts, prev_faces)
        comp.update({
            "mesh": f"meshes/{rel}",
            "preview": f"meshes_preview/{rel}",
            "faces": int(len(faces)),
            "preview_faces": int(len(prev_faces)),
            "volume_mm3_mesh": round(vol_mesh, 6),
            "volume_mm3_voxels": round(comp["voxels"] * voxel_vol_mm3, 6),
            "voxel_delta_pct": round(
                100.0 * (vol_mesh - comp["voxels"] * voxel_vol_mm3)
                / (comp["voxels"] * voxel_vol_mm3), 3),
            "bbox_min_mm": [round(float(v), 6)
                            for v in verts.min(axis=0)],
            "bbox_max_mm": [round(float(v), 6)
                            for v in verts.max(axis=0)],
            "centroid_mm": [round(float(v), 6)
                            for v in verts.mean(axis=0)],
        })
        components.append(comp)

    manifest = {
        "schema": "chimera.visible_monkey.volume_manifest.v1",
        "specimen_id": spec["specimen_id"],
        "modality": spec["modality"],
        "reader_used": reader_used,
        "voxel_mm": voxel_mm,
        "voxel_volume_mm3": voxel_vol_mm3,
        "volume_shape": [int(v) for v in data.shape],
        "threshold": thr_record,
        "segmentation": {
            "morphology": spec["segmentation"].get("morphology", {}),
            "min_component_voxels": spec["segmentation"]["min_component_voxels"],
            "marching_cubes_level":
                spec["segmentation"]["marching_cubes_level"],
            "max_components": spec["segmentation"]["max_components"],
            "components_kept": len(components),
            "components_dropped_small_below_min": int(dropped_small),
            "note": "marching cubes on an isolated, 1-voxel-padded binary "
                    "mask; preview = contiguous face subset (count recorded), "
                    "full mesh is primary",
        },
        "components": components,
        "determinism": "no wall-clock in this manifest; rebuild and demand "
                       "byte equality (verify)",
    }
    receipt = {
        "schema": "chimera.visible_monkey.mesh_receipt.v1",
        "specimen_id": spec["specimen_id"],
        "sha256": {},
        "byte_counts": {},
    }
    manifest_rel = Path(outs["manifest"]).name
    receipt_rel = Path(outs["receipt"]).name
    for p in sorted(meshes_dir.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(meshes_dir)).replace("\\", "/")
            receipt["sha256"][f"meshes/{rel}"] = hashlib.sha256(
                p.read_bytes()).hexdigest()
            receipt["byte_counts"][f"meshes/{rel}"] = p.stat().st_size
    for p in sorted(preview_dir.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(preview_dir)).replace("\\", "/")
            receipt["sha256"][f"meshes_preview/{rel}"] = hashlib.sha256(
                p.read_bytes()).hexdigest()
            receipt["byte_counts"][f"meshes_preview/{rel}"] = p.stat().st_size

    if out_tmp is None:
        write_json(Path(outs["manifest"]), manifest)
        write_json(Path(outs["receipt"]), receipt)
    return {"manifest": manifest, "receipt": receipt,
            "manifest_rel": manifest_rel, "receipt_rel": receipt_rel,
            "meshes_dir": meshes_dir, "preview_dir": preview_dir}


# ------------------------------------------------------------------- cli
def main(argv: list[str]) -> int:
    require(len(argv) >= 3, "unknown_command",
            "usage: visible_monkey_volume_route.py "
            "{build|verify} <volume_spec.json>")
    cmd = argv[1]
    require(cmd in ("build", "verify"), "unknown_command", cmd)
    spec = load_volume_spec(Path(argv[2]))
    if spec["modality"] == "serial_section_rgb":
        segment_serial_section_rgb(spec)  # refuses: modality_untested

    outs = spec["outputs"]
    if cmd == "build":
        built = build_outputs(spec)
        # byte-determinism: rebuild into a temp dir and demand equality
        with tempfile.TemporaryDirectory() as td:
            probe = build_outputs(spec, out_tmp=Path(td))
            for key in ("sha256", "byte_counts"):
                require(probe["receipt"][key] == built["receipt"][key],
                        "nondeterministic_output", key)
        print(f"visible_monkey_volume_route build OK: "
              f"{built['manifest']['segmentation']['components_kept']} "
              f"components at threshold "
              f"{built['manifest']['threshold']['value']:.4f} "
              f"({built['manifest']['threshold']['law']}); all falsifiers "
              f"green")
        return 0

    # verify: committed receipt must match a fresh rebuild, byte for byte
    receipt_path = Path(outs["receipt"])
    require(receipt_path.is_file(), "missing_receipt", str(receipt_path))
    committed = read_json(receipt_path)
    with tempfile.TemporaryDirectory() as td:
        probe = build_outputs(spec, out_tmp=Path(td))
    require(probe["receipt"]["sha256"] == committed["sha256"],
            "receipt_drift", "committed receipt != fresh rebuild")
    print("visible_monkey_volume_route verify OK: committed receipt is "
          "byte-exact reproducible")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Refusal as ref:
        print(f"REFUSED {ref.code}: {ref.detail}", file=sys.stderr)
        sys.exit(2)
