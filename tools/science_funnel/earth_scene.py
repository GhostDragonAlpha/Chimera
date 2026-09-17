"""Pinned Earth field data and local native scene compilation; no weather inference."""
from pathlib import Path
import argparse,json,re,math
import numpy as np
from .common import canonical,digest,sha,require,local_file
from .force_models import compile_packet
from .macaque_anatomy import compile_native
from tools.creature_graph.store import CreatureGraph
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'tools/science_funnel/data/earth'
SOURCE='source.environment.earth';RECIPE='model.environment.earth_patch'

def source_parameters(data=DATA):
    receipt=json.loads((data/'download_receipt.json').read_text(encoding='utf-8-sig'));blobs={}
    require({f['path'] for f in receipt['sources']}=={'nga_wgs84.html','nasa_atmosphere_metric.html','nasa_drag.html'},'earth_source_inventory')
    for f in receipt['sources']:
        raw=local_file(data,f['path']).read_bytes();require(len(raw)==f['bytes'] and sha(raw)==f['sha256'],'earth_source_pin_drift');blobs[f['path']]=raw.decode('utf-8')
    # Extract the numeric rows/formula tokens from pinned primary pages, fail on drift.
    nga=blobs['nga_wgs84.html'];nasa=blobs['nasa_atmosphere_metric.html']
    a=re.search(r'(6378137\.0) meters',nga);f=re.search(r'>(298\.257223563)<',nga)
    require(a is not None and f is not None,'earth_datum_parse')
    for token in ['T=15.04-.00649h','p=101.29','273.1','288.08','5.256','.2869']:
        require(token in nasa,'earth_atmosphere_formula_drift',token)
    return {'datum':{'name':'WGS84','semi_major_m':float(a[1]),'inverse_flattening':float(f[1])},'atmosphere':{'model':'NASA_Glenn_troposphere_fit','max_altitude_m':10000.,'temperature0_C':15.04,'lapse_C_m':.00649,'pressure_scale_Pa':101290.,'fit_temperature_offset':273.1,'pressure_reference_K':288.08,'exponent':5.256,'density_R_J_kg_K':286.9,'celsius_to_kelvin':273.15,'scope':'Historical altitude-only educational curve fit; no weather, humidity or real-time climate. Preserve source 273.1 fit offset independently of Celsius-to-Kelvin conversion.'}},receipt

def local_frame(datum,latitude_deg,longitude_deg,altitude_m):
    require(all(math.isfinite(v) for v in (latitude_deg,longitude_deg,altitude_m)) and -90<=latitude_deg<=90 and -180<=longitude_deg<=180,'earth_coordinate_range')
    lat,lon=np.deg2rad([latitude_deg,longitude_deg]);a=datum['semi_major_m'];f=1/datum['inverse_flattening'];e2=f*(2-f);n=a/math.sqrt(1-e2*math.sin(lat)**2)
    origin=np.array([(n+altitude_m)*math.cos(lat)*math.cos(lon),(n+altitude_m)*math.cos(lat)*math.sin(lon),(n*(1-e2)+altitude_m)*math.sin(lat)])
    east=np.array([-math.sin(lon),math.cos(lon),0]);up=np.array([math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)]);south=np.cross(east,up)
    return origin,np.column_stack((east,up,south))

def compile_scene(graph,output):
    output=Path(output);params,receipt=source_parameters();obj=graph.get(RECIPE);scene=obj['physical']['contract'];source=graph.get(SOURCE)
    require(source['physical']['parameters']==params and source['physical']['receipt']==receipt,'earth_graph_source_drift')
    require(scene['schema']=='chimera.earth_patch.v1' and scene['tick_hz']==300,'earth_scene_contract')
    world=graph.get(scene['world_id']);patch=graph.get(scene['patch_id']);ground=graph.get(scene['ground_id']);port=graph.get(scene['hand_port_id'])
    require(world['physical']['datum']==params['datum'] and ground['geometry']['half_width_m']==scene['patch_half_width_m'],'earth_entity_recipe_drift')
    require(patch['spatial']['frame']=='local_EUS' and patch['spatial']['latitude_deg']==scene['latitude_deg'] and patch['spatial']['longitude_deg']==scene['longitude_deg'],'earth_patch_frame_drift')
    require(port['physical']['source_body']=='ref.macaque_arm.body.hand','earth_attachment_drift')
    arm=compile_native(graph,output/'arm');models=compile_packet(graph);require('399' in models['gravity'],'earth_gravity_missing')
    bundle={'schema':'chimera.earth_scene.v1','graph_hash':graph.graph_hash(),'recipe_sha256':digest(obj),'source_parameters':params,'models':models,'scene':scene,'arm':{'mesh_file':str(output/'arm/mesh.bin'),'body_file':str(output/'arm/body.bin'),'mesh_sha256':arm['mesh_sha256'],'body_sha256':arm['binding_sha256'],'hand_vertex_start':next(b for b in arm['bones'] if b['body']=='hand')['vertex_start'],'hand_vertex_count':next(b for b in arm['bones'] if b['body']=='hand')['vertex_count']},'page_file':str(ROOT/'tools/science_funnel/earth.html'),'graph_file':str(ROOT/'tools/creature_graph/data/creature_graph.json'),'sources':[{'title':f['path'],'url':f['url']} for f in receipt['sources']]+[{'title':'JPL gravitational parameters','url':'https://ssd.jpl.nasa.gov/astro_par.html'}],'scope':'Local Earth reference around a kinematic macaque arm. Source gravity/atmosphere and WGS84 frame; authored planar ground and reference sample coefficients. No measured terrain, weather, muscles, biological grasp, rolling, GPU-resident dynamics or whole planet simulation.'}
    bundle['scene_sha256']=digest(bundle);output.mkdir(parents=True,exist_ok=True);(output/'scene.json').write_bytes(canonical(bundle));return bundle

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.tmp/earth-patch');a=p.parse_args();g=CreatureGraph.load(str(ROOT/'tools/creature_graph/data/creature_graph.json'));b=compile_scene(g,a.output);print(json.dumps({'scene':str(a.output/'scene.json'),'hash':b['scene_sha256']}))
if __name__=='__main__':main()
