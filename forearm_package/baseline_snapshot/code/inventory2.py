"""Round-2 inventory: spatial tendon paths, muscle count, joint coords, sites.
Grounds the fixture honestly against the ACTUAL file (the task memo's counts
may come from a different intake; measured numbers win).
"""
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

et = ET.parse(r"E:\PythonChimera\.tmp\chimanoid.xml")
root = et.getroot()

joints = [(b.get("name"), j.get("name"), j.get("type")) for b in root.findall(".//body") for j in b.findall(".//joint")]
print("joints:", len(joints), "types:", Counter(t for _, _, t in joints))
print("---- joint names ----")
for bn, jn, t in joints:
    print(f"  {bn:14s} {t:6s} {jn}")

# sites
sites = root.findall(".//site")
print("\ntotal <site> elements:", len(sites))
body_sites = [s for s in sites if s in [c for b in root.findall(".//body") for c in b]]
print("sites that are body children:", len(body_sites))
site_parent = {}
for b in root.findall(".//body"):
    for s in b.findall("site"):
        site_parent[s.get("name")] = (b.get("name"), tuple())
    for child in b.findall("body"):
        pass

# spatial tendon paths
spatial_paths = []
muscle_names = []
for t in root.findall(".//tendon"):
    for sp in t.findall("spatial"):
        sites_in = sp.findall("site")
        spatial_paths.append((t.get("class"), [s.get("site") for s in sites_in]))
    for m in t.findall("muscle"):
        muscle_names.append(m.get("name"))
print("\nspatial tendon paths:", len(spatial_paths))
for cls, path in spatial_paths[:6]:
    print("  spatial class=", cls, "len", len(path), path[:5])

frac = [len(p) for _, p in spatial_paths]
print("path length histogram:", dict(Counter(frac)))
all_ref = [s for _, p in spatial_paths for s in p]
print("site refs in tendons:", len(all_ref), "| unique referenced sites:", len(set(all_ref)))

# muscles
muscles = root.findall(".//muscle")
print("\nmuscle actuators:", len(muscles), "| names unique:", len({m.get('name') for m in muscles}))
refd = {m.get("tendon") for m in muscles}
print("muscles reference tendons:", len(refd), "| of", len(spatial_paths), "spatial paths")
missing_refs = [t for t in refd if all((m.get("name") or t) for m in muscles)]
# which spatial paths are referenced by muscle names?
muscle_by_name = {m.get("name"): m for m in muscles}
unref = [p for p in spatial_paths if p not in spatial_paths]
# count muscle->path mapping by matching 'name' vs path index
print("first muscle attribs:", dict(list(muscles)[0].attrib))
print("last muscle attribs:", dict(list(muscles)[-1].attrib))

# scale/mass/inertia on bodies
inertias = []
for b in root.findall(".//body"):
    i = b.find("inertial")
    if i is not None:
        inertias.append((b.get("name"), dict(i.attrib)))
print("\ninertial count:", len(inertias))
for row in inertias[:4]:
    print("  inertial:", row)

# coordinate/dof naming — the 39 claim
names = [jn for _, jn, t in joints]
base = set()
for n in names:
    base.add(n.rsplit("_", 1)[0] if n.rsplit("_", 1)[-1] in ("l", "r") else n)
base_full = set(names)
print("\n39-claim probe: distinct full coordinate names:", len(base_full))
# free/pelvis motion
pelvis = [j for b, j, t in joints if b == "pelvis"]
print("pelvis coords:", pelvis)