"""GENERATED from Chimera/docs/THE_STORY.md by gen_decl.py -- DO NOT EDIT.

The story is the source; its ```chimera-terms``` block is the decomposition of the
timeline into the game. Re-run `python ChimeraEngine/gen_decl.py` after changing it."""

TERMS = [
    ('theStory', None, 'H', 'the teddy bear -- a third-person character, trained like a robot, run by CA rules'),
    ('theSeed', 'theStory', 'P', 'the genome + the GENERATED base: one AI-authored still -> controlled multi-view imagery (azimuth AND elevation) -> feed-forward 3DGS (AnySplat) -> 14-float cloud; one seed grows the same bear, deterministically'),
    ('theDeterminism', 'theSeed', 'P', "same genome -> same cells, bit-identical -- the seed's only law"),
    ('theShape', 'theStory', 'P', 'the voxel lattice body -- the generated 3DGS cloud gives the base representation; the CA owns it after'),
    ('theBalance', 'theShape', 'P', 'center of mass inside the paw support hull (margin >= 1 cell) -- the standing gate'),
    ('theMuscle', 'theStory', 'P', 'a column that shortens -- movement is cells added/removed on the lattice'),
    ('theRig', 'theStory', 'P', 'the chains the muscle rides on, derived from the shape (never the reverse)'),
    ('theGait', 'theStory', 'P', 'the beat machine (LIFT/SWING/PLANT/SHIFT) -- each joint verified before the walk'),
    ('theStand', 'theGait', 'P', 'rest equilibrium: paws planted, zero drift, no airwalk'),
    ('theWalk', 'theGait', 'P', 'the stride -- trained only after every movement is verified'),
    ('theScan', 'theStory', 'P', 'sense: the retinal senses read the field around the bear (ground, goal bearing, reach)'),
    ('theChoose', 'theStory', 'P', 'plan: Q-learning over rest/wave/walk picks the steps toward a goal (sense -> plan -> act)'),
    ('theControl', 'theStory', 'P', 'third-person control -- the operator steers the bear, or hands over to its own policy'),
    ('theWorld', 'theStory', 'P', 'the training environment (the gym): terrain, contact, gravity, and the goal placed in it'),
    ('theAppearance', 'theStory', 'P', 'the splat surface -- SPL markers so the outer skin transforms smoothly with the lattice'),
    ('theMeaning', 'theStory', 'H', 'is it recognizably a teddy bear -- the eye judges each movement (right knee? right bend?)'),
]
