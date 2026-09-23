"""gen_ucrt_consts.py -- emit ucrt_math_consts.h: every labeled .rdata double of
the extracted UCRT math objects as a named C constant, so the reconstruction
references the SAME names the disasms use (no hand-typed constant bits).
Trailer Agent: GLM 5.3.
"""
import struct, re

def secs(path):
    b = open(path, "rb").read()
    (mach, nsec, ts, symoff, nsyms, opthdr, chars) = struct.unpack_from("<HHIIIHH", b, 0)
    off = 20; ss = []
    for i in range(nsec):
        nm = b[off:off+8].rstrip(b"\0").decode(errors="replace")
        (vs, va, rs, rp, rlp, lnp, nr, nl, sc) = struct.unpack_from("<IIIIIIHHH", b, off+8)
        ss.append((nm, rs, rp)); off += 40
    return b, ss

def symget(path, name):
    b, ss = secs(path)
    (mach, nsec, ts, symoff, nsyms, opthdr, chars) = struct.unpack_from("<HHIIIHH", b, 0)
    stroff = symoff + nsyms * 18
    for i in range(nsyms):
        e = symoff + i * 18; raw = b[e:e+8]
        if raw[:4] == b"\0\0\0\0":
            so = struct.unpack_from("<I", raw, 4)[0]; s2 = b[stroff+so:]
            nm = s2[:s2.index(b"\0")].decode(errors="replace")
        else:
            nm = raw.rstrip(b"\0").decode(errors="replace")
        if nm == name:
            (val, secn, typ, cl, naux) = struct.unpack_from("<IhhBB", b, e+8)
            nm2, rs, rp = ss[secn-1]
            return b[rp+val:rp+rs]
    raise KeyError(f"{path}:{name}")

OBJS = {
    "sin":  "ucrt_objs/sin_mt.obj",
    "cos":  "ucrt_objs/cos_mt.obj",
    "rem":  "ucrt_objs/rempiby2_fma3.obj",
    "acos": "ucrt_objs/acos_fma.obj",
    "atan": "ucrt_objs/atan2_fma.obj",
    "hyp":  "ucrt_objs/hypot_mt.obj",
}

def all_labels(path):
    b, ss = secs(path)
    (mach, nsec, ts, symoff, nsyms, opthdr, chars) = struct.unpack_from("<HHIIIHH", b, 0)
    stroff = symoff + nsyms * 18
    out = {}
    for i in range(nsyms):
        e = symoff + i * 18; raw = b[e:e+8]
        if raw[:4] == b"\0\0\0\0":
            so = struct.unpack_from("<I", raw, 4)[0]; s2 = b[stroff+so:]
            nm = s2[:s2.index(b"\0")].decode(errors="replace")
        else:
            nm = raw.rstrip(b"\0").decode(errors="replace")
        (val, secn, typ, cl, naux) = struct.unpack_from("<IhhBB", b, e+8)
        if secn == 0 or nm.startswith(".") or nm.startswith("$"):
            continue
        if naux or typ != 0:   # skip extern/function entries
            continue
        out[nm] = (secn, val)
    return b, ss, out

def get_bytes(b, ss, secn, val):
    nm, rs, rp = ss[secn-1]
    return b[rp+val:rp+rs]

lines = []
lines.append("/* ucrt_math_consts.h -- generated VERBATIM labeled .rdata constants of the")
lines.append(" * extracted UCRT math objects (gen_ucrt_consts.py). Do not hand-edit.")
lines.append(" * Trailer Agent: GLM 5.3. */")
lines.append("#ifndef UCRT_MATH_CONSTS_H")
lines.append("#define UCRT_MATH_CONSTS_H")

emitted = set()
for tag, path in OBJS.items():
    b, ss, labels = all_labels(path)
    for nm, (secn, val) in sorted(labels.items()):
        if "@" in nm:   # MSVC __real@ / string labels: name by their hex value
            m = re.match(r"__real@([0-9a-f]+)$", nm)
            if not m:
                continue
            hexs = m.group(1)
            if len(hexs) != 16:
                continue
            cname = "uc_" + tag + "_" + hexs[-8:]
            if cname in emitted:
                continue
            data = get_bytes(b, ss, secn, val)
            if len(data) < 8:
                continue
            q = struct.unpack_from("<Q", data, 0)[0]
            expect = int(hexs, 16)
            # the label name IS the bit pattern for __real@
            if q != expect:
                continue
            val=struct.unpack_from("<d",data,0)[0]
            lines.append(f'static const double {cname} = {val:.17g}; // {nm} (0x{q:016X})')
            emitted.add(cname)
        else:
            data = get_bytes(b, ss, secn, val)
            safe = re.sub(r"[^A-Za-z0-9]", "_", nm)
            if len(data) == 8:
                q = struct.unpack_from("<Q", data, 0)[0]
                if safe in emitted:
                    continue
                val=struct.unpack_from("<d",data,0)[0]
                lines.append(f'static const double u_{tag}_{safe} = {val:.17g}; // {nm} (0x{q:016X})')
                emitted.add(safe)
            elif len(data) >= 16:
                q0 = struct.unpack_from("<Q", data, 0)[0]
                q1 = struct.unpack_from("<Q", data, 8)[0]
                if safe in emitted:
                    continue
                v0=struct.unpack_from("<d",data,0)[0]; v1=struct.unpack_from("<d",data,8)[0]
                lines.append(f'static const double u_{tag}_{safe}[2] = {{ {v0:.17g}, {v1:.17g} }}; // {nm}')
                emitted.add(safe)

lines.append("#endif")
open("ucrt_math_consts.h", "w").write("\n".join(lines) + "\n")
print("constants written:", len(emitted))
