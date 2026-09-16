"""Compile the graph's thermal salvage experience for the native engine."""
import argparse
from pathlib import Path
from .common import canonical, digest, loads, require
from .force_catalog import ROOT
from .force_models import compile_packet

EXPERIENCE = "experience.science.thermal_salvage"

def compile_scene(graph):
    objects=graph.objects if hasattr(graph,"objects") else graph["objects"]
    obj=objects[EXPERIENCE]
    scene=obj["physical"]["contract"]
    require(scene["schema"]=="chimera.thermal_salvage.v1","thermal_scene_schema")
    require(scene["time"]["tick_hz"]==300 and scene["time"]["render_independent"] is True,
            "thermal_clock_contract")
    graph_hash=graph.graph_hash() if hasattr(graph,"graph_hash") else None
    bundle={"schema":"chimera.thermal_scene.v1","experience_id":EXPERIENCE,
        "recipe_sha256":digest(obj),"graph_hash":graph_hash,"models":compile_packet(graph),
        "scene":scene,"render_m_to_units":25,
        "camera":[11.5,.15,.35,-2.7,2.2,0,0,0],
        "page_file":str(ROOT/"tools/science_funnel/thermal.html"),
        "graph_file":str(ROOT/"tools/creature_graph/data/creature_graph.json"),
        "render_scope":"Uniform visual scale only. Native corrugated chamber volume equals its gas volume; beam profile is the ideal small-deflection solution. Diagnostic colors are not measured optics."}
    bundle["scene_sha256"]=digest(bundle)
    return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,default=ROOT/"tools/creature_graph/data/creature_graph.json")
    p.add_argument("--output",type=Path,default=ROOT/".tmp/thermal-salvage/scene.json")
    a=p.parse_args()
    from tools.creature_graph.store import CreatureGraph
    bundle=compile_scene(CreatureGraph.load(str(a.graph)))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(canonical(bundle))
    print(canonical({"scene":str(a.output),"scene_sha256":bundle["scene_sha256"],
                     "graph_hash":bundle["graph_hash"]}).decode())
if __name__=="__main__":main()
