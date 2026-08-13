"""kernel_dsl.py -- .chimera kernel DSL: declare a point-source interaction,
get every code fragment the Barnes-Hut tree needs for it.

The tree does not care WHAT it aggregates. A kernel declaration names:
  quantity   - the per-particle field (mass, lum, charge, ...)
  aggregate  - how children combine into a node (weighted_sum, bipolar_sum, sum)
  kernel_fn  - the far-field law (inverse_squared, irradiance)
  sign       - attractive | repulsive | bipolar (sign rides on the quantities)
  coupling   - named constant the host program defines (G, K_E, ...)
  toggle     - optional runtime gate (emEnabled)

generate_kernel(decl) returns the six fragments the brief requires;
generate_regions() assembles the seven named regions that --inject splices
into spiace_phase6.html between // <GENERATED:NAME> ... // </GENERATED:NAME>
markers. --verify checks those regions are current (used by test_phase6.py).

Node layout (must match the WGSL TreeNode struct and packTree exactly):
  base 64 B: bb_min @0 (12) | bb_max @12 (12) | children @24 (8 x u32)
             | leaf_offset @56 | leaf_count @60
  then 16 B per kernel, in declaration order: center vec3f + quantity f32
  gravity @64 | light @80 | electromagnetism @96 | heat @112  ->  128 B/node

kernel_fn vocabulary:
  inverse_squared  - force-like, F ~ q1 q2 / d^2 along the displacement
  irradiance       - scalar flux field, E = L/(4 pi d^2)  -> accumulates `flux`
  potential_1r     - scalar potential field, T = Q * coupling / d (steady-state
                     diffusion Green's function)  -> accumulates `theat` (WGSL)
                     / `fluxOut.t` (JS). A field, not a force: no pair PE.
"""

import re
import sys

BASE_NODE_BYTES = 64
KERNEL_NODE_BYTES = 16

KERNELS_TEXT = r'''
kernel gravity {
    quantity  = "mass"
    aggregate = "weighted_sum"    # total = sum(m), center = m-weighted (COM)
    kernel_fn = "inverse_squared"
    sign      = "attractive"
    coupling  = "G"
}

kernel light {
    quantity  = "lum"
    aggregate = "weighted_sum"    # total = sum(L), center = L-weighted (COL)
    kernel_fn = "irradiance"      # E = L / (4 pi d^2) -- scalar flux, no force
    sign      = "attractive"
    coupling  = "FOUR_PI"
}

kernel electromagnetism {
    quantity  = "charge"
    aggregate = "bipolar_sum"     # total = sum(q) signed, center = |q|-weighted
    kernel_fn = "inverse_squared"
    sign      = "bipolar"         # attraction AND repulsion (sign on q1*q2)
    coupling  = "K_E"
    toggle    = "emEnabled"
}

kernel heat {
    quantity  = "heat"            # per-particle heat source (W) = thermal emission
    aggregate = "weighted_sum"    # total = sum(Q), center = Q-weighted (sources >= 0)
    kernel_fn = "potential_1r"    # T = Q/(4 pi kappa d) — steady-state diffusion Green's fn
    sign      = "attractive"      # positive sources raise the temperature field
    coupling  = "KAPPA_INV_4PI"   # 1/(4 pi kappa), host-derived (diffusion == radiation @1AU)
    toggle    = "heatEnabled"
}
'''

AGGREGATES = {"weighted_sum", "bipolar_sum", "sum"}
KERNEL_FNS = {"inverse_squared", "irradiance", "potential_1r"}
SIGNS = {"attractive", "repulsive", "bipolar"}
REQUIRED = ("quantity", "aggregate", "kernel_fn", "sign", "coupling")


# --- parser -------------------------------------------------------------------

def parse_kernels(text: str = KERNELS_TEXT) -> list[dict]:
    """Parse kernel declarations. Refuses compound/unknown claims loudly."""
    kernels = []
    for m in re.finditer(r"kernel\s+(\w+)\s*\{(.*?)\}", text, re.S):
        name, body = m.group(1), m.group(2)
        fields = {}
        for line in body.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            fm = re.match(r'(\w+)\s*=\s*"([^"]*)"', line)
            if not fm:
                raise ValueError(f"kernel {name}: unparsable line: {line!r}")
            fields[fm.group(1)] = fm.group(2)
        for req in REQUIRED:
            if req not in fields:
                raise ValueError(f"kernel {name}: missing required field {req!r}")
        if fields["aggregate"] not in AGGREGATES:
            raise ValueError(f"kernel {name}: unknown aggregate {fields['aggregate']!r}")
        if fields["kernel_fn"] not in KERNEL_FNS:
            raise ValueError(f"kernel {name}: unknown kernel_fn {fields['kernel_fn']!r}")
        if fields["sign"] not in SIGNS:
            raise ValueError(f"kernel {name}: unknown sign {fields['sign']!r}")
        fields["name"] = name
        fields["node_offset"] = BASE_NODE_BYTES + KERNEL_NODE_BYTES * len(kernels)
        kernels.append(fields)
    if not kernels:
        raise ValueError("no kernels declared")
    return kernels


# --- WGSL generators (host names: n, tgt, a, flux, params, masses, lums, ----
#     charges, idx, pid, dx, dy, dz, dist_sq, dist; consts G, K_E, FOUR_PI) ---

def _wgsl_fields(k: dict) -> str:
    o = k["node_offset"]
    q = k["quantity"]
    return (f"  {k['name']}_c : array<f32, 3>, // @{o} center of {q}\n"
            f"  {k['name']}_q : f32,           // @{o + 12} total {q}")


def _wgsl_accept(k: dict) -> str:
    """Accumulation from an ACCEPTED node (opening-angle criterion passed)."""
    nm = k["name"]
    if k["kernel_fn"] == "irradiance":
        return (f"    // kernel {nm}: irradiance from center of {k['quantity']} (scalar flux)\n"
                "    {\n"
                f"      let dx = n.{nm}_c[0] - tgt.x;\n"
                f"      let dy = n.{nm}_c[1] - tgt.y;\n"
                f"      let dz = n.{nm}_c[2] - tgt.z;\n"
                "      let d_sq = dx*dx + dy*dy + dz*dz + params.softening_sq;\n"
                f"      flux += n.{nm}_q / (FOUR_PI * d_sq);\n"
                "    }")
    if k["kernel_fn"] == "potential_1r":
        gate = k.get("toggle")
        body = (f"      let dx = n.{nm}_c[0] - tgt.x;\n"
                f"      let dy = n.{nm}_c[1] - tgt.y;\n"
                f"      let dz = n.{nm}_c[2] - tgt.z;\n"
                "      let d_sq = dx*dx + dy*dy + dz*dz + params.softening_sq;\n"
                f"      theat += n.{nm}_q * {k['coupling']} / sqrt(d_sq); // T field, 1/d\n")
        head = (f"    // kernel {nm}: potential_1r from center of {k['quantity']} (scalar temperature field)\n"
                "    {\n")
        if gate:
            return head + f"      if (params.{gate} == 1u) {{\n" + body + "      }\n    }"
        return head + body + "    }"
    head = (f"    // kernel {nm}: {k['sign']} {k['kernel_fn']} from center of {k['quantity']}\n"
            "    {\n")
    if k["sign"] == "bipolar":
        body = (f"      if (params.emEnabled == 1u) {{\n"
                f"        let dx_{nm} = n.{nm}_c[0] - tgt.x;\n"
                f"        let dy_{nm} = n.{nm}_c[1] - tgt.y;\n"
                f"        let dz_{nm} = n.{nm}_c[2] - tgt.z;\n"
                f"        let d_sq_{nm} = dx_{nm}*dx_{nm} + dy_{nm}*dy_{nm} + dz_{nm}*dz_{nm} + params.softening_sq;\n"
                f"        let dist_{nm} = sqrt(d_sq_{nm});\n"
                f"        let f_{nm} = {k['coupling']} * charges[idx] * n.{nm}_q / (masses[idx] * d_sq_{nm} * dist_{nm});\n"
                f"        a -= f_{nm} * vec3f(dx_{nm}, dy_{nm}, dz_{nm}); // like signs repel\n"
                "      }\n")
    else:
        op = "+=" if k["sign"] == "attractive" else "-="
        body = (f"      let dx_{nm} = n.{nm}_c[0] - tgt.x;\n"
                f"      let dy_{nm} = n.{nm}_c[1] - tgt.y;\n"
                f"      let dz_{nm} = n.{nm}_c[2] - tgt.z;\n"
                f"      let d_sq_{nm} = dx_{nm}*dx_{nm} + dy_{nm}*dy_{nm} + dz_{nm}*dz_{nm} + params.softening_sq;\n"
                f"      let dist_{nm} = sqrt(d_sq_{nm});\n"
                f"      let f_{nm} = {k['coupling']} * n.{nm}_q / (d_sq_{nm} * dist_{nm});\n"
                f"      a {op} f_{nm} * vec3f(dx_{nm}, dy_{nm}, dz_{nm});\n")
    return head + body + "    }"


def _wgsl_leaf(k: dict) -> str:
    """Direct accumulation from one leaf particle (dx/dy/dz/dist_sq/dist in scope)."""
    nm = k["name"]
    if k["kernel_fn"] == "irradiance":
        return f"        flux += {k['quantity']}s[pid] / (FOUR_PI * dist_sq); // kernel {nm}"
    if k["kernel_fn"] == "potential_1r":
        stmt = f"theat += {k['quantity']}s[pid] * {k['coupling']} / dist;"
        gate = k.get("toggle")
        if gate:
            return f"        if (params.{gate} == 1u) {{ {stmt} }} // kernel {nm}"
        return f"        {stmt} // kernel {nm}"
    if k["sign"] == "bipolar":
        return (f"        if (params.emEnabled == 1u) {{ // kernel {nm} (bipolar)\n"
                f"          let f_{nm} = {k['coupling']} * charges[idx] * charges[pid] / (masses[idx] * dist_sq * dist);\n"
                f"          a -= f_{nm} * vec3f(dx, dy, dz);\n"
                "        }")
    op = "+=" if k["sign"] == "attractive" else "-="
    return (f"        {{ let f_{nm} = {k['coupling']} * {k['quantity']}es[pid] / (dist_sq * dist);\n"
            f"          a {op} f_{nm} * vec3f(dx, dy, dz); }} // kernel {nm}")


# --- JS generators (host names: node, particles, targetPos, target, acc, -----
#     fluxOut, pi, pj, dist; consts G, K_E, FOUR_PI, SOFT_SQ, emEnabled) -------

def _js_aggregate(k: dict) -> str:
    """Node aggregation over a particle list, run at tree build (CPU)."""
    nm = k["name"]
    q = k["quantity"]
    if k["aggregate"] == "bipolar_sum":
        return (f"  // kernel {nm}: bipolar_sum -> total = signed sum, center = |q|-weighted\n"
                f"  node.k_{nm}_q = 0; node.k_{nm}_w = 0; node.k_{nm}_c = [0, 0, 0];\n"
                "  for (const p of particles) {\n"
                f"    const w = Math.abs(p.{q});\n"
                f"    node.k_{nm}_q += p.{q};\n"
                f"    node.k_{nm}_w += w;\n"
                f"    node.k_{nm}_c[0] += w * p.pos[0];\n"
                f"    node.k_{nm}_c[1] += w * p.pos[1];\n"
                f"    node.k_{nm}_c[2] += w * p.pos[2];\n"
                "  }\n"
                f"  if (node.k_{nm}_w > 0) for (let d = 0; d < 3; d++) node.k_{nm}_c[d] /= node.k_{nm}_w;")
    return (f"  // kernel {nm}: weighted_sum -> total = sum, center = q-weighted\n"
            f"  node.k_{nm}_q = 0; node.k_{nm}_c = [0, 0, 0];\n"
            "  for (const p of particles) {\n"
            f"    node.k_{nm}_q += p.{q};\n"
            f"    node.k_{nm}_c[0] += p.{q} * p.pos[0];\n"
            f"    node.k_{nm}_c[1] += p.{q} * p.pos[1];\n"
            f"    node.k_{nm}_c[2] += p.{q} * p.pos[2];\n"
            "  }\n"
            f"  if (node.k_{nm}_q > 0) for (let d = 0; d < 3; d++) node.k_{nm}_c[d] /= node.k_{nm}_q;")


def _js_accept(k: dict) -> str:
    nm = k["name"]
    if k["kernel_fn"] == "irradiance":
        return (f"  // kernel {nm}: irradiance from center of {k['quantity']}\n"
                "  {\n"
                f"    const dx = node.k_{nm}_c[0] - targetPos[0];\n"
                f"    const dy = node.k_{nm}_c[1] - targetPos[1];\n"
                f"    const dz = node.k_{nm}_c[2] - targetPos[2];\n"
                f"    fluxOut.v += node.k_{nm}_q / (FOUR_PI * (dx*dx + dy*dy + dz*dz + SOFT_SQ));\n"
                "  }")
    if k["kernel_fn"] == "potential_1r":
        gate = k.get("toggle")
        body = (f"    const dx = node.k_{nm}_c[0] - targetPos[0];\n"
                f"    const dy = node.k_{nm}_c[1] - targetPos[1];\n"
                f"    const dz = node.k_{nm}_c[2] - targetPos[2];\n"
                f"    fluxOut.t += node.k_{nm}_q * {k['coupling']} / Math.sqrt(dx*dx + dy*dy + dz*dz + SOFT_SQ);")
        head = f"  // kernel {nm}: potential_1r (scalar temperature field)"
        if gate:
            return f"{head} (gated by {gate})\n  if ({gate}) {{\n{body}\n  }}"
        return f"{head}\n  {{\n{body}\n  }}"
    if k["sign"] == "bipolar":
        body = (f"    const dx = node.k_{nm}_c[0] - targetPos[0];\n"
                f"    const dy = node.k_{nm}_c[1] - targetPos[1];\n"
                f"    const dz = node.k_{nm}_c[2] - targetPos[2];\n"
                "    const dSq = dx*dx + dy*dy + dz*dz + SOFT_SQ;\n"
                "    const dist = Math.sqrt(dSq);\n"
                f"    const f = {k['coupling']} * target.{k['quantity']} * node.k_{nm}_q / (target.mass * dSq * dist);\n"
                "    acc[0] -= f * dx; acc[1] -= f * dy; acc[2] -= f * dz; // like signs repel")
        gate = k.get("toggle")
        head = f"  // kernel {nm}: bipolar {k['kernel_fn']}" + (f" (gated by {gate})" if gate else "")
        if gate:
            return f"{head}\n  if ({gate}) {{\n{body}\n  }}"
        return f"{head}\n  {{\n{body}\n  }}"
    op = "+=" if k["sign"] == "attractive" else "-="
    return (f"  // kernel {nm}: {k['sign']} {k['kernel_fn']}\n"
            "  {\n"
            f"    const dx = node.k_{nm}_c[0] - targetPos[0];\n"
            f"    const dy = node.k_{nm}_c[1] - targetPos[1];\n"
            f"    const dz = node.k_{nm}_c[2] - targetPos[2];\n"
            "    const dSq = dx*dx + dy*dy + dz*dz + SOFT_SQ;\n"
            "    const dist = Math.sqrt(dSq);\n"
            f"    const f = {k['coupling']} * node.k_{nm}_q / (dSq * dist);\n"
            f"    acc[0] {op} f * dx; acc[1] {op} f * dy; acc[2] {op} f * dz;\n"
            "  }")


def _js_leaf(k: dict) -> str:
    nm = k["name"]
    if k["kernel_fn"] == "irradiance":
        return f"  fluxOut.v += p.{k['quantity']} / (FOUR_PI * distSq); // kernel {nm}"
    if k["kernel_fn"] == "potential_1r":
        stmt = f"fluxOut.t += p.{k['quantity']} * {k['coupling']} / dist;"
        gate = k.get("toggle")
        if gate:
            return f"  if ({gate}) {{ {stmt} }} // kernel {nm}"
        return f"  {stmt} // kernel {nm}"
    if k["sign"] == "bipolar":
        body = (f"  const f = {k['coupling']} * target.{k['quantity']} * p.{k['quantity']} / (target.mass * distSq * dist);\n"
                "  acc[0] -= f * dx; acc[1] -= f * dy; acc[2] -= f * dz;")
        gate = k.get("toggle")
        if gate:
            return f"  if ({gate}) {{ // kernel {nm} (bipolar)\n{body}\n  }}"
        return f"  // kernel {nm} (bipolar)\n{body}"
    op = "+=" if k["sign"] == "attractive" else "-="
    return (f"  {{ const f = {k['coupling']} * p.{k['quantity']} / (distSq * dist);\n"
            f"    acc[0] {op} f * dx; acc[1] {op} f * dy; acc[2] {op} f * dz; }} // kernel {nm}")


def _js_energy_pe(k: dict) -> str:
    """One statement: the pair PE term of this kernel (empty for radiative)."""
    if k["kernel_fn"] in ("irradiance", "potential_1r"):
        return ""
    name = k["name"][0].upper() + k["name"][1:]
    if k["sign"] == "bipolar":
        return f"  const pe{name} = ({k['coupling']} * pi.{k['quantity']} * pj.{k['quantity']}) / dist; // sign rides on the charges"
    s = "-" if k["sign"] == "attractive" else "+"
    return f"  const pe{name} = {s}({k['coupling']} * pi.{k['quantity']} * pj.{k['quantity']}) / dist;"


def _js_pack(k: dict) -> str:
    o = k["node_offset"]
    return (f"    view.setFloat32(base + {o},      n.k_{k['name']}_c[0], true);\n"
            f"    view.setFloat32(base + {o + 4},  n.k_{k['name']}_c[1], true);\n"
            f"    view.setFloat32(base + {o + 8},  n.k_{k['name']}_c[2], true);\n"
            f"    view.setFloat32(base + {o + 12}, n.k_{k['name']}_q,  true); // kernel {k['name']}")


def generate_kernel(decl: dict) -> dict:
    """One declaration -> every code fragment the tree needs for this kernel."""
    return {
        "wgsl_node_fields": _wgsl_fields(decl),
        "wgsl_aggregate_fn": "(aggregation runs on the CPU at tree build; see cpu_aggregate_fn)",
        "wgsl_traversal_accum": _wgsl_accept(decl),
        "wgsl_leaf_accum": _wgsl_leaf(decl),
        "cpu_aggregate_fn": _js_aggregate(decl),
        "cpu_accept_fn": _js_accept(decl),
        "cpu_leaf_fn": _js_leaf(decl),
        "cpu_pack_fn": _js_pack(decl),
        "falsifier_check": _js_energy_pe(decl),
    }


# --- region assembly ----------------------------------------------------------

REGIONS = [
    "NODE_FIELDS_WGSL", "ACCEPT_WGSL", "LEAF_WGSL",
    "AGGREGATE_JS", "KERNEL_FNS_JS", "ENERGY_PE_JS", "PACK_JS",
]


def _assemble_energy_pe(kernels: list[dict], gen: list[dict]) -> str:
    """kernelPairPE: one named const per conservative kernel, object return."""
    cons = [(k, g) for k, g in zip(kernels, gen)
            if k["kernel_fn"] not in ("irradiance", "potential_1r")]
    lines = [g["falsifier_check"] for _, g in cons]
    names = ["pe" + k["name"][0].upper() + k["name"][1:] for k, _ in cons]
    keys = ", ".join(f"{k['name']}: {n}" for (k, _), n in zip(cons, names))
    total = " + ".join(names) if names else "0"
    return ("// Potential energy of one pair across all conservative kernels.\n"
            "// (irradiance/potential kernels transport energy or a field;\n"
            "//  they carry no pair PE)\n"
            "function kernelPairPE(pi, pj, dist) {\n"
            + "\n".join(lines) +
            f"\n  return {{ {keys}, total: {total} }};\n}}")


def generate_regions(text: str = KERNELS_TEXT) -> dict[str, str]:
    kernels = parse_kernels(text)
    gen = [generate_kernel(k) for k in kernels]
    accept_js = "\n\n".join(g["cpu_accept_fn"] for g in gen)
    leaf_js = "\n".join(g["cpu_leaf_fn"] for g in gen)
    return {
        "NODE_FIELDS_WGSL": "\n".join(g["wgsl_node_fields"] for g in gen),
        "ACCEPT_WGSL": "\n".join(g["wgsl_traversal_accum"] for g in gen),
        "LEAF_WGSL": "\n".join(g["wgsl_leaf_accum"] for g in gen),
        "AGGREGATE_JS": "\n\n".join(g["cpu_aggregate_fn"] for g in gen),
        "KERNEL_FNS_JS": (
            "// Per-kernel far-field accumulation for an ACCEPTED node.\n"
            "function kernelAccept(node, targetPos, target, acc, fluxOut) {\n"
            + accept_js +
            "\n}\n\n"
            "// Per-kernel direct accumulation from one leaf particle.\n"
            "function kernelLeaf(p, targetPos, target, acc, fluxOut) {\n"
            "  const dx = p.pos[0] - targetPos[0];\n"
            "  const dy = p.pos[1] - targetPos[1];\n"
            "  const dz = p.pos[2] - targetPos[2];\n"
            "  const distSq = dx*dx + dy*dy + dz*dz + SOFT_SQ;\n"
            "  const dist = Math.sqrt(distSq);\n"
            + leaf_js +
            "\n}"
        ),
        "ENERGY_PE_JS": _assemble_energy_pe(kernels, gen),
        "PACK_JS": "\n".join(g["cpu_pack_fn"] for g in gen),
    }


MARK_RE = lambda region: re.compile(
    r"([ \t]*// <GENERATED:" + region + r">).*?(// </GENERATED:" + region + r">)",
    re.S)


def inject(path: str, verify_only: bool = False) -> bool:
    """Rewrite (or verify) the GENERATED regions of an HTML file.

    Marker lines are JS/WGSL comments, so the file is valid with empty
    regions; injection fills them. verify_only returns True when current."""
    src = open(path, encoding="utf-8").read()
    regions = generate_regions()
    stale = []
    for region, body in regions.items():
        rx = MARK_RE(region)
        m = rx.search(src)
        if not m:
            raise ValueError(f"{path}: missing marker for region {region}")
        indent = m.group(1).replace("// <GENERATED:" + region + ">", "")
        indented = "\n".join((indent + line if line.strip() else line)
                             for line in body.split("\n"))
        current = m.group(0)
        wanted = m.group(1) + "\n" + indented + "\n" + indent + m.group(2).lstrip()
        # ^ end marker keeps its own indent; compare ignoring trailing ws
        if current.replace("\r\n", "\n").rstrip() != wanted.rstrip():
            stale.append(region)
            if not verify_only:
                src = src[:m.start()] + wanted + src[m.end():]
    if verify_only:
        return not stale
    open(path, "w", encoding="utf-8", newline="\n").write(src)
    if stale:
        print(f"injected: {', '.join(stale)}")
    else:
        print("all regions already current")
    return True


def _summary() -> None:
    kernels = parse_kernels()
    node_bytes = BASE_NODE_BYTES + KERNEL_NODE_BYTES * len(kernels)
    print(f"{len(kernels)} kernels declared; node size = "
          f"{BASE_NODE_BYTES} B base + {len(kernels)}x{KERNEL_NODE_BYTES} B = {node_bytes} B")
    for k in kernels:
        g = generate_kernel(k)
        print(f"  {k['name']:<16} quantity={k['quantity']:<8} fn={k['kernel_fn']:<15} "
              f"agg={k['aggregate']:<13} sign={k['sign']:<10} @{k['node_offset']}B "
              f"(wgsl fields {len(g['wgsl_node_fields'])} ch, traversal {len(g['wgsl_traversal_accum'])} ch)")


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[1] == "--verify":
        ok = inject(argv[2], verify_only=True)
        print(f"{argv[2]}: generated regions {'current' if ok else 'STALE'}")
        return 0 if ok else 1
    if len(argv) >= 3 and argv[1] == "--inject":
        inject(argv[2])
        return 0
    _summary()
    print("\nusage: --inject FILE.html | --verify FILE.html")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
