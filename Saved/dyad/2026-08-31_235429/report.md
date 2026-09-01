# dyad scan — 2026-08-31_235429

- started: 2026-08-31T23:54:32
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — show t = 0.00s
`fps 58.440437 · ft avg 14.199703 ms · stage: B7 ARTICULATE`

**read 0** (105.9s)

Reading the mesh on its own, it does not read as a believable creature. It reads as a torso that lost its lower half and had its neck over-cranked. Ranked by severity:

1. **Legs / pelvis — collapsed to nothing.** Below the waist there is no thigh, knee, shin, or foot at all; the body simply tapers to a thin point and stops. The lowest geometry floats well above the perspective grid, so the "standing" pose is a lie — there is zero ground contact, no weight, no shadow anchor. This alone breaks the silhouette: an animal cannot be balanced on a single narrowing stump.

2. **Throat / neck-to-shoulder junction — torn open.** There is a horizontal rip across the front of the neck where it meets the chest. The edge is jagged and you can see a fringe of small spiky triangles (interior geometry / inverted faces) poking through, like skin peeled back from the joint. This is exactly the "torn at a joint" failure mode.

3. **Chest — open seam.** Just under the rounded pectoral bulge there is a dark horizontal gash running across the torso. It reads as a hole or un-welded edge rather than shading, breaking the volume of the chest wall.

4. **Neck — over-stretched.** The neck is an unnaturally long, thin rubbery column; the cranium sits far too high on it for any quadrupedal or brachiating monkey. Combined with the spine bend readout (theta ~117°), the head looks dislocated upward rather than articulated.

5. **Shoulders / elbows — pinched creases.** At both deltoids and around the right elbow there are hard fold lines where triangles collapse into a sharp ridge; the left shoulder in particular shows a shading discontinuity that looks like a seam or partial tear, not smooth skin.

6. **Arms & hands — disproportionate spikes.** The arms are too long and too thin for the torso (gibbon-length on a body with no legs), and the hands read as flat splayed claws/fused mittens rather than grasping hands; they hang like detached flaps.

7. **Shading coherence.** The form is patchy: hard flat facets on the ear flaps, banded/uneven shading across the neck and chest, and the torn regions punch dark holes that read as missing surface rather than shadowed volume. The result looks noisy and partially hollow in places it should be solid (throat, chest, hips).

Net: the silhouette is unreadable as an animal — a floating head-on-a-stretched-neck with a gashed torso and no legs touching the ground.

## shot 01 — show t = 1.50s
`fps 55.944309 · ft avg 14.956426 ms · stage: B7 ARTICULATE`

**read 0** (161.6s)

Ranked by how badly they break the creature read:

1. **Neck / head seam — catastrophic tear and collapse.** The single worst defect. Where the face/muzzle should project forward there is instead a concave crater, and below it a second horizontal jagged gap with exposed interior geometry (the row of tiny spikes in the dark cavity reads as torn-back faces or broken verts, not teeth). The neck itself is not a cylindrical column but an elongated flat strap/slab that kinks rather than curves. At its base — the neck‑to‑upper‑shoulder seam — there is a frayed, comb‑like torn edge where the surface has been pulled apart by the spine_upper rotation (theta ≈ 117°). This junction looks like an open wound, not anatomy; it destroys any sense of a head sitting on a neck.

2. **Legs / pelvis — collapsed to nothing.** The lower torso tapers into a single thin vertical spike at the crotch and simply ends. There is no thigh, no knee, no calf, no foot anywhere below the torso. So despite the "standing on a perspective grid" framing, the figure has zero ground contact — it reads as a head‑and‑torso floating above the floor plane. This is a silhouette failure: the body looks amputated at the pelvis and top‑heavy, with nothing anchoring it to the world.

3. **Torso surface holes / pinched seams.** The front of the chest has a dark curved slot beneath the pectoral bulge — that is not a mouth or a muscle crease, it's an inverted/pinched seam showing backface geometry (a hole in the torso skin). The right deltoid/armpit (viewer‑left) also shows a clean diagonal split line where arm meets shoulder, reading as a tear rather than a smooth join. These read as patchy noise on an otherwise smooth body.

4. **Arms and hands — wrong proportions, fused digits.** Both arms are grossly over‑long and tube‑like: no elbow taper or forearm bulge, hanging well past where the hips should be (and there is nothing to hang past). The fingers read as splayed claws; on the viewer‑left hand they blur/fuse into indistinct spikes rather than separate phalanges. Readable as limbs, but not as a monkey's arms.

5. **Ears and minor shading coherence.** The two "ears" are flat lateral tabs that read as fins or flaps rather than rounded ears — they sit too high and flat on the skull to read as ears at all. Shading is mostly a clean single warm key from upper‑left, but it exposes hard facets on the brow shelf and deltoids, and the dark interior of the neck crater plus the chest slot break surface continuity so the form reads as punctured rather than solid volume in those regions.

Net: the torso massing and overall stance do not read as a monkey — they read as an incomplete puppet with

## shot 02 — show t = 3.00s
`fps 56.673721 · ft avg 14.71831 ms · stage: B7 ARTICULATE`

**read 0** (130.3s)

Reading it as a sculptor would, this thing does not read as an animal — it reads as a stack of separate lumps that failed to fuse, with one open wound in the face. Ranked worst first:

**1. Face / jaw — torn open, interior exposed.** The single most broken area is the lower head. There is no continuous skin from cranium to muzzle; instead a dark, jagged horizontal gash cuts across where the mouth and lower jaw should be, and you can see *inside* the mesh (the row of little vertical slivers along that seam are back‑faces / inner triangles showing through). The top dome and the snout read as two disconnected shells with a gap between them. This is not a mouth, it's a hole — skin pulled away from the facial joint and never re‑welded.

**2. Hind legs / feet — missing entirely.** Below the ribcage there are no legs. The torso simply tapers into a single rounded stump that ends in mid‑air above the grid. There is no hip split, no thigh, no knee, no foot, and therefore no honest ground contact: the creature appears to hover on a fused cone rather than stand on two planted feet. The silhouette of the lower body has collapsed to nothing.

**3. Neck — kinked past anatomical range.** The head sits on a thick stalk that bends at a hard angle (the readout confirms it: *spine_upper theta 117°*), producing a broken‑neck / dislocated‑cervical look rather than a supple curve. A monkey cannot articulate its neck like this while the torso stays upright; the column also appears to intersect and pass behind the shoulder line, i.e. interpenetration at the neck–back junction.

**4. Arms — wrong length, wrong mass.** Both forelimbs are far too long and far too thin for a primate: they hang like spider legs well past the hip line, with no deltoid, no triceps swell, and only a faint diagonal seam where the arm cap meets the torso (clearly visible on the viewer‑left upper arm). The shoulder reads as a separate ball dropped onto the chest rather than grown from it.

**5. Hands — merged paddles with floating spikes.** Neither hand reads as a primate hand. They are flattened flippers/claws; on the viewer‑right hand the "fingers" read as thin detached spikes splaying off a paddle, not articulated digits. The silhouette of both hands is unreadable at this angle.

**6. Chest / torso surface — cut edges and patchy normals.** Under the pectoral bulge there is a hard horizontal slit (an open edge rather than shaded form), and along that same tear plus the neck kink the shading goes noisy/patchy — you can see individual facets and flipped normals where the surface should be smooth volume. The rest of the clay body reads as lumpy blobs more than anatomy: no defined clavicle, scapula, waist, or pelvis.

Net: the silhouette is top‑heavy (oversized cranium + long dangling arms) with a void where the legs and feet belong, and one open facial wound. As it stands it would not pass an artist's eye test as a believable creature — fix the jaw/face topology first, then grow the hind limbs and plant them on the grid, then tame the neck bend and rebuild arm/hand mass.

## shot 03 — show t = 4.50s
`fps 56.08543 · ft avg 14.918736 ms · stage: B7 ARTICULATE`

**read 0** (117.2s)

Looking past the chrome, here's what's wrong with the creature itself, worst first.

**1. Head / jaw — detached and hollow.** The single worst thing: there is a clean horizontal shear right under the skull. The entire lower face (muzzle, jaw, mouth) has sheared off or collapsed inward into the neck cavity, leaving a jagged open hole with raw interior triangles showing along its bottom edge like broken teeth. The head reads as a featureless balloon — no eyes, no nose, no brow — sitting on top of an empty socket rather than being attached to a face. It looks like a sliced mannequin head dropped onto a tube.

**2. Neck / upper spine — impossible elongation and kink.** The neck is grotesquely long and bends at a sharp crease near the base of the skull, folding back on itself in a way no primate neck can. The readout (`spine_upper theta 117°`, ROM up to ~169°) confirms it's being driven far past a sane range: the result is a pinched, crumpled tube with a hard fold line rather than a smooth cervical curve. The head floats far above the shoulders on this twisted column — the neck–shoulder junction has no structural logic.

**3. Lower body / legs / feet — missing; no honest ground contact.** Despite the "standing on grid" intent, there are no visible legs or feet in this pose. Below the pelvis the mesh collapses into a single thin vertical strip (spine/tail edge-on), and nothing actually meets the perspective floor — the creature is effectively floating with no lower limbs planted. The silhouette simply dies at the hips.

**4. Shoulders / deltoids — torn seams.** Both shoulder caps show diagonal gashes where arm meets torso: a triangular flap of skin peeled back on each side (clearly visible on the viewer-left shoulder, mirrored on the right). The arm doesn't blend into the body; it looks stapled on with the joint exposed.

**5. Chest / pectorals — protruding blob and open slit.** The upper sternum has an inflated rounded mass that bulges forward like a separate object, with a dark horizontal gash beneath it (the lower pec line reads as a cut, not anatomy). Combined with the over-narrow waist and oddly flared hips, the torso silhouette is lumpy and incoherent rather than reading as one solid ribcage.

**6. Hands — fused spiked mittens.** The hands are flat, thumbless claws; fingers read as thin splayed spikes (worst on the viewer-right hand) with no separation or palm volume. They don't function as grasping hands at any point in this pose.

Net: the head/neck junction is broken (missing face + over-rotated kinked neck), the lower body isn't there to make ground contact, and the limb-to-torso seams (shoulders, chest) are tearing open. The surface shading is mostly coherent as volume *except* at exactly those torn cavities, where it reads as hollow and unshaded.

## shot 04 — show t = 6.00s
`fps 59.160149 · ft avg 14.053323 ms · stage: B7 ARTICULATE`

**read 0** (107.8s)

Reading the mesh on its own terms, this does not read as an animal — it reads as a deformation blowout. Ordered by how badly each defect breaks the figure:

1. **Head / jaw — torn open.** The face is split horizontally into two disconnected slabs with a dark jagged void between them (roughly where muzzle meets lower jaw). Inside that gap you can see raw interior geometry and a fringe of small spike/teeth artifacts along the bottom rim. This is not a mouth, it's a hole in the surface; the skin has pulled apart at the cranio‑facial seam and nothing closes it.

2. **Neck — catastrophically over‑stretched.** The cervical region is a long, thin, taut tube pulling the cranium far away from the shoulders (consistent with that `spine_upper theta 117°` readout). No primate neck elongates like this; it reads as a stretched‑taffy deformation failure rather than anatomy, and it makes the head look bolted on at the end of a stalk.

3. **Lower body / legs — collapsed and absent.** Below the waist there are no thighs, knees, ankles or feet — just a smooth flared cone (a "skirt"/bell) with a faint vertical crease down the front. The entire lower silhouette vanishes into one inflated mass. Consequently there is **zero ground contact**: the bottom of that cone hovers above the perspective grid with no foot, no shadow, no weight line — the creature floats. That's dishonest grounding.

4. **Hands / fingers — spiked.** Both hands terminate in jagged claw‑like protrusions instead of formed digits (the screen‑right hand is worst: a cluster of thin spikes). The geometry is poking through where knuckles and fingertips should be.

5. **Torso surface — patchy creases, weak volume.** There's a horizontal slit/crease across the lower chest that reads as a cut rather than a pectoral line, and the shoulders/hips have no deltoid or pelvic structure — they're smooth lumps. The clay shading is mostly even but it gives an inflated‑balloon surface with little internal form; combined with the dark interior showing through the head tear, the volume breaks down exactly where you'd expect muscle to be.

Net: proportions are unreadable (oversized cranium on a stalk, stick arms, no legs), the silhouette collapses at the bottom into a cone, and there is an actual mesh hole across the face plus spike artifacts in the hands. The articulation is currently pulling the upper spine past any plausible cervical range, which is what's stretching the neck and dragging the head off‑axis from the torso.

## shot 05 — show t = 7.50s
`fps 60.566906 · ft avg 13.591177 ms · stage: B7 ARTICULATE`

**read 0** (104.8s)

Reading the mesh on its own, it does not pass as a creature. It reads as a stretched clay blob that has been pulled apart at several seams. Ordered by severity:

1. **Lower body / pelvis → legs.** This is the worst defect and it is total. Below the ribcage the torso simply tapers to a point and stops — there are no thighs, no knees, no feet. The figure hangs in mid-air above the perspective grid with nothing touching the ground plane. There is no honest contact because there is no lower limb geometry at all; whatever should be legs has collapsed into the pelvis stump.

2. **Neck / jaw junction.** There is a clean horizontal tear across the front of the neck, just under the cranium: a jagged lip with a row of spike-like interior edges (the "teeth" shelf) where skin has been ripped open and the inner shell shows through. The head therefore looks unscrewed from the body — a big balloon skull sitting on top of a thin stretched tube, joined by torn geometry rather than a continuous neck.

3. **Chest / sternum.** A second mouth-like horizontal slit is cut into the middle of the chest, with its own dark interior gap. Either this is a hole in the mesh or facial geometry has been welded onto the torso; either way it reads as damage and breaks the silhouette of the torso front.

4. **Ears.** Asymmetric and detached-feeling: the left ear (viewer's left) is a flat disc hovering off the side of the skull with a visible seam/shadow gap, while the right side is just a small nub. They do not sit flush on the skull.

5. **Arms / shoulders.** The arms are far too long and thin for the torso and flare outward at the shoulder in a way that suits a hanging brachiator, not this upright stance; the deltoid area shows pinched seam artifacts and the elbow line reads as a single tapering tube rather than an upper-arm/forearm with a defined joint.

6. **Face.** The cranium is a featureless smooth mass — no eyes, brow, nose, or muzzle. The head silhouette is unreadable as a monkey; combined with defect #2 it just looks like a swollen neck tumor.

7. **Shading coherence.** Mostly smooth clay shading, but there is visible banding and patchy normal discontinuity right at the neck tear and around the chest slit, so those regions look noisy/flat rather than solid volume.

Net: the upper spine articulation has sheared the mesh open at the jaw/neck and left a phantom opening on the chest, while the entire leg chain is missing — so the figure floats, has no feet, and its head reads as detached. The silhouette collapses below the waist and the face is absent; those are the things to fix first.

## shot 06 — show t = 9.00s
`fps 57.775898 · ft avg 14.402111 ms · stage: B7 ARTICULATE`

**read 0** (107.4s)

No, it does not read as a believable creature at this moment; it reads as a broken rig mid‑failure. Ranked by severity:

**1 — Neck / base of skull is torn open.** This is the worst thing in the frame. There is a clean horizontal rip running across the neck right where the head mass meets the lower cervical column, and you can see straight into the model through it: a dark serrated band of interior geometry with jagged, separated edge loops. The "skin" above the tear (the skull) and below it (the long neck tube) are not continuous — they have pulled apart at the joint exactly as a bad skin‑bind does when a bone rotates past its envelope. On top of that, the neck itself is stretched into an absurdly elongated column; whatever deformation is driving `spine_upper` has yanked the head far above the shoulders on a thin, over‑stretched stalk rather than articulating a normal cervical curve. So you have both defects at once here: a hole *and* skin tearing away from the joint.

**2 — The lower body simply stops; there is no ground contact.** Below the pelvis the mesh tapers to a rounded stump around mid‑thigh and then ends in empty air. There are no shins, no knees worth naming, no feet, nothing touching the perspective grid — the figure is floating well above the floor plane it is supposedly standing on. The "standing" premise fails: there is no honest contact because there is nothing to make contact. Whatever weight‑bearing structure should exist below the hips has collapsed or was never generated.

**3 — The face is collapsed and the skull is asymmetric.** The head is a smooth featureless bulb with no muzzle, eyes, nose, or brow — the entire front of the face reads as caved in or missing, so the silhouette gives you an animal's cranium but none of its expression apparatus. The ears confirm something is wrong on one side: viewer‑left has a large flat ear flap, while viewer‑right has only a small nub, which reads as detached or under‑generated geometry rather than a mirrored pair.

**4 — Chest/sternum shading and form break down.** There is an inflated spherical bulge on the sternum that does not correspond to any pectoral anatomy, and directly beneath it a horizontal slit/line across the lower chest that reads like a seam or partial hole rather than muscle. In this region the surface stops reading as continuous volume and becomes patchy — flat planes meeting a sphere with no transitional shading.

**5 — Shoulders, forearms, and hands pinch.** The deltoid attachments show pinching/seam lines where the arms meet the torso, the arms are spindly and over‑long relative to the body mass, and the wrists transition into flat, spiked flipper‑hands that look only loosely attached to the forearm — thin at the joint, splayed fingers reading as spikes rather than digits.

Net: the silhouette is dominated by an oversized head on a stretched neck with no legs beneath it, and the single most damaging defect is the open tear at the neck joint exposing the interior mesh. As posed, this is not something any animal could hold; it is a rig whose spine/neck deformation has exceeded its skin envelope while the lower limbs are entirely absent.

## shot 07 — show t = 10.50s
`fps 54.212051 · ft avg 15.522893 ms · stage: B7 ARTICULATE`

**read 0** (117.5s)

Looking only at the mesh in the viewport, here is what is wrong, worst first.

**Head / neck / upper‑torso junction — open tear and detachment.** This is the dominant defect. The head does not sit on the body; it hovers above it, joined by a single thin neck column that leans to one side, while directly beneath the chin there is a wide horizontal gash where the jaw has been sheared away. You can see straight through into the model: an open rim of geometry and a row of small jagged triangles (the "teeth" spikes) hanging in the void between skull and chest. That is not shading or a shadow — it is missing skin, a hole exposing interior faces, and a limb‑to‑torso separation at the neck/shoulder line. No amount of articulation hides that the head is unattached on one side.

**Lower body / legs — collapsed to nothing.** Below the ribcage the torso simply pinches down into a thin tapering stump with two tiny nub spikes at the crotch, and then there is *nothing*. There are no thighs, knees, shins, ankles, or feet anywhere in the frame. The creature is described as "standing on a perspective grid," but it cannot be standing: its lowest geometry is that pointed stump hovering at/above the plane with no foot touching it. So ground contact is absent and therefore dishonest — there is no weight, no planted foot, no compression; the body looks like it is floating or impaled rather than supported.

**Cranium / neck proportions.** The skull is a huge bulbous balloon on top of an absurdly long, narrow giraffe‑like neck, with two small lopsided ear flaps and no readable face (no eyes, nose, or mouth as structures). The silhouette reads as a broken puppet or an alien, not a monkey: massively top‑heavy, the head dwarfing the entire torso.

**Chest / sternum — second hole and wrong anatomy.** The pectoral region is two inflated rounded lobes that read more like breasts than primate chest muscle, and beneath them sits a dark horizontal slit/opening — another break in the surface rather than an anatomical feature. These lobes look like separate inflated shapes stuck onto the front of the body instead of being integrated into it.

**Arms / shoulders / hands.** The arms are too long and stick‑thin for a monkey, with no visible elbow bend; at both shoulder caps there are raised seam ridges where the geometry meets the torso (the viewer‑left shoulder especially shows a hard step). The "hands" are flat splayed fins/claws — no fingers, no palm structure.

**Shading.** Mostly smooth clay shading that does give some volume on the head and upper arms, but it is exactly at the broken regions that coherence fails: the neck tear and chest slit read as flat, dark, patchy interior faces rather than shaded form, and the spike row reads as noise/spikes rather than surface. So the surface only holds together where it is intact; everywhere there is a hole the volume collapses into a noisy flat gap.

Net impression to an artist: top‑heavy bulbous head on too long a neck, floating over a torso that has no legs and never touches the ground, with two open tears (neck/jaw and chest) showing the inside of the mesh. The structural breaks at the neck and the missing lower limbs are the things to fix first; everything else is secondary anatomy/proportion work.
