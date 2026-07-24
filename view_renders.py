#!/usr/bin/env python3
"""Start HTTP server for viewing rendered children images."""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = "Saved/SplatEmit"

def start_server():
    """Start the HTTP server and open browser."""
    os.chdir(DIRECTORY)
    
    # Create handler
    Handler = http.server.SimpleHTTPRequestHandler
    
    # BIND LOCALHOST ONLY (fixed 2026-07-23). ("", PORT) means EVERY network interface,
    # so this was serving Saved/SplatEmit to anything on the LAN -- it was reachable at
    # 192.168.3.169:8080. That is an accident of a copied idiom, not a decision: the print
    # below has always said "localhost", which was the intent all along.
    #
    # Nothing is lost by this. The browser and the agent both run ON this machine, so
    # 127.0.0.1 serves them exactly as well and serves nobody else. If you ever genuinely
    # need another device to reach it, change it back deliberately and know that you did.
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Serving images at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        
        # Open browser after a short delay
        import threading
        def open_browser():
            import time
            time.sleep(1)  # Wait for server to start
            webbrowser.open(f"http://localhost:{PORT}")
        
        thread = threading.Thread(target=open_browser)
        thread.daemon = True
        thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    start_server()
