# Master: two living systems — audio_visual_sync/telemetry_accessors

- **ChimeraMovementComponent (locomotion):** the interaction is total — stride
  events are this feature's heartbeat, and movement regressions surface here
  first (H-24: features tagged only by movement beats are hostage to rig
  health; a GameMode with no PlayerControllerClass zeroes displacement AND
  footsteps together). The exploit at the seam: a hostile player wiggle-walks
  (rapid strafe reversals) to fire contact events faster than real cadence,
  inflating any future step-counted reward. Fix: the debounce plus a
  velocity-consistency check — steps only count when displacement over the
  debounce window exceeds half a stride length.
- **Ground surface system (Ground_Sand/Rock/Metal_Surface):** surface type
  selects the sound and tags the sample; the per-surface accessors are how
  those three provisional features get their collapse evidence. The exploit at
  the seam: standing on a surface BOUNDARY and rocking in place to double-tag
  samples across two surfaces, muddying per-surface stats. Fix: tag by the
  surface under the CONTACT foot at event time, never by volume overlap, and
  count boundary rocks into the orphan bucket when displacement fails the
  stride check.
