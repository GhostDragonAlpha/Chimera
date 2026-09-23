# make_variant.py -- build the lane-private statedump variant from the tree's
# gait_unit.cpp (f89cab4e): 4 additive, stdout/stderr-inert hunks.
from pathlib import Path

BASE = Path('E:/ChimeraWork/viswalk-agent/ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp')
HDR = Path('E:/ChimeraWork/viswalk-agent/ChimeraEngine/engine/gait_controller.hpp')
OUTDIR = Path('E:/ChimeraWork/viswalk-agent/.tmp/viswalk_dump')

src = BASE.read_bytes()
NL = b'\r\n' if b'struct WalkOut{\r\n' in src else b'\n'

def rx(s):
    return s.replace(b'\n', NL)

# HUNK 1: include <cstdlib> for getenv
a1 = rx(b'#include <fstream>\n')
assert src.count(a1) == 1, ('h1', src.count(a1))
src = src.replace(a1, a1 + rx(b'#include <cstdlib> // VISIBLE-WALK PRESTAGE: getenv (dump path; stdout/stderr-inert)\n'), 1)

# HUNK 2: WalkOut member
a2 = rx(b'struct WalkOut{\n std::string stream;\n')
assert src.count(a2) == 1, ('h2', src.count(a2))
src = src.replace(a2, a2 + rx(b' std::string qstream; // VISIBLE-WALK PRESTAGE: per-tick full q/v dump (separate stream, reads only)\n'), 1)

# HUNK 3: per-tick qstream append (d, i in scope)
c = rx(b"   if(i%10==0){std::string j=s.dump();out.stream+=j;out.stream+='") + b'\\n' + rx(b"';}\n")
assert src.count(c) == 1, ('h3', src.count(c))
qblock = NL.join([
    b'   { // VISIBLE-WALK PRESTAGE: full q/v every tick, %.17g round-trip, own',
    b'     // stream (reads only; no status byte, no stdout byte, no stderr byte',
    b'     // depends on it -- the anchor shas are this hunk inertness proof).',
    b'     const Dense& qv=d.angles();const Dense& vv=d.speeds();',
    b'     std::string line="{\\"tick\\":"+std::to_string(i)+",\\"q\\":[";',
    b'     for(size_t k=0;k<qv.size();++k){char b[40];std::snprintf(b,40,"%s%.17g",k?",":"",qv[k]);line+=b;}',
    b'     line+="],\\"v\\":[";',
    b'     for(size_t k=0;k<vv.size();++k){char b[40];std::snprintf(b,40,"%s%.17g",k?",":"",vv[k]);line+=b;}',
    b'     line+="]}\\n";out.qstream+=line;}',
    b''])
src = src.replace(c, c + qblock + NL, 1)

# HUNK 4: silent dumps after the F-G7 second run (inside its block)
d4 = rx(b'  note("F-G7 streams bit-identical="+std::to_string(w2.stream==w.stream));}\n')
assert src.count(d4) == 1, ('h4', src.count(d4))
e = NL.join([
    b'  note("F-G7 streams bit-identical="+std::to_string(w2.stream==w.stream));',
    b'  if(const char* dp=std::getenv("GAIT_STATE_DUMP");dp&&dp[0]){std::ofstream f(dp,std::ios::binary);f<<w.qstream;}',
    b'  if(const char* dp2=std::getenv("GAIT_STATE_DUMP2");dp2&&dp2[0]){std::ofstream f2(dp2,std::ios::binary);f2<<w2.qstream;}}',
    b''])
src = src.replace(d4, e, 1)

outdir = OUTDIR / 'tests_coupled_arm'
outdir.mkdir(parents=True, exist_ok=True)
(outdir / 'gait_unit_viswalk_dump.cpp').write_bytes(src)
OUTDIR.joinpath('gait_controller.hpp').write_bytes(HDR.read_bytes())
print('variant written; NL =', repr(NL), '; bytes', len(src))
