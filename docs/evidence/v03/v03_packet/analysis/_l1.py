import io, re, json

pat = re.compile(r'(stride|gait|no pack|steps\s*=\s*0|steps\s*=\s*\d+)', re.I)
out = io.open(r'E:/PythonChimera/.tmp\v02_20260906_190511\_links_raw.txt', 'w', encoding='utf-8')

out.write('=== P02 audit lines ===\n')
with io.open(r'E:/PythonChimera/.tmp/p02_20260906_122252/P02_PLATFORM_AUDIT.md', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            out.write('%4d: %s\n' % (i, line.rstrip()[:210]))

out.write('\n=== dyad_log.txt lines ===\n')
with io.open(r'E:/PythonChimera/Saved/dyad/dyad_log.txt', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            out.write('%4d: %s\n' % (i, line.rstrip()[:210]))
out.close()
print('part1 done')