"""
Two terminals. Two Pi agents. One conversation channel.
"""
import subprocess, os, time, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHANNEL = HERE / "docs" / "CHANNEL.md"
BRIEF = HERE / "docs" / "BRIEF.md"
PI = r"C:\Users\allen\node-portable\node-v22.23.1-win-x64\pi.CMD"
NEW_CONSOLE = 0x00000010

# Shared message file
CHANNEL.write_text("# CHANNEL - Agent Conversation\n\nDYAD: Awaiting instructions.\n", encoding="utf-8")
BRIEF.write_text("# DYAD BRIEF\n\nTwo-agent system active.\n", encoding="utf-8")

os.chdir(str(HERE))

# Launch DYAD terminal - watches channel, produces guidance
dyad_py = r"""
import subprocess, time, os
os.chdir(r'""" + str(HERE) + r"""')
PI = r'""" + PI + r"""'
CHANNEL_FILE = r'""" + str(CHANNEL) + r"""'
BRIEF_FILE = r'""" + str(BRIEF) + r"""'

print('=== DYAD AGENT ===')
print('Watching conversation channel. Writing guidance.')
print()

while True:
    # Read the channel to see LEAD's latest message
    channel_text = open(CHANNEL_FILE, encoding='utf-8').read()
    brief_text = open(BRIEF_FILE, encoding='utf-8').read() if os.path.exists(BRIEF_FILE) else ''
    
    prompt = (
        f"You are the DYAD — the guiding mind. Read the conversation channel and brief.\n\n"
        f"CHANNEL:\n{channel_text[-1500:]}\n\n"
        f"BRIEF:\n{brief_text[-1500:]}\n\n"
        f"If LEAD has sent a message or result, respond with:\n"
        f"1. Your analysis of what was done\n"
        f"2. What to do next, starting with 'NEXT:'\n"
        f"Write your full response to docs/CHANNEL.md starting with 'DYAD:'.\n"
        f"If no message from LEAD yet, just say 'DYAD: Waiting for LEAD.'"
    )
    
    r = subprocess.run([PI, '--provider', 'lmstudio', '--model', 'unsloth/qwen3.6-35b-a3b',
                        '--no-session', '-p', prompt],
                       capture_output=True, text=True, timeout=120, cwd=str(HERE))
    
    response = (r.stdout or '')[:1000]
    # Write to channel
    with open(CHANNEL_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\nDYAD: {response[:500]}\n")
    
    print(f"[DYAD] {response[:100].strip()}")
    time.sleep(15)
"""

p1 = subprocess.Popen(
    ['cmd.exe', '/k', f'cd /d {HERE} && python -c "{dyad_py}"'],
    creationflags=NEW_CONSOLE)
print(f'DYAD terminal launched. PID: {p1.pid}')

# Launch LEAD terminal - watches channel, executes work
lead_py = r"""
import subprocess, time, os
os.chdir(r'""" + str(HERE) + r"""')
PI = r'""" + r"C:\Users\allen\node-portable\node-v22.23.1-win-x64\pi.CMD" + r"""'
CHANNEL_FILE = r'""" + str(CHANNEL) + r"""'

print('=== LEAD AGENT ===')
print('Watching for DYAD instructions. Executing with full tools.')
print()

while True:
    channel_text = open(CHANNEL_FILE, encoding='utf-8').read()
    
    if 'NEXT:' in channel_text and 'LEAD:' not in channel_text.split('NEXT:')[-1][:200]:
        # DYAD has given an instruction
        prompt = (
            f"You are the LEAD developer. You have FULL TOOL ACCESS.\n"
            f"Read files, edit code, run commands, use MCP.\n\n"
            f"CHANNEL:\n{channel_text[-1500:]}\n\n"
            f"Execute DYAD's instruction. When done, write your results "
            f"to docs/CHANNEL.md starting with 'LEAD:'. Include what you "
            f"accomplished starting with 'RESULT:'."
        )
        
        r = subprocess.run([PI, '--provider', 'lmstudio', '--model', 'unsloth/qwen3.6-35b-a3b',
                            '--no-session', '-p', prompt],
                           capture_output=True, text=True, timeout=300, cwd=str(HERE))
        
        response = (r.stdout or '')[:1000]
        with open(CHANNEL_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\nLEAD: {response[:500]}\n")
        
        print(f"[LEAD] Task complete.")
    else:
        print("[LEAD] Waiting for DYAD instruction...")
    
    time.sleep(10)
"""

p2 = subprocess.Popen(
    ['cmd.exe', '/k', f'cd /d {HERE} && python -c "{lead_py}"'],
    creationflags=NEW_CONSOLE)
print(f'LEAD terminal launched. PID: {p2.pid}')

print(f'\nTwo terminals should be visible now.')
print(f'DYAD watches the channel and produces guidance.')
print(f'LEAD watches the channel and executes instructions.')
print(f'They talk through docs/CHANNEL.md.')
print(f'\nClose the terminal windows to stop, or press Ctrl+C here.')
input('\nPress Enter to stop both agents...')

import signal
for p in [p1, p2]:
    try: p.terminate()
    except: pass
print("Agents stopped.")
