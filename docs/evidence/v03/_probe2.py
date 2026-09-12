import io, re

t = io.open('E:/PythonChimera/ChimeraEngine/cpp_bridge.py', encoding='utf-8', errors='replace').read()
lines = t.splitlines()

print('=== engine_available (lines ~30-60) ===')
print('\n'.join('%4d: %s' % (i+1, l.rstrip()[:150]) for i, l in enumerate(lines[28:60])))

print()
print('=== fetch_frame (lines ~170-200) ===')
print('\n'.join('%4d: %s' % (i+170, l.rstrip()[:150]) for i, l in enumerate(lines[169:200])))