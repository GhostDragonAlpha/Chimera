"""Generate educational content catalog from env_education.py."""
import sys, types
sys.path.insert(0, "core")

# Mock the relative imports
sys.modules["cloud_education"] = types.ModuleType("cloud_education")
sys.modules["cloud_weather"] = types.ModuleType("cloud_weather")

# Read and execute env_education
with open("core/env_education.py", "r") as f:
    source = f.read()
source = source.replace("from . import cloud_education\n", "")
source = source.replace("from . import cloud_weather\n", "")

# Execute in a namespace
ns = {}
exec(source, ns)

# Extract prompt dictionaries
GEOLOGY = ns["GEOLOGY_PROMPTS"]
WEATHER = ns["WEATHER_PROMPTS"] 
ASTRONOMY = ns["ASTRONOMY_PROMPTS"]
CONSTELLATIONS = ns["ASTRONOMY_CONSTELLATIONS"]
TIME = ns["TIME_PROMPTS"]

# Generate catalog
lines = ["# Deep Space Trader — Educational Content Catalog", ""]

lines.append("## Geology")
for rock, prompts in sorted(GEOLOGY.items()):
    lines.append(f"\n### {rock.replace('_', ' ').title()}")
    for p in prompts:
        lines.append(f"- {p}")

lines.append("\n## Meteorology")
for weather, prompts in sorted(WEATHER.items()):
    lines.append(f"\n### {weather.title()}")
    for p in prompts:
        lines.append(f"- {p}")

lines.append("\n## Astronomy")
for feature, prompts in sorted(ASTRONOMY.items()):
    lines.append(f"\n### {feature.title()}")
    for p in prompts:
        lines.append(f"- {p}")

lines.append("\n## Constellations")
for name, desc in sorted(CONSTELLATIONS.items()):
    lines.append(f"\n### {name.replace('_', ' ').title()}")
    lines.append(f"- {desc}")

lines.append("\n## Time of Day")
for time, desc in sorted(TIME.items()):
    lines.append(f"\n### {time.title()}")
    lines.append(f"- {desc}")

geo = sum(len(v) for v in GEOLOGY.values())
wea = sum(len(v) for v in WEATHER.values())
ast = sum(len(v) for v in ASTRONOMY.values())
lines.append(f"\n---\nTotal: {geo} geology + {wea} weather + {ast} astronomy = {geo + wea + ast} educational prompts")

open("../docs/EDUCATIONAL_CONTENT.md", "w").write("\n".join(lines))
print(f"Catalog generated: {geo + wea + ast} prompts")
