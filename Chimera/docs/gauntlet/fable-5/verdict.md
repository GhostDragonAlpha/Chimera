# Exit gate verdict — fable-5 chooses

**I choose audio_visual_sync/telemetry_accessors.**

Defense. Both live candidates are limbs of one body: the sleepwalker's beats
failed them together because SandSoundComponent either isn't attached to the
character or never populates its counters at runtime. H-31 names this disease
precisely — telemetry commands that fall back to hardcoded defaults indicate
missing component integration, so verify attachment and initialization order
before blaming action handlers. telemetry_accessors is the attachment-side fix;
report_telemetry merely reads what it populates — fix the accessor root and the
reporter follows for near-free, which is why it outranks its sibling.

My research.md already wrote this feature's exam: footstep count > 0 units as
the liveness sentinel before any latency number is trusted, then the asymmetric
sync window (audio leads <= 45 ms, lags <= 125 ms) measured at 60 fps
foregrounded. The fix is done when THOSE numbers pass in a beat, not when code
compiles.

Graph prior: surprise_79acef63880dfc4d warns that node parameters can be plain
strings — every read-back this fix adds must type-guard its telemetry reads, or
the verifier itself becomes the next hardcoded-defaults lie. The board task is
tb-0001; it sits blocked on exactly this root cause, and unblocking it releases
two rejected features with one change. That is the highest-leverage move on the
board, and I would stake my new credential on it.
