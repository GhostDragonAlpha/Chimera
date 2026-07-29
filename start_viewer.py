import subprocess
import time
import os

os.chdir(r'E:\PythonChimera')
print("Starting Chimera Engine viewer on port 8765...")
proc = subprocess.Popen(['python', 'ChimeraEngine/gallery.py', '8765'])
time.sleep(3)
print(f"Server started with PID {proc.pid}")
