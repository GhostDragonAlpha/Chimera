"""inject_probe.py -- (re)create probe_kernels.cuh from the CLEAN
walker_kernels.cuh: dump q/v after each tick-1 substep in tick_integ_kernel.
Trailer Agent: GLM 5.3."""
src = open('walker_kernels.cuh', encoding='utf-8').read()
NL = chr(10)
BS = chr(92)  # backslash

old = """        for (i = 0; i < (18); ++i) {
            q[i] = trial_q[i];
            v[i] = trial_v[i];
            w[i] = trial_w[i];
}"""
assert old in src, "per-substep commit site not found"

fmt = ('[SUB] sub=%d rc=%d q12=%.17g v9=%.17g v12=%.17g v13=%.17g '
       'v14=%.17g v17=%.17g v4=%.17g' + BS + 'n')
args = ('sub, rc, q[12], v[9], v[12], v[13], v[14], v[17], v[4]')
new = (old + NL +
       '        if (a_ticks[e] == 0) {' + NL +
       '            printf("' + fmt + '", ' + args + ');' + NL +
       '        }')

src = src.replace(old, new, 1)
open('probe_kernels.cuh', 'w', encoding='utf-8', newline=NL).write(src)
print("probe_kernels.cuh written clean")
