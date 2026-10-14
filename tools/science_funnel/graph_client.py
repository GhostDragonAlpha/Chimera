"""Client for the in-memory graph server. Eliminates 3.4s graph loads
by querying a persistent server that holds the graph resident."""
import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def call(path, method="GET", body=None):
    url = f"http://127.0.0.1:8290{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", metavar="ID", help="query an object by id")
    group.add_argument("--hash", action="store_true", help="get the graph hash")
    group.add_argument("--stats", action="store_true", help="server stats")
    group.add_argument("--load", action="store_true", help="force graph reload")
    group.add_argument("--add-object", metavar="JSON", help="add/update an object")
    args = ap.parse_args()

    if args.query:
        result = call(f"/query?id={args.query}")
        print(json.dumps(result, indent=1, ensure_ascii=False)[:2000])
    elif args.hash:
        result = call("/hash")
        print(result.get("graph_hash", "no hash"))
    elif args.stats:
        result = call("/stats")
        print(json.dumps(result, indent=1))
    elif args.load:
        result = call("/load")
        print(json.dumps(result, indent=1))
    elif args.add_object:
        obj = json.loads(args.add_object)
        result = call("/add", method="POST", body=obj)
        print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
