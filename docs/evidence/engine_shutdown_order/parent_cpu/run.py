"""Compile exact production helper text; preserve candidates and mutant runs."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
source = ROOT / "ChimeraEngine" / "engine" / "main.cpp"
text = source.read_text(encoding="utf-8")
block = text[text.index("struct ShutdownCancellation {};"):text.index("#ifdef _WIN32\nBOOL WINAPI handleCtrlC")]
assert text.count("wait_for_shutdown(g_") == 27
assert all("notify_shutdown(g_" + n + "_mutex, g_" + n + "_cv)" in block
           for n in ("mem", "md", "mesh", "hinge", "water", "gait", "volp", "frost", "skin"))
assert "notify_shutdown(boot_restore_mutex, boot_restore_cv);" in text
assert not any("g_" + n + "_cv.wait_for" in text
               for n in ("mem", "md", "mesh", "hinge", "water", "gait", "volp", "frost", "skin"))
variants = {
    "candidate": block,
    "ignore_cancel": block.replace("predicate() || g_shutdown_closing.load(std::memory_order_acquire)", "predicate()"),
    "false_success": block.replace("throw ShutdownCancellation{};", "return true;"),
    "unlocked_notify": block.replace("std::lock_guard<Mutex> lock(mutex);", "// mutant omits notification lock"),
}
assert all(b != block for n, b in variants.items() if n != "candidate")
out = HERE / "run_01"
out.mkdir(exist_ok=False)
build = ROOT / ".tmp" / "shutdown_parent_cpu_01"
build.mkdir(exist_ok=False)
results = []
compiler = "C:/ProgramData/mingw64/mingw64/bin/g++.exe"
for name, code in variants.items():
    lane = build / name
    lane.mkdir()
    (lane / "production_helpers.hpp").write_text(code, encoding="utf-8")
    (out / (name + ".hpp")).write_text(code, encoding="utf-8")
    exe = lane / "harness.exe"
    command = [compiler, "-std=c++17", "-O2", "-static", "-pthread", "-DCHIMERA_SHUTDOWN_TEST", "-I" + str(lane), str(HERE / "harness.cpp"), "-o", str(exe)]
    cp = subprocess.run(command, capture_output=True)
    (out / (name + ".build.log")).write_bytes(cp.stdout + cp.stderr)
    if cp.returncode:
        results.append(dict(name=name, build_exit=cp.returncode, command=command))
        continue
    proc = subprocess.Popen([str(exe)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    watchdog = False
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        watchdog = True
        proc.kill()  # exact process handle created above; no other process touched
        stdout, stderr = proc.communicate()
    (out / (name + ".stdout.log")).write_bytes(stdout)
    (out / (name + ".stderr.log")).write_bytes(stderr)
    results.append(dict(name=name, build_exit=0, exit=proc.returncode, watchdog=watchdog,
                        source_sha256=hashlib.sha256(code.encode()).hexdigest(), command=command))
(out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
(out / "main_sha256.txt").write_text(hashlib.sha256(source.read_bytes()).hexdigest())
print(json.dumps(results, indent=2))
assert all(r["build_exit"] == 0 for r in results), "Build error is not mutation detection"
assert results[0]["exit"] == 0 and not results[0]["watchdog"]
assert all(r["exit"] != 0 or r["watchdog"] for r in results[1:]), "mutant survived"
print("PASS: actual source helper and three rejected mutants; runtime order/API gates remain separate")
