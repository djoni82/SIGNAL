#!/usr/bin/env python3
"""
Simple HTTP server for Telegram Mini App
Serves the CryptoAlphaPro Mini App on localhost
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = Path(__file__).parent

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler with CORS support"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def start_server():
    """Start the Mini App server"""
    os.chdir(DIRECTORY)
    
    print("🚀 Starting CryptoAlphaPro Mini App Server...")
    print(f"📱 Server will run on: http://localhost:{PORT}")
    print(f"📂 Serving files from: {DIRECTORY}")
    print()
    print("🔗 URLs for BotFather:")
    print(f"   Local: http://localhost:{PORT}")
    print(f"   Use ngrok for public URL: ngrok http {PORT}")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            
            # Try to open browser
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 Opened in default browser")
            except:
                pass
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use!")
            print("   Try a different port or stop the existing server")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    start_server()
