"""Five planned engine installations; no provisioning or port reservation."""
from pathlib import Path


def slot_layout(root, number):
    if type(number) is not int or not 1 <= number <= 5:
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
