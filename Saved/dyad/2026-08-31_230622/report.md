# dyad scan — 2026-08-31_230622

- started: 2026-08-31T23:06:25
- reads per shot: 1 (NOT a vote — all reported)
- crop: none (whole window)
- engine: 2560x1440

## shot 00 — show t = 0.00s
`fps 53.196346 · ft avg 15.912309 ms · stage: B7 ARTICULATE`

**read 0** (73.5s)

It does not read as a believable creature right now — it reads as a broken rig test, and several parts are actively torn or detached rather than just poorly proportioned. Most severe first:

1. **Jaw / neck junction — torn.** The lower skull is missing its jaw; there's a serrated, jagged hole where the mouth and chin should be, and a dark gap between the head and the body. The head looks like it's hanging off rather than attached. This is the worst defect on the model.

2. **Neck — wrong proportion.** It's a long thin tube, several times too long for the torso, which makes the whole figure look stretched and doll-like instead of animal. Combined with #1 it sells "detached head."

3. **Right hand (viewer's right) — spiked / detached digits.** The fingers are exploding into flat spikes and the forearm-to-hand transition looks like skin tearing away from the joint. It does not read as a hand or a foot; it reads as geometry failing at that joint.

4. **Chest / pectoral area — collapsed volume.** There's a flat oval plate inset on the front of the torso with a dark slit beneath it. Instead of rounded chest mass you get a flattened disc and a hole, so the front of the body loses its sense of solid form.

5. **Pelvis / tail — reads as a blade, not a tail.** The long curved element coming off the hip is flat, pointed, and fin-like; it looks like a stretched spike or a tear in the mesh rather than a tapered tail with volume.

6. **Left shoulder (viewer's left) — gap at the joint.** There's a visible break where the upper arm meets the torso; skin appears to pull away from the shoulder socket.

7. **Legs / feet — no honest ground contact.** The legs end in short stubs that don't clearly resolve into feet, and they don't sit convincingly on the grid; the figure looks like it's floating or cut off at the ankles rather than standing.

Shading is otherwise coherent matte clay, so the problem isn't noise or patchiness — it's topology: tears at the jaw/neck and right hand, a flattened chest, a spike-tail, and a neck that's far too long. Fix the torn jaw/neck seam and the spiking right hand first; those are what make it look broken rather than just unrefined.

## shot 01 — show t = 1.50s
`fps 54.259464 · ft avg 15.570381 ms · stage: B7 ARTICULATE`

**read 0** (93.4s)

Most severe first:

1. **Neck / throat — torn skin.** Where the head meets the torso there is a jagged, saw‑toothed tear running across the upper chest/neck base. The surface pulls apart into a flap with a visible gap behind it; this reads as broken topology or a failed skinning weight at that joint, not as anatomy. It's the single worst defect and it sits right in the visual centre of the figure.

2. **Chest / ribcage — collapsed patch.** On the front of the torso there is a flat elliptical depression (mouth‑shaped) that looks like missing or flattened geometry rather than a pectoral form. It breaks the volume of an otherwise rounded chest and reads as a hole or a deflated region.

3. **Hands / fingers — stretched into spikes.** Both hands, especially the right one extended to the side, have fingers pulled out into long thin claws that look detached from the wrist and far too elongated for a monkey hand. The left hanging hand shows the same over‑stretch at the knuckles. This is the "spiked/detached" class of defect on the limbs.

4. **Feet / lower legs — no foot, dishonest contact.** The two legs run straight down as thin columns and simply terminate in a flat line at the grid plane; there is no readable foot geometry pressing into the floor. So while the model does touch the ground, the contact looks fake because nothing with mass or shape is actually making it.

5. **Proportions / silhouette — head too big, torso collapses to a stick.** The skull is oversized relative to the body, and the trunk is so narrow and elongated that the whole figure reads as a lanky mannequin rather than a monkey's compact mass. The silhouette flattens at the waist/shoulders because there isn't enough volume in the ribcage or pelvis to carry it.

6. **Tail — wire‑thin.** It is connected at the hip and curves plausibly, but it tapers to a needle point with almost no body; it reads as a tube/wire rather than a tail with mass.

Pose: no joint bends in an impossible direction (the head tilt and arm spread are within range), so this isn't a rig‑direction error — the problem is that the static wide arm splay plus the thin limbs make it look posed like a mannequin, not like an animal mid‑motion.

Shading: largely coherent matte volume on the head and torso; it does not read as flat or noisy overall. The only places shading fails are exactly where geometry fails — the neck tear and the chest patch.

## shot 02 — show t = 3.00s
`fps 53.953854 · ft avg 15.613012 ms · stage: B7 ARTICULATE`

**read 0** (75.2s)

Most severe first:

1. **Neck / base of skull — torn skin.** This is the worst defect. The mesh at the top of the spine is pulled apart into a fan of spiky triangles with an open gap you can see straight through to the background between the neck and the shoulder line. It's not stretched, it's *torn*: the skinning has failed where `spine_upper` is driven to ~117°, so the head is craning back past what the weights can follow and the surface rips instead of bending.

2. **Chest / pectoral — open hole or unsealed flap.** On the front of the upper torso there's an oval dark opening that reads as a missing patch (or a double skin fold that never closes). It looks like a mouth-shaped gap in the breastplate, not intended geometry.

3. **Head — wrong silhouette and proportions.** The skull is a bulbous balloon roughly the size of the ribcage, sitting on a thin neck; the side "ear" is a flat disc/paddle sticking out rather than a rounded ear, and the face is a featureless blunt wedge. Silhouette reads as a ball on a stick, not an animal head.

4. **Arms and hands — over-long, spiky.** The limbs are string-thin and far too long for the torso (spider/puppet proportions), and the hands flare into splayed claw-like spikes, especially the right hand which looks like a star of points rather than fingers.

5. **Legs / ground contact — unverifiable, likely clipped.** The lower legs run off the bottom edge of the viewport, so foot contact with the grid can't be read; whatever is there isn't showing an honest planted foot in this frame. (The tail, by contrast, curls cleanly and is fine.)

Shading itself is acceptable — matte clay, volume reads on head and torso, no noise or patchiness — so the problem is geometry and skinning, not surface. The two real failures are the torn neck and the chest hole; everything else is proportion/silhouette.

## shot 03 — show t = 4.50s
`fps 55.067078 · ft avg 15.315495 ms · stage: B7 ARTICULATE`

**read 0** (80.4s)

Most severe first:

1. **Neck base / top of torso — torn.** There is a jagged, saw‑toothed gap where the neck meets the shoulders; skin has pulled away and geometry is simply missing, leaving a dark zig‑zag hole across the upper chest/neck root. This is the worst defect on the body.

2. **Neck + head proportions — wrong silhouette.** The neck is far too long and spindly for a monkey (reads as giraffe/insect), and the head sits oversized on top of it. The creature's overall proportion does not read as a believable primate; the torso‑to‑neck ratio collapses the animal identity.

3. **Chest — flat patch / hole.** A flat elliptical disc or inset floats on the front of the upper torso, like a missing skin patch or a misplaced mouth‑plate. It breaks the volume there and looks detached from the surrounding form.

4. **Hands and fingers — stretched/spiked.** Both hands are oversized mittens with thin spike‑like fingers; the right hand's digits splay into blades and the left hand's fingers hang as long thin spikes. They do not read as functional primate hands.

5. **Tail — detached ribbon.** The tail leaves the groin area as a flat, curved blade/ribbon rather than a tapered limb, and its attachment looks loose/stretched rather than rooted in the pelvis.

6. **Ground contact — not honest / not visible.** The legs terminate at the bottom edge of the viewport; no feet are seen meeting the grid, so the model does not show an honest standing contact (it reads as cropped or floating relative to the floor).

Shading otherwise reads as coherent matte volume; the flatness problems are localised to the chest patch and the torn neck seam, not a global lighting issue.

## shot 04 — show t = 6.00s
`fps 53.907768 · ft avg 15.697047 ms · stage: B7 ARTICULATE`

**read 0** (90.8s)

Most severe first:

1. **Neck / upper‑chest — torn and holed.** This is the worst defect. Where the neck meets the torso there is an open gap: skin has pulled away from the body, leaving a dark hole with jagged, unbound edges and a row of little spike‑like triangles (a "zipper" of loose verts) running across the collarbone/neck base. It's being driven by the spine bend (spine_upper ≈ 117°), which is stretching that region past what the mesh can hold. Reads as a wound, not an animal.

2. **Abdomen / lower chest — open cavity.** There's a horizontal elliptical hole in the belly/chest, like a missing patch or a detached ring of geometry floating inside the torso. Skin does not close over it; you see straight through to the back face.

3. **Tail — wrong form and reads as detached.** It's an overlong, blade‑thin spike shooting out to the side, far too long and sharp for a monkey (reads rat‑ or needle‑like). Its base at the pelvis looks pinched rather than blended into the body.

4. **Arms — proportionally broken.** Both arms are wire‑thin and too long; the shoulders pinch down to a small deltoid bump before tapering to sticks, and the hands are oversized relative to the forearms. The right arm reaching out sideways at that angle looks like it would snap at the shoulder. Not believable limb volume for this body mass.

5. **Head — oversized and featureless.** It's a smooth egg with two ear nubs, no eyes/snout/mouth, and too big for the torso. Silhouette doesn't read as a monkey face; reads as a blob on a stick.

6. **Legs / feet — contact not honest.** The legs are short vertical columns that end at the grid without visible feet, so ground contact looks like flat cut ends resting on the plane rather than planted feet. Combined with the splayed arms and extreme forward spine pitch, the whole stance reads as an awkward reach/T‑pose hybrid rather than something a monkey would actually stand in.

Shading is otherwise coherent matte clay and does read as volume; the only place it breaks is at the torn neck, where you see dark back‑faces through the hole. The defects are topological (tears/holes) and proportional (head, arms, tail), not lighting problems.

## shot 05 — show t = 7.50s
`fps 56.37886 · ft avg 15.049344 ms · stage: B7 ARTICULATE`

**read 0** (81.8s)

Most severe first:

1. **Mid‑torso (chest/upper abdomen): a through‑hole.** There's an oval opening dead‑center on the front of the body where triangles are simply missing — you can see straight through to the back faces. This is the worst defect; it makes the torso read as broken rather than solid, and it's exactly where the mass should be.

2. **Throat / lower‑jaw‑to‑chest junction: torn skin.** Just under the head there's a jagged horizontal rip — the mesh edge is serrated and you can see exposed interior geometry, like the neck has been pulled open from the chest. The head reads as only loosely attached to the body through this tear.

3. **Neck and torso proportions / silhouette: collapsed.** The neck is far too long and thin for a monkey, and the ribcage/abdomen are pinched into a narrow flat slab instead of a rounded volume. Combined with the large head, the whole figure reads as a lanky stick‑figure rather than a believable quadruped/bipedal primate; the shoulder‑to‑chest transition in particular flattens out and loses its form.

4. **Wrists / hands: spiking.** Both forearms end in jagged, spiked geometry at the wrist — most visible on the viewer's‑left hand, where the fingers/wrist break into sharp spikes instead of a clean joint. The right hand is better but still has a hard, angular break at the wrist.

5. **Tail tip: spike.** The tail sweeps out to the viewer's right and terminates in a single sharp point rather than tapering naturally — minor, but it looks like an artifact.

6. **Feet / ground contact: not honest.** The legs run straight down into the bottom reel panel and you never see planted feet with weight on them; there's no visible foot‑to‑grid contact, so the stance doesn't read as grounded.

Shading is the least of the problems — it's a flat matte tan that does give some volume in the crevices, but the form is undermined by the hole and the tear above it. The creature does not currently read as believable: the torn throat and the chest hole are the two things that break it first.

## shot 06 — show t = 9.00s
`fps 54.799812 · ft avg 15.33769 ms · stage: B7 ARTICULATE`

**read 0** (74.9s)

Most severe first:

1. **Neck / upper spine — torn open.** The skin is ripped apart where the neck meets the chest: a jagged, zig‑zag hole you can see straight through, with spiky backface triangles along its edge. This is the over‑rotated `spine_upper` (≈117°) failing to bind; it's not a pose an animal holds, it's a skinning tear.

2. **Mid‑chest / ribcage — collapsed and slit.** The torso reads flat, deflated, with a dark horizontal seam/slit running across the middle of the chest (looks like a pinched mouth or a closed gap). No volume in the barrel; the form flattens instead of rounding.

3. **Neck + head — wrong proportions for a monkey.** The neck is far too long and thin (giraffe‑like) and the skull is oversized and bulbous on top of it. Silhouette doesn't read as a primate; it reads as a lanky humanoid with a big head.

4. **Arms / hands — over‑long, spiky digits.** The arms hang straight down past the hips (too long for this torso), and the fingers are stretched into thin spikes that look half‑detached from the palm, especially the hand on the viewer's right.

5. **Tail — flat ribbon, bad base.** It comes out of the pelvis as a flat band rather than a rounded tail, and its root merges ambiguously with the leg/crotch instead of attaching cleanly to the spine.

6. **Feet / ground contact — not verifiable.** The legs terminate behind the REEL strip at the bottom, so no foot actually meets the grid in view; the stance's grounding is occluded and therefore unreadable.

Shading elsewhere (clay normals on limbs) is coherent enough that it isn't a defect worth flagging; the problems above are geometry/skinning, not lighting.

## shot 07 — show t = 10.50s
`fps 55.007229 · ft avg 15.253155 ms · stage: B7 ARTICULATE`

**read 0** (88.1s)

Most severe first:

1. **Neck / base of skull — torn open.** There is a jagged hole where the head meets the neck; the skin has pulled apart and you can see raw geometry (a row of exposed vertices) through the gap. This is the worst defect on the body and it's directly tied to `spine_upper` being driven to ~117° against a ROM ceiling of 119° — the joint is at its limit and the mesh around it is failing, not bending.

2. **Chest / upper belly — cavity hole.** A flat dark ellipse sits in the front of the ribcage with a hard rim; it reads as missing geometry or an unshaded void rather than volume. It flattens the torso and breaks the silhouette at the centre of mass.

3. **Hands, especially the right (viewer's right) — spiked digits.** The fingers splay into wide flat blades instead of articulated digits; they look detached from a believable hand and spike outward. The left hand is better but still too long and spindly.

4. **Proportions / overall silhouette — not monkey-like.** Head is oversized and bulbous, arms are over-long and stick-thin, legs are short. The whole figure reads as a lanky humanoid with an egg head rather than a quadruped-capable primate; the arm-to-leg ratio inverts what you'd expect.

5. **Muzzle / skull — hard seam.** There's a visible cut line where the flat snout meets the round cranium, so the face looks like a separate lobe bolted on rather than one continuous form. The ears are just nubs and don't sit convincingly on the head.

6. **Feet / ground contact — unverified, likely clipped.** The lower legs end bluntly right at the top edge of the REEL strip, so you cannot confirm honest foot-to-grid contact; as framed it looks like the feet are cut off or floating rather than planted.

Shading is otherwise coherent clay on the limbs (volume reads fine there); the incoherence is concentrated exactly where the geometry fails — the neck tear and the chest cavity.
