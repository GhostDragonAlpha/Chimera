import json, socket, sys, time

host = "127.0.0.1"
port = 49173
nonloop = sys.argv[1:]

def request(method, path, body=b""):
    req = (f"{method} {path} HTTP/1.1\r\n"
           f"Host: {host}:{port}\r\n"
           "Connection: close\r\n")
    if body:
        req += f"Content-Length: {len(body)}\r\n"
    req += "\r\n"
    with socket.create_connection((host, port), timeout=1.0) as s:
        s.sendall(req.encode("ascii") + body)
        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    raw = b"".join(chunks)
    head, sep, payload = raw.partition(b"\r\n\r\n")
    first = head.splitlines()[0].decode("ascii", "replace") if head else ""
    return {"status_line": first, "body": payload.decode("utf-8", "replace")}

results = {"local_get": request("GET", "/health"),
           "local_post": request("POST", "/control", b'{"probe":true}')}
nonloop_results = {}
for addr in nonloop:
    rec = {"address": addr}
    try:
        with socket.create_connection((addr, port), timeout=0.8):
            rec.update({"connected": True, "outcome": "UNEXPECTED_ACCEPT"})
    except ConnectionRefusedError as e:
        rec.update({"connected": False, "outcome": "CONNECTION_REFUSED", "errno": e.errno})
    except TimeoutError as e:
        rec.update({"connected": False, "outcome": "TIMEOUT", "error": str(e)})
    except OSError as e:
        rec.update({"connected": False, "outcome": "OSERROR", "errno": e.errno, "error": str(e)})
    nonloop_results[addr] = rec
results["nonloopback"] = nonloop_results
results["all_local_pass"] = (results["local_get"]["status_line"].startswith("HTTP/1.1 200") and
                              results["local_post"]["status_line"].startswith("HTTP/1.1 200"))
results["all_nonloop_refused"] = bool(nonloop_results) and all(
    r["outcome"] == "CONNECTION_REFUSED" for r in nonloop_results.values())
results["pass"] = results["all_local_pass"] and results["all_nonloop_refused"]
print(json.dumps(results, sort_keys=True, indent=2))
raise SystemExit(0 if results["pass"] else 1)
