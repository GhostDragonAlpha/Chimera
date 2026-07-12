# High: the governing curve — audio_visual_sync/telemetry_accessors

The governing quantity is per-step offset: delta = t_audio_start -
t_visual_contact. The acceptance curve is the asymmetric window
W(delta) = pass if -45 ms <= delta <= +125 ms — asymmetric because human
perception forgives late audio roughly 3x more than early audio (sound cannot
physically precede its cause).

Worked typical case: walking at 1.6 steps/s, animation notify fires at contact
frame, audio starts next audio buffer -> delta ~= +12 ms — comfortably inside.
Worked extreme case: 30 fps hitch drops the notify a frame late while audio was
scheduled off the previous tick -> visual contact slides +33 ms, delta reads
-33 ms (audio now EARLY) — one hitch from the -45 ms cliff, which is why the
sync budget must be measured at the fps floor, not at the average.
