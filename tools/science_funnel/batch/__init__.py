"""Batch database integration: connect a source, integrate every record, prove
the whole batch mechanically against per-class contracts in one run.

Two run classes:
  admit    -- new connectors through the current pipeline (bundles, proposals)
  reprove  -- existing admissions replayed under their RECORDED producer and
             byte-compared against the graph (code drift can never fake this)
"""
