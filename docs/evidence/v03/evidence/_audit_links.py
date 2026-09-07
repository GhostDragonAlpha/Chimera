import io, os, re

pat = re.compile(r'(stride|gait|no pack|steps\s*=\s*0|steps\s*=\s*\d+)', re.I)

print('=== P02 audit lines mentioning gait/stride/pack ===')
with io.open(r'E:/PythonChimera/.tmp/p02_20260906_122252/P02_PLATFORM_AUDIT.md', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            print('%4d: %s' % (i, line.rstrip()[:210]))

print()
print('=== dyad_log.txt lines mentioning gait/stride/pack ===')
with io.open(r'E:/PythonChimera/Saved/dyad/dyad_log.txt', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            print('%4d: %s' % (i, line.rstrip()[:210]))

print()
print('=== dyad_log.jsonl: full records mentioning gait/stride/pack ===')
with io.open(r'E:/PythonChimera/Saved/dyad/dyad_log.jsonl', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            d = json.loads(line)
            print('line %d ts=%s kind=%s image=%s' % (i, d.get('ts'), d.get('kind'), d.get('image')))
            r = d.get('report','')
            for j, rl in enumerate(r.split('\n')):
                if pat.search(rl):
                    print('     %s' % rl.rstrip()[:200]))