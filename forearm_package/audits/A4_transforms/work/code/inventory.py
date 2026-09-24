"""Inventory of the real chimanoid.xml at the verified revision.
Read-only analysis; grounds the synthetic fixture in the true record counts.
"""
import xml.etree.ElementTree as ET
from collections import Counter

et = ET.parse(r"E:\PythonChimera\.tmp\chimanoid.xml")
root = et.getroot()

print("root tag:", root.tag, "| attrib:", dict(root.attrib))
for child in root:
    if child.tag in ("compiler", "option", "default", "size", "visual"):
        print("top-level:", child.tag, dict(child.attrib))
    elif child.tag == "worldbody":
        bodies = child.findall(".//body")
        print("worldbody bodies:", len(bodies))
        names = Counter(b.get("name") for b in bodies if b.get("name"))
        print("body names present:", len(names), "| unnamed bodies:", sum(1 for b in bodies if not b.get("name")))
        for n, c in names.most_common(80):
            print("   body:", n, "x", c)
        joint_types = Counter(j.get("type") for b in bodies for j in b.findall(".//joint"))
        print("joint type counts:", dict(joint_types))
        jn = [j.get("name") for b in bodies for j in b.findall(".//joint")]
        print("joints total (all types incl none):", len(jn))
        named = [j for j in jn if j]
        print("named joints:", len(named))
        print("  sample:", named[:10])
        # joints as direct attributes (old style joint="") on body
        body_jnt_attr = [b.get("joint") for b in bodies if b.get("joint")]
        print("body[joint=] attributes:", len(body_jnt_attr), body_jnt_attr[:10])
        # inertial/fullinertia
        print("bodies with inertial:", sum(1 for b in bodies if b.find("inertial") is not None))
        print("bodies with fullinertia:", sum(1 for b in bodies if b.find("fullinertia") is not None))
        print("bodies with freejoint:", sum(1 for b in bodies if b.find("freejoint") is not None))
        site_count = len(root.findall(".//site"))
        print("sites in worldbody:", site_count)

tendons = root.findall(".//tendon")
print("tendon defs:", len(tendons))
spatial = [t for t in tendons if t.get("class") == "muscle" or any(ch.tag == "spatial" for ch in t)]
print("spatial tendons:", sum(1 for t in tendons if t.find("spatial") is not None))
for t in tendons[:3]:
    print("  tendon:", t.tag, dict(t.attrib))
    sp = t.find("spatial")
    if sp is not None:
        for site in sp.findall("site"):
            print("     site:", dict(site.attrib))

actuators = root.findall(".//actuator") if root.findall(".//actuator") else []
print("actuator wrappers:", len(root.findall(".//actuator")))
muscles = root.findall(".//muscle")
print("muscle actuators:", len(muscles))
print("sample muscle:", dict(muscles[0].attrib))
print("sample muscle2:", dict(muscles[1].attrib))

contact = root.find(".//contact")
if contact is not None:
    print("contact paircount:", len([p for p in contact.findall("pair")]))
    print("contact excludefcount:", len([p for p in contact.findall("exclude")]))