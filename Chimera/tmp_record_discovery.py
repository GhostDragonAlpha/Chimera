import sys
sys.path.insert(0, r'E:\PythonChimera\Chimera\core')
from graphify_interface import graphify_mutate

# Record research discovery for Apollo 17 LRV audio
result = graphify_mutate("research_discovery", details={
    "source": "Apollo 17 Lunar Rover Audio Clips (Apollo Journals / NASA Johnson Space Center)",
    "campus": "engineering_school",
    "quality_rating": "A+",
    "principles": [
        "Lunar surface travel audio transmitted through suit bone conduction",
        "No airborne sound on lunar surface (vacuum propagation)",
        "Rover wheel/regolith impact sounds transmitted via suit structure",
        "Helmet audio environment: low-pass filtered, 40-60 dB SPL voice comms",
        "Radio interference (VHF whistling) accidentally heard by Apollo 10 crew"
    ]
})
print(f"Research discovery recorded: {result}")
