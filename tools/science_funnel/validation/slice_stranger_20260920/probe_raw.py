"""probe_raw.py -- raw TCP canned-HTTP responder (diagnostic only).
Serves an immediate 5-byte response to every connection on 8931."""
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 8931))
s.listen(8)
print("raw responder on 8931", flush=True)
while True:
    c, _ = s.accept()
    try:
        c.recv(4096)
        c.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
                  b"Content-Length: 5\r\nConnection: close\r\n\r\nHELLO")
    except OSError:
        pass
    finally:
        c.close()
