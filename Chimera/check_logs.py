import os
import glob

logs = glob.glob('Saved/Logs/*.log')
if logs:
    latest_log = sorted(logs, key=os.path.getmtime)[-1]
    print(f'Latest log: {latest_log}')
    
    with open(latest_log, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    relevant = [l for l in lines if 'SPAWNED' in l or 'SPAWN FAILED' in l or 'Uninitialized script struct' in l or 'PreExit Game' in l or 'LogInit: Display: Starting Game' in l or 'GAMEMODE BEGINPLAY' in l]
    
    print(f'\nFound {len(relevant)} relevant lines:')
    for l in relevant[-30:]:
        print(l)
else:
    print('No log files found')
