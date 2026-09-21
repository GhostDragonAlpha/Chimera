"""THE CLASS RECORDS APPLY SCRIPT (lane agent/joint-class-records-20260921).

Applies the joint_class records -- the matter-law amendment named by the
tarsal_cycle_pivots_20260921 receipt ("the class-gap amendment is the named
successor work") -- to all 23 committed bonds of
tools/science_funnel/data/morphosource_ct/matter_skeleton/infant_skeleton.body.json.

THE AMENDMENT DISCIPLINE (law doc sections 1.1 and 3):
  - The joint_class records are metadata WITH TEETH: the class's dof_count
    binds what poses may vary; the geometry never binds a DOF by itself.
  - Extra keys ride as inert metadata in validate_bond's accepted schema --
    the same convention that already carries refined_gap_mm,
    closest_points_mm and anatomical_reading on the committed hip bonds.
  - The amendment is SURGICAL: every bond object gains exactly one new last
    key ("joint_class"); every other byte of the definition is preserved.
    The membranes, the tris refs, the vertex books, the measured gaps, the
    cure constants, the evidence strings and both hips' anatomical_reading
    are byte-identical before and after; theta = 0 stays the committed
    bytes (the P6 law's A1 -- the class records carry no transform).

Run:  python -B apply_class_records.py --apply     (after the preregistration is banked)
      python -B apply_class_records.py --table     (markdown table for the preregistration)
"""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFN = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton" / "infant_skeleton.body.json"

TAXONOMY = ("ball_and_socket", "hinge_revolute", "condyled_gliding",
            "syndesmosis_nodof", "positional_contact")

# ---- the cited held records (sha-pinned; the battery re-parses and re-checks every one) ----
SRC_R = "Rajagopal2016.osim (sha256 4ed1b573715b5747a203f6ea1dfdbbc6480ce8f24cf70fb00447591b1f599a1e)"
SRC_G = "gait2392_thelen2003muscle.osim (sha256 18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019)"
SRC_M = "monkeyArm_current.osim (sha256 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895; limblab/monkeyArmModel @ 4fb7ddde, MIT)"

HINGE_PIVOT_NOTE = ("PRESCRIBED FORM, AXIS DERIVATION OPEN: the engine's 8-float hinge record "
                    "(pivot J, axis A, theta_rad; the gait engine's hinge columns, law doc section 1.3a) "
                    "is the wire form; no axis derivation is registered for this bond yet - the first pose "
                    "through it pre-registers the axis derivation with zero free numbers and inherits the "
                    "law doc A1-A5 falsifiers")

TARSAL_RANGE_SOURCE = ("Rajagopal2016.osim subtalar_l/r subtalar_angle [-0.34906585, 0.34906585] rad "
                       "(parsed from the sha-pinned committed record; symmetric both sides) - the "
                       "tarsal-class cited band and the registered band of tarsal_cycle_pivots_20260921; "
                       "same-model adjacent records: ankle_l/r [-0.6981317, 0.52359878], "
                       "mtp_l/r [-0.52359878, 0.52359878]; gait2392 wide bands (+/-1.57079633) context "
                       "only; adult-human band, species and stage deviation named, never tuned")

TARSAL_PIVOT_MEASURED = ("the measured evidence recorded beside it, never as prescription: the transplanted "
                         "sphere-form fits of tarsal_cycle_pivots_20260921 converge on this bond, seat through "
                         "the registered band, and DISCRIMINATE real from null (the receipt's class verdict; "
                         "the prescription gap that receipt named is filled here by the cited PinJoint form)")

TEETH = "THE CLASS RECORD BINDS THE DOFS, not the geometry"


def hip(side, band_ref, radius, rms):
    return {
        "class": "ball_and_socket",
        "reading": "hip joint (%s): femoral head apposed to the acetabular region of the composite pelvis "
                   "mass (Hartman & Straus 1933) - the bond's anatomical_reading promoted verbatim to the "
                   "class record by lane agent/joint-class-records-20260921" % side,
        "dof_count": 3,
        "dof_form": "three named rotational coordinates (the OpenSim ball-and-socket record: flexion, "
                    "adduction, rotation) - " + TEETH,
        "range_rad": [[-2.0943951, 2.0943951], [-2.0943951, 2.0943951], [-2.0943951, 2.0943951]],
        "range_source": "gait2392_thelen2003muscle.osim hip_%s: hip_flexion_%s/adduction_%s/rotation_%s, "
                        "each [-2.0943951, 2.0943951] rad (parsed from the sha-pinned committed record; the "
                        "hip lane's registered band edge R); Rajagopal2016.osim hip per-axis bands "
                        "[-0.52359878, 2.0943951] / [-0.87266463, 0.52359878] / [-0.6981317, 0.6981317] "
                        "recorded as the same-class context; adult-human band, species and stage deviation "
                        "named, never tuned" % (band_ref, band_ref, band_ref, band_ref),
        "pivot_form": "sphere_fit",
        "pivot_record": "REGISTERED: the femoral-head center fit of "
                        "hip_pivot_proof_20260921/battery.json (radius %s mm, rms_residual %s mm; predicate "
                        "P6' v2, law doc 5B - real-vs-null discriminating); the axis is the bilateral line "
                        "through the two hip pivots, sign set by the recorded curl (law doc section 3)"
                        % (radius, rms),
        "citations": "docs/THE_ARTICULATION_LAW.md sections 3, 5, 5A, 5B; " + SRC_G + "; " + SRC_R
                     + "; Hartman & Straus 1933, The Anatomy of the Rhesus Monkey",
    }


def knee(side, gap_note):
    return {
        "class": "hinge_revolute",
        "reading": "knee joint (%s): femorotibial apposition, the hind chain's touching_edge at the derived "
                   "gap valley (%s)" % (side, gap_note),
        "dof_count": 1,
        "dof_form": "one revolute coordinate (hinge) - " + TEETH,
        "range_rad": [-2.0943951, 0.17453293],
        "range_source": "gait2392_thelen2003muscle.osim knee_l/r knee_angle [-2.0943951, 0.17453293] rad, "
                        "one-sided flexion (parsed from the sha-pinned committed record); "
                        "Rajagopal2016.osim walker_knee_l/r knee_angle [0.0, 2.0944] recorded as the "
                        "same-class context (one-sided, opposite sign convention); adult-human band, species "
                        "and stage deviation named, never tuned",
        "pivot_form": "pin_axis",
        "pivot_record": HINGE_PIVOT_NOTE,
        "citations": "docs/THE_ARTICULATION_LAW.md sections 1.3a and 3; " + SRC_G + "; " + SRC_R,
    }


def elbow(limb, partner):
    return {
        "class": "hinge_revolute",
        "reading": "elbow (forelimb %s): humero-antebrachial apposition - the humerus membrane articulates "
                   "with BOTH forearm membranes (the elbow's two osseous appositions of one anatomical "
                   "hinge, carried by this bond and %s)" % (limb, partner),
        "dof_count": 1,
        "dof_form": "one revolute coordinate (hinge) per anatomical hinge - " + TEETH,
        "range_rad": [0.34906585, 2.44346095],
        "range_source": "monkeyArm_current.osim (macaca forelimb) elbow elbow_flexion [0.34906585, "
                        "2.44346095] rad, one-sided (parsed from the sha-pinned committed record) - the "
                        "closest-species record in the held set; Rajagopal2016.osim elbow_l/r [0.0, 2.618] "
                        "same-class context; adult-band, species and stage deviation named, never tuned",
        "pivot_form": "pin_axis",
        "pivot_record": HINGE_PIVOT_NOTE,
        "citations": "docs/THE_ARTICULATION_LAW.md sections 1.3a, 1.4 and 3; " + SRC_M + "; " + SRC_R,
    }


def radioulnar(limb):
    return {
        "class": "hinge_revolute",
        "reading": "radioulnar articulation (forelimb %s): the apposed shafts of the two forearm membranes "
                   "(the bond carries the radioulnar complex's apposition; the proximal and distal pivots "
                   "are not distinguished at membrane granularity)" % limb,
        "dof_count": 1,
        "dof_form": "one revolute coordinate (pronation-supination pivot) - the same paired-bone morphology "
                    "that holds NO DOF as the tibiofibular syndesmosis by cited absence: " + TEETH,
        "range_rad": [-1.57079633, 1.57079633],
        "range_source": "monkeyArm_current.osim ulnar_radial radial_pronation [-1.57079633, 1.57079633] rad "
                        "(parsed from the sha-pinned committed record); Rajagopal2016.osim radioulnar_l/r "
                        "pro_sup [0.0, 1.57079633] same-class context; adult-band, species and stage "
                        "deviation named, never tuned",
        "pivot_form": "pin_axis",
        "pivot_record": HINGE_PIVOT_NOTE,
        "citations": "docs/THE_ARTICULATION_LAW.md sections 1.3a, 1.4 and 3; " + SRC_M + "; " + SRC_R,
    }


def tarsal(reading, measured=True, extra_range="", extra_pivot=""):
    pivot_record = "PRESCRIBED FORM (the held PinJoint records), AXIS DERIVATION OPEN - and " + TARSAL_PIVOT_MEASURED
    if not measured:
        pivot_record += (". This bond is NOT among the six measured cycle bonds: no fit or seat reading "
                         "exists for it; the first pose through it pre-registers its derivation and "
                         "inherits the falsifiers")
    if extra_pivot:
        pivot_record += " " + extra_pivot
    return {
        "class": "condyled_gliding",
        "reading": reading,
        "dof_count": 1,
        "dof_form": "one revolute coordinate (the held PinJoint record of the tarsal complex) - " + TEETH,
        "range_rad": [-0.34906585, 0.34906585],
        "range_source": TARSAL_RANGE_SOURCE + (("; " + extra_range) if extra_range else ""),
        "pivot_form": "pin_axis",
        "pivot_record": pivot_record,
        "citations": "docs/THE_ARTICULATION_LAW.md sections 1.4, 3 and 5B; " + SRC_R + "; " + SRC_G
                     + "; tools/science_funnel/validation/tarsal_cycle_pivots_20260921/receipt.json",
    }


def syndesmosis(side, gap):
    return {
        "class": "syndesmosis_nodof",
        "reading": "tibiofibular syndesmosis (%s): the apposed shafts of tibia and fibula, measured gap %s mm" % (side, gap),
        "dof_count": 0,
        "dof_form": "NONE - fusion class (law doc section 3(4)): today's bond semantics IS the law for this "
                    "class, stated explicitly instead of by omission - " + TEETH,
        "range_rad": None,
        "range_source": "CITED ABSENCE: no tibiofibular joint exists in any held model (Rajagopal2016.osim: "
                        "ten PinJoints - ankle/subtalar/mtp/elbow/radioulnar per side - and none "
                        "tibiofibular; gait2392_thelen2003muscle.osim: none; monkeyArm_current.osim: none); "
                        "no range exists to cite and none is invented",
        "pivot_form": "none",
        "pivot_record": "the measured sphere fits of tarsal_cycle_pivots_20260921 converge on this bond and "
                        "DISCRIMINATE real from null - and bind NOTHING: geometric admissibility is not a "
                        "DOF; the class record refuses every pose through this bond "
                        "(out_of_anatomical_range), the law doc A5 refusal",
        "citations": "docs/THE_ARTICULATION_LAW.md sections 1.4 and 3(4); " + SRC_R + "; " + SRC_G
                     + "; tools/science_funnel/validation/tarsal_cycle_pivots_20260921/receipt.json",
    }


def positional(chain, limb_kind, side_label):
    return {
        "class": "positional_contact",
        "reading": "curl apposition (%s, %s): the %s carried against the %s in the scanned curled fetal "
                   "pose - a positional contact, NOT an anatomical articulation (the pose_contacts finding "
                   "of this definition, applied here to the in-chain appositions); flagged for anatomical "
                   "review" % (chain, side_label, limb_kind[0], limb_kind[1]),
        "dof_count": 0,
        "dof_form": "NONE - no anatomical joint exists at this contact to own a coordinate (the corpse-pose "
                    "apposition class); the bond keeps its cure and B2 failure semantics exactly like every "
                    "bond - the class record binds poses only",
        "range_rad": None,
        "range_source": "none exists to cite: no anatomical joint is claimed at this contact - no range is "
                        "invented; the pose_contacts wording is the precedent",
        "pivot_form": "none",
        "pivot_record": "no rotation center: a pose that would rotate this bond has no anatomical record to "
                        "cite and is refused by name",
        "citations": "this definition's pose_contacts section; docs/THE_ARTICULATION_LAW.md sections 0 and 3(3)",
    }


# ---- THE PER-BOND CLASS RECORDS (pre-registered in preregistration.md BEFORE applying) ----
RECORDS = {
    "bond.joint_01_02": hip("left", "l", "3.044128510081", "0.155477725893"),
    "bond.joint_01_03": hip("right", "r", "2.682250273053", "0.147474758014"),
    "bond.joint_02_06": knee("left, femur (side left) to tibia", "2.91 mm at the (2.91, 3.04) shared cut interval"),
    "bond.joint_03_07": knee("right, femur to tibia (side right)", "2.83 mm"),
    "bond.joint_02_15": positional("hind", ("pes fragment mem.bone_15", "femur mem.bone_02"), "left"),
    "bond.joint_03_17": positional("hind", ("pes fragment mem.bone_17", "femur mem.bone_03"), "right"),
    "bond.joint_04_08": positional("fore", ("hand membrane mem.bone_08", "humerus mem.bone_04"), "chain A"),
    "bond.joint_05_09": positional("fore", ("hand membrane mem.bone_09", "humerus mem.bone_05"), "chain B"),
    "bond.joint_04_10": elbow("A", "bond.joint_04_12"),
    "bond.joint_04_12": elbow("A", "bond.joint_04_10"),
    "bond.joint_05_11": elbow("B", "bond.joint_05_13"),
    "bond.joint_05_13": elbow("B", "bond.joint_05_11"),
    "bond.joint_10_12": radioulnar("A"),
    "bond.joint_11_13": radioulnar("B"),
    "bond.joint_06_20": syndesmosis("left", "0.48"),
    "bond.joint_07_21": syndesmosis("right", "0.45"),
    "bond.joint_06_25": tarsal("tibiocrural apposition (left): the pes's tarsal trochlear region against the "
                               "tibia - tarsal 3-cycle A (06-20-25) DRIVER bond"),
    "bond.joint_20_25": tarsal("fibulotarsal apposition (left): the lateral malleolar contact of the pes - "
                               "tarsal 3-cycle A (06-20-25) LOOP bond; measured loop-seat margin "
                               "0.357668256426 mm at the registered band"),
    "bond.joint_07_24": tarsal("tibiocrural apposition (right): the pes's tarsal trochlear region against the "
                               "tibia - tarsal 3-cycle B (07-21-24) DRIVER bond"),
    "bond.joint_21_24": tarsal(
        "fibulotarsal apposition (right): the lateral malleolar contact of the pes - tarsal 3-cycle B "
        "(07-21-24) LOOP bond; measured loop-seat margin 0.040529146675 mm at the registered band - THIN, "
        "RECORDED THIN: the practical edge of the band on this cycle; a future pose needing margin narrows "
        "the band lawfully (a pre-registered, derived narrowing of the class's own range record), never "
        "widens the committed 3.0 mm cut; the class-prescribed pin-axis form is the receipt's named lawful "
        "route to widen the margin itself",
        extra_pivot="The receipt's own words: the successor class amendment (a hinge-axis or contact-frame "
                    "pivot form prescribed per class) is the lawful way to widen it."),
    "bond.joint_07_18": tarsal("tibiocrural apposition (right): tibiopodal contact of the pes fragment "
                               "mem.bone_18", measured=False),
    "bond.joint_22_25": tarsal("intertarsal apposition within the left pes (fragments mem.bone_22 - "
                               "mem.bone_25)", measured=False,
                               extra_range="the held models carry NO intertarsal record; the class's cited "
                                           "band is applied as the class record and the joint-level gap is "
                                           "named, never tuned"),
    "bond.joint_23_24": tarsal("intertarsal apposition within the right pes (fragments mem.bone_23 - "
                               "mem.bone_24)", measured=False,
                               extra_range="the held models carry NO intertarsal record; the class's cited "
                                           "band is applied as the class record and the joint-level gap is "
                                           "named, never tuned"),
}

EXPECTED_COUNTS = {"ball_and_socket": 2, "hinge_revolute": 8, "condyled_gliding": 7,
                   "syndesmosis_nodof": 2, "positional_contact": 4}


def indent_block(record: dict) -> str:
    """Serialise a joint_class record at bond-key depth (3 spaces / inner 4)."""
    text = json.dumps(record, indent=1, ensure_ascii=True)
    lines = text.split("\n")
    out = ["   \"joint_class\": " + lines[0]]
    for ln in lines[1:]:
        out.append("   " + ln)  # json indent=1 inner lines carry 1 space -> 4; closing '}' -> 3
    return "\n".join(out)


def apply_records() -> None:
    raw = DEFN.read_text(encoding="utf-8")
    body = json.loads(raw)
    bond_ids = [b["id"] for b in body["bonds"]]
    missing = [bid for bid in bond_ids if bid not in RECORDS]
    extra = [bid for bid in RECORDS if bid not in bond_ids]
    if missing or extra:
        raise SystemExit("record table != committed bonds; missing=%s extra=%s" % (missing, extra))
    for bid in bond_ids:
        anchor = "\"id\": \"%s\"" % bid
        i = raw.index(anchor)
        j = raw.index("\"\n  }", i)  # the bond object's closing quote + closer (2-space indent)
        insertion = ",\n" + indent_block(RECORDS[bid])
        raw = raw[:j + 1] + insertion + raw[j + 1:]
    DEFN.write_bytes(raw.encode("utf-8"))
    print("applied joint_class records to %d bonds -> %s" % (len(bond_ids), DEFN))


def emit_table() -> str:
    rows = []
    for bid, rec in RECORDS.items():
        rows.append("| %s | %s | %s | %s | %s |" % (
            bid, rec["class"], rec["dof_count"],
            json.dumps(rec["range_rad"]),
            rec["pivot_form"]))
    return "\n".join(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    if args.apply:
        apply_records()
    elif args.table:
        print(emit_table())
    else:
        print("nothing to do: pass --apply or --table")
