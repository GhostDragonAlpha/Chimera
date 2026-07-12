# Elementary: the smallest slice — audio_visual_sync/telemetry_accessors

The smallest shippable slice today: ONE counter that increments on the footstep
sound's actual play event, exposed through ONE accessor, read back in PIE after
ten real strides and asserted > 0. No latency math, no window, no histogram —
just proof the nervous system is connected to the body.

That minimal slice already proves the hard part: SandSoundComponent is
attached, initialized before first footfall, and wired to the real audio event
rather than the animation notify alone. The full version adds what the smallest
one makes meaningful — per-step latency samples, the asymmetric sync window,
and surface-type breakdown — but none of those matter until count moves.
