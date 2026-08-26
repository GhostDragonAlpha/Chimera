import sys, os, time, json, argparse

# Force anonymous HuggingFace access: a stale HF token in the environment makes
# huggingface_hub send bad credentials and 401 on otherwise-public repos.
for _k in list(os.environ):
    if 'HF_' in _k or 'HUGGINGFACE' in _k or _k == 'HF_TOKEN':
        del os.environ[_k]

sys.path.insert(0, r"E:\PythonChimera\.tmp\trellis-py")
os.environ.setdefault("SPCONV_ALGO", "native")
# Use PyTorch's built-in scaled-dot-product attention instead of flash-attn
# (which is a heavy CUDA build). Mathematically identical; no extra install.
os.environ["ATTN_BACKEND"] = "sdpa"

import torch
from trellis.pipelines import TrellisTextTo3DPipeline
import trimesh

MODEL = "microsoft/TRELLIS-text-xlarge"
MESH_DIR = r"E:\PythonChimera\models\trellis"
RESULT_DIR = r"E:\PythonChimera\tools\t23d\results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="a soft plush teddy bear")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_name = (args.out or "teddy").replace(" ", "_")

    print("Ensuring weights are present (downloads on first run)...", flush=True)
    t0 = time.time()
    from huggingface_hub import snapshot_download
    L = r"E:\PythonChimera\.tmp\trellis-ckpt"
    os.makedirs(L, exist_ok=True)
    # Text pipeline's own flow models (live in the microsoft repo under ckpts/).
    snapshot_download(
        "microsoft/TRELLIS-text-xlarge",
        allow_patterns=["pipeline.json",
                       "ckpts/ss_flow_txt_dit_XL_16l8_fp16.*",
                       "ckpts/slat_flow_txt_dit_XL_64l8p2_fp16.*"],
        local_dir=L,
    )
    # Decoders are reused from the image-large repo; mirror them under their full
    # repo-relative path so base.py's f"{path}/{v}" resolves locally for every model.
    jf_local = os.path.join(L, "JeffreyXiang", "TRELLIS-image-large")
    snapshot_download(
        "JeffreyXiang/TRELLIS-image-large",
        allow_patterns=["ckpts/ss_dec_conv3d_16l8_fp16.*",
                       "ckpts/slat_dec_gs_swin8_B_64l8gs32_fp16.*",
                       "ckpts/slat_dec_rf_swin8_B_64l8r16_fp16.*",
                       "ckpts/slat_dec_mesh_swin8_B_64l8m256c_fp16.*"],
        local_dir=jf_local,
    )
    pipe = TrellisTextTo3DPipeline.from_pretrained(L)
    print(f"[{time.time()-t0:.1f}s] Pipeline loaded from {L}", flush=True)

    print("Sampling...", flush=True)
    torch.cuda.empty_cache()
    t0 = time.time()
    res = pipe.run(args.prompt, num_samples=1, seed=args.seed, formats=['mesh'])
    m = res['mesh'][0]
    V = m.vertices.detach().cpu().numpy().astype('float32')
    F = m.faces.detach().cpu().numpy().astype('int64')
    print(f"[{time.time()-t0:.1f}s] Sampled. verts={V.shape[0]} faces={F.shape[0]}", flush=True)

    tm = trimesh.Trimesh(vertices=V, faces=F, process=False)
    E = len(tm.edges)
    info = {
        "model": MODEL,
        "prompt": args.prompt,
        "seed": args.seed,
        "vertices": int(V.shape[0]),
        "triangles": int(F.shape[0]),
        "edges": int(E),
        "euler_number": int(V.shape[0]) - E + int(F.shape[0]),
        "watertight": bool(tm.is_watertight),
        "winding_consistent": bool(tm.is_winding_consistent),
    }

    os.makedirs(MESH_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    obj_path = os.path.join(MESH_DIR, f"{out_name}.obj")
    glb_path = os.path.join(MESH_DIR, f"{out_name}.glb")
    tm.export(obj_path)
    try:
        tm.export(glb_path)
    except Exception as e:
        print("GLB export failed:", repr(e), flush=True)
    with open(os.path.join(RESULT_DIR, f"trellis_text_{out_name}_info.json"), "w") as f:
        json.dump(info, f, indent=2)

    print(json.dumps(info, indent=2), flush=True)
    print("Exported:", obj_path, glb_path, flush=True)


if __name__ == "__main__":
    main()
