import json
import urllib.request

url = "http://localhost:1234/v1/chat/completions"

body = {
    "model": "qwen3.6-35b-a3b-mtp@iq2_m",
    "messages": [
        {
            "role": "system",
            "content": "You are the Professor for the Chimera Project's Ralph Loop. Your task is to review research summaries for features and assign a grade (A, B, C, or F) based on the quality, completeness, and fidelity to references and parameters. Provide the grade letter, a score (0-100), and the reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        },
        {
            "role": "user",
            "content": "RESEARCH SUMMARY FOR LOOP 4 TOOL_SHOVEL_MODEL (GEOMETRY):\n\nCampus Sources Queried:\nFrom RESEARCH_CAMPUSES.md:\nCampus 5: Engineering School - Seed sources include NASA Technical Reports, Industrial Design Principles (Form Follows Function), Spacecraft Design Constraints and Requirements, and Engineering Form and Function Case Studies. Quality ratings: A+ for official NASA documentation and engineering textbooks.\nCampus 2: Art School - Focus on form/mass, composition, and material rendering. Seed sources include Form and Silhouette Design Principles and PBR Materials Explained by Artists.\nCampus 4: Architecture School - Focus on spatial design and materiality.\n\nWeb Research via Playwright (Port 8342):\nI conducted image and documentation searches using Playwright for:\n\"Apollo lunar sample scoop\"\n\"lunar sample scoop site:nasa.gov OR site:lunarpedia.org\"\n\"NASA lunar sample scoop specifications OR 'lunar sample tool'\"\nThese searches confirmed the existence and design of the Apollo Lunar Sample Tool (also known as the lunar soil sampler or trowel-scoop combination), which was used by astronauts during the Apollo missions to collect lunar regolith. The project already contains a reference mesh: SM_ApolloLunarScoop.obj.\n\nExtracted Parameters for Tool_Shovel_Model (geometry):\nGeometry Dimensions: L-shaped or T-shaped handle with a scoop/bucket head at the end. Handle length ~30–40 cm to allow reach while standing in a spacesuit; scoop width ~10–15 cm; scoop depth ~5–8 cm.\nProportions: Ergonomic grip section designed for use with bulky Apollo spacesuit gloves; wide scoop mouth for regolith collection; reinforced cutting edge for breaking compacted lunar soil.\nScale: 1:1 scale relative to astronaut height (Apollo suit height ~1.7m with helmet). Handle length ~0.35m, scoop width ~0.12m.\nMaterial Properties (for geometry context): Aluminum or anodized aluminum alloy for the handle and scoop body (lightweight, non-magnetic to avoid interfering with scientific instruments); stainless steel or coated metal for the cutting edge of the trowel/scoop.\n\nCanonical Reference Locked:\nApollo Lunar Sample Tool (Lunar Soil Sampler / Trowel-Scoop combination) as documented in NASA's Apollo Lunar Surface Journal and NTRS reports. The specific mesh reference already present in the project is SM_ApolloLunarScoop.obj.\n\nNew Source Discovered (Campus +1):\nFrom the Engineering School Campus, I identified the NASA Technical Reports Server (NTRS) documentation on \"Apollo Lunar Sampling Tools\" and the Apollo Lunar Surface Journal tool descriptions as A+ quality engineering and industrial design references. These sources provide form-follows-function specifications for space tools designed specifically for use with pressurized spacesuit gloves, detailing the ergonomic proportions, material constraints (non-magnetic, lightweight aluminum alloys), and functional geometry of the lunar sample scoop and trowel.\n\nPlease review this research summary and assign a grade (A, B, C, or F), a score (0-100), and provide the exact reasoning sentence. Format your response as: Grade: [Letter], Score: [Score], Reasoning: [reasoning sentence]. Full verbatim response will be used for recording."
        }
    ],
    "temperature": 0.1,
    "max_tokens": 500
}

req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers={'Content-Type': 'application/json'})
response = urllib.request.urlopen(req)
response_data = response.read().decode('utf-8')
print(response_data)
