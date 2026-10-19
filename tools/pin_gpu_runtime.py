# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deliberately stage a locally built GPU engine; never copy a moving agents build."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'vendor/gpu/GPU_SOURCE_LOCK.pre-continuation.json'
if not old.exists():shutil.copyfile(ROOT/'GPU_SOURCE_LOCK.json',old)
lock=json.loads(old.read_text(encoding='utf-8'))
files=[f for f in lock['files'] if not f['copy'].replace('\\','/').startswith('vendor/gpu/runtime/')]
build=ROOT/'build/gpu-engine/Release'
exe=build/'chimera_engine.exe'
if not exe.is_file():raise SystemExit('Build the isolated GPU engine first')
for source in [exe]+sorted((build/'shaders').glob('*.spv')):
    dest=ROOT/'runtime/gpu'/source.relative_to(build)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    files.append({'source':source.relative_to(ROOT).as_posix(),'copy':dest.relative_to(ROOT).as_posix(),
                  'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
for source in sorted((ROOT/'native/gpu_engine').rglob('*')):
    if source.is_file():files.append({'source':source.relative_to(ROOT).as_posix(),'copy':source.relative_to(ROOT).as_posix(),
         'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bytes':source.stat().st_size})
lock={'schema':'chimera.studio.gpu-lock.v2','note':'Built in isolated Studio lane from the included native/gpu_engine sources; original vendor snapshot retained. Physics shader stages unchanged; presentation CSR/center mapping repaired for Blender. See tools/Build-Gpu.ps1.',
      'base_lock_sha256':hashlib.sha256((ROOT/'GPU_ENGINE_BASE_LOCK.json').read_bytes()).hexdigest(),
      'build':{'generator':'Visual Studio 17 2022','compiler':'MSVC 19.44.35228.0','configuration':'Release x64','vulkan_sdk':'1.4.328.1'},'files':files}
(ROOT/'GPU_SOURCE_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
print('Pinned',len(files),'files;',hashlib.sha256((ROOT/'GPU_SOURCE_LOCK.json').read_bytes()).hexdigest())
