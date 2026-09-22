"""THE AUDIT FENCE v2 (declared instrument; AMENDED in the receipt with the
diagnosis -- the v1 clause as frozen in the prereg fired on COMMITTED REPORTING
GROWTH, not on instrument perturbation; this version measures the actual
invariants directly and carries both the red and the green legs).

LEG A (instrument inertness, the v1 clause's intent): the scratch
GAIT_EVENT_TRACE build and a no-trace build of the IDENTICAL source, run on the
identical scene, must produce BYTE-IDENTICAL stdout (the trace instrument is
stderr-only, stdout-inert).

LEG B (the ship anchor): the same-run stdout must equal the wave-47 ship
stdout sha 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc
byte-for-byte (this lane's HEAD-source build IS the wave-47 ship reporting;
measured), and the ref-exe vintage (wave-38/command-adapter pin, stdout
71065ac5...) must appear as a PURE SUBSEQUENCE -- every ship line present in
order, the only additions being the committed F-G39/F-G40 read-only plumbing
report lines, with the walk headline (WALK refused_tick=302
worst_ledger_J=30.970714) byte-equal and the stderr refusal class identical.

Usage: python fence_audit_stdout.py <trace_stdout> <notrace_stdout> <ref_stdout> <trace_stderr>
Exit 0 iff both legs green.
"""
import hashlib
import json
import sys

W47_SHIP_SHA = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"
REF_SHIP_SHA = "71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f7db69b10d4b8d94517592"
ALLOWED_ADDITION_PREFIXES = ("F-G39 NOT MEASURED", "F-G40 NOT MEASURED")

tr, nt, rf, trerr = (open(p, "rb").read() for p in sys.argv[1:5])
ok = True

print("== LEG A: instrument inertness ==")
a = hashlib.sha256(tr).hexdigest()
b = hashlib.sha256(nt).hexdigest()
print("trace stdout   :", a)
print("notrace stdout :", b)
legA = a == b
print("LEG A (byte-identical):", legA)
ok &= legA

print("== LEG B: the ship anchor ==")
sb = hashlib.sha256(tr).hexdigest()
print("trace == wave-47 ship sha", W47_SHIP_SHA[:12], ":", sb == W47_SHIP_SHA)
ok &= sb == W47_SHIP_SHA

ref_doc, tr_doc = json.loads(rf.decode("utf-8")), json.loads(tr.decode("utf-8"))
rm, nm = ref_doc["measured"], tr_doc["measured"]
i = 0
added = []
for l in nm:
    if i < len(rm) and l == rm[i]:
        i += 1
    else:
        added.append(l)
pure = (i == len(rm)) and all(l.startswith(ALLOWED_ADDITION_PREFIXES) for l in added)
print(f"ref lines {len(rm)} all present in order: {i == len(rm)}; additions: {len(added)} "
      f"all committed plumbing: {all(l.startswith(ALLOWED_ADDITION_PREFIXES) for l in added)}")
print("LEG B pure-subsequence:", pure)
ok &= pure
rl = lambda d: next(l for l in d["measured"] if l.startswith("WALK refused_tick"))
print("walk headline byte-equal:", rl(ref_doc) == rl(tr_doc), "|", rl(tr_doc))
ok &= rl(ref_doc) == rl(tr_doc)
print("pass/reds/checks equal:", ref_doc["pass"] == tr_doc["pass"],
      ref_doc["red_falsifiers"] == tr_doc["red_falsifiers"],
      ref_doc["checks"] == tr_doc["checks"])
ok &= (ref_doc["pass"] == tr_doc["pass"] and ref_doc["red_falsifiers"] == tr_doc["red_falsifiers"]
       and ref_doc["checks"] == tr_doc["checks"])
refus = [l for l in trerr.decode("utf-8", "replace").splitlines() if l.startswith("WALK REFUSED")]
print("stderr refusal:", refus[-1] if refus else "NONE")
ok &= bool(refus) and "tick 302" in refus[-1] and "gait_positional_correction_budget" in refus[-1]

print("FENCE VERDICT:", "GREEN" if ok else "VOID")
sys.exit(0 if ok else 1)
