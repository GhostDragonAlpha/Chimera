# Elementary: noun & verb — audio_visual_sync/telemetry_accessors

The NOUN the player holds is their own boots — the footfall — and the crunch of
regolith answering it. The VERB is WALK (and its louder cousin, sprint): the W
key / left stick axis drives locomotion; every stride is an input that demands
an answer.

H-21 rules here: a verb needs behavior, not metadata. For this feature the
behavior chain is: movement input -> footfall animation event -> footstep sound
fires -> SandSoundComponent increments its counters and timestamps the pair.
The world-state change that proves the verb fired is twofold: the audible
crunch in the mix AND the telemetry state change (footstep_count += 1, a fresh
latency sample). Today the second half is dead — the accessors return their
initializer defaults, which means the verb's proof-of-behavior is missing even
while the sound plays. That gap is the feature.
