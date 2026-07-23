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
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
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
