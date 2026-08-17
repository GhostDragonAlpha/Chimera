# SPIACE operator window launcher — the ONE entry point for the human.
# Starts the native relay (if not already up) on 127.0.0.1:8799 and opens
# the hub page (live sim + scoreboard + latest proofs) in the default browser.
#
#   python START_VIEWER.py            # default body: the standing teddy
#   python START_VIEWER.py bearhill   # any genome name in native/genomes/

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = 8799
genome = sys.argv[1] if len(sys.argv) > 1 else "teddystandmuscle"
if not genome.endswith(".chimera"):
    genome += ".chimera"
genome_path = HERE / "native" / "genomes" / genome
if not genome_path.exists():
    sys.exit(f"no such genome: {genome_path}")


def port_open():
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


if port_open():
    print(f"relay already on :{PORT} — opening hub")
else:
    subprocess.Popen(
        [sys.executable, str(HERE / "native" / "relay.py"),
         "30", str(PORT), str(genome_path)],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    for _ in range(100):                     # up to 10 s for the relay to bind
        if port_open():
            break
        time.sleep(0.1)
    else:
        sys.exit("relay failed to start on :" + str(PORT))
    print(f"relay up on :{PORT} ({genome_path.name})")

webbrowser.open(f"http://127.0.0.1:{PORT}/hub")
