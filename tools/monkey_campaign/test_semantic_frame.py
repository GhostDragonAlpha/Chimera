import copy
import unittest

import semantic_frame as s


def packet():
    h = "a" * 64
    return {
        "schema": s.SCHEMA,
        "subject_id": "right_hand",
        "subject_kind": "anatomical_membrane",
        "source_head": "b" * 40,
        "coordinate_unit": "m",
        "frame": {"frame_id": "right_hand_birth", "parent_frame_id": "right_radius",
                  "handedness": "right", "origin": [0, 0, 0],
                  "basis": {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}},
        "semantic_directions": {
            "distal": [1, 0, 0], "proximal": [-1, 0, 0],
            "dorsal": [0, 1, 0], "palm": [0, -1, 0],
            "lateral": [0, 0, 1], "medial": [0, 0, -1],
        },
        "required_knowledge_domains": ["biology", "physics"],
        "knowledge_claims": [
            {"id": "build", "domain": "authored_semantics",
             "authority": "operator_authored_semantics", "source_ref": "mesh recipe",
             "artifact_sha256": h, "statement": "landmarks construct the birth frame"},
            {"id": "bio", "domain": "biology", "authority": "authoritative_database",
             "source_ref": "anatomy record: right manus", "artifact_sha256": h,
             "statement": "wrist, palm, digits and sidedness"},
            {"id": "physics", "domain": "physics", "authority": "derived_physics",
             "source_ref": "finite-difference flexion witness", "artifact_sha256": h,
             "statement": "positive flexion advances digit samples toward palm half-space"},
        ],
        "construction_claim_ids": ["build"],
        "validation_claim_ids": ["bio", "physics"],
        "required_landmark_roles": ["joint_center", "surface", "digit_tip"],
        "landmarks": [
            {"id": "wrist", "position": [0, 0, 0], "role": "joint_center", "claim_id": "bio"},
            {"id": "digit3", "position": [0.12, 0, 0], "role": "digit_tip", "claim_id": "bio"},
            {"id": "dorsum", "position": [0.04, 0.02, 0], "role": "surface", "claim_id": "bio"},
            {"id": "palm_surface", "position": [0.04, -0.02, 0], "role": "surface", "claim_id": "bio"},
            {"id": "radial", "position": [0.04, 0, 0.03], "role": "surface", "claim_id": "bio"},
        ],
        "direction_witnesses": [
            {"semantic": "distal", "positive_landmark": "digit3", "negative_landmark": "wrist",
             "claim_id": "bio", "min_separation": 0.1},
            {"semantic": "dorsal", "positive_landmark": "dorsum", "negative_landmark": "palm_surface",
             "claim_id": "bio", "min_separation": 0.03},
            {"semantic": "lateral", "positive_landmark": "radial", "negative_landmark": "wrist",
             "claim_id": "bio", "min_separation": 0.02},
        ],
        "geometry_coverage": {
            "required_elements": ["wrist", "palm", "digit_1", "digit_2", "digit_3", "digit_4", "digit_5"],
            "element_bindings": {"wrist": "mesh:wrist", "palm": "mesh:palm",
                                 "digit_1": "mesh:d1", "digit_2": "mesh:d2", "digit_3": "mesh:d3",
                                 "digit_4": "mesh:d4", "digit_5": "mesh:d5"}},
        "ports": [{"id": "palm_contact", "position": [0.04, -0.02, 0],
                   "normal": [0, -1, 0], "outward_semantic": "palm"}],
        "kinematic_witness": {
            "semantic": "palm", "claim_id": "physics", "reference_origin": [0, 0, 0],
            "rest_points": [[0.1, 0.04, -0.02], [0.1, 0.05, 0.02]],
            "moved_points": [[0.1, 0.01, -0.02], [0.1, 0.01, 0.02]],
            "minimum_signed_progress": 0.02,
        },
    }


class SemanticFrameTests(unittest.TestCase):
    def assert_error(self, value, outcome, code):
        with self.assertRaises(s.SemanticFrameError) as caught:
            s.validate_semantic_frame(value)
        self.assertEqual((caught.exception.outcome, caught.exception.code), (outcome, code))

    def test_complete_hand_frame_passes_without_visual_inference(self):
        value = packet()
        before = copy.deepcopy(value)
        result = s.validate_semantic_frame(value)
        self.assertEqual(value, before)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["machine_qualified"])
        self.assertFalse(result["visual_acceptance"])
        self.assertEqual(result["debug_views"][:6], ["+x", "-x", "+y", "-y", "+z", "-z"])

    def test_palm_sign_swap_fails_physical_flexion_witness(self):
        value = packet()
        value["semantic_directions"]["palm"] = [0, 1, 0]
        value["semantic_directions"]["dorsal"] = [0, -1, 0]
        value["direction_witnesses"][1].update(
            positive_landmark="palm_surface", negative_landmark="dorsum", semantic="dorsal")
        value["ports"][0]["normal"] = [0, 1, 0]
        self.assert_error(value, "FAIL", "kinematic_witness_semantic_contradiction")

    def test_smooth_paddle_without_digits_refuses_instead_of_guessing(self):
        value = packet()
        value["geometry_coverage"]["element_bindings"] = {
            "wrist": "mesh:wrist", "palm": "mesh:paddle"}
        self.assert_error(value, "REFUSED", "semantic_geometry_coverage_missing")

    def test_circular_construction_and_validation_claim_refuses(self):
        value = packet()
        value["validation_claim_ids"].append("build")
        self.assert_error(value, "REFUSED", "circular_validation_claim")

    def test_missing_physics_or_biology_authority_refuses(self):
        value = packet()
        value["knowledge_claims"] = [row for row in value["knowledge_claims"] if row["domain"] != "physics"]
        value["validation_claim_ids"] = ["bio"]
        value["kinematic_witness"]["claim_id"] = "bio"
        self.assert_error(value, "REFUSED", "required_knowledge_domain_missing")

    def test_mirrored_or_skewed_coordinate_frame_fails(self):
        value = packet()
        value["frame"]["basis"]["z"] = [0, 0, -1]
        self.assert_error(value, "FAIL", "frame_basis_not_proper")
        value = packet()
        value["frame"]["basis"]["y"] = [0.2, 1, 0]
        self.assert_error(value, "FAIL", "direction_not_unit")

    def test_collinear_landmarks_refuse(self):
        value = packet()
        for index, row in enumerate(value["landmarks"]):
            row["position"] = [index * 0.01, 0, 0]
        self.assert_error(value, "REFUSED", "landmarks_collinear")

    def test_port_normal_must_match_semantic_direction(self):
        value = packet()
        value["ports"][0]["normal"] = [0, 1, 0]
        self.assert_error(value, "FAIL", "semantic_port_normal_contradiction")

    def test_required_landmark_role_cannot_be_silently_omitted(self):
        value = packet()
        value["required_landmark_roles"].append("tendon_attachment")
        self.assert_error(value, "REFUSED", "required_landmark_role_missing")

    def test_every_base_semantic_axis_needs_independent_witness(self):
        value = packet()
        value["direction_witnesses"] = value["direction_witnesses"][:2]
        self.assert_error(value, "REFUSED", "semantic_direction_unwitnessed")


if __name__ == "__main__":
    unittest.main()
