"""Pinned reference sources -- the registry of record for deterministic imports.

Every entry records: the pinned entry URL, the release/version it resolved to
(observed 2026-09-15), the license EVIDENCE (a fetched artifact + its own
checksum, not a claim from memory), and the cache path. First-fetch checksums
are frozen in data/pins.json by fetch_cache.verify_or_pin(); later imports
REFUSE to run against drift (pin semantics), so re-imports are bit-stable.

No LLM rows anywhere: these are structured files parsed by deterministic
parsers (parsers.py). Importing a model file NEVER executes it (the .osim is
parsed as XML only).
"""

SOURCES = {
    "uberon.appendicular-minimal": {
        "family": "anatomy ontology subset (appendicular skeleton: limbs)",
        "entry_url": "http://purl.obolibrary.org/obo/uberon/appendicular-minimal.obo",
        "resolved_url": "https://github.com/obophenotype/uberon/releases/download/"
                        "v2026-06-23/appendicular-minimal.obo",
        "release": "uberon v2026-06-23 (resolved via purl 302 chain, 2026-09-15)",
        "release_page": "https://obophenotype.github.io/uberon/current_release/",
        "license": "CC BY 3.0",
        "license_evidence": {
            "artifact": "obo_registry/uberon.md",
            "source": "https://raw.githubusercontent.com/OBOFoundry/"
                      "OBOFoundry.github.io/master/ontology/uberon.md",
            "statement": "license: label 'CC BY 3.0' "
                         "(http://creativecommons.org/licenses/by/3.0/)",
        },
        "cache": "uberon/appendicular-minimal.obo",
        "parser": "obo",
        "coverage": "the appendicular-minimal module (1,227 [Term] stanzas): limb "
                    "skeleton concepts (femur, tibia/fibula, pes, autopod...) with "
                    "is_a/part_of relations -- the musculoskeletal subset relevant "
                    "to the selected limb",
        "known_gaps": "full Uberon (~700 MB uberon.owl) NOT imported; axial skeleton "
                      "and organs deferred; no developmental/axiom-heavy subsets",
    },
    "ro.base": {
        "family": "relation ontology (relation types + meanings)",
        "entry_url": "https://raw.githubusercontent.com/oborel/obo-relations/"
                     "v2026-09-04/ro-base.owl",
        "resolved_url": "https://raw.githubusercontent.com/oborel/obo-relations/"
                        "v2026-09-04/ro-base.owl",
        "release": "obo-relations v2026-09-04 (latest release tag, published "
                   "2026-09-07, observed 2026-09-15)",
        "release_page": "https://obofoundry.org/ontology/ro.html",
        "license": "CC0 1.0",
        "license_evidence": {
            "artifact": "obo_registry/ro.md",
            "source": "https://raw.githubusercontent.com/OBOFoundry/"
                      "OBOFoundry.github.io/master/ontology/ro.md",
            "statement": "license: label 'CC0 1.0' "
                         "(http://creativecommons.org/publicdomain/zero/1.0/)",
        },
        "cache": "ro/ro-base.owl",
        "parser": "ro_owl",
        "coverage": "ro-base.owl (876 KB): the relation TYPES referenced by the "
                    "Uberon subset (part_of, has_part, connected/continuous...) "
                    "with labels + definitions",
        "known_gaps": "ro-full.owl (with domain/range axioms over all of OBO) NOT "
                      "imported; only the selected relation IRIs are projected",
    },
    "qudt.units": {
        "family": "units + quantity kinds (QUDT)",
        "entry_url": "https://qudt.org/vocab/unit/{UNIT}",
        "resolved_url": "https://qudt.org/vocab/unit/{UNIT} (Turtle via "
                        "Accept: text/turtle)",
        "release": "QUDT live LOD endpoint, served 2026-09-15; NOT a release-pinned "
                   "artifact -- pinned instead by per-file sha256 in data/pins.json "
                   "(drift fails the import loudly)",
        "release_page": "https://qudt.org/",
        "license": "not stated in the served unit documents -- recorded UNKNOWN "
                   "(QUDT site terms govern; qudt-public-repo not fetched this run)",
        "license_evidence": {
            "artifact": None,
            "source": None,
            "statement": "absence recorded honestly (missing metadata stays unknown)",
        },
        "cache": "qudt/unit_{UNIT}.ttl / qudt/quantitykind_{KIND}.ttl",
        "parser": "qudt_ttl",
        "units": ["PA", "PER-PA", "M3", "M2", "M", "SEC", "MIN", "HR", "KiloGM",
                  "N", "N-M", "N-PER-M", "J", "W", "K", "RAD", "RAD-PER-SEC",
                  "M-PER-SEC", "KiloGM-PER-M3", "PA-SEC-PER-M3"],
        "quantity_kinds": ["Pressure", "Volume", "Length", "Mass", "Time", "Force",
                           "Dimensionless", "Velocity", "Density"],
        "coverage": "the units the creature's physical laws actually use "
                    "(Pa, Pa^-1, m^3, N/m, N*m, kg, s, hydraulic resistance "
                    "Pa*s/m^3...) + 9 quantity kinds",
        "known_gaps": "full QUDT vocabularies (all units/prefixes/currencies) NOT "
                      "imported; no unit-conversion graph beyond SI multipliers",
    },
    "opensim.leg6dof9musc": {
        "family": "musculoskeletal reference model (ONE limb)",
        "entry_url": "https://github.com/opensim-org/opensim-models",
        "resolved_url": "https://raw.githubusercontent.com/opensim-org/opensim-models/"
                        "master/Models/Leg6Dof9Musc/leg6dof9musc.osim",
        "release": "opensim-models master as of 2026-09-15 (repo default branch "
                   "'master', last push 2025-11-05; commit-level pin via sha256)",
        "release_page": "https://github.com/opensim-org/opensim-models",
        "license": "NOT STATED in the repo (no LICENSE file at repo root, checked "
                   "2026-09-15 via the GitHub contents API) -- recorded UNKNOWN; "
                   "treated as reference-only",
        "license_evidence": {
            "artifact": None,
            "source": "https://api.github.com/repos/opensim-org/opensim-models/"
                      "contents/ (no LICENSE entry)",
            "statement": "absence recorded honestly (missing metadata stays unknown)",
        },
        "cache": "osim/leg6dof9musc.osim",
        "parser": "osim_xml",
        "coverage": "the human RIGHT leg: bodies pelvis/femur_r/tibia_r/patella_r/"
                    "talus_r/calcn_r/toes_r; joints ground_pelvis, hip_r, knee_r, "
                    "tib_pat_r, ankle_r (CustomJoint) + subtalar_r, mtp_r (WeldJoint); "
                    "9 Thelen2003Muscle units with max isometric force, optimal "
                    "fiber length, tendon slack length, pennation",
        "known_gaps": "human proportions are REFERENCE, not Chimera proportions; "
                      "model is one side (right); tendon wrapping paths simplified; "
                      "NO license terms -- selection/adaptation is a human decision",
        "safety": "parsed as XML ONLY (xml.etree; never executed, no macros)",
    },
    "bodyparts3d": {
        "family": "anatomy geometry (DEFERRED -- registered, not imported)",
        "entry_url": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html",
        "resolved_url": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html",
        "release": "archive layout observed 2026-09-15 (FMA-based tables + mesh "
                   "zips; no release versioning on the archive)",
        "release_page": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html",
        "license": "CC Attribution 4.0 International",
        "license_evidence": {
            "artifact": "bp3d/lic.html",
            "source": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html",
            "statement": "\"The license for this database is specified in the "
                         "Creative Commons Attribution 4.0 International\"; "
                         "attribution: \"BodyParts3D, (c) The Database Center for "
                         "Life Science licensed under CC Attribution 4.0 "
                         "International\"",
        },
        "cache": "bp3d/lic.html + bp3d/download.html",
        "parser": None,
        "coverage": "NONE imported this run -- registration + license only",
        "known_gaps": "bulk mesh/table zips NOT imported: geometry is only useful "
                      "once the leg partition needs conforming caps; HUMAN "
                      "proportions are NOT Chimera proportions (the sealed-"
                      "compartment design remains a Chimera requirement)",
    },
}
