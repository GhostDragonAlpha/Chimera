import io, re

t = io.open('E:/PythonChimera/ChimeraEngine/cpp_bridge.py', encoding='utf-8', errors='replace').read()
paths = sorted(set(re.findall(r'"/([a-z_]+)"', t)))
print('endpoint strings found:', paths)
print()
for m in re.finditer(r'def (\w+)\(', t):
    print('def', m.group(1))
print()
print('=== lines mentioning http / GET / POST ===')
for i, line in enumerate(t.splitlines(), 1):
    if re.search(r'requests\.|urllib|http|GET|POST|/frame|/glass|/state|/camera|/joints|/show', line):
        print('%4d: %s' % (i, line.rstrip()[:160]))