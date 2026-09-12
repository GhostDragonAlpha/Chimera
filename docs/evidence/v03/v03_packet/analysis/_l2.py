import io, json

pat = __import__('re').compile(r'(stride|gait|no pack|steps\s*=\s*0|steps\s*=\s*\d+)', re.I) if False else None
import re
pat = re.compile(r'(stride|gait|no pack|steps\s*=\s*0|steps\s*=\s*\d+)', re.I)

with io.open(r'E:/PythonChimera/Saved/dyad/dyad_log.jsonl', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if pat.search(line):
            d = json.loads(line)
            with io.open(r'E:/PythonChimera/.tmp\v02_20260906_190511\_links_raw.txt', 'a', encoding='utf-8') as o:
                o.write('line %d ts=%s kind=%s image=%s\n' % (i, d.get('ts'), d.get('kind'), d.get('image')))
                for rl in d.get('report','').split('\n'):
                    if pat.search(rl):
                        o.write('     %s\n' % rl.rstrip()[:200])
print('part2 done')