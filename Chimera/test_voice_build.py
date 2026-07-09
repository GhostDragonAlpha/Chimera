#!/usr/bin/env python3
"""Quick UBT build test for VoiceEntity files."""

import subprocess
from pathlib import Path

# Setup UBT path from preflight
ue_root = 'C:/Program Files/Epic Games/UE_5.8'
ubt_path_new = ue_root + '/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe'
ubt_path_legacy = ue_root + '/Engine/Binaries/DotNET/UnrealBuildTool.exe'

if Path(ubt_path_new).exists():
    ubt_path = ubt_path_new
elif Path(ubt_path_legacy).exists():
    ubt_path = ubt_path_legacy
else:
    print('UBT not found')
    import sys
    sys.exit(1)

uproject = str(Path('Chimera.uproject').resolve())

# Build command (same as UBTBuilder uses)
ubt_command = [
    ubt_path,
    'ChimeraEditor',
    'Win64',
    'Development',
    uproject,
    '-TargetType=Editor',
    '-Progress',
    '-NoEngineChanges',
    '-NoHotReloadFromIDE'
]

print('Running UBT build...')
print('Command: ' + ' '.join(ubt_command))
print()

try:
    result = subprocess.run(ubt_command, capture_output=True, text=True, errors='replace', timeout=300)
    
    # Check for success/failure
    if result.returncode == 0:
        print('BUILD SUCCESSFUL!')
    else:
        print('Build failed with return code ' + str(result.returncode))
        
    # Show last 50 lines of output (most relevant)
    lines = result.stdout.split(chr(10))[-60:] if result.stdout else []
    for line in lines:
        if any(kw in line.lower() for kw in ['error', 'warning', 'succeeded', 'failed', 'voice', 'nlp', 'tts']):
            print('  ' + line)
            
except subprocess.TimeoutExpired:
    print('Build timed out (300s)')
