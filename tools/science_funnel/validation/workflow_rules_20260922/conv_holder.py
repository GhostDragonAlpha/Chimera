import os
import sys
import time

TARGET = r"E:\ChimeraWork\conv-janitor-test3"
os.chdir(TARGET)  # a live CWD inside the dir locks the dir itself, not its contents
with open(r"E:\ChimeraWork\_scratch\conv_holder_pid.txt", "w") as f:
    f.write(str(os.getpid()))
time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 600)
