"""Multiprocess HTTP server test."""

import http.server
import multiprocessing
import sys
import os
import time

def run_server():
    """Run HTTP server in a separate process."""
    try:
        print("Server process starting...", file=sys.stderr)
        print(f"Process ID: {os.getpid()}", file=sys.stderr)
        
        # Create handler
        handler = http.server.SimpleHTTPRequestHandler
        
        # Create server
        port = 4000
        server = http.server.HTTPServer(('127.0.0.1', port), handler)
        print(f"Server bound to port {port}", file=sys.stderr)
        
        # Start serving
        print("Starting server...", file=sys.stderr)
        server.serve_forever()
        
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        # Start server in separate process
        server_process = multiprocessing.Process(target=run_server)
        server_process.start()
        print(f"Server process started with PID {server_process.pid}", file=sys.stderr)
        
        # Keep main process running
        try:
            while True:
                time.sleep(1)
                if not server_process.is_alive():
                    print("Server process died", file=sys.stderr)
                    break
        except KeyboardInterrupt:
            print("\nShutting down...", file=sys.stderr)
        finally:
            server_process.terminate()
            server_process.join()
            
    except Exception as e:
        print(f"Main process error: {e}", file=sys.stderr)
        raise
