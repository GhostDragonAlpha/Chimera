"""tree_appearance — trainable domain for a stylized tree's appearance parameters.

The Construction layer (../Construction) authors a TEMPLATE tree from a reference
photo: morphology + pattern-groups + the photo's palette.  The template is
PARAMETERIZED — crown shape, foliage density, the lighting curve, colour tint,
trunk proportions: a couple dozen numbers.  Those numbers are DATA, so we TRAIN
them instead of hand-guessing (the studio's whole thesis).

THE LOOP NEVER RENDERS — statistics space only (Julesz descriptors), thousands of
evals/sec.  measure() compares the descriptor statistics the genome IMPLIES to the
descriptors EXTRACTED from the real photo.  The witness is the full render beside
the photo (render_tree(), not called in the loop).

  reference = the photo   ·   no reference, no verdict.

DOMAIN CONTRACT:
  seed(rng) -> genome            mutate(genome, rng) -> genome
  measure(genome) -> {metric: float}   # facts only; dist_* = distance to the photo
"""
from __future__ import annotations
import json, math, os
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]              # core/trainables/x.py -> Chimera/
REFNAME = os.environ.get("CHIMERA_TREE_REF", "baginton_oak")
REF_PATH = ROOT / "docs" / "tree_references" / f"{REFNAME}.json"

# The template's trainable parameters (init = the hand-authored template values).
GENOME_SCHEMA = {
    "rx":       {"min": 120.0, "max": 340.0, "init": 255.0},   # crown half-width
    "rz":       {"min":  90.0, "max": 240.0, "init": 150.0},   # crown half-height
    "zc":       {"min": 200.0, "max": 420.0, "init": 300.0},   # crown centre height
    "flat":     {"min":   0.0, "max":   1.0, "init":   0.40},  # flat-top factor
    "droop":    {"min":   0.0, "max":   1.6, "init":   1.10},  # limb droop
    "density":  {"min":   0.05,"max":   0.45,"init":   0.22},  # foliage fill
    "hf":       {"min":  90.0, "max": 280.0, "init": 180.0},   # fork height
    "base_w":   {"min":  30.0, "max":  95.0, "init":  66.0},   # trunk base half-width
    "shade_lo": {"min":   0.30,"max":   1.00,"init":   0.55},  # lighting curve floor
    "shade_hi": {"min":   1.00,"max":   1.75,"init":   1.30},  # lighting curve ceiling
    "bright":   {"min":   0.70,"max":   1.30,"init":   1.00},  # overall colour gain
    "grn":      {"min":   0.80,"max":   1.30,"init":   1.00},  # green-channel gain
}
FW, FH = 680.0, 840.0   # nominal frame the descriptors live in


# --- reference (self-loaded from committed descriptors) -------------------------
REF = None; _FOL = None
def _ensure_reference():
    global REF, _FOL
    if REF is None:
        if REF_PATH.exists():
            data = json.loads(REF_PATH.read_text())
            REF = data["descriptors"]; _FOL = np.array(data["foliage_palette"], np.float32)
            print(f"[tree_appearance] reference '{REFNAME}': LOADED {sorted(REF.keys())}")
        else:
            REF = {}; _FOL = np.tile(np.array([[0.20,0.42,0.16]],np.float32),(64,1))
            print(f"[tree_appearance] reference '{REFNAME}': MISSING at {REF_PATH} - TRAINING BLIND")
    return REF


def seed(rng=None) -> dict:
    if rng is None: rng = np.random.RandomState()
    rand = (lambda: rng.random()) if hasattr(rng, "random") else (lambda: rng.rand())
    return {f: float(s["min"] + rand()*(s["max"]-s["min"])) for f, s in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng) -> dict:
    out = dict(genome)
    for f, s in GENOME_SCHEMA.items():
        sigma = (s["max"]-s["min"]) * 0.1
        step = rng.normal(0, sigma) if hasattr(rng, "normal") else rng.gauss(0, sigma)
        out[f] = float(max(s["min"], min(s["max"], genome[f] + step)))
    return out


def _implied(genome: dict) -> dict:
    """The descriptor statistics this genome's tree would produce — computed in
    statistics space (no pixels).  Structure is analytic; colour moments are
    sampled from the photo palette through the genome's shade/tint model."""
    g = genome
    cw = 2*g["rx"]*(1 + 0.12*g["droop"]); ch = 2*g["rz"]*(1 - 0.18*g["flat"]) + g["droop"]*28
    cover = 1.0 - math.exp(-g["density"]*6.0)
    d = {
        "aspect":  cw/ch,
        "fill":    (math.pi*g["rx"]*g["rz"]*cover)/(FW*FH),
        "cy":      (FH - g["zc"])/FH,
        "cover":   cover,
        "trunk_w": g["base_w"]/g["rx"],
        "fork":    (FH - g["hf"])/FH,
    }
    rng = np.random.RandomState(42)
    cols = _FOL[rng.randint(0, len(_FOL), 4000)]
    sh = rng.uniform(g["shade_lo"], g["shade_hi"], (len(cols), 1))
    tint = np.array([g["bright"], g["bright"]*g["grn"], g["bright"]], np.float32)
    c = np.clip(cols * sh * tint, 0, 1)
    lum = 0.299*c[:,0] + 0.587*c[:,1] + 0.114*c[:,2]
    d["lum"] = float(lum.mean()); d["lstd"] = float(lum.std())
    d["grn_desc"] = float((2*c[:,1] - c[:,0] - c[:,2]).mean())
    return d


def measure(genome: dict, reference: dict | None = None) -> dict:
    ref = reference if reference is not None else _ensure_reference()
    d = _implied(genome)
    if not ref:
        return d
    dists = []
    for k, rv in ref.items():
        if k in d:
            nd = abs(d[k]-rv)/(abs(rv)+1e-6); d["dist_"+k] = float(nd); dists.append(min(nd, 3.0))
    d["fidelity"] = float(max(0.0, 1.0 - (np.mean(dists) if dists else 1.0)))
    return d


# --- reference extraction (run once; commits the descriptors) -------------------
def descriptors_from_photo(path: str) -> dict:
    from PIL import Image
    ph = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)/255.0
    H, W, _ = ph.shape
    r, g, b = ph[...,0], ph[...,1], ph[...,2]; mx = ph.max(2); mn = ph.min(2)
    green = (g>r) & (g>b) & (g>0.20) & ((mx-mn)>0.05)
    reg = np.zeros((H,W), bool); reg[int(H*0.33):int(H*0.92), int(W*0.34):int(W*0.66)] = True
    bark = reg & (~green) & (mx<0.72) & (mx>0.13)
    ys, xs = np.where(green); by, bx = np.where(bark)
    gw = xs.max()-xs.min(); gh = ys.max()-ys.min()
    fol = ph[green]; lum = 0.299*fol[:,0]+0.587*fol[:,1]+0.114*fol[:,2]
    desc = {
        "aspect":  float(gw/max(gh,1)),
        "fill":    float(green.sum()/(H*W)),
        "cy":      float(ys.mean()/H),
        "cover":   float(green.sum()/max(gw*gh,1)),
        "trunk_w": float((bx.max()-bx.min())/max(gw,1)) if len(bx) else 0.2,
        "fork":    float(by.min()/H) if len(by) else 0.4,
        "lum":     float(lum.mean()),
        "lstd":    float(lum.std()),
        "grn_desc":float((2*fol[:,1]-fol[:,0]-fol[:,2]).mean()),
    }
    idx = np.random.RandomState(0).randint(0, len(fol), 1000)
    return {"descriptors": desc, "foliage_palette": fol[idx].round(4).tolist(),
            "bark_palette": ph[bark][np.random.RandomState(1).randint(0, max(bark.sum(),1), 300)].round(4).tolist() if bark.sum() else []}


# --- witness renderer (NOT called in the training loop) -------------------------
def render_tree(genome: dict, path: str, yaw: float = 0.0, size=(860, 1080)):
    """Full stylized render from a genome — the witness, beside the photo."""
    from PIL import Image, ImageDraw
    _ensure_reference()
    g = genome; W, Hpx = size; cx = W*0.5; groundY = Hpx*0.90; SC = 1.30
    rng = np.random.default_rng(7)
    LIGHT = np.array([-0.45,-0.5,0.74]); LIGHT /= np.linalg.norm(LIGHT)
    rx, rz, zc = g["rx"], g["rz"], g["zc"]; Zb, Zt = zc-rz, zc+rz
    def bend(z): return 9*math.sin(z*0.017)-4
    def hw(z): t=z/g["hf"]; return (g["base_w"]*(1-0.42*t))*(1.0+1.05*math.exp(-t*6))
    fol_pal = _FOL
    tint = np.array([g["bright"], g["bright"]*g["grn"], g["bright"]])
    clumps=[]
    for i in range(20):
        ang=rng.uniform(0,2*math.pi); rad=math.sqrt(rng.uniform(0.04,1.0))
        X=math.cos(ang)*rx*rad; Y=math.sin(ang)*rz*1.5*rad
        Z=min(zc + rng.uniform(-0.35,0.65)*rz - (rad**2)*rz*(0.4+0.5*g["flat"]), zc+rz*0.60)
        clumps.append([X,Y,Z, rng.uniform(48,82)])
    blobs=[]
    for (X,Y,Z,cr) in clumps:
        for _ in range(int(cr*cr*g["density"]*1.6)):   # calibrated so measure.cover matches the render
            o=rng.normal(0,cr*0.60,3); base=fol_pal[rng.integers(0,len(fol_pal))]
            hf=np.clip((Z+o[2]-Zb)/(Zt-Zb+1e-6),0,1)
            lf=float(np.dot(o/(np.linalg.norm(o)+1e-6),LIGHT))
            sh=g["shade_lo"]+(g["shade_hi"]-g["shade_lo"])*hf+0.28*max(lf,0)+0.10*rng.random()
            col=tuple(np.clip(base*tint*sh*255,0,255).astype(int))
            # droop pitches outer blobs down
            zz=Z+o[2]-g["droop"]*((math.hypot(X,Y)/max(rx,1))**2)*rz*0.5
            blobs.append((X+o[0],Y+o[1],zz, rng.uniform(1.7,3.8), col))
    def proj(x,y,z,c,s): xr=x*c-y*s; return (cx+xr*SC, groundY-z*SC, x*s+y*c)
    img=Image.new("RGB",(W,Hpx)); dr=ImageDraw.Draw(img,"RGBA")
    top=np.array([150,183,216.]); bot=np.array([224,231,224.])
    for yy in range(Hpx):
        t=yy/Hpx; dr.line([(0,yy),(W,yy)],fill=tuple((top*(1-t)+bot*t).astype(int)))
    dr.ellipse([cx-260,groundY-16,cx+260,groundY+50],fill=(66,84,58,120))
    c,s=math.cos(yaw),math.sin(yaw); dep=lambda p:proj(p[0],p[1],p[2],c,s)[2]
    P=sorted(blobs,key=lambda p:-dep(p))
    for p in P:
        if dep(p)>0:
            sx,sy,_=proj(p[0],p[1],p[2],c,s); dr.ellipse([sx-p[3],sy-p[3],sx+p[3],sy+p[3]],fill=p[4]+(215,))
    tl=[(proj(bend(z)-hw(z),0,z,c,s)[0], groundY-z*SC) for z in np.linspace(0,g["hf"],30)]
    trr=[(proj(bend(z)+hw(z),0,z,c,s)[0], groundY-z*SC) for z in np.linspace(0,g["hf"],30)]
    dr.polygon(tl+trr[::-1], fill=(72,58,44,255))
    bark_pal = np.array(json.loads(REF_PATH.read_text())["bark_palette"], np.float32) if REF_PATH.exists() and json.loads(REF_PATH.read_text()).get("bark_palette") else np.array([[0.36,0.30,0.22]],np.float32)
    for _ in range(4000):
        z=rng.uniform(2,g["hf"]-4); w=hw(z); dxr=rng.uniform(-w*0.96,w*0.96)
        base=bark_pal[rng.integers(0,len(bark_pal))]; fis=0.5+0.5*abs(math.sin(dxr*0.10+z*0.02))
        sx=proj(bend(z)+dxr,0,z,c,s)[0]; sy=groundY-z*SC; rr=rng.uniform(1.4,3.0)
        dr.ellipse([sx-rr,sy-rr,sx+rr,sy+rr],fill=tuple(np.clip(base*fis*255,0,255).astype(int))+(235,))
    for p in P:
        if dep(p)<=0:
            sx,sy,_=proj(p[0],p[1],p[2],c,s); dr.ellipse([sx-p[3],sy-p[3],sx+p[3],sy+p[3]],fill=p[4]+(215,))
    img.save(path); return path


def _main():
    import argparse
    ap = argparse.ArgumentParser(prog="python -m core.trainables.tree_appearance")
    ap.add_argument("cmd", choices=["extract","render"])
    ap.add_argument("--photo"); ap.add_argument("--genome"); ap.add_argument("--out", default="tree.png")
    a = ap.parse_args()
    if a.cmd == "extract":
        data = descriptors_from_photo(a.photo)
        REF_PATH.parent.mkdir(parents=True, exist_ok=True); REF_PATH.write_text(json.dumps(data))
        print("wrote", REF_PATH, "\ndescriptors:", json.dumps(data["descriptors"], indent=2))
    else:
        g = {f: s["init"] for f, s in GENOME_SCHEMA.items()}
        if a.genome: g = json.loads(Path(a.genome).read_text()).get("genome", g)
        print("rendered", render_tree(g, a.out))

if __name__ == "__main__":
    _main()
