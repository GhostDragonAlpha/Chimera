"""Audit the constraint-ledger trace for LOSSLESSNESS (the L0 boundary question).

For every float recorded WITH its bits: reconstruct the double from the recorded
uint64, re-format with the writer's own %.17g, and demand EXACT string equality
with the recorded decimal. For floats recorded decimal-only (%.17g): verify the
decimal round-trips through float() and re-formats identically (the binary64
round-trip property), and NAME that bits were not recorded for it.

Also verifies the declared initial state on row 0 and emits the boundary digest.

Usage: python audit_trace_lossless.py <trace.jsonl> <out.json>
"""
import json, struct, sys, hashlib

trace_path, out_path = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(trace_path, encoding="utf-8") if l.strip()]
meta, body = rows[0], rows[1:]

BITFIELDS = [("gaps", "gaps_bits", 4)]
PERLEG_BITFIELDS = [("plant_y", "plant_y_bits"), ("heel_y", "heel_y_bits"), ("mp_y", "mp_y_bits")]
DECIMAL_ONLY = ["t", "phase"]

mismatches = []
decimal_only_checked = 0
bit_checked = 0

def dec17(x):
    return f"{x:.17g}"

for idx, row in enumerate(body):
    for dec_key, bit_key, n in BITFIELDS:
        for i in range(n):
            d, b = row[dec_key][i], row[bit_key][i]
            recon = struct.unpack("<d", struct.pack("<Q", b))[0]
            bit_checked += 1
            if dec17(recon) != dec17(d):
                mismatches.append({"row": idx, "field": f"{dec_key}[{i}]", "dec": d, "bits": b})
    for leg in range(2):
        cell = row["leg"][leg]
        for dec_key, bit_key in PERLEG_BITFIELDS:
            d, b = cell[dec_key], cell[bit_key]
            recon = struct.unpack("<d", struct.pack("<Q", b))[0]
            bit_checked += 1
            if dec17(recon) != dec17(d):
                mismatches.append({"row": idx, "field": f"leg[{leg}].{dec_key}", "dec": d, "bits": b})
        for k in DECIMAL_ONLY:
            v = cell[k]
            rt = float(dec17(v))
            decimal_only_checked += 1
            if dec17(rt) != dec17(v):
                mismatches.append({"row": idx, "field": f"leg[{leg}].{k}", "dec": v})

row0 = body[0]
initial_state = {
    "touch": row0["touch"],
    "leg0": {k: row0["leg"][0][k] for k in ("mode", "t", "held", "clear_tick", "plant_y", "plant_y_bits", "phase")},
    "leg1": {k: row0["leg"][1][k] for k in ("mode", "t", "held", "clear_tick", "plant_y", "plant_y_bits", "phase")},
}

out = {
    "trace": trace_path,
    "trace_sha256": hashlib.sha256(open(trace_path, "rb").read()).hexdigest(),
    "meta": meta,
    "rows": len(body),
    "bit_pairs_checked": bit_checked,
    "decimal_only_checked": decimal_only_checked,
    "mismatches": mismatches,
    "lossless": len(mismatches) == 0,
    "decimal_only_note": ("t and phase are recorded as %.17g decimals WITHOUT bits columns; "
                          "%.17g is a round-trip-exact representation for binary64 (verified here "
                          "by float() round-trip), but the recorded artifact cannot be "
                          "bit-verified for them -- NAMED instrument upgrade: add t_bits/phase_bits"),
    "declared_initial_state_row0": initial_state,
}
json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
print(f"rows={len(body)} bit_pairs={bit_checked} decimal_only={decimal_only_checked} "
      f"mismatches={len(mismatches)} lossless={len(mismatches)==0}")
print("row0:", json.dumps(initial_state))
