"""tools/science_funnel/diagnosis -- the machine-generated failure-analysis packet.

Lane: agent/failure-packets-20260921 (Astra P2, the failure-analysis-packet protocol).
Input: a failed run's GAIT_EVENT_TRACE stderr + its stdout census + the receipt's
pre-registered rule_0 block (+ a reference run's trace when supplied).
Output: a compact packet -- first fired falsifier, earliest relevant divergence,
the dependency slice (controller decisions -> forces -> contacts -> death),
the phase/force/work/energy bookkeeping, a replayable state reference, ranked
discriminating interventions, and a signature matched against the past waves'
death records.  The packet is a READ-ONLY projection of the trace: it never cuts
trace sections and never proposes a law.

Rule-0: tools/science_funnel/validation/failure_packets_20260921/prereg.json
(frozen BEFORE this package existed; falsifiers F-DIAGNOSIS-TIME / -WRONG / -LEAK).
"""
