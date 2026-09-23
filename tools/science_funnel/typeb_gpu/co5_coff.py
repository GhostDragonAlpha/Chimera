"""co5_coff.py -- parse a COFF .obj (the extracted UCRT math objects) and dump
the named .rdata constants as raw hex + doubles, so the UCRT's actual pi/2
chunks and polynomial coefficient tables can be identified and ported.
Trailer Agent: GLM 5.3.
"""
import struct, sys

def parse(path):
    b = open(path, "rb").read()
    (mach, nsec, ts, symoff, nsyms, opthdr, chars) = struct.unpack_from("<HHIIIHH", b, 0)
    sections = []
    off = 20
    for i in range(nsec):
        name = b[off:off+8].rstrip(b"\0").decode(errors="replace")
        (vsize, vaddr, rawsz, rawptr, relptr, lnptr, nrel, nln, schar) = struct.unpack_from("<IIIIIIHHH", b, off+8)
        sections.append(dict(name=name, vsize=vsize, vaddr=vaddr, rawsz=rawsz,
                             rawptr=rawptr, relptr=relptr, nrel=nrel, schar=schar))
        off += 40
    # symbols
    syms = []
    stroff = symoff + nsyms * 18
    for i in range(nsyms):
        e = symoff + i * 18
        raw = b[e:e+8]
        if raw[:4] == b"\0\0\0\0":
            so = struct.unpack_from("<I", raw, 4)[0]
            s = b[stroff+so:]
            name = s[:s.index(b"\0")].decode(errors="replace")
        else:
            name = raw.rstrip(b"\0").decode(errors="replace")
        (val, secnum, typ, sclass, naux) = struct.unpack_from("<IhhBB", b, e+8)
        syms.append((name, val, secnum, typ, sclass, naux))
    return b, sections, syms

def main(path):
    b, sections, syms = parse(path)
    for s in sections:
        print(f"SECTION {s['name']:10s} vaddr={s['vaddr']:#x} rawsz={s['rawsz']:#x} nrel={s['nrel']}")
    # externs (section 0) that are constants the asm references
    print("\nSYMBOLS (section 0 = external, others = defined):")
    for (name, val, sec, typ, sclass, naux) in syms:
        if sclass in (2, 3) and (sec == 0 or val is not None):
            pass
    for (name, val, sec, typ, sclass, naux) in syms:
        if sec == 0:
            continue
        if not name.startswith(".") and not name.startswith("$"):
            print(f"  {name:40s} val={val:#x} sec={sec} class={sclass}")
    # dump .rdata (or any read-only data) as doubles aligned by symbol value
    for s in sections:
        if "rdata" not in s["name"] and "data" not in s["name"]:
            continue
        data = b[s["rawptr"]:s["rawptr"]+s["rawsz"]]
        labels = sorted(((v, n) for (n, v, sec, t, c, a) in syms if sec == int(s["name"].split("$")[-1]) if isinstance(v, int)) , key=lambda x: x[0])
        # sec numbers are 1-based in symbol table; section list is 0-based
        # redo properly:
        secidx = sections.index(s) + 1
        labels = sorted(((v, n) for (n, v, sec, t, c, a) in syms if sec == secidx and isinstance(v, int)), key=lambda x: x[0])
        print(f"\n--- {s['name']} (sec {secidx}) as labeled doubles ---")
        for i in range(0, len(data) - 7, 8):
            q = struct.unpack_from("<Q", data, i)[0]
            d = struct.unpack_from("<d", data, i)[0]
            lab = ""
            for j in range(len(labels)):
                if labels[j][0] == i:
                    lab = labels[j][1]
            print(f"  {i:06x}: {q:016x} {d!r:26s} {lab}")

if __name__ == "__main__":
    main(sys.argv[1])
