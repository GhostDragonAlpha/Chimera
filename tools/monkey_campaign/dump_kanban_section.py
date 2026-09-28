"""Print kanban.py lines 76-245 to recover the worker-facing functions."""
path = r"E:\PythonChimera\tools\monkey_campaign\kanban.py"
with open(path, encoding="utf-8") as f:
    lines = f.readlines()
print("".join(lines[75:245]))
