"""Read-only RDF projection; JSON remains authoritative. No qualification writes."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

try:
    from . import model
except ImportError:
    import model

NS = 'urn:chimera:ontology:'


def export(definition):
    model.validate(definition)
    triples = set()
    def iri(kind, *parts):
        return '<' + NS + kind + '/' + '/'.join(quote(p, safe='') for p in parts) + '>'
    def add(s, p, o):
        triples.add(f'{s} <{NS}{p}> {o} .')
    def literal(s):
        return json.dumps(s, ensure_ascii=False)
    def typed(s, name):
        triples.add(f'{s} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <{NS}{name}> .')
    for node in definition['nodes']:
        subject = iri('node', node['id'])
        typed(subject, 'Membrane')
        if node['parent'] is None:
            typed(subject, 'Root')
        else:
            typed(subject, 'ContainedMembrane')
            add(subject, 'parent', iri('node', node['parent']))
        # kind is a vocabulary value, never a containment edge or invented class.
        add(subject, 'kind', literal(node['kind']))
        add(subject, 'label', literal(node['name']))
        add(subject, 'validationStatus', literal(node['validation']['status']))
        for port in node['ports']:
            pid = iri('port', node['id'], port['id'])
            typed(pid, 'Port')
            add(subject, 'port', pid)
            add(pid, 'owner', subject)
            for field in ('protocol', 'unit'):
                add(pid, field, literal(port[field]))
            if 'delegates_to' in port:
                end = port['delegates_to']
                add(pid, 'delegatesTo', iri('port', end['node'], end['port']))
        for claim in node.get('matter_claims', []):
            mid = iri('matter', claim['matter_id'])
            typed(mid, 'MatterIdentity')
            add(subject, 'ownsMatter' if claim['role'] == 'owner' else 'referencesMatter', mid)
        if node['kind'] == 'connection':
            typed(subject, 'Connection')
            add(subject, 'connectionStatus', literal(node['connection_status']))
            for end in node['endpoints']:
                add(subject, 'endpoint', iri('port', end['node'], end['port']))
    snapshot = iri('snapshot', hashlib.sha256(model.canonical(definition)).hexdigest())
    typed(snapshot, 'AuthoredSnapshot')
    add(snapshot, 'authority', literal(definition['authority']))
    add(snapshot, 'canonicalSourceSha256', literal(hashlib.sha256(model.canonical(definition)).hexdigest()))
    return '\n'.join(sorted(triples)) + '\n'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('definition', type=Path)
    args = p.parse_args()
    with args.definition.open('rb') as f:
        definition = model.decode(f.read(model.MAX_DEFINITION + 1))
    print(export(definition), end='')


if __name__ == '__main__':
    main()
