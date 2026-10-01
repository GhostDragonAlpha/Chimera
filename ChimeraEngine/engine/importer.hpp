// importer.hpp -- THE ALIVENESS LAW ingestion (prereg: SEAL_PREREGISTRATION,
// "THE MESH IMPORT PREREGISTRATION", fleet C1). Any mesh + skeleton comes
// alive; this unit owns only the IMPORT step: OBJ subset / glTF 2.0 ->
// the engine's full mesh format (the /mesh_bin payload), refused by name
// when the surface cannot close (the seal cuts a CLOSED body or nothing).
#pragma once

#include <cstdint>
#include <string>

namespace importer {

// Refused past these by name: the seal/cut machinery is O(tris) per cut
// and the divergence closure map is O(edges); past ~500k triangles a
// "creature" is a landscape, not a body.
constexpr uint32_t kMaxTris  = 500000u;
constexpr uint32_t kMaxVerts = 1500000u;

struct Stats {
    uint32_t verts = 0, tris = 0;
    double   volume = 0.0;        // divergence volume, outward-positive
    float    ymin = 0.f, ymax = 0.f;   // y-extent AFTER centering
    bool     winding_flipped = false;  // inward source, flipped to outward
};

// kind 'O' = OBJ subset (v/f lines, fan triangulation), 'G' = glTF 2.0
// (JSON text or GLB container; POSITION + indices, triangles only).
// On ok: body holds the full mesh format with a fit camera and slotmode 0
// (slot 0 = the cell field), st reports what came through, err stays empty.
// On refusal: ok=false, err names the cause (JSON-safe, no quotes), body
// and st are untouched. err is never empty when false.
bool import_mesh(char kind, const std::string& src,
                 std::string& body, Stats& st, std::string& err);

}  // namespace importer
