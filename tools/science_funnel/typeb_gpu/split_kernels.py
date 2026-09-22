"""split_kernels.py -- the phase-split pass over the generated monolith.

Reads walker_numba_gen.py, cuts tick_kernel at its natural seams (the
PREREG_DIAG.md T2 fix for the H1 codegen wall), and emits
walker_numba_split.py with three kernels per tick, same per-env serial
semantics (no cross-env state exists; launches are same-stream ordered):

  tick_plan_kernel    preamble(+settle decr) + eval0 + reflex/gait planning
                      + state writeback (rc=0, no bookkeeping, no a_ticks)
  tick_integ_kernel   preamble(-settle decr) + the 4-substep
                      servo/store-bisection/advance loop + state writeback
                      + a_rc[e] = rc (no bookkeeping, no a_ticks)
  tick_post_kernel    preamble(-settle decr) + the full tick bookkeeping
                      (rc = a_rc[e]; NaN/collapse; refused/collapsed;
                      a_ticks increment ONCE; rb/rbi)

Device prints of the monolith are dropped in the split (production);
reset_kernel is copied verbatim and launched exactly as today ([E,1]).
Every emitted kernel gains a bounds guard `if e >= ne: return` so blocks
with >1 thread are safe (the H2 block ladder needs it). All three kernels
are @cuda.jit(cache=True) so subsequent processes skip recodegen.

FAILS LOUD if any marker is missing or non-unique. Trailer Agent: GLM 5.3.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'walker_numba_gen.py'
DST = HERE / 'walker_numba_split.py'


def marker_once(text, marker, label):
    n = text.count(marker)
    if n != 1:
        raise SystemExit(f'MARKER {label!r} occurs {n} times (need 1)')
    return text.index(marker)


def strip_line(block, line, label):
    n = block.count(line)
    if n != 1:
        raise SystemExit(f'STRIP {label!r} occurs {n} times (need 1)')
    i = block.index(line)
    j = block.index('\n', i) + 1
    return block[:i] + block[j:]


def main():
    text = SRC.read_text(encoding='utf-8')

    # ---- locate tick_kernel (the file's last function) ----
    i_def = marker_once(text, 'def tick_kernel(', 'tick def')
    i_dec = text.rindex('@cuda.jit', 0, i_def)
    head = text[:i_dec]                      # module docstring .. reset_kernel
    tick_block = text[i_def:]                # def tick_kernel .. EOF

    m = re.search(r'def tick_kernel\((.*?)\):\n', tick_block, re.S)
    if not m:
        raise SystemExit('cannot parse tick_kernel params')
    params = m.group(1)
    defline = f'def {{NAME}}({params}, a_rc):\n'
    defline_end = m.end()

    # ---- phase markers ----
    mk_eval0 = "print('K eval0', e)"
    mk_sub = '    sub = int32(0)'
    mk_book = '# \u2500\u2500 the tick bookkeeping \u2500\u2500'
    mk_wb_for = '    for i in range(18):'
    mk_wb_body = '        a_q[e * 18 + i] = q[i]'
    mk_settle = '        settle_n = settle_n - 1'
    mk_settle_if = '    if settle_n > 0:'
    mk_aticks = '        a_ticks[e] = tick + np.int64(1)'
    mk_guard = '    if rc == 0 and collapsed == 0:'

    i_eval0 = marker_once(tick_block, mk_eval0, 'eval0 print')
    i_sub = marker_once(tick_block, mk_sub, 'sub loop')
    i_book = marker_once(tick_block, mk_book, 'bookkeeping comment')
    i_wb_body = tick_block.rindex(mk_wb_body)
    i_wb_for = tick_block.rindex(mk_wb_for, 0, i_wb_body)
    i_settle_line = marker_once(tick_block, mk_settle, 'settle decr')
    i_settle_if = marker_once(tick_block, mk_settle_if, 'settle if')

    defline_txt = tick_block[:defline_end]

    pre = tick_block[defline_end:i_settle_if]          # decls + state load
    settle_only = tick_block[i_settle_if:i_eval0]      # settle decr (+blank lines)
    p1 = tick_block[i_eval0:i_sub]                     # eval0 + planning
    p2 = tick_block[i_sub:i_book]                      # the 4-substep loop
    p3 = tick_block[i_book:]                           # bookkeeping + writeback
    wb_part = tick_block[i_wb_for:]                    # state writeback .. EOF
    book_part = tick_block[i_book:i_wb_for]            # nan/collapse/refused + a_ticks

    # plan/integ writeback: drop a_ticks line, then its orphaned guard line
    wb_no_ticks = strip_line(wb_part, mk_aticks, 'a_ticks')
    wb_no_ticks = strip_line(wb_no_ticks, mk_guard, 'a_ticks guard')

    # K_post bookkeeping: rc comes from the scratch array
    post_book = book_part.replace(mk_book, mk_book + '\n\n    rc = a_rc[e]\n', 1)
    if post_book == book_part:
        raise SystemExit('rc injection failed')

    guard_line = '    e = cuda.grid(1)'
    if pre.count(guard_line) != 1:
        raise SystemExit(f'grid line occurs {pre.count(guard_line)} times in preamble (need 1)')
    pre = pre.replace(guard_line,
                      guard_line + '\n\n'
                      '    ne = a_q.shape[0] // 18\n\n'
                      '    if e >= ne:\n\n'
                      '        return', 1)

    body_plan = pre + settle_only + p1 + '\n\n    rc = int32(0)\n\n    collapsed = int32(0)\n\n' + wb_no_ticks
    body_integ = pre + '\n\n' + p2 + '\n\n    a_rc[e] = rc\n\n    rc = int32(0)\n\n    collapsed = int32(0)\n\n' + wb_no_ticks
    body_post = pre + '\n\n' + post_book + wb_part

    def kernel(name, body):
        dl = defline.replace('{NAME}', name)
        return f'@cuda.jit(cache=True)\n\n{dl}{body}\n'

    out = []
    out.append('"""AUTO-DERIVED by split_kernels.py from walker_numba_gen.py -- do not edit.\n\n'
               'The phase-split tick: plan -> integrate -> post, one kernel each, same\n'
               'per-env serial semantics; a_rc carries the integration verdict to post.\n'
               'Device prints dropped; bounds guard added; cache=True for codegen reuse.\n'
               'Trailer Agent: GLM 5.3.\n"""\n')
    out.append(head)
    out.append(kernel('tick_plan_kernel', body_plan))
    out.append('\n\n')
    out.append(kernel('tick_integ_kernel', body_integ))
    out.append('\n\n')
    out.append(kernel('tick_post_kernel', body_post))

    dst_text = ''.join(out)
    DST.write_text(dst_text, encoding='utf-8')
    print(f'wrote {DST.name}: {dst_text.count(chr(10))} lines')
    print('plan lines:', body_plan.count('\n'),
          'integ lines:', body_integ.count('\n'),
          'post lines:', body_post.count('\n'))


if __name__ == '__main__':
    main()
