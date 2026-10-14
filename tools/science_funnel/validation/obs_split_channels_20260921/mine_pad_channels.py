#!/usr/bin/env python3
"""THE OBS-SPLIT-CHANNELS MINE (declared instrument; prereg frozen at 97fd15fb
BEFORE this build). Reads THE WAVE-47 PRESERVED TRACE OUTPUTS ONLY:

  the wave-47 declared ship trace (f106fc54 build), sha256
  c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481,
  65870 lines -- verified before every use; parse convention =
  mine_wave47.py VERBATIM (LAST walk run, [dvfa]/[dvfl] first-sample per
  (t,leg), [hindstep] dedup, wave-46 calibration: plane_model_y_ = pad
  radius = 0.004, split_abs = 2*(pad_y - gmin), sref = 2*(pad_y(f) -
  gmin(f+1)), era span [fire, ct]).

THE THREE FALSIFIERS (prereg obs_split_channels_20260921/prereg.json):

  F-CHANNELS-DISTINCT  the identity gate (the retrospective's rule, first
                       use): the band's collapsed pair is the CONTROL
                       (g1 == g2 measured); the reconstructed individual
                       pair (g_lo = gmin, g_hi = 2*pad_y - g_lo) must be
                       DISTINCT: the reconstruction identity on every
                       sample, split_abs > kTouch on a measured fraction,
                       non-degeneracy vs the min channel.
  F-CHANNELS-SEPARATE  the class backfill: the PROJECTED channels (the V2
                       schema, ordering 'lohi') must reproduce
                       mine_wave47_out.txt -- the 18-era census, the 12/12
                       never-crossed cross-check, the class envelopes and
                       THE SEPARATING WINDOWS intact, the projector
                       round-trip, and the mask honesty (endpoint-signed
                       channels declared unavailable on EVERY wave-47
                       record: the endpoint identity is not in the
                       preserved outputs).
  F-CHANNELS-INERT     the pure-addition gate: the scope diff vs 9808dc94
                       touches only the declared paths (zero engine
                       bytes); P3's frozen block equals the 1b6d7749
                       literal; P3's banked action stream replays
                       byte-identically through the extended schema.

Output: mine_pad_channels_out.txt (this run's preserved output) and
band_channels_wave47.json (the extracted channel inputs, pinned to the
trace sha). Read-only over the trace; zero engine bytes.
"""
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
P3VAL = os.path.join(REPO, "tools", "science_funnel", "validation", "typeb_p3_20260921")
sys.path.insert(0, EXPORT)

import observation_schema as oschema  # noqa: E402
import pad_channels  # noqa: E402
import legacy_v1_table  # noqa: E402
import policy_manifest as pman  # noqa: E402
from infer_numpy import NumpyPolicy  # noqa: E402
from run_f_cpu_policy_bytes import fixed_obs_sequence, replay  # noqa: E402

TRACE = os.environ.get(
    "W47_TRACE",
    r"E:\ChimeraWork\w47-agent\.tmp\w47_receipt\base_tr_stderr.txt")
TRACE_SHA = pad_channels.WAVE47_TRACE_SHA256
KTOUCH = pad_channels.KTOUCH

# ---- the frozen reference (mine_wave47_out.txt, preserved in this dir) ----
W45_MAXLEV_MM = {161: -3.142, 175: -0.003, 184: 0.151, 193: -0.497, 220: 6.902,
                 229: 9.125, 238: 7.476, 247: 11.577, 256: 0.468, 265: 16.426,
                 291: -6.416, 300: 0.551}
EXPECT = dict(
    lift_lev=(6.902, 16.426), lift_rate=(0.767, 1.825), lift_inc=(0.872, 2.233),
    stall_lev=(-6.416, 0.551), stall_rate=(-0.713, 0.275), stall_inc=(-2.506, 0.536),
    win_level=(0.551, 6.902), win_rate=(0.275, 0.767), win_inc=(0.536, 0.872))
CENSUS_REF = [  # (fire, ct, leg, label, class, span, nSamp) -- the 18 era rows
    (98, 107, 1, "LIFT", "slot", 9, 1), (142, 160, 0, "LIFT", "alt", 18, 1),
    (160, 174, 1, "LIFT", "alt", 14, 1), (161, 170, 0, "STALL", "alt", 9, 9),
    (175, 184, 0, "STALL", "alt", 9, 9), (184, 193, 1, "STALL", "alt", 9, 9),
    (193, 202, 0, "STALL", "alt", 9, 9), (202, 211, 1, "LIFT", "alt", 9, 4),
    (211, 220, 0, "LIFT", "alt", 9, 4), (220, 229, 1, "LIFT", "alt", 9, 9),
    (229, 238, 0, "LIFT", "alt", 9, 9), (238, 247, 1, "LIFT", "alt", 9, 9),
    (247, 256, 0, "LIFT", "alt", 9, 9), (256, 265, 1, "STALL", "alt", 9, 9),
    (265, 274, 0, "LIFT", "alt", 9, 9), (274, 291, 1, "STALL", "alt", 17, 1),
    (291, 300, 0, "STALL", "alt", 9, 9), (300, 302, 1, "STALL", "alt", 2, 2),
]

out_lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out_lines.append(s)
    print(s)

P("THE OBS-SPLIT-CHANNELS MINE -- the wave-47 preserved trace outputs,")
P("trace:", TRACE)
P("=" * 150)

# ============================ the parse =====================================
sha = pad_channels.sha256_file(TRACE)
n_lines = sum(1 for _ in open(TRACE, encoding="utf-8", errors="replace"))
P("trace sha256:", sha, sha == TRACE_SHA and "PIN-MATCH" or "SHA-MISMATCH ** FIRES **")
P("trace lines:", n_lines, "(pinned 65870)")
parsed = pad_channels.parse_wave4x_trace(TRACE, expect_sha256=TRACE_SHA)
recon = pad_channels.reconstruct_pairs(parsed)
P("refusal:", parsed["refusal"], " fires:", len(parsed["fires"]),
  " tds:", len(parsed["tds"]),
  " dvfl (t,leg) first-sample series:", recon["n_band_lines"],
  " reconstructed (dvfa AND dvfl):", recon["n_reconstructed"])
P("-" * 150)

# ==================== F-CHANNELS-DISTINCT (the identity gate) ================
P("F-CHANNELS-DISTINCT (the identity gate; the retrospective's rule, first use)")
P("  CONTROL -- the band's printed pair ([dvfl] g1 vs g2, the pair-min printed twice):")
import re
n_ctl = n_eq = 0
for l in open(TRACE, encoding="utf-8", errors="replace"):
    if l.startswith("[dvfl]"):
        m = re.match(r"\[dvfl\] t=\d+ leg=\d g1=(\S+) g2=(\S+)", l)
        n_ctl += 1
        if float(m.group(1)) == float(m.group(2)):
            n_eq += 1
P("    whole-file [dvfl] lines: %d   |g1-g2| == 0: %d   (the collapsed pair: the"
  " band view reads gap_of TWICE at two pair-based endpoints)" % (n_ctl, n_eq))
pairs = recon["pairs"]
samples = [(t, leg, p) for t in sorted(pairs) for leg, p in pairs[t].items()]
ident_res = max(abs(p["split_abs"] - 2.0 * (p["pad_y"] - p["gmin"]))
                for _, _, p in samples)
ident_ok = ident_res <= 1e-9
sabs = np.array([p["split_abs"] for _, _, p in samples])
gmin = np.array([p["gmin"] for _, _, p in samples])
n_above = int((sabs > KTOUCH).sum())
frac_above = n_above / len(samples)
max_sabs_mm = float(sabs.max()) * 1e3
min_sabs_mm = float(sabs.min()) * 1e3
std_sabs = float(sabs.std())
corr = float(np.corrcoef(sabs, gmin)[0, 1]) if std_sabs > 0 else 1.0
P("  TREATMENT -- the reconstructed individual pair (g_lo=gmin, g_hi=2*pad_y-g_lo):")
P("    reconstructed (t,leg) samples: %d" % len(samples))
P("    (a) reconstruction identity |split_abs - 2*(pad_y-gmin)| max: %.3e m (<= 1e-9: %s)"
  % (ident_res, ident_ok))
P("    (b) split_abs > kTouch=1e-5 m: %d/%d samples (%.1f%%);  max split_abs = %+.3f mm;  min = %+.3f mm"
  % (n_above, len(samples), 100.0 * frac_above, max_sabs_mm, min_sabs_mm))
P("    (c) non-degeneracy: std(split_abs) = %.6e m (>0: %s);  corr(split_abs, gmin) = %+.6f (|c|<1: %s)"
  % (std_sabs, std_sabs > 0, corr, abs(corr) < 1.0))
distinct = ident_ok and n_above > 0 and std_sabs > 0 and abs(corr) < 1.0
P("  F-CHANNELS-DISTINCT: %s" % ("GREEN" if distinct else "** FIRED **"))
P("-" * 150)

# ==================== the projection (the V2 harness) ========================
records = pad_channels.build_records(recon)
projections = pad_channels.project_records(records)
chan = pad_channels.channel_split_abs_series(records, projections)
series = chan["series"]
masks = chan["masks"]

# ---- the round-trip + the mask census (F-CHANNELS-SEPARATE clauses) --------
i_abs = {leg: oschema.FIELD_NAMES.index("pad_split_abs_" + leg) for leg in ("hl", "hr")}
i_end = {oschema.FIELD_NAMES.index(n) for n in oschema.FIELD_NAMES[64:68]}
i_sig = {oschema.FIELD_NAMES.index(n) for n in
         [f"pad_split_{l}" for l in ("hl", "hr")]
         + [f"pad_split_rate_{l}" for l in ("hl", "hr")]}
rt_max = 0.0
for rec, (obs, mask) in zip(records, projections):
    t = rec["tick"]
    for leg_idx in (0, 1):
        if t in series and leg_idx in series[t]:
            rt_max = max(rt_max, abs(series[t][leg_idx] - pairs[t][leg_idx]["split_abs"]))
n_abs_avail = sum(len(v) for v in masks.values())
endpoint_avail = 0
signed_avail = 0
for rec, (obs, mask) in zip(records, projections):
    endpoint_avail += int(sum(1 for i in i_end if mask[i] > 0))
    signed_avail += int(sum(1 for i in i_sig if mask[i] > 0))
P("THE PROJECTION (the V2 schema, identity normalization, ordering 'lohi'):")
P("  records: %d ticks;  projected pad_split_abs mask=1 slots: %d (reconstructed: %d)"
  % (len(records), n_abs_avail, recon["n_reconstructed"]))
P("  round-trip max |projected - reconstructed| split_abs: %.3e m (float32 path)"
  % rt_max)
P("  endpoint-signed channels available: %d (MUST be 0 -- the endpoint identity is"
  " not in the preserved outputs: declared unavailable, never invented)" % endpoint_avail)
P("  signed split/split_rate available: %d (MUST be 0 under 'lohi')" % signed_avail)
roundtrip_ok = rt_max <= 1e-6 and n_abs_avail == recon["n_reconstructed"]
mask_ok = endpoint_avail == 0 and signed_avail == 0
P("-" * 150)

# ---- the extraction artifact (pinned channel inputs) -----------------------
extraction = dict(
    trace_sha256=sha, trace_lines=n_lines,
    plane_model_y=0.004, pad_radius=0.004,
    calibration="split_abs = 2*(pad_y - gmin); g_lo = gmin; g_hi = 2*pad_y - g_lo",
    pair_ordering="lohi (endpoint identity not in the preserved outputs)",
    samples=[dict(tick=t, leg=leg, pad_y=p["pad_y"], gmin=p["gmin"],
                  g_lo=p["g_lo"], g_hi=p["g_hi"], split_abs=p["split_abs"],
                  hd=p["hd"]) for t in sorted(pairs) for leg, p in pairs[t].items()])
with open(os.path.join(HERE, "band_channels_wave47.json"), "w", encoding="utf-8") as f:
    json.dump(extraction, f, indent=1)
P("extraction artifact written: band_channels_wave47.json (%d samples, pinned to the trace sha)"
  % len(extraction["samples"]))
P("-" * 150)

# ==================== F-CHANNELS-SEPARATE (the class backfill) ===============
P("F-CHANNELS-SEPARATE (the class backfill; the census FROM the projected channels)")
rows = pad_channels.era_census(parsed, dict(series=series))
P("ERA RATE CENSUS (from the projected pad_split_abs channels; mine_wave47 conventions verbatim):")
for r in rows:
    P("  %4d->%4d leg=%d %-5s(%-3s) span=%2d nB=%2d leverMax=%+8.3f mm rate=%+7.3f mm/tick maxInc=%+7.3f mm/tick cross=%s"
      % (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["span"], r["n"],
         r["maxlev"] * 1e3, r["rate_span"] * 1e3, r["maxinc"] * 1e3,
         r["cross"] if r["cross"] is not None else "never"))

# ---- the era-table shape check vs the frozen reference ---------------------
shape_ok = len(rows) == len(CENSUS_REF)
if shape_ok:
    for r, ref in zip(rows, CENSUS_REF):
        if (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["span"], r["n"]) != ref:
            shape_ok = False
            P("    ERA-SHAPE MISMATCH at fire %d: got %s want %s"
              % (r["ft"], (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["span"], r["n"]), ref))
P("  era-table shape vs the frozen census (18 rows, fire/ct/leg/label/class/span/nSamp): %s"
  % ("GREEN" if shape_ok else "** FIRED **"))

# ---- the 12/12 never-crossed cross-check -----------------------------------
P("THE CALIBRATION CROSS-CHECK (the era-total levers vs mine_wave45_out.txt's printed maxima):")
ok = True
for r in rows:
    if r["ft"] in W45_MAXLEV_MM:
        got = r["maxlev"] * 1e3
        match = abs(got - W45_MAXLEV_MM[r["ft"]]) <= 0.001 + 1e-9
        ok = ok and match
        P("  fire %d %s: mine=%+.3f mm  wave45=%+.3f mm  %s"
          % (r["ft"], r["era_class"], got, W45_MAXLEV_MM[r["ft"]],
             "MATCH" if match else "MISMATCH"))
P("  CROSS-CHECK: %s" % ("GREEN (all 12 never-crossed eras match to the printed precision)"
                        if ok else "** FIRED **"))

# ---- the class envelopes + the separating windows --------------------------
never = [r for r in rows if r["cross"] is None]
lift = [r for r in never if r["era_class"] == "LIFT"]
stall = [r for r in never if r["era_class"] == "STALL"]
P("THE CLASS ENVELOPES (never-crossed eras, the wave-45/46 labels):")
def env(rows_, key):
    vals = [r[key] * 1e3 for r in rows_]
    return (min(vals), max(vals), len(vals))
got = dict(
    lift_lev=env(lift, "maxlev"), lift_rate=env(lift, "rate_span"),
    lift_inc=env(lift, "maxinc"), stall_lev=env(stall, "maxlev"),
    stall_rate=env(stall, "rate_span"), stall_inc=env(stall, "maxinc"))
env_ok = True
for k, (lo, hi) in ((k, v) for k, v in EXPECT.items() if not k.startswith("win_")):
    glo, ghi, n = got[k]
    m = abs(glo - lo) <= 0.001 + 1e-9 and abs(ghi - hi) <= 0.001 + 1e-9
    env_ok = env_ok and m
    P("  %-9s n=%d  %.3f .. %.3f   (frozen %.3f .. %.3f)  %s"
      % (k, n, glo, ghi, lo, hi, "MATCH" if m else "MISMATCH"))
P("THE SEPARATING WINDOWS (STALL max < window < LIFT min, measured vs frozen):")
win_ok = True
pairs_win = [("win_level", got["stall_lev"][1], got["lift_lev"][0]),
             ("win_rate", got["stall_rate"][1], got["lift_rate"][0]),
             ("win_inc", got["stall_inc"][1], got["lift_inc"][0])]
for k, s_hi, l_lo in pairs_win:
    flo, fhi = EXPECT[k]
    m = abs(s_hi - flo) <= 0.001 + 1e-9 and abs(l_lo - fhi) <= 0.001 + 1e-9 and s_hi < l_lo
    win_ok = win_ok and m
    P("  %-10s measured (%.3f, %.3f)  frozen (%.3f, %.3f)  %s"
      % (k, s_hi, l_lo, flo, fhi, "INTACT" if m else "** MOVED **"))
separate = shape_ok and ok and env_ok and win_ok and roundtrip_ok and mask_ok
P("  round-trip: %s   mask honesty: %s"
  % ("GREEN" if roundtrip_ok else "** FIRED **", "GREEN" if mask_ok else "** FIRED **"))
P("  F-CHANNELS-SEPARATE: %s" % ("GREEN" if separate else "** FIRED **"))
P("-" * 150)

# ==================== F-CHANNELS-INERT (the pure-addition gate) ==============
P("F-CHANNELS-INERT (the pure-addition gate)")
diff = subprocess.run(["git", "diff", "--name-only", "9808dc94"], capture_output=True,
                      text=True, cwd=REPO).stdout.split()
ALLOWED_PREFIX = ("tools/science_funnel/typeb_export/",
                  "tools/science_funnel/validation/obs_split_channels_20260921/",
                  "tools/science_funnel/validation/typeb_p3_20260921/")
bad = [f for f in diff if not f.replace("\\", "/").startswith(ALLOWED_PREFIX)]
P("  (a) scope diff vs 9808dc94: %d paths; outside the declared scope: %d %s"
  % (len(diff), len(bad), bad if bad else ""))
scope_ok = not bad
# (b) the legacy block equals the 1b6d7749 literal
got_fields = [{k: f[k] for k in ("name", "group", "source", "unit", "frame",
                                 "privileged", "dtype", "shape")}
              for f in oschema.FIELDS[:64]]
legacy_ok = got_fields == legacy_v1_table.LEGACY_FIELDS
P("  (b) FIELDS[:64] == the frozen 1b6d7749 v1 table: %s" % legacy_ok)
# (c) P3's banked action stream replays byte-identically through the extended schema
manifest = pman.load_manifest(os.path.join(P3VAL, "policy_manifest.json"),
                              os.path.join(P3VAL, "dummy_actor.npz"))
params = dict(np.load(os.path.join(P3VAL, "dummy_actor.npz")))
policy = NumpyPolicy(manifest, params)
ev = manifest["evaluation"]["fixed_obs_sequence"]
seq = fixed_obs_sequence(os.path.join(P3VAL, "trace_slice_wave38.json"),
                         ev["passes"], ev["n_ticks"])
stream, _ = replay(policy, seq)
got_sha = hashlib.sha256(stream).hexdigest()
replay_ok = got_sha == "e25406e86cbf5347683ee3824d385bc1d07bfd500e83eb6b9133a1e82d4bfbd9"
P("  (c) P3's banked action-stream replay through the V2 schema: %s (sha %s...)"
  % ("BYTE-IDENTICAL" if replay_ok else "** MOVED ** " + got_sha, got_sha[:16]))
# (d) P3's frozen artifacts unchanged (byte shas)
P3_SHAS = {
    "policy_manifest.json": "aa5334f797b50c2a",
    "dummy_actor.npz": "5fb2b7857d872fcc",
    "trace_slice_wave38.json": "69babe846e244733",
    "prereg.json": "6ec61b901b2e4754",
}
pins_ok = True
for fn, want in P3_SHAS.items():
    h = hashlib.sha256(open(os.path.join(P3VAL, fn), "rb").read()).hexdigest()[:16]
    if h != want:
        pins_ok = False
        P("    PIN MOVED: %s -> %s (want %s)" % (fn, h, want))
P("  (d) P3 frozen artifact pins (manifest/npz/slice/prereg): %s" % ("GREEN" if pins_ok else "** FIRED **"))
inert = scope_ok and legacy_ok and replay_ok and pins_ok
P("  F-CHANNELS-INERT: %s" % ("GREEN" if inert else "** FIRED **"))
P("-" * 150)

# ============================ the verdict ====================================
P("THE VERDICT (the frozen prereg rule: all three falsifiers GREEN -> the channels ship):")
P("  F-CHANNELS-DISTINCT : %s" % ("GREEN" if distinct else "FIRED"))
P("  F-CHANNELS-SEPARATE : %s" % ("GREEN" if separate else "FIRED"))
P("  F-CHANNELS-INERT    : %s" % ("GREEN" if inert else "FIRED"))
verdict = distinct and separate and inert
P("  VERDICT: %s" % ("THE PAD-SPLIT CHANNELS SHIP -- OBS_DIM 64->80, the first learned"
                     " skill reads the split the reflex layer structurally cannot"
                     " (the free training labels attach: LIFT/STALL windows intact)."
                     if verdict else
                     "FIRED FALSIFIER CARRIED -- see the numbers above; nothing tuned."))
P("Trailer Agent: GLM 5.3")

with open(os.path.join(HERE, "mine_pad_channels_out.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")
print("written mine_pad_channels_out.txt")
sys.exit(0 if verdict else 1)
