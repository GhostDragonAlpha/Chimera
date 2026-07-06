import urllib.request
import json

req = urllib.request.Request('http://localhost:1234/v1/models')
try:
    resp = urllib.request.urlopen(req, timeout=5)
    print(resp.read().decode('utf-8'))
except Exception as e:
    print(f'Error: {e}')
