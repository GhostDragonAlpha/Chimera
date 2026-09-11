"""Five planned engine installations; no provisioning or port reservation."""
from pathlib import Path


# fleet-slot-expansion-03 (2026-09-11): slots materialize on demand like
# worktrees; this bound is the SAFETY FUSE (named refusal beyond it), not a
# design ceiling. Registry growth is additive; fresh registries still init 5.
SLOT_MAX = 64


def slot_layout(root, number):
    if type(number) is not int or not 1 <= number <= SLOT_MAX:
        raise ValueError('invalid_slot_number')
    slot = Path(root) / f'slot-{number:02d}'
    return {
        'path': str(slot),
        'kind': 'integration' if number == 1 else 'worker',
        'engine': {
            'build_root': str(slot / '.tmp' / 'engine_build'),
            'runtime_root': str(slot / '.tmp' / 'engine_runtime'),
            'evidence_root': str(slot / '.tmp' / 'engine_evidence'),
            'port_candidate': 8100 + number,
            'port_reserved': False,
            'provisioned': False,
            'binary_identity': 'UNBUILT: bind source head, dirty diff, executable and shader hashes before launch',
        },
    }
