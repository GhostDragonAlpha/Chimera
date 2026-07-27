"""Thin CLI wrapper around graphify_query -- the real, general query dispatcher.

Usage (from E:/PythonChimera/Chimera):
    python -m core.graphify_query_cli <query_type> [identifier]

query_type: pattern | file | mutation | community | chain | config | campus | health | feature | pathway | gpa
"""
import json
import sys

from core.graphify_interface import graphify_query


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m core.graphify_query_cli <query_type> [identifier]")
    query_type = sys.argv[1]
    identifier = sys.argv[2] if len(sys.argv) > 2 else None
    result = graphify_query(query_type, identifier)
    print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    main()
