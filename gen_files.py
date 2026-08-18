import os

ENGINE_PATH = r"e:\PythonChimera\ChimeraEngine\engine\engine.cpp"
SHIM_PATH   = r"e:\PythonChimera\ChimeraShim\__init__.py"


lines.append("""// engine.cpp — Vulkan engine implementation matching engine.hpp""")
lines.append("""#include "engine.hpp" """)
lines.append("""#include <iostream> """)
lines.append("""#include <fstream> """)
lines.append("""#include <cstring> """)
lines.append("""#include <algorithm> """)
lines.append("""#include <vector> """)
lines.append("""#include <string> """)
lines.append("")
lines.append("static std::vector<char> read_spirv(const char* path) {")
lines.append("    std::ifstream f(path, std::ios::binary);")
lines.append("    if (!f) return {};")
lines.append("    return std::vector<char>(std::istreambuf_iterator<char>(f), {});")
lines.append("}")
lines.append("")

