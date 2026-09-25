"""Emit a deterministic ontology snapshot. Reads sources; never modifies them."""
import argparse
from pathlib import Path
import sys
from model import canonical, snapshot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--definition', type=Path, default=Path(__file__).with_name('ontology.json'))
    p.add_argument('--output', type=Path)
    p.add_argument('--catalog', type=Path, default=Path(__file__).resolve().parents[1] / 'monkey_campaign/monkey_completion_map.json')
    args = p.parse_args()
    try:
        result = canonical(snapshot(args.definition, args.root, args.catalog)) + b'\n'
        if args.output:
            # Never let an export overwrite the definition or any referenced source.
            import json
            data = json.loads(result)
            protected = {args.definition.resolve(), args.catalog.resolve()} | {(args.root / s['path']).resolve() for s in data['sources']}
            if args.output.resolve() in protected:
                raise ValueError('output_overwrites_source')
            args.output.write_bytes(result)
        else:
            sys.stdout.buffer.write(result)
        return 0
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        sys.stderr.buffer.write(canonical({'refused': str(exc)}) + b'\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
