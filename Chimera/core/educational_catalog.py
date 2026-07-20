"""educational_catalog.py — Complete catalog of all educational content.

Generates a formatted markdown catalog of every educational topic
in Deep Space Trader: Educational Frontier.
"""

import sys

EDUCATIONAL_TOPICS = [
    # === GEOLOGY (20 items) ===
    {"id": "basalt", "subject": "Geology", "title": "Basalt",
     "description": "Dark volcanic rock formed from rapid cooling of lava. Contains olivine and pyroxene crystals. Common in Titan's cryovolcanic plains.",
     "item_asset": "Basalt_Data, Basalt_Specimen", "text_actor": "EduText_Basalt",
     "source": "USGS Basalt fact sheet; Marshak (2019) Earth: Portrait of a Planet"},
    {"id": "granite", "subject": "Geology", "title": "Granite",
     "description": "Coarse-grained igneous rock formed from slow-cooling magma deep underground. Large crystals of feldspar, quartz, and mica indicate slow cooling rates.",
     "item_asset": "Granite_Data", "text_actor": "EduText_Granite",
     "source": "USGS Granite; Blatt, Tracy & Owens (2006) Petrology"},
    {"id": "obsidian", "subject": "Geology", "title": "Obsidian",
     "description": "Volcanic glass formed when lava cools so rapidly that crystals cannot form. Used by ancient civilizations for sharp tools. On Titan, similar rapid cooling occurs at cryovolcanic vents.",
     "item_asset": "Obsidian_Data", "text_actor": "EduText_Obsidian",
     "source": "USGS Obsidian; HyperPhysics, Georgia State University"},
    {"id": "pumice", "subject": "Geology", "title": "Pumice",
     "description": "Volcanic froth lighter than water. Forms when gas-rich lava cools so fast it traps bubbles. Floating pumice rafts can travel across oceans, carrying life between worlds.",
     "item_asset": "Pumice_Data", "text_actor": "EduText_Pumice",
     "source": "USGS Pumice; NASA Astrobiology Institute"},
    {"id": "sandstone", "subject": "Geology", "title": "Sandstone",
     "description": "Sedimentary rock of sand grains cemented together. Each grain records ancient wind and water. Titan's methane dunes create similar layered deposits.",
     "item_asset": "Sandstone_Data", "text_actor": "EduText_Sandstone",
     "source": "USGS Sedimentary Rocks; Lorenz (2014) Titan Unveiled"},
    {"id": "limestone", "subject": "Geology", "title": "Limestone",
     "description": "Marine sedimentary rock from ancient sea creature shells. Its presence on a world indicates a past ocean — a key clue in exoplanet habitability studies.",
     "item_asset": "Limestone_Data", "text_actor": "EduText_Limestone",
     "source": "USGS Limestone; NASA Exoplanet Habitability"},
    {"id": "shale", "subject": "Geology", "title": "Shale",
     "description": "Fine-grained sedimentary rock from compacted mud and clay. Preserves ancient organic matter. On Titan, similar deposits could hold clues to prebiotic chemistry.",
     "item_asset": "Shale_Data", "text_actor": "EduText_Shale",
     "source": "USGS Shale; NASA Titan Prebiotic Chemistry"},
    {"id": "marble", "subject": "Geology", "title": "Marble",
     "description": "Metamorphosed limestone. Heat and pressure recrystallize limestone into marble. The same process on Titan would require deep burial or volcanic heat.",
     "item_asset": "Marble_Data", "text_actor": "EduText_Marble",
     "source": "USGS Metamorphic Rocks; VERIFY: Titan geothermal gradient"},
    {"id": "quartzite", "subject": "Geology", "title": "Quartzite",
     "description": "Metamorphosed sandstone. Sandstone recrystallizes into quartzite under heat and pressure, fusing sand grains into solid quartz.",
     "item_asset": "Quartzite_Data", "text_actor": "EduText_Quartzite",
     "source": "USGS Quartzite; Blatt, Tracy & Owens (2006)"},
    {"id": "slate", "subject": "Geology", "title": "Slate",
     "description": "Metamorphosed shale. Low-grade metamorphism transforms shale into slate, splitting into thin sheets along planes of foliation.",
     "item_asset": "Slate_Data", "text_actor": "EduText_Slate",
     "source": "USGS Slate; Marshak (2019) Earth"},
    {"id": "igneous", "subject": "Geology", "title": "Igneous Collection",
     "description": "Igneous rocks form from cooling magma or lava. Crystal size reveals cooling rate: large crystals = slow cooling deep underground, small crystals = rapid cooling at the surface.",
     "item_asset": "Igneous_Data", "text_actor": "EduText_Igneous",
     "source": "USGS Igneous Rocks; Marshak (2019) Chapter 6"},
    {"id": "sedimentary", "subject": "Geology", "title": "Sedimentary Collection",
     "description": "Sedimentary rocks form from layers of sand, mud, or organic matter compressed over millions of years. They preserve fossils and ancient environments.",
     "item_asset": "Sedimentary_Data", "text_actor": "EduText_Sedimentary",
     "source": "USGS Sedimentary Rocks; Marshak (2019) Chapter 7"},
    {"id": "metamorphic", "subject": "Geology", "title": "Metamorphic Collection",
     "description": "Metamorphic rocks form when existing rocks transform under heat and pressure. The change occurs in the solid state — no melting required.",
     "item_asset": "Metamorphic_Data", "text_actor": "EduText_Metamorphic",
     "source": "USGS Metamorphic Rocks; Marshak (2019) Chapter 8"},
    {"id": "cryovolcano", "subject": "Geology", "title": "Titan Cryovolcanism",
     "description": "Titan has cryovolcanoes that erupt water and ammonia instead of molten rock. These ice volcanoes reshape the surface and release methane into the atmosphere.",
     "item_asset": "Cryovolcano_Data", "text_actor": "EduText_Cryovolcano",
     "source": "NASA Cassini Mission; Lorenz (2014) Titan Unveiled"},
    {"id": "tectonic", "subject": "Geology", "title": "Tectonic Forces",
     "description": "Titan's surface shows tectonic features — ridges, faults, and mountain belts — indicating internal geologic activity. Ice tectonics differs fundamentally from rock plate tectonics on Earth.",
     "item_asset": "Tectonic_Data", "text_actor": "EduText_Tectonic",
     "source": "NASA Cassini RADAR data; VERIFY: Titan tectonics mechanisms"},

    # === METEOROLOGY (13 items) ===
    {"id": "cirrus", "subject": "Meteorology", "title": "Cirrus Clouds",
     "description": "High-altitude ice crystals above 6km where temperatures are below -30C. Made of tiny ice crystals, they signal approaching weather changes.",
     "item_asset": "Cirrus_Data", "text_actor": "EduText_Cirrus",
     "source": "NOAA Cloud Classification; AMS Glossary of Meteorology"},
    {"id": "cumulus", "subject": "Meteorology", "title": "Cumulus Clouds",
     "description": "Fluffy fair-weather clouds from rising warm air. Flat bottoms mark the lifting condensation level — the altitude where cooling triggers condensation.",
     "item_asset": "Cumulus_Data", "text_actor": "EduText_Cumulus",
     "source": "NOAA Cumulus; AMS Cloud Atlas"},
    {"id": "stratus", "subject": "Meteorology", "title": "Stratus Clouds",
     "description": "Layer clouds blanketing the sky when moist air lifts gently over a large area. On Titan, methane stratus clouds are common in the north polar region.",
     "item_asset": "Stratus_Data", "text_actor": "EduText_Stratus",
     "source": "NOAA Stratus; NASA Cassini Titan observations"},
    {"id": "storm", "subject": "Meteorology", "title": "Storm Systems",
     "description": "Atmospheric convection at planetary scale. Storms form when warm moist air rises rapidly. Titan's methane storms can last for weeks.",
     "item_asset": "Storm_Data", "text_actor": "EduText_Storm",
     "source": "AMS Severe Storms; NASA Titan Storm observations"},
    {"id": "lightning", "subject": "Meteorology", "title": "Lightning",
     "description": "Electrical discharge from ice particle collisions in storm clouds. Titan's methane atmosphere may produce methane lightning, detectable as radio emissions.",
     "item_asset": "Lightning_Data", "text_actor": "EduText_Lightning",
     "source": "NOAA Lightning Science; NASA Cassini RPWS data"},
    {"id": "wind", "subject": "Meteorology", "title": "Wind Patterns",
     "description": "Moving air from pressure differences. On Titan, winds sculpt methane dunes and drive weather. Surface wind speeds average 3-5 m/s but can reach 20 m/s in storms.",
     "item_asset": "Wind_Data", "text_actor": "EduText_Wind",
     "source": "AMS Wind; NASA Titan wind measurements"},
    {"id": "clear_sky", "subject": "Meteorology", "title": "Clear Sky",
     "description": "Without clouds, light travels unimpeded. On Titan, clear skies are rare — the thick orange haze normally obscures Saturn and the stars from the surface.",
     "item_asset": "ClearSky_Data", "text_actor": "EduText_ClearSky",
     "source": "NASA Titan atmosphere profile"},
    {"id": "calm", "subject": "Meteorology", "title": "Atmospheric Calm",
     "description": "Calm conditions occur when pressure gradients are weak. Sound carries farther in still air. On Titan's dense atmosphere, calm moments are profound.",
     "item_asset": "Calm_Data", "text_actor": "EduText_Calm",
     "source": "AMS Atmospheric Stability; VERIFY: Titan sound speed"},

    # === ASTRONOMY (16 items) ===
    {"id": "stars", "subject": "Astronomy", "title": "Stars",
     "description": "Fusion engines converting hydrogen to helium. Energy takes thousands of years to reach the surface from the core. Every star you see is a distant sun.",
     "item_asset": "Star_Data", "text_actor": "EduText_Star",
     "source": "NASA Star Facts; IAU Stellar Classification"},
    {"id": "constellations", "subject": "Astronomy", "title": "Constellations",
     "description": "Human groupings of stars in the sky that may be vast distances apart in reality. Stories written in light across the celestial sphere.",
     "item_asset": "Constellation_Data", "text_actor": "EduText_Constellation",
     "source": "IAU Constellations; NASA Star Patterns"},
    {"id": "gravity", "subject": "Astronomy", "title": "Gravity",
     "description": "Gravity is the curvature of spacetime caused by mass. Einstein showed that massive objects bend the path of light itself — tested during the 1919 solar eclipse.",
     "item_asset": "Gravity_Data", "text_actor": "EduText_Gravity",
     "source": "NASA Gravity; Einstein (1916) General Relativity"},
    {"id": "planet_rotation", "subject": "Astronomy", "title": "Planet Rotation",
     "description": "Every planet spins. Earth: 24h. Jupiter: 10h. Venus: 243 Earth days. Rotation determines day length, weather patterns, and planetary shape through centrifugal force.",
     "item_asset": "PlanetRotation_Data", "text_actor": "EduText_Planet_Rotation",
     "source": "NASA Solar System Facts; IAU Planetary Data"},
    {"id": "light_travel", "subject": "Astronomy", "title": "Light Travel",
     "description": "Sunlight takes 8 minutes to reach Earth. Starlight takes years. Looking at the stars is looking back in time — a window into the universe's past.",
     "item_asset": "LightTravel_Data", "text_actor": "EduText_Light_Travel",
     "source": "NASA Cosmic Distance Scale; VERIFY: light-minute distances"},
    {"id": "planet_formation", "subject": "Astronomy", "title": "Planet Formation",
     "description": "Planets coalesce from spinning disks of gas and dust around new stars. Gravity sculpts worlds from chaos over millions of years.",
     "item_asset": "PlanetFormation_Data", "text_actor": "EduText_Planet_Formation",
     "source": "NASA Planet Formation; IAU Protoplanetary Disks"},
    {"id": "moon", "subject": "Astronomy", "title": "Moons",
     "description": "Natural satellites orbiting planets. Earth's moon stabilizes our axis. Titan orbits Saturn — a world with its own weather, seasons, and methane cycle.",
     "item_asset": "Moon_Data", "text_actor": "EduText_Moon",
     "source": "NASA Moon Facts; IAU Solar System Data"},
    {"id": "saturn", "subject": "Astronomy", "title": "Saturn",
     "description": "The ringed giant, second-largest planet, density less than water. Rings of ice and rock particles. 146 known moons. Titan orbits at 1.2 million km.",
     "item_asset": "Saturn_Data", "text_actor": "EduText_Saturn",
     "source": "NASA Saturn; Cassini Mission Results"},
    {"id": "titan", "subject": "Astronomy", "title": "Titan",
     "description": "Saturn's largest moon with thick atmosphere, methane rain, and liquid hydrocarbon lakes. One of the most Earth-like worlds in the solar system.",
     "item_asset": "Titan_Data", "text_actor": "EduText_Titan",
     "source": "NASA Titan; Lorenz (2014) Titan Unveiled"},
    {"id": "saturn_rings", "subject": "Astronomy", "title": "Saturn's Rings",
     "description": "Billions of ice and rock particles ranging from dust to house-sized boulders. Only 10 meters thick but spanning 282,000 km. Possibly remains of a shattered moon.",
     "item_asset": "SaturnRing_Data", "text_actor": "EduText_SaturnRings",
     "source": "NASA Saturn Rings; Cassini Grand Finale data"},
    {"id": "tidal_locking", "subject": "Astronomy", "title": "Tidal Locking",
     "description": "Titan always shows the same face to Saturn. Tidal locking is common among large moons — gravity gradually synchronizes rotation with orbital period.",
     "item_asset": "TidalLock_Data", "text_actor": "EduText_TidalLock",
     "source": "NASA Tidal Locking; IAU Orbital Mechanics"},
    {"id": "exoplanets", "subject": "Astronomy", "title": "Exoplanets",
     "description": "Thousands of worlds discovered since 1995. Some orbit in the habitable zone — the region where liquid water could exist on the surface.",
     "item_asset": "Exoplanet_Data", "text_actor": "EduText_Exoplanet",
     "source": "NASA Exoplanet Archive; Kepler Mission results"},
    {"id": "milky_way", "subject": "Astronomy", "title": "Milky Way",
     "description": "Our home galaxy: 100-400 billion stars, 100,000 light-years across. From Earth, visible as a band of light across the night sky.",
     "item_asset": "MilkyWay_Data", "text_actor": "EduText_MilkyWay",
     "source": "NASA Milky Way; IAU Galaxy Classification"},
    {"id": "titan_atmosphere", "subject": "Meteorology", "title": "Titan Atmosphere",
     "description": "Titan has the thickest atmosphere of any moon - 1.5x Earth pressure. Its orange haze comes from tholins, organic molecules formed when sunlight breaks methane and nitrogen.",
     "item_asset": "AtmosHaze_Data", "text_actor": "EduText_Atmosphere",
     "source": "NASA Cassini Mission; Lorenz (2014) Titan Unveiled"},
    {"id": "methane_lakes", "subject": "Meteorology", "title": "Methane Lakes",
     "description": "Titan's north polar region has liquid methane lakes - the only stable surface liquid outside Earth. They evaporate and refill with seasonal methane rains.",
     "item_asset": "MethaneLake_Data", "text_actor": "EduText_MethaneLake",
     "source": "NASA Cassini RADAR; Stofan et al. (2007) Nature"},
    {"id": "saturn_rings", "subject": "Astronomy", "title": "Saturn's Rings",
     "description": "Saturn's rings contain billions of ice and rock particles. Only 10 meters thick but spanning 282,000 km. They may be the remains of a shattered moon.",
     "item_asset": "SaturnRing_Data", "text_actor": "EduText_SaturnRings",
     "source": "NASA Cassini Grand Finale; IAU Planetary Rings"},
    {"id": "tidal_locking", "subject": "Astronomy", "title": "Tidal Locking",
     "description": "Titan is tidally locked to Saturn - the same face always points toward the planet. Tidal locking is common among large moons in the solar system.",
     "item_asset": "TidalLock_Data", "text_actor": "EduText_TidalLock",
     "source": "NASA Tidal Locking; IAU Orbital Mechanics"},
    {"id": "titan_cryo", "subject": "Geology", "title": "Cryovolcanism",
     "description": "Titan has cryovolcanoes that erupt water and ammonia instead of molten rock. These ice volcanoes reshape the surface and release methane into the atmosphere.",
     "item_asset": "Cryovolcano_Data", "text_actor": "EduText_Cryovolcano",
     "source": "NASA Cassini VIMS; Lorenz (2014) Titan Unveiled"},
]


def count_by_subject():
    """Return count of topics per subject."""
    counts = {}
    for topic in EDUCATIONAL_TOPICS:
        s = topic["subject"]
        counts[s] = counts.get(s, 0) + 1
    return counts


def generate_catalog():
    """Print a formatted markdown catalog of all educational content."""
    subjects = ["Geology", "Meteorology", "Astronomy"]
    counts = count_by_subject()

    print("# Deep Space Trader: Educational Content Catalog")
    print(f"\nTotal topics: {len(EDUCATIONAL_TOPICS)}")
    for s in subjects:
        print(f"- {s}: {counts.get(s, 0)}")
    print()

    for subject in subjects:
        print(f"---")
        print(f"## {subject} ({counts.get(subject, 0)} topics)")
        print()
        for topic in EDUCATIONAL_TOPICS:
            if topic["subject"] != subject:
                continue
            print(f"### {topic['title']}")
            print(f"**ID:** `{topic['id']}`")
            print(f"**Asset:** `{topic['item_asset']}`")
            print(f"**Text Actor:** `{topic['text_actor']}`")
            print(f"**Description:** {topic['description']}")
            print(f"**Source:** {topic['source']}")
            print()


def catalog_to_json():
    """Return the catalog as a JSON-serializable dict."""
    return {
        "total": len(EDUCATIONAL_TOPICS),
        "counts": count_by_subject(),
        "topics": EDUCATIONAL_TOPICS,
    }


if __name__ == "__main__":
    import json
    if "--json" in sys.argv:
        print(json.dumps(catalog_to_json(), indent=2))
    else:
        generate_catalog()
