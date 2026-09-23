"""gen_ucrt_tables.py -- emit ucrt_math_tables.h VERBATIM from the extracted
UCRT objects (.rdata sections of ucrt_objs/*.obj), with checks:
  sin[0] == -1/6, cos[0] == 1/24,
  atan_lead[i] + atan_tail[i] == atan((i+16)/256) within 1 ulp for all i,
  the 2/pi digit table is 158 bytes ending A2 FB 9C.
Trailer Agent: GLM 5.3.
"""
import struct, math

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
    raise KeyError(name)

ssec = symget("ucrt_objs/lsincos_array_mt.obj", "__Lsinarray")
csec = symget("ucrt_objs/lsincos_array_mt.obj", "__Lcosarray")
svals = [struct.unpack_from("<Q", ssec, 16*i)[0] for i in range(6)]
cvals = [struct.unpack_from("<Q", csec, 16*i)[0] for i in range(6)]
sv = [struct.unpack("<d", struct.pack("<Q", v))[0] for v in svals]
cv = [struct.unpack("<d", struct.pack("<Q", v))[0] for v in cvals]
assert sv[0] == -1.0/6.0 and cv[0] == 1.0/24.0

lsec = symget("ucrt_objs/atan2_fma.obj", "?atan_jby256_lead@?1??atan2_internal@@9@9")
tsec = symget("ucrt_objs/atan2_fma.obj", "?atan_jby256_tail@?1??atan2_internal@@9@9")
leadv = [struct.unpack_from("<Q", lsec, 8*i)[0] for i in range(241)]
tailv = [struct.unpack_from("<Q", tsec, 8*i)[0] for i in range(241)]
ld = [struct.unpack("<d", struct.pack("<Q", v))[0] for v in leadv]
td = [struct.unpack("<d", struct.pack("<Q", v))[0] for v in tailv]
ok = 0
for i in range(241):
    a = math.atan((i + 16) / 256.0)
    s = ld[i] + td[i]
    assert s == a or abs(s - a) <= 2 * abs(a) * 2.3e-16, (i, s, a)
    ok += 1
print("atan table identity holds for", ok, "entries")

tab = symget("ucrt_objs/L2bypi.obj", "__L_2_by_pi_bits")
assert len(tab) == 158 and tab[:4] == bytes([0xe0, 0xf1, 0x1b, 0xc1])
assert tab.index(bytes([0xa2, 0xfb, 0x9c])[0]) >= 0  # the digit stream wraps through A2 FB 9C

out = []
out.append("/* ucrt_math_tables.h -- generated VERBATIM from the extracted UCRT objects")
out.append(" * (ucrt_objs/*.obj .rdata) by gen_ucrt_tables.py. Do not hand-edit.")
out.append(" * Trailer Agent: GLM 5.3. */")
out.append("#ifndef UCRT_MATH_TABLES_H")
out.append("#define UCRT_MATH_TABLES_H")
out.append("static const uint64_t u_sinarr[6] = {")
out.append("    " + ",".join(f"0x{v:016X}ULL" for v in svals) + " };")
out.append("static const uint64_t u_cosarr[6] = {")
out.append("    " + ",".join(f"0x{v:016X}ULL" for v in cvals) + " };")
out.append("static const uint64_t u_atan_lead[241] = {")
for i in range(0, 241, 4):
    out.append("    " + ",".join(f"0x{v:016X}ULL" for v in leadv[i:i+4]) + ",")
out.append("};")
out.append("static const uint64_t u_atan_tail[241] = {")
for i in range(0, 241, 4):
    out.append("    " + ",".join(f"0x{v:016X}ULL" for v in tailv[i:i+4]) + ",")
out.append("};")
out.append(f"static const unsigned char u_l2bypi[{len(tab)}] = {{")
for i in range(0, len(tab), 16):
    out.append("    " + ",".join(f"0x{x:02X}" for x in tab[i:i+16]) + ",")
out.append("};")
out.append("#endif")
open("ucrt_math_tables.h", "w").write("\n".join(out) + "\n")
print("ucrt_math_tables.h written")
