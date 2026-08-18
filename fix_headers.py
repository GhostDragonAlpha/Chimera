# fix engine.hpp — add cmd_pool_ (required but missing)
path_hpp = r"e:\PythonChimera\ChimeraEngine\engine\engine.hpp"
with open(path_hpp, "r") as f:
    hpp = f.read()
if "cmd_pool_" not in hpp:
    hpp = hpp.replace(
        "std::vector<VkFence>         fences_;",
        "std::vector<VkFence>         fences_;\n    VkCommandPool              cmd_pool_= VK_NULL_HANDLE;"
    )
    with open(path_hpp, "w") as f:
        f.write(hpp)
    print("engine.hpp: added cmd_pool_")
else:
    print("engine.hpp: cmd_pool_ already present")
