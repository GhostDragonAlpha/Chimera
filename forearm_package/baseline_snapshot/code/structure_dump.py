import xml.etree.ElementTree as ET
et = ET.parse(r"E:\PythonChimera\.tmp\chimanoid.xml")
root = et.getroot()
wb = root.find("worldbody")

def walk(b, depth=0):
    print("  "*depth + "<body name=%r pos=%r childclass=%r>" % (b.get("name"), b.get("pos"), b.get("childclass")))
    for j in b.findall("joint"):
        print("  "*depth + "   J ", dict(j.attrib))
    for i in b.findall("inertial"):
        print("  "*depth + "   I ", dict(i.attrib))
    sites = b.findall("site")
    if sites:
        print("  "*depth + "   S  n=%d first=%s" % (len(sites), dict(sites[0].attrib)))
    for c in b.findall("body"):
        walk(c, depth+1)

for b in wb.findall("body"):
    walk(b)

# show one spatial tendon with all sites + the muscle that drives it
print("---- tendon wrappers ----")
for t in root.findall(".//tendon"):
    print("tendon", dict(t.attrib))
    for sp in t.findall("spatial"):
        print("   spatial[%d]:" % len(sp.findall("site")), [s.get("site") for s in sp.findall("site")][:8], "...")
    mus = t.findall("muscle")
    if mus:
        print("   muscles:", [m.get("name") for m in mus][:4], "n=", len(mus))