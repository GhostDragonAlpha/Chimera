"""Graph-required fleet entry point. Requires externally provisioned secrets."""
import argparse
import os
from pathlib import Path
from graph_workflow import GraphWorkflowControl
from service import Server


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'db', 'graph'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--auxiliary', type=Path)
    p.add_argument('--port', type=int, required=True)
    a = p.parse_args()
    admin = os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN', '')
    enroll = os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN', '')
    if not admin or not enroll:
        p.error('Provision controller secrets outside agent access; do not paste credentials.')
    control = GraphWorkflowControl(a.db, admin, enroll, a.root, graph_path=a.graph, auxiliary_path=a.auxiliary)
    server = Server(('127.0.0.1', a.port), control)
    print('Graph-required controller active; raw filesystem access is not sandboxed.', flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
