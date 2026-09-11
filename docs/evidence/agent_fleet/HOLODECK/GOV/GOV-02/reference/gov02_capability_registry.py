"""GOV-02 INDEPENDENT REFERENCE MODEL — capability and evidence registry.

Written for holodeck-gov-02 (catalogue card GOV-02) as planning-independent
reference text: a small, self-contained, stdlib-only model of per-device /
per-law support records with INDEPENDENT evidence classes, plus the
supervisor-authority qualification gate of the deployed controller
(tools/agent_fleet/control.py at base 62b8e357: qualify op 430-439, claim
caps gate 526, closed resource-class set 178-197, same-task GPU chain gates
581-582 / 253-255).

Card gates modeled verbatim:
  prediction - missing runtime or DYAD evidence remains UNKNOWN regardless of
               unit-test success;
  falsifier  - any inferred capability is advertised as executed (the
               registry refuses, by name, every path that would do this).

Typed states per class: MISSING < INFERRED < EXECUTED. Classes are
independent: no op promotes one class from another's evidence. This file is
evidence; the control runner imports it read-only.
"""


class Refusal(Exception):
    """A named refusal, mirroring the controller's require()/Refusal pair."""


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


CLASS_ORDER = {'MISSING': 0, 'INFERRED': 1, 'EXECUTED': 2}
CLASSES = ('unit_test', 'runtime', 'dyad')


class CapabilityRegistry:
    def __init__(self):
        # key -> {'unit_test': str, 'runtime': str, 'dyad': str,
        #         'runtime_holder': str|None, 'sources': {cls: [source,...]}}
        self.records = {}
        self.agents = {}   # agent -> {'qualified','capabilities','max_tasks'}
        self.revision = 0

    # ---- fixtures ----------------------------------------------------------

    def add_agent(self, aid, max_tasks=2):
        self.agents[aid] = {'qualified': False, 'capabilities': [],
                            'max_tasks': max_tasks}
        return self.agents[aid]

    def record(self, key):
        if key not in self.records:
            self.records[key] = {'unit_test': 'MISSING', 'runtime': 'MISSING',
                                 'dyad': 'MISSING', 'runtime_holder': None,
                                 'sources': {'unit_test': [], 'runtime': [],
                                             'dyad': []}}
        return self.records[key]

    # ---- evidence-class ops (independent by construction) ------------------

    def record_unit_test(self, key, suite='unit'):
        rec = self.record(key)
        rec['unit_test'] = 'EXECUTED'
        rec['sources']['unit_test'].append(suite)
        self.revision += 1
        return dict(rec)

    def infer(self, key, cls, source):
        """A claim from another source: INFERRED is the ceiling (falsifier gate)."""
        require(cls in CLASSES, 'unknown_evidence_class')
        rec = self.record(key)
        if CLASS_ORDER[rec[cls]] < CLASS_ORDER['INFERRED']:
            rec[cls] = 'INFERRED'
        rec['sources'][cls].append('inferred:' + source)
        self.revision += 1
        return dict(rec)

    def reserve_device(self, key, holder):
        """The ONLY path to runtime=EXECUTED: a real (modeled) reservation."""
        rec = self.record(key)
        rec['runtime'] = 'EXECUTED'
        rec['runtime_holder'] = holder
        rec['sources']['runtime'].append('reservation:' + holder)
        self.revision += 1
        return dict(rec)

    def record_dyad(self, key, holder, gpu_key='rtx4090'):
        """DYAD visual evidence requires the same-holder GPU runtime record
        (deployed control.py:581 dyad_requires_gpu_reservation)."""
        gpu = self.record(gpu_key)
        require(gpu['runtime'] == 'EXECUTED' and gpu['runtime_holder'] == holder,
                'dyad_requires_gpu_reservation')
        rec = self.record(key)
        rec['dyad'] = 'EXECUTED'
        rec['sources']['dyad'].append('dyad:' + holder)
        self.revision += 1
        return dict(rec)

    # ---- advertisement (the card falsifier gate) ---------------------------

    def advertise(self, key, cls, as_executed=False):
        """Advertisement must match the stored class. Requesting EXECUTED
        advertisement for a non-EXECUTED class refuses by name."""
        require(cls in CLASSES, 'unknown_evidence_class')
        rec = self.record(key)
        if as_executed:
            require(rec[cls] == 'EXECUTED', 'inferred_advertised_as_executed')
        return {'key': key, 'cls': cls, 'stored': rec[cls],
                'advertised': rec[cls] if as_executed else
                ('EXECUTED' if rec[cls] == 'EXECUTED' else rec[cls])}

    def advertise_visual_capability(self, key, as_executed=False):
        """A visual capability advertises EXECUTED only with dyad EXECUTED."""
        rec = self.record(key)
        if as_executed:
            require(rec['dyad'] == 'EXECUTED', 'inferred_advertised_as_executed')
        return {'key': key, 'advertised': rec['dyad'], 'cls': 'dyad'}

    # ---- qualification / claim gates (deployed 430-439, 526) ---------------

    def qualify(self, actor, agent, caps, evidence, max_tasks=2):
        require(actor == 'SUPERVISOR', 'supervisor_only')
        require(isinstance(evidence, str) and bool(evidence.strip()),
                'missing_qualification_evidence')
        a = self.agents[agent]
        a.update(qualified=True, capabilities=sorted(set(caps)),
                 max_tasks=max_tasks, qualification=evidence)
        self.revision += 1
        return dict(a)

    def claim_requires(self, agent, needed):
        a = self.agents[agent]
        require(a['qualified'], 'qualified_agent_required')
        require(set(needed) <= set(a['capabilities']), 'capability_missing')
        return True

    # ---- persistence boundary ----------------------------------------------

    def save(self, path):
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'revision': self.revision,
                       'records': self.records,
                       'agents': self.agents}, f, sort_keys=True)

    @classmethod
    def load(cls, path):
        import json
        with open(path, encoding='utf-8') as f:
            blob = json.load(f)
        m = cls()
        m.revision = blob['revision']
        m.records = blob['records']
        m.agents = blob['agents']
        return m
