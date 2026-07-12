# Middle: the first ten seconds — audio_visual_sync/telemetry_accessors

0s: W held; the first stride begins. ~0.4s: first footfall — the crunch must
land within 45 ms of the visual boot-contact (audio may lag up to 125 ms before
humans notice; it may lead almost not at all). 0.4–6s: six strides settle into
rhythm; each pair (footfall, crunch) is timestamped by the accessors —
footstep_count climbs 1 per stride, latency samples accumulate. 6s: sprint
starts; cadence doubles and the sync window gets HARDER to hold because anim
notifies compress. 8–10s: stop dead — the test of trailing audio: no orphan
crunch later than 125 ms after the last visible contact.

Response latency budget, stated once for the whole feature: measured
audio-visual offset within [-45 ms, +125 ms] per step. MISSING today: the
counters do not move, so none of the above is currently provable.
