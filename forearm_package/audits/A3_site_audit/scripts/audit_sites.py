"""A3 site audit — independent verification of the 32 forearm packet sites
against the raw source XML. Reimplemented from scratch (stdlib only); the
pipeline's own test suite (run_tests.py S13 etc.) is NOT invoked.

Checks per site:
  (a) exact float identity: packet source_pos_local == float triple of XML pos
  (b) unit check: 0.065 (MESH_UNIT_TO_M) NOT applied; detectability shown
  (c) identity: owning body in XML + every spatial tendon referencing the site
      with path index + path length, compared to packet tendon_membership
  (d) role: derived from path index (0=first_endpoint, last=last_endpoint,
      interior=waypoint) vs packet role fields
Plus completeness, provenance uniformity, and canonical-hash reproduction.
Writes receipts/audit_receipt.json; prints human-readable summary.
"""
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

BASE = r"E:\PythonChimera\forearm_package\baseline_snapshot"
XML_PATH = os.path.join(BASE, "source_xml", "chimanoid.xml")
PACKET_PATH = os.path.join(BASE, "runs", "attachment_candidates.json")
OUT_DIR = r"E:\PythonChimera\forearm_package\audits\A3_site_audit\receipts"

MESH_UNIT_TO_M = 0.065  # the factor that must NEVER touch source coordinates

EXPECT_RAW_SHA = "675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1"
EXPECT_CANON_SHA = "7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5"
EXPECT_FITTED_SHA = "a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937"

# ---------------------------------------------------------------- XML parse
with open(XML_PATH, "rb") as fh:
    xml_bytes = fh.read()

raw_sha = hashlib.sha256(xml_bytes).hexdigest()  # independent reimplementation
canonical_bytes = xml_bytes.replace(b"\r\n", b"\n").rstrip(b"\n") + b"\n"
canon_sha = hashlib.sha256(canonical_bytes).hexdigest()

root = ET.fromstring(xml_bytes)

# parent map for body attribution
parent = {c: p for p in root.iter() for c in p}

# site index: name -> list of dicts (allow duplicates to be detected)
xml_sites = {}
for s in root.iter("site"):
    name = s.get("name")
    body = parent[s]
    body_name = body.get("name") if body.tag == "body" else "(non-body parent:%s)" % body.tag
    raw_pos = s.get("pos")
    xml_sites.setdefault(name, []).append({
        "body": body_name,
        "pos_raw": raw_pos,
        "pos_floats": [float(v) for v in raw_pos.split()] if raw_pos else [0.0, 0.0, 0.0],
    })

# spatial tendons: name -> ordered site-name list
spatial = {}
for sp in root.iter("spatial"):
    nm = sp.get("name")
    sites_in_order = [s.get("site") for s in sp.findall("site")]
    spatial[nm] = sites_in_order

# reverse index: site -> {tendon: index}
site_tendons = {}
for tname, sites_in_order in spatial.items():
    for i, sn in enumerate(sites_in_order):
        site_tendons.setdefault(sn, {})[tname] = i

# --------------------------------------------------------------- packet load
with open(PACKET_PATH, "rb") as fh:
    packet_bytes = fh.read()
packet = json.loads(packet_bytes)

prov = packet["provenance_hashes"]

rows = []
fail_count = 0

for body_name in ("radius", "radius_l"):
    side = "right" if body_name == "radius" else "left"
    body_pkt = packet["bodies"][body_name]
    for cand in body_pkt["candidates"]:
        sid = cand["site_id"]
        pkt_pos = cand["source_pos_local"]
        r = {
            "site_id": sid,
            "packet_body": cand.get("source_body"),
            "side": side,
            "in_xml": sid in xml_sites,
            "xml_occurrences": len(xml_sites.get(sid, [])),
            "checks": {},
        }
        fails = []

        if not r["in_xml"]:
            r["verdict"] = "FAIL"
            r["reason"] = "site not found in XML"
            rows.append(r)
            fail_count += 1
            continue

        occ = xml_sites[sid]
        xe = occ[0]
        r["xml_body"] = xe["body"]
        r["xml_pos_raw"] = xe["pos_raw"]
        r["xml_pos_floats"] = xe["pos_floats"]
        r["packet_pos_floats"] = pkt_pos

        # (a) exact float identity (no tolerance)
        eq_exact = pkt_pos == xe["pos_floats"]
        # also verify per-coordinate float() of the raw string tokens
        str_roundtrip = [repr(float(v)) for v in xe["pos_raw"].split()] == [repr(v) for v in pkt_pos]
        r["checks"]["exact_equality"] = eq_exact
        r["checks"]["raw_string_roundtrip_identical_repr"] = str_roundtrip
        if not eq_exact:
            fails.append("float identity: packet=%r xml=%r" % (pkt_pos, xe["pos_floats"]))

        # (b) unit check: prove 0.065 was not applied
        scaled = [v * MESH_UNIT_TO_M for v in xe["pos_floats"]]
        not_scaled = pkt_pos != scaled
        scaled_differs_from_xml = scaled != xe["pos_floats"]  # detectability
        max_abs_scaled_delta = max(abs(a - b) for a, b in zip(pkt_pos, scaled))
        r["checks"]["packet_equals_xml_not_scaled"] = not_scaled and eq_exact
        r["checks"]["would_be_scaled_value"] = scaled
        r["checks"]["scaled_would_differ_from_xml"] = scaled_differs_from_xml
        r["checks"]["max_abs_packet_vs_scaled_delta"] = max_abs_scaled_delta
        if not not_scaled:
            fails.append("packet equals XML*0.065 -> unit factor WAS applied")
        if not scaled_differs_from_xml:
            r["checks"]["unit_check_undetectable_all_zero"] = True

        # (c) identity: owning body + tendon references
        body_ok = xe["body"] == body_name == cand.get("source_body")
        r["checks"]["body_match"] = body_ok
        if not body_ok:
            fails.append("body: xml=%s packet_body=%s expected=%s" % (xe["body"], cand.get("source_body"), body_name))

        xml_mem = site_tendons.get(sid, {})
        pkt_mem = cand["tendon_membership"]
        pkt_mem_map = {m["tendon"]: m for m in pkt_mem}
        tendons_match = set(xml_mem) == set(pkt_mem_map)
        r["checks"]["tendon_set_match"] = tendons_match
        r["xml_tendon_refs"] = {t: {"index": i, "path_length": len(spatial[t])} for t, i in sorted(xml_mem.items())}
        if not tendons_match:
            fails.append("tendon set: xml=%s packet=%s" % (sorted(xml_mem), sorted(pkt_mem_map)))
        mem_detail = []
        for tname, idx in sorted(xml_mem.items()):
            plen = len(spatial[tname])
            derived_role = "first_endpoint" if idx == 0 else ("last_endpoint" if idx == plen - 1 else "waypoint")
            entry = {
                "tendon": tname,
                "xml_index_in_path": idx,
                "xml_path_length": plen,
                "derived_role": derived_role,
            }
            if tname in pkt_mem_map:
                m = pkt_mem_map[tname]
                entry["packet_index_in_path"] = m.get("index_in_path")
                entry["packet_path_length"] = m.get("path_length")
                entry["packet_role"] = m.get("role")
                entry["index_match"] = m.get("index_in_path") == idx
                entry["pathlen_match"] = m.get("path_length") == plen
                entry["role_match"] = m.get("role") == derived_role
                if not entry["index_match"]:
                    fails.append("index in %s: xml=%s packet=%s" % (tname, idx, m.get("index_in_path")))
                if not entry["pathlen_match"]:
                    fails.append("path_length in %s: xml=%s packet=%s" % (tname, plen, m.get("path_length")))
                if not entry["role_match"]:
                    fails.append("role in %s: derived=%s packet=%s" % (tname, derived_role, m.get("role")))
            else:
                fails.append("membership missing in packet: %s" % tname)
            mem_detail.append(entry)
        r["membership_comparison"] = mem_detail

        # (d) aggregate endpoint_roles consistency
        derived_endpoints = sorted({e["derived_role"] for e in mem_detail if e["derived_role"] != "waypoint"})
        pkt_endpoint_roles = sorted(cand["endpoint_roles"])
        if derived_endpoints:
            agg_ok = pkt_endpoint_roles == derived_endpoints
        else:
            # pure waypoint site: packet may store ['waypoint'] or []
            agg_ok = pkt_endpoint_roles in (["waypoint"], [])
        r["checks"]["derived_endpoint_roles"] = derived_endpoints
        r["checks"]["packet_endpoint_roles"] = pkt_endpoint_roles
        r["checks"]["endpoint_roles_consistent"] = agg_ok
        if not agg_ok:
            fails.append("endpoint_roles: derived=%s packet=%s" % (derived_endpoints, pkt_endpoint_roles))

        r["verdict"] = "PASS" if not fails else "FAIL"
        if fails:
            r["reasons"] = fails
            fail_count += 1
        rows.append(r)

# ------------------------------------------------------------- completeness
xml_body_sites = {}
for bname in ("radius", "radius_l"):
    for s in root.iter("site"):
        if parent[s].tag == "body" and parent[s].get("name") == bname:
            xml_body_sites.setdefault(bname, []).append(s.get("name"))

pkt_sites = {}
for bname in ("radius", "radius_l"):
    pkt_sites[bname] = [c["site_id"] for c in packet["bodies"][bname]["candidates"]]

completeness = {}
for bname in ("radius", "radius_l"):
    xset, pset = set(xml_body_sites[bname]), set(pkt_sites[bname])
    completeness[bname] = {
        "xml_n_sites": len(xml_body_sites[bname]),
        "packet_n_candidates": len(pkt_sites[bname]),
        "packet_not_in_xml": sorted(pset - xset),  # invented sites
        "xml_not_in_packet": sorted(xset - pset),  # missing sites
        "duplicates_in_xml": sorted(n for n in xset if len(xml_sites[n]) > 1),
        "set_equal": xset == pset,
    }

# every packet site in >=1 spatial tendon
no_tendon = [r["site_id"] for r in rows if r.get("xml_tendon_refs") is not None and len(r["xml_tendon_refs"]) == 0]

# role counts: site-level aggregate (any endpoint membership dominates) and membership-level
role_site = {"right": {"first_endpoint": 0, "last_endpoint": 0, "waypoint": 0},
             "left": {"first_endpoint": 0, "last_endpoint": 0, "waypoint": 0}}
role_mem = {"right": {"first_endpoint": 0, "last_endpoint": 0, "waypoint": 0},
            "left": {"first_endpoint": 0, "last_endpoint": 0, "waypoint": 0}}
for r in rows:
    eps = r["checks"].get("derived_endpoint_roles", [])
    if "first_endpoint" in eps:
        agg = "first_endpoint"
    elif "last_endpoint" in eps:
        agg = "last_endpoint"
    else:
        agg = "waypoint"
    role_site[r["side"]][agg] += 1
    for e in r["membership_comparison"]:
        role_mem[r["side"]][e["derived_role"]] += 1

# ------------------------------------------------------------- provenance
per_site_prov_keys = set()
for bname in ("radius", "radius_l"):
    for c in packet["bodies"][bname]["candidates"]:
        per_site_prov_keys.update(k for k in c if "provenance" in k or "sha256" in k)

prov_verdict = {
    "packet_level_block": prov,
    "per_site_provenance_keys_found": sorted(per_site_prov_keys),
    "raw_sha_recomputed": raw_sha,
    "raw_sha_matches_packet": raw_sha == prov["source_xml_raw_sha256"],
    "raw_sha_matches_expected": raw_sha == EXPECT_RAW_SHA,
    "canon_sha_recomputed": canon_sha,
    "canon_sha_matches_packet": canon_sha == prov["source_xml_canonical_sha256"],
    "canon_sha_matches_expected": canon_sha == EXPECT_CANON_SHA,
    "canon_recipe": "sha256(data.replace(b'\\r\\n', b'\\n').rstrip(b'\\n') + b'\\n')  [stdin-dependent CRLF normalization per intake.py:64]",
}

# fitted packet hash: try to identify the file it pins
fitted_candidates = {}
runs_dir = os.path.join(BASE, "runs")
for fn in sorted(os.listdir(runs_dir)):
    p = os.path.join(runs_dir, fn)
    if os.path.isfile(p):
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        fitted_candidates[fn] = h
fitted_match = [fn for fn, h in fitted_candidates.items() if h == EXPECT_FITTED_SHA]
prov_verdict["fitted_packet_sha256_search"] = {
    "expected": EXPECT_FITTED_SHA,
    "files_hashed": fitted_candidates,
    "matches": fitted_match,
}

# --------------------------------------------------------------- summary
summary = {
    "n_rows": len(rows),
    "n_pass": sum(1 for r in rows if r["verdict"] == "PASS"),
    "n_fail": fail_count,
    "completeness": completeness,
    "sites_without_tendon": no_tendon,
    "role_counts_site_level": role_site,
    "role_counts_membership_level": role_mem,
    "spatial_tendon_count": len(spatial),
    "xml_total_sites": sum(len(v) for v in xml_sites.values()),
    "provenance": prov_verdict,
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "audit_receipt.json"), "w", encoding="utf-8") as fh:
    json.dump({"summary": summary, "rows": rows}, fh, indent=1)

print(json.dumps(summary, indent=1))
print("\nper-site verdicts:")
for r in rows:
    print(" %-14s %s" % (r["site_id"], r["verdict"]))
